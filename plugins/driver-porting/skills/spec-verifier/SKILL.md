---
name: spec-verifier
description: >-
  Verify a spec against the sources it cites and write a verification record outside the spec.
  Works for board specs (board-expert's SPEC-FORMAT.md), clean-room driver specs (cleanroom-spec),
  and source-anchored specs and reviews (anchored-peripheral-spec, reference-driver-review): a fresh
  verifier subagent opens every cited authority at the recorded ref, commit, or date, gives a
  verdict per claim, and never edits the spec. Use when asked to verify, re-verify, double-check, or
  audit a spec, to check a spec against its sources, when a checker reports a spec unverified or
  its record stale, after a spec edit, or after the sources moved. Re-runnable; orchestrator only.
---

<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Spec verifier (re-derive a spec's claims from its sources, on demand)

A spec is written once by an author who read the sources as they went. Verification is the separate
pass that re-derives every claim from the authority it cites, in a context that never saw the
author's reasoning, and records the result **outside the spec**, so the record costs no context when
the spec is used. Every spec-creating skill here runs this phase as its last step and points back
here for the re-run: `board-spec-scaffold` for board specs, `cleanroom-spec` for clean-room driver
specs, `anchored-peripheral-spec` and `reference-driver-review` for anchored specs and reviews.

## Terms

- **Claim** — the unit that gets a verdict. For a board spec, one fact bullet. For an anchored
  spec or review, one anchor (`[src:]`, `[tgt:]`, `[impl:]`, `[ref:]`) and the claim it is attached
  to. For a clean-room driver spec, one tagged fact (`[databook]`, `[standard]`, `[DT]`,
  `[inference]`) in the register tables and sequences.
- **Source** — what a claim cites: a repository at a commit, a patch series, a document at a URL, a
  device tree file, a databook section.
- **Verdict** — `PASS`, `FAIL`, `UNVERIFIABLE`, `GAP`, or `ADJUDICATE`, per claim.
- **Adjudication** — a decision only a person can make, because two independent readers of the same
  authority reached different answers. An `ADJUDICATE` claim is excluded from the pass/fail counts
  and carried in its own `summary.adjudicate` bucket; it is neither credit nor blame until settled.
- **Verification record** — the file that holds the verdicts, in a `resources/` directory beside
  the spec's root or the spec itself. Not a spec; never loaded by a reader.
- **Verifier** — the subagent that produces the verdicts. A fresh context: the spec, its declared
  sources, and this file. Nothing else.
- **Orchestrator** — you. You spawn the verifier, write the record, run the mechanical checks, and
  report. You never read sources and never edit the spec.

## The record

Same frontmatter for every kind; the body's keys differ per kind (below).

```markdown
---
spec: rpi5                          # the spec id, or the spec's basename for kinds without ids
spec_file: rpi5.spec.md             # path relative to the record's parent's parent
spec_sha256: <64 hex digits>        # sha256 of the spec file as verified
verified: 2026-09-18                # ISO date
verifier: <which agent and harness produced this record>
sources:                            # every repo, series, and doc actually consulted
  - name: linux-rpi
    commit: <40 hex digits>
    fetch: ok
  - name: RP1 peripherals datasheet
    url: https://datasheets.raspberrypi.com/rp1/rp1-peripherals.pdf
    fetch: ok
  - name: TF-A Raspberry Pi 5 platform page
    url: https://trustedfirmware-a.readthedocs.io/en/latest/plat/rpi5.html
    fetch: blocked
summary: {pass: 9, fail: 0, unverifiable: 1, gap: 1, adjudicate: 0}
---

# Verification of `rpi5`

- Quick-facts/1 "Boot media and chain": PASS — chain and config.txt role match the Raspberry Pi
  documentation config.txt page; BL31 role matches the TF-A rpi5 platform page.
- Quick-facts/5 "Power": GAP — a TODO-only bullet; nothing to verify.
- Gotchas/2: UNVERIFIABLE — the RP1 datasheet section is cited by number; the PDF fetch was
  blocked, so the section was not read this pass.
- Gotchas/3: FAIL — the spec says the psci node's method is "smc"; bcm2712.dtsi at <commit> says
  "hvc". Proposed correction: change the parenthetical and the claim to hvc, and check the BL31
  page for which conduit it installs.
```

Rules that hold for every kind:

- **One line per claim, every claim.** Gaps get `GAP`; claims whose authority could not be reached
  get `UNVERIFIABLE` with the reason (fetch blocked, NDA, no public authority named); claims two
  independent verifiers read differently get `ADJUDICATE` with both readings.
- **A citation that cannot be located is a `FAIL`**, not `UNVERIFIABLE`: a file that does not exist
  at the recorded ref, a line range that no longer holds the symbol, a page that does not say what
  the claim says, a databook section that does not cover the register.
- **`FAIL` carries the discrepancy and the proposed correction.** The verifier never edits the
  spec. The user, or the creating skill on the user's say-so, applies the fix; then re-run.
- **No source in the record.** It is a clean-side artifact like the spec: describe what was
  compared and how it differs; never quote driver or firmware code. `os-investigator`'s rule
  applies in full, and the record must pass `os-investigator/scripts/leak_scan.py`.
- **Keys survive edits.** Claims are keyed by something stable (section and ordinal, the anchor
  text), never by line number.
- `summary` counts equal the verdict lines, `adjudicate` included (omit the key only when it is
  zero); `spec_sha256` is the spec file's hash at write time, so any later edit makes the record
  visibly stale.

## The procedure

1. **Identify the kind** from the spec: YAML frontmatter with `kind:` or `overlays:` is a board
   spec; `Source pin:` / `Impl pin:` lines and `[src:]`-family anchors mean an anchored spec or
   review; the `cleanroom-spec` required structure (provenance ledger, usage notice) means a
   clean-room driver spec. Resolve a board spec across roots the way `board-expert` § 1 does; a
   path names the others. "Re-verify everything under `<dir>`" means every spec file below it.
2. **Run the kind's mechanical checks first** (below). They are cheap, and a spec that fails them
   is not worth a verifier's time until fixed.
3. **Spawn the verifier**: a subagent with a fresh context, given the spec file, read-only access
   to whatever the spec composes or pins (a board spec's `parts`; an anchored spec's source and
   target checkouts at their pins; a driver spec's cited documents), this file, and
   `os-investigator` for the clean-room rule and the cache discipline. Not the author's report,
   not the previous record, not this conversation. Verify several specs in parallel, one verifier
   per spec.
4. **The verifier materializes the sources** it needs: repositories cloned into the cache the spec
   names (or the checkout the pin names) at the recorded ref or commit, series pulled in the form
   their note says works, documents fetched. It records every one under `sources` with its commit
   or URL and the fetch result.
5. **For every claim, in order**: open the cited authority, compare each stated value (address,
   size, interrupt number, cell count, clock name, frequency, ordering, register bit, exception
   level, line range, symbol) with what the authority says, and write the verdict line.
6. **Independent second verifier** where the kind says so (bring-up-critical facts of a board spec;
   the register-map tables of an anchored spec). Same brief, no shared context. **A disagreement is
   an `ADJUDICATE` item, not a `FAIL`**: the two readers could not settle the question between
   them, which says nothing yet about whether the spec is wrong. Record both readings, and leave
   the claim **out of the pass/fail counts** — it is reported separately and waits for a person.
   Two things follow. If adjudication finds the spec wrong, that is a `FAIL` on the merits, and the
   record is rewritten with the resolved verdict. If adjudication finds the spec stated something
   more definitely than its evidence supports — a claim true of one tree written as true of both,
   an `[inference]` written as though it were read — that is also a `FAIL`, on the definiteness
   rather than on the disagreement. What is never a `FAIL` is the disagreement itself.
7. **Write the record.** Compute `spec_sha256`, fill `verified` and `verifier`, check the summary
   against the body, write the file at the kind's location, replacing any earlier record, and run
   the kind's checker so it is accepted.
8. **Report** the summary and every `FAIL` with its proposed correction, quoted from the record.
   Do not apply corrections. After a fix, run again; the loop ends at zero `FAIL`.

## Board specs

The kind defined by `board-expert/SPEC-FORMAT.md`; this section is the one statement of its
verification procedure, and `SPEC-FORMAT.md` § Verification points here.

- **Claims** are the fact bullets of the fact sections (`Quick-facts`, `Gotchas`, and for an IP spec
  `Standards and databook`, `Programming model`, `Known variants and quirks`), each keyed as
  `<Section>/<ordinal> "<bold lead-in>"` (1-based, top-level bullets only, lead-in omitted when
  absent). A gap bullet (`TODO (verify on hardware)` first) is `GAP`.
- **Sources** are the bullet's tag clause: `[DT] (file)` names a device tree in a `repos` or
  `series` entry at its `ref`; `[databook]`, `[standard]`, `[doc]` name a `docs` entry or a document
  id; `[hardware]` names a board and a method; `[press]` and `[source-observed]` name a page or a
  tree and are compared against it like any other claim, TODO or not; `[inference]` names its
  premises and derivation in its parenthetical, and is verified on whether those premises hold and
  whether the conclusion follows from them. `instances:` rows are claims
  too: each `reg`, `irq`, and `clocks` value against the device tree it came from, keyed
  `instances/<name>`.
- **Composition.** The verifier may read the specs a board composes through `parts`, so "see
  `bcm2712`" resolves, but each spec file gets its own record. Overlays are verified under their own
  root, one record each.
- **Two verifiers** for the bring-up-critical facts: the addressing model, the boot chain and entry
  state, and the debug UART bullets of every `soc` spec in the composition, and the debug console
  bullet of the board.
- **Mechanical check**: `board-expert/scripts/spec_check.py <root>... --stubs-from <skills dir>`
  before and after; afterwards it must accept the record (`--require-verified` makes a missing or
  stale record an error).
- **Record location**: `<root>/resources/<id>.verify.md`, beside the root marker; `spec_file` is
  relative to the root.

## Anchored specs and reviews

The kinds produced by `anchored-peripheral-spec` (`[src:]`/`[tgt:]` anchors, `Source pin:` /
`Target pin:`) and `reference-driver-review` (`[impl:]`/`[ref:]`, `Impl pin:` / `Ref pin:`). **Every
anchor is verified back to source**, in two layers:

1. **Resolve every anchor, mechanically.** Run `anchored-peripheral-spec/scripts/anchor_check.py`
   in its default mode with the spec's repositories (`--repo` / `--target-repo`, or `--impl-repo` /
   `--ref-repo` for a review) at the pins: every path must exist, every line range be in bounds,
   every symbol be present in or near its range, every hex literal in a claim appear in the lines it
   cites, every `[hw-required]` be backed by a `[doc:]`. Where register headers exist, run
   `inventory_check.py` too: omissions and value mismatches against the headers are findings. Any
   `[stale: was <pin>]` marker is a `FAIL` until a person re-verifies the claim and clears it.
2. **Judge every anchor, by reading.** Run the creating skill's own independent verifier as it
   defines it (`anchored-peripheral-spec/templates/verifier-prompt.md`, or
   `reference-driver-review/templates/verifier-prompt.md` for a review): a fresh subagent that
   renders the review sheet with `anchor_check.py --show`, which places each claim beside the
   source lines it cites, reads the main source files in full once, and decides for every anchor
   whether the cited lines *support the claim*, not merely whether they resolve: a range that
   exists but describes a different register, a symbol that is present but whose value the claim
   misstates, an ordering the lines do not establish, all `FAIL`. It keeps that verifier's blind
   re-derivation sample, recomputed counts, and re-established negative claims. `[doc:]` tags are
   checked against the document section the same way a board spec's `[databook]` is. What this
   skill adds is the record: that verifier's `{section, line, anchor, reason}` list becomes
   per-anchor verdict lines, and every anchor it passed gets a `PASS` line too.

- **Claims** are keyed by the anchor text as written (`[src: path:L1-L2 (symbol)]`), plus the
  `[doc:]` tags; a claim with several anchors gets one line per anchor.
- **Two verifiers** for the register-map tables (offsets, widths, bit positions), the densest values
  and the place `anchored-peripheral-spec` already runs two investigators.
- **Record location**: `resources/<spec-basename>.verify.md` in a `resources/` directory beside the
  spec, or, when the project already keeps `docs/provenance/` for the spec's sidecars, there as
  `<spec-basename>.verify.md`; say which in the report. `spec_file` is relative to the record's
  parent's parent. Save the `anchor_check.py` and `inventory_check.py` reports beside it.
- The record complements `anchor_check.py --drift`: drift detection says which anchors need
  re-review when the tree moves; this record says whether the claims were right at the pin.

## Clean-room driver specs

The kind produced by `cleanroom-spec`. Two passes, and the first is not this skill's to redefine:

1. **`cleanroom-spec`'s own verifier**, exactly as that skill defines it: a fresh subagent with its
   verifier template, the five checks (mechanical scan, leak judgment, hardware-derived structure,
   attractants, usage notice), and `os-investigator/scripts/leak_scan.py`. Run it; record its
   verdict in the record's body as the first line (`Clean-room verifier: PASS` or `FAIL — <what>`).
   That verifier checks the wall, not accuracy, by design.
2. **Accuracy**, which that verifier deliberately leaves out: every `[databook]`, `[standard]`, and
   `[DT]` fact in the register tables, bit fields, sequences, and constants is compared against the
   cited document section or device tree the way a board spec's facts are. `[source-observed]`
   facts are checked for their required markers ("order not known to be required", "re-derive on
   hardware") and against the source commit named in the provenance ledger; the verifier reads
   that source under `os-investigator`'s rule and quotes none of it. An `[inference]` fact is
   verified on its **argument**, not on a citation: do the stated premises hold at the pinned
   source, and does the conclusion actually follow from them? A premise that does not hold is a
   `FAIL`; premises that hold under a conclusion they do not support is also a `FAIL`, with the
   gap in the reasoning named. The commonest form is a workaround a driver applies to a whole
   family being written as a hardware requirement, when the erratum scopes it to one part.

- **Claims** are keyed by section and ordinal (tables: `<Section>/<table>/<row name>`; sequences:
  `<Section>/<step number>`).
- **Two verifiers** for the register map and the init sequence.
- **Record location**: `resources/<spec-basename>.verify.md` beside the spec, or the project's
  `docs/provenance/` directory when the spec's ledger already lives there; `spec_file` relative to
  the record's parent's parent. The record itself must pass `leak_scan.py`.

## Rules

- **You never read sources.** The verifier subagent does, in its own context.
- **You never edit a spec.** A `FAIL` is a finding with a proposed fix, not a change.
- **The record is the only output.** Nothing from the verifier's work goes anywhere else, and no
  reader loads the record's body: `board-expert` reports a spec's `verified` date and `summary`
  from the record's frontmatter only.
- **Fresh context, every time.** A re-run gets a new verifier that has not seen the old record.
- Commit or stage the record if the project commits them; do not push unprompted.
