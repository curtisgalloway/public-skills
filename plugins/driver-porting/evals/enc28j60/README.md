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
| `ledger.yaml` | 2 | the gold ledger: authored blind by two independent readers from `corpus.yaml` alone, merged with every disagreement preserved; **not yet frozen** |
| `LEDGER-CONFLICTS.md` | 2 | the merge's conflict log: every reader disagreement, one-sided critical row, overlap, and correction applied since, for the adjudicator |
| `ADJUDICATION.md` | 2 | the decisions a person must make before the freeze, each answerable with a letter or number |
| `SCORING-POLICY.md` | 2 | the versioned scoring policy the freeze lock names: which classes are in the recall denominator, how precision is computed, how results are reported |
| `ledger_check.py` | 2 | the mechanical gate on the ledger: schema, ids, classes, derivations against the corpus pins; `--freeze` for the freeze rules; `--lock` to check a frozen ledger against its lock |

## State of the ledger

Authored 2026-09-19. Two readers, A and B, each wrote a full ledger from the pinned corpus in a
fresh context, without sight of each other or of any generated specification; there was no
ENC28J60 candidate spec anywhere in this repository at the time, so the blind rule held by
construction. A merger, not an author, combined the drafts (175 and 171 rows) into one file under
written rules: nothing dropped, A's ids kept, weight disputes recorded rather than settled. The
proposal's author reviewed the result through the `consult` skill; the row-level corrections that
review established from the sources, and a clause-level overlap pass, were then applied and
logged. Every step is in `LEDGER-CONFLICTS.md`.

What remains before the freeze is adjudication: `ADJUDICATION.md` holds the decisions, and
`ledger_check.py --freeze` counts what is still provisional. The ledger is usable now for reading;
it is not usable for scoring until it is frozen.

## Freezing the ledger

Run in this directory (the checker needs PyYAML):

```bash
uv run --with pyyaml python3 ledger_check.py ledger.yaml --freeze   # must report 0 errors
python3 corpus_check.py                                              # must report 0 drifted
python3 ../../skills/os-investigator/scripts/leak_scan.py \
  ledger.yaml SCORING-POLICY.md LEDGER-CONFLICTS.md ADJUDICATION.md README.md \
  --whitelist leak-scan-whitelist.txt \
  --against <your cache>/enc28j60.c <your cache>/enc28j60_hw.h    # must report no findings
```

The ledger is a clean-side artifact: it describes what the reference driver does and never quotes
it, so it has to pass the scanner the same way a clean-room spec does. The whitelist holds the two
file names the corpus pins, because a row cites them in `derivation.source` by name.

Then write `ledger.lock`. The checker requires **all seven** of these fields, and refuses a lock
that omits one — `ledger_check.py ledger.yaml --json` prints the five digest and version values
it computes, so the lock can be filled from its output:

| Field | What it holds |
|---|---|
| `frozen` | the date the ledger was frozen |
| `revision` | the repository revision that holds the checker, the adjudication record and the authoring brief; a digest identifies bytes, a revision makes them recoverable |
| `sha256` | `ledger.yaml`'s digest |
| `corpus_sha256` | `corpus.yaml`'s digest, the manifest the check ran against |
| `policy_version` | the scoring policy's `Version:` string, currently `enc28j60-1.2` |
| `policy_sha256` | `SCORING-POLICY.md`'s digest, because a version label on a mutable file binds nothing |
| `format_sha256` | `LEDGER-FORMAT.md`'s digest, because the verdict definitions and authoring rules the policy builds on live there |

and the adjudicator's attestation:

> Each scored proposition has one active scoring representation, except any duplicated
> contributions explicitly enumerated by the frozen policy. Multi-proposition scoring units are
> explicitly enumerated and use that policy's verdict rule. All provisional merge decisions have
> recorded dispositions. Each critical requirement has independent supporting derivations or an
> explicitly unresolved disposition. The ledger and corpus digests were recorded before candidate
> generation; subsequent candidate-informed corrections belong to a separately identified
> benchmark revision.

From then on `ledger_check.py ledger.yaml --lock ledger.lock` refuses an edited ledger, and a
candidate run names the lock it was scored against. A row added after a candidate has been read
is not part of that denominator and says so.

**What the lock check now enforces.** `ledger_check.py --lock` validates the ledger and corpus
digests **and** the scoring policy's version string and sha256, refusing a lock that omits either
and a policy file that declares no `Version:` line — two absent versions no longer compare equal
and pass by accident. It also pins `LEDGER-FORMAT.md`'s bytes and requires a repository revision,
so a score cites a policy, a format and a tree that can all be reconstructed. This was open work
and a stated prerequisite to freezing; it is closed.

## Input history

Entries a reader of a score needs, in order:

- **2026-09-19, before any freeze or candidate.** `corpus.yaml` recorded DS80349C silicon issue 1
  (MAC registers unreliable with a slow asynchronous SPI clock) as affecting B5 and B7. One of the
  blind readers, working from the extracted text, saw the marks under B1 and B4 and flagged the
  disagreement instead of following the manifest; the rendered Table 2 and the issue's own box
  confirmed B1 and B4. Corrected in the manifest, and in the one ledger row that cites the issue
  (`ENC28J60-SPI-017`). The pinned documents did not change. No score used the earlier manifest,
  because no candidate has been scored.
- **2026-09-19.** The remaining affected-revision lists (issues 2, 4 to 7, 9 to 12, 14 to 19) and
  Table 3's three conformance issues were added to the manifest from the same page, so the map is
  the source of those lists rather than the drafts.

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
