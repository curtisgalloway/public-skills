#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""doc_diff.py - find a reviewer's direct edits in a Google Doc read-back.

Compares the repo Markdown against the text read back from the Doc after
normalizing both past the noise the Markdown -> Doc -> text round trip adds
(escaped underscores and heading numbers, dropped code spans, synthesized
table header and alignment rows with bolded cells, curly quotes, hard wraps,
fenced code blocks flattened to one paragraph per line with a stray language
tag on the opening fence, horizontal rules that come back as ----- , and the
inline <comment_start/end id=...> anchors). The Doc-only header line
(`# <Title> -- <date> r<N>`) and the "Review status" and "Decisions needed"
blocks at the top are split off and reported -- the round named, the ticked
boxes listed -- not diffed. What survives is the reviewer's work:
the comment threads in document order, every paragraph carrying a
`~~strikethrough~~` deletion, and a unified diff of paragraphs. Stdlib only,
Python 3.9+. Exit 0 when the two agree, 1 when they differ.

The repo side is hard-wrapped Markdown, so its paragraphs are blank-line
blocks. The read-back is never hard-wrapped (Docs joins wrapped lines) and
separates paragraphs with a single newline or a blank line depending on the
call that produced it, so every line of it is a paragraph.

Usage:
  doc_diff.py REPO.md READBACK.txt
  doc_diff.py --self-test
