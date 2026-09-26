---
name: orchestrate-milestones
description: >-
  Run a project's remaining implementation-plan milestones end to end as an orchestrator:
  recover state (including after a crash or interrupted session), then for each milestone
  in turn launch a fresh subagent that executes it by the project-plan process, verify its
  report, push its branch, open a pull request, wait for CI, merge, clean up, and launch
  the next. Keeps pushes, merges, user questions, and any launch the user must approve in
  the orchestrator. Use when the user says "act as orchestrator", "run the remaining
  milestones with subagents", "a fresh subagent per milestone, PR and merge each", or asks
  to recover an interrupted multi-milestone run.
---

<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Orchestrate Milestones

`project-plan` runs one milestone per session and then stops for the user. This skill
replaces that stop with a loop: one milestone per **fresh subagent**, landed as one pull
request, then the next. The orchestrator plans, verifies, lands, and talks to the user; the
subagents do the work. The per-milestone process (tests, review with an artifact, evidence,
notebook, checkpoint commit) is `project-plan`'s, unchanged. Read
`<base-dir>/../project-plan/SKILL.md` for it; this skill does not restate it.

**Terms.** *Orchestrator*: this session. *Subagent*: a delegated agent with its own fresh
context (Claude Code: the Agent tool; continued later with SendMessage). *Milestone*: a unit
in the project's implementation plan. *Landing*: push, pull request, CI, merge, cleanup.

## Why the split is shaped this way

- **Fresh context per milestone.** Each subagent starts from the plan and the files, not a
  long conversation, so every milestone gets the full context budget `project-plan` sizes
  for, and the orchestrator stays small enough to run the whole queue.
- **Outward and approval-gated actions stay with the orchestrator.** Pushing, merging,
  asking the user, and launching anything the user must approve per launch (another agent
  CLI with a copied credential, a sandbox bypass, hardware, paid runs) happen here, where
  the user can see and approve them. Observed 2026-09-25: a harness safety check refused to
  create a subagent whose brief pre-authorized it to launch a second agent CLI with its
  sandbox bypassed, although the user had approved that launch earlier in the orchestrator.
  Authority the user granted to one session does not travel inside a brief.
- **The orchestrator verifies, it does not trust.** A subagent's report is a claim until
  the branch, the evidence file, and the review artifact confirm it.

## 1. Recover state

Do this at the start, and always after a crash or interrupted session. The plan and
notebook say what was *recorded*; the artifacts say what *happened*. After a crash, the
second is usually ahead of the first.

1. Fetch with prune. List branches, worktrees, and open pull requests. For each branch not
   on the integration branch, run `git cherry origin/<main> <branch>` to see unique commits,
   and check each worktree for uncommitted changes.
2. Read the plan's status table and next-session section, the notebook index, and the
   current milestone's chapter. Note the last recorded timestamp.
3. Look for artifacts newer than that timestamp: run directories, ledgers, logs, build
   outputs, test results. List live processes the work may have left running.
4. Probe every external dependency the next step needs (an agent CLI's authentication, a
   test host, CI). Something that failed before the crash may work now, or the reverse.
5. Tell the user in a few lines: the milestone in flight, what the artifacts show beyond
   the notebook, uncommitted work, and the queue you intend to run. Mark each fact as
   verified or inferred.

Do not repair or commit anything during recovery; the milestone's subagent does that, with
the recovered facts in its brief.

## 2. Build the queue

Take the milestones in plan order that are neither complete, deferred, nor blocked on
something outside the session (hardware, a user decision not yet made). Resume an
unfinished milestone before its successors. State the queue and what you left out, and
why, before launching. If the plan leaves the order or scope ambiguous, ask once, then go.

## 3. Brief each subagent

One fresh subagent per milestone, working in its own branch and worktree created from the
up-to-date integration branch. Never commit in a worktree while its subagent is live. The
brief must stand alone:

- **Unit and role:** the milestone ID and title; "you are the implementer; the orchestrator
  lands the work."
- **Where things are:** the worktree path and branch, starting commit, private run
  directories, and the files to read first (project instructions, plan sections, notebook
  index and chapter, relevant evidence).
