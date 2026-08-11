<!--
SPDX-FileCopyrightText: 2026 Curtis Galloway
SPDX-License-Identifier: Apache-2.0

Append to the project's context file, next to the docs index:

  AGENTS.md                     the one to use — Antigravity reads it at the
                                workspace root, and it is the cross-tool
                                standard, so it keeps working if the project
                                is opened by something else
  GEMINI.md                     outranks AGENTS.md in Antigravity. Use it only
                                for wording that must differ, never as a second
                                full copy — two copies drift, and the one that
                                loses is the one you edited
  .agent/rules/cleanroom.md     workspace rules, if you'd rather manage this
                                through Antigravity's rules panel (confirm the
                                directory name in your build — both `.agent/`
                                and `.agents/` have shipped)

One copy is enough; a rule the agent reads twice is not enforced twice. This
block is re-injected every session and survives compaction; the spec's usage
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
- Enforcement hooks and policy rules block and log violations. A contaminated session's diff is
  discarded wholesale and regenerated from the spec — see the `cleanroom-implementer` skill.
