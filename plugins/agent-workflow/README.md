# agent-workflow

Skills for working with a coding agent over time rather than one prompt at a time: think a
design through before building, keep a long session from thrashing, hand work across a context
clear, summarize what happened, turn the lessons into instructions, review a document with a
stakeholder, and write skills that survive a change of harness.

## Installing

### Claude Code

Add this repo as a plugin marketplace (once per machine), then install the plugin:

```
/plugin marketplace add curtisgalloway/public-skills
/plugin install agent-workflow@curtisg-skills
```

`curtisg-skills` is the marketplace's name, set in `.claude-plugin/marketplace.json`; it is
what follows the `@`. Outside a session, the same commands run as `claude plugin marketplace
add ...` and `claude plugin install ...`. To install from a local clone instead, pass the
clone's path to `marketplace add`. To pick up new versions later:

```
/plugin marketplace update curtisg-skills
```

Skip this if you installed the `everything` plugin, which already includes these skills;
installing both loads every skill twice.

### Other agents

Antigravity and other harnesses that read skill directories: clone the repo and link the
skill you want from `plugins/agent-workflow/skills/<name>` into your skills root. The
[top-level README](../../README.md#installing) has the paths for each harness.

## A session, start to finish

- **`design-partner`** — before anything is built: a thinking-partner posture for design,
  architecture, and brainstorming that explores the problem, lays out options and trade-offs,
  and pushes back, without touching code. Triggers on "let's brainstorm", "should I", "talk me
  through the trade-offs"; drops when the user says to build.
- **`consult`** — ask the other coding agent to independently assess a question, then
  exchange follow-ups toward an explicitly confirmed recommendation. Claude Code consults
  Codex and Codex consults Claude Code; the original conversation stays in charge. Ships a
  Python helper for restricted peer sessions, resumable context, bounded rounds, cancellation,
  and local transcripts. Requires Python 3.9+, macOS/Linux, and an authenticated counterpart
  CLI. Triggers on "consult your counterpart" or "work toward consensus".
- **`project-plan`** — turn a project outcome into a detailed design and an implementation
  plan. Requires approval for a new or materially revised design unless waived, reuses
  an unchanged authoritative design, and builds cohesive milestones sized for roughly
  75% of a fresh session's context. Requires testing, review, and linked evidence before
  completion. Commits at every checkpoint by default and stops after one milestone for
  user review, with a handoff for a fresh session; unfinished work is handed off without
  advancing. Triggers on
  "plan this project", "turn this design into an implementation plan", or "break this
  work into milestones".
- **`intern-mode`** — during: a loop-safety posture. After twelve turns without meaningful
  progress the agent stops, files a stuck report, and waits for direction. Stays active until
  explicitly released. For "stop if you get stuck" and protection against silent thrashing.
- **`handoff`** — across a context clear or restart: write mode dumps a `HANDOFF.md` the next
  session can cold-start from (task, state, decisions, dead ends, next steps); resume mode reads
  it back and continues. The reasoning behind it is in
  [How To Claude](../../docs/how-to-claude.md).
- **`learn`** — after: review the session transcript for lessons that would have made it go
  smoother (failed commands, wrong tool arguments, user corrections, environment surprises) and
  propose additions to the workspace or global instruction file. The promotion path from
  private auto-memory into reviewed, versioned instructions.
- **`teach`** — later: summarize past sessions into teaching-oriented Markdown, one file per
  session not yet summarized (keyed on the session id in existing summary frontmatter).

**`claude-session-transcript`** is the shared reference the transcript-reading skills load
before parsing: where the live Claude Code transcript is on disk and how to extract real user
prompts from it (filter rules, slash-command pair collapsing, noise stripping). It is not a
user-invocable skill.

> `learn`, `teach`, and `claude-session-transcript` are written against Claude Code's
> session layout and have not been ported to other harnesses yet.

## Reviewing a document with someone

- **`gdoc-review-loop`** — review a repo-owned Markdown document with a stakeholder through
  Google Docs, in numbered rounds: the file in git stays the source of truth, each round is a
  new Doc built from it, the reviewer's direct edits (decisions) and margin comments
  (instructions) are read back and applied, and the reply to their comments opens the next
  round. Round state lives in Doc titles because the Drive tooling can neither update a Doc's
  content in place nor write comments. Needs a Google Drive MCP server. Ships
  `scripts/round_text.py` (builds the round text) and `scripts/doc_diff.py` (finds direct
  edits under the Markdown-to-Doc-to-text conversion noise), both stdlib-only.

## Writing skills that outlive a harness

- **`agent-agnostic-skills`** — how to write skills, hooks, subagent definitions, and
  agent-facing scripts that survive a change of agent, and how to port one that didn't.
  Harness lock-in fails silently: a tool-name table that matches nothing allows everything, so
  the skill is mostly about turning invisible no-ops into checkable behavior. Ships
  `scripts/portability_scan.py`, a mechanical check for these assumptions, a dated
  cross-harness reference matrix under `references/`, and tests under `tests/`.

## Tests

```bash
python3 -m unittest discover -s plugins/agent-workflow/skills/agent-agnostic-skills/tests -v
python3 -m unittest discover -s plugins/agent-workflow/skills/consult/tests -v
```
