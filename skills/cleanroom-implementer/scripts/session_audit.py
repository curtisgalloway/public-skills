#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Curtis Galloway
# SPDX-License-Identifier: Apache-2.0
"""
session_audit.py - post-session transcript audit for clean-room
implementation sessions (the detection layer behind the hook).

Scans agent session records for evidence that encumbered source entered the
context, regardless of route. Point it at any of:

  Gemini CLI    ~/.gemini/tmp/<project_hash>/chats/*.jsonl
                (or the `transcript_path` handed to a hook event)
  Antigravity   ~/.gemini/antigravity/brain/<GUID>/          (task artifacts:
                implementation plans, walkthroughs - pass the directory)
                plus any conversation .db from the CLI's store
  Claude Code   ~/.claude/projects/<slug>/<session>.jsonl

Format is sniffed, not assumed: SQLite, JSONL, single-document JSON, and
plain text/markdown all work, and a directory is walked recursively.

Four checks:

  1. TOOL TARGETS - every tool call in the record is checked against the
     same clean-room policy the hook enforces (paths, checkout roots,
     kernel-mirror URLs, shell commands). Catches sessions that ran without
     the hook, harnesses that do not run hooks at all (the Antigravity IDE
     does not), and MCP side channels. Tool-call shapes understood:
     `functionCall`/`functionResponse` parts and `toolCalls[]` entries
     (Gemini CLI / Antigravity), `tool_use`/`tool_result` blocks (Claude
     Code), and raw `tool_name`/`tool_input` hook payloads.
  2. LICENSE MARKERS - tool-result and artifact text is scanned for
     GPL/kernel markers (SPDX GPL tags, MODULE_LICENSE, EXPORT_SYMBOL,
     '#include <linux/', GPL boilerplate). A marker in ANY result is
     high-signal that source text arrived, whatever fetched it.
  3. CODE-SHAPED NETWORK PAYLOADS - results of network/shell tools with a
     high density of C-shaped lines. (Workspace file reads are exempt:
     reading the target OS tree is legitimate and full of C. Text artifacts
     are exempt too - a walkthrough quotes the driver the agent just wrote.)
  4. HOOK LOG - if the policy's hook log exists, blocked/allowed-role
     counts are summarized for cross-reference (info, not findings).

The report cites record/line numbers, tool names, pattern/marker names and
counts - it never reproduces fetched content. Exit 0 = clean, 1 = findings,
2 = error.

Usage:
  python3 session_audit.py SESSION [...] [--policy FILE] [--out FILE]
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

# Tools that can pull bytes in from outside the workspace, per harness:
# Gemini CLI, Antigravity, Claude Code. Anything with "fetch" in the name
# counts too (MCP fetchers).
NETWORKISH_TOOLS = {
    "web_fetch", "google_web_search", "run_shell_command",
    "read_url_content", "search_web", "run_command", "run_terminal_command",
    "WebFetch", "WebSearch", "Bash",
}

TEXT_SUFFIXES = {".md", ".txt", ".log", ".patch", ".diff", ".html"}
SQLITE_MAGIC = b"SQLite format 3\x00"


def _tool_input_of(node):
    for key in ("input", "args", "arguments", "tool_input", "toolInput",
                "parameters"):
        val = node.get(key)
        if isinstance(val, dict):
            return val
    return {}


def _result_of(node):
    for key in ("result", "response", "output", "tool_response",
                "toolResponse", "resultDisplay", "content"):
        if key in node:
            return node[key]
    return None


def _flatten(node, out):
    """Collect every string leaf under `node` into `out`."""
    if isinstance(node, str):
        out.append(node)
    elif isinstance(node, dict):
        for val in node.values():
            _flatten(val, out)
    elif isinstance(node, (list, tuple)):
        for val in node:
            _flatten(val, out)


def _text_of(node):
    out = []
    _flatten(node, out)
    return "\n".join(out)


def walk(node, tool_uses, results):
    """Collect tool calls and (correlation-key, result-text) pairs.

    tool_uses entries are {"name", "input", "id"}. Correlation keys are the
    tool-call id where the format has one (Claude Code) and the tool name
    where the result is carried inside the call itself (Gemini CLI's
    toolCalls[], Antigravity artifacts, functionResponse parts).
    """
    if isinstance(node, dict):
        # Claude Code content blocks.
        if node.get("type") == "tool_use":
            tool_uses.append({"name": node.get("name", "?"),
                              "input": _tool_input_of(node),
                              "id": node.get("id")})
            return
        if node.get("type") == "tool_result":
            results.append((node.get("tool_use_id"),
                            _text_of(node.get("content"))))
            return
        # Gemini / Antigravity function-call parts.
        call = node.get("functionCall") or node.get("function_call")
        if isinstance(call, dict):
            name = call.get("name", "?")
            tool_uses.append({"name": name, "input": _tool_input_of(call),
                              "id": call.get("id")})
            res = _result_of(call)
            if res is not None:
                results.append((call.get("id") or name, _text_of(res)))
            return
        resp = node.get("functionResponse") or node.get("function_response")
        if isinstance(resp, dict):
            results.append((resp.get("id") or resp.get("name"),
                            _text_of(_result_of(resp) or resp)))
            return
        # Gemini CLI toolCalls[] records and raw hook payloads: the call and
        # its result live in one object.
        name = None
        for key in ("tool_name", "toolName"):
            if isinstance(node.get(key), str):
                name = node[key]
                break
        if name is None and isinstance(node.get("name"), str) and (
                any(k in node for k in ("args", "input", "tool_input",
                                        "toolInput", "arguments"))):
            name = node["name"]
        if name:
            tool_uses.append({"name": name, "input": _tool_input_of(node),
                              "id": node.get("id") or node.get("callId")})
            res = _result_of(node)
            if res is not None:
                results.append((node.get("id") or node.get("callId") or name,
                                _text_of(res)))
            # fall through: nested structures may hold further calls
        for val in node.values():
            walk(val, tool_uses, results)
    elif isinstance(node, list):
        for val in node:
            walk(val, tool_uses, results)


def code_density(text):
    return sum(1 for line in text.splitlines() if CODE_LINE.match(line))


def scan_records(records, pol, min_code_lines):
    """Audit an iterable of (record_number, parsed_json) pairs."""
    findings = []
    id_to_tool = {}
    for lineno, obj in records:
        tool_uses, results = [], []
        walk(obj, tool_uses, results)
        for tu in tool_uses:
            name = tu["name"]
            if tu.get("id"):
                id_to_tool[tu["id"]] = name
            target, hit = pick_target(name, tu["input"], pol)
            if hit:
                findings.append(
                    (lineno, "tool-target",
                     f"{name} matched '{hit}' (target: {target[:120]})"))
        for key, text in results:
            if not text:
                continue
            tool = id_to_tool.get(key) or (key if isinstance(key, str)
                                           else None) or "?"
            findings.extend(scan_text(text, tool, lineno, min_code_lines))
    return findings


def scan_text(text, tool, lineno, min_code_lines, allow_density=True):
    """License markers always; code density only for network/shell results."""
    findings = []
    for label, rx in LICENSE_MARKERS:
        n = len(rx.findall(text))
        if n:
            findings.append((lineno, "license-marker",
                             f"{label} x{n} in {tool} result"))
    if allow_density and (tool in NETWORKISH_TOOLS or "fetch" in tool.lower()):
        dens = code_density(text)
        if dens >= min_code_lines:
            findings.append((lineno, "code-payload",
                             f"{dens} code-shaped lines in {tool} result"))
    return findings


def sniff(path):
    """Return 'sqlite', 'jsonl', 'json' or 'text'."""
    try:
        with open(path, "rb") as f:
            head = f.read(len(SQLITE_MAGIC))
        if head == SQLITE_MAGIC:
            return "sqlite"
    except Exception:
        return "text"
    if os.path.splitext(path)[1].lower() in TEXT_SUFFIXES:
        return "text"
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    json.loads(raw)
                    return "jsonl"
                except Exception:
                    break
        with open(path, encoding="utf-8", errors="replace") as f:
            json.load(f)
        return "json"
    except Exception:
        return "text"


def audit_jsonl(path, pol, min_code_lines):
    def records():
        with open(path, encoding="utf-8", errors="replace") as f:
            for lineno, raw in enumerate(f, 1):
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    yield lineno, json.loads(raw)
                except Exception:
                    continue
    return scan_records(records(), pol, min_code_lines)


def audit_json(path, pol, min_code_lines):
    with open(path, encoding="utf-8", errors="replace") as f:
        obj = json.load(f)
    items = obj if isinstance(obj, list) else [obj]
    return scan_records(enumerate(items, 1), pol, min_code_lines)


def audit_sqlite(path, pol, min_code_lines):
    """Antigravity keeps conversations in SQLite; the schema is not public.

    Every text cell is therefore treated as a candidate record: parsed as
    JSON when it parses (so embedded tool calls are checked properly) and
    scanned as text when it does not.
    """
    import sqlite3
    findings = []
    uri = "file:" + path.replace("?", "%3f").replace("#", "%23") + \
          "?mode=ro&immutable=1"
    con = sqlite3.connect(uri, uri=True)
    try:
        con.text_factory = lambda b: b.decode("utf-8", "replace")
        tables = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table','view')")]
        for table in tables:
            try:
                rows = con.execute(f'SELECT * FROM "{table}"')
            except Exception:
                continue
            for rowno, row in enumerate(rows, 1):
                where = f"{table}:{rowno}"
                for cell in row:
                    if not isinstance(cell, str) or not cell.strip():
                        continue
                    parsed = None
                    try:
                        parsed = json.loads(cell)
                    except Exception:
                        pass
                    if isinstance(parsed, (dict, list)):
                        findings.extend(
                            scan_records([(where, parsed)], pol,
                                         min_code_lines))
                    else:
                        findings.extend(
                            scan_text(cell, "sqlite-cell", where,
                                      min_code_lines, allow_density=False))
    finally:
        con.close()
    return findings


def audit_text(path, pol, min_code_lines):
    """Artifacts (plans, walkthroughs, logs): license markers only.

    No code-density check here: an implementation plan or walkthrough
    legitimately quotes the driver the agent just wrote.
    """
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    return scan_text(text, "artifact", 1, min_code_lines, allow_density=False)


AUDITORS = {"sqlite": audit_sqlite, "jsonl": audit_jsonl,
            "json": audit_json, "text": audit_text}


def expand(paths):
    """Files stay; directories expand to their files, recursively."""
    out = []
    for path in paths:
        if os.path.isdir(path):
            for root, _dirs, names in os.walk(path):
                for name in sorted(names):
                    out.append(os.path.join(root, name))
        else:
            out.append(path)
    return out


def audit_file(path, pol, min_code_lines):
    """Audit one record file, dispatching on its sniffed format."""
    return AUDITORS[sniff(path)](path, pol, min_code_lines)


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
        description="Audit clean-room implementation session records "
                    "(Gemini CLI, Antigravity, Claude Code).")
    ap.add_argument("transcripts", nargs="+",
                    help="session transcript(s), artifact directory, or "
                         "conversation database")
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

    for path in args.transcripts:
        if not os.path.exists(path):
            print(f"session_audit: error: no such transcript: {path}",
                  file=sys.stderr)
            sys.exit(2)

    lines = ["session_audit report",
             f"  transcripts: {', '.join(args.transcripts)}",
             f"  min-code-lines: {args.min_code_lines}"]
    total = 0
    for path in expand(args.transcripts):
        try:
            findings = audit_file(path, pol, args.min_code_lines)
        except Exception as exc:
            lines.append(f"\n== {path} ==")
            lines.append(f"  ! unreadable ({type(exc).__name__}) - "
                         f"audit this file by hand")
            total += 1
            continue
        total += len(findings)
        lines.append(f"\n== {path} ({sniff(path)}) ==")
        lines.append(f"{len(findings)} finding(s)")
        for lineno, kind, detail in findings:
            where = f"L{lineno}" if isinstance(lineno, int) else str(lineno)
            lines.append(f"  - {where} [{kind}] {detail}")

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
