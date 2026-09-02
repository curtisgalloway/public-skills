#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""round_text.py - build the text of one review round from a repo Markdown file.

The repo file is the source of truth; the Google Doc is only the review
surface. This strips what belongs to the repo and not to the reviewer (a
leading license/SPDX HTML comment, any `**DRAFT.**` marker line) and, for
rounds after r1, prepends the Doc-only "What changed since r<N-1>" section
followed by a horizontal rule. Stdlib only, Python 3.9+.

Usage:
  round_text.py DOC.md --out round.txt
  round_text.py DOC.md --changed changed.md --round 2 --out round.txt

`changed.md` holds the What-changed bullets. If it already opens with a
`## ` heading that heading is kept; otherwise `--round N` supplies the N in
`## What changed since r<N-1>`. Without --out the text goes to stdout.
"""
import argparse
import re
import sys

LEADING_COMMENT = re.compile(r"\A\s*<!--.*?-->[ \t]*\n?", re.S)
DRAFT_LINE = re.compile(r"^[ \t]*\*\*DRAFT\.\*\*.*(?:\n|\Z)", re.M)


def strip_repo_only(text):
    """Drop the leading HTML comment block and every **DRAFT.** marker line."""
    text = text.lstrip("\ufeff")
    text = LEADING_COMMENT.sub("", text, count=1)
    text = DRAFT_LINE.sub("", text)
    return text.lstrip("\n")


def what_changed(body, round_no):
    """The Doc-only reply section, closed by a rule. Never enters the repo file."""
    body = body.strip()
    if not body:
        raise SystemExit("round_text: --changed file is empty")
    if not body.startswith("## "):
        if round_no is None or round_no < 2:
            raise SystemExit("round_text: --changed without a heading needs "
                             "--round N (N >= 2) to name the previous round")
        body = f"## What changed since r{round_no - 1}\n\n{body}"
    return body + "\n\n---\n\n"


def build(source_text, changed_text=None, round_no=None):
    text = strip_repo_only(source_text)
    if changed_text is not None:
        text = what_changed(changed_text, round_no) + text
    return text if text.endswith("\n") else text + "\n"


def main():
    ap = argparse.ArgumentParser(
        description="Build the text of one Google Doc review round from a "
                    "repo Markdown file.")
    ap.add_argument("source", help="the repo Markdown file (source of truth)")
    ap.add_argument("--changed", metavar="FILE",
                    help="What-changed bullets to prepend (rounds after r1)")
    ap.add_argument("--round", type=int, metavar="N",
                    help="round being published; names r<N-1> in the heading")
    ap.add_argument("--out", metavar="FILE",
                    help="write here (default: stdout)")
    args = ap.parse_args()

    with open(args.source, encoding="utf-8") as f:
        source = f.read()
    changed = None
    if args.changed:
        with open(args.changed, encoding="utf-8") as f:
            changed = f.read()

    text = build(source, changed, args.round)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        first = text.splitlines()[0] if text.strip() else ""
        print(f"round_text: wrote {len(text.encode('utf-8'))} bytes to "
              f"{args.out}; first line: {first!r}", file=sys.stderr)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
