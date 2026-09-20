<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# ENC28J60 gold ledger: scoring policy

Version: enc28j60-1.1
Adopted: 2026-09-20 (superseding `enc28j60-1.0` of the same day; see "Version history")

`LEDGER-FORMAT.md` says that whether `observed-software-behavior` and `inference` rows count
toward recall is a per-run decision, and that the decision is **versioned and named in the freeze
lock before any candidate is generated**. This file is that named policy for the ENC28J60 pilot,
adopted by the adjudicator as group A4 answer (a).

## Terms

- **Denominator** — the set of ledger rows a recall percentage is computed over. Frozen before any
  candidate exists, and the candidate cannot influence it.
- **Recall** — the fraction of the denominator a candidate covers.
- **Precision** — the fraction of the candidate's own claims that are not errors. Its denominator
  is the candidate's claims, not the ledger's rows.
- **Class** — what kind of claim a row is: `documented-hardware-requirement`,
  `observed-software-behavior`, `inference`, `implementation-choice`, `unresolved-conflict`.
- **Weight** — `critical` (a driver that misses it does not work, or corrupts data), `important`
  (degraded or fragile), `minor` (completeness). Recall is reported per weight.
- **Claim** — one independently falsifiable proposition in the candidate, as segmented below.

## Eligibility

A row is in the recall denominator when **all four** hold: `status: active`, `in_scope: true`,
`recoverable: true`, and a class the table below includes. Nothing else filters the set. Not
silicon revision — a row affecting one revision counts the same as one affecting four. Not
`applicability.vendor_confirmed`, `implementation_observed` or `unresolved`; those columns are
reported, never subtracted. And never anything derived from a candidate: not its scope, its
headings, its stated assumptions, or what it turned out to cover.

| Class | In the recall denominator? |
|---|---|
| `documented-hardware-requirement` | **Yes.** |
| `unresolved-conflict` | **Yes.** Scored `covered` when the candidate states the conflict, not when it picks a side. |
| `inference` | **Yes.** A conclusion a careful reader of the corpus can reach is a conclusion a candidate is expected to reach. |
| `observed-software-behavior` | **No.** Reported as its own count, never folded into recall. |
| `implementation-choice` | **No.** A precision probe: a candidate that states it as a hardware requirement is scored `misstated`; one that omits it is scored nothing at all. |

Rows that are out of scope, not recoverable, or withdrawn are outside every denominator, whatever
their class, and are reported separately — they measure the corpus, not the candidate.

**Rosters, as of 2026-09-20 and regenerated from the ledger at freeze.** Observed software
behavior, thirteen active rows, counted but not in recall: REG-007, TX-022, RX-026, RX-030,
RX-037, RX-039, IRQ-014, IRQ-018, IRQ-019, PHY-027, SPI-022, SPI-023, ERR-006. Inference, three
active rows, in recall: RX-006, RX-031, PHY-012. Their conditions and inference status survive
inclusion: RX-006 is not a universal odd-`ERXND` obligation and PHY-012 is not a universal
explicit-programming obligation. `unresolved-conflict`, no active rows: REG-007 was the only one
and was reclassed on 2026-09-20 (`ADJUDICATION.md` group E2), so the class stays in the table
above for a future row and contributes nothing to this run's denominator.

## The recall formula

    recall = (covered + 0.5 x partial) / eligible rows

Reported **overall and within each weight bucket**, never blended into one number: 90% with every
`critical` row missing is not a good specification. `missing` and `misstated` contribute zero.
Each bucket prints its own numerator terms beside the percentage, because a specification that is
100% `partial` is a distinct failure from one that is 50% `missing` and both print the same
percentage. An empty weight bucket prints `n/a (0 eligible rows)` — never `0%`, and never `100%`.

## Composite scoring units

These sixteen rows are composite scoring units, exempt from `LEDGER-FORMAT.md` authoring rule 3
(atomic rows):

- Named in `enc28j60-1.0`: **REG-010, PHY-007, PHY-008, PHY-016, PHY-017, PHY-018, PHY-019.**
- Added in `enc28j60-1.1`: **REG-008, REG-009, REG-018, REG-021, REG-022, RX-011, RX-019,
  IRQ-001, TX-008.**

Each contributes one denominator unit, under one verdict rule for all sixteen. `covered` means
every enumerated fact is stated correctly; `partial` means at least one is correct, others are
omitted or underspecified, and none is contradicted; `missing` means none is stated; `misstated`
means at least one is contradicted. `partial` earns 0.5; `missing` and `misstated` earn zero.
Precision evaluates the candidate's individual claims independently, so one wrong bit is one
precision error whatever the row verdict is.

The set is not strictly one row per register: PHY-007 covers MICMD **and** MISTAT, and PHY-019
covers PHIE **and** PHIR. Nor is every unit a register: TX-008 is the seven-byte transmit status
vector and RX-011 the four-byte receive one, and RX-019 carries the ANDOR combination rule and
CRCEN's ordering alongside ERXFCON's bit positions, because the 2026-09-19 pass withdrew RX-034
into it and splitting would undo that.

