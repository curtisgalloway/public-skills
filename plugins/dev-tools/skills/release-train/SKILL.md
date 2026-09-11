---
name: release-train
description: >-
  Cut a release only after every distribution channel has been built, installed the way a user
  would in a throwaway prefix, and smoke-tested end to end by a parallel subagent per channel,
  with a regression archaeologist pinning every previously fixed bug that has no executing test.
  Blocks on any failure and files one issue per failure with a minimal reproduction; on all-green,
  and only behind an explicit gate, tags, pushes, publishes, then re-verifies the published
  artifacts from the URLs a user would use. Driven by a per-repo RELEASE-TRAIN.md profile the
  skill can construct (init), check for drift against the repo (check), and execute (run).
  Use for "cut a release", "release train", "is this ready to ship", "dry-run the release", or
  when a project has a .deb/Homebrew/zip/registry channel that unit tests never exercise.
  Ships scripts/profile_check.py (stdlib-only drift checker) and a profile template.
---

<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# release-train: the tests are not the release

`cargo test` green means the code passes its own assertions. It says nothing about whether the
`.deb` installs, whether the Homebrew keg finds its helpers, whether the Windows zip carries
the data files the CLI reads, or whether a bug fixed in March is still fixed. This skill answers
those questions before a tag exists and refuses to tag until it has.

The skill is generic. Everything it needs to know about one project lives in that project's
**profile**, `RELEASE-TRAIN.md` at the repo root, plus a gitignored `RELEASE-TRAIN.local.md`
for the facts that must never be committed (hostnames, addresses, key paths). Three modes:

| mode | invocation | what it does |
|---|---|---|
| `run` (default) | `/release-train [--dry-run] [--version X.Y.Z] [--waive <arm>] [--max-archaeology N]` | check the profile, then drive the train |
| `init` | `/release-train init` | construct the profile for a repo that has none |
| `check` | `/release-train check [--update]` | report profile drift against the repo; `--update` re-pins it after re-reading |

`run` begins with `check`, and a stale or malformed profile stops the train before any arm
starts. That is the point of the profile being checkable: a train that runs from a description
of last quarter's packaging ships last quarter's mistakes.

## Non-negotiables (every mode)

- **Never touch the developer's checkout or installs.** Work in a git worktree for the release
  branch. Install into throwaway prefixes: a fresh `HOME`, a keg-only formula, a container, a
  VM, a temp dir on the bench host. If an install step of the project itself writes to a fixed
  per-user path, redirect it (`CARGO_INSTALL_ROOT`, `UV_TOOL_DIR`, `npm_config_prefix`, and so
  on) and record in the profile which variable was needed.
- **Never publish from a red board.** Any arm FAIL, any unwaived PARTIAL or SKIP, or any
  archaeology assertion failing on HEAD → `BLOCKED`. `--waive` never waives a FAIL.
- **Never push, merge, or tag without the gate.** On all-green, stop and ask. Whatever push
  policy the user's instructions carry (schedules, confirm-first rules) applies; quote `date`.
- **`--dry-run` mutates nothing remote.** No branch push, no PR, no issues, no tag. Issue bodies
  go in the report. The release branch exists only in the local worktree.
- **Logs are the deliverable.** Every arm writes `<log dir>/<run>/<arm>.log` (full transcript)
  and `<arm>.json` (verdict). A verdict without a log is not a verdict. The log dir is named in
  the profile and should be gitignored but persistent (not a session scratch dir).
- **No private facts in the profile.** Hosts are roles (`linux-builder`, `windows-bench`); the
  machines behind them live in `RELEASE-TRAIN.local.md`. A public repo's profile must read as
  public.

## Mode `init`: construct the profile

Inputs the agent gathers, in this order, each cited in the profile's `## Sources` table so
`check` can watch it:

1. **How the project releases today.** The release workflow (`.github/workflows/release*.yml`,
   `.gitlab-ci.yml`, `Makefile release`, a `justfile`): every job that produces an artifact is a
   candidate channel; every job that publishes (a Release, a tap dispatch, a registry push, an
   apt pool rebuild) goes under `## Publish`. Read the smoke steps the workflow already has;
   they seed the smoke contract.
