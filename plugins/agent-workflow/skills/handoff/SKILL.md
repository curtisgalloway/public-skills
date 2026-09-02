---
name: handoff
description: Preserve working state across a context clear or agent restart. Write mode dumps a HANDOFF.md the next session can cold-start from (task, state, decisions, dead ends, next steps); resume mode reads it back and continues the work. Use when the user invokes /handoff, says they're about to clear context / restart / compact / "pick this up tomorrow", or starts a session by asking to resume from a handoff.
---

<!--
SPDX-FileCopyrightText: 2026 Curtis Galloway
SPDX-License-Identifier: Apache-2.0
-->

# Handoff: carry working state across a context clear

A session about to be cleared holds state that exists nowhere else: what the user actually asked
for, decisions and their reasons, approaches that failed, verbal instructions, environment facts
learned the hard way. The repo keeps the code; git keeps the diffs; this skill keeps everything
else. It writes a `HANDOFF.md` the *next* session reads to continue as if the clear never
happened.

The file lives at the **project root** — discoverable by any agent in any harness with a plain
"read HANDOFF.md", and stable across both `/clear` and a full process restart. It is excluded from
git locally (see below) and consumed on resume.

## Mode selection

`/handoff` takes an optional argument: `write`, `resume` (alias `read`), or nothing.

With no argument, decide by state:

- **`HANDOFF.md` exists at the project root, and this conversation has not touched it** → resume
  mode. A fresh session invoking `/handoff` next to an unconsumed handoff wants to pick the work
  up.
- **This conversation already wrote or resumed the handoff** → write mode, updating the file in
  place. The user is checkpointing again before another clear, not asking to re-read what's
  already in context.
- **No `HANDOFF.md`** → write mode.

An explicit argument overrides the detection. `resume` with no file present: say so and stop —
check for `HANDOFF.md.read` (a consumed handoff, see resume mode) and offer it if one exists.

## Locating the project root

Use the repo top level if inside a git checkout, otherwise the current working directory:

```bash
git rev-parse --show-toplevel 2>/dev/null || pwd
```

If that directory is not writable, tell the user and ask where to put the file instead of failing
silently.

## Write mode

### 1. Gather ground truth

Record the concrete state a future session can verify itself against: current branch, short HEAD
SHA, and a one-line summary of `git status --short` (count and nature of uncommitted files — not
the full diff). Outside a git repo, skip this.

### 2. Write `HANDOFF.md`

Follow this skeleton. Omit sections that would be empty rather than padding them; keep the whole
file under about a hundred lines — a handoff is a briefing, not a transcript.

```markdown
# Session handoff — <absolute date, e.g. 2026-08-27>

> Written by /handoff for the next agent session. Disposable; excluded from git.

## Task
<What the user is trying to accomplish and why, one or two sentences. Quote the
user's own framing where the wording carries intent.>

## State
- Branch `<name>` at `<short-sha>`, <clean | N files uncommitted: which>
- Done: <...>
- In progress: <...> — <exactly where it stopped>
- Not started: <...>

## Next steps
1. <Concrete enough to execute immediately: exact command, exact file:line.>
2. <...>

## Decisions
- <Choice made> — <why, and whether the user or the agent made it>

## Dead ends
- <What was tried> — <why it failed; do not retry>

## Gotchas
- <Environment or tool facts learned this session that are written down nowhere else>

## Key files
- `<path>` — <role; hot spots as path:line>

## Standing user instructions
- <Constraints given this session that still bind — verbatim where wording matters>
```

Optionally append a `## Deeper history` line pointing at the session transcript, if the harness
exposes one (in Claude Code, the `claude-session-transcript` skill describes how to find it), so
the next session can dig past the summary when it needs to.

### 3. Exclude it from git

If inside a git repo and `git check-ignore -q HANDOFF.md` fails, append `HANDOFF.md*` to
`.git/info/exclude`. That keeps both the handoff and its consumed form out of `git status` without
touching the repo's tracked `.gitignore`.

### 4. Close out

Tell the user: where the file was written, that it's safe to clear or exit now, and that
`/handoff` (or just "read the handoff") in the next session resumes.

## Resume mode

1. **Read `HANDOFF.md` in full.**
2. **Verify before trusting.** The world may have moved since the handoff was written: compare its
   recorded branch and SHA against the current repo state, and glance at `git status`. Note any
   drift to the user ("handoff was written on `foo` at abc1234; you're now on `main`") rather than
   silently proceeding on stale assumptions.
3. **Consume it**: rename `HANDOFF.md` → `HANDOFF.md.read`. This keeps one generation recoverable
   if the resume goes sideways, while letting the next no-argument `/handoff` correctly mean
   "write". The next write mode overwrites any stale `.read` file's sibling normally — no cleanup
   needed.
4. **Recap and continue.** Give the user a two-or-three-sentence recap — the task, where it
   stands, what you're about to do — then start on the first next step. If the handoff says the
   work is blocked on a user decision, ask that question instead of guessing past it.

## What makes a good handoff

- **Write for a reader with zero session context.** No shorthand, codenames, or "the fix we
  discussed" — the next session did not attend the discussion. This includes you: assume you will
  remember nothing.
- **Record what is *not* recoverable from disk.** Intent, rationale, failures, and spoken
  constraints die with the context; diffs and file contents do not. If `git log` or the code
  already says it, leave it out.
- **Dead ends are the highest-value section.** The most expensive failure mode of a fresh session
  is confidently re-walking a path the last one already proved wrong.
- **Absolute dates, exact commands, real paths.** "Today" and "the script" mean nothing next week.
- **No secrets.** The file is plaintext at the project root; tokens, passwords, and internal
  hostnames must not appear in it, even briefly.