**The exception covers these sixteen ids and no others.** Any other row that bundles
independently falsifiable facts remains subject to the atomic-row rule; adding one here takes a
decision in `ADJUDICATION.md` and a new policy version, because the id list is part of the frozen
policy text. The two rows of `ADJUDICATION.md` group G that are not in the list were narrowed
instead of enumerated: REG-029 now states the EIR bit positions and its reserved bit only, and
PHY-020 the PHLCON layout, reset value and reserved-as-1 bits, with the LED configuration codes
split out as PHY-032. This exception says nothing about two rows stating the same clause — that is
overlap, a different problem, disposed of in the ledger with `overlaps` and `replaced_by` and
adjudicated in group F, which is now answered.

## Precision adjudication

- Precision is computed over **the candidate's own claims, including claims with no ledger row**. A
  claim the ledger never anticipated is still judged, and a wrong one is still an error.
- **Segmentation.** A claim is one independently falsifiable proposition: one value, one ordering,
  one access rule, one consequence. A candidate sentence carrying three of them is three claims,
  and a table row is a claim per cell that asserts something.
- **Deduplication.** The same proposition asserted more than once in the candidate is one claim,
  judged once, at its strongest statement. A candidate claim that matches several ledger rows is
  also one claim and counts once — overlapping ledger rows do not multiply a single error, which
  is why the freeze gate refuses undisposed overlaps.
- **Contradicted** — the corpus says otherwise. An error.
- **Unsupported** — the corpus neither states it nor contradicts it. Not an error; recorded as its
  own count, because a specification full of unsupported claims is a distinct failure from an
  accurate one and the number has to be visible.
- **Partial** — true but underspecified (a value without its constraint, a sequence without its
  ordering). Not an error; counted separately, and it may still leave the matching row `partial`.
- **Conditional** — true under a condition the candidate states (a silicon revision, a duplex
  mode, a configuration). Judged against the condition: correct with it, an error without it if
  the unconditional form is false.
- **An observation of driver behavior, correctly attributed** — "the reference driver does X" — is
  judged as that claim and is not an error when true. Asserting the same X as a hardware
  requirement is an error, and that inversion is what the `implementation-choice` probes measure.
- `misstated` counts as `missing` for recall **and** as an error for precision.

## Uncertainty

- **An inference presented as an inference** — stated with its premises and marked as a conclusion
  rather than a reading — scores `covered` on an `inference` row and is not a precision error. The
  same content asserted as documented fact is `covered` for recall and a precision error for the
  attribution.
- **An unresolved conflict** scores `covered` when the candidate states that the sources disagree
  and names both readings; picking a side, however defensible, is `partial`, and picking one while
  presenting it as settled is `misstated`.
- **Uncertainty never shrinks the denominator.** `applicability.unresolved: true`, a hedge in a
  row's `notes`, or a reviewer's open question leaves the row eligible exactly as it was.
  Excluding a row takes `in_scope: false` or `recoverable: false`, with the reason in `notes`,
  recorded before the freeze.

## Reporting

Recall per weight and unweighted, never one blended number, with `partial` also as its own count;
the observed-software-behavior counts beside recall, never inside it; the implementation-choice
probes as a count of `misstated` out of the probes, which is a precision result and not a recall
one; the unsupported-claim count beside precision.

## Binding

The freeze lock records this file's **sha256 as well as the version string** `enc28j60-1.1`,
beside the ledger and corpus digests, and every run cites the lock rather than the version. A
version label on a mutable file binds nothing: the label can stay while the text moves. Enforcing
this in `ledger_check.py` is open work and is a prerequisite to freezing.

## Version history

A version is a name for one exact set of scoring rules. The id list under "Composite scoring
units" is part of that set, so lengthening it is a new version and not an edit: a run scored under
`enc28j60-1.0` put one denominator unit where a run scored under `enc28j60-1.1` puts one for nine
further rows, and the two recall numbers are not comparable. Nothing forces the bump
mechanically — the freeze lock pins the file's sha256, so an unversioned edit would be caught as a
changed hash rather than as a changed policy, which says "this file moved" and not "these results
mean something different". The version string is what carries that second meaning, so it moves
whenever the rules do.

| Version | Adopted | What changed, and why the bump |
|---|---|---|
| `enc28j60-1.0` | 2026-09-20 | First named policy: the group A4 denominator rule, eligibility, the recall formula, precision adjudication, uncertainty, binding, and seven composite scoring units. |
| `enc28j60-1.1` | 2026-09-20 | Nine more composite scoring units (REG-008, REG-009, REG-018, REG-021, REG-022, RX-011, RX-019, IRQ-001, TX-008), from `ADJUDICATION.md` group G. The id list is frozen policy text and each addition moves a row from "one wrong bit fails the row" to the composite verdict rule, so the denominator and the per-row verdicts both change. The observed-software-behavior roster also grew from ten rows to thirteen (REG-007 reclassed by group E2; SPI-023 and RX-039 added by group D), which changes the recall denominator by removing REG-007 from it; the same bump carries it. |

No candidate has been read under either version, so nothing needs rescoring; the rule below is for
when that stops being true.

## Changes after a candidate has been read

A correction found after any candidate has been read gets a **new ledger or policy version and a
declared rescoring procedure**. The original result is never silently altered: it keeps its own
version beside the new one, and a rescore is a new run with its own record. A denominator chosen
after seeing a candidate is not a measurement.
