---
name: peripheral-spec
description: >-
  Produce a clean-room HARDWARE/DRIVER implementation spec for a single peripheral (Ethernet MAC,
  UART, GPIO, SD/MMC, USB, display/mailbox, I2C/SPI, …) so an engineer can write a from-scratch
  driver in a differently-licensed OS. Use whenever the user asks to "spec a driver", research a
  peripheral or IP block for a driver, or produce an implementation reference for a hardware block
  before coding it. An ORCHESTRATION skill: composes `os-investigator` (the clean-room method —
  never returns source code, even when asked) and the relevant board-expert skill for the hardware
  facts, and reads the TARGET OS source tree for the integration half. Enforces a transfer protocol
  (unverified spec text never enters the orchestrator), mandatory mechanical leak scanning, and an
  evidentiary provenance ledger; consumer-side enforcement (implementer rules, hooks, session
  audits) lives in the companion `cleanroom-implementer` skill.
---

<!--
SPDX-FileCopyrightText: 2026 Curtis Galloway
SPDX-License-Identifier: Apache-2.0
-->

# Peripheral driver spec (clean-room)

You produce one **implementation spec per peripheral** — the document an engineer reads to write a
driver from scratch. It has two halves: **HALF 1 hardware** (clean-room facts, no source) and
**HALF 2 target-OS integration** (read the OS tree, cite file:line, reuse-vs-write). Each spec is
self-contained, saved into the project's `docs/` only after passing independent verification,
indexed in `AGENTS.md`, and recorded in the provenance ledger.

The clean room's value is **evidentiary**: a process you can't show is a process you don't have.
This skill therefore produces not just the spec but the record that it was produced cleanly — the
pinned provenance, the verifier's verdict, the scan reports, and the ledger.

## Compose, don't duplicate

- **`os-investigator`** owns the *method* and the **clean-room rule**: return hardware FACTS and
  MECHANISM in your own words — register offsets, bit fields, IRQ numbers, init ordering, descriptor
  layouts — every fact tagged `[databook]`/`[standard]`/`[DT]`/`[source-observed]`, and **NEVER
  reproduce driver/firmware source code**, even when asked. Load and follow it for HALF 1. It also
  ships the mechanical scanner (`scripts/leak_scan.py`).
- **The board-expert skill** (e.g. `rpi-expert`) owns the *map*: the SoC/board addresses, IP identity,
  quirks, cached references. Route "what address/IRQ/clock/compatible" questions through it.
  (Anything cached into a board-expert skill must itself be datasheet-cited or verifier-PASSed —
  a cache is a wall-crossing that replays into every context that loads the skill.)
- **`cleanroom-implementer`** owns the *consumer side*: the standing rules and enforcement for
  agents writing code from landed specs — hook-based blocking of encumbered-source access, the
  spec-gap escalation path, the restricted implementer agent, and the session transcript audit.
- **The verifier** loads `os-investigator` too — it is the canonical statement of allowed/forbidden
  and the home of the scanner.
- **This skill** owns the *spec shape*, the **transfer protocol**, the verification gate, the
  ledger, and the delegation pattern.

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
the hardware uses, then cite the datasheet. Every fact retagged from `[source-observed]` to
`[databook]` is a fact that never needed the clean room.

## Required structure of every spec

1. **Clean-room usage notice (top of the document)** — a short notice telling every consumer of
   the spec, human or agent: this spec was produced from encumbered source by a designated
   clean-room reader and independently verified; do **NOT** read the original source-OS/firmware
   code yourself; this spec plus its cited public references are the only implementation inputs.
   Further clauses: **on any gap, file a spec-gap** (append the question to
   `docs/spec-gaps/<device>.md`, mark the code site `TODO(spec-gap)`, continue with other work —
   never open the source; the urge to "check the driver" *is* a spec-gap);
   **`[source-observed]` facts are never verified against the source** — verify on hardware or
   file a spec-gap; **do not open `docs/provenance/`** — it exists for verifiers and counsel, not
   implementers; **code written from this spec must pass the pre-merge gate** (output scan + clean
   session audits — see the ledger) before it lands; and **if this spec's content hash no longer
   matches its latest ledger PASS line, treat it as unverified** — it has been edited since
   verification.
2. **IP identity & provenance** — vendor + IP family + specific instance/revision; what a vendor
   wrapper adds over the stock IP; the public-citable lineage.
