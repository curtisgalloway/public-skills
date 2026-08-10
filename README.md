# public-skills

A collection of reusable agent skills designed to be generally agent-neutral. Skills have been developed and tested primarily with Claude Code and Gemini, but are written to work with any agent that supports the skill/slash-command pattern.

## What's here

Each skill lives in its own directory under `skills/` and contains at minimum a `SKILL.md` describing its purpose, inputs, and behavior. Some skills include supporting scripts or templates.

### Clean-room driver porting

Three skills compose into one pipeline for reimplementing a driver in a differently-licensed OS, splitting the work across contexts so encumbered source never reaches the one that writes the new code:

- **`os-investigator`** — the dirty-side method: read the original source and return hardware facts and mechanism prose, never code, every fact tagged by provenance class. Ships `scripts/leak_scan.py`, the mechanical leak scanner.
- **`peripheral-spec`** — orchestration and the wall: the transfer protocol, the independent five-check verifier, mandatory scanning, and the evidentiary provenance ledger.
- **`cleanroom-implementer`** — the consumer side: standing rules for the implementing agent, enforcement (a PreToolUse hook, a restricted agent definition, policy and settings fragments), and the session transcript audit.

Board-expert skills (e.g. `rpi-expert`, `indiedroid-nova-expert`) supply the per-SoC map and are dirty-side roles that `os-investigator` calls into. The `assets/` under `cleanroom-implementer` are install material for *consuming* projects — they are not this repo's own configuration.

## Using these skills

Skills are designed to be dropped into an agent's skills directory and invoked via slash command or natural language trigger. See each skill's `SKILL.md` for trigger phrases, required tools, and usage notes.

Most skills assume:
- A Unix-like shell (macOS or Linux)
- Standard CLI tools (`git`, `curl`, etc.) available on `PATH`
- Any skill-specific dependencies called out in the skill's own docs

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
