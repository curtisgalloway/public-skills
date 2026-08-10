#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Curtis Galloway
# SPDX-License-Identifier: Apache-2.0
"""
cleanroom_hook.py - Claude Code PreToolUse hook enforcing the clean-room
source ban in implementation sessions.

Reads the PreToolUse JSON from stdin, checks the tool's target (file path,
URL, bash command, search query) against the clean-room policy, and:

  - no match           -> exit 0 (allow, silent)
  - match, role set    -> exit 0 (allow) but LOG the access. Dirty-side
                          processes (investigator/verifier) run with
                          CLEANROOM_ROLE=investigator|verifier; their
                          source reads are authorized and recorded, so the
                          log is a complete, attributed record of every
                          encumbered-source access in the project.
  - match, no role     -> exit 2 (block). stderr goes back to the model
                          with the sanctioned alternative (file a
                          spec-gap), and the attempt is logged.

Policy resolution: $CLEANROOM_POLICY, then
$CLAUDE_PROJECT_DIR/.claude/cleanroom-policy.json, then
./.claude/cleanroom-policy.json, then built-in defaults.

Only known path/url/command fields are checked. Edit/Write CONTENT is
deliberately not scanned (a doc comment mentioning "trusted-firmware-a"
must not block the edit); content-level leaks are the job of
session_audit.py and the pre-merge output scan.

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

# Tools whose target is a filesystem path (field name per tool).
PATH_FIELDS = {
    "Read": "file_path", "Edit": "file_path", "Write": "file_path",
    "MultiEdit": "file_path", "NotebookRead": "notebook_path",
    "NotebookEdit": "notebook_path", "Grep": "path", "Glob": "path",
}


def project_dir():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def load_policy():
    candidates = [
        os.environ.get("CLEANROOM_POLICY"),
        os.path.join(project_dir(), ".claude", "cleanroom-policy.json"),
        os.path.join(".claude", "cleanroom-policy.json"),
    ]
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


def pick_target(tool, tool_input, pol):
    """Return (target_text, matched_pattern_or_None) for this tool call."""
    if tool in PATH_FIELDS:
        text = str(tool_input.get(PATH_FIELDS[tool], ""))
        return text, match(text, pol)
    if tool == "Bash":
        text = str(tool_input.get("command", ""))
        return text, match(text, pol)
    if tool == "WebFetch":
        text = str(tool_input.get("url", ""))
        return text, match(text, pol)
    if tool == "WebSearch":
        text = str(tool_input.get("query", ""))
        return text, match(text, pol, use_paths=False, use_roots=False)
    # Unknown tools (incl. MCP fetch/read tools): scan serialized input for
    # URLs and checkout roots only - path patterns over arbitrary content
    # would false-positive on legitimate payloads.
    text = json.dumps(tool_input)
    return text, match(text, pol, use_paths=False)


def log_entry(pol, entry):
    try:
        path = pol.get("log_file", DEFAULT_POLICY["log_file"])
        if not os.path.isabs(path):
            path = os.path.join(project_dir(), path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # logging is best-effort; never break the session


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}
    pol = load_policy()
    target, hit = pick_target(tool, tool_input, pol)
    if not hit:
        sys.exit(0)

    role = os.environ.get("CLEANROOM_ROLE", "").strip().lower()
    authorized = role in [r.lower() for r in pol.get("authorized_roles", [])]
    log_entry(pol, {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "session_id": data.get("session_id", ""),
        "cwd": data.get("cwd", os.getcwd()),
        "tool": tool,
        "pattern": hit,
        "target": target[:300],
        "role": role or None,
        "action": "allowed-role" if authorized else "blocked",
    })
    if authorized:
        sys.exit(0)

    sys.stderr.write(
        f"cleanroom: BLOCKED {tool} - target matches '{hit}'. Encumbered "
        f"source (Linux/U-Boot/TF-A/vendor firmware) is off-limits in "
        f"implementation sessions. If the spec is insufficient, append the "
        f"question to {pol.get('gap_hint')} as '- [open] <date> <section> "
        f"<question>', mark the code site TODO(spec-gap), and continue with "
        f"other work. This attempt was logged.\n")
    sys.exit(2)


if __name__ == "__main__":
    main()