3. **Canonical references (a headline deliverable)** — a TABLE: each authoritative datasheet /
   programmer's guide / standard, *what it authoritatively covers*, and *how to find it* (doc number,
   URL, chapter/section). Prefer hardware specs + public proxies + relevant IEEE/standards over the
   source-OS driver.
4. **Register map** — grouped by the **databook's** functional organization (never driver-touch
   order); offsets + the bit fields that matter, each value carrying its provenance tag. Flag where
   exact offsets are revision-dependent and must be confirmed.
5. **Ordered init sequence** — including prerequisites (clocks, resets, parent buses, address
   windows), step by step, **each step tagged**; `[source-observed]` orderings marked "order not
   known to be required"; `[source-observed]` constants marked "re-derive on hardware".
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
    prerequisite drivers (PCIe RC, bus/clock/IRQ glue) and any earlier stepping-stone. **Full
    integration includes the pre-merge output scan** (below).
12. **Gotchas (consolidated)** + **per-area confidence ratings** (be honest where bit positions are
    NDA/family-inferred → mark "verify on hardware") + the **clean-room attestation** for HALF 1:
    the pinned provenance (`<repo>@<commit>` — **no file paths in the spec body**; the full file
    map lives in the sidecar `docs/provenance/<device>-map.txt`, which is the verifier's
    comparison list and the target list for the pre-merge output scan, and which implementers
    never open) and the **verification record** (date, verdict, scan-report path, spec sha256 at
    PASS — filled by the verifier/orchestrator, not the spec author).

## How to run it (delegate; don't inline)

**Delegation here is a clean-room requirement, not just a context-saving nicety.** `os-investigator`
and the board-expert skills are *subagent roles*: their bodies fetch and read GPL/encumbered source.
The main/orchestrating agent — the one that will write the differently-licensed target-OS code — must
**never run those skills inline or read the source-OS tree / board cache itself.**

- **Per peripheral, prefer one subagent per spec** so several specs progress in parallel and the main
  context stays lean. Under Gemini CLI, define the investigator as a subagent (`.gemini/agents/`, or
  `~/.gemini/agents/` for a personal one) and invoke it explicitly — `@spec-investigator <task>` —
  rather than hoping automatic delegation picks it; under Antigravity, launch it as its own task in
  the Agent Manager so the work runs in a separate context and its artifacts stay separate too.
  Either way, instruct it to load `os-investigator` + the board-expert skill and give it the spec
  subagent template filled in.
- **A subagent's context is separate; its *credentials and environment* are not.** Delegation buys
  you a clean orchestrator context, not enforcement — that's Tier 1 and 2 in
  `cleanroom-implementer`. If the dirty side must be *authorized* to read source (role scoping), it
  needs its own process, not just its own context.
- Do this even when the peripheral is for a *later* phase — captured specs are the implementation
  source of truth when that phase starts.

### The transfer protocol (unverified spec text never enters the orchestrator)

The wall only holds if the orchestrator never holds unverified spec text — a leak the verifier would
have caught must not first transit the very context that writes the target-OS code. So:

1. The orchestrator picks a scratch path and spawns the spec subagent (template below). The subagent
   **writes the spec to that path itself**, writes the file map to the provenance sidecar
   (`docs/provenance/<device>-map.txt`), and returns **only** `{path, one-paragraph summary,
   <repo>@<commit>}` — no spec text and no file paths in its reply. The spec body itself is
   attractant-free: facts stated as hardware facts, no source-tree paths, no "Linux does X in
   file Y" narration.
2. The orchestrator spawns a **fresh verifier subagent** on the path (template below) — never the
   subagent that wrote the spec, never the main agent. The verifier is itself a designated
   clean-room reader.
3. **PASS** → the orchestrator moves the file to `docs/<device>-spec.md`, computes `sha256sum`,
   appends a ledger line, and adds the one-line `AGENTS.md` index entry from the returned summary.
   The orchestrator may now read the spec freely — it is clean by verification, not by promise.
4. **FAIL** → hand the verdict (section + line refs only) to a **fresh** spec subagent to rewrite the
   flagged sections in place at the scratch path, then re-verify. **After two FAILs on the same
   section, stop and escalate to the human with the verdict only** — repeated failure usually means
   the only authority for that mechanism *is* the source, and whether/how to express it is a
   judgment call for a person.