2. **How a user installs.** The README's install section, a packaging manifest (`nfpm.yaml`,
   a formula, `pyproject.toml`, `package.json`), `make install`. Each distinct path is a channel,
   including the from-source path when the README documents one. Only channels that actually
   exist; a registry the project does not publish to is not an arm.
3. **What the CLI exposes.** `<cli> --help` for the top-level verbs. The smoke contract needs one
   verb that reads packaged data files (skills, templates, completions), one that runs a bundled
   helper or plugin, one config or state round trip, and one hardware-free diagnostic. Verbs
   that need real hardware or network are not smoke steps.
4. **Versioning and tag conventions.** Latest tag, tag message style, whether a manifest carries
   the version or the tag is the source, any repo rule for minor versus patch, the author email
   convention (`git log --format=%ae | sort -u` reveals a noreply pattern; the profile records
   the *rule*, never an address).
5. **Where tests live and how they run**, per language, for the archaeologist.
6. **Hosts.** Which roles the channels need (a Linux builder for `.deb`, a Windows machine for a
   zip, a container runtime), what each must have installed. The agent probes what is present
   on the current machine and records roles it cannot fill as `UNVERIFIED`.
7. **Branch protection and CI checks** (`gh api repos/<o>/<r>/branches/main/protection`,
   rulesets), for `## Publish`.

Then write `RELEASE-TRAIN.md` from `templates/RELEASE-TRAIN.md`, keeping every heading, one
`### <arm>` per channel with all six required bullets, and mark every inferred fact
`UNVERIFIED`. Run `scripts/profile_check.py RELEASE-TRAIN.md --update` to pin the Sources
table, then `--cli <built cli>` once to validate the smoke rows. Finish by listing the
`UNVERIFIED` lines for the maintainer; a `--dry-run` of the train is how they get cleared
(an arm that PASSes verifies its own section).

If a channel needs a machine the current host cannot reach, write the arm anyway with its
`host:` role and say in the report that the arm will SKIP until `RELEASE-TRAIN.local.md`
names a reachable host.

## Mode `check`: is the profile still true?

```bash
python3 <skill dir>/scripts/profile_check.py RELEASE-TRAIN.md [--cli <path>] [--json]
```

