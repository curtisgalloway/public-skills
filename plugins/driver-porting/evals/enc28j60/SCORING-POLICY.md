<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# ENC28J60 gold ledger: scoring policy

Version: enc28j60-1.2
Adopted: 2026-09-20 (superseding `enc28j60-1.1` of the same day; see "Version history")

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

## The operating envelope the weights assume

`LEDGER-FORMAT.md` weighs a row's consequence **adjusted for necessity**, and `critical` means a
working driver cannot avoid the requirement. "Cannot avoid" is only meaningful against a stated
idea of what the driver is for, so this is that statement, and every `critical` weight in the
ledger is to be read against it:

> The envelope is a driver that brings up an ordinary Ethernet interface: it receives frames
> addressed to its own unicast address and frames addressed to broadcast, it transmits, and it
> interoperates with a link partner in either duplex.

A requirement a driver can avoid **only by operating outside that envelope** is still `critical`.
Running permanently in promiscuous mode is the worked example: reception in that mode does not
depend on the MAADR registers, so a promiscuous-only driver could omit `INIT-024` and still
receive — and that is not a counterexample to the weight, because a driver that never accepts its
own unicast address is not the driver the envelope describes. `PHY-018` rests on the same clause
from the other direction: half duplex is inside the envelope, so a `critical` weight justified by
a half-duplex consequence does not have to argue that full-duplex drivers are also affected.

The envelope bounds the necessity argument only. It is not a scope rule: `in_scope` is what
removes a row from a denominator, and a row about an optional feature still caps at `important`
under `LEDGER-FORMAT.md`'s rule whatever the envelope says.

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

**Scope, recoverability and withdrawal filter the ledger's recall and probe rosters only.
Precision evaluates every claim the candidate makes.** A row that is out of scope, not
recoverable, or withdrawn sits outside every *denominator* and is reported separately, because it
measures the corpus rather than the candidate — but a candidate claim about its subject is judged
like any other claim. An incorrect wake-on-LAN claim is a precision error even though `IRQ-016` is
out of scope; a correct one is a correct claim that earns no recall credit. Nothing about a row's
scope reaches precision.

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

`LEDGER-FORMAT.md` authoring rule 3 says a row states one thing, and allows this policy to name a
**bounded** set of ids scored as composite units instead. The set below is that list.

**How a row was judged composite.** A row is composite when it states **two or more facts that
can each be checked, and found right or wrong, on their own** — a register's bit positions, a
table of codes, an address map, a set of reset values, a list of filter criteria or prohibitions,
the steps of a sequence with their own values, or two peer requirements sharing one subject. A row
is atomic when it states **one requirement**, even where the statement also carries the mechanism
that produces it, the value it takes, the condition it holds under, or the consequence of ignoring
it: contradict any of those and the requirement itself is contradicted, and a candidate that
states the requirement without them is already `partial` under the ordinary rule.

**The inventory was made by walking every active row in `ledger.yaml` on 2026-09-20**, not by
collecting the rows a reviewer happened to name. It is meant to be exhaustive as of that date and
that ledger, and the counts below are printed so a reader can check the list against the file
rather than take the claim on trust. It replaces the sixteen-id list of `enc28j60-1.1`, which was
an illustration presented as a boundary: an outside review found many rows outside it that bundle
independently falsifiable facts, and that gap is what this version closes.

**The inventory found 113 composite units among the 204 active rows**; the other 91 are atomic.

| Facet | Composite scoring units | Count |
|---|---|---|
| `REG` | REG-001, REG-002, REG-003, REG-004, REG-006, REG-007, REG-008, REG-009, REG-010, REG-011, REG-013, REG-014, REG-015, REG-017, REG-018, REG-019, REG-020, REG-021, REG-022, REG-023, REG-024, REG-025, REG-026, REG-027, REG-029 | 25 |
| `INIT` | INIT-001, INIT-003, INIT-005, INIT-007, INIT-010, INIT-011, INIT-012, INIT-015, INIT-016, INIT-017, INIT-019, INIT-020 | 12 |
| `TX` | TX-001, TX-002, TX-003, TX-004, TX-006, TX-007, TX-008, TX-010, TX-012, TX-014, TX-015, TX-018, TX-019 | 13 |
| `RX` | RX-001, RX-007, RX-009, RX-011, RX-012, RX-015, RX-017, RX-018, RX-019, RX-020, RX-021, RX-024, RX-025, RX-026, RX-027 | 15 |
| `IRQ` | IRQ-001, IRQ-006, IRQ-007, IRQ-008, IRQ-009, IRQ-010, IRQ-011, IRQ-012, IRQ-016, IRQ-018 | 10 |
| `PHY` | PHY-001, PHY-002, PHY-003, PHY-006, PHY-007, PHY-008, PHY-011, PHY-013, PHY-014, PHY-015, PHY-016, PHY-017, PHY-018, PHY-019, PHY-020, PHY-022, PHY-026, PHY-029, PHY-031, PHY-032 | 20 |
| `SPI` | SPI-001, SPI-002, SPI-004, SPI-005, SPI-006, SPI-013, SPI-014, SPI-016, SPI-019, SPI-020 | 10 |
| `ELEC` | ELEC-001, ELEC-002, ELEC-003, ELEC-004, ELEC-005, ELEC-007, ELEC-008 | 7 |
| `ERR` | ERR-001 | 1 |
| **Total** | | **113** |

