#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Curtis Galloway
# SPDX-License-Identifier: Apache-2.0
"""
cleanroom_hook.py - pre-tool-use hook enforcing the clean-room source ban in
implementation sessions.

Wire it as the Gemini CLI `BeforeTool` event or the Antigravity `PreToolUse`
event, with matcher `.*` so MCP and provider-specific tools are covered too:

  Gemini CLI     .gemini/settings.json   -> assets/gemini-settings-fragment.json
  Antigravity    .agents/hooks.json      -> assets/antigravity-hooks.json

Reads the hook event JSON from stdin, checks the tool's target (file path,
shell command, URL, search query) against the clean-room policy, and:

  - no match           -> exit 0 (allow, silent)
  - match, role set    -> exit 0 (allow) but LOG the access. Dirty-side
                          processes (investigator/verifier) run with
                          CLEANROOM_ROLE=investigator|verifier; their
                          source reads are authorized and recorded, so the
                          log is a complete, attributed record of every
                          encumbered-source access in the project.
  - match, no role     -> DENY. The sanctioned alternative (file a spec-gap)
                          goes back to the model, and the attempt is logged.

Deny is emitted three ways at once so one script serves every harness: a
decision object on stdout (`decision: deny` for Gemini CLI and Antigravity,
`hookSpecificOutput.permissionDecision` for Claude Code), the reason on
stderr, and exit code 2 - which every one of them treats as a hard block.
Set CLEANROOM_BLOCK_EXIT_CODE=0 for a harness that only honours the stdout
object. Exit 2 is the default because it fails closed.

Tool names differ per harness (`read_file` / `Read`, `run_shell_command` /
`Bash` / `run_command`, `web_fetch` / `WebFetch`), so nothing here is keyed
on a tool-name table. Targets are found by ARGUMENT KEY: path-ish and
command-ish keys are matched against the full policy, every other key
against URLs and checkout roots only. An unrecognised tool from an
unrecognised harness is still checked.

Project dir: $CLEANROOM_PROJECT_DIR, then $GEMINI_PROJECT_DIR (Gemini CLI
exports it to hooks), then $CLAUDE_PROJECT_DIR, then the event's `cwd`
walked up to the nearest harness config dir.

Policy: $CLEANROOM_POLICY, then <project>/{.gemini,.agents,.agent,.claude}/
cleanroom-policy.json, then built-in defaults.

Edit/Write CONTENT is deliberately not scanned (a doc comment mentioning
"trusted-firmware-a" must not block the edit); content-level leaks are the
job of session_audit.py and the pre-merge output scan.

Never breaks the session: malformed input or logging failure -> allow.
"""

import json
import os
import sys
import time

DEFAULT_POLICY = {
    "checkout_roots": [
        "~/src/linux", "~/linux", "~/src/u-boot",
        "~/src/arm-trusted-firmware", "~/src/trusted-firmware-a",
    ],
    "blocked_path_patterns": [
        "/linux/drivers/", "/linux/arch/", "/linux/include/",
        "/linux/kernel/", "/linux/sound/", "/linux/net/", "/linux/block/",
        "/linux/fs/", "/linux/mm/", "linux.git", "linux-stable",
        "linux-next", "/u-boot/", "u-boot.git", "arm-trusted-firmware",
        "trusted-firmware-a", "/optee", "raspberrypi/linux",
    ],
    "blocked_url_patterns": [
        "kernel.org", "bootlin.com", "kernel.googlesource.com",
        "android.googlesource.com/kernel", "github.com/torvalds",
        "github.com/raspberrypi/linux", "github.com/u-boot",
        "github.com/ARM-software/arm-trusted-firmware", "source.denx.de",
        "git.trustedfirmware.org", "review.trustedfirmware.org",
        "sources.debian.org/src/linux",
    ],
    "authorized_roles": ["investigator", "verifier"],
    "log_file": "docs/provenance/hook-blocks.jsonl",
    "gap_hint": "docs/spec-gaps/<device>.md",
}

# Harness config directories, in policy-resolution order: Gemini CLI,
# Antigravity (workspace agents/hooks), Antigravity rules, Claude Code.
CONFIG_DIRS = (".gemini", ".agents", ".agent", ".claude")

# Argument keys whose values are filesystem paths, per harness vocabulary:
# read_file/write_file/replace (file_path, absolute_path), glob/grep_search
# (path), list_directory (dir_path), read_many_files (paths), Claude Code
# (file_path, notebook_path), Antigravity/Cascade-style (target_file).
PATH_KEYS = {
    "file_path", "filepath", "absolute_path", "path", "paths", "dir_path",
    "directory", "notebook_path", "target_file", "targetfile", "file",
    "files", "root", "cwd", "workdir",
}

# Argument keys whose values are shell command lines.
COMMAND_KEYS = {
    "command", "commands", "cmd", "command_line", "commandline", "script",
    "shell_command", "safe_to_autorun_command",
}

# Argument keys carrying authored text. NEVER matched: blocking an edit
# because its prose names a forbidden project is a false positive, and
# content-level leaks belong to session_audit.py and the output scan.
CONTENT_KEYS = {
    "content", "contents", "text", "body", "old_string", "new_string",
    "old_str", "new_str", "replacement", "patch", "diff", "instruction",
    "message", "summary",
}


def _find_root(start):
    """Walk up from `start` to the nearest harness config dir (or .git)."""
    cur = os.path.abspath(start)
    while True:
        for marker in CONFIG_DIRS + (".git",):
            if os.path.isdir(os.path.join(cur, marker)):
                return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return os.path.abspath(start)
        cur = parent