"""
import argparse
import difflib
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from round_text import strip_repo_only  # noqa: E402

ANCHOR = re.compile(r"<comment_(?:start|end) id=([^>\s]+)>")
ESCAPES = re.compile(r"\\([_*\[\]<>#|.&~])")
BLOCK_START = re.compile(r"^(#{1,6}\s|\||[-*+]\s|\d+[.)]\s|>|---\s*$)")
# A heading or a rule is a whole block by itself: it ends at its own line
# even when the next line follows without a blank line between.
BLOCK_WHOLE = re.compile(r"^(#{1,6}\s|---\s*$)")
CHARS = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"',
                       "\u201d": '"', "\u00a0": " "})
# A Markdown `---` rule comes back from Docs as `-----`; fold every width to
# one form so it stays a block boundary on both sides of the diff.
RULE = re.compile(r"^-{3,}\s*$")
# Docs imports "- [ ]" as a real checklist and exports the ticked state the
# same way. It strikes a ticked label through on screen, but that renders the
# checked state rather than formatting the run: the export carries [x] and no
# ~~ (checked 2026-09-08 in the Docs UI). Read the label past ~~ regardless,
# so a struck label and a clean one parse identically.
BOX = re.compile(r"^[-*+]\s*\[([ xX])\]\s*(.*)$")
STATUS_HEAD = re.compile(r"^\*{0,2}review status:?\*{0,2}$", re.I)
# The Doc-only header round_text.py puts above everything: the Doc's title
# without its bracketed status. Docs may hand the dash back as an em dash,
# an en dash or a hyphen run, so accept any of them.
ROUND_HEAD = re.compile(
    r"^#{1,6}\s+(?P<title>.+?)\s+(?:\u2014|\u2013|-{1,3})\s+"
    r"(?P<date>\d{4}-\d{2}-\d{2})\s+r(?P<round>\d+)\s*$")
COMMENTS_HEAD = re.compile(r"^\*{0,2}comments:?\*{0,2}$", re.I)
DECISIONS_HEAD = re.compile(r"^\*{0,2}decisions needed:?\*{0,2}$", re.I)
BOXES = ("Reviewed with comments", "Approved as-is")
# What each ticked box means for the loop; SKILL.md step 8 is the authority.
# No box ticked is the default and a state of its own - the review is still
# in progress - so there is no box for it.
ACTIONS = {
    "reviewed with comments": "apply the round, then publish the next one",
    "approved as-is": "close the review: commit the Markdown, retitle [CLOSED]",
}
NO_BOX = ("reviewer has not signed off - still in progress unless they said "
          "otherwise in chat, or the Doc carries comments (then treat it as "
          "'Reviewed with comments')")


def normalize(text):
    return normalize_line(strip_repo_only(text))


def normalize_line(text):
    return ESCAPES.sub(r"\1", text.translate(CHARS)).replace("`", "")


def paragraphs(text, hard_wrapped=True):
    """Split normalized text into paragraphs.

    With hard_wrapped=True (the repo Markdown) a paragraph is a blank-line
    block with its wrapped lines joined, split further at headings, table
    rows, list items and rules; a heading or rule never absorbs the line
    after it. With hard_wrapped=False (a Doc read-back) every non-blank line
    is its own paragraph, whichever separator the read-back used.

    Returns (paragraphs, threads). `threads` is one (anchor_id, first_index,
    last_index) per comment thread in document order, covering the
    paragraphs between its start and end anchors; the anchors themselves
    are stripped from the text.

    A fenced code block is one paragraph per line on both sides: the repo
    keeps its lines, and Docs flattens the block that way (tagging the
    opening fence with a language name such as "Unset"). The fences
    themselves are dropped."""
    paras, cur = [], []
    threads = {}
    fence = False

    def flush():
        if cur:
            joined = re.sub(r"\s+", " ", " ".join(cur)).strip()
            cur.clear()
            if joined:
                paras.append(joined)

    for raw in strip_repo_only(text).splitlines():
        if raw.strip().startswith("```"):
            fence = not fence
            flush()
            continue
        s = normalize_line(raw).strip()
        if not s:
            flush()
            continue
        if fence:
            paras.append(re.sub(r"\s+", " ", s))
            continue
        bare = ANCHOR.sub("", s).strip()
        if RULE.match(bare):
            bare = "---"
        if bare.startswith("|"):
            if not bare.strip("|:- \t"):       # alignment row or empty row
                continue
            bare = bare.replace("**", "")      # Docs bolds header cells
        if BLOCK_START.match(bare):
            flush()
        for cid in ANCHOR.findall(s):
            if cid in threads:
                threads[cid][1] = len(paras)
            else:
                threads[cid] = [len(paras), len(paras)]
        cur.append(bare)
        if not hard_wrapped or BLOCK_WHOLE.match(bare):
            flush()
    flush()
    return paras, [(cid, a, b) for cid, (a, b) in threads.items()]


def preamble_len(doc, repo):
    """Paragraphs of a Doc-only 'What changed' section, so it is not read as an insertion."""
    if doc and repo and doc[0].startswith("## What changed since"):
        if repo[0] in doc:
            return doc.index(repo[0])
        if "---" in doc:
            return doc.index("---") + 1
    return 0


def round_header(doc):
    """Split the Doc-only `# <Title> -- <date> r<N>` line off a read-back.

    Returns (paragraphs after it, header, dropped). `header` is
    {"title", "date", "round"} or empty when the read-back has no such line;
    `dropped` is 1 or 0. It is the first paragraph or nothing: a heading of
    that shape further down is the document's own."""
    if doc:
        m = ROUND_HEAD.match(doc[0].strip())
        if m:
            head = {"title": m.group("title").strip(), "date": m.group("date"),
                    "round": int(m.group("round"))}
            return doc[1:], head, 1
    return doc, {}, 0


def review_status(doc):
    """Split the leading Doc-only Review status block off a read-back.

    Returns (paragraphs after the block, status, dropped). `status` is
    {"boxes": [every label], "checked": [labels ticked], "comments": str,
     "closed": bool} and is empty when there is no block; `dropped` is how
    many leading paragraphs the block occupied, which the caller needs to
    keep comment-thread indices pointing at the right paragraph.

    The label is read past any ~~ markers, so a struck label and a clean one
    parse the same: Docs strikes ticked labels on screen but exports them
    without ~~, and nothing here depends on which shape arrives. Splitting
    the block off here -- before the caller scans for deletions -- is what
    keeps a struck label from being reported as a reviewer deletion: it is a
    checkbox, not an edit.

    The block runs to its closing rule. If the reviewer deleted that rule,
    it ends at the last checkbox or the Comments label instead and "closed"
    is False; anything they typed under Comments then falls through to the
    body diff, where it shows up as an insertion rather than being silently
    swallowed."""
    head = next((i for i, p in enumerate(doc[:6])
                 if STATUS_HEAD.match(p.strip())), None)
    if head is None:
        return doc, {}, 0

    boxes, checked, comments = [], [], []
    end, last_block, in_comments = None, head, False
    for j in range(head + 1, min(len(doc), head + 40)):
        para = doc[j].strip()
        if para == "---":
            end = j
            break
        box = BOX.match(para)
        if box and not in_comments:
            label = box.group(2).replace("~~", "").strip()
            boxes.append(label)
            if box.group(1).lower() == "x":
                checked.append(label)
            last_block = j
        elif COMMENTS_HEAD.match(para):
            in_comments = True
            last_block = j
        elif in_comments and para:
            comments.append(para)
    status = {"boxes": boxes, "checked": checked,
              "comments": " ".join(comments).strip(),
              "closed": end is not None}
    if end is None:                       # no closing rule: keep the body whole
        status["comments"] = ""
        end = last_block
    return doc[end + 1:], status, end + 1


