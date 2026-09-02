---
name: jj
description: Use Jujutsu (jj) for version control instead of git. Trigger whenever a `.jj/` directory exists in the repo, or the user mentions jj or jujutsu, and then for ANY version-control operation in that repo — status, diff, log, commit, branch, bookmark, push, fetch, rebase, squash, split, conflict resolution, undo, or history rewriting. Do not trigger in plain git repos with no `.jj/`.
---

<!--
SPDX-FileCopyrightText: 2026 Curtis Galloway
SPDX-License-Identifier: Apache-2.0
-->

# Jujutsu (jj)

## Confirm you're in a jj repo

Run `jj st`. If it errors that there's no jj repo, stop using this skill and use git.

If both `.jj/` and `.git/` exist, the repo is **colocated**. Git commands will appear to work, but jj re-imports git state on every jj command, and a git write can leave the two out of sync. Read-only git (`git log`, `git show`) is fine. Never run a git command that writes: `add`, `commit`, `checkout`, `reset`, `stash`, `rebase`, `push`.

## Non-negotiables

jj's defaults assume a human with an editor and a pager. You are neither.

- Always pass `-m` to `describe` and `commit`. Without it jj opens `$EDITOR` and the command hangs forever.
- Never pass `-i` / `--interactive`, and never run `jj diffedit` or `jj resolve`. These open a TUI diff editor and hang.
- Verify after every mutation with `jj st` and `jj log`. jj does not fail loudly the way git does — it will record a conflict and report success.

## Mental model

- **The working copy is a commit**, named `@`. Every jj command snapshots your file edits into `@` before doing anything else. There is no staging area, no `git add`, no `git stash`, and no "your local changes would be overwritten" errors.
- `@-` is `@`'s parent, `@--` its grandparent.
- **Change ID** is stable across rewrites (letters k–z, e.g. `qpvuntsm`). **Commit ID** is a content hash and changes on every rewrite. Reference commits by change ID.
- **Descendants rebase automatically.** Editing a commit rewrites everything stacked on it. That's the design, not a mistake.
- **Conflicts don't block.** A rebase or squash that conflicts still succeeds, recording the conflict in the commit. Success is not evidence of a clean result — check.
- **Everything is undoable** via the operation log.

## The normal loop

1. `jj st` — see where you are. If `@` already has a description or contains work that isn't yours, run `jj new` first so you don't silently amend it.
2. `jj new` — start a fresh empty change on top of `@`. Do this *before* editing anything.
3. Edit files with your normal tools. No add, no stage.
4. `jj describe -m "message"` — set the message on `@`.
5. `jj st` and `jj diff` — confirm what you actually captured.

`jj commit -m "msg"` is `describe -m` followed by `new`; use it to close out a change and immediately start the next one.

## git → jj

| git | jj |
|---|---|
| `git status` | `jj st` |
| `git log --graph` | `jj log` |
| `git diff` | `jj diff` |
| `git show <rev>` | `jj show <rev>` |
| `git add` + `git commit -m` | `jj commit -m` (no add step) |
| `git commit --amend` | `jj describe -m` on `@`, or just keep editing |
| `git checkout <branch>` | `jj new <bookmark>` |
| `git checkout -- <file>` | `jj restore <file>` |
| `git stash` | not needed — `jj new` |
| `git rebase -i` to squash | `jj squash` (moves `@` into `@-`) |
| `git rebase -i` to split | `jj split <paths>` |
| `git rebase --onto` | `jj rebase -r\|-s\|-b <rev> -d <dest>` |
| `git reset --hard` | `jj undo`, or `jj op restore <op-id>` |
| `git blame` | `jj file annotate <path>` |
| `git fetch` / `git push` | `jj git fetch` / `jj git push` |
| branch | bookmark |

`jj squash` also takes `--from <rev>` and `--into <rev>` to move changes between arbitrary commits.

## Bookmarks and pushing

Bookmarks do not follow you. `jj new` on top of a bookmark leaves the bookmark pointing at the old commit.

- Point one at a commit: `jj bookmark set <name> -r @-`. Moving a bookmark backwards needs `--allow-backwards`.
- `jj git push` pushes tracked bookmarks. A bookmark not yet on the remote needs `--allow-new`. Push one specifically with `jj git push -b <name>`.
- To get a change onto a throwaway PR branch: `jj git push -c @-` creates a bookmark named `push-<change-id>` and pushes it.
- Prefer pushing `@-` over `@` — `@` is usually an empty in-progress change.
- Updating an existing PR means rewriting the change, not stacking on it: `jj squash --into <change-id>` or `jj edit <change-id>`, then `jj bookmark set <name> -r <change-id>` and `jj git push`.
- Run `jj bookmark list` and confirm the target before pushing. Never push to a protected branch.

## Fetch and rebase

```
jj git fetch
jj rebase -b @ -d main@origin
```

Remote bookmarks are addressed as `<name>@<remote>`. `-b` moves the whole local stack, `-s` a commit and its descendants, `-r` a single commit. Conflicts are recorded rather than stopping the rebase.

## Conflicts

Do not run `jj resolve` — it's interactive.

1. `jj st` lists conflicted files.
2. Open the file. jj materializes conflict markers into the working copy.
3. Edit the markers out and save. The next jj command snapshots the resolution automatically — there is no "continue" step.
4. `jj st` to confirm the conflict is gone.

jj may use a 3-way diff-style marker block (`%%%%%%%` with a diff inside) rather than git's `<<<<<<<`/`=======`. Read the entire marked region before editing it.

## Recovery

Nothing is lost.

- `jj op log` — every operation, with IDs.
- `jj undo` — reverse the last operation (itself undoable).
- `jj op restore <op-id>` — rewind the whole repo to that point.
- `jj evolog -r <change-id>` — previous versions of one change; use it to recover an edit you squashed or abandoned.

When something looks wrong, read `jj op log` before doing anything else. Do not try to repair state by hand.

## Things that will bite you

- `jj edit <rev>` makes that commit the working copy, and every subsequent file edit amends it. Use deliberately; prefer `jj new` for new work.
- jj refuses to rewrite commits reachable from `trunk()` or tags. That error is a guardrail — do not pass `--ignore-immutable` to get around it.
- Empty changes are normal and harmless. `jj abandon <rev>` removes one.
- In a non-colocated repo, `gh` and other git tools can't find the git dir. Set `GIT_DIR="$(jj workspace root)/.jj/repo/store/git"` if you need them.
- Flags and bookmark behavior have shifted across jj releases. If a command errors on an unrecognized flag, run `jj help <subcommand>` rather than guessing.
