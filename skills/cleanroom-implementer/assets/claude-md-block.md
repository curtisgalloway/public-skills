<!--
SPDX-FileCopyrightText: 2026 Curtis Galloway
SPDX-License-Identifier: Apache-2.0
Append to the project's CLAUDE.md (and mirror in AGENTS.md next to the docs index).
This block is re-injected every session and survives compaction; the spec's usage
notice does not — that's why the rules live here too.
-->

## Clean-room rules (standing — apply to every session in this project)

- Ported-driver specs (`docs/<device>-spec.md`) plus their cited public references
  (`docs/references/`) are the ONLY implementation inputs for those drivers.
- Never read, fetch, search for, or clone Linux / U-Boot / TF-A / vendor-firmware source, never
  ask a subagent to, and never load the dirty-side skills (`os-investigator`, board-experts) as an
  implementer. Only designated dirty-side processes (os-investigator / verifier, running with
  `CLEANROOM_ROLE` set) touch encumbered source.
- Spec insufficient? Append `- [open] <date> <section> <question>` to
  `docs/spec-gaps/<device>.md`, mark the code site `TODO(spec-gap)`, and continue with other
  work. The urge to "check the Linux driver" is a spec-gap, not a task.
- `[source-observed]` facts: verify on hardware or file a spec-gap — never against the source.
- Do not open `docs/provenance/` (verifier/counsel material).
- Enforcement hooks block and log violations. A contaminated session's diff is discarded
  wholesale and regenerated from the spec — see the `cleanroom-implementer` skill.
