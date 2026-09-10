---
name: gdoc-review-loop
description: >-
  Review a repo-owned Markdown document with a stakeholder through Google Docs, in numbered
  rounds. The Markdown file in git stays the source of truth; each round is a new Doc built from
  it, the reviewer's direct edits and margin comments are read back and applied to the file, and
  the reply to their comments opens the next round. Use when the user says "review this in a
  Google Doc", "send it to <name> for review", "process my comments in the doc", "read the doc
  back", "next round", "publish round 2", or "close out the review". Needs a Google Drive MCP
  server that can create, read, retitle/move and search files. Ships scripts/round_text.py
  (builds the round text) and scripts/doc_diff.py (finds direct edits under the conversion noise).
---

<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# gdoc-review-loop: review a repo document through Google Docs, in rounds

A Markdown deliverable lives in a git repo. Its reviewer does not work in git — they work in
Google Docs, where they can edit a sentence directly and leave a comment in the margin. This skill
runs that review as a loop of numbered rounds without ever letting the Doc become the document:
the repo file is the source of truth, each round is a fresh Doc generated from it, and everything
the reviewer does in the Doc is read back and applied to the file.

Two limits of the Drive tooling shape the whole design, and neither is a preference. **Doc content
cannot be updated in place**, so every round is a new Doc and its status lives in its title. And
**comments can be read but not written**, so the reply to the reviewer is a section at the top of
the next round, never a margin reply. Details under *Limits of the Drive tooling*.

## When to use

- A Markdown file in a repo (`<path/to/doc.md>`: a report edition, a spec, a post, a policy) needs
  review by someone who will not read a diff or a pull request.
- The user says any of: "review this in a Google Doc", "send it to <name> for review", "process my
  comments in the doc", "read the doc back", "next round", "publish round 2", "close out the
  review", "what did they change".

Not for documents whose source of truth *is* the Doc — there is nothing to round-trip — nor for
live co-editing by several people at once; the loop assumes one reviewer acting between rounds.

## Roles and invariants

- **The repo file is the deliverable.** The Doc is a review surface. Only the committed Markdown
  ships, and there is no "FINAL" Doc.
- **Rounds are numbered r1, r2, … per document.** Each is a new Doc. `<date>` in a title is the
  document's own date (typically from its filename), not the day the round was published.
- **The Drive folder** (`<folder-id>`, ask the maintainer; do not record folder ids in a public
  repo) has a flat contract: its root holds **exactly one Doc per document**, either awaiting the
  reviewer or closed; its `Archive/` subfolder holds every superseded round with its comment
  history intact. A Doc whose title has no bracketed status has not been looked at yet.
- **Direct edits are decisions; comments are usually instructions.** A sentence the reviewer
  rewrote in the Doc goes into the repo file verbatim — do not improve it. A comment is acted on
  and answered; if it is a question, answer it; if you decline it, say so and why.
- **The "What changed since r<N-1>" section is Doc-only.** It is the reply to the reviewer. It
  never enters the committed Markdown.
- **Every round opens with a Doc-only header line**, `# <Title> — <date> r<N>`: the Doc's own
  title without its bracketed status, so a reviewer with the Doc open — or a copy of it, or a
  printout — can tell which document and which round they are looking at without the Drive
  listing (asked for by a reviewer on 2026-09-10, when a round arrived with no version on the
  page). `round_text.py` builds it from the file's H1 and the date in its filename;
  `doc_diff.py` splits it off the read-back and reports the round it names.
- **Under the header, a Doc-only "Review status" block**, above everything else in the Doc:
  two boxes the reviewer ticks — *Reviewed with comments* and *Approved as-is* — over a
  *Comments* label for anything that does not belong in a margin comment. **No box ticked is the
  default and a state of its own**: the review is still in progress. There is no box for it —
  an untouched block already says it, and a box for the default only invites a reviewer to tick
  it and then forget to change it. Step 8 says what each box does. Docs imports `- [ ]` as a
  real clickable checklist and exports the ticked state the same way (verified 2026-09-08), so
  the reviewer ticks a box rather than editing text. `round_text.py` prepends the block and
  `doc_diff.py` splits it off the read-back and reports the ticked box. It never enters the
  committed Markdown either.
