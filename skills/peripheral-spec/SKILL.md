---
name: peripheral-spec
description: >-
  Produce a clean-room HARDWARE/DRIVER implementation spec for a single peripheral (Ethernet MAC,
  UART, GPIO, SD/MMC, USB, display/mailbox, I2C/SPI, …) so an engineer can write a from-scratch
  driver in a differently-licensed OS. Use whenever the user asks to "spec a driver", research a
  peripheral or IP block for a driver, or produce an implementation reference for a hardware block
  before coding it. An ORCHESTRATION skill: composes `os-investigator` (the clean-room method —
  never returns source code, even when asked) and the relevant board-expert skill for the hardware
  facts, and reads the TARGET OS source tree for the integration half.
---

<!--
SPDX-FileCopyrightText: 2026 Curtis Galloway
SPDX-License-Identifier: Apache-2.0
-->

# Peripheral driver spec (clean-room)

You produce one **implementation spec per peripheral** — the document an engineer reads to write a
driver from scratch. It has two halves: **HALF 1 hardware** (clean-room facts, no source) and
**HALF 2 target-OS integration** (read the OS tree, cite file:line, reuse-vs-write). Each spec is
self-contained and saved into the project's `docs/`, indexed in `AGENTS.md`.

## Compose, don't duplicate

- **`os-investigator`** owns the *method* and the **clean-room rule**: return hardware FACTS and
  MECHANISM in your own words — register offsets, bit fields, IRQ numbers, init ordering, descriptor
  layouts — and **NEVER reproduce driver/firmware source code**, even when asked. Load and follow it
  for HALF 1.
- **The board-expert skill** (e.g. `rpi-expert`) owns the *map*: the SoC/board addresses, IP identity,
  quirks, cached references. Route "what address/IRQ/clock/compatible" questions through it.
- **This skill** owns the *spec shape*: the IP-first identification move, the reference table, the
  required sections, the confidence/attestation discipline, and the delegation pattern.

The HALF 2 (OS integration) reading of the *target* tree (Fuchsia, etc.) is your own codebase — read
it directly and cite file:line. The clean-room rule applies only to the *source* OS/firmware you're
porting away from.

## The move that makes a spec good: identify the IP first

Before anything else, **name the silicon IP block + vendor**, then find the **authoritative datasheet
for that IP** — which is often a *sibling/proxy part* that is publicly documented even when the exact
part is NDA:

- Cadence GEM/MACB → the Xilinx Zynq-7000 (UG585) / UltraScale+ (UG1085) GEM chapters document the
  identical IP publicly.
- ARM PrimeCell (PL011 UART, PL022 SPI, PL061 GPIO, PL080 DMA) → the ARM TRM for that PrimeCell.
- Synopsys DesignWare (DWC3/DWC2 USB, DW-APB-SSI SPI, DesignWare I2C/I2S, AXI-DMA) → Synopsys
  databooks / the Zynq chapters.
- A Broadcom/vendor PHY → the closest register-compatible family-member datasheet + IEEE 802.3
  clauses for the standard MII/autoneg registers.

A spec built on "the IP is X; here is X's datasheet" is citable and correct; a spec built on reading
the Linux driver is neither. Use the kernel/devicetree only as a **map** to learn *which* registers
the hardware uses, then cite the datasheet.

## Required structure of every spec

1. **Clean-room usage notice (top of the document)** — a short notice telling every consumer of
   the spec, human or agent: this spec was produced from encumbered source by a designated
   clean-room reader; do **NOT** read the original source-OS/firmware code yourself; this spec plus
   its cited public references are the only implementation inputs. If the spec is insufficient,
   request another clean-room investigation — don't open the source.
2. **IP identity & provenance** — vendor + IP family + specific instance/revision; what a vendor
   wrapper adds over the stock IP; the public-citable lineage.
