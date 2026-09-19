<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# ENC28J60 pilot

The calibration device for the driver-spec evaluation described in `../../EVAL-PLAN.md`. A small,
fully public SPI Ethernet controller: the point is to get the ledger format, the scoring and the
test quality right on something cheap before the method is pointed at a complex SoC.

## What is here

| File | Phase | What it is |
|---|---|---|
| `corpus.yaml` | 1 | the frozen reference corpus: every source the gold ledger may be authored from, pinned by commit or document hash |
| `corpus_check.py` | 1 | re-fetches every pin and reports drift |
| `LEDGER-FORMAT.md` | 2 | what a gold-ledger row is, and why its IDs come from the corpus rather than from any document's headings |

The ledger itself is not written yet. It must be authored **from `corpus.yaml` alone, before any
generated specification is read** — that independence is what makes the recall number mean anything,
and it cannot be recovered after the fact. `LEDGER-FORMAT.md` is deliberately settled first, because
the one decision that cannot be retrofitted is how a requirement is identified.

## Checking the pins

```bash
python3 corpus_check.py            # 0 all match, 1 drift, 3 something unreachable
python3 corpus_check.py --json
```

Stdlib only, no network credentials. Run it before authoring against the corpus and again before
scoring a candidate: a document that drifted between those two moments is a document the ledger and
the candidate were judged against differently.

## Two traps this corpus exists to record

**Errata are renumbered between editions.** DS80349C inserts two issues ahead of the list in
DS80349B, so every number below them shifts. A bare "issue 12" in a driver comment or a mailing
list post names different silicon depending on which edition its author had. `errata_map` records
both editions in full so a bare reference can be resolved, or recorded as unresolvable.

**Both served errata editions accompany DS39662C, while the current data sheet is DS39662E.** There
is no errata edition published against D or E at the vendor's url pattern. A ledger row pairing an
erratum with a data sheet section has to say which data sheet edition it read that section in.
