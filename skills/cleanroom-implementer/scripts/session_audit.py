#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Curtis Galloway
# SPDX-License-Identifier: Apache-2.0
"""
session_audit.py - post-session transcript audit for clean-room
implementation sessions (the detection layer behind the hook).

Scans Claude Code session transcripts (JSONL) for evidence that encumbered
source entered the context, regardless of route:

  1. TOOL TARGETS - every tool_use in the transcript is checked against the
     same clean-room policy the hook enforces (paths, checkout roots,
     kernel-mirror URLs, bash commands). Catches sessions that ran without
     the hook, and MCP/side channels.
  2. LICENSE MARKERS - tool_result content is scanned for GPL/kernel
     markers (SPDX GPL tags, MODULE_LICENSE, EXPORT_SYMBOL,
     '#include <linux/', GPL boilerplate). A marker in ANY result is
     high-signal that source text arrived, whatever fetched it.
  3. CODE-SHAPED NETWORK PAYLOADS - results of network/bash tools with a
     high density of C-shaped lines. (Workspace Read results are exempt:
     reading the target OS tree is legitimate and full of C.)
  4. HOOK LOG - if the policy's hook log exists, blocked/allowed-role
     counts are summarized for cross-reference (info, not findings).

The report cites transcript line numbers, tool names, pattern/marker names
and counts - it never reproduces fetched content. Exit 0 = clean,
1 = findings, 2 = error.

Usage:
  python3 session_audit.py SESSION.jsonl [...] [--policy FILE] [--out FILE]
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from cleanroom_hook import (DEFAULT_POLICY, load_policy, pick_target,
                                project_dir)
except Exception:  # pragma: no cover - ships alongside the hook
    print("session_audit: cannot import cleanroom_hook.py from the same "
          "directory", file=sys.stderr)
    sys.exit(2)

LICENSE_MARKERS = [
    ("SPDX-GPL", re.compile(r"SPDX-License-Identifier:\s*GPL", re.I)),
    ("MODULE_LICENSE", re.compile(r"MODULE_LICENSE\s*\(")),
    ("EXPORT_SYMBOL", re.compile(r"\bEXPORT_SYMBOL(_GPL)?\b")),
    ("include-linux", re.compile(r"#include\s*<linux/")),
    ("GPL-boilerplate", re.compile(
        r"GNU General Public License|Free Software Foundation", re.I)),
]

CODE_LINE = re.compile(
    r"^\s*(#include\b|#define\b|static\b|struct\b|switch\b|case\b|"
    r"return\b.*;|[^=<>!]+=[^=].*;|.*[;{}]\s*$)")

NETWORKISH_TOOLS = {"WebFetch", "WebSearch", "Bash"}


def walk(node, tool_uses, results):
    """Recursively collect tool_use dicts and (tool_use_id, text) results."""
    if isinstance(node, dict):
        if node.get("type") == "tool_use":
            tool_uses.append(node)
        elif node.get("type") == "tool_result":
            texts = []
            def grab(x):
                if isinstance(x, str):
                    texts.append(x)
                elif isinstance(x, dict):
                    for v in x.values():
                        grab(v)
                elif isinstance(x, list):
                    for v in x:
                        grab(v)
            grab(node.get("content"))
            results.append((node.get("tool_use_id"), "\n".join(texts)))
            return
        for v in node.values():
            walk(v, tool_uses, results)
    elif isinstance(node, list):
        for v in node:
            walk(v, tool_uses, results)


def code_density(text):
    return sum(1 for line in text.splitlines() if CODE_LINE.match(line))


def audit_file(path, pol, min_code_lines):
    findings = []
    id_to_tool = {}
    with open(path, encoding="utf-8", errors="replace") as f:
        for lineno, raw in enumerate(f, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except Exception:
                continue
            tool_uses, results = [], []
            walk(obj, tool_uses, results)
            for tu in tool_uses:
                name = tu.get("name", "?")
                if tu.get("id"):
                    id_to_tool[tu["id"]] = name
                tool_input = tu.get("input")
                if not isinstance(tool_input, dict):
                    tool_input = {}
                target, hit = pick_target(name, tool_input, pol)
                if hit:
                    findings.append(
                        (lineno, "tool-target",
                         f"{name} matched '{hit}' (target: {target[:120]})"))
            for use_id, text in results:
                if not text:
                    continue
                tool = id_to_tool.get(use_id, "?")
                for label, rx in LICENSE_MARKERS:
                    n = len(rx.findall(text))
                    if n:
                        findings.append(
                            (lineno, "license-marker",
                             f"{label} x{n} in {tool} result"))
                if tool in NETWORKISH_TOOLS or "fetch" in tool.lower():
                    dens = code_density(text)
                    if dens >= min_code_lines:
                        findings.append(
                            (lineno, "code-payload",
                             f"{dens} code-shaped lines in {tool} result"))
    return findings


def hook_log_summary(pol):
    path = pol.get("log_file", DEFAULT_POLICY["log_file"])
    if not os.path.isabs(path):
        path = os.path.join(project_dir(), path)
    if not os.path.isfile(path):
        return None
    blocked = allowed = 0
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                e = json.loads(line)
            except Exception:
                continue
            if e.get("action") == "blocked":
                blocked += 1
            elif e.get("action") == "allowed-role":
                allowed += 1
    return path, blocked, allowed


def main():
    ap = argparse.ArgumentParser(
        description="Audit clean-room implementation session transcripts.")
    ap.add_argument("transcripts", nargs="+", help="session JSONL file(s)")
    ap.add_argument("--policy", help="cleanroom-policy.json "
                    "(default: same resolution as the hook)")
    ap.add_argument("--out", help="also write the report to this file")
    ap.add_argument("--min-code-lines", type=int, default=20,
                    help="code-shaped-line threshold for network payloads "
                         "(default 20)")
    args = ap.parse_args()

    if args.policy:
        os.environ["CLEANROOM_POLICY"] = args.policy
    pol = load_policy()

    lines = ["session_audit report",
             f"  transcripts: {', '.join(args.transcripts)}",
             f"  min-code-lines: {args.min_code_lines}"]
    total = 0
    for path in args.transcripts:
        if not os.path.isfile(path):
            print(f"session_audit: error: no such transcript: {path}",
                  file=sys.stderr)
            sys.exit(2)
        findings = audit_file(path, pol, args.min_code_lines)
        total += len(findings)
        lines.append(f"\n== {path} ==")
        lines.append(f"{len(findings)} finding(s)")
        for lineno, kind, detail in findings:
            lines.append(f"  - L{lineno} [{kind}] {detail}")

    summary = hook_log_summary(pol)
    if summary:
        lp, blocked, allowed = summary
        lines.append(f"\nhook log ({lp}): {blocked} blocked, "
                     f"{allowed} allowed-role")
        if blocked:
            lines.append("  note: blocked attempts are enforcement working; "
                         "verify no successful alternate route above")

    verdict = "clean" if total == 0 else "FINDINGS - contaminated session(s)"
    lines.append(f"\nverdict: {verdict}")
    if total:
        lines.append("response: discard the session's diff wholesale, add a "
                     "ledger line, regenerate from the spec in a fresh "
                     "restricted session")
    lines.append("ledger line: <date> | <device> | session-audit: "
                 "<session-id> | " + ("clean" if total == 0 else "FINDINGS")
                 + " | <report path>")

    report = "\n".join(lines)
    print(report)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report + "\n")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
