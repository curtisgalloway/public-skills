---
name: lab-notebook
description: >-
  Keep a running lab notebook and a process log while working: one append-only,
  timestamped chapter per unit of work (a milestone, an investigation, a debugging
  session), a timestamped index that makes the chapters searchable, and a per-project log
  of where the agent's process cost time, as input for improving the agent. Use when the
  user asks to keep a lab notebook, keep notes as you go, log the work, or record what
  went wrong for later improvement; when resuming work that has a docs/notebook/
  directory; and whenever another skill (such as project-plan) says to follow it.
---

<!--
SPDX-FileCopyrightText: 2026 Curtis Galloway
SPDX-License-Identifier: Apache-2.0
-->

# Lab Notebook

Keep two records while the work happens, not after it:

- **The notebook** records the path: what was tried, what failed, what was decided and
  why. A later session reads it to avoid repeating dead ends.
- **The process log** records what the path cost the agent: failed commands, surprises,
  corrections. It is input for improving the agent, not the project.

A verdict record (an evidence file, a PR description, a handoff) says where the work
ended up. These say how it got there. Link them from the verdict record rather than
copying from them.

**Why notes need defined moments:** records written at the end are reconstructed from
memory, and what drops out is exactly what did not affect the outcome: the failed
attempts, dead ends, and friction. Those are what the next session needs, and what
improving the agent needs. A note with no defined moment gets written at the end or not
at all. So every entry below has a trigger, and the index carries timestamps that show
when it has fallen behind.

## Where the records live

Follow the project's documentation conventions and user-specified locations. Otherwise:

- `docs/notebook/<chapter>.md` — one chapter per unit of work. A calling skill names its
  chapters (project-plan uses milestone IDs); standalone, use a short kebab-case slug of
  the work, such as `flaky-login-test`.
- `docs/notebook/index.md` — the index.
- `docs/process-log.md` — one process log per project.

Use the templates in [templates.md](templates.md) when creating these files. The files are
committed like any other project document: keep secrets out, and follow the project's
rules about what may appear in its repository.

## Timestamps

Take every timestamp from the system clock at the moment of writing, in ISO 8601 with a
time zone (`2026-09-24T14:05-07:00`). Never infer one from the session start, an earlier
entry, or the conversation. The index's staleness check depends on these being real.

## Chapters

A chapter is append-only. Write an entry at each of these moments, when it happens:

- **Opening:** the goal, the starting revision, pre-existing working-tree changes, and
  the intended approach. Resuming a chapter in a new session also gets an entry.
- **Attempt:** each hypothesis or attempt and its outcome, including the ones that failed.
- **Dead end:** an abandoned approach and why, so a later session does not retry it.
- **Decision:** a choice the design or instructions did not settle, and its reason.
- **Surprise:** behavior, tooling, or data that contradicted an assumption.
- **Direction:** a user instruction that changes course.
- **Checkpoint:** where the chapter stands, at every commit checkpoint or early stop. The
  last checkpoint entry of finished work is marked closing.

Keep entries to a few lines and link logs or files rather than pasting them. Correct an
earlier entry by appending a new one that says what it corrects; never rewrite or tidy
earlier entries. One chapter is open per unit of work; parallel work in separate
worktrees gets separate chapters, so two sessions never append to the same file.

## The index

The index lets a session find the right chapter by concept, not only by exact term, and
follow topics that span chapters. It is read at the start of every session that uses the
notebook, so it stays small.

- An `Updated:` timestamp at the top.
- One row per chapter: the link, the span it covers (first entry through the last entry
  indexed), a one-line outcome (`open` while the chapter is open), and the key findings
  and dead ends in at most five lines.
- A `Threads` section linking topics that span chapters: a bug seen in two places, a
  decision revisited later.

Add a row when a chapter opens. Refresh the row and `Updated:` at every checkpoint entry,
not after every entry. A row is **stale** when its chapter has an entry newer than the
row's "indexed through" timestamp; refresh it before relying on it. Do not copy other
status records (a plan's status table, an issue tracker) into it.

## The process log

Append an entry when it happens, for any of:

- A failed command, wrong tool argument, or retried step.
- A harness, tool, or environment behavior that surprised the agent.
- A user correction of approach, scope, or style.
- A sizing miss: work split late, an early stop, or unexpected context compaction.
- An instruction or skill that was missing, wrong, ambiguous, or not followed.

Each entry names the chapter, what happened, what it cost, what would have prevented it,
and where the fix belongs: a skill (by name), project instructions, user instructions, or
a tool. Findings about the project itself belong in the project's backlog or tracker, not
here.

Do not edit instructions or skills from the log on your own. It feeds the user's review
or a lesson-extraction skill such as `learn`, where available. When a fix is applied,
append an entry recording where, rather than editing the original.

## Resuming

Read the index, then the current chapter. Check the current chapter's row for staleness.
Read other chapters only when the index points to one that matters; do not read the
whole notebook. After an unexpected context compaction, reconstruct state from the
current chapter first, and log the compaction in the process log.

## Reporting

When reporting a checkpoint to the user, link the chapter and give the number of
process-log entries added this session, so friction is visible without opening the file.
