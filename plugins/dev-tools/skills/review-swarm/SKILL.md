---
name: review-swarm
description: >-
  Adversarial code review of a diff or pull request by seven independent reviewer subagents with
  distinct mandates (security and secrets handling; correctness and concurrency; data loss,
  migration and backward compatibility; documentation-vs-reality truthfulness; regressions
  against the project's git and pull-request history; the project's own written rules in
  AGENTS.md/CLAUDE.md and directive comments; performance), each forbidden from reporting
  anything it cannot quote verbatim from the code, followed by a mechanical evidence check that
  also marks findings outside the diff's hunks, and a referee subagent that re-reads every
  citation, drops what the code does not support or the change did not cause, and deduplicates. Liveness is enforced: a reviewer that produces no output within
  its budget is marked EXPLICITLY FAILED in the result, never silently omitted. Ends with one
  ranked table of surviving findings and a question about which to fix — or, where a project or
  the user has authorized fixing without the question, with the fixes and a written record of
  every finding, what was fixed, and what was not and why. On request, posts the result to the
  pull request as a comment with permalinks. Use when asked to
  "review this PR", "adversarial review", "review swarm", "red-team this diff", or before
  merging anything that touches secrets, concurrency, persisted data, or user-facing docs.
  Ships scripts/swarm.py (stdlib-only evidence checker and table renderer).
---

<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# review-swarm: seven adversaries, one referee, one table

A single reviewer reading a diff tends to find what it went looking for and then stop. Several
reviewers with narrow, non-overlapping mandates find more, and they find different things. But
seven reviewers also produce seven times the plausible-sounding claims about code nobody read. So
the skill pairs the fan-out with two walls: a **quote rule** (a finding that cannot be quoted
from the code does not exist) and a **referee** that re-reads every citation before anything
reaches the user.

The third wall is **liveness**. A subagent that hangs, runs out of budget, or returns prose
instead of JSON must not disappear from the result. An arm that goes quiet is reported as
`ARM FAILED`, in capitals, at the top of the table, because a review that silently ran six
arms instead of seven is worse than one that ran six and said so.

## Terms

- **Arm** — one reviewer subagent with one mandate. There are seven; their names are `security`,
  `correctness`, `compat`, `docs`, `history`, `conventions`, `perf`.
- **Mandate** — the one thing an arm is allowed to look for. `references/mandates.md` is the
  full text; each arm gets only its own.
- **Run directory** — a scratch directory holding everything one review produced: the scope,
  the diff, one JSON file per arm, the checker's output, the referee's output.
- **Referee** — one more subagent that judges the arms' findings and writes nothing else.
- **Head checkout** — the working tree at the commit under review. Line numbers and quotes are
  taken from it, never from the diff hunks.
- **Hunk** — one contiguous changed region of the diff, with its few lines of unchanged context.
  A finding whose lines touch no hunk is **outside the diff**.
- **Instruction file** — a file the project wrote to tell coding agents and contributors its
  rules: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `CONTRIBUTING.md`. The `conventions` arm reads
  them.

## What a finding is

Every arm writes one JSON file, `<run>/<arm>.json`:

```json
{
  "arm": "correctness",
  "status": "complete",
  "findings": [
    {
      "severity": "high",
      "file": "cli/src/main.rs",
      "line_range": [412, 418],
      "claim": "The retry loop re-sends the whole image after a partial write, so a block already committed by the target is written twice.",
      "evidence_quote": "for attempt in 0..RETRIES {\n    port.write_all(&image)?;",
      "suggested_fix": "Resume from the last acknowledged block offset instead of index 0."
    }
  ]
}
```

- `severity` is one of `critical`, `high`, `medium`, `low`.
- `file` is relative to the repository root, as checked out at the head commit.
- `line_range` is `[first, last]`, 1-based, inclusive, from the head checkout.
- `evidence_quote` is text copied from those lines, verbatim. Whitespace is normalized when
  checked, nothing else is. Paraphrase fails the check.
- `claim` says what is wrong and what happens because of it. `suggested_fix` says what to change.
- `status` is `complete`, or `partial` when the arm ran out of budget and wrote what it had.

**The quote rule**: an arm may not report anything it cannot quote. "The function does not check
the return value" is reportable only with the call site quoted. "There is no test for X" is
reportable only if the arm can quote the place that should have exercised X, and the mandate
allows it. An arm that wants to say something without a quote says nothing.

## Procedure

Every step writes into the run directory, so a review that dies halfway leaves evidence of how
far it got.

### 1. Fix the scope

Decide what is under review and pin it. In order of preference:

- **A pull request** — the user names a number or URL. Resolve the base and head commits (with
  the `gh` CLI: `gh pr view <n> --json baseRefOid,headRefOid,files`). If the head is not checked
  out, add a detached worktree at it outside the repository.
