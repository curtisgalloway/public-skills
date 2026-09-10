#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""round_text.py - build the text of one review round from a repo Markdown file.

The repo file is the source of truth; the Google Doc is only the review
surface. This strips what belongs to the repo and not to the reviewer (a
leading license/SPDX HTML comment, any `**DRAFT.**` marker line) and, for
rounds after r1, prepends the Doc-only "What changed since r<N-1>" section
followed by a horizontal rule. Every round opens with a Doc-only header
line, `# <Title> -- <date> r<N>`, the Doc's own title without its bracketed
status, so the reviewer can tell which document and which round they have
open (--no-header omits it). Under it sits a Doc-only "Review status" block
-- two boxes (Reviewed with comments / Approved as-is) plus a Comments label
-- that the reviewer ticks to sign off; no box ticked is the default and
means the review is still in progress. --no-status omits the block. A round that needs the reviewer to choose between alternatives also
carries a Doc-only "Decisions needed" block (--decisions). Stdlib only,
Python 3.9+.

Usage:
  round_text.py DOC.md --out round.txt
  round_text.py DOC.md --changed changed.md --round 2 --out round.txt
  round_text.py DOC.md --decisions decisions.md --out round.txt

`changed.md` holds the What-changed bullets. If it already opens with a
`## ` heading that heading is kept; otherwise `--round N` supplies the N in
`## What changed since r<N-1>`. Without --out the text goes to stdout.

`decisions.md` holds one question line per decision, each followed by its
alternatives as `- [ ] ` checkboxes, one per line -- Docs only renders a
checkbox for a line that starts a list item, so alternatives cannot share a
line. Mark the one you recommend `Recommended: <choice>` and put it first,
end each set with an `Other: ` escape hatch, and capitalize every
alternative the same way (a reviewer flagged `decline` next to
`Recommended: ...` as a nit on 2026-09-10):

    Which flavor for the launch?

    - [ ] Recommended: Vanilla
    - [ ] Chocolate
    - [ ] Other:

The header takes its title from the source file's first `# ` heading and
its date from the first YYYY-MM-DD in the source filename; --title and
--date override either, and --round (default 1) supplies the N.
"""
import argparse
import re
import sys

LEADING_COMMENT = re.compile(r"\A\s*<!--.*?-->[ \t]*\n?", re.S)
DRAFT_LINE = re.compile(r"^[ \t]*\*\*DRAFT\.\*\*.*(?:\n|\Z)", re.M)
H1 = re.compile(r"^#[ \t]+(.+?)[ \t]*#*[ \t]*$", re.M)
FILE_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")

# The reviewer's sign-off block, at the top of every round. Doc-only:
# doc_diff.py splits it off the read-back and reports which box is ticked.
# Docs' Markdown import turns "- [ ]" into a real clickable checklist and
# exports it back the same way, so the reviewer ticks a box instead of
# editing text (verified 2026-09-08). The rules above and below it are what
# separate it from the round's own content. There is no "In progress" box:
# an untouched block already says that, and a box for the default state
# only invites a reviewer to tick it and then forget to change it.
REVIEW_STATUS = (
    "---\n\n"
    "**Review status:**\n\n"
    "- [ ] Reviewed with comments\n"
    "- [ ] Approved as-is\n\n"
    "**Comments:**\n\n"
    "---\n\n"
)

DECISIONS_HEAD = "**Decisions needed:**"
BOX_LINE = re.compile(r"^[-*+]\s*\[([ xX])\]\s*(.*)$")


def header(source_text, source_name=None, title=None, date=None, round_no=None):
    """The Doc-only header line: the Doc's title without its bracketed status.

    `# <Title> -- <date> r<N>`, so a reviewer with the Doc open (or a copy
    of it, or a printout) can tell which document and which round it is
    without looking at the Drive listing. Title from the source's first H1
    and date from its filename unless given; both are required, because a
    header missing either would name nothing.
    """
    if title is None:
        m = H1.search(strip_repo_only(source_text))
        if not m:
            raise SystemExit("round_text: no '# ' heading in the source to take "
                             "the title from; pass --title (or --no-header)")
        title = m.group(1).strip()
    if date is None:
        m = FILE_DATE.search(source_name or "")
        if not m:
            raise SystemExit("round_text: no YYYY-MM-DD in the source filename "
                             "to take the date from; pass --date (or --no-header)")
        date = m.group(0)
    return f"# {title} \u2014 {date} r{round_no or 1}\n\n"


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


def decisions(body, warn=sys.stderr):
    """The Doc-only 'Decisions needed' block, closed by a rule.

    `body` is one question line per decision, each followed by its
    alternatives as `- [ ] ` lines. Every alternative is its own line
    because Docs renders a checkbox only for a line that opens a list item.
    A pre-ticked box is refused: the tick is the reviewer's answer, and one
    written here would read back as a decision they never made.
    """
    body = body.strip()
    if not body:
        raise SystemExit("round_text: --decisions file is empty")
    if not body.startswith(DECISIONS_HEAD):
        body = f"{DECISIONS_HEAD}\n\n{body}"

    groups = []                       # [(question, [alternatives])]
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(DECISIONS_HEAD):
            continue
        box = BOX_LINE.match(stripped)
        if box:
            if box.group(1).lower() == "x":
                raise SystemExit(
                    f"round_text: --decisions pre-ticks a box ({stripped!r}); "
                    "the reviewer ticks it, not you")
            if not groups:
                raise SystemExit(
                    f"round_text: --decisions opens with an alternative "
                    f"({stripped!r}); each set needs a question line first")
            groups[-1][1].append(box.group(2).strip())
        else:
            groups.append((stripped, []))
    for question, alts in groups:
        label = question if len(question) < 60 else question[:57] + "..."
        if len(alts) < 2:
            raise SystemExit(f"round_text: decision {label!r} has "
                             f"{len(alts)} alternative(s); it needs at least 2")
        if not alts[0].lower().startswith("recommended"):
            print(f"round_text: warning: decision {label!r} does not put a "
                  "'Recommended: ' alternative first", file=warn)
        if not any(a.lower().startswith("other") for a in alts):
            print(f"round_text: warning: decision {label!r} has no "
                  "'Other: ' escape hatch", file=warn)
    if not groups:
        raise SystemExit("round_text: --decisions file has no decisions")
    return body + "\n\n---\n\n"


def build(source_text, changed_text=None, round_no=None, status=True,
          decisions_text=None, header_line=True, source_name=None, title=None,
          date=None):
    """Header, status block, decisions, the Doc-only reply, then the document."""
    text = strip_repo_only(source_text)
    if changed_text is not None:
        text = what_changed(changed_text, round_no) + text
    if decisions_text is not None:
        text = decisions(decisions_text) + text
    if status:
        text = REVIEW_STATUS + text
    if header_line:
        text = header(source_text, source_name, title, date, round_no) + text
    if not text.endswith("\n"):
        text += "\n"
    return text


def main():
    ap = argparse.ArgumentParser(
        description="Build the text of one Google Doc review round from a "
                    "repo Markdown file.")
    ap.add_argument("source", help="the repo Markdown file (source of truth)")
    ap.add_argument("--changed", metavar="FILE",
                    help="What-changed bullets to prepend (rounds after r1)")
    ap.add_argument("--round", type=int, metavar="N",
                    help="round being published; names r<N-1> in the heading")
    ap.add_argument("--decisions", metavar="FILE",
                    help="question + checkbox alternatives for each decision "
                         "the reviewer has to make this round")
    ap.add_argument("--out", metavar="FILE",
                    help="write here (default: stdout)")
    ap.add_argument("--no-status", action="store_true",
                    help="omit the leading Review status sign-off block")
    ap.add_argument("--title", metavar="TEXT",
                    help="document title for the header line (default: the "
                         "source's first '# ' heading)")
    ap.add_argument("--date", metavar="YYYY-MM-DD",
                    help="document date for the header line (default: the "
                         "first date in the source filename)")
    ap.add_argument("--no-header", action="store_true",
                    help="omit the leading '# <Title> -- <date> r<N>' line")
    args = ap.parse_args()

    with open(args.source, encoding="utf-8") as f:
        source = f.read()
    changed = None
    if args.changed:
        with open(args.changed, encoding="utf-8") as f:
            changed = f.read()
    decisions_text = None
    if args.decisions:
        with open(args.decisions, encoding="utf-8") as f:
            decisions_text = f.read()

    text = build(source, changed, args.round, status=not args.no_status,
                 decisions_text=decisions_text, header_line=not args.no_header,
                 source_name=args.source, title=args.title, date=args.date)
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
