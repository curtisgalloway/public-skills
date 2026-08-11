# public-skills

A collection of reusable agent skills designed to be generally agent-neutral. Skills have been developed and tested primarily with Claude Code and Gemini, but are written to work with any agent that supports the skill/slash-command pattern.

## What's here

Each skill lives in its own directory under `skills/` and contains at minimum a `SKILL.md` describing its purpose, inputs, and behavior. Some skills include supporting scripts or templates.

### Clean-room driver porting

Three skills compose into one pipeline for reimplementing a driver in a differently-licensed OS, splitting the work across contexts so encumbered source never reaches the one that writes the new code:

- **`os-investigator`** — the dirty-side method: read the original source and return hardware facts and mechanism prose, never code, every fact tagged by provenance class. Ships `scripts/leak_scan.py`, the mechanical leak scanner.
- **`peripheral-spec`** — orchestration and the wall: the transfer protocol, the independent five-check verifier, mandatory scanning, and the evidentiary provenance ledger.
- **`cleanroom-implementer`** — the consumer side: standing rules for the implementing agent, enforcement (a pre-tool-use hook, Gemini policy-engine rules, a restricted subagent definition, policy and settings fragments), and the session/artifact audit.

Enforcement install material targets **Gemini CLI** (`BeforeTool` hook, `.gemini/settings.json`, `~/.gemini/policies/*.toml`, `.gemini/agents/`) and **Antigravity** (`PreToolUse` hook in `.agents/hooks.json`, workspace rules, task artifacts under `~/.gemini/antigravity/brain/`). The two shipped Python scripts are harness-neutral — they key off argument names and event fields rather than tool-name tables — so they also run unchanged under Claude Code with `.claude/` paths and `$CLAUDE_PROJECT_DIR`.

Board-expert skills (e.g. `rpi-expert`, `indiedroid-nova-expert`) supply the per-SoC map and are dirty-side roles that `os-investigator` calls into. The `assets/` under `cleanroom-implementer` are install material for *consuming* projects — they are not this repo's own configuration.

## Using these skills

Skills are designed to be dropped into an agent's skills directory and invoked via slash command or natural language trigger. See each skill's `SKILL.md` for trigger phrases, required tools, and usage notes.

Most skills assume:
- A Unix-like shell (macOS or Linux)
- Standard CLI tools (`git`, `curl`, etc.) available on `PATH`
- Any skill-specific dependencies called out in the skill's own docs

### Installing in Gemini CLI

Skills are plain directories, so point Gemini CLI's context at them and load a skill by name. The
simplest route is a clone plus an import line in your context file:

```bash
git clone https://github.com/curtisgalloway/public-skills ~/src/public-skills
```

```markdown
<!-- in GEMINI.md or AGENTS.md -->
@~/src/public-skills/skills/peripheral-spec/SKILL.md
```

To make `AGENTS.md` the context file Gemini CLI reads, set it in `~/.gemini/settings.json`:

```json
{ "context": { "fileName": ["AGENTS.md", "GEMINI.md"] } }
```

Skills written as subagent roles (`os-investigator`, and the shipped
`cleanroom-implementer/assets/driver-implementer.md`) install as `.gemini/agents/*.md` and are
invoked with `@<name>`.

### Installing in Antigravity

Copy or symlink the skills you want into the workspace rules directory (`.agent/rules/` in current
builds — confirm in your build's rules panel), or reference them from `AGENTS.md` at the workspace
root, which Antigravity reads. Subagent definitions go in `<workspace>/.agents/`, and hooks in
`<workspace>/.agents/hooks.json`. Note that workspace-local hooks load only in a **trusted**
workspace, and that hooks are the `agy` CLI's mechanism — verify they fire in the surface you
actually use before relying on them.

### Installing in Claude Code

This repo is a Claude Code plugin. Add it as a marketplace and install:

```bash
claude plugins marketplace add curtisgalloway/public-skills
claude plugins install public-skills@public-skills
```

Or install directly from a local clone:

```bash
claude plugins install --path /path/to/public-skills
```

## License

Apache 2.0 — see [LICENSE](LICENSE).
