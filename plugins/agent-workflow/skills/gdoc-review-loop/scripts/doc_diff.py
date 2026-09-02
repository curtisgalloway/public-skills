#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""doc_diff.py - find a reviewer's direct edits in a Google Doc read-back.

Compares the repo Markdown against the text read back from the Doc after
normalising both past the noise the Markdown -> Doc -> text round trip adds
(escaped underscores, dropped code spans, synthesised table header and
alignment rows with bolded cells, curly quotes, hard wraps, and the inline
<comment_start/end id=...> anchors). What survives is the reviewer's work:
the anchors in document order, every paragraph carrying a `~~strikethrough~~`
deletion, and a unified diff of paragraphs. Stdlib only, Python 3.9+.
Exit 0 when the two agree, 1 when they differ.

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
CHARS = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"',
                       "\u201d": '"', "\u00a0": " "})


def normalise(text):
    text = strip_repo_only(text).translate(CHARS)
    return ESCAPES.sub(r"\1", text).replace("`", "")


def paragraphs(text):
    """Blank-line blocks, split further at headings, rows, items and rules.

    Returns (paragraphs, [(anchor_id, paragraph_index)] in document order);
    the anchors themselves are stripped from the text."""
    paras, anchors, cur = [], [], []

    def flush():
        if cur:
            paras.append(re.sub(r"\s+", " ", " ".join(cur)).strip())
            cur.clear()

    for raw in normalise(text).splitlines():
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
        anchors.extend((cid, len(paras)) for cid in ANCHOR.findall(s))
        cur.append(bare)
    flush()
    return paras, anchors


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
    doc, anchors = paragraphs(doc_text)
    skip = preamble_len(doc, repo)
    doc = doc[skip:]

    if anchors:
        print("== comment anchors, document order ==", file=out)
        for cid, idx in anchors:
            idx -= skip
            where = doc[idx][:100] if 0 <= idx < len(doc) else "(preamble)"
            print(f"  {cid}: {where}", file=out)
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
          f"{len(anchors)} anchor(s)", file=out)
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


def self_test():
    buf = io.StringIO()
    rc = report(REPO_FIXTURE, DOC_FIXTURE, out=buf)
    text = buf.getvalue()
    body = [l for l in text.splitlines() if l[:1] in "+-" and l[:3] not in ("---", "+++")]
    assert rc == 1, text
    assert len(body) == 2 and "~~will~~" in body[1] and "Inserted." in body[1], text
    assert "kix.1: - A bullet the reviewer ~~will~~" in text, text
    assert "1 deletion(s); 2 anchor(s)" in text, text
    assert "response_format" not in "\n".join(body), text   # artifacts normalised away
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
