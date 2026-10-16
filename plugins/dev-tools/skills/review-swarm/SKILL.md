---
name: review-swarm
description: >-
  Adversarial code review of a diff or pull request, sized to the change: a script reads the
  diff and picks a light (one reviewer), standard (four or five) or full (seven narrow-mandate
  reviewers) tier, every finding must quote the code verbatim and is checked mechanically, a
  referee re-reads high-severity findings, and failed reviewers are reported, never omitted.
  Ends with a ranked table and a question about which findings to fix, plus a cheap recheck
  after fixes. Use when asked to "review this PR", "adversarial review", "review swarm",
  "red-team this diff", or at a pull-request or milestone close.
---

<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# review-swarm: the most verified findings for the fewest tokens

The goal is the best review outcome per token: every real, material defect found and
verified, at the lowest cost that finds it. A single reviewer tends to find what it went looking
for and stop; several reviewers with narrow mandates find more. But every reviewer costs a full
agent session (a seven-reviewer run on a 500-line diff measured about 2.7M tokens, mostly cached
input, in Codex), and measured use showed where that buys little. Across 118 recorded runs:

- Diffs of prose, plan, evidence or config only (67 runs) produced no high or critical finding.
- The `history`, `conventions` and `perf` reviewers produced 165 findings between them and no
  high or critical one.
- The referee dropped 3% of what reached it; nearly all of the value is in its handling of the
  few high-severity findings and of duplicates.
- Every high or critical finding came from a diff that touched secrets or auth, concurrency, or
  a persisted format, which the planner below sends to the full tier.
- Breadth did not buy depth: one bug every reviewer missed cost a failed hardware attempt. The
  correctness reviewer gets the strong model.

So the skill keeps its three walls and spends the reviewers where they pay:

1. **The quote rule.** A finding that cannot be quoted from the code does not exist, and a
   script checks every quote. This costs nothing and applies at every tier.
2. **The referee**, a subagent that re-reads cited code, runs when a high or critical finding
   or a group of possible duplicates survives the quote check, and not otherwise.
3. **Liveness.** A reviewer that hangs, runs out of budget, or returns prose instead of JSON is
   reported as `ARM FAILED`, in capitals, at the top of the table, never silently omitted.

## Terms

- **Arm** — one reviewer subagent with one mandate. The full tier's seven are `security`,
  `correctness`, `compat`, `docs`, `history`, `conventions`, `perf`. The standard tier merges
  the last three into one `context` arm; the light tier runs one generalist `light` arm.
- **Mandate** — what an arm is allowed to look for. `references/mandates.md` is the full text.
- **Tier** — how many arms a review runs: `light`, `standard`, or `full`. Chosen by
  `swarm.py plan` from the diff, not by the agent.
