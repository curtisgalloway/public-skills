---
name: anchored-peripheral-spec
description: >-
  Produce a source-anchored implementation spec for a single peripheral (Ethernet MAC, UART, GPIO,
  SD/MMC, USB, I2C/SPI, …) from driver source you or your organization authored or may otherwise
  copy from — every fact cites the file:line it was derived from at a pinned commit, so a reviewer
  can check the spec against the code and drift is detectable when the code moves. Use when asked
  to document, spec, or port a driver whose source is yours; for encumbered (GPL, NDA, third-party)
  source use cleanroom-spec instead, whose wall this skill deliberately does not have. Ships
  scripts/anchor_check.py (resolve anchors, render a review sheet, detect and rewrite drift).
---

<!--
SPDX-FileCopyrightText: 2026 Curtis Galloway
SPDX-License-Identifier: Apache-2.0
-->

# Peripheral driver spec (source-anchored)

You produce one **implementation spec per peripheral** — the document an engineer reads to write
or rewrite a driver — from driver source you are **allowed to read, quote, and copy from**: your
own tree, your organization's, or a compatibly-licensed one. The spec has the same shape as a
clean-room spec (HALF 1 hardware, HALF 2 target-OS integration), but its discipline is the
opposite: instead of hiding where facts came from, **every source-derived fact carries an anchor to
the exact lines it was derived from**, at a pinned commit. A reader can open the spec and the
tree side by side and confirm that the spec is telling the truth; a checker can tell you which
claims need re-reading when the tree moves.

This skill's value is **traceability**: a spec you can't trace back to code is a spec you have to
take on faith, and a spec whose anchors have gone stale is one you *shouldn't*. The clean-room
skill answers "can we prove we didn't copy?"; this one answers "can we prove the spec is right?".

## Which skill: the eligibility test

Use this skill only when the source's license permits the target to derive from it — same author,
same organization, or a license compatible with the target's. **If you are not sure, use
`cleanroom-spec`.** The two skills are not interchangeable: an anchored spec is a *derivative* of
the source, and its anchors are an attractant that leads every reader straight into the tree. That
is exactly right for owned source and exactly wrong for encumbered source.

Do **not** load `os-investigator` here — its clean-room rule (never reproduce code, never name the
file) forbids the thing this skill requires. The board-expert skills (e.g. `rpi-expert`) remain
useful as the *map* of SoC addresses, IP identity, and quirks. `cleanroom-implementer` does not
apply: implementers of an anchored spec may and should read the source.

## Datasheet first, anchor always

The advice from `cleanroom-spec` still holds: **name the silicon IP block + vendor and find its
authoritative datasheet** (or a public sibling — Zynq's chapters for Cadence GEM, the ARM TRM for a
PrimeCell, the Synopsys databook for DesignWare). The datasheet says *why the code is right*; the
anchor says *where the code does it*. The best fact carries both:

```
CTRL bit 0 (EN) enables the block; must be cleared before reprogramming the clock divider.
[doc: FOO TRM v1.2 §4.3.1] [src: drivers/foo/foo_hw.c:212-219 (foo_reset)]
```

A fact with only a `[doc:]` tag is fine (the spec author read the datasheet). A fact with only a
`[src:]` tag is fine — it is what this skill is for — but say whether it is a hardware requirement
or a driver choice when you can tell, and mark "reason not known" when you can't. A fact with
**neither** is an error.

## The anchor grammar

```
[src: <path>:<L1>[-<L2>] [(<symbol>)]]      resolves in the SOURCE repo at the Source pin
[tgt: <path>:<L1>[-<L2>] [(<symbol>)]]      resolves in the TARGET repo at the Target pin
[doc: <document> §<section>]                a document citation; not resolved mechanically
```

- **Paths are repo-relative**, lines are 1-based and inclusive. Several anchors may share one tag,
  separated by `;`: `[src: foo.h:40-44 (FOO_CTRL); foo.c:212 (foo_reset)]`.
- **Always give the symbol** — the `#define`/constant/struct/function the lines belong to. Line
  numbers drift; symbols survive. The checker accepts a symbol that appears within the range or up
  to 200 lines before it (the enclosing definition), so `foo_hw.c:215 (foo_reset)` is the normal
  way to cite one statement inside a function.
