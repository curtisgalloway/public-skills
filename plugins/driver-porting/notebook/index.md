<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Notebook index

Updated: 2026-09-24T13:09-07:00

A row is stale when its chapter has an entry newer than "indexed through". The notebook
starts with L02e; earlier units' paths are in their [evidence files](../evidence/). The
process log for this project is [PROCESS-NOTES.md](../PROCESS-NOTES.md). Terms: a chapter is
one unit's append-only notes; see the [glossary](../../../GLOSSARY.md) (lab notebook, process log).

## Chapters

### [L02e — Implement, build, and review the candidate](L02e.md)
Entries: 2026-09-24T12:22-07:00 through 2026-09-24T13:09-07:00
Outcome: complete; driver builds clean, reviewed, repaired once, never run.
- GCC 15 cannot build Linux v6.12; the test host builds with gcc-14.
- Dead end: forcing a 32-bit DMA mask (the spec permits 64-bit with fallback).
- Spec error found: PSCON bit 11 (carrier sense on transmit) should be set.
- The session auditor flags a clean Claude Code session; its 8 findings were traced by hand.
- Entries before 12:22 are reconstructed from the run ledger.

## Threads
- **Spec errors found downstream:** [L02e](L02e.md) — the reference review found a spec §5.4
  error (PSCON bit 11) that L02c's two readings passed; the implementer filed it during repair.