- **Recovered state:** what the orchestrator verified, marked as verified, with the
  instruction to confirm it independently.
- **The process:** "finish the unit per `project-plan` and the project's instructions",
  plus any milestone-specific decisions the user has made, quoted with their dates.
- **Hard limits:** no push, pull request, or merge. No launching of agent CLIs, sandbox
  bypasses, or anything else that needs per-launch user approval: prepare it (brief,
  workspace, hashes, the exact command) and stop. No guessing at user decisions: return
  the question with a recommendation.
- **The report:** which case it ended in (finished, stopped to hand over a gated step,
  question); branch state and whether the tree is clean; test and review outcomes with
  artifact locations; open items; a suggested pull-request title and body free of private
  infrastructure.

## 4. Handle what comes back

- **Gated step:** run it here, where the user can approve it. Record it where the project
  records such runs, then resume *the same* subagent with the outcome, so it keeps its
  context for the audit and the rest of the milestone.
- **Question:** decide it yourself when the plan, the design, and the project's recorded
  decisions give you enough to judge. Record the decision (see below), then resume the
  subagent. Put it to the user, with the subagent's recommendation, only when you cannot
  judge it or the sources conflict irreconcilably.
- **Review findings:** decide which to fix yourself; do not stop to ask the user. Running
  this loop is the standing authorization that a review skill (such as `review-swarm`) asks
  for before fixing without a question. For each finding that survived review, decide:
  fix, fix differently, defer (to which milestone, issue, or backlog entry), or reject (and
  why). Send the fixes back to the subagent. Two limits still apply. Findings a review
  dropped stay dropped. A fix that would reverse a decision the project already recorded
  (a calibrated constant, a documented contract, an accepted tradeoff) goes to the user as
  a question.
- **Finished:** verify before landing. Check that the branch holds the claimed commits and
  the tree is clean, that the evidence file exists and links a review artifact, that the
  plan's status changed, and run the project's cheap checks yourself. A mismatch goes back
  to the subagent; it is not fixed silently by the orchestrator.

Do not relay any part of a subagent's result to the user before its report has arrived.

**Record every decision you make in the user's place.** Put it in the milestone's evidence
file (for review findings, its Review section) with the finding or question, your decision,
and a one-line reason. List these decisions again at the end of the milestone's progress
line, and all of them in the final report, so the user can review them and reopen any they
disagree with.

Stop and ask only when you cannot judge, or when two authorities the project defers to
conflict and nothing ranks them. "Unsure which is better" is a judgment to make and record;
it is not a reason to stop the loop.

## 5. Land

1. Fetch. If the integration branch moved, have the branch rebased on it (by the subagent
   if it is still live) and rerun the checks.
2. Scan the diff and the pull-request text for private infrastructure: hostnames, internal
   addresses, home paths, usernames.
3. Push, and open the pull request with the subagent's title and body, checked by you.
   The user's instruction to run this loop is the push and merge authorization for these
   milestone branches only. Record that in the first pull request's body. It does not
   extend to other repositories or other branches.
4. Wait for CI. A red check stops the loop for that milestone: send it back to the
   subagent or ask the user. Never merge on red.
5. Merge in the style the repository's history uses (merge commit, squash, or rebase).
6. Fetch, confirm the branch is dead with `git cherry`, delete the local and remote branch,
   and remove its worktree.

## 6. Next, and when to stop

After each landing, give a progress line ("M3 merged, 2 of 4; next M4") and launch
the next milestone's subagent from the updated integration branch. Stop the loop and tell
the user when:

- a milestone needs a decision only the user can make;
- a milestone ends incomplete or blocked. Land its checkpoint only if the plan permits
  landing incomplete work, and do not start its successor;
- CI fails and the cause is not a quick, clear send-back;
- the queue is empty. Report each milestone's pull request, what now works, and what is
  still open. End with a section headed **Decisions for your review**: every decision
  you made in the user's place (review findings fixed, deferred or rejected; questions you
  answered), each with its milestone, a one-line reason, and where it is recorded.

Each checkpoint commit is also crash insurance: a subagent that commits at its planned
checkpoints loses at most one step to a crash, and step 1 recovers from there.
