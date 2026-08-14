---
name: fuchsia-multi-checkout
description: >-
  Run several Fuchsia checkouts (or several agents) on one machine without their builds, ffx
  daemons, or target devices colliding. Use when setting up a second tree, when fx/ffx picks up
  the wrong tree or targets the wrong device, or on cross-tree symptoms (two emulators fighting, a
  daemon on the wrong socket). Provides the fx-tree helper and the two conventions that prevent
  the real collisions.
---

<!--
SPDX-FileCopyrightText: 2026 Curtis Galloway
SPDX-License-Identifier: Apache-2.0
-->

# fuchsia-multi-checkout — multiple Fuchsia trees on one machine

Goal: several agents working different topics concurrently, each in its own checkout, without stepping
on each other's builds, ffx daemons, or target devices.

**Headline:** the Fuchsia tools are already *mostly* multi-checkout-safe. `fx`/`ffx` resolve the tree
from the **current directory** and the daemon/build-config/device/lock are all already **per-build-dir**.
The only real single-checkout assumptions left are (1) the user's *shell env* and (2) a couple of
*shared ffx files*. This skill's `fx-tree` helper plus two conventions cover both. Use **separate full
checkouts**, one per topic — not git worktrees (see the last section).

## The helper: `fx-tree`

The canonical script is `fx-tree` in this skill's directory (the directory containing this SKILL.md,
referred to as `<skill-dir>` below). For convenience, symlink it somewhere on `$PATH`, e.g.
`ln -s <skill-dir>/fx-tree ~/.local/bin/fx-tree`. Either form works:

```bash
fx-tree <cmd>               # if a $PATH symlink is set up
<skill-dir>/fx-tree <cmd>   # always works
```

| Command | What it does |
|---|---|
| `eval "$(fx-tree env)"` | Point the **current shell** at the tree your cwd is in: strips any *other* tree's `.jiri_root/bin` from `PATH`, prepends this tree's, sets `FUCHSIA_DIR`, adds an `[fx:<tree>]` prompt tag. Run this first in every agent shell. |
| `fx-tree doctor` | Diagnose multi-tree hazards for the current tree (PATH/`FUCHSIA_DIR`, per-build-dir device + daemon, shared user-level default target, emulator-name collisions). |
| `fx-tree list` | All checkouts found under `$FX_TREE_ROOTS` (default `~/src`): build dir / device / daemon state, with `*` marking your current tree. |
| `fx-tree new NAME [opts]` | Scaffold a new sibling checkout via `jiri` with a shared git cache. **Dry-run by default** (prints commands); add `--run` to execute. Opts: `--branch B --root DIR --reference TREE --cache DIR --partial --run`. |
| `fx-tree shim [DIR]` | Drop a `.envrc` (`eval "$(fx-tree env)"`) into a tree and git-exclude it (for direnv). |

## The two conventions (this is the whole trick)

These are the only manual rules needed; `fx-tree doctor` checks both.

1. **Targets:** use `fx set-device <name>` — it stores the default **per build dir** (`out/<dir>.device`,
   surfaced to ffx as `$FUCHSIA_NODENAME`). Do **not** use `ffx target default set`: current trees removed
   the command outright and bypass stateful `target.default` config entirely (fxbug.dev/394619603); on
   checkouts predating that fix it writes a **shared** user-level default that overrides every tree.
   Clear a stale value with `ffx config remove target.default` (`target default unset` is also gone).
2. **Emulators:** always pass a unique name per tree: `fx ffx emu start --name <tree>-emu …`. Emulator
   instances are keyed by name only and shared across trees, so two trees both using `fuchsia-emulator`
   corrupt each other.

## Setting up a new topic/agent

```bash
fx-tree new fuchsia-<topic> --branch <topic> --run     # one-time; downloads gigabytes
cd <tree-root>/fuchsia-<topic>                          # <tree-root> = $FX_TREE_ROOTS (default ~/src), or --root
eval "$(fx-tree env)"                                   # activate this shell
fx set <product>.<board> --debug --ccache              # default: debug build + ccache (e.g. bringup.rpi5-debug)
fx set-device <device-or-emu>                           # NOT `ffx target default set`
fx ffx emu start --name <topic>-emu …                  # only if using an emulator
fx build
```

