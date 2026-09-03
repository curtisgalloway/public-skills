#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""doc_diff.py - find a reviewer's direct edits in a Google Doc read-back.

Compares the repo Markdown against the text read back from the Doc after
normalizing both past the noise the Markdown -> Doc -> text round trip adds
(escaped underscores, dropped code spans, synthesized table header and
alignment rows with bolded cells, curly quotes, hard wraps, and the inline
<comment_start/end id=...> anchors). What survives is the reviewer's work:
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
ESCAPES = re.compile(r"\\([_*\[\]<>#|])")
BLOCK_START = re.compile(r"^(#{1,6}\s|\||[-*+]\s|\d+[.)]\s|>|---\s*$)")
# A heading or a rule is a whole block by itself: it ends at its own line
# even when the next line follows without a blank line between.
BLOCK_WHOLE = re.compile(r"^(#{1,6}\s|---\s*$)")
CHARS = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"',
                       "\u201d": '"', "\u00a0": " "})


def normalize(text):
    text = strip_repo_only(text).translate(CHARS)
    return ESCAPES.sub(r"\1", text).replace("`", "")


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
    are stripped from the text."""
    paras, cur = [], []
    threads = {}

    def flush():
        if cur:
            joined = re.sub(r"\s+", " ", " ".join(cur)).strip()
            cur.clear()
            if joined:
                paras.append(joined)

    for raw in normalize(text).splitlines():
        s = raw.strip()
        if not s:
            flush()
            continue
        bare = ANCHOR.sub("", s).strip()
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


def report(repo_text, doc_text, out=sys.stdout):
    repo, _ = paragraphs(repo_text)
    doc, threads = paragraphs(doc_text, hard_wrapped=False)
    skip = preamble_len(doc, repo)
    doc = doc[skip:]

    if threads:
        print("== comment threads, document order ==", file=out)
        for cid, first, last in threads:
            first -= skip
            last -= skip
            where = doc[first][:100] if 0 <= first < len(doc) else "(preamble)"
            span = f"  (through paragraph {last + 1})" if last != first else ""
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
    print(f"{changed} paragraph line(s) differ; {len(deletions)} deletion(s); "
          f"{len(threads)} comment thread(s)", file=out)
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

# Read-back with blank lines between paragraphs (includeComments: false
# has produced this shape), a Doc-only preamble, one edit, one thread.
DOC_FIXTURE = """## What changed since r1

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

    buf = io.StringIO()
    rc = report(REPO_FIXTURE, DOC_FIXTURE_SINGLE_NEWLINE, out=buf)
    text = buf.getvalue()
    assert rc == 0, text
    assert "0 paragraph line(s) differ; 0 deletion(s); 1 comment thread(s)" in text, text
    assert "kix.2: - A bullet the reviewer will edit.  (through paragraph 6)" in text, text

    repo = "# Title\n\nFirst paragraph.\n\nSecond paragraph.\n"
    doc = "# Title\nFirst paragraph.\nSecond paragraph.\n"
    assert paragraphs(repo)[0] == paragraphs(doc, hard_wrapped=False)[0]
    assert paragraphs("# T\nBody line one\nline two\n")[0] == ["# T", "Body line one line two"]
    assert paragraphs("---\nAfter the rule\n")[0] == ["---", "After the rule"]
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
