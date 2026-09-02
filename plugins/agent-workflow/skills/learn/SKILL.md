---
name: learn
description: >-
  Two modes. Quick (default): review the current session transcript for lessons that would have
  made it go smoother — failed commands, wrong tool arguments, user corrections, environment
  surprises — and propose additions to the workspace or global instruction file
  (AGENTS.md/CLAUDE.md); the promotion path from private auto-memory into reviewed, versioned
  instructions. Full (/learn --full): analyze the last 30 days of sessions, cluster recurring task
  patterns, propose new skills for your skills repo, and flag friction in existing skills. Use when
  the user invokes /learn or asks to "extract learnings". Both modes propose before writing.
---

# Learn: extract durable lessons

Convert mistakes, retries, and corrections into instructions and skills that future sessions
will see. The output is always a proposal for review — never silent writes.

- **Quick** (`/learn`): this session → additions to an instruction file.
- **Full** (`/learn --full`): the quick scan *plus* a 30-day analysis → new-skill proposals and
  fixes to existing skills.

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
- **Session facets (full mode, Claude Code):** `$HOME/.claude/usage-data/facets/<session-uuid>.json`
  — per-session summaries the harness writes, with `brief_summary`, `goal_categories`,
  `friction_detail`, `outcome`, `session_type`. Far cheaper than raw transcripts; other harnesses
  have no equivalent yet, so there fall back to transcripts.
- **Global instruction file:** the user-level file the harness actually loads — for Claude Code
  `$HOME/.claude/CLAUDE.md` (check what exists; some setups symlink it into a dotfiles repo, and
  other harnesses load their own user-level files, so confirm what yours actually reads). Use for
  OS, toolchain, CLI ergonomics, shell quoting, generic tool gotchas.
- **Workspace instruction file:** `<repo-root>/AGENTS.md` (the cross-agent convention), or
  `CLAUDE.md` where that's what the repo uses. Use for project conventions, paths, infra
  specifics. If neither exists and the lesson is project-scoped, ask before creating one.
- **Session memory (if present):** the harness names the directory in its system prompt (Claude
  Code: `$HOME/.claude/projects/<project-key>/memory/`, with `MEMORY.md` as the index).
- **Skills repo (full mode):** where new skills go. `--skills-repo <path>` names it; otherwise
  use the repo this skill was invoked from if it holds skills (a `skills/` directory, or
  `plugins/*/skills/` for a themed marketplace repo), else ask. New skills land at
  `skills/<name>/SKILL.md` or under the fitting `plugins/<theme>/skills/`, and are registered
  however that repo expects (a manifest entry, a marketplace entry) — read its AGENTS.md.
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

## Quick mode procedure

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

## Full mode: 30-day analysis

`/learn --full [--skills-repo <path>]` runs the quick-mode scan on the current session *and*
the analysis below. Delegate steps 1 to 3 to a sub-agent for the same reason as above; it
returns the proposal document, and the main session presents and applies.

### Step 1 — Gather session data

Prefer the harness's per-session summaries. On Claude Code:

```bash
find "$HOME/.claude/usage-data/facets" -name "*.json" -type f -mtime -30
```

Read each facet's `brief_summary`, `goal_categories`, `friction_detail`, `outcome`, and
`session_type`. Where a session has no facet (or the harness writes none), read its transcript
using the `claude-session-transcript` conventions — but only for those sessions; transcripts
are large.

### Step 2 — Cluster recurring patterns

Group sessions by the semantic similarity of their summaries and goal categories. Look for:

- The same goal category in three or more sessions.
- Similar task descriptions across different projects (several "bootstrap a project" sessions
  under different repos, say).
- Repeated tool sequences (every session of one kind starting with the same verification dance).

A pattern qualifies as a new-skill proposal when it appears three or more times in the window,
involves a repeatable procedure no existing skill already captures, and would save meaningful
setup time as a single invocation. Check the skills repo and the currently linked skills before
proposing; a near-miss is an edit to an existing skill, not a new one.

### Step 3 — Identify existing-skill friction

Look for:

