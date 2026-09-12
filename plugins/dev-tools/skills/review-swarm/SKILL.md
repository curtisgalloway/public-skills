---
name: review-swarm
description: >-
  Adversarial code review of a diff or pull request by four independent reviewer subagents with
  distinct mandates (security and secrets handling; correctness and concurrency; data loss,
  migration and backward compatibility; documentation-vs-reality truthfulness), each forbidden
  from reporting anything it cannot quote verbatim from the code, followed by a mechanical
  evidence check and a referee subagent that re-reads every citation, drops what the code does
  not support, and deduplicates. Liveness is enforced: a reviewer that produces no output within
  its budget is marked EXPLICITLY FAILED in the result, never silently omitted. Ends with one
  ranked table of surviving findings and a question about which to fix — or, where a project or
  the user has authorized fixing without the question, with the fixes and a written record of
  every finding, what was fixed, and what was not and why. Use when asked to
  "review this PR", "adversarial review", "review swarm", "red-team this diff", or before
  merging anything that touches secrets, concurrency, persisted data, or user-facing docs.
  Ships scripts/swarm.py (stdlib-only evidence checker and table renderer).
---

<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# review-swarm: four adversaries, one referee, one table

A single reviewer reading a diff tends to find what it went looking for and then stop. Four
reviewers with narrow, non-overlapping mandates find more, and they find different things. But
four reviewers also produce four times the plausible-sounding claims about code nobody read. So
the skill pairs the fan-out with two walls: a **quote rule** (a finding that cannot be quoted
from the code does not exist) and a **referee** that re-reads every citation before anything
reaches the user.

The third wall is **liveness**. A subagent that hangs, runs out of budget, or returns prose
instead of JSON must not disappear from the result. An arm that goes quiet is reported as
`ARM FAILED`, in capitals, at the top of the table, because a review that silently ran three
arms instead of four is worse than one that ran three and said so.

## Terms

- **Arm** — one reviewer subagent with one mandate. There are four; their names are `security`,
  `correctness`, `compat`, `docs`.
- **Mandate** — the one thing an arm is allowed to look for. `references/mandates.md` is the
  full text; each arm gets only its own.
- **Run directory** — a scratch directory holding everything one review produced: the scope,
  the diff, one JSON file per arm, the checker's output, the referee's output.
- **Referee** — a fifth subagent that judges the four arms' findings and writes nothing else.
- **Head checkout** — the working tree at the commit under review. Line numbers and quotes are
  taken from it, never from the diff hunks.

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
- `diff.patch` — `git diff <base>...<head>`.

A diff of more than roughly 3000 changed lines is too big for one run. Say so and split it by
directory or by commit rather than reviewing a sample and calling it a review.

### 2. Launch the four arms, in parallel

Fill `templates/reviewer-prompt.md` once per arm. Substitute every angle-bracket placeholder;
the mandate text comes from `references/mandates.md`, and only that arm's section. Launch all
four in one message so they run concurrently, in the background, each writing its own
`<run>/<arm>.json`.

Give each arm the same **budget**: a count of tool calls (default 40) and a wall-clock limit
(default 15 minutes). The budget is in the prompt because the delegation tool on most harnesses
has no turn limit of its own; the wall clock is enforced by you, in step 3.

Arms do not talk to each other and do not see each other's output. That independence is what
makes agreement between two arms informative in step 6.

### 3. Wait, with a deadline

Wait for four files or the wall-clock limit, whichever comes first. A bounded loop, not an
unbounded watch:

```sh
n=0
until [ -f "<run>/security.json" ] && [ -f "<run>/correctness.json" ] \
   && [ -f "<run>/compat.json" ] && [ -f "<run>/docs.json" ]; do
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

It also merges findings that are plainly the same (same file, overlapping lines, claims sharing
most of their words) and flags overlapping findings that are not plainly the same as
**duplicate candidates** for the referee.

Exit status 1 means at least one arm is `FAILED` or `PARTIAL`. Read the report either way.

### 5. Referee

Fill `templates/referee-prompt.md` and launch one subagent. It gets `verified.json`, the head
checkout, and the same budget as an arm. For each surviving finding it opens the cited lines and
decides whether the code **supports the claim**, which is a stronger test than the quote being
present: a correct quote attached to a wrong conclusion is dropped here. It resolves each
duplicate-candidate group into one finding or several. It may lower a severity with a reason.
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

## Reporting rules

- **Never omit a failed arm.** If the message to the user does not contain the words
  `ARM FAILED` and there was one, the message is wrong.
- **Never promote a dropped finding.** A finding the checker or the referee dropped is not
  "worth mentioning anyway". The counts of dropped findings are reported; their content is in the
  run directory if the user asks.
- **Never present the diff's intent as evidence.** A commit message saying the change is safe is
  not a quote from the code.
- **Say what was reviewed.** The message names the base and head commits and the number of files
  in scope. A reader must be able to tell a review of the branch from a review of the working
  tree.

## Adjusting the arms

The four mandates are the default because they rarely overlap and together cover most of what
a merge can break. To add or replace one, write its section in `references/mandates.md` in the
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
