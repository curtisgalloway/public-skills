---
name: locked-skill
description: SYNTHETIC TEST FIXTURE - a skill welded to one harness. Every finding here is deliberate.
---

# Locked skill

Install this skill to `~/.claude/skills/locked-skill/` and it will be picked up
automatically. Add the standing rules to your `CLAUDE.md` so they survive
compaction.

Run the helper:

```bash
python3 ~/.claude/skills/locked-skill/scripts/helper.py /home/rjmiller/src/project
```

The hook reads `$CLAUDE_PROJECT_DIR` to find the project root.