def project_dir(cwd_hint=None):
    for var in ("CLEANROOM_PROJECT_DIR", "GEMINI_PROJECT_DIR",
                "CLAUDE_PROJECT_DIR"):
        val = os.environ.get(var)
        if val:
            return val
    return _find_root(cwd_hint or os.getcwd())


def load_policy(cwd_hint=None):
    root = project_dir(cwd_hint)
    candidates = [os.environ.get("CLEANROOM_POLICY")]
    for cfg in CONFIG_DIRS:
        candidates.append(os.path.join(root, cfg, "cleanroom-policy.json"))
    for cfg in CONFIG_DIRS:
        candidates.append(os.path.join(cfg, "cleanroom-policy.json"))
    for cand in candidates:
        if cand and os.path.isfile(cand):
            try:
                with open(cand, encoding="utf-8") as f:
                    pol = dict(DEFAULT_POLICY)
                    pol.update(json.load(f))
                    return pol
            except Exception:
                pass
    return dict(DEFAULT_POLICY)


def norm(s):
    return str(s).lower().replace("\\", "/")


def match(text, pol, use_paths=True, use_urls=True, use_roots=True):
    """Return the matched pattern label, or None."""
    t = norm(text)
    if not t:
        return None
    if use_roots:
        for root in pol.get("checkout_roots", []):
            r = norm(os.path.expanduser(root)).rstrip("/")
            if r and r in t:
                return f"checkout_root:{root}"
    if use_paths:
        for p in pol.get("blocked_path_patterns", []):
            if norm(p) in t:
                return f"path:{p}"
    if use_urls:
        for u in pol.get("blocked_url_patterns", []):
            if norm(u) in t:
                return f"url:{u}"
    return None


def _strings(node, key=None):
    """Yield (key, string) for every string leaf in a tool-input tree."""
    if isinstance(node, str):
        yield key, node
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from _strings(v, str(k).lower())
    elif isinstance(node, (list, tuple)):
        for v in node:
            yield from _strings(v, key)


def pick_target(tool, tool_input, pol):
    """Return (target_text, matched_pattern_or_None) for this tool call.

    Keyed on argument names, not tool names, so the same policy covers
    Gemini CLI, Antigravity, Claude Code and MCP tool vocabularies.
    """
    first = ""
    for key, text in _strings(tool_input):
        if not text:
            continue
        if not first:
            first = text
        if key in CONTENT_KEYS:
            continue
        if key in PATH_KEYS or key in COMMAND_KEYS:
            hit = match(text, pol)
        else:
            # Unknown keys (web_fetch's `prompt`, search queries, MCP
            # arguments): URLs and checkout roots only. Path patterns over
            # arbitrary prose would false-positive.
            hit = match(text, pol, use_paths=False)
        if hit:
            return text, hit
    return first, None


def log_entry(pol, entry, cwd_hint=None):
    try:
        path = pol.get("log_file", DEFAULT_POLICY["log_file"])
        if not os.path.isabs(path):
            path = os.path.join(project_dir(cwd_hint), path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # logging is best-effort; never break the session


def deny(reason):
    """Emit a deny in every harness's dialect, then exit fail-closed."""
    payload = {
        "decision": "deny",           # Gemini CLI, Antigravity
        "reason": reason,
        "continue": True,             # block this call, not the session
        "systemMessage": "cleanroom: encumbered-source access blocked",
        "hookSpecificOutput": {       # Claude Code
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        },
    }
    sys.stdout.write(json.dumps(payload))
    sys.stderr.write(reason + "\n")
    try:
        code = int(os.environ.get("CLEANROOM_BLOCK_EXIT_CODE", "2"))
    except ValueError:
        code = 2
    sys.exit(code)


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    if not isinstance(data, dict):
        sys.exit(0)
    tool = ""
    for key in ("tool_name", "toolName", "name", "tool"):
        if isinstance(data.get(key), str) and data[key]:
            tool = data[key]
            break
    tool_input = None
    for key in ("tool_input", "toolInput", "args", "arguments", "input",
                "parameters"):
        if key in data:
            tool_input = data[key]
            break
    if tool_input is None:
        tool_input = {}
    cwd_hint = data.get("cwd") or None
    pol = load_policy(cwd_hint)
    target, hit = pick_target(tool, tool_input, pol)
    if not hit:
        sys.exit(0)

    role = os.environ.get("CLEANROOM_ROLE", "").strip().lower()
    authorized = role in [r.lower() for r in pol.get("authorized_roles", [])]
    log_entry(pol, {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "session_id": data.get("session_id", data.get("sessionId", "")),
        "cwd": cwd_hint or os.getcwd(),
        "tool": tool,
        "pattern": hit,
        "target": target[:300],
        "role": role or None,
        "action": "allowed-role" if authorized else "blocked",
    }, cwd_hint)
    if authorized:
        sys.exit(0)

    deny(
        f"cleanroom: BLOCKED {tool} - target matches '{hit}'. Encumbered "
        f"source (Linux/U-Boot/TF-A/vendor firmware) is off-limits in "
        f"implementation sessions. If the spec is insufficient, append the "
        f"question to {pol.get('gap_hint')} as '- [open] <date> <section> "
        f"<question>', mark the code site TODO(spec-gap), and continue with "
        f"other work. This attempt was logged.")


if __name__ == "__main__":
    main()