- `friction_detail` entries that mention a skill by name or describe behaviour a skill should
  have prevented.
- Failed tool calls that a skill's "verify first" guidance would have caught.
- Sessions where the user corrected the agent on something a skill explicitly covers, which
  means the skill either wasn't loaded or isn't working.

Cross-reference against the skills repo to propose concrete edits.

### Step 4 — Write the proposal document

Write `PROPOSED_SKILLS.md` in the current working directory:

```markdown
# Proposed Changes — YYYY-MM-DD

## Section 1: Instruction-file edits (from the current session)

### [target: global | workspace]
**Section:** [existing header or "new section"]
**Proposed text:**
[the addition verbatim]
**Why:** [cite the session moment]

## Section 2: New skill proposals

### Skill: `[name]` (N occurrences)
**One-liner:** [description for the SKILL.md frontmatter]
**Sessions observed:**
- [summary excerpt 1]
- [summary excerpt 2]
**Procedure sketch:** [what the skill would do, in 3-5 bullet points]
**Where it lands:** [path in the skills repo, and how it gets registered there]

## Section 3: Existing-skill friction

### Skill: `[name]`
**Issue:** [what went wrong]
**Evidence:** [session id or summary excerpt]
**Proposed edit:** [concrete change to the skill's SKILL.md]
```

Show the document and wait for explicit approval on each item; the user may approve all, some,
or none.

### Step 5 — Apply approved changes

- **Instruction-file edits:** the quick-mode rules apply (edit the real file behind any
  symlink).
- **New skill:** create its SKILL.md in the skills repo (format below), register it the way the
  repo expects, and commit locally. Do not push.
- **Existing-skill fix:** edit that skill's SKILL.md and commit with the rest, or separately if
  the user prefers.

## Writing a new SKILL.md

Minimum viable SKILL.md:

```markdown
---
name: <kebab-case-name>
description: <1–3 sentences: what the skill does + the trigger phrases that should invoke it>
---

# <Title>

<What the skill does and when to use it — 1-2 sentences.>

## Procedure

1. ...
2. ...

## Where things live

...
```

Guidelines:

- The `description` is loaded into every session whether or not the skill fires — keep it to
  1–3 sentences (what the skill does + when to trigger it). Procedure detail belongs in the
  body, which loads only on invocation.
- Lead with "Use when the user asks to X" or "Covers Y, Z, W."
- A skill that grows past a few hundred lines should split topic content into `references/*.md`
  files the body points at, so an invocation loads only what the task needs.
- Include a "Where things live" section for any skill that reads or writes files.
- If the skill produces output for user review before taking action, say so explicitly.
- If the skill wraps another skill, call it out: "Read `claude-session-transcript` first."
- Write it to survive a change of harness — the `agent-agnostic-skills` skill has the rules and
  a scanner.
- Keep it scannable — a future session reads it cold and needs to know what to do in under 30
  seconds.

## Style for the additions

- **Rule first, then `Why:`** — one sentence each; the why lets future sessions judge edge cases.
- **Imperative, not narrative.** "Use `op run --env-file`" beats "I learned that…".
- **No session-specific names** — generalize so the lesson reads correctly in six months.
- **No editorializing** ("this is important") and code fences for commands, with ✗/✓ framing
  where the wrong pattern is instructive.

## Self-update: improving this skill

If the session surfaced a kind of learning the signal list missed, a new sensible home for
lessons, a heuristic here that steered wrong, or a cluster full mode missed that was obvious in
retrospect, the skill itself is a valid edit target. Treat self-updates like any other
proposal: show the diff, cite the motivating moment, wait for confirmation, and keep the
frontmatter description in sync if the scope changes. Don't expand speculatively.

## Things to avoid

- No learnings the transcript can't support — if you can't cite the moment, don't propose it.
- Don't contradict existing instructions without flagging the conflict explicitly.
- Keep lessons granular so the user can accept/reject individually.
- Never write to an instruction file without showing the diff first.
- In full mode, don't propose a new skill for a one-off task — the three-occurrence threshold
  exists for a reason.
- Don't open PRs or push to remote. Commit locally; the user pushes.
