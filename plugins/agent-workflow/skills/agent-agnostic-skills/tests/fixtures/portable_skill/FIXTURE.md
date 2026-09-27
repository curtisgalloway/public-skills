---
name: portable-skill
description: SYNTHETIC TEST FIXTURE - the same skill written to survive a change of harness.
---

# Portable skill

Install this skill wherever your agent discovers skills — `~/.gemini/antigravity/skills/` or
`<workspace>/.agents/skills/` for Antigravity, `~/.claude/skills/` for Claude Code — and confirm
with `/skills` that it loaded. Below, `<portable-skill>` stands for wherever it landed.

Add the standing rules to `AGENTS.md` at the workspace root. Use a harness-specific context file
(`GEMINI.md`, `CLAUDE.md`) only for wording that must differ: it overrides `AGENTS.md`, so a second
full copy drifts from the one you edit.

Run the helper:

```bash
python3 <portable-skill>/scripts/helper.py <path/to/project>
```

The helper finds the project root from the event payload, falling back to whichever project
variable the harness exports.