**The verdict rule, for all 113.** Each contributes one denominator unit. `covered` means every
enumerated fact is stated correctly; `partial` means at least one is correct, others are omitted
or underspecified, and none is contradicted; `missing` means none is stated; `misstated` means at
least one is contradicted. `partial` earns 0.5; `missing` and `misstated` earn zero. Precision
evaluates the candidate's individual claims independently, so one wrong bit is one precision error
whatever the row verdict is.

Eleven of the 113 are rows no recall denominator contains: the `observed-software-behavior` rows
REG-007, RX-026 and IRQ-018, the `implementation-choice` rows INIT-010, RX-021, RX-025 and
TX-018, and the out-of-scope rows IRQ-016, ELEC-004, ELEC-005 and ELEC-007. They are listed
because the rule still has
work to do wherever the row is scored at all: a precision probe is `misstated` when at least one
of its enumerated facts is asserted as a hardware requirement, on the same "at least one"
threshold, and not only when the whole row is.

**Enumerated rather than split.** Enumeration is the disposition for a row that is one register's
definition, one document table, or one mechanism a reader looks up in one place — the shape the
adjudicator approved for the original seven, and the disposition 111 of the 113 took. Splitting
is for a row that bundles things a reader would look up in different places. Every one of the 113
was put to that second question and two met it, on 2026-09-20: PHY-006's reserved-bit write
rule became PHY-033 (a register's write rule is read in that register's definition, not in the
PHY register summary), and TX-019's half-duplex backpressure clause became TX-024 (a different
mechanism from the pause frames the rest of the row describes). Two rows were deliberately *not*
split: REG-023, because the 2026-09-19 merge folded the withdrawn REG-030 and REG-031 into it and
splitting would reopen a settled merge, and RX-019, for the same reason with RX-034.

The set is not one row per register. PHY-007 covers MICMD **and** MISTAT and PHY-019 covers PHIE
**and** PHIR; TX-008 is the seven-byte transmit status vector and RX-011 the four-byte receive
one; RX-019 carries the ANDOR combination rule and CRCEN's ordering alongside ERXFCON's bit
positions; REG-001 to REG-004 are the four bank columns of one register map.

**The exception covers these 113 ids and no others.** A row not in the table is governed by
authoring rule 3, and the walk that produced the table is the evidence that a row's absence from
it is a judgment rather than an oversight. Adding an id takes a decision in `ADJUDICATION.md` and
a new policy version, because the list is part of the frozen policy text. Two rows stating the
same clause is a different problem — that is overlap, disposed of in the ledger with `overlaps`
and `replaced_by`, adjudicated in group F and swept again before the freeze.

## Precision adjudication

- Precision is computed over **the candidate's own claims, including claims with no ledger row**. A
  claim the ledger never anticipated is still judged, and a wrong one is still an error.
- **The formula.**

      precision = (N - errors) / N

  `N` is every claim the candidate makes, after the deduplication below. Unsupported and partial
  claims **stay in `N`** and are not errors: they are counted and reported separately, beside
  precision, precisely because they do not move it. `N = 0` prints `n/a (0 claims)`, never `0%`
  and never `100%`.
- **Segmentation.** A claim is one independently falsifiable proposition: one value, one ordering,
  one access rule, one consequence. **Count semantic assertions independent of formatting: a label
  and its value form one assertion.** The same register mapping is the same number of claims
  whether the candidate prints it as a sentence, a bullet or a table row, so a candidate cannot
  move its own precision by reformatting. A candidate sentence carrying three assertions is three
  claims, and a table row is a claim per cell that asserts something.
- **Deduplication.** The same proposition asserted more than once in the candidate is one claim,
  judged once, at its strongest statement. A candidate claim that matches several ledger rows is
  also one claim and counts once — overlapping ledger rows do not multiply a single error, which
  is why the freeze gate refuses undisposed overlaps.