- **A decision the reviewer has to make is a checkbox set, never a question in prose.** When a
  round needs them to choose — a title, a number, whether a section stays — put it in the
  Doc-only *Decisions needed* block, right under the Review status block: a question line, then
  one `- [ ]` alternative per line, the one you recommend first and marked `Recommended: `, and
  an `Other: ` line last for an answer you did not think of. Capitalize every alternative the
  same way — `Decline`, not `decline`, beside `Recommended: Apply it` — a reviewer flagged the
  mix as a nit on 2026-09-10, and a nit in the ask list costs attention the document needs.

  ```
  **Decisions needed:**

  Which flavor for the launch?

  - [ ] Recommended: Vanilla
  - [ ] Chocolate
  - [ ] Other:
  ```

  One alternative per line is a constraint, not a style: Docs only renders a checkbox for a line
  that opens a list item, so `[ ] vanilla [ ] chocolate` on one line arrives as plain text.
  `round_text.py --decisions` builds the block (and refuses a box you pre-ticked — the tick is
  the reviewer's answer); `doc_diff.py` reports each decision with what they chose and flags any
  left unanswered. Doc-only, like the rest.
- **Every comment thread gets an answer** in the next round's What-changed section and in chat.
  Never leave one unanswered in both places.

## Per-round procedure

Round N, starting from a repo file that is ready for eyes.

1. **Build the round text mechanically** from the repo file: drop the leading license/SPDX HTML
   comment, drop any `**DRAFT.**` marker line, prepend the header line and the Review status
   block, and for N > 1 put the Doc-only section `## What changed since r<N-1>` and a `---` rule
   between that block and the document. `scripts/round_text.py` does exactly this, taking the
   header's title from the file's first `# ` heading and its date from the filename (`--title`
   and `--date` override either; `--round` is the N, default 1):

   ```bash
   python3 <skill-dir>/scripts/round_text.py <path/to/doc.md> --out round.txt
   python3 <skill-dir>/scripts/round_text.py <path/to/doc.md> \
       --changed changed.md --round 2 --out round.txt
   python3 <skill-dir>/scripts/round_text.py <path/to/doc.md> \
       --changed changed.md --round 2 --decisions decisions.md --out round.txt
   ```

   Write `changed.md` yourself: one bullet per comment thread and per direct edit, in document
   order, each quoting the comment briefly and saying what was done with it — applied, applied
   differently and why, declined and why, or answered.

   Write `decisions.md` when this round needs the reviewer to choose something — an open
   question you cannot settle, two readings of a comment they left, a placeholder only they can
   fill. One question line per decision, its alternatives as `- [ ]` lines under it,
   recommendation first, `Other: ` last (format above). A question you ask in prose instead gets
   read past; a checkbox gets answered. If nothing needs deciding, omit the flag — do not ship
   an empty block.

2. **Read the scratch file back into context before uploading**, and upload that text and nothing
   else. The uploaded text must be byte-identical to the file; if it drifts, every later diff will
   attribute your drift to the reviewer.

3. **Create the Doc** with the Drive create-file capability: `contentMimeType: text/markdown`,
   `textContent` the round text, `parentId: <folder-id>`, title
   `<Title> — <date> r<N> [DRAFT — your turn]`. Drive converts headings, bold, lists, links and
   tables. Known limits of that conversion: code-span backticks land as plain text; links *inside
   table cells* land as literal `[text](url)`; and `fileSize` in the create response reads `1`
   until conversion finishes, so verify by reading the Doc back, not by trusting the size.

4. Tell the user it is the reviewer's turn, and stop. The reviewer edits the Doc directly and
   leaves margin comments.

5. **Read the round back**, look at the ticked box first, and classify everything (next
   section). Apply direct edits verbatim and comment instructions as instructed to the repo
   file, drafting the What-changed bullets as you go.

6. **Publish round N+1 as a new Doc** (steps 1–3). Content cannot be updated in place.

7. **Archive the round just processed**: retitle it
   `<Title> — <date> r<N> [processed <MM-DD> → r<N+1>]` and move it into `Archive/` in one
   update-file call (it takes `fileId`, `title`, `parentId`). `<MM-DD>` is the processing date.

8. **Let the ticked box decide.** *Reviewed with comments* means process the round and publish
   r<N+1>. *Approved as-is* closes the document out: commit the Markdown and retitle the last
   Doc `<Title> — <date> r<N> [CLOSED → <path/to/doc.md>]`, leaving it in the folder root.
   **Neither box ticked means the reviewer has not signed off** — the default, still in
   progress: leave the round alone and come back to it, *unless* they have left comments or
   edits in the Doc or said "done" in chat, either of which decides it for them. Ticking is a
   convenience for them, not a gate on you. An unanswered decision is its own reason to wait:
   ask for it rather than publishing r<N+1> with the choice made for them.

**Finding the current round:** search the folder with `parentId = '<folder-id>'`; the one Doc
per document in the root is the current state, and its bracket says whose turn it is.

**A round that was never processed** (the draft was withdrawn, or the document was re-dated) is
not discarded: fold its comments into the *next* document's r1 What-changed section, and archive
it as `<Title> — <date> r<N> [processed <MM-DD> → <new-date> r1]`.

## Reading a round back

Use the read-file-content capability with `includeComments: true`. The result carries:

- a `commentThreads` list, **newest first**, each thread with an id; and
- inline `<comment_start id=…>` / `<comment_end id=…>` anchors in **document order**, marking the
  text each thread is attached to. Match thread to anchor by id, not by position.
- Deleted text shows as `~~strikethrough~~`; inserted text appears inline with no marker.

Direct edits do not announce themselves, so diff the Doc body against the repo copy paragraph by
paragraph, normalizing whitespace. `scripts/doc_diff.py` does that and also strips the conversion
noise the round trip introduces, so what survives is the reviewer's work:

```bash
python3 <skill-dir>/scripts/doc_diff.py <path/to/doc.md> readback.txt
```

It prints the round the header names, then the ticked box with what that box means for the
loop (look there before anything else — that is step 8), then each decision with the alternative the reviewer ticked
(`(UNDECIDED)` when they ticked none), then the comment threads in document order, one line per thread
with the paragraph it starts in (and the paragraph it runs through when a thread spans several), every paragraph
carrying a `~~` deletion, and a unified diff of the remaining paragraphs. Exit 0 means no
differences. The read-back separates paragraphs with a single newline on some calls and a blank
line on others; the script treats every read-back line as a paragraph, so both shapes diff clean
against the hard-wrapped repo file.

A box the reviewer ticked reads back as `- [x] <label>`. **On screen Docs strikes a ticked label
through, but the read-back carries no `~~`** — the strikethrough is a rendering of the checked
state, not character formatting, so only the `[x]` survives the export (checked 2026-09-08
against a box ticked by hand in the Docs UI). Expect the mismatch and do not build on it either
way: `doc_diff.py` reads the label past any `~~`, so a struck label and a clean one parse the
same. The real protection is ordering — both Doc-only blocks are split off *before* the deletion
scan, so a tick can never surface as a reviewer deletion, in the status block or in a decision.

**Conversion artifacts — never mistake these for edits**, and add any new one you find to the
script's normalizer rather than to your head:

| Seen in the read-back | What it is |
|---|---|
| `response\_format` | Docs escapes underscores; `\_` is `_` |
| a name with its backticks gone | code spans do not survive the conversion |
| a table opening with an empty row, then `\| :- \| :- \|`, then a **bold** header row | Docs synthesises the header/alignment rows and bolds the header cells |
| `“smart quotes”` and `’` | Docs autocorrect |
| paragraphs on one long line where the repo wraps them | hard wraps do not survive; compare by paragraph |
| `## 1\. Title` | Docs escapes the period after a heading number |
| `E\&C`, `\~/.claude` | Docs escapes ampersands and tildes too |
| a fenced code block with `\`\`\` Unset` on the opening fence and every line a paragraph of its own | the block flattens line by line; the language tag is Docs' |
| `-----` where the Markdown had `---` | Docs widens a horizontal rule; the script folds every width back to `---` |

Then classify each real finding: **direct edit** (decision — apply verbatim), **comment**
(instruction or question — act, then answer in What-changed), or **artifact** (ignore). When a
direct edit and a comment touch the same passage, the edit stands and the comment explains it;
say so in your bullet.

## Title conventions

| Title | Where | Meaning |
|---|---|---|
| `<Title> — <date> r<N> [DRAFT — your turn]` | root | awaiting the reviewer |
| `<Title> — <date> r<N> [processed <MM-DD> → r<N+1>]` | `Archive/` | superseded; comments answered in r<N+1> |
| `<Title> — <date> r<N> [processed <MM-DD> → <new-date> r1]` | `Archive/` | withdrawn draft, folded into the next document's r1 |
| `<Title> — <date> r<N> [CLOSED → <path/to/doc.md>]` | root | done; the repo file is the deliverable |
| `<Title> — <date> r<N>` (no bracket) | root | not yet looked at — transient; give it a status |

`<Title>` is the document's display name (e.g. its H1), `<date>` is its own date, `<MM-DD>` is
the day the round was processed. Use the em dash and the arrow as shown so the folder sorts and
scans uniformly.

## Limits of the Drive tooling

Verified 2026-09-01 against the Google Drive MCP server; check the server's tool list before
assuming these have moved.

- **Doc content cannot be updated in place.** The update-file capability changes metadata only —
  title and parent folder. Hence a new Doc per round, status carried in the title, and archiving
  by retitle-and-move.
- **Comments can be read but not written.** Hence the What-changed section, which is the reply,
  and a chat summary alongside it. Do not tell the user you "replied in the Doc"; you cannot.
- **Markdown conversion is lossy in known ways** (table above): code spans, links in table cells,
  and the header row of every table. Say so once to the reviewer so they do not "fix" them.
- **`fileSize` lies briefly.** The create response reports `1` until conversion completes. Read
  the Doc back to confirm it exists and is whole.

## Agent-neutral notes

The steps above name capabilities, not tools. The Google Drive MCP server exposes four that this
loop needs — create a file from Markdown text, read a Doc back as text with its comments, retitle
or move a file, and search a folder — and each harness prefixes their names its own way. Look them
up in your harness's tool list rather than hardcoding a prefix into project instructions.

| Capability | Server tool | Claude Code name (verified 2026-09-01) |
|---|---|---|
| create a Doc from Markdown text | `create_file` | `mcp__claude_ai_Google_Drive__create_file` |
| read a Doc back, with comments | `read_file_content` | `mcp__claude_ai_Google_Drive__read_file_content` |
| retitle and/or move a file | `update_file` | `mcp__claude_ai_Google_Drive__update_file` |
| list a folder, find the current round | `search_files` | `mcp__claude_ai_Google_Drive__search_files` |

Under Antigravity or any other MCP-capable harness the same server presents the same four tools
under a different prefix; the arguments (`contentMimeType`, `textContent`, `parentId`, `fileId`,
`title`, `includeComments`) are the server's and do not change. The two scripts are stdlib-only
Python 3.9+ and know nothing about any harness; run them from wherever the skill is installed
(`<skill-dir>/scripts/…`).
