#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Curtis Galloway
# SPDX-License-Identifier: Apache-2.0
"""
cleanroom_hook.py - PreToolUse hook enforcing the clean-room source ban in
implementation sessions.

Wire it into Antigravity's hooks.json with matcher `.*` so MCP and
provider-specific tools are covered too:

  <workspace>/.agents/hooks.json     per project -> assets/antigravity-hooks.json
  ~/.gemini/config/hooks.json        every project (older builds:
                                     ~/.gemini/antigravity-cli/hooks.json)

Reads the hook event JSON from stdin, checks the tool's target (file path,
shell command, URL, search query) against the clean-room policy, and:

  - no match           -> allow, silent
  - match, role set    -> allow but LOG the access. Dirty-side processes
                          (investigator/verifier) run with
                          CLEANROOM_ROLE=investigator|verifier; their
                          source reads are authorized and recorded, so the
                          log is a complete, attributed record of every
                          encumbered-source access in the project.
  - match, no role     -> DENY. The sanctioned alternative (file a spec-gap)
                          goes back to the model, and the attempt is logged.

ALLOW IS EXPLICIT, ALWAYS. Antigravity's PreToolUse contract does not accept
an empty object or empty stdout as permission to proceed - a hook that stays
silent can wedge every tool call in the session. So every allow path here,
including the malformed-input path, prints {"decision": "allow"}.

And ONLY that. The allow deliberately omits Claude Code's
hookSpecificOutput.permissionDecision: "allow", which is not a no-op there -
it auto-approves the call and consumes the user's permission prompt. Deny
broadcasts to every dialect because withholding permission is safe to
repeat; allow does not, because granting it is not. Keep that asymmetry if
you edit this.

DENY is emitted three ways at once - {"decision": "deny", "reason": ...} on
stdout, the reason on stderr, and exit code 2 - because Antigravity honours
the decision object and treats a non-zero exit as a block, while other
harnesses read only one of the two. Exit 2 is the default because it fails
closed; set CLEANROOM_BLOCK_EXIT_CODE=0 if a build objects to it.

Antigravity nests the call as {"toolCall": {"name": ..., "args": {...}}} and
names arguments in PascalCase (run_command takes CommandLine, Cwd). Tool
vocabularies differ between builds and harnesses, so nothing here is keyed on
a tool-name table: targets are found by ARGUMENT KEY, case-folded. Path-ish
and command-ish keys are matched against the full policy, every other key
against URLs and checkout roots only. An unrecognised tool is still checked.

Project dir: $CLEANROOM_PROJECT_DIR, then the event's `workspacePaths[0]` /
`cwd`, then legacy $GEMINI_PROJECT_DIR / $CLAUDE_PROJECT_DIR, then the
working directory walked up to the nearest harness config dir.

Policy: $CLEANROOM_POLICY, then <project>/{.agents,.agent,.gemini,.claude}/
cleanroom-policy.json, then built-in defaults.

Written/edited CONTENT is deliberately not scanned (a doc comment mentioning
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

# Harness config directories, in policy-resolution order: Antigravity
# workspace, Antigravity rules, shared ~/.gemini layout, Claude Code.
CONFIG_DIRS = (".agents", ".agent", ".gemini", ".claude")

# Argument keys whose values are filesystem paths. Keys are compared
# case-folded, which is what makes Antigravity's PascalCase (TargetFile,
# AbsolutePath, Cwd) and snake_case tool vocabularies land in one set.
PATH_KEYS = {
    "file_path", "filepath", "absolute_path", "absolutepath", "path",
    "paths", "dir_path", "dirpath", "directory", "directorypath",
    "notebook_path", "target_file", "targetfile", "file", "files",
    "relative_path", "relativepath", "relativefilepath", "search_directory",
    "searchdirectory", "root", "cwd", "workdir", "workingdirectory",
}

# Argument keys whose values are shell command lines.
COMMAND_KEYS = {
    "command", "commands", "commandline", "command_line", "cmd", "script",
    "shell_command", "safe_to_autorun_command",
}

# Argument keys carrying authored text. NEVER matched: blocking an edit
# because its prose names a forbidden project is a false positive, and
# content-level leaks belong to session_audit.py and the output scan.
CONTENT_KEYS = {
    "content", "contents", "text", "body", "old_string", "new_string",
    "old_str", "new_str", "codeedit", "code_edit", "replacement", "patch",
    "diff", "instruction", "message", "summary", "explanation",
}

ALLOW = {"decision": "allow"}


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
    explicit = os.environ.get("CLEANROOM_PROJECT_DIR")
    if explicit:
        return explicit
    if cwd_hint:
        return _find_root(cwd_hint)
    for var in ("GEMINI_PROJECT_DIR", "CLAUDE_PROJECT_DIR"):
        val = os.environ.get(var)
        if val:
            return val
    return _find_root(os.getcwd())


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
    """Yield (case-folded key, string) for every string leaf in a tree."""
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

    Keyed on argument names, not tool names, so one policy covers
    Antigravity's vocabulary (and PascalCase), MCP tools, and whatever a
    future build renames.
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
            # Unknown keys (search queries, prompts carrying URLs, MCP
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


def allow():
    """Antigravity needs an explicit allow; silence can wedge the session."""
    sys.stdout.write(json.dumps(ALLOW))
    sys.exit(0)


def deny(reason):
    """Emit a deny in every dialect at once, then exit fail-closed."""
    payload = {
        "decision": "deny",           # Antigravity
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


def parse_event(data):
    """Return (tool_name, tool_args, cwd_hint, session_id, extra_paths).

    Antigravity nests the call under `toolCall` and reports the workspace in
    `workspacePaths`; flat `tool_name`/`tool_input` payloads are accepted too
    so the same hook keeps working on other harnesses.
    """
    call = data.get("toolCall")
    if not isinstance(call, dict):
        call = data
    tool = ""
    for key in ("name", "tool_name", "toolName", "tool"):
        if isinstance(call.get(key), str) and call[key]:
            tool = call[key]
            break
    args = None
    for key in ("args", "arguments", "tool_input", "toolInput", "input",
                "parameters"):
        if key in call:
            args = call[key]
            break
    if args is None:
        args = {}

    cwd_hint = None
    paths = data.get("workspacePaths")
    if isinstance(paths, list) and paths and isinstance(paths[0], str):
        cwd_hint = paths[0]
    cwd_hint = cwd_hint or data.get("cwd") or None

    session = (data.get("conversationId") or data.get("session_id")
               or data.get("sessionId") or "")

    # Where this session's own record lives - worth logging, because the
    # pre-merge audit has to find it later.
    extra = {}
    for src, dst in (("transcriptPath", "transcript"),
                     ("transcript_path", "transcript"),
                     ("artifactDirectoryPath", "artifacts")):
        val = data.get(src)
        if isinstance(val, str) and val and dst not in extra:
            extra[dst] = val
    return tool, args, cwd_hint, session, extra


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        allow()
    if not isinstance(data, dict):
        allow()
    tool, args, cwd_hint, session, extra = parse_event(data)
    pol = load_policy(cwd_hint)
    target, hit = pick_target(tool, args, pol)
    if not hit:
        allow()

    role = os.environ.get("CLEANROOM_ROLE", "").strip().lower()
    authorized = role in [r.lower() for r in pol.get("authorized_roles", [])]
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "session_id": session,
        "cwd": cwd_hint or os.getcwd(),
        "tool": tool,
        "pattern": hit,
        "target": target[:300],
        "role": role or None,
        "action": "allowed-role" if authorized else "blocked",
    }
    entry.update(extra)
    log_entry(pol, entry, cwd_hint)
    if authorized:
        allow()

    deny(
        f"cleanroom: BLOCKED {tool} - target matches '{hit}'. Encumbered "
        f"source (Linux/U-Boot/TF-A/vendor firmware) is off-limits in "
        f"implementation sessions. If the spec is insufficient, append the "
        f"question to {pol.get('gap_hint')} as '- [open] <date> <section> "
        f"<question>', mark the code site TODO(spec-gap), and continue with "
        f"other work. This attempt was logged.")


if __name__ == "__main__":
    main()
