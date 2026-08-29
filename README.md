# public-skills

A collection of reusable agent skills designed to be generally agent-neutral. Skills have been developed and tested primarily with Google Antigravity (the `agy` CLI and the IDE) and Claude Code, but are written to work with any agent that supports the skill/slash-command pattern.

## What's here

Each skill lives in its own directory under `skills/` and contains at minimum a `SKILL.md` describing its purpose, inputs, and behavior. Some skills include supporting scripts or templates.

### Writing skills that outlive a harness

- **`agent-agnostic-skills`** — how to write skills, hooks, subagent definitions and agent-facing
  scripts that survive a change of agent, and how to port one that didn't. Harness lock-in fails
  silently — a tool-name table that matches nothing allows everything — so the skill is mostly about
  turning invisible no-ops into checkable behaviour. Ships `scripts/portability_scan.py` and a dated
  cross-harness reference matrix.

### Fuchsia — moved to its own repo

The Fuchsia skills now live in
**[curtisgalloway/fuchsia-skills](https://github.com/curtisgalloway/fuchsia-skills)** — checking out
the tree, bridging its Gemini-oriented in-tree agent config into Claude Code, running several
workstreams on one machine, deep source questions, driver bind debugging, and the hardware
bench / boot-test CI pair. Install it alongside this plugin:

```
/plugin marketplace add curtisgalloway/fuchsia-skills
/plugin install fuchsia-skills@fuchsia-skills
```

`os-investigator`, `cleanroom-spec`, and the board experts stayed here — they are not
Fuchsia-specific, and the Fuchsia skills hand off to them by name.

### Clean-room driver porting

Three skills compose into one pipeline for reimplementing a driver in a differently-licensed OS, splitting the work across contexts so encumbered source never reaches the one that writes the new code:

- **`os-investigator`** — the dirty-side method: read the original source and return hardware facts and mechanism prose, never code, every fact tagged by provenance class. Ships `scripts/leak_scan.py`, the mechanical leak scanner.
- **`cleanroom-spec`** — orchestration and the wall: the transfer protocol, the independent five-check verifier, mandatory scanning, and the evidentiary provenance ledger.
- **`cleanroom-implementer`** — the consumer side: standing rules for the implementing agent, enforcement (a `PreToolUse` hook, permission deny rules, a restricted subagent definition, policy fragments), and the session/artifact audit.

Enforcement install material targets **Antigravity**: a `PreToolUse` hook in `<workspace>/.agents/hooks.json`, permission deny rules, a sandboxed `driver-implementer` subagent in `.agents/agents/`, the `AGENTS.md` standing block, and audits over session transcripts and task artifacts (`~/.gemini/antigravity/brain/<GUID>/`). The two shipped Python scripts are harness-neutral — they key off argument names and event fields rather than tool-name tables — so they also run unchanged under Claude Code with `.claude/` paths.

Board-expert skills (e.g. `rpi-expert`, `indiedroid-nova-expert`) supply the per-SoC map and are dirty-side roles that `os-investigator` calls into. The `assets/` under `cleanroom-implementer` are install material for *consuming* projects — they are not this repo's own configuration.

### Source-anchored driver specs

- **`anchored-peripheral-spec`** — the same per-peripheral spec shape as `cleanroom-spec`, for
  driver source you (or your organization) authored or may otherwise copy from — where the wall is
  not just unnecessary but in the way. Every source-derived fact carries a
  `[src: path:L1-L2 (symbol)]` anchor at a pinned commit, so a reviewer can check the spec against
  the code and the checker can tell which claims need re-reading when the tree moves. Ships
  `scripts/anchor_check.py` (stdlib-only): resolves anchors, renders a claim-vs-source review
  sheet (`--show`), and detects and rewrites drift when re-pinning (`--drift REV --rewrite`).
  Not a substitute for `cleanroom-spec` on encumbered source — an anchored spec is a derivative
  of its source by design.

### Dependency evaluation

- **`dep-quality`** — score the health of open-source packages (0–10 "Dependency Fitness
  Score") to choose between dependency alternatives on evidence instead of fame. Hard gates
  (license allowlist, archived repo, unpatched critical advisory), then a weighted geometric
  mean of responsiveness, adoption, bus factor, security hygiene, and release cadence.
  Bot and AI-agent commits are excluded from bus factor. Ships `scripts/depscore.py`
  (stdlib-only; wants a read-only `GITHUB_TOKEN`).

### Version control

- **`jj`** — drive Jujutsu instead of git in any repo that has a `.jj/` directory: the
  working-copy-is-a-commit mental model, a git→jj command table, bookmarks and pushing, fetch/rebase,
  conflict resolution without the interactive tools, and recovery via the operation log. Written
  for an agent, so it pins the non-negotiables (`-m` always, never `-i`, verify after every
  mutation) and the colocated-repo rule (never a git write).

## Guides

- [How To Claude](docs/how-to-claude.md) — session hygiene for working with Claude: one topic per
  session, keeping context short, thinking before the first message, knowing when to start over,
  and handing off between sessions (the reasoning behind the `handoff` skill).

## Using these skills

Skills are designed to be dropped into an agent's skills directory and invoked via slash command or natural language trigger. See each skill's `SKILL.md` for trigger phrases, required tools, and usage notes.

Most skills assume:
- A Unix-like shell (macOS or Linux)
- Standard CLI tools (`git`, `curl`, etc.) available on `PATH`
- Any skill-specific dependencies called out in the skill's own docs

### Installing in Antigravity

Skills are plain directories. Clone the repo and put the skills you want where your build
discovers them — `~/.gemini/antigravity/skills/` for user-level, `<workspace>/.agents/skills/`
for one project, or inside a plugin's `skills/` directory:

```bash
git clone https://github.com/curtisgalloway/public-skills ~/src/public-skills
ln -s ~/src/public-skills/skills/cleanroom-spec ~/.gemini/antigravity/skills/cleanroom-spec
```

Check with `/skills` that they loaded. Skills that are subagent roles (`os-investigator`, and the
shipped `cleanroom-implementer/assets/driver-implementer.md`) install instead as
`<workspace>/.agents/agents/<name>.md` with `subagent: true` in the frontmatter, and show up under
`/agents`. Workspace-wide instructions go in `AGENTS.md` at the workspace root, or as rules under
`.agent/rules/`.

Antigravity has relocated skills, hooks and settings between releases, so confirm the paths your
build actually reads before assuming an install took — the slash commands above are the quickest
check.

> Skills that read agent transcripts (`learn`, `teach`, `wrapup`, `claude-session-transcript`) are
> still written against Claude Code's session layout and have not been ported.

### Installing in Claude Code

This repo is a Claude Code plugin and hosts its own single-plugin marketplace
(`.claude-plugin/marketplace.json`; skills are auto-discovered from `skills/`). In a session, or
with the `claude plugin` CLI outside one:

```
/plugin marketplace add curtisgalloway/public-skills
/plugin install public-skills@public-skills
```

For a local clone, add the clone directory as the marketplace instead:

```
/plugin marketplace add /path/to/public-skills
/plugin install public-skills@public-skills
```

## License

Apache 2.0 — see [LICENSE](LICENSE).
