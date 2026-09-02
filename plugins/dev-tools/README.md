# dev-tools

Engineering utilities that stand on their own: a version-control skill for Jujutsu, and an
evidence-based scorer for choosing dependencies.

```
/plugin install dev-tools@public-skills
```

Antigravity and other harnesses that read skill directories: link the skill you want from
`plugins/dev-tools/skills/<name>` into your skills root.

## Skills

- **`jj`** — drive Jujutsu instead of git in any repo that has a `.jj/` directory: the
  working-copy-is-a-commit mental model, a git-to-jj command table, bookmarks and pushing,
  fetch and rebase, conflict resolution without the interactive tools, and recovery via the
  operation log. Written for an agent, so it pins the non-negotiables (`-m` always, never `-i`,
  verify after every mutation) and the colocated-repo rule (never a git write). Triggers on the
  `.jj/` directory or any mention of jj, and stays out of plain git repos.
- **`dep-quality`** — score the health of open-source packages (a 0 to 10 "Dependency Fitness
  Score") to choose between dependency alternatives on evidence instead of fame. Hard gates
  first (license allowlist, archived repo, unpatched critical advisory), then a weighted
  geometric mean of responsiveness, adoption, bus factor, security hygiene, and release
  cadence. Bot and AI-agent commits are excluded from bus factor. Triggers before any new
  package is pinned in a manifest, even when the popular choice seems obvious. Ships
  `scripts/depscore.py` (stdlib-only; wants a read-only `GITHUB_TOKEN`).