3. **Canonical references (a headline deliverable)** — a TABLE: each authoritative datasheet /
   programmer's guide / standard, *what it authoritatively covers*, and *how to find it* (doc number,
   URL, chapter/section). Prefer hardware specs + public proxies + relevant IEEE/standards over the
   source-OS driver.
4. **Register map** — grouped by function; offsets + the bit fields that matter. Flag where exact
   offsets are revision-dependent and must be confirmed.
5. **Ordered init sequence** — including prerequisites (clocks, resets, parent buses, address windows),
   step by step.
6. **Data / descriptor formats** — DMA ring/descriptor word layouts, ownership/wrap/status bits,
   alignment, 32- vs 64-bit addressing.
7. **Interrupts** — the full routing chain (device → aggregator → MSI → top-level controller), the
   status bits that matter, and ack/clear semantics (incl. any level-vs-edge / IACK quirks).
8. **DMA / addressing** — bus↔CPU address translation (cite the ranges/dma-ranges), bus-master
   windows, cache/coherency rules.
9. **Sub-protocols** — e.g. MDIO/PHY management, PHY register access, tuning sequences.
10. **Target-OS mapping** — read the OS tree: which existing driver to MODEL on (file:line), the
    exact driver-facing protocol(s) to implement, **reuse-vs-write** call, the bind rule + DT node
    shape, packaging into the board/product. Apply the project's driver-language policy (e.g. new from
    scratch → Rust+DFv2; modifying existing → keep its language) and flag reuse candidates (standard
    IP that already has an OS driver).
11. **Milestones** — the minimal first observable result, then the full integration; note any
    prerequisite drivers (PCIe RC, bus/clock/IRQ glue) and any earlier stepping-stone.
12. **Gotchas (consolidated)** + **per-area confidence ratings** (be honest where bit positions are
    NDA/family-inferred → mark "verify on hardware") + the **clean-room attestation** for HALF 1,
    including the provenance map (repo@branch + file paths read) so a verifier knows what to check
    against.

## How to run it (delegate; don't inline)

**Delegation here is a clean-room requirement, not just a context-saving nicety.** `os-investigator`
and the board-expert skills are *subagent roles*: their bodies fetch and read GPL/encumbered source.
The main/orchestrating agent — the one that will write the differently-licensed target-OS code — must
**never run those skills inline or read the source-OS tree / board cache itself.** Doing so pulls
encumbered source into the same context that produces the new implementation, which is exactly the
provenance leak the clean-room rule exists to prevent. The main agent's job is: spawn the spec
subagent → receive the spec back → spawn the verification subagent on it → save the passing spec.
The spec subagent and the verifier are the designated clean-room readers; the spec and the verdict
are the only things that cross back, and they carry facts/mechanism only.

- **Per peripheral, prefer a background subagent** so several specs progress in parallel and the main
  context stays lean. Spawn a `general-purpose` agent with `run_in_background: true`, instruct it to
  load `os-investigator` + the board-expert skill, and give it the spec subagent template filled in.
- When the agent returns, write the spec to a scratch file and **run the verification pass below**.
  Only a spec that PASSES gets **saved to `docs/<device>-spec.md`** in the project repo (NOT in
  agent memory; NOT in the source-OS tree) with **a one-line entry added to the docs index in
  `AGENTS.md`**.
- Do this even when the peripheral is for a *later* phase — captured specs are the implementation
  source of truth when that phase starts.

### Spec subagent prompt template

