---
name: learn
description: >-
  Review the current session transcript for lessons that would have made it go smoother — failed
  commands, wrong tool arguments, user corrections, environment surprises — and propose additions
  to the workspace or global instruction file (AGENTS.md/CLAUDE.md). The promotion path from
  private auto-memory into reviewed, versioned instructions. Use when the user invokes /learn or
  asks to "extract learnings" from the session.
---

# Learn: extract durable lessons from the current session

Convert *this session's* mistakes, retries, and corrections into instructions future sessions
will see. The output is proposed edits to an instruction file — never silent writes.

## Division of labor with auto-memory

Harnesses with persistent memory (Claude Code's auto-memory is on by default) already capture
corrections, preferences, and environment facts privately as they work. That does not replace
this skill; it changes its job:

- **Memory is private and unreviewed** — per-user, per-project, invisible to teammates and to
  other agents. Instruction files are versioned, reviewed, and shared. `/learn` is the
  *promotion* path: it moves a lesson from "this agent happens to know it" to "every session in
  this repo (or every project) is told it".
- **Promote, don't duplicate.** A lesson that only matters for this user on this machine can
  stay in memory — skip it. A lesson any agent or teammate working in the repo would need
  belongs in the workspace file; one that bites in unrelated projects belongs in the global file.
- **Memory is also a source.** If the session's memory directory exists, scan its index for
  facts worth promoting alongside what the transcript surfaces.

## Where things live

- **Current-session transcript:** see the companion `claude-session-transcript` skill — its
  SKILL.md is in a sibling directory of this skill's base directory (the harness reports the
  base directory on invocation). Read it before doing transcript work.
- **Global instruction file:** the user-level file the harness actually loads — for Claude Code
  `$HOME/.claude/CLAUDE.md` (check what exists; some setups symlink it into a dotfiles repo, and
  other harnesses load their own user-level files, so confirm what yours actually reads). Use for
  OS, toolchain, CLI ergonomics, shell quoting, generic tool gotchas.
- **Workspace instruction file:** `<repo-root>/AGENTS.md` (the cross-agent convention), or
  `CLAUDE.md` where that's what the repo uses. Use for project conventions, paths, infra
  specifics. If neither exists and the lesson is project-scoped, ask before creating one.
- **Session memory (if present):** the harness names the directory in its system prompt (Claude
  Code: `$HOME/.claude/projects/<project-key>/memory/`, with `MEMORY.md` as the index).
- **This skill itself:** the SKILL.md in this skill's own base directory — a valid target when
  the session surfaced a kind of learning the procedure didn't anticipate (see "Self-update").

## What counts as a learning

Something a future session benefits from knowing *before* it starts. Strong signals:

- **Failed-then-fixed commands** — the fix is the lesson.
- **Tool-call validation errors** followed by a corrected call.
- **User corrections** ("no, don't do X", "use Y instead") — highest signal; capture faithfully.
- **Environment surprises** — machine/repo-specific failures (PEP 668, blocked URL, custom path).
- **Platform / OS differences** — BSD vs GNU flags, package managers, shell versions,
  platform-only tools, arch. Always note *which* platform the rule applies to, and don't file a
  lesson from a remote host under the local host's platform.
- **Code patterns that didn't work** — first attempt rejected, different approach succeeded.
- **Validated non-obvious choices** the user explicitly approved.

Not learnings: bugs fixed in the code (they live in the commit), one-off values from this task,
anything already covered by an existing instruction (check first), routine first-try successes,
and private-machine detail that memory already holds (see the division of labor above).

## Procedure

Delegate the transcript analysis to a sub-agent — raw JSONL and intermediate reasoning would
chew up the main session's context. The main session only locates inputs, presents proposals,
and applies what the user approves.

1. **Main session:** locate the live transcript (per `claude-session-transcript`), resolve the
   instruction-file paths above, and note the memory index path if one exists.
2. **Spawn a sub-agent** with those absolute paths plus this skill's own SKILL.md path. It scans
   for the signals above; reads the existing instruction files, skips anything covered, and
   proposes an edit to a near-miss section rather than a new one;
   classifies each candidate global vs workspace (verify platform with `uname`, don't assume)
   and applies the memory boundary; drafts additions in the target file's style; and returns a
   structured proposal list — target file, section, exact text, one-line transcript citation.
   It must not write any files.
3. **Main session:** show the proposed diff grouped by target file, with citations. Wait for
   confirmation; apply only what the user approves (with `Edit`; `Write` only when creating a new
   file the user agreed to). Report what was written and which candidates were dropped and why.

## Style for the additions

- **Rule first, then `Why:`** — one sentence each; the why lets future sessions judge edge cases.
- **Imperative, not narrative.** "Use `op run --env-file`" beats "I learned that…".
- **No session-specific names** — generalize so the lesson reads correctly in six months.
- **No editorializing** ("this is important") and code fences for commands, with ✗/✓ framing
  where the wrong pattern is instructive.

## Self-update: improving this skill

If the session surfaced a kind of learning the signal list missed, a new sensible home for
lessons, or a heuristic here that steered wrong, the skill itself is a valid edit target. Treat
self-updates like any other proposal: show the diff, cite the motivating moment, wait for
confirmation, and keep the frontmatter description in sync if the scope changes. Don't expand
speculatively.

## Things to avoid

- No learnings the transcript can't support — if you can't cite the moment, don't propose it.
- Don't contradict existing instructions without flagging the conflict explicitly.
- Keep lessons granular so the user can accept/reject individually.
- Never write to an instruction file without showing the diff first.
