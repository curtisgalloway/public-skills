<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Gold ledger format

The answer key's shape, designed before the key is written. `../../EVAL-PLAN.md` phase 2 authors the
rows; this file says what a row is, and it exists separately because one constraint has to be
settled before authoring starts and cannot be retrofitted afterwards: **a requirement's identity
comes from the corpus, never from a document's structure.**

## Terms

- **Requirement** — one atomic thing the hardware demands of any correct driver. Not a sentence in a
  document and not a section: if two claims can be independently right or wrong, they are two rows.
- **Row** — one requirement in the ledger, with the fields below.
- **Candidate** — the specification being graded, produced by `cleanroom-spec` on a given run.
- **Denominator** — the set of rows a recall percentage is computed over. Frozen, and the candidate
  cannot influence it.
- **Corpus** — the pinned sources in `corpus.yaml`. The only thing a row may be derived from.

## Why IDs cannot come from headings

The obvious scheme — number a requirement after the data sheet section it came from — fails three
ways at once, and each failure is silent.

A data sheet is re-sectioned between editions, so an ID minted against DS39662C names something
else, or nothing, in DS39662E. Errata are renumbered outright: DS80349C inserts two issues ahead of
DS80349B's list, so the same subject moves from item 12 to item 15 (`corpus.yaml` → `renumbering`).
And an ID taken from the *candidate's* headings lets a candidate change its own denominator by
reorganizing, which is the failure the whole exercise exists to prevent.

So an ID is minted once, at authoring time, from a fixed facet vocabulary, and never changes
meaning again. Where the requirement was read is a *field*, not the name.

```
ENC28J60-<FACET>-<NNN>
```

`<NNN>` is a zero-padded sequence within the facet, assigned in authoring order. **Numbers are never
reused and never renumbered**, including when a row is withdrawn: a withdrawn row keeps its ID and
gains `status: withdrawn`, so a score computed last month can still be read.

| Facet | Covers |
|---|---|
| `REG` | register existence, address, width, access, reset value, bit semantics |
| `INIT` | power-on and reset sequencing, ordering constraints, required waits |
| `TX` | transmit path: buffer layout, descriptors, status, collision behavior |
| `RX` | receive path: buffer layout, the circular buffer, filters, status |
| `IRQ` | interrupt sources, flags, masking, acknowledgement, known unreliability |
| `PHY` | PHY registers, link, duplex, loopback, polarity, LEDs |
| `SPI` | host interface: framing, opcodes, clock constraints, timing |
| `ELEC` | electrical and environmental limits that constrain software |
| `ERR` | an erratum's *hardware* requirement, where no other facet states it |

A requirement goes in the facet a driver author would look under, not the one the document filed it
in. `ERR` is for a requirement that exists only because of an erratum and has no natural home;
an erratum that changes a register's meaning is a `REG` row that cites the erratum.

## Row schema

```yaml
- id: ENC28J60-RX-004
  statement: >-
    The receive buffer must begin at address 0x0000; a driver that places it elsewhere will see
    corrupted receive data.
  class: documented-hardware-requirement
  derivation:
    - source: DS80349C
      locator: "silicon issue 5 (Memory, Ethernet Buffer)"
    - source: DS39662E
      locator: "receive buffer section"
  applicability:
    vendor_confirmed: [B1, B4, B5, B7]
    implementation_observed: true
    unresolved: false
  weight: critical
  in_scope: true
  recoverable: true
  status: active
  notes: >-
    Stated in the errata rather than the data sheet body; a reader working only from DS39662E can
    reach the opposite conclusion.
```

### Fields

**`id`** — as above. Immutable.

**`statement`** — what the hardware requires, in the ledger author's own words, phrased so it can be
judged present or absent in a candidate without matching wording. Never a quotation.

**`class`** — one of five, and the distinction the evaluation turns on:

| Class | Meaning |
|---|---|
| `documented-hardware-requirement` | a vendor document states it |
| `observed-software-behavior` | the reference driver does it; whether the hardware demands it is a separate question |
| `inference` | concluded from the above rather than read; carries `premises`, `derivation`, `confidence`, `settled_by` |
| `implementation-choice` | the driver's decision, binding on nobody — present so a candidate is not penalized for omitting it, and *is* penalized for stating it as a requirement |
| `unresolved-conflict` | two sources disagree and no reading settles it |

A candidate that states an `implementation-choice` as a hardware requirement fails on precision even
though the underlying behavior is real. That inversion is the sharpest probe in the benchmark and it
only works if the ledger classes every row honestly, including the uncomfortable ones.

**`derivation`** — where it came from: a `source` naming a pin in `corpus.yaml` by its edition or
commit, plus a `locator` a reader can follow. **Never a page number alone** — a page number is an
edition's property, and the locator has to survive the edition changing.

**`applicability`** — the three columns EVAL-PLAN Correction 2 requires, never collapsed into a
boolean:

- `vendor_confirmed` — silicon revisions the errata's affected-revisions matrix lists
- `implementation_observed` — whether the reference driver applies it, whatever the vendor says
- `unresolved` — true when neither settles the question

`unresolved: true` is never scored as a proven contradiction in either direction. Absence from a
vendor document does not prove a device unaffected.

**`weight`** — `critical` (a driver that misses it does not work, or corrupts data), `important`
(degraded or fragile), `minor` (completeness). Recall is reported **per weight and unweighted**,
never as a single blended number: 90% with every `critical` row missing is not a good spec.

**`in_scope`** — whether the row counts toward the denominator for this evaluation. Set at authoring
time with a reason in `notes`. A row can be out of scope for being about a facet the evaluation is
not asking for; it is never out of scope for being hard.

**`recoverable`** — whether the requirement is *derivable at all* from the material a candidate was
given. A row that is not recoverable stays in the ledger, is excluded from the recall denominator,
and is reported separately: it measures the corpus, not the candidate.

**`status`** — `active` or `withdrawn`. Withdrawal keeps the ID and records why.

## Scoring, gold to candidate

Each in-scope, recoverable, active row gets exactly one verdict against a candidate:

| Verdict | Meaning |
|---|---|
| `covered` | the candidate states the requirement with enough precision to implement it |
| `partial` | present but underspecified: a value without its constraint, a sequence without its ordering, a requirement stated as optional |
| `missing` | absent, or present only as a `TODO` |
| `misstated` | present and wrong — counts as `missing` for recall **and** as an error for precision |

**The denominator is the frozen in-scope set.** Not the candidate's sections, not its TODO list. A
candidate that omits an entire facet incurs every omission in it. `partial` counts as half in the
weighted recall and is always also reported as its own count, because a spec that is 100% partial is
a distinct failure from one that is 50% missing and both can print the same percentage.

## Authoring rules

1. **Blind.** The ledger is authored without reading any candidate specification. Once a row's
   author has seen a candidate, that author cannot write rows for that device.
2. **From the corpus only.** Every row cites a pin in `corpus.yaml`. Run `corpus_check.py` first: a
   row derived from a document that has since drifted is a row derived from an unknown document.
3. **Atomic.** If a reviewer can agree with half a row, split it.
4. **Two readers on `critical` rows**, independently, with disagreements recorded as
   `unresolved-conflict` rather than settled by whoever wrote first — the same rule
   `spec-verifier` applies to a claim, applied to the answer key.
5. **Freeze before generating.** The ledger's hash is recorded before a candidate run begins. A row
   added after a candidate is read is not part of the denominator, and is marked so.

## What this format cannot do

It scores whether a requirement is *stated*. It does not score whether a driver written from the
statement would work — that needs the hardware fixture and an executing test, and those results
belong beside a run, not in the ledger. A row's `weight` is a judgment about consequence, made
before any of that evidence exists, and should be read as one.