- **Anchor the definition, not a use**: a register offset points at its `#define`; a bit field at
  the mask; a descriptor layout at the `struct`; a sequence step at the statement(s) that perform
  it; a DT-derived fact at the node in the `.dts`/`.dtsi`.
- **Block anchors**: a line containing *only* tags anchors the whole table or list that follows
  it (blank lines between are fine). Use it for a register table whose rows all come from one
  header region; rows that come from elsewhere carry their own tag in addition.
- **Pins** are stated once, near the top, on their own lines — the checker reads them:
  ```
  Source pin: <repo-name-or-url>@<commit>
  Target pin: <repo-name-or-url>@<commit>
  ```
- **Quoting** is allowed but rationed: quote at most a few lines, and only when the exact
  expression is the point (a magic constant with its comment, a non-obvious mask). The anchor is
  still required next to the quote. A spec that pastes the driver is a second copy of the driver
  that goes stale silently; a spec that *points* at the driver is checkable.

## Required structure of every spec

1. **Provenance notice (top of the document)** — this spec is derived from `<repo>@<commit>`;
   every source-derived fact carries a `[src:]` anchor and every datasheet fact a `[doc:]`
   citation; **the source is authoritative** — where spec and source disagree, the spec is wrong
   and must be fixed, never worked around; anchors are pinned — before trusting the spec at a
   newer commit run `anchor_check.py --drift`; the verification record at the end says when and
   at what pin the claims were last checked against the code.
2. **IP identity & provenance** — vendor + IP family + specific instance/revision; what a vendor
   wrapper adds; the driver's own view of the identity (version register reads, quirk flags),
   anchored.
3. **Canonical references** — a TABLE of datasheets / programmer's guides / standards, what each
   authoritatively covers, and how to find it (doc number, URL, chapter). Add a row for the driver
   source itself with its pin.
4. **Register map** — grouped by the **databook's** functional organization (never driver-touch
   order); offsets + the bit fields that matter; every row anchored (block anchor to the header
   region + per-row anchors where they differ). Flag revision-dependent offsets.
5. **Ordered init sequence** — prerequisites (clocks, resets, parent buses, address windows) then
   step by step, **each step anchored to the statement(s) that perform it**. Say which orderings
   the datasheet requires, which the driver merely does, and which the code comments or commit
   history explain (anchor the comment; cite the commit if that is where the reason lives).
6. **Data / descriptor formats** — DMA ring/descriptor layouts, ownership/wrap/status bits,
   alignment, 32- vs 64-bit addressing; anchor the `struct`/macros.
7. **Interrupts** — the routing chain, the status bits that matter, ack/clear semantics; anchor the
   handler and the enable/mask writes.
8. **DMA / addressing** — bus↔CPU translation (anchor `ranges`/`dma-ranges` in the DT), bus-master
   windows, cache/coherency rules (anchor the sync calls that reveal them).
9. **Sub-protocols** — MDIO/PHY management, tuning sequences, and so on; anchored.
10. **Target-OS mapping** — read the target tree: which existing driver to model on, the exact
    driver-facing protocol(s), reuse-vs-write, bind rule + DT node shape, packaging — every claim
    anchored with `[tgt:]`. When source and target are the same tree (a rewrite in place, a
    documentation pass), say so and use `[src:]` throughout.
11. **Milestones** — minimal first observable result, then full integration; prerequisite drivers.
12. **Gotchas (consolidated)** — anchored to the code that works around each one — plus
    **per-area confidence** (which areas rest on datasheet + code, which on code alone, which are
    inferred) and the **verification record**: pins, date, verdict, checker report path, spec
    sha256 at PASS — filled by the verifier/orchestrator, not the spec author.

## How to run it

Delegation is a context-hygiene choice here, not a requirement: the orchestrator may read the
source itself. For anything bigger than a UART, still **prefer one subagent per spec** so several
peripherals progress in parallel and the reading of a 5,000-line driver does not crowd the main
context. The subagent template is `templates/spec-subagent-prompt.md`; fill in every
`<angle-bracket>` placeholder and pass the result as the prompt. The subagent writes the spec to a
scratch path and returns the path, a one-paragraph summary, and the pins. It may return spec text
too — there is no wall — but the path is what the verifier needs.