def decisions(doc):
    """Split the leading Doc-only 'Decisions needed' block off a read-back.

    Returns (paragraphs after the block, items, dropped). Each item is
    {"question": str, "options": [label], "chosen": [label]}; `chosen` is
    what the reviewer ticked, and an empty one is an unanswered decision --
    the round is not finished with it. A ticked "Other: <text>" carries the
    text they typed in its label.

    Like the Review status block it runs to its closing rule; without one it
    ends at its last box, and whatever follows falls through to the body
    diff rather than being silently swallowed."""
    head = next((i for i, p in enumerate(doc[:6])
                 if DECISIONS_HEAD.match(p.strip())), None)
    if head is None:
        return doc, [], 0

    items, end, last_block = [], None, head
    for j in range(head + 1, len(doc)):
        para = doc[j].strip()
        if para == "---":
            end = j
            break
        box = BOX.match(para)
        if box:
            label = box.group(2).replace("~~", "").strip()
            if not items:
                items.append({"question": "(no question line)",
                              "options": [], "chosen": []})
            items[-1]["options"].append(label)
            if box.group(1).lower() == "x":
                items[-1]["chosen"].append(label)
            last_block = j
        elif para:
            items.append({"question": para, "options": [], "chosen": []})
            last_block = j
    if end is None:
        end = last_block
    return doc[end + 1:], items, end + 1


def report(repo_text, doc_text, out=sys.stdout):
    repo, _ = paragraphs(repo_text)
    doc, threads = paragraphs(doc_text, hard_wrapped=False)
    doc, head, dropped_head = round_header(doc)
    doc, status, dropped_status = review_status(doc)
    doc, chosen, dropped_dec = decisions(doc)
    after_status = dropped_head + dropped_status   # the header rides above the block
    dropped = after_status + dropped_dec
    pre = preamble_len(doc, repo)
    doc = doc[pre:]
    skip = dropped + pre                  # Doc-only paragraphs ahead of the body
    if head:
        print(f"== round ==\n  {head['title']} \u2014 {head['date']} "
              f"r{head['round']}", file=out)
    else:
        print("== round ==\n  ! no '# <Title> \u2014 <date> r<N>' header "
              "line in this read-back", file=out)
    if status:
        print("== review status ==", file=out)
        checked = status["checked"]
        print(f"  checked: {', '.join(checked) if checked else '(none)'}",
              file=out)
        print(f"  comments: {status['comments'] or '(empty)'}", file=out)
        for label in checked:
            action = ACTIONS.get(label.lower())
            if action:
                print(f"  action: {action}", file=out)
        if not checked:
            print(f"  action: {NO_BOX}", file=out)
        if len(checked) > 1:
            print("  ! more than one box ticked - ask the reviewer", file=out)
        if tuple(status["boxes"]) != BOXES:
            print(f"  ! boxes are not the standard three: "
                  f"{status['boxes'] or '(none found)'}", file=out)
        if not status["closed"]:
            print("  ! block has no closing rule; anything typed under "
                  "Comments will show in the diff below", file=out)
    elif dropped_status == 0:
        print("== review status ==\n  ! no Review status block in this "
              "read-back", file=out)

    undecided = 0
    if chosen:
        print("== decisions ==", file=out)
        for n, item in enumerate(chosen, 1):
            picks = item["chosen"]
            answer = " | ".join(picks) if picks else "(UNDECIDED)"
            if not picks:
                undecided += 1
            print(f"  {n}. {item['question']} -> {answer}", file=out)
            if len(picks) > 1:
                print(f"     ! decision {n} has more than one box ticked - "
                      "ask the reviewer", file=out)
            if not item["options"]:
                print(f"     ! decision {n} has no alternatives - the "
                      "reviewer may have deleted them", file=out)
        if undecided:
            print(f"  ! {undecided} decision(s) unanswered - ask before "
                  "publishing the next round", file=out)

    if threads:
        print("== comment threads, document order ==", file=out)
        for cid, first, last in threads:
            if first < dropped_head:
                where = "(round header)"
            elif first < after_status:
                where = "(review status block)"
            elif first < dropped:
                where = "(decisions block)"
            elif first < skip:
                where = "(preamble)"
            else:
                i = first - skip
                where = doc[i][:100] if i < len(doc) else "(preamble)"
            span = (f"  (through paragraph {last - skip + 1})"
                    if last != first else "")
            print(f"  {cid}: {where}{span}", file=out)
    deletions = [p for p in doc if "~~" in p]
    if deletions:
        print("== deletions (~~) ==", file=out)
        for p in deletions:
            print(f"  - {p}", file=out)
    diff = list(difflib.unified_diff(repo, doc, "repo", "doc", n=0, lineterm=""))
    if diff:
        print("== paragraph diff (repo -> doc) ==", file=out)
        print("\n".join(diff), file=out)
    changed = sum(1 for l in diff[2:] if l[:1] in "+-")
    tail = (f"; {len(chosen) - undecided}/{len(chosen)} decision(s) answered"
            if chosen else "")
    print(f"{changed} paragraph line(s) differ; {len(deletions)} deletion(s); "
          f"{len(threads)} comment thread(s){tail}", file=out)
    return 1 if diff else 0