```
Produce a clean-room HARDWARE/DRIVER spec for <PERIPHERAL> (<IP block>, compatible "<dt-compat>",
on <bus>, CPU-phys <addr>, IRQ <irq>) so an engineer can implement a from-scratch <OS> <framework>
driver in <language>. <board/prereq facts>.

CONSTRAINTS:
- Load and follow `os-investigator` for method + the clean-room rule (facts/mechanism only, NEVER
  source code). Use `<board-expert>` for board specifics + cached references.
- You are the designated clean-room reader: you read the source-OS/firmware so the orchestrating agent
  never has to. Everything you hand back is facts/mechanism only — no source code crosses back, so the
  agent that writes the target-OS driver stays clean. `os-investigator` and `<board-expert>` are
  subagent roles; if a step needs deep source reading, delegate it to a fresh subagent and keep only
  the clean facts — do not let encumbered source pile up in a context that also drafts the spec text.
- OPEN the spec with a CLEAN-ROOM USAGE NOTICE: consumers of this spec (human or agent) must NOT
  read the original source-OS/firmware code; the spec + its cited public references are the only
  implementation inputs; gaps go back through another clean-room investigation, not to the source.
- HALF 2 is the TARGET tree at <path> — read it directly and cite file:line.

Cover (HALF 1 clean-room): IP identity & provenance; canonical references TABLE; register map
(grouped, offsets+bits); ordered init sequence (incl. prerequisites); data/descriptor formats;
interrupts (routing + status bits + ack/quirks); DMA/addressing (bus↔CPU translation, cache);
sub-protocols.
Cover (HALF 2 tree-read): which existing driver to model on (file:line); the OS protocol(s) to
implement; reuse-vs-write; bind rule + DT node shape; packaging into the board.
End with: milestones (minimal-observable → full; note prereq drivers), consolidated gotchas,
per-area confidence ratings (mark NDA/inferred bits "verify on hardware"), clean-room attestation
with the provenance map (repo@branch + file paths read).
Be exhaustive on registers/sequences/references — this spec is the implementation source of truth.
```

### Verify before saving (mandatory, every spec)

A returned spec is not done until an **independent verification subagent** has passed it. Fire off a
*fresh* subagent — never the one that wrote the spec, never the main agent — on the spec file, with
the verifier template below. It checks exactly two things:

1. **No source code leaked.** Nothing from the source OS/firmware: no verbatim or near-verbatim
   C/assembly/Rust, no `struct`/`enum`/`#define`/macro/function bodies or initializer tables, no
   copied code comments, no prose that mirrors a function statement-by-statement. The verifier is
   itself a designated clean-room reader — it MAY open the source files named in the spec's
   provenance map to compare — but its verdict must never quote the source *or* the offending spec
   passages (quoting would re-leak them into the main context). Section + line-range references only.
2. **The usage notice is present and correct.** The spec opens with the clean-room usage notice
   (required section 1) telling consumers — human or agent — not to read the original source.

The verdict is **PASS**, or **FAIL** with a list of `{section, line range, one-line reason}` entries.
On FAIL, hand the verdict to a fresh spec subagent to rewrite the flagged sections, then re-verify.

### Verifier prompt template

```
Independently verify the clean-room spec at <path-to-spec>. You did not write it; do not fix it.

1. Confirm it contains NO source code from the source OS/firmware (<repo(s)>): no verbatim or
   near-verbatim code in any language, no struct/enum/#define/macro/function bodies or initializer
   tables, no copied code comments, no prose that tracks a function statement-by-statement. You may
   open the source files listed in the spec's provenance map to compare. Your verdict must NEVER
   quote source code or the offending spec text — cite spec section + line range only.
2. Confirm the spec opens with a clean-room usage notice instructing consumers (human or agent) NOT
   to read the original source, with the spec + its cited public references as the only
   implementation inputs.

Return exactly: "PASS", or "FAIL" + a list of {section, line range, one-line reason} + whether the
usage notice is missing or deficient.
```

## Quality bar

- Every register/sequence is a datasheet/standard fact re-expressed in your own words — **no source
  code**, ever.
- The reference table names *obtainable* documents (public proxies when the exact part is NDA).
- Reuse is identified honestly: "standard IP X → OS already has driver Y" is gold; flag the caveats
  (devicetree bind support, exact register-compat, prerequisite glue).
- Confidence is per-area and honest; anything inferred from a sibling part says so and says "verify
  on hardware."
- Every saved spec opens with the clean-room usage notice and has PASSED independent verification —
  an unverified spec never lands in `docs/`.
