---
name: project-plan
description: >-
  Plan project work by creating or updating a detailed design document (approved by
  the user before planning), then deriving an implementation plan with cohesive,
  session-sized milestones and mandatory testing and review gates, then executing one
  milestone per session with recorded evidence and a handoff. Use for "plan this
  project", "design doc", "turn this design into an implementation plan", "break this
  work into milestones", or "what's next on this project"; also use when the project
  already has an implementation plan and the user wants to resume, continue, or check
  status, even if they don't say "plan".
---

<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Project Plan

Produce two durable artifacts: a design explaining what to build and why, and an
implementation plan explaining how to deliver it in independently verifiable milestones.
The plan must carry enough context for a new session to resume without the conversation.
Complete one milestone before context compaction, then stop for the user to inspect the
result and choose when to clear context or start a new session. This is a delivery
boundary, not just a way to divide a task list.

## Inputs, tools, and scope

Inputs are the requested outcome, project files, any existing design or plan, and user
constraints. Use the available file search, reading, and editing tools; no third-party
tool or particular agent harness is required. Executing milestones also requires the
project's build and test tools; identify these in the plan.

Follow the project's documentation conventions and user-specified locations. Otherwise,
use `docs/design.md` and `docs/implementation-plan.md`; use topic-specific filenames when
the project has several workstreams. Link the documents using relative paths.

A planning request authorizes producing these documents, with one pause: after the
design is written or materially revised, stop and ask the user to approve it before
deriving the plan. Every milestone inherits whatever is wrong in the design, so this is
the cheapest place to fix it. The user can waive the pause ("go straight to the plan");
record the waiver and its scope in the plan's conventions block so later sessions honor
it. Preserve authorization already given. Begin implementation only when the user has
also requested it. A status-only request calls for reporting state, not starting work.
The milestone close-out pause below is intentional even when further work is authorized.

Orient from the documents' contents, not just their existence: establish whether the
design needs work, the plan is ready, or a milestone is unfinished. State the current
phase and next action briefly. Use the templates in [templates.md](templates.md) when
creating documents; adapt their structure to existing project conventions.

## 1. Establish the design

Inspect project instructions, relevant source and tests, and existing design documents
before writing. Find the authoritative design for this work rather than creating a
competing document. Reuse a current, sufficiently detailed design; amend gaps or stale
sections while preserving decisions that still apply. If none exists, write one first.

Make the design specific enough to resolve implementation choices:

- Problem, intended users, observable outcomes, scope, and explicit non-goals.
- Current behavior and constraints, grounded in relevant files or other evidence.
- Proposed architecture, component responsibilities, interfaces, data models, and the
  important flows through them, including errors and failure recovery.
- Relevant compatibility, migration, security, performance, and operational concerns;
  omit concerns that do not apply rather than filling sections with boilerplate.
- Significant alternatives, chosen tradeoffs, assumptions, risks, and open questions.
- Acceptance criteria and a verification strategy for the complete outcome.

Give requirements or acceptance criteria stable labels so the plan can refer to them.
Separate observed facts from assumptions. Ask about missing decisions that materially
affect scope or architecture while continuing independent documentation work. Mark
dependent work blocked until those decisions are resolved; do not invent user choices.
For technical uncertainty, define a bounded investigation with a question, evidence to
collect, and an exit criterion before committing to a dependent implementation sequence.

Review the design for internal consistency and sufficient detail before deriving the
plan. A design with unresolved blockers can support a provisional plan, but label the
affected milestones and explain what must be decided before they are executable.

Then stop for the design gate: end the turn with a short summary of the design and one
clear ask — approve it, or say what to change. Do not derive the plan in the same turn
unless the user has waived the gate. When an authoritative design already exists and
needed no material amendment, the gate is already satisfied; say so and proceed.

## 2. Derive the implementation plan

Link the authoritative design and identify its revision (a commit when available, or a
dated revision note). Map every in-scope design requirement to milestones and verification;
flag omissions and contradictions before calling the plan ready.

