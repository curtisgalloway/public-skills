# dev-tools

Engineering utilities that stand on their own: a version-control skill for Jujutsu, an
evidence-based scorer for choosing dependencies, and the conventions that make a command-line
tool drivable by a program.

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
- **`cli-conventions`** — how to build a command-line tool whose callers include programs, not
  just people. A portable exit-code contract organized in bands, so a caller that has never seen
  the tool can branch on `code / 10` and still behave sensibly; a `--skill` flag that prints the
  tool's own agent-facing doc, embedded at build time so it cannot drift from the binary; and the
  rules that only bite once the caller is not a human — strict `--json`, the stdout/stderr split,
  no prompting without a TTY, `--dry-run`, secrets never in argv, and a four-line CI harness that
  catches most of it. Triggers when writing or reviewing a CLI, or deciding what a command should
  return when it fails.
- **`review-swarm`** — adversarial review of a diff or pull request by four independent reviewer
  subagents with non-overlapping mandates (security and secrets; correctness and concurrency;
  data loss, migration and backward compatibility; documentation-vs-reality), each forbidden from
  reporting anything it cannot quote verbatim from the checkout. A stdlib checker
  (`scripts/swarm.py verify`) re-reads every cited `file:line`, drops findings whose quote is not
  there, merges plain duplicates, and marks any arm that produced no usable output `ARM FAILED`
  in capitals rather than letting it vanish; a referee subagent then judges whether the code
  supports each surviving claim and resolves the rest of the duplicates. Ends with one ranked
  table and the question of which findings to fix. Triggers on "review this PR", "adversarial
  review", "red-team this diff".