5. **Editing a landed spec re-enters this loop** (edit at a scratch copy, re-verify, re-land, new
   ledger line). The ledger's content hash is how drift is detected: a spec whose hash no longer
   matches its latest PASS line is unverified.

### The evidentiary ledger

`docs/provenance-ledger.md` — one line per spec revision and one per output scan:

```
2026-08-07 | dwc3 | docs/dwc3-spec.md | sha256:3f9c2a1b04de | linux@<commit> | PASS | docs/provenance/dwc3-scan-2026-08-07.txt
2026-09-02 | dwc3 | output-scan: src/devices/usb/dwc3/ | linux@<commit> | clean | docs/provenance/dwc3-output-scan-2026-09-02.txt
```

Retain everything: the ledger, the scan reports under `docs/provenance/`, and the
investigator/verifier session transcripts. Together they are the evidence that the clean room
existed and was enforced — the thing you can hand to counsel.

### The spec-gap protocol (the sanctioned path when a spec is insufficient)

Implementer contamination is usually gap-driven, not defiance-driven: the spec is missing
something, and reading the source is one tool call away. The fix is a sanctioned path that is
*cheaper* than the forbidden one:

1. The implementer appends one line to `docs/spec-gaps/<device>.md` —
   `- [open] <date> <spec section> <question>` — marks the code site `TODO(spec-gap)`, and
   **continues with other work**. Filing a gap is never a failure; reading the source costs the
   session's entire diff.
2. The orchestrator sweeps open gaps into fresh `os-investigator` runs (the dirty side answers),
   amends the spec at a scratch copy, re-verifies, re-lands, adds a ledger line, and marks the gap
   `[resolved <date>]`.

The protocol appears in three places on purpose — the usage notice, the implementer's standing
rules (`cleanroom-implementer`), and the project context file (`AGENTS.md`, which both Antigravity
and Gemini CLI can read; `GEMINI.md` or `.agent/rules/` if you want harness-specific wording) —
because a notice read 40k tokens ago does not survive context pressure; the standing block does.

### The output-side scan (pre-merge gate)