**Default build flags — `--debug --ccache`.** Configure new trees with a `debug` compilation mode
(assertions on, full symbols — best for driver development) and ccache enabled (speeds rebuilds). Pass
`--ccache` *explicitly*: Fuchsia only auto-enables ccache when `CCACHE_DIR` is set, and the default
compilation mode is `balanced` — so neither is on unless you ask. Requires `ccache` installed
(`which ccache`). The build dir encodes the mode (`out/<product>.<board>-debug`), and the default
device is per-build-dir, so re-run `fx set-device` if you later switch modes. Use `--release` /
`--balanced` (or `--no-ccache`) only when you specifically need them.

Each agent shell that joins an existing tree only needs: `cd <tree-root>/<tree> && eval "$(fx-tree env)"`.

## Why it works (facts, verified in-tree 2026-06)

Already isolated **per build dir** — no action needed:

| Concern | Where | Source |
|---|---|---|
| Which tree `fx`/`ffx` act on | resolved from **cwd** (`.fx-root` walk); `$FUCHSIA_DIR` ignored; `$PATH`-invoked binary auto-redirects into the cwd's tree | `scripts/fx:188-228`, `src/developer/ffx/scripts/ffx` |
| ffx daemon socket | `out/<dir>/.ffx-daemon/daemon.sock` (in-tree mode) | `config/src/paths.rs:87-99` |
| ffx build config (product bundle, repo, qemu/sdk overrides) | `out/<dir>/ffx-config.json` | `config/.../context.rs:354-383` |
| default target device | `out/<dir>.device` → `$FUCHSIA_NODENAME` | `tools/devshell/set-device`, `lib/vars.sh:444` |
| default target resolution | `-t` flag, else `$FUCHSIA_DEVICE_ADDR`/`$FUCHSIA_NODENAME`; stateful user/build/global `target.default` config **bypassed** | `ffx/lib/target/src/lib.rs:690-714` (fxbug.dev/394619603) |
| build lock | `out/<dir>.build_lock` | `lib/vars.sh:500` |

So two **separate checkouts** run concurrent builds and devices without colliding out of the box.

What still needs handling:

1. **Shell env.** A typical `~/.bashrc` pins *one* tree's `.jiri_root/bin` onto `PATH` and sources its
   `fx-env.sh`; a second tree's shell inherits the wrong tools and only survives via the cwd-redirect.
   `fx-tree env` fixes the shell.
2. **Shared ffx user state** under `~/.local/share/Fuchsia/ffx/`: `emu/instances/<name>` — the one
   real remaining hazard (→ convention #2). The user-level `target.default` only bites on checkouts
   predating fxbug.dev/394619603 (current trees removed `ffx target default set` and bypass the
   stateful value); convention #1 stays as defense-in-depth for mixed-age trees.

## Do NOT use `FFX_ISOLATE_DIR` / `--isolate-dir` as a per-tree switch

It is tempting but **wrong**. Isolate mode flips ffx to `EnvironmentKind::Isolated`, which has no
`build_dir`, so ffx stops loading `out/<dir>/ffx-config.json` (product bundle, repository, qemu/sdk
overrides) — breaking `fx ffx emu`, `fx serve`, and product-bundle resolution. It is for hermetic
tests, not day-to-day multi-tree dev. (Overriding `XDG_*` is also wrong: those leak into every other
XDG-aware tool.) The per-build-dir in-tree isolation above is what you want.

## Why not git worktrees

`git worktree add` only materializes git-tracked files, but Fuchsia's heavy parts live **outside git**:
`prebuilt/` (~24 GB, CIPD), `.jiri_root/`, `integration/`, and the jiri/submodule working contents are
all gitignored. A worktree boots up missing all of that, so you'd have to symlink it from the primary
tree — which only stays consistent while every worktree sits on the **same integration revision**, and
build dirs bake absolute paths (e.g. `ffx-config.json` contains the checkout path), so they aren't
relocatable. Net: fragile and unsupported for marginal disk savings. Separate checkouts are simpler.

## Note for the agent

- Before recommending file/flag specifics, remember the line/file citations above reflect the tree as
  of 2026-06; verify with `fx-tree doctor` and a quick look if behavior differs.
- `fx-tree new --run` downloads gigabytes and creates a checkout — treat it as a heavy, confirm-first
  action. Default to showing the dry-run output and let the user trigger `--run`.
- The `fx-tree env` output is shell code meant to be `eval`'d by the **user's interactive shell** or an
  agent's shell — emitting it (without eval) just prints the snippet for inspection.