- **Contradicted** — the corpus says otherwise. An error.
- **Unsupported** — the corpus neither states it nor contradicts it. Not an error; recorded as its
  own count, because a specification full of unsupported claims is a distinct failure from an
  accurate one and the number has to be visible.
- **The three ways a claim about hardware necessity can go wrong**, which the two rules above are
  otherwise read as deciding differently:
  - **Contradicted** when the corpus establishes a valid alternative — that the requirement can be
    met another way, or need not be met at all. An error.
  - **Unsupported** when the corpus neither states the necessity nor establishes an alternative.
    Not an error. Corpus silence never makes a necessity claim wrong, in either direction.
  - **An attribution error** when the claim is credited to a named source that does not state it.
    An error whether or not the requirement itself turns out to be true, and counted once, against
    the claim it attaches to.
  A candidate asserting a behavior the reference driver chose as a hardware requirement is the
  first of these where the corpus shows the alternative — which is what the `implementation-choice`
  probes measure — and the second where it does not.
- **Partial** — true but underspecified (a value without its constraint, a sequence without its
  ordering). Not an error; counted separately, and it may still leave the matching row `partial`.
- **Conditional** — true under a condition the candidate states (a silicon revision, a duplex
  mode, a configuration). Judged against the condition: correct with it, an error without it if
  the unconditional form is false.
- **An observation of driver behavior, correctly attributed** — "the reference driver does X" — is
  judged as that claim and is not an error when true.
- **What a verdict is given against.** A row's `statement` is the scoring target. Its `notes`, its
  `derivation` locators and any cross-reference either of them carries are context for the scorer
  and are never content a candidate is expected to reproduce: a candidate loses nothing by omitting
  them and gains nothing by restating them. Where a clause was moved to another row and left behind
  as a cross-reference, the row named in the cross-reference is the one that scores that clause.
- **Content that follows from a concrete value.** A candidate that states a concrete value from
  which a row's content follows **covers** that row, without also stating it in the row's terms.
  RX-029 is the worked example: a candidate specifying `ERXST = 0x0000` has satisfied the
  even-address recommendation and does not have to repeat the recommendation to earn the row.
- `misstated` counts as `missing` for recall **and** as an error for precision.

## Uncertainty

- **An inference presented as an inference** — stated with its premises and marked as a conclusion
  rather than a reading — scores `covered` on an `inference` row and is not a precision error.
- **The same content asserted as documented fact** is **`covered` for recall and a separate
  precision attribution error**. It is explicitly *not* a `misstated` recall row: the content is
  right and the sourcing is wrong, those are two different failures, and the general `misstated`
  rule — which would zero the row — does not apply. Scoring it both ways would punish one mistake
  twice and hide which one it was.
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

The freeze lock records this file's **sha256 as well as the version string** `enc28j60-1.2`,
beside the ledger and corpus digests, and every run cites the lock rather than the version. A
version label on a mutable file binds nothing: the label can stay while the text moves.
`ledger_check.py --lock` now enforces that. It requires a `Version:` line in this file and a
non-empty `policy_version` and `policy_sha256` in the lock, and fails when either side is missing
or the two disagree — two absent versions no longer agree by accident. The lock additionally pins
`LEDGER-FORMAT.md`'s bytes as `format_sha256`, because the verdict definitions and the authoring
rules this policy builds on live there, and carries a `revision` identifying the repository state
that holds the checker, the adjudication record and the authoring brief: a digest identifies
bytes, and a revision is what makes them recoverable.

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
| `enc28j60-1.2` | 2026-09-20 | The composite inventory, made by walking every active row: **16 ids to 113**, with the test that decided each row written down and the per-facet counts printed. Every row's verdict rule can change with it, so the bump is mandatory. The same version carries five other rule changes a scorer would feel: the operating envelope the `critical` weights assume, stated so the necessity argument is checkable; that scope filters rosters only while precision covers every candidate claim; the contradicted / unsupported / attribution-error distinction for necessity claims; that correct inference content presented as documented fact is covered content with a precision attribution error and not a `misstated` row; formatting-independent segmentation; what a verdict is given against and when a concrete value earns coverage; and the precision formula written out with its denominator and its `n/a` case. Two rows were split rather than enumerated (PHY-006 to PHY-033, TX-019 to TX-024), so the ledger's active row count moves from 202 to 204. |

No candidate has been read under any version, so nothing needs rescoring; the rule below is for
when that stops being true.

## Changes after a candidate has been read

A correction found after any candidate has been read gets a **new ledger or policy version and a
declared rescoring procedure**. The original result is never silently altered: it keeps its own
version beside the new one, and a rescore is a new run with its own record. A denominator chosen
after seeing a candidate is not a measurement.