Order milestones by dependencies and risk. Each milestone should deliver a coherent
capability that can be comprehensively tested at its boundary. Prefer a thin working
path through the relevant layers to separate "all backend", "all frontend", and "all
tests" phases. A foundational milestone is appropriate when it has its own observable
contract and tests. Do not defer all integration or testing to the end.

For each milestone, record:

- **ID, title, and outcome:** the capability or contract delivered, with an observable
  before/after example where useful.
- **Design coverage and dependencies:** requirement labels, prerequisite milestones,
  external prerequisites, and decisions that must be resolved.
- **Scope and exclusions:** the functionality included and explicitly deferred work.
- **Implementation steps:** ordered, concrete changes to components, interfaces, files,
  and data as known from inspection; label proposed locations as proposed.
- **Acceptance criteria:** observable pass/fail conditions, including relevant error
  paths, edge cases, and compatibility behavior.
- **Verification:** appropriate automated tests, integration checks, manual or hardware
  checks, and project-required checks. Give known commands and expected results; mark
  commands needing discovery rather than presenting guesses as working commands.
- **Review:** what to inspect against the design and what regressions to consider.
- **Sizing and checkpoint:** why the scope fits a session, likely sources of uncertainty,
  and a safe split point if it grows.
- **Status and evidence:** initially `pending`; later record results and remaining work.

Include a final verification milestone or gate that checks the assembled system against
the full design, including cross-milestone interactions and outstanding regression checks.
This supplements the testing and review required for every earlier milestone.

### Size for a session, with room to finish properly

Aim for a milestone to fit one fresh session within roughly 75% of its context capacity,
including orientation, implementation, test output, review, fixes, and checkpoint writing.
Treat this as a planning heuristic, not a guarantee or a measurable limit on every harness.
Do not invent context percentages or equate a fixed number of tasks or lines with tokens.

Use scope as the fallback: a small number of related components, a focused test surface,
and limited unknowns. A fresh session should need only the design, the milestone and
handoff, and a handful of relevant files to begin. If it would need to explore most of
the codebase, narrow the scope or first document the necessary map in a bounded
investigation. Roughly one component with its tests and at most one new interface is a
useful sizing prompt, not a hard limit on a coherent slice across layers.
Split milestones spanning several independent capabilities or substantial investigation.
Preserve meaningful, testable boundaries when splitting.
Aim to finish implementation, verification, and handoff without compaction; leave the
remaining context available for the user's review and follow-up fixes. If a milestone
cannot reasonably fit, split it before starting rather than relying on compaction.

When context usage is exposed, use it to adjust remaining scope early enough to leave
room for verification. Without a meter, watch for growing investigation, repeated
re-reading, and repeated debugging attempts without new evidence. If finishing safely
before compaction looks unlikely, save an incomplete handoff and stop early. If compaction
happens unexpectedly, disclose that the sizing goal was missed, reconstruct the state
from files, and write a safe handoff rather than continuing implementation in that session.
A session boundary does not make a milestone complete.

## 3. Execute and close milestones when authorized

On resumption, read the design, plan, latest checkpoint, and relevant working-tree state.
Check that prerequisites still hold and that the design has not drifted. Implement the
milestone identified by the handoff within the user's authorized scope: resume an
unfinished milestone before advancing; after a completed one, start the next eligible
milestone when the user asks to resume. If no handoff exists, use plan status and evidence
to choose. Mark it `in_progress` and briefly state its acceptance criteria.

Record the starting revision when available and any pre-existing working-tree changes
so the milestone's actual changes can be identified for review. Write tests alongside
implementation. Put unrelated discoveries in the plan's backlog with their impact and
follow-up, rather than expanding the current milestone silently.

Before declaring **any milestone complete**:

1. Run its planned tests and applicable project checks. Check the acceptance criteria,
   relevant failure paths, and integration with previously completed milestones.
