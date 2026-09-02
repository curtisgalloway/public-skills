#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Curtis Galloway
# SPDX-License-Identifier: Apache-2.0
"""
portability_scan.py - flag harness lock-in in a skill directory.

Portability bugs do not raise. A skills path that doesn't exist falls
through, a tool-name table that matches nothing returns an empty dict, a
hook wired to an event the harness never fires simply never runs. The
symptom is silence, which is why a mechanical pass is worth having: it finds
the assumptions you can't see failing.

The core heuristic is LADDER vs CONSTANT. One harness's path, variable or
tool vocabulary appearing alone is lock-in. The same names appearing
alongside another harness's are a resolution ladder or a translation table,
which is the pattern this skill is arguing for - so they pass. Checks:

  single-harness-path   a harness config/skills directory named where no
                        other harness is named in the file
  single-harness-env    $CLAUDE_PROJECT_DIR / $GEMINI_PROJECT_DIR and friends
                        with no alternative in sight
  brand-context-file    CLAUDE.md / GEMINI.md without AGENTS.md nearby - the
                        harness-specific file overrides the portable one, so
                        naming only the override strands every other agent
  tool-name-table       three or more brand tool names from a single harness
                        quoted in code, which is the signature of keying
                        logic on tool names instead of argument names
  absolute-home-path    /home/<user>/ or /Users/<user>/ - unportable, and
                        this repo's AGENTS.md forbids it for privacy anyway

A finding is a prompt to look, not a verdict: a skill that is deliberately
harness-specific (one that reads Claude Code's transcripts, say) will light
up, and that is correct. Two opt-outs, both of which want a reason next to
them: `portability-ok` on a line, or `portability-scan: intentional` anywhere
in the file for one that is single-harness by design.

Exit 0 clean / 1 findings / 2 error.

Usage:
  python3 portability_scan.py PATH [...] [--allow PATTERN] [--quiet]
"""

import argparse
import os
import re
import sys

# A harness "family" is a set of surface names that all belong to one agent.
# Naming two or more families in a file is the signal that the author is
# translating rather than assuming.
FAMILY_MARKERS = {
    "claude-code": [
        re.compile(r"\.claude\b"),
        re.compile(r"CLAUDE_PROJECT_DIR"),
        re.compile(r"\bCLAUDE\.md\b"),
    ],
    "gemini-cli": [
        # Not ~/.gemini/antigravity - that directory is Antigravity's, and
        # counting it here would let an Antigravity-only file masquerade as
        # a two-harness ladder.
        re.compile(r"\.gemini\b(?![/\\]antigravity)"),
        re.compile(r"GEMINI_PROJECT_DIR"),
        re.compile(r"\bGEMINI\.md\b"),
    ],
    "antigravity": [
        re.compile(r"\.agents?[/\\]"),
        re.compile(r"antigravity", re.I),
        re.compile(r"\bAGENTS\.md\b"),
        re.compile(r"workspacePaths"),
        re.compile(r"\bagy\b"),
    ],
}

# Prose counts as naming a harness: a doc that says "Claude Code" while
# showing an Antigravity path is translating for the reader, which is the
# behaviour this check is looking for.
FAMILY_MARKERS["claude-code"].append(re.compile(r"\bClaude Code\b"))
FAMILY_MARKERS["gemini-cli"].append(re.compile(r"\bGemini CLI\b"))

PATH_MARKERS = {
    "claude-code": re.compile(r"[~$\w/\\.]*\.claude[/\\][\w*/\\.-]*"),
    "gemini-cli": re.compile(r"[~$\w/\\.]*\.gemini[/\\](?!antigravity)[\w*/\\.-]*"),
    "antigravity": re.compile(r"[~$\w/\\.]*\.agents?[/\\][\w*/\\.-]*"),
}

ENV_MARKERS = {
    "CLAUDE_PROJECT_DIR": ("claude-code",
                           re.compile(r"\bCLAUDE_PROJECT_DIR\b")),
    "GEMINI_PROJECT_DIR": ("gemini-cli",
                           re.compile(r"\bGEMINI_PROJECT_DIR\b")),
}

CONTEXT_FILE = re.compile(r"\b(CLAUDE|GEMINI)\.md\b")
AGENTS_FILE = re.compile(r"\bAGENTS\.md\b")

# Brand tool names, by the harness that ships them. Names shared by more
# than one harness are listed under each, so a shared vocabulary counts as
# portable rather than as lock-in.
BRAND_TOOLS = {
    "claude-code": {"Read", "Write", "Edit", "MultiEdit", "Bash", "Grep",
                    "Glob", "WebFetch", "WebSearch", "NotebookEdit", "Task"},
    "gemini-cli": {"read_file", "write_file", "replace", "run_shell_command",
                   "web_fetch", "google_web_search", "glob",
                   "search_file_content", "grep_search", "read_many_files",
                   "list_directory"},
    "antigravity": {"read_file", "write_file", "view_file", "edit_file",
                    "run_command", "grep_search", "codebase_search",
                    "list_dir", "read_url_content", "search_web",
                    "invoke_subagent"},
}
QUOTED = re.compile(r"""['"]([A-Za-z_][A-Za-z0-9_]{1,31})['"]""")

