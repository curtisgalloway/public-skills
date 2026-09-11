# Release train profile: <project>

Derived from commit unknown on <YYYY-MM-DD>. Executed by the `release-train`
skill; kept honest by `profile_check.py` (see `## Sources`). Lines marked
`UNVERIFIED` were inferred by the agent that wrote this file and have not been
confirmed by a maintainer or by a passing arm.

## Project

- cli: `<binary name>`
- version source: <tag | Cargo.toml | package.json | ...> (how the released version is derived)
- tag format: `v<X.Y.Z>`; subject `v<X.Y.Z>: <lowercase summary>`
- main branch: `main`; protected: <yes: PR + required checks | no>
- release workflow: `<path to the workflow that builds and publishes>`
- ci workflow: `<path>`; required checks: <names>
- bump rules: conventional commits (`feat` minor, `fix` patch, others none) plus <repo-specific overrides, or "none">
- releaser identity: <how the tag author is chosen; never a real email here>

## Hosts

Roles only. The machines behind them, how to reach them, and any credentials
live in `RELEASE-TRAIN.local.md` (gitignored), one section per role.

| role | needed by | what it must have |
|---|---|---|
| local | <arms> | <toolchain> |
| linux-builder | <arms> | <container runtime or VM, packaging tools> |
| windows-bench | <arms> | <toolchain, PowerShell over ssh> |

## Smoke contract

Run against the installed copy, with `HOME` (or the platform equivalent)
pointed at a fresh temp dir and the working directory outside the checkout.

| id | check | pass condition |
|---|---|---|
| S1 | `<cli> --help` | exit 0; lists <the top-level verbs> |
| S2 | `<cli> <a verb that reads packaged data>` | <what proves the package's data files were found> |
| S3 | `<cli> <a verb that runs a bundled helper or plugin>` | exit 0 (proves shared libraries loaded) |
| S4 | <a config/state round trip> | <expected> |
| S5 | <a hardware-free diagnostic> | exit 0 or a clean "nothing configured"; never a panic |

## Channels

One `### <arm>` per channel the project actually ships. Bullets `kind`,
`artifact`, `build`, `install like a user`, `smoke`, `cleanup` are required
(`profile_check.py` refuses an arm without them); `workflow job` is checked
against the release workflow when present.

### <arm name, e.g. homebrew | deb | zip | source | pypi | crates>

- kind: <homebrew | deb | rpm | zip | msi | source | registry>
- artifact: `<file name pattern>`
- workflow job: <job id or name in the release workflow, or none>
- host: <role from Hosts>
- build: <steps that produce the artifact exactly as the workflow does>
- install like a user: <the real install path, into a throwaway prefix>
- smoke: S1..S5 <plus arm-specific additions; never fewer>
- cleanup: <what to undo, always, even on failure>
- caveats: <fidelity gaps between this arm and the real pipeline>

## Archaeology

- issue source: `gh issue list --state closed --limit 200` <or other tracker>
- fix commits: <grep pattern over git log subjects and bodies>
- test locations: <dirs and conventions per language>
- how to run: <per-language test commands>
- prove-it-bites: `git checkout <fix>^ -- <fixed files>` then the test must fail; restore; it must pass

## Publish

- gate: ask before tag/push; <any schedule or policy rules>
- steps: <branch push, PR, merge, tag, push tag, watch which runs>
- re-verify: one bullet per channel, each a public URL a user would use and the command that proves it runs

## Sources

Files this profile was derived from. `profile_check.py` recomputes each blob
id; a CHANGED row means the section it feeds needs re-reading, `--update`
rewrites the ids once that is done.

| path | blob | feeds |
|---|---|---|
| `<release workflow>` | unknown | Channels, Publish |
| `<packaging manifest>` | unknown | Channels |
| `<Makefile or build script>` | unknown | Channels: source |
| `<README install section's file>` | unknown | Channels: install like a user |