REPO_FIXTURE = """<!-- SPDX-License-Identifier: Apache-2.0 -->

**DRAFT.** Under review.

# Title

Issue 1 - a paragraph that wraps
across two lines with `response_format` and "quotes".

| Model | Limits |
|---|---|
| [`a/b:free`](https://example.com/a) | no `response_format` |

- A bullet the reviewer will edit.
- A bullet the reviewer leaves alone.
"""

# The Doc-only header line as Docs reads it back.
ROUND_HEADER = "# Title \u2014 2026-09-01 r2\n\n"

# The Doc-only sign-off block as Docs reads it back: the rules widen to
# ----- and a box ticked in the UI comes back struck through.
STATUS_HEADER = """-----

**Review status:**

- [ ] Reviewed with comments
- [x] Approved as-is

**Comments:**

ship it

-----

"""

# The Doc-only decisions block, read back with one choice made and one left
# open. It rides between the status block and any What-changed preamble.
DECISIONS_BLOCK = """**Decisions needed:**

Which flavor for the launch?

- [ ] Recommended: vanilla
- [x] chocolate
- [ ] Other:

Ship before or after the conference?

- [ ] Recommended: after
- [ ] before
- [ ] Other:

-----

"""

# Read-back with blank lines between paragraphs (includeComments: false
# has produced this shape), a Doc-only preamble, one edit, one thread.
DOC_FIXTURE = ROUND_HEADER + STATUS_HEADER + """## What changed since r1

- "Trim the intro" - trimmed.

---

# Title

Issue 1 - a paragraph that wraps across two lines with response\\_format and \u201cquotes\u201d.

| | |
| :- | :- |
| **Model** | **Limits** |
| [a/b:free](https://example.com/a) | no response\\_format |

- A bullet the reviewer ~~will~~ edited.<comment_start id=kix.1> Inserted.<comment_end id=kix.1>
- A bullet the reviewer leaves alone.
"""

# Read-back with a single newline between paragraphs (includeComments: true
# has produced this shape) and no edits at all: must diff clean. One thread
# spans two paragraphs.
DOC_FIXTURE_SINGLE_NEWLINE = """# Title
Issue 1 - a paragraph that wraps across two lines with response\\_format and \u201cquotes\u201d.
| | |
| :- | :- |
| **Model** | **Limits** |
| [a/b:free](https://example.com/a) | no response\\_format |
<comment_start id=kix.2>- A bullet the reviewer will edit.
- A bullet the reviewer leaves alone.<comment_end id=kix.2>
"""