### Check, verify, land

1. **Mechanical check** (orchestrator, every spec, before any human reads it):
   ```
   python3 <this-skill>/scripts/anchor_check.py <spec> --repo <source checkout> \
       [--target-repo <target checkout>] -o docs/spec-reports/<device>-check-<date>.txt
   ```
   The revision defaults to the spec's pin lines; `PATH@REV` overrides. It fails on: dangling
   paths, out-of-range lines, a symbol absent from the file, malformed tags, `[stale:]` markers.
   It warns on fact-bearing lines (hex literals, bit numbers, IRQs, delays, timeouts) that carry
   no tag; `--strict` makes *every* table row and list item require one. Fix all errors and
   every warning you cannot justify before step 2.
2. **Independent verification** (a fresh subagent, `templates/verifier-prompt.md`): it runs the
   checker itself, then reads the review sheet —
   ```
   python3 <this-skill>/scripts/anchor_check.py <spec> --repo <source checkout> --show
   ```
   — which prints each claim followed by the cited source lines, and judges **whether the cited
   lines actually support the claim**: the offset matches the `#define`, the step is what the
   statement does, the bit is the bit. Unlike the clean-room verifier, this one *is* an accuracy
   check and may quote both sides freely. It also checks coverage (facts without tags, sections
   missing), datasheet-vs-driver labelling, and the notice. Verdict: `PASS + report path` or
   `FAIL + report path + {section, spec line, anchor, one-line reason}` list.
3. **PASS** → move the spec to `docs/<device>-spec.md`, fill the verification record (pins, date,
   report path, `sha256sum` of the file at PASS), add a one-line `AGENTS.md` index entry from the
   returned summary.
4. **FAIL** → hand the verdict to a spec subagent (the original is fine — there is nothing to
   protect it from) to fix the flagged claims at the scratch path, then re-verify. A claim the
   verifier could not confirm from the cited lines is fixed by **finding the right lines**, not by
   widening the range until it contains them.

### Keeping it true

The spec is a **derived artifact**; the source is the truth. Three consequences:

- **When they disagree, fix the spec.** An implementer who finds the code doing something the
  spec doesn't say — or the opposite — corrects the spec (with the anchor) in the same change.
  Working around a wrong spec leaves the next reader with two wrong documents.
- **Moving the pin is a checked operation.** Before re-pinning to a newer commit:
  ```
  python3 <this-skill>/scripts/anchor_check.py docs/<device>-spec.md --repo <src> --drift <new-rev>
  ```
  It reports which cited ranges are byte-identical (nothing to do), which merely **moved** (line
  shift), and which **changed** or vanished (the claim needs re-reading). Then
  `--drift <new-rev> --rewrite` updates the moved anchors and the `Source pin:` line in place and
  appends `[stale: was <old-pin>]` to every changed anchor. A stale marker fails every later
  check until a person re-verifies that claim against the new code and removes the marker. Run the
  verifier on the stale claims, then update the verification record.
- **The verification record's hash is the drift signal for the spec itself.** A spec whose sha256
  no longer matches its record has been edited since it was verified; re-run the checker, and
  re-verify if any anchors changed.

## Quality bar

- Every constant, sequence step, layout, and gotcha derived from source carries a `[src:]` anchor
  with a symbol; every datasheet fact a `[doc:]` citation; nothing carries neither.
- Anchors point at definitions and performing statements, not at the nearest comment or the
  function's first line; ranges are as tight as the claim (one `#define`, one statement, one
  `struct`), not "the whole function".
- Register tables follow the databook's organization, and the spec says which orderings are
  hardware requirements versus driver habits.
- The reference table names obtainable documents and the pinned source.
- The checker reports zero errors at the pin, the verifier PASSed by reading the review sheet, and
  the verification record's hash matches the file.
- `anchor_check.py --drift` is part of the re-pin procedure, and `[stale:]` markers are never
  removed without re-verifying the claim.
