# dev-tools

Engineering utilities that stand on their own: Jujutsu version control, an evidence-based
dependency scorer, conventions for command-line tools that programs drive, adversarial code
review, and a release gate that tests every distribution channel.

## Installing

### Claude Code

```
/plugin marketplace add curtisgalloway/public-skills
/plugin install dev-tools@curtisg-skills
```

Add the marketplace once per machine. `curtisg-skills` is its name, set in
`.claude-plugin/marketplace.json`. Outside a session, run the same commands as `claude plugin
marketplace add ...` and `claude plugin install ...`. For a local clone, pass its path to
`marketplace add`. Update later with `/plugin marketplace update curtisg-skills`.

### Codex

```
codex plugin marketplace add curtisgalloway/public-skills
codex plugin add dev-tools@curtisg-skills
```

Update later with `codex plugin marketplace upgrade curtisg-skills`.

### Other agents

For Antigravity and other harnesses that read skill directories, clone the repo and link each
skill you want from `plugins/dev-tools/skills/<name>` into your skills root. The
[top-level README](../../README.md#installing) has the paths for each harness.

Skip all of this if you installed the `everything` plugin, which already includes these
skills. Installing both loads every skill twice.

## Skills

- **`jj`** — drive Jujutsu instead of git in any repo with a `.jj/` directory. Covers the
  working-copy-is-a-commit model, a git-to-jj command table, bookmarks and pushing, fetch and
  rebase, conflict resolution without the interactive tools, and recovery through the
  operation log. Written for an agent, so it pins the non-negotiables (`-m` always, never
  `-i`, verify after every mutation) and the colocated-repo rule (never a git write). Triggers
  on the `.jj/` directory or any mention of jj, and stays out of plain git repos.
- **`dep-quality`** — score the health of open-source packages (a 0 to 10 "Dependency Fitness
  Score") to choose between alternatives on evidence instead of fame.
  - Hard gates come first: license allowlist, archived repo, unpatched critical advisory.
  - Then a weighted geometric mean of responsiveness, adoption, bus factor, security hygiene,
    and release cadence. Bot and AI-agent commits don't count toward bus factor.

  Triggers before any new package is pinned in a manifest, even when the popular choice seems
  obvious. Ships `scripts/depscore.py` (stdlib-only; wants a read-only `GITHUB_TOKEN`).
- **`cli-conventions`** — how to build a command-line tool whose callers include programs,
  not just people.
  - A portable exit-code contract organized in bands, so a caller that has never seen the
    tool can branch on `code / 10` and still behave sensibly.
  - A `--skill` flag that prints the tool's own agent-facing doc, embedded at build time so it
    cannot drift from the binary.
  - The rules that only bite once the caller is not a human: strict `--json`, the
    stdout/stderr split, no prompting without a TTY, `--dry-run`, and secrets never in argv.
  - A four-line CI harness that catches most of it.

  Triggers when writing or reviewing a CLI, or deciding what a command should return when it
  fails.
- **`review-swarm`** — adversarial review of a diff or pull request, sized to the change for
  the most verified findings per token.
  - `scripts/swarm.py plan` reads the diff and picks the tier: one generalist reviewer for
    prose-only diffs and small code changes; four or five for ordinary code; all seven
    narrow-mandate reviewers (security, correctness, compatibility, docs versus reality,
    history, the project's written rules, performance) when the change touches secrets or
    auth, concurrency or a persisted format, or closes a pull request or milestone. The
    correctness reviewer runs on the strong model, the others on a cheaper one.
  - Every reviewer may report only what it can quote verbatim from the checkout. A stdlib
    checker (`swarm.py verify`) re-reads every cited `file:line`, drops findings whose quote is
    not there, merges plain duplicates, and marks findings that touch no hunk of the diff. Any
    reviewer that produced no usable output is marked `ARM FAILED` in capitals instead of
    vanishing.
  - A referee subagent judges high-severity findings and possible duplicates; after fixes, one
    cheap recheck confirms each fix by quote instead of a second review.

  Ends with one ranked table and the question of which findings to fix; on request, posts the
  result to the pull request with permalinks. Triggers on "review this PR", "adversarial
  review", "red-team this diff".
- **`release-train`** — cut a release only after every distribution channel has passed: a
  `.deb` through an apt repo, a Homebrew keg, a portable zip, a from-source install, a
  registry.
  - Each channel is built, installed the way a user would in a throwaway prefix, and
    smoke-tested end to end by its own parallel subagent.
  - Meanwhile a regression archaeologist pins every previously fixed bug that has no
    executing test.
  - Any failure blocks and becomes an issue with a minimal reproduction. All-green tags,
    pushes, publishes, then re-verifies the published artifacts from the URLs a user would
    use.

  Driven by a per-repo `RELEASE-TRAIN.md` profile the skill constructs (`init`), checks for
  drift (`check`), and executes (`run`). Ships `scripts/profile_check.py` (stdlib-only) so the
  profile cannot quietly describe last quarter's packaging.