It reports, per check: `sources` (a listed file's git blob id changed or the file is gone),
`paths` (a backtick-quoted repo path in the profile no longer exists), `headings` (a required
section is missing), `channels` (an arm lacks a required bullet, or names a workflow job that
is not in the release workflow), and `smoke` (with `--cli`, a smoke row's subcommand is not in
`--help`). Exit 1 on any finding.

On `CHANGED` rows: re-read the changed file, revise the sections the row says it feeds, and
only then run `--update`, which rewrites the blob ids and the "Derived from commit" line and
nothing else. Never run `--update` to make the check pass; that is how a profile becomes a
description of last quarter's packaging with a fresh date on it.

`run` executes `check` first. `check` is also cheap enough for the project's CI or a pre-commit
hook: a workflow edit that forgets the profile fails there, not in the next release.

## Mode `run`: the train

### Step 0: preflight (main model)

Fetch; on the main branch, clean, in sync with the remote. CI green on HEAD (every workflow
that ran on that commit concluded success). Repo visibility quoted from the forge, not
inferred from the URL. Toolchain inventory for every role the profile's arms name, resolved
through `RELEASE-TRAIN.local.md`; a role with no reachable host makes its arms SKIP. Then
`check`; stop on findings.

### Step 1: version and release branch

Latest tag; commits since it; classify each subject. Conventional prefixes first (`feat` or a
breaking marker → minor, or major once the project is past 1.0; `fix`/`perf` → patch;
`build`/`chore`/`ci`/`docs`/`refactor`/`style`/`test` → none); then the profile's bump rules
for anything else, marked `heuristic` in the report so the reader can overrule. `none`, or HEAD
already carrying the latest tag, means no release is due: a real run reports that and stops; a
dry run continues with the hypothetical next patch and says so in the report's first line.
Create the worktree and branch (`release/vX.Y.Z`); all builds and archaeology commits happen
there.

### Step 2: channel arms (parallel subagents)

One subagent per `### <arm>` in the profile, all launched in one message. Each gets the
worktree, the run dir, the version, its arm section verbatim, the smoke contract, the host
recipe from the local file, and the verdict schema:

```json
{"arm": "deb", "verdict": "PASS|FAIL|PARTIAL|SKIP", "artifact": "<path>",
 "installed_as": "<how a user would>", "steps": [{"id": "S1", "ok": true, "note": ""}],
 "caveats": [], "duration_s": 0, "repro": "<one command block showing the failure, or empty>"}
```

`PASS`: built, installed like a user, every smoke step green. `PARTIAL`: built and inspected,
not installed and run (no host). `SKIP`: could not build. `FAIL`: anything red. An arm may add
smoke steps; it may not drop one. Each arm records the exact command and the first 20 lines of
output for every failing step, and always runs its `cleanup` bullet, even on failure.

Use a cheaper model for the arms if the harness offers one; they execute a written recipe.
Keep the verdict on the main model.

### Step 3: regression archaeologist (one subagent, parallel with Step 2)

From the profile's `## Archaeology`: gather closed issues and fix commits, join on issue
number where possible (a fix commit with no issue still counts; loose `#N` matching mis-maps
prose mentions, so prefer `Fixes #N`/`Closes #N` trailers). For each, find a test that would
fail if the fix were reverted, cited `file:line`; a comment naming the issue is not a test.
For the newest N without one (`--max-archaeology`, default 8), write the smallest assertion
that executes the fixed path in the crate's own test convention, then **prove it bites**: check
out the fix's parent for the fixed source files only, run the test, it must fail; restore, it
must pass. A test that passes on the pre-fix code is not accepted. Commit accepted tests on
the release branch, one per bug. A new assertion that fails on HEAD is a regression and blocks
like an arm FAIL. Write `archaeology.json` (`pinned`, `already_tested`, `could_not_pin`,
`backlog`, `regressions`) and `archaeology.log`.

### Step 4: verdict and issues (main model)

Green only when every arm is PASS (or waived PARTIAL/SKIP) and `regressions` is empty. For every
FAIL, unwaived PARTIAL/SKIP, and regression, open one issue titled `<arm or component>:
<one-line symptom>` with: the run id and commit, the minimal reproduction, expected, actual
(first 20 lines), the log path. In `--dry-run`, write those bodies into the report instead.
Print the report and stop with `BLOCKED`, or go on.

### Step 5: publish, then re-verify (real run, all-green only)

Gate: `date`, the applicable push policy, an explicit question to the user. Then, following
`## Publish` in the profile: push the release branch, PR with only the archaeology commits,
wait for CI, merge, tag the merged head in the profile's tag format, push the tag, watch the
runs it fires. Then re-verify with one subagent per channel, each starting from the public URL
a user would use: download, verify checksums against their sidecars, install into a throwaway
prefix, run at least the first three smoke steps. A re-verify failure does not roll back a
public tag: open an issue and report `PUBLISHED, unverified on <channel>`.

## Report template

```
# release-train report: <run>
Mode: dry-run | real    HEAD: <sha> <subject>    Repo: public | private
Latest tag: vA.B.C   Candidate: vX.Y.Z (<bump>; <n> commits; <m> heuristic)
Release due: yes | NO (<why>) [dry run continued anyway]
Profile: current | <findings>

## Arms
| arm | verdict | artifact | installed as | duration | caveats |

## Smoke steps
| arm | S1 | S2 | ... |

## Regression archaeology
pinned: ...   already tested: ...   could not pin: ...   backlog: ...   regressions on HEAD: none | ...

## Verdict: WOULD PUBLISH | BLOCKED | PUBLISHED | PUBLISHED, unverified on <channel>

## Issues opened | Issues that would be opened

Logs: <log dir>/<run>/    Worktree: <path> (how to remove)
```

## What the first dry run of this skill taught (keep these)

- The arm that had never been run is the one that fails. A workflow that builds and zips
  but never expands and runs its own artifact hides a missing data directory for every
  release. The smoke contract exists so that every channel runs its artifact, including the
  one CI does not.
- An install recipe can be wrong in a way the product is not. Distinguish "the arm's recipe
  skipped a step the real install does" from "the artifact is broken", and fix the profile for
  the first.
- A project's own installer may write to fixed per-user paths. Redirect before running it;
  record the variable in the arm's `install like a user` bullet.
- Machines that sleep, addresses whose DNS records lapse, and ssh keyrings with too many keys
  all look like "host down". The local file should carry the liveness probe and the exact
  reach recipe, not just a hostname.