2. Prefer a reviewer subagent with fresh context when delegation is available and permitted;
   otherwise perform an explicit self-review after re-reading the design and milestone.
   Supply the design, milestone, verification evidence, and the milestone's commits since
   the starting revision. Also include any relevant staged, unstaged, and new files still
   awaiting the checkpoint commit; a commit-only diff can omit unfinished work.
   Ask the reviewer to check every acceptance criterion with evidence, design conformance,
   regressions, maintainability, test coverage, and scope deviations, and rank findings by
   severity. Record the review method; do not imply an independent review occurred when it
   did not.
3. Fix blocking findings and failures. Repeat affected tests and review changed areas;
   broaden verification when the findings indicate a wider risk. Obtain another review
   for substantial fixes. If review or debugging stops producing progress, save an
   incomplete handoff; a limit on review rounds never waives a blocker.
4. Write full evidence (commands/checks, outcomes, output excerpts, review findings and
   resolutions) to a linked evidence file, `docs/evidence/<milestone-id>.md` unless the
   project has a convention. Keep only status, the evidence link, and open limitations
   in the plan's evidence block. Mark complete only when acceptance criteria and required
   verification pass and blocking review findings are resolved. At completion, move the
   detailed milestone entry into the evidence file, preserving design coverage and
   acceptance criteria there; retain its ID, outcome, dependencies, status, evidence link,
   and open limitations in the plan. Finished milestones should cost each new session a
   few lines, not a page.

Unavailable hardware, missing credentials, or a skipped required check means verification
is incomplete. Record the blocker and leave the milestone `in_progress` or `blocked`;
never substitute "tests added" for tests executed. Disclose pre-existing failures and
their effect on verification. Nonblocking follow-ups must be explicit and cannot silently
replace an acceptance criterion.

If the work grows or the design changes, update the design first where needed, then revise
dependent milestones and coverage after satisfying the design gate for material revisions.
Preserve completed evidence and explain any reopened
milestone. Do not silently shrink acceptance criteria to obtain a passing status.

## 4. Handoff and stop

At completion or an early stop, update the plan and write a handoff using the project's
existing handoff convention, or the plan's `Next session` section when none exists.
Record the current milestone and status, work done, relevant files and working-tree state,
test/review evidence, outstanding failures or decisions, and the exact next action.
Distinguish required work from optional backlog items. Do not require a separate handoff
skill or create competing records.

Commit the milestone's changes together with the evidence and plan/handoff update at
every checkpoint, completed or early-stopped, on the project's working branch, under a
message that names the milestone (`<prefix>: M3 — <title>`). Record the branch and message
prefix in the plan's conventions block. A user instruction or project workflow that
forbids agent commits overrides this; make the uncommitted state clear in the handoff.
Include only the milestone's changes, preserving unrelated pre-existing work. Record
existing milestone commits and identify the checkpoint commit by its message when its
hash is not yet available; do not amend repeatedly to embed a commit's own hash.

- **Completed:** identify the next eligible milestone and the documents/files needed to
  begin it. Stop for the user to inspect the result. Do not start another milestone in
  this session unless the user explicitly overrides the one-milestone boundary.
- **Incomplete:** leave status `in_progress` or `blocked`, explain why work stopped, and
  identify remaining implementation, tests, and review. The next session resumes this
  milestone, not its successor. Split remaining work when appropriate without relabeling
  unmet acceptance criteria as completed.

Do not clear context yourself or claim ending a turn creates a fresh session. The user
chooses when to reset and resume. Address requested feedback on the completed milestone
within remaining capacity; reopen its status if feedback reveals a completion blocker,
and refresh affected verification and the handoff after changes.

## Delivery

For planning-only work, report the design and plan paths, the milestone sequence, and any
unresolved decisions or verification prerequisites. Make clear that implementation has
not run. For execution, lead with a progress line ("M3 of 6 complete" or "M3 of 6
incomplete: <reason>"), then two or three bullets on what now works and how it was
verified, any design change or unexpected compaction, and the handoff link. Give the
next action for a fresh session as a single line, resuming unfinished work when needed.
Keep the documents authoritative so a new session can proceed without reconstructing
decisions from chat.