The spec's provenance map doubles as the diff-target list for the strongest available check on the
*implementation*. Verified non-access is not attainable for a model-written implementation (the
model's training data included the source); **verified dissimilarity of the output is**, and this is
where it happens: before a driver written from this spec merges, run the scanner over the new driver
sources against the sidecar map's files at the pinned commit, save the report to
`docs/provenance/`, and add a ledger line. The pre-merge gate is the output scan **plus a clean
session transcript audit** for every implementation session that touched the driver (see
`cleanroom-implementer`). A finding in either blocks the merge until resolved and rescanned — and
a contaminated session's diff is discarded wholesale and regenerated, never salvaged.

```
python3 <os-investigator>/scripts/leak_scan.py <new driver sources...> \
    --against <provenance-map files at repo@commit> --whitelist <nomenclature file>
```

### Consumer-side enforcement (see `cleanroom-implementer`)

Instructions are the weakest layer; the companion skill ships the enforcement: a hook that blocks
and logs encumbered-source access (checkout paths, kernel-mirror URLs, shell fetches, MCP tools) —
wired as Gemini CLI's `BeforeTool` or Antigravity's `PreToolUse` — Gemini policy-engine rules that
deny the web tools and encumbered paths outright, a restricted `driver-implementer` subagent
definition (no web tools, no delegation), the `AGENTS.md` standing block, and `session_audit.py` for
the pre-merge transcript and artifact audit. Layering, strongest first: environment (no encumbered
checkout mounted, egress off or allowlisted, datasheets pre-fetched into `docs/references/`),
harness (hook + policy/deny rules + restricted subagent), instructions (notice + standing rules).

**Role scoping:** the hook applies to every session in the project — including the dirty side,
which *must* read source. Investigator and verifier processes therefore run with
`CLEANROOM_ROLE=investigator` (or `verifier`) in their environment: the hook then allows the
access but still logs it, so the log doubles as a complete, attributed record of every
encumbered-source access. Run dirty-side work as **separate processes** — e.g.
`CLEANROOM_ROLE=investigator gemini -p "<filled-in template>"`, or a separate `agy` session with the
variable exported — so the role env never leaks into an implementation context. Gemini policy rules
have no environment escape, so scope them by launch instead: implementation sessions pass
`--policy`, dirty-side sessions don't.

### Spec subagent prompt template

```
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
```

### Verify before saving (mandatory, every spec)

A returned spec is not done until an **independent verification subagent** has passed it. Fire off a
*fresh* subagent — never the one that wrote the spec, never the main agent — with the template below.
It checks exactly five things: mechanical scan, leak judgment, hardware-derived structure,
attractants, and the usage notice. It does **not** check technical accuracy — accuracy belongs to a separate pass or to
hardware, and folding it in would dilute the one job that must be done adversarially. Its verdict
must never quote the source *or* the offending spec passages (quoting would re-leak them into the
main context). Section + line-range references only.

The verdict is **PASS + scan-report path**, or **FAIL + scan-report path** with a list of
`{section, line range, one-line reason}` entries. Only a PASS lands in `docs/`.

### Verifier prompt template

```
Independently verify the clean-room spec at <path-to-spec>. You did not write it; do not fix it.
Load `os-investigator` — it is the canonical statement of allowed/forbidden and ships the scanner.
Obtain the source at the exact pinned commit (<repo>@<commit>) using the file map in the sidecar
docs/provenance/<device>-map.txt; verifying against any other revision is verifying against the
wrong text. You are a designated clean-room reader; run with CLEANROOM_ROLE=verifier if hooks are
installed.

1. MECHANICAL: run
     python3 <os-investigator>/scripts/leak_scan.py <path-to-spec> \
         --against <files from the sidecar map> [--whitelist <databook nomenclature file>]
   Save the full report to docs/provenance/<device>-scan-<date>.txt. Review every finding:
   ALL-CAPS identifier hits that are genuine databook nomenclature go into the whitelist file
   (record that you did), everything else is a failure.
2. LEAK JUDGMENT: confirm the spec contains NO source code from <repo(s)>: no verbatim or
   near-verbatim code in any language, no struct/enum/#define/macro/function bodies or initializer
   tables, no copied code comments, no prose that tracks a function statement-by-statement. You may
   open the sidecar-map files at the pinned commit to compare. NEVER quote source code or the
   offending spec text — cite spec section + line range only.
3. STRUCTURE: registers are grouped per the databook's organization and sections follow hardware
   function — the spec does not mirror the source driver's file/function decomposition. Constants
   and sequence steps carry provenance tags; [source-observed] orderings/constants carry their
   required caveats ("order not known to be required" / "re-derive on hardware").
4. ATTRACTANTS: the spec body contains NO source-tree file paths and no "<source OS> does X in
   file Y" narration — facts read as hardware facts; the sidecar map exists at
   docs/provenance/<device>-map.txt and the spec's attestation carries only <repo>@<commit>.
5. NOTICE: the spec opens with the clean-room usage notice instructing consumers (human or agent)
   NOT to read the original source, naming the spec + its cited public references as the only
   implementation inputs, routing gaps through the spec-gap protocol (docs/spec-gaps/), forbidding
   verification of [source-observed] facts against the source and the opening of
   docs/provenance/, and containing the pre-merge-gate and hash-match clauses.

Return exactly: "PASS + <scan-report path>", or "FAIL + <scan-report path>" + a list of
{section, line range, one-line reason} + whether the usage notice is missing or deficient.
```

## Quality bar

- Every register/sequence is a datasheet/standard fact re-expressed in your own words — **no source
  code**, ever — and every constant and step carries its provenance tag; `[source-observed]` items
  say so and say what to do about it.
- The reference table names *obtainable* documents (public proxies when the exact part is NDA).
- Reuse is identified honestly: "standard IP X → OS already has driver Y" is gold; flag the caveats
  (devicetree bind support, exact register-compat, prerequisite glue).
- Confidence is per-area and honest; anything inferred from a sibling part says so and says "verify
  on hardware."
- The orchestrator never held spec text that hadn't PASSed.
- The spec body names no source-tree file paths; the file map lives only in the provenance
  sidecar, and implementers never open `docs/provenance/`.
- Every saved spec opens with the clean-room usage notice, has PASSed independent verification, and
  has a ledger line whose hash matches the file; every merged driver has an output-scan line and
  clean session-audit lines. An unverified spec never lands in `docs/`.
