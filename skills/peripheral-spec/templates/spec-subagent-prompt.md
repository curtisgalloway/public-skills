<!--
SPDX-FileCopyrightText: 2026 Curtis Galloway
SPDX-License-Identifier: Apache-2.0
Fill-in prompt for the spec-writing subagent; substitute every <angle-bracket> placeholder.
-->

Produce a clean-room HARDWARE/DRIVER spec for <PERIPHERAL> (<IP block>, compatible "<dt-compat>",
on <bus>, CPU-phys <addr>, IRQ <irq>) so an engineer can implement a from-scratch <OS> <framework>
driver in <language>. <board/prereq facts>.

TRANSFER PROTOCOL: write the finished spec to <scratch path> yourself, and write the provenance
file map to docs/provenance/<device>-map.txt (file paths go in the sidecar, never in the spec
body). Return ONLY: the spec path, a one-paragraph summary (for the docs index), and the pinned
source provenance as <repo>@<commit>. Do not return spec text or source file paths in your reply —
neither may enter the orchestrator before verification.

CONSTRAINTS:
- Load and follow `os-investigator` for method + the clean-room rule: facts/mechanism only, NEVER
  source code; every constant and sequence step tagged [databook]/[standard]/[DT]/[source-observed];
  [source-observed] orderings marked "order not known to be required" and [source-observed]
  constants marked "re-derive on hardware"; register tables grouped per the databook, never
  driver-touch order; provenance pinned to an exact commit. Use `<board-expert>` for board
  specifics + cached references.
- You are the designated clean-room reader: you read the source-OS/firmware so the orchestrating
  agent never has to. `os-investigator` and `<board-expert>` are subagent roles; if a step needs
  deep source reading, delegate it to a fresh subagent and keep only the clean facts — do not let
  encumbered source pile up in a context that also drafts the spec text.
- Self-scan before returning if the source tree is local:
    python3 <os-investigator>/scripts/leak_scan.py <scratch path> --against <source paths> \
        [--whitelist <databook nomenclature>]
  Rewrite any finding. If sources were read remotely, note that the self-scan was skipped.
- ATTRACTANT RULES: the spec body contains no source-tree file paths and no "Linux does X in
  file Y" narration — state facts as hardware facts. The [source-observed] tag says a fact came
  from code; it never says where.
- OPEN the spec with the CLEAN-ROOM USAGE NOTICE (required section 1), including the spec-gap,
  [source-observed], provenance-dir, pre-merge-gate, and hash-match clauses.
- HALF 2 is the TARGET tree at <path> — read it directly and cite file:line.

Cover (HALF 1 clean-room): IP identity & provenance; canonical references TABLE; register map
(grouped per databook, offsets+bits, tagged); ordered init sequence (incl. prerequisites, steps
tagged); data/descriptor formats; interrupts (routing + status bits + ack/quirks); DMA/addressing
(bus↔CPU translation, cache); sub-protocols.
Cover (HALF 2 tree-read): which existing driver to model on (file:line); the OS protocol(s) to
implement; reuse-vs-write; bind rule + DT node shape; packaging into the board.
End with: milestones (minimal-observable → full; note prereq drivers; full integration includes
the pre-merge output scan), consolidated gotchas, per-area confidence ratings (mark NDA/inferred
bits "verify on hardware"), and the clean-room attestation with the pinned provenance
(<repo>@<commit>; file map in the sidecar) plus an empty verification record for the verifier
to fill.
Be exhaustive on registers/sequences/references — this spec is the implementation source of truth.
