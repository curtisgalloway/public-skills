<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Phase 3: the paired with-skill and without-skill run

`EVAL-PLAN.md` phase 3 is the measurement the whole pilot exists for: does the driver-porting
skill make a specification better? That question is only answerable by generating two candidates
that differ in **one** thing, and the first practice run is the record of how easily that one
thing stops being one thing. This file is the protocol, written before a run so it cannot be
adjusted after seeing a result.

No paired run has taken place. This is a protocol, not a result.

## What the practice run established about the design

The 2026-09-20 run (`PRACTICE-RUN.md`) was a workflow trial with a single arm, and its record
names three ways the comparison would have been invalid had it claimed to be one:

- **The author received the full corpus manifest.** `corpus.yaml` pins the sources *and* carries
  the reading of them: the EREVID revision codes that `ENC28J60-REG-015` scores, the
  edition-by-edition errata index, the renumbering worked example, and comments explaining why
  each trap is a trap. An author given that file has been handed scored facts.
- **The prompt repeated the skill's structure.** A baseline arm whose prompt describes the
  treatment is not a baseline; it is the treatment, delivered by another route.
- **The generating model's relationship to the ledger's authors was unknown**, and stayed
  recorded as unknown rather than assumed away.

## The one difference

| | Treatment arm | Baseline arm |
|---|---|---|
| Skill | driver-porting skills loaded | none loaded |
| Prompt | the skill's own entry point | the task, with no structure, headings, section list, or method |
| Author manifest | `author-manifest.yaml` | the same bytes |
| Documents and driver | fetched by the author from the pins | the same |
| Tools, budget, access profile | identical | identical |
| Model | the same model and settings | the same |

Everything in the "identical" rows is recorded per arm in the review's `run` block, and a run
whose arms differ in any of them is reported as unpaired rather than scored as a comparison.

## The author manifest

Generate it; never hand over `corpus.yaml`:

```sh
uv run --with pyyaml python3 author_manifest.py --output author-manifest.yaml
uv run --with pyyaml python3 author_manifest.py --check author-manifest.yaml   # before each run
```

It carries the device, the document editions with their hashes and url pattern, and the driver's
commit and file hashes — enough to fetch every source and verify it arrived intact. It carries no
errata index, no revision codes, no reading of which editions pair with which, and no comments,
because it is re-emitted from an explicit key allowlist rather than filtered. A key added to
`corpus.yaml` later is absent from it until someone adds it to that allowlist deliberately.

**The author still has to read the documents.** That is the point: the traps the ledger scores —
that errata issue numbers are renumbered between editions, that both served errata editions name
a data sheet edition two revisions old, that `EREVID`'s codes do not track the revision number —
are reachable from the pinned documents and are exactly what the manifest refuses to pre-chew.

## Baseline prompt discipline

The baseline prompt states the task and the deliverable, and nothing about how to do it. In
particular it must not name a section, a table, a provenance tag, a confidence vocabulary, an
applicability column, or any other structure the skill supplies. Write it before writing the
treatment prompt, so the treatment's vocabulary cannot leak backwards into it.

Both prompts are stored verbatim in each arm's `run.generation_prompt`. A prompt reconstructed
from memory afterwards is recorded as `unknown`, and the arm is unpaired.

## Reviewing both arms

Each arm is a separate candidate and gets the full review path of `SCORING-RUN.md`: its own
inventory, its own packet, its own review, its own scoring attempt. In addition:

- **Reviewers are not told which arm they are reading.** Arm identity lives in the run metadata
  the operator fills in, not in the packet — the packet's field allowlist has no room for it.
- **Both arms are reviewed before either is scored**, so a reviewer cannot calibrate the second
  reading against the first arm's result.
- **The frozen ledger, policy and fact lists are the same for both.** Nothing about the
  comparison touches the answer key.

## What a paired result can and cannot say

It can say that two candidates, generated under recorded conditions differing in the skill,
scored a given recall and precision against an answer key frozen before either existed.

It cannot say that the difference generalizes beyond this device, this model, this budget and
this pair of runs; **n = 1 per arm**. It cannot establish the ledger is right — two blind readers
can share a wrong belief. It cannot establish that the model had not seen ENC28J60 material in
training, and the relationship between the generating model and the ledger's author models stays
recorded as whatever is actually known, which so far is `unknown`.

A single pair is a pilot observation. Reporting it as an effect size, or as evidence the skill
works, would be the same overreach the practice run refused when it declined to headline a
precision ratio of one.

## Before starting

1. `python3 corpus_check.py` — 0 drifted. A document that changed between arms makes them
   incomparable.
2. `uv run --with pyyaml python3 ledger_check.py ledger.yaml --lock ledger.lock` — 0 errors.
3. `uv run --with pyyaml python3 author_manifest.py --check author-manifest.yaml`.
4. Decide and write down, for both arms: the model, the budget, the tool set, the access profile,
   and whether the run is `practice` or `blind`. Record unknowns as `unknown`.
5. Decide who reviews, and whether they can be independent of the authors. If they cannot, say so
   in the report rather than in a footnote.