def self_test():
    buf = io.StringIO()
    rc = report(REPO_FIXTURE, DOC_FIXTURE, out=buf)
    text = buf.getvalue()
    body = [l for l in text.splitlines() if l[:1] in "+-" and l[:3] not in ("---", "+++")]
    assert rc == 1, text
    assert len(body) == 2 and "~~will~~" in body[1] and "Inserted." in body[1], text
    assert "kix.1: - A bullet the reviewer ~~will~~" in text, text
    assert "1 deletion(s); 1 comment thread(s)" in text, text
    assert "response_format" not in "\n".join(body), text   # artifacts normalized away
    # The block rides ahead of a What-changed preamble: both are dropped,
    # and the comment-thread index survives being shifted twice.
    assert "  checked: Approved as-is" in text, text
    assert "  comments: ship it" in text, text
    assert "close the review" in text, text
    assert "== round ==\n  Title \u2014 2026-09-01 r2" in text, text

    # The header alone, above a body with no status block (--no-status):
    # it is named, not diffed as an insertion. An en dash or a hyphen run
    # in place of the em dash parses the same.
    for dash in ("\u2014", "\u2013", "-", "--"):
        buf = io.StringIO()
        rc = report(REPO_FIXTURE,
                    f"# Title {dash} 2026-09-01 r3\n" + DOC_FIXTURE_SINGLE_NEWLINE,
                    out=buf)
        text = buf.getvalue()
        assert rc == 0, (dash, text)
        assert "  Title \u2014 2026-09-01 r3" in text, (dash, text)
        assert "no Review status block" in text, text

    buf = io.StringIO()
    rc = report(REPO_FIXTURE, DOC_FIXTURE_SINGLE_NEWLINE, out=buf)
    text = buf.getvalue()
    assert rc == 0, text
    assert "! no '# <Title>" in text, text
    assert "0 paragraph line(s) differ; 0 deletion(s); 1 comment thread(s)" in text, text
    assert "kix.2: - A bullet the reviewer will edit.  (through paragraph 6)" in text, text


    # Docs strikes a ticked label on screen and exports it clean, so both
    # shapes have to parse the same. Either way it is a checkbox, not a
    # deletion: the label reads clean and the deletion scan never sees it.
    struck = STATUS_HEADER.replace("- [x] Approved as-is",
                                   "- [x] ~~Approved as-is~~")
    buf = io.StringIO()
    rc = report(REPO_FIXTURE, struck + DOC_FIXTURE_SINGLE_NEWLINE, out=buf)
    text = buf.getvalue()
    assert rc == 0, text
    assert "  checked: Approved as-is" in text, text
    assert "0 deletion(s)" in text, text
    assert "kix.2: - A bullet the reviewer will edit.  (through paragraph 6)" in text, text

    # Reviewer left it mid-review: no box ticked is the default state, and
    # there is no box to tick for it.
    buf = io.StringIO()
    rc = report(REPO_FIXTURE,
                STATUS_HEADER.replace("- [x] Approved as-is",
                                      "- [ ] Approved as-is")
                + DOC_FIXTURE_SINGLE_NEWLINE, out=buf)
    text = buf.getvalue()
    assert rc == 0 and "  checked: (none)" in text, text
    assert "reviewer has not signed off" in text, text
    assert "! boxes are not the standard" not in text, text
    assert "In progress" not in text, text

    # A decisions block: the answered one is reported with its choice, the
    # unanswered one is called out, and neither is diffed as an edit.
    buf = io.StringIO()
    rc = report(REPO_FIXTURE,
                STATUS_HEADER + DECISIONS_BLOCK + DOC_FIXTURE_SINGLE_NEWLINE,
                out=buf)
    text = buf.getvalue()
    assert rc == 0, text
    assert "  1. Which flavor for the launch? -> chocolate" in text, text
    assert "  2. Ship before or after the conference? -> (UNDECIDED)" in text, text
    assert "! 1 decision(s) unanswered" in text, text
    assert "1/2 decision(s) answered" in text, text
    assert "kix.2: - A bullet the reviewer will edit.  (through paragraph 6)" in text, text

    # A free-text "Other:" answer arrives as the label the reviewer typed.
    buf = io.StringIO()
    report(REPO_FIXTURE,
           STATUS_HEADER
           + DECISIONS_BLOCK.replace("- [x] chocolate", "- [ ] chocolate")
                            .replace("- [ ] Other:\n\nShip",
                                     "- [x] Other: strawberry\n\nShip")
           + DOC_FIXTURE_SINGLE_NEWLINE, out=buf)
    text = buf.getvalue()
    assert "-> Other: strawberry" in text, text

    # Two boxes ticked on one decision is a question for the reviewer, and a
    # comment anchored inside the block is located there, not in the body.
    buf = io.StringIO()
    report(REPO_FIXTURE,
           STATUS_HEADER
           + DECISIONS_BLOCK.replace(
               "- [ ] Recommended: vanilla",
               "<comment_start id=kix.9>- [x] Recommended: vanilla<comment_end id=kix.9>")
           + DOC_FIXTURE_SINGLE_NEWLINE, out=buf)
    text = buf.getvalue()
    assert "-> Recommended: vanilla | chocolate" in text, text
    assert "! decision 1 has more than one box ticked" in text, text
    assert "kix.9: (decisions block)" in text, text

    # No box ticked at all, and the closing rule deleted: the block still
    # ends, and what they typed under Comments surfaces in the diff instead
    # of being swallowed with the block.
    buf = io.StringIO()
    rc = report(REPO_FIXTURE,
                STATUS_HEADER.replace("- [x] Approved as-is",
                                      "- [ ] Approved as-is")
                .rsplit("-----", 1)[0]          # opening rule kept, closing one gone
                + DOC_FIXTURE_SINGLE_NEWLINE, out=buf)
    text = buf.getvalue()
    assert "  checked: (none)" in text, text
    assert "no closing rule" in text, text
    assert "+ship it" in text, text
    assert rc == 1, text

    # A read-back with no block at all is called out, not silently accepted.
    buf = io.StringIO()
    rc = report(REPO_FIXTURE, DOC_FIXTURE_SINGLE_NEWLINE, out=buf)
    text = buf.getvalue()
    assert rc == 0 and "no Review status block" in text, text

    repo = "# Title\n\nFirst paragraph.\n\nSecond paragraph.\n"
    doc = "# Title\nFirst paragraph.\nSecond paragraph.\n"
    assert paragraphs(repo)[0] == paragraphs(doc, hard_wrapped=False)[0]
    assert paragraphs("# T\nBody line one\nline two\n")[0] == ["# T", "Body line one line two"]
    assert paragraphs("---\nAfter the rule\n")[0] == ["---", "After the rule"]
    assert paragraphs("-----\nAfter\n", hard_wrapped=False)[0] == ["---", "After"]
    assert paragraphs("## 1\\. Title\n", hard_wrapped=False)[0] == ["## 1. Title"]
    assert paragraphs("E\\&C in \\~/.claude\n", hard_wrapped=False)[0] == ["E&C in ~/.claude"]
    fenced_repo = "Intro.\n\n```\n  a -> b\n  | c\n```\n\nAfter.\n"
    fenced_doc = "Intro.\n``` Unset\n  a -\\> b\n  | c\n```\nAfter.\n"
    assert paragraphs(fenced_repo)[0] == ["Intro.", "a -> b", "| c", "After."]
    assert paragraphs(fenced_doc, hard_wrapped=False)[0] == paragraphs(fenced_repo)[0]
    print("doc_diff: self-test passed")


def main():
    ap = argparse.ArgumentParser(
        description="Diff a Google Doc read-back against its repo Markdown, "
                    "ignoring conversion artifacts.")
    ap.add_argument("repo", nargs="?", help="the repo Markdown file")
    ap.add_argument("readback", nargs="?", help="text read back from the Doc")
    ap.add_argument("--self-test", action="store_true", help="run the inline fixture")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not (args.repo and args.readback):
        ap.error("REPO.md and READBACK.txt are required (or --self-test)")
    with open(args.repo, encoding="utf-8") as f:
        repo = f.read()
    with open(args.readback, encoding="utf-8") as f:
        doc = f.read()
    sys.exit(report(repo, doc))


if __name__ == "__main__":
    main()