- **The current branch** — no PR named. Base is the merge-base with the default branch; head is
  `HEAD`. Uncommitted changes are part of the review only if the user says so.
- **The working tree** — the user says "the uncommitted diff". Base is `HEAD`; the head checkout
  is the working tree itself.

Create the run directory (under the harness's scratch space; never inside the repository) and
write:

- `scope.txt` — repository path, base and head commits, how the scope was chosen.
- `files.txt` — `git diff --name-only <base>...<head>`, one path per line. Deleted files are
  listed with a `D ` prefix so an arm knows there is nothing to quote there.
- `diff.patch` — `git diff <base>...<head>`. The checker reads its hunks in step 4; without it,
  nothing can be marked outside the diff, and the checker says so.

A diff of more than roughly 3000 changed lines is too big for one run. Say so and split it by
directory or by commit rather than reviewing a sample and calling it a review.

### 2. Launch the seven arms, in parallel

Fill `templates/reviewer-prompt.md` once per arm. Substitute every angle-bracket placeholder;
the mandate text comes from `references/mandates.md`, and only that arm's section. Launch all
seven in one message so they run concurrently, in the background, each writing its own
`<run>/<arm>.json`.

Run all seven unless the user narrows the review ("just security", "skip perf"). A narrowed
review passes the same arm list to the checker with `--arms` and names the arms it left out in
the message: an arm that was never launched is not a failure, but a reader must still be able to
tell a seven-arm review from a two-arm one. Do not drop an arm on your own because it looks
unlikely to find anything; the `history` arm on a repository with no history, or the
`conventions` arm on one with no instruction files, writes an empty findings list quickly, and
that empty list is itself the evidence that it looked.

Give each arm the same **budget**: a count of tool calls (default 40) and a wall-clock limit
(default 15 minutes). The budget is in the prompt because the delegation tool on most harnesses
has no turn limit of its own; the wall clock is enforced by you, in step 3.

Arms do not talk to each other and do not see each other's output. That independence is what
makes agreement between two arms informative in step 6.

### 3. Wait, with a deadline

Wait for every arm's file or the wall-clock limit, whichever comes first. A bounded loop, not
an unbounded watch:

```sh
n=0
while :; do
  missing=0
  for arm in security correctness compat docs history conventions perf; do
    [ -f "<run>/$arm.json" ] || missing=1
  done
  [ "$missing" -eq 0 ] && break
  n=$((n+1)); [ "$n" -ge 180 ] && break   # 180 × 5 s = 15 min
  sleep 5
done
```

When the loop exits on the deadline, stop every arm still running (the harness's task-stop
tool) and continue. Do not extend the deadline once; an arm that needed 20 minutes will need 40.

### 4. Mechanical check

```sh
python3 <skill-dir>/scripts/swarm.py verify --repo <head checkout> --run <run>
```

This is the first wall. For every arm it reports one of:

- `OK` — file present, valid JSON, every finding checked.
- `PARTIAL` — the arm said it ran out of budget. Its findings are checked and kept, and the
  status is shown in the final table.
- `ARM FAILED` — no file, unparsable JSON, or a file with no `findings` list. Printed in
  capitals with the reason and the expected path.

For every finding it checks that the file exists in the head checkout, the range is inside the
file, and the normalized quote occurs within the range (or within three lines of it, in which
case the range is corrected and the correction recorded). Anything else is **dropped** with a
reason: quote not in file, quote elsewhere in the file, malformed range, unknown severity,
missing field. Dropped findings are listed in `verified.json`; they do not reach the referee and
they do not reach the user, except as a count.

When `diff.patch` is in the run directory, every surviving finding whose lines touch no hunk of
the diff is marked `outside_diff`. It is kept, not dropped: a change can break code it did not
touch. The referee decides whether the claim says how. The checker's summary line gives the
count, or says the diff was not checked.

It also merges findings that are plainly the same (same file, overlapping lines, claims sharing
most of their words) and flags overlapping findings that are not plainly the same as
**duplicate candidates** for the referee.

Exit status 1 means at least one arm is `FAILED` or `PARTIAL`. Read the report either way.

### 5. Referee

Fill `templates/referee-prompt.md` and launch one subagent. It gets `verified.json`, the head
checkout, and the same budget as an arm. For each surviving finding it opens the cited lines and
decides whether the code **supports the claim**, which is a stronger test than the quote being
present: a correct quote attached to a wrong conclusion is dropped here. It resolves each
duplicate-candidate group into one finding or several. It may lower a severity with a reason. It drops an `outside_diff` finding whose claim does not
explain how the change caused or exposed it, so a problem the change left as it was does not
reach the table.
It may not add findings, may not edit code, and may not rewrite a claim beyond tightening it.
It writes `<run>/final.json`.

Wait for the referee with the same bounded loop. If it produces nothing, the table is rendered
from `verified.json` and headed `UNREFEREED`; say so in the message. Do not skip the table
because the referee failed, and do not present unrefereed findings as refereed.

### 6. The table, then the question — or the record

```sh
python3 <skill-dir>/scripts/swarm.py table --run <run>
```

The table is ranked by severity, then by how many arms independently reported the same thing,
then by file. Above it, always, one line per arm that did not finish cleanly:

```
!!! ARM FAILED: security — no output file (expected <run>/security.json)
!!! ARM PARTIAL: docs — ran out of budget after 40 tool calls; 3 findings written
```

Present the table to the user verbatim, with the arm-status lines above it and the counts of
what the checker and referee dropped below it. Then ask which findings to fix, by ID. Use the
harness's structured question tool where there is one (multi-select over the IDs); otherwise
ask in prose. **Fix nothing until the user answers.** A review that fixes what it found is not
a review any more, and the user has not yet seen it.

**Unless fixing is already authorized.** A project's instruction file or plan may say that
verified findings are fixed without asking, and the user may say so in the session. Where that
authorization exists, skip the question and fix the findings you accept — the point of the
question was never the pause, it was that the user must be able to see what the review found and
what became of it. So the authorization carries an obligation in its place: write the record,
into the project's verification or evidence file where there is one, and otherwise into the
reply.

The record names, at minimum:

- every finding that survived the referee, with its severity and location — the whole table,
  not the part that got fixed;
- for each one, what was changed, and the check that now covers it;
- for each one *not* fixed, why, what the tradeoff is, and which milestone, issue, or owner has
  it now. A finding quietly dropped because fixing it was awkward is exactly what this rule
  exists to prevent.

Two things the authorization does not extend to. It is not permission to fix **unverified**
findings: the mechanical check and the referee still run first, and a finding they dropped stays
dropped. And it does not cover a fix that changes a decision the project has already recorded —
a calibrated constant, a documented contract, an accepted design tradeoff. Fixing those is a
decision, not a repair; report the finding, propose the change, and leave it to the user.

### 7. Post to the pull request (only when asked)

Posting is outward-facing, and a comment on a public repository cannot be fully taken back. Post
only when the user asks, and only after they have seen the table in the terminal.

1. Render the comment with permalinks to the head commit. The URL must hold the full 40-character
   SHA, written out, not a branch name:

   ```sh
   python3 <skill-dir>/scripts/swarm.py table --run <run> --format pr \
     --blob-url https://github.com/<owner>/<repo>/blob/<full head sha> > <run>/pr-comment.md
   ```

   The comment carries the same arm-status lines and the same `UNREFEREED` marker as the table.
2. Read `<run>/pr-comment.md` before posting. On a public repository, check it for anything
   private that reviewers quoted from logs or config: internal host names, private addresses,
   home-directory paths, usernames, tokens. Where the project's instruction file lists what
   counts as private, check against that list. Remove what you find and tell the user.
3. Post it as one comment: `gh pr comment <n> --body-file <run>/pr-comment.md`. Line-by-line
   review comments are not part of this skill.

## Reporting rules

- **Never omit a failed arm.** If the message to the user does not contain the words
  `ARM FAILED` and there was one, the message is wrong.
- **Never promote a dropped finding.** A finding the checker or the referee dropped is not
  "worth mentioning anyway". The counts of dropped findings are reported; their content is in the
  run directory if the user asks.
- **Never present the diff's intent as evidence.** A commit message saying the change is safe is
  not a quote from the code.
- **Say what was reviewed.** The message names the base and head commits, the number of files
  in scope, and, if the user narrowed the arms, the arms that did not run. A reader must be able to tell a review of the branch from a review of the working
  tree.

## Adjusting the arms

The seven mandates are the default because they rarely overlap and together cover most of what
a merge can break. The first four read the code as it is now; `history` reads how it got there,
`conventions` reads what the project said it must be, and `perf` reads what it costs. To add or replace one, write its section in `references/mandates.md` in the
same shape (scope, what counts, what does not count, what to quote) and pass the arm list to
the checker with `--arms`. Do not give two arms overlapping mandates to "be safe": overlap
manufactures duplicates that the referee then has to spend budget resolving, and the agreement
signal in the ranking becomes noise.

## What this skill does not do

- It does not run tests, build the code, or execute anything in the repository. A finding that
  needs a test to confirm is a finding with a `suggested_fix` of "add this test".
- It does not fix anything on its own initiative. The user picks, or a standing authorization
  in the project says to fix without asking; either way the fixing is a later step, and the
  record of what was and was not fixed is part of it.
- It does not review the review. If the user wants a second opinion on the referee's drops,
  `verified.json` still holds every finding the checker passed, with the referee's reason for
  each drop in `final.json`.