# Conventional placeholder accounts - the thing this check wants you to use.
PLACEHOLDER_USERS = {"dev", "user", "username", "me", "you", "example",
                     "alice", "bob", "test", "someone", "youruser", "name"}
HOME_PATH = re.compile(r"/(?:home|Users)/(?!<)([A-Za-z0-9._-]+)/")

# Per-line opt-out, and a file-level one for a file that is single-harness on
# purpose (a per-harness install asset, a transcript reader). Put the
# file-level marker in a comment - an HTML comment in Markdown, so readers
# never see it - and say why in the same breath.
SUPPRESS = re.compile(r"portability-ok")
FILE_SUPPRESS = re.compile(r"portability-scan:\s*intentional")

CODE_SUFFIXES = {".py", ".js", ".ts", ".sh", ".rs", ".go"}
TEXT_SUFFIXES = {".md", ".json", ".toml", ".yaml", ".yml", ".txt"}
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "fixtures"}


def families_in(text):
    """Which harnesses does this file mention at all?"""
    found = set()
    for family, patterns in FAMILY_MARKERS.items():
        if any(p.search(text) for p in patterns):
            found.add(family)
    return found


def tool_families_in(text):
    """Which harnesses' tool vocabularies appear as quoted strings?"""
    quoted = set(QUOTED.findall(text))
    return {fam: quoted & tools for fam, tools in BRAND_TOOLS.items()
            if quoted & tools}


def scan_file(path, allow):
    findings = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except Exception:
        return findings
    if any(a in text for a in allow):
        return findings

    breadth = families_in(text)
    is_ladder = len(breadth) >= 2 or bool(FILE_SUPPRESS.search(text))
    suffix = os.path.splitext(path)[1].lower()

    tool_hits = tool_families_in(text)
    # A vocabulary is lock-in only if it is one harness's alone. Shared names
    # (read_file, grep_search) resolve to several families and so never trip
    # this on their own.
    if suffix in CODE_SUFFIXES and len(tool_hits) == 1:
        family, names = next(iter(tool_hits.items()))
        if len(names) >= 3:
            findings.append((0, "tool-name-table",
                             f"{len(names)} {family} tool names quoted "
                             f"({', '.join(sorted(names)[:4])}...) - key on "
                             f"argument names instead"))

    for lineno, line in enumerate(text.splitlines(), 1):
        if SUPPRESS.search(line):
            continue
        stripped = line.strip()
        if not stripped:
            continue

        if not is_ladder:
            for family, rx in PATH_MARKERS.items():
                m = rx.search(line)
                if m:
                    findings.append((lineno, "single-harness-path",
                                     f"{family} path '{m.group(0)}' with no "
                                     f"other harness named in this file"))
                    break
            for var, (family, rx) in ENV_MARKERS.items():
                if rx.search(line):
                    findings.append((lineno, "single-harness-env",
                                     f"${var} ({family}) used without a "
                                     f"fallback ladder"))
                    break

        if suffix in TEXT_SUFFIXES:
            m = CONTEXT_FILE.search(line)
            if m and not AGENTS_FILE.search(text):
                findings.append((lineno, "brand-context-file",
                                 f"{m.group(0)} named but AGENTS.md is not - "
                                 f"the portable context file is the one to "
                                 f"lead with"))

        m = HOME_PATH.search(line)
        if m and m.group(1).lower() not in PLACEHOLDER_USERS:
            findings.append((lineno, "absolute-home-path",
                             f"'{m.group(0)}' - use ~ or a <placeholder>"))
    return findings


def walk(paths):
    for path in paths:
        if os.path.isfile(path):
            yield path
            continue
        for root, dirs, names in os.walk(path):
            dirs[:] = [d for d in sorted(dirs) if d not in SKIP_DIRS]
            for name in sorted(names):
                if os.path.splitext(name)[1].lower() in (
                        CODE_SUFFIXES | TEXT_SUFFIXES):
                    yield os.path.join(root, name)


def main():
    ap = argparse.ArgumentParser(
        description="Flag harness lock-in in a skill directory.")
    ap.add_argument("paths", nargs="+", help="skill directory or file(s)")
    ap.add_argument("--allow", action="append", default=[],
                    help="skip files containing this string (repeatable)")
    ap.add_argument("--quiet", action="store_true",
                    help="print findings only")
    args = ap.parse_args()

    for path in args.paths:
        if not os.path.exists(path):
            print(f"portability_scan: error: no such path: {path}",
                  file=sys.stderr)
            sys.exit(2)

    total = 0
    for path in walk(args.paths):
        findings = scan_file(path, args.allow)
        if not findings:
            continue
        total += len(findings)
        print(f"\n== {path} ==")
        for lineno, kind, detail in findings:
            where = f"L{lineno}" if lineno else "file"
            print(f"  - {where} [{kind}] {detail}")

    if not args.quiet:
        print(f"\n{total} finding(s)")
        if total:
            print("A finding is a prompt to look, not a verdict. Deliberate "
                  "single-harness code (a transcript reader, say) should say "
                  "so in its description; add `portability-ok` on the line "
                  "to silence it.")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
