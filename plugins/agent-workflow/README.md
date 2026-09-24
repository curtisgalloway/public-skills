# agent-workflow

Skills for working with a coding agent over time, not one prompt at a time: think a design
through before building, keep a long session from thrashing, hand work across a context clear,
summarize what happened, turn the lessons into instructions, review a document with a
stakeholder, and write skills that survive a change of harness.

## Installing

### Claude Code

```
/plugin marketplace add curtisgalloway/public-skills
/plugin install agent-workflow@curtisg-skills
```

Add the marketplace once per machine. `curtisg-skills` is its name, set in
`.claude-plugin/marketplace.json`. Outside a session, run the same commands as `claude plugin
marketplace add ...` and `claude plugin install ...`. For a local clone, pass its path to
`marketplace add`. Update later with `/plugin marketplace update curtisg-skills`.

### Codex

```
codex plugin marketplace add curtisgalloway/public-skills
codex plugin add agent-workflow@curtisg-skills
```

Update later with `codex plugin marketplace upgrade curtisg-skills`.

### Other agents

For Antigravity and other harnesses that read skill directories, clone the repo and link each
skill you want from `plugins/agent-workflow/skills/<name>` into your skills root. The
[top-level README](../../README.md#installing) has the paths for each harness.

Skip all of this if you installed the `everything` plugin, which already includes these
skills. Installing both loads every skill twice.

## A session, start to finish

- **`design-partner`** — before anything is built: a thinking partner for design,
  architecture, and brainstorming. It explores the problem, lays out options and trade-offs,
  and pushes back, without touching code. Triggers on "let's brainstorm", "should I", "talk
  me through the trade-offs"; drops when the user says to build.
- **`consult`** — ask the other coding agent to assess a question independently, then trade
  follow-ups until both confirm a recommendation. Claude Code consults Codex and Codex
  consults Claude Code; the original conversation stays in charge. Ships a Python helper for
  restricted peer sessions, resumable context, bounded rounds, cancellation, and local
  transcripts. Needs Python 3.9+, macOS or Linux, and an authenticated counterpart CLI.
  Triggers on "consult your counterpart" or "work toward consensus".
- **`project-plan`** — turn a project outcome into a detailed design, then an implementation
  plan of cohesive milestones, each sized for about 75% of a fresh session's context.
  - A new or materially revised design needs approval unless waived; an unchanged
    authoritative design is reused.
  - A milestone needs testing, review, and linked evidence before it is complete, and gets
    its own `lab-notebook` chapter.
  - By default it commits at every checkpoint, stops after one milestone for user review, and
    writes a handoff for a fresh session. Unfinished work is handed off without advancing.

  Triggers on "plan this project", "turn this design into an implementation plan", or "break
  this work into milestones".
- **`lab-notebook`** — during: an append-only, timestamped notebook with one chapter per unit
  of work (attempts, dead ends, decisions, surprises). Its index carries timestamps that show
  when it has fallen behind. A per-project process log records where the agent's process cost
  time, as input for improving its instructions and skills. `project-plan` uses one chapter
  per milestone. Triggers on "keep a lab notebook" or "take notes as you go".
- **`intern-mode`** — during: a loop-safety posture. After twelve turns without meaningful
  progress, the agent stops, files a stuck report, and waits for direction. Stays active until
  explicitly released. Use it for "stop if you get stuck" and against silent thrashing.
- **`handoff`** — across a context clear or restart. Write mode dumps a `HANDOFF.md` the next
  session can cold-start from (task, state, decisions, dead ends, next steps); resume mode
  reads it back and continues. The reasoning is in [How To Claude](../../docs/how-to-claude.md).
- **`learn`** — after: review the session transcript for lessons that would have made it go
  smoother (failed commands, wrong tool arguments, user corrections, environment surprises)
  and propose additions to the workspace or global instruction file. It also reads the
  project's `lab-notebook` process log, routes each open entry to where its fix belongs, and
  records the outcome in the log. This is the path from private auto-memory to reviewed,
  versioned instructions.
- **`teach`** — later: summarize past sessions into teaching-oriented Markdown, one file per
  session not yet summarized (keyed on the session id in existing summary frontmatter).

**`claude-session-transcript`** is not user-invocable. It is the shared reference the
transcript-reading skills load before parsing: where the live Claude Code transcript is on
disk, and how to extract real user prompts from it (filter rules, slash-command pair
collapsing, noise stripping).

> `learn`, `teach`, and `claude-session-transcript` are written against Claude Code's
> session layout and have not been ported to other harnesses yet.

## Reviewing a document with someone

- **`gdoc-review-loop`** — review a repo-owned Markdown document with a stakeholder through
  Google Docs, in numbered rounds.
  - The file in git stays the source of truth; each round is a new Doc built from it.
  - The reviewer's direct edits (decisions) and margin comments (instructions) are read back
    and applied, and the reply to their comments opens the next round.
  - Round state lives in Doc titles, because the Drive tooling can neither update a Doc's
    content in place nor write comments.

  Needs a Google Drive MCP server. Ships two stdlib-only scripts: `scripts/round_text.py`
  builds the round text, and `scripts/doc_diff.py` finds direct edits under the
  Markdown-to-Doc-to-text conversion noise.

## Writing skills that outlive a harness

- **`agent-agnostic-skills`** — how to write skills, hooks, subagent definitions, and
  agent-facing scripts that survive a change of agent, and how to port one that didn't.
  Harness lock-in fails silently: a tool-name table that matches nothing allows everything.
  The skill is mostly about turning those invisible no-ops into checkable behavior. Ships
  `scripts/portability_scan.py` (a mechanical check for these assumptions), a dated
  cross-harness reference matrix under `references/`, and tests under `tests/`.

## Tests

```bash
python3 -m unittest discover -s plugins/agent-workflow/skills/agent-agnostic-skills/tests -v
python3 -m unittest discover -s plugins/agent-workflow/skills/consult/tests -v
```
