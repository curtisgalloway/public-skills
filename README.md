# public-skills

A collection of reusable agent skills designed to be generally agent-neutral. Skills have been developed and tested primarily with Claude Code and Gemini, but are written to work with any agent that supports the skill/slash-command pattern.

## What's here

Each skill lives in its own directory under `skills/` and contains at minimum a `SKILL.md` describing its purpose, inputs, and behavior. Some skills include supporting scripts or templates.

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