- **External arm** — an arm run in another agent CLI (another vendor's model) instead of as a
  subagent. Its plan entry has `"model": "external:<cli>"`; it prints its JSON instead of
  writing a file, and `swarm.py collect` turns that output into `<run>/<arm>.json`.
- **Strong / cheap model** — the harness's most capable model available to subagents, and a
  cheaper capable one. In Claude Code, strong is the session's own model (usually Opus) and
  cheap is `sonnet`; in Codex, strong is the frontier model and cheap is its smaller sibling.
  Honor a model the user names.
- **Run directory** — a scratch directory holding everything one review produced: the scope,
  the diff, the plan, one JSON file per arm, the checker's output, the referee's output.
- **Referee** — a subagent that judges the arms' findings and writes nothing else.
- **Head checkout** — the working tree at the commit under review. Line numbers and quotes are
  taken from it, never from the diff hunks.
- **Hunk** — one contiguous changed region of the diff, with its few lines of unchanged context.
  A finding whose lines touch no hunk is **outside the diff**.
- **Instruction file** — a file the project wrote to tell coding agents and contributors its
  rules: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `CONTRIBUTING.md`.
- **Recheck** — after fixes, one cheap subagent confirms the fixed findings are gone and the
  fix broke nothing, instead of a second review.

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
far it got, and a later session can resume it (step 3).

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
- `diff.patch` — `git diff <base>...<head>`. The planner reads it in step 2 and the checker
  reads its hunks in step 5.

**Review at boundaries, not at every checkpoint.** When a plan or orchestrator calls for this
skill, run it once per pull request or milestone close, over the whole change, not once per
intermediate commit or sub-checkpoint inside it. Measured: a plan that ran a full review on each
of four sub-checkpoints of one milestone paid for four reviews of code the closing review read
again anyway.

### 2. Plan the tier

```sh
python3 <skill-dir>/scripts/swarm.py plan --run <run> [--close] [--tier light|standard|full] \
  [--external <cli>]
```

The script, not the agent, picks the tier and writes `<run>/plan.json` with the arms to launch,
the model class (strong or cheap) and the budget for each, and the reasons:

| Tier | When | Arms |
|---|---|---|
| `light` | No code file changed (prose, plan, evidence, data, config), or at most 50 changed lines of code with no risk trigger | `light` (strong model when code changed, cheap otherwise) |
| `standard` | More than 50 changed lines of code, no risk trigger | `correctness` (strong), `docs`, `compat`, `context`; plus `security` when the changed code touches a security surface (process spawning, `eval`, sockets, SQL, deserialization, temp files) |
| `full` | Changed code touches secrets or auth, concurrency, or a persisted format (by words in the changed lines or by path, such as `migrations/` or `*.sql`); or `--close` on a diff that changes code; or the user asks | all seven; `correctness` strong, and `security` or `compat` strong when theirs is the trigger that fired |

Pass `--close` when this review is the gate before merging a pull request or closing a
milestone. Pass `--tier` only when the user asked for one ("full review", "just a quick look").
A user who narrows the arms ("just security", "skip perf") gets exactly those arms: pass them to
the checker with `--arms`, and name the arms left out in the message.

Pass `--external <cli>` to add a **cross-vendor correctness arm**, `correctness-<cli>`, in the
standard and full tiers (never the light tier, which stays one reviewer). It gets the
`correctness` mandate and runs in that CLI, so the review is not every arm on one vendor's
model: breadth on one model did not find the bug that model missed. Add it when the user asks,
or when the user's instruction file names an agent CLI for this. The CLI must bill from a plan
with its own usage limits; a CLI billed per token runs only when the user names it for this
review. Which is which is the user's fact; read it from their instruction file, and treat an
undescribed CLI as per-token. A duplicate of a `correctness` finding by its twin is the
agreement the ranking rewards, not noise.

Do not add or drop arms on your own judgment because they look likely or unlikely to find
something; that is the plan's decision, and its reasons are written down where the reader can
check them. *Why:* in a measured run a controller split a large diff and, on its own, ran only
two arms on the half that looked low-risk, so a whole class of findings went unchecked there.

**Splitting.** When the plan prints `SPLIT REQUIRED` (more than about 3000 changed lines),
split by directory or by commit rather than reviewing a sample and calling it a review. The tier
and arm list are decided once, on the whole diff, and every part runs that same list: copy
`plan.json` into each part's run directory. Never re-plan a part on its own; a part that looks
low-risk in isolation is how the arm narrowing above happened.

### 3. Launch the arms, in parallel

Fill `templates/reviewer-prompt.md` once per arm in the plan. Substitute every angle-bracket
placeholder; the mandate text comes from `references/mandates.md`: only that arm's section,
except that `context` also gets the `history`, `conventions` and `perf` sections, and `light`
also gets `correctness`, `docs` and `conventions`. Launch every arm in one message so they run
concurrently, in the background, each on the model class its plan entry names, each writing its
own `<run>/<arm>.json`. If the harness caps concurrent subagents, launch in waves, strongest
model first.

Each arm's budget, a count of tool calls and a wall-clock limit, is in the plan and goes into
its prompt, because the delegation tool on most harnesses has no turn limit of its own; the wall
clock is enforced by you, in step 4.

Arms do not talk to each other and do not see each other's output. That independence is what
makes agreement between two arms informative in the ranking.

**External arms.** Fill the same template for `correctness-<cli>`, with the `correctness`
mandate, and launch it in the background in that CLI, headless and read-only, with its output
saved in the run directory. For Muse (checked with Muse Code 1.4.9 on 2026-10-16):

```sh
muse exec --json --no-foreign-personal-context --disable-write --disable-shell \
  --disable-web-tools --disable-request-user-input \
  -c hooks.enabled=false -c plugins.enabled=false --reasoning-effort high \
  --workspace <head checkout> --prompt-file <run>/correctness-muse.prompt.md \
  > <run>/correctness-muse.jsonl 2> <run>/correctness-muse.log
python3 <skill-dir>/scripts/swarm.py collect --run <run> --arm correctness-muse \
  --stream <run>/correctness-muse.jsonl
```

Run it from the head checkout, with no model flag unless the user names one (the CLI's plan
picks its default). Without write access the arm prints its JSON as its final message, which
the template allows; `collect` takes the first JSON object with a `findings` list and writes
`<run>/correctness-muse.json`, or writes nothing and says `ARM FAILED`, which `verify` then
reports like any missing arm. Without a shell it cannot run `git`; its mandate does not need
it. Another CLI works the same way when it has a headless, read-only mode; `collect` reads
Muse's event stream or plain text.

**Resuming.** If a session stalls or dies mid-review (a usage limit, a capacity error, a
closed terminal), the arms it launched die with it. On resume, do not wait for them and do not
start over: list the run directory, relaunch only the arms in `plan.json` whose `<arm>.json` is
missing, and continue from step 4.

### 4. Wait, with a deadline

Wait for every planned arm's file or the wall-clock limit, whichever comes first. A bounded
loop, not an unbounded watch; take the arm names from `plan.json`:

```sh
n=0
while :; do
  missing=0
  for arm in <arms from plan.json>; do
    [ -f "<run>/$arm.json" ] || missing=1
  done
  [ "$missing" -eq 0 ] && break
  n=$((n+1)); [ "$n" -ge 180 ] && break   # 180 × 5 s = 15 min
  sleep 5
done
```

When the loop exits on the deadline, stop every arm still running (the harness's task-stop
tool) and continue. Do not extend the deadline once; an arm that needed 20 minutes will need 40.

**Never end the session while reviewers run.** The orchestrating agent waits for every arm and
the referee to finish, or to hit the deadline and be marked failed under the liveness rule,
before it ends its turn. *Why:* in a headless one-shot session the reviewers are killed with the
session, and in a measured run an agent started a seven-arm review in the background, ended its
turn, and the review died with it, so the next session had to redo it.

### 5. Mechanical check

```sh
python3 <skill-dir>/scripts/swarm.py verify --repo <head checkout> --run <run>
```

This checks the arms named in `plan.json` (or `--arms`). For every arm it reports one of:

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
touch. The checker's summary line gives the count, or says the diff was not checked.

It also merges findings that are plainly the same (same file, overlapping lines, claims sharing
most of their words) and flags overlapping findings that are not plainly the same as
**duplicate candidates**.

Its last line says whether the referee is `NEEDED`: a high or critical finding survived, or
there is a duplicate-candidate group. Exit status 1 means at least one arm is `FAILED` or
`PARTIAL`. Read the report either way.

### 6. Referee (only when needed)

When the checker says `referee: not needed`, skip this step: the table is rendered from
`verified.json` and marked "not refereed" with the reason. Before presenting it, read each
`outside_diff` finding's claim yourself and leave out of your summary any that does not say how
the change caused or exposed it; say how many you set aside.

When it says `NEEDED`, fill `templates/referee-prompt.md` and launch one subagent on the strong
model. It gets `verified.json`, the head checkout, and an arm's budget. For each surviving
finding it opens the cited lines and decides whether the code **supports the claim**, which is a
stronger test than the quote being present: a correct quote attached to a wrong conclusion is
dropped here. It resolves each duplicate-candidate group into one finding or several. It may
lower a severity with a reason. It drops an `outside_diff` finding whose claim does not explain
how the change caused or exposed it. It may not add findings, may not edit code, and may not
rewrite a claim beyond tightening it. It writes `<run>/final.json`.

Wait for the referee with the same bounded loop. If a needed referee produces nothing, the table
is rendered from `verified.json` and headed `UNREFEREED`; say so in the message. Do not skip the
table because the referee failed, and do not present unrefereed findings as refereed.

### 7. The table, then the question — or the record

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

- every finding that survived the checker and, where one ran, the referee, with its severity
  and location — the whole table, not the part that got fixed;
- for each one, what was changed, and the check that now covers it;
- for each one *not* fixed, why, what the tradeoff is, and which milestone, issue, or owner has
  it now. A finding quietly dropped because fixing it was awkward is exactly what this rule
  exists to prevent.

Two things the authorization does not extend to. It is not permission to fix **unverified**
findings: the mechanical check, and the referee when one is needed, still run first, and a
finding they dropped stays dropped. And it does not cover a fix that changes a decision the
project has already recorded — a calibrated constant, a documented contract, an accepted design tradeoff. Fixing those is a
decision, not a repair; report the finding, propose the change, and leave it to the user.

### 8. Recheck after fixes

Do not run a second review to confirm fixes. Make a new run directory for the fix, write its
`diff.patch` (`git diff <pre-fix commit>..<fix commit>`), fill `templates/recheck-prompt.md` with
the ids that were fixed and the original run directory, and launch one subagent on the cheap
model. It writes `<recheck-run>/recheck.json`: each fixed finding as `resolved` (with the line
that now handles it, quoted) or `unresolved`, plus any defect the fix itself introduced. Then:

```sh
python3 <skill-dir>/scripts/swarm.py verify --repo <head checkout> --run <recheck-run> \
  --arms recheck
```

The checker confirms every `resolved` quote exists where it says (a resolution it cannot find
prints `!!! RESOLUTION NOT CONFIRMED` and exits 1) and checks new findings like any other.
Report resolved, unresolved and new counts. A new high or critical finding from the fix goes
through the referee as in step 6. Run a fresh review only when the fix grew into a change of its
own, large enough that `swarm.py plan` on its diff would not say `light`.

### 9. Post to the pull request (only when asked)

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
- **Say what was reviewed, and how hard.** The message names the base and head commits, the
  number of files in scope, the tier and the plan's reason for it, and, if the user narrowed
  the arms, the arms that did not run. A reader must be able to tell a review of the branch from
  a review of the working tree, and a one-reviewer review from a seven-reviewer one.

## Adjusting the arms

The seven full-tier mandates rarely overlap and together cover most of what a merge can break.
The first four read the code as it is now; `history` reads how it got there, `conventions` reads
what the project said it must be, and `perf` reads what it costs. The `context` and `light` arms
combine mandates for the cheaper tiers. To change the tiers, edit `make_plan` in
`scripts/swarm.py` and its tests, and replay the planner over recorded run directories to see
which past findings a change would have cost. To add or replace a mandate, write its section in
`references/mandates.md` in the same shape (scope, what counts, what does not count, what to
quote) and pass the arm list to the checker with `--arms`. Do not give two arms overlapping
mandates to "be safe": overlap manufactures duplicates that the referee then has to spend budget resolving, and the agreement
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
