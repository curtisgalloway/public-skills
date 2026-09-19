<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Evaluating the driver-spec skills

How the driver-specification evaluation lands in this repository: what gets built, in what order,
and which of its measurements this plugin's existing machinery can and cannot make.

The evaluation itself asks one question — **does `cleanroom-spec` produce a hardware contract
precise and complete enough that a different implementer can write a working driver and meaningful
tests from it, without ever reading the original source?** Everything below is in service of
answering that with numbers rather than impressions.

## Terms

This document borrows vocabulary from three places. Definitions first, because a reader who has not
used these tools cannot follow the plan without them.

- **Gold ledger** — the answer key. A list of atomic hardware requirements for one device, each
  written down *before anyone looks at the specification being graded*, derived only from the
  adjudicated reference corpus. "Gold" means it is the standard the candidate is measured against,
  not that it is infallible.
- **Candidate spec** — the document under evaluation: what `cleanroom-spec` produced for that
  device on a given run.
- **Reference corpus** — the frozen set of sources the ledger is authored from: datasheets and
  errata at named editions, a driver at a pinned commit, standards documents. Frozen means every
  item is pinned by hash, commit or document edition so the same inputs can be reconstructed later.
- **Recall** — of the requirements in the gold ledger, what fraction does the candidate actually
  cover? This is the omission measure.
- **Precision** — of the claims the candidate makes, what fraction are correct and supported? This
  is the error measure. A document can score perfectly on one and badly on the other; they are
  reported separately, never averaged.
- **Ablation** — a comparison run with something removed, here the skill itself. The "without
  skill" arm is the baseline the "with skill" arm is measured against.
- **`claude plugin eval`** — the harness that runs a case against this plugin and against a
  no-plugin baseline and reports the difference. Cases live in `plugins/<plugin>/evals/<case>/`.
  See the "Behavioral evals" section of `AGENTS.md` at the repository root.
- **`cleanroom-spec`** — the skill that produces a clean-room driver spec. The thing being
  evaluated.
- **`spec-verifier`** — the skill that re-derives a spec's claims from the sources it cites and
  writes a verdict per claim into a record outside the spec. Not the thing being evaluated; a tool
  used by the evaluation.
- **Provenance tag** — the marker on each fact saying where it came from: `[databook]`,
  `[standard]`, `[DT]`, `[source-observed]`. Defined in `skills/board-expert/SPEC-FORMAT.md` and
  used by both spec kinds.
- **Adjudication** — a human decision resolving a conflict two readers could not settle between
  themselves. An adjudication item is not a pass and not a failure; it is a question waiting for a
  person.

## The measurement, in four steps

The order matters more than any individual step, because the independence of the answer key is what
makes the numbers mean anything.

1. **Author and freeze the gold ledger**, from the adjudicated reference corpus only, without
   seeing any generated specification. Each requirement gets a **stable ID that does not depend on
   any document's section structure** — neither the corpus's nor a candidate's. The ledger is
   frozen before step 2 begins.
2. **Generate the candidate specification.** This is the "with skill" arm; the baseline arm runs
   the same model, sources, tools and budget without the skill.
3. **Coverage, gold → candidate.** Walk the ledger. Every applicable, recoverable requirement must
   map to sufficient evidence in the candidate, or be scored missing or partial. **The weighted
   recall denominator is the frozen, in-scope ledger** — never the candidate's section list, and
   never its TODOs. A candidate that omits an entire section still incurs every omission in it.
4. **Claim verification, candidate → sources.** Check every factual claim the candidate makes,
   *including claims that have no ledger row*. An extra claim is not wrong for being extra, but it
   still needs support, and an unsupported one counts against precision.

Steps 3 and 4 run in opposite directions and measure different things. Collapsing them loses the
recall number entirely — see the next section for why.

## Why the answer key cannot come from the verifier

`spec-verifier` keys its claims to the candidate's own structure: for a clean-room spec,
`<Section>/<table>/<row name>` and `<Section>/<step number>`. A requirement the candidate never
states therefore never becomes a row, and never gets a verdict. Its `GAP` verdict does not close
the hole — `GAP` fires on a bullet whose author already wrote `TODO`, which is a disclosed gap, not
an undisclosed omission.

So `spec-verifier` answers "are the claims that are present correct?" It cannot answer "which
required claims are absent?" That makes it exactly right for step 4 and structurally unfit for
step 3.

This is a limitation of the mechanism, established by reading how it keys claims. The first
end-to-end run (2026-09-18, `pixel10` and `tensor-g5`, 87 claims, 10 FAIL) is consistent with it —
every failure was a wrong value, a wrong scope or an unlocatable citation, and none was an omission
— but a run finding no omissions does not by itself prove it cannot find them. The keying does.

**Sharing an independently authored ledger between the evaluator and the verifier is fine. Deriving
that ledger from the specification being evaluated is circular.** The two passes can eventually run
against one gold ledger without compromising independence; what must never happen is the answer key
being read off the answer.

## Build order

Step 3 as a separately reviewed evaluation and step 4 on the existing verifier is the initial
implementation. Extending `spec-verifier` to run both directions against one ledger is the intended
integration, and **ledger construction does not wait for it** — stable requirement IDs and an
explicit mapping are what make the later merge possible, and both are cheap to design now.

| Phase | What | Blocks on |
|---|---|---|
| 1 | Corpus manifest for the ENC28J60 pilot: driver and header hashes at v6.12, document editions and hashes, the edition-specific errata map | nothing |
| 2 | Gold ledger authored blind, with stable IDs; conflict log; second reviewer adjudicates | phase 1 |
| 3 | `claude plugin eval` case: with-skill and without-skill arms plus diagnostics | phase 1 |
| 4 | Coverage scoring (gold → candidate) as a reviewed manual pass | phases 2 and 3 |
| 5 | Claim verification (candidate → sources) via `spec-verifier` | phase 3 |
| 6 | Extend `spec-verifier` to score both directions against the ledger | phases 4 and 5, and a decision that it earns its cost |

The hardware purchase in the proposal's first action — two ENC28J60 modules, about $4 each — is a
user decision and is not assumed anywhere above. Phases 1 through 5 are all reachable without the
physical fixture; what the fixture adds is execution evidence for the boundary and recovery checks,
and its absence is recorded test by test rather than papered over.

## Three changes this requires in the existing skills

Each is a change to shipped text, listed with what it breaks if left alone.

### 1. A verifier disagreement is an adjudication item, not a failure

`skills/spec-verifier/SKILL.md` currently says, of the two-verifier rule, that "a disagreement is a
`FAIL` with both readings recorded until a person resolves it."

That conflates two different things. A disagreement means the two readers could not settle the
question between them; it does not establish that the specification is wrong. Correct handling:
record both readings, mark the claim an **adjudication item**, and **exclude it from binary
scoring** while reporting it separately. If adjudication then shows the specification stated
something more definitely than its evidence supports, *that* counts against precision — but on the
merits, not on the disagreement.

Left alone, every unresolved reading disagreement inflates the failure count and depresses
precision for a reason that has nothing to do with the document's quality.

Already affected: `specs/resources/tensor-g5.verify.md`, Quick-facts/1, where two verifiers read
the production device tree's bus structure differently and the claim was recorded FAIL under the
current rule. It is an adjudication item.

### 2. An explicit `[inference]` provenance tag

The evaluation labels every ledger row as one of: documented hardware requirement, observed
software behavior, inference, implementation choice, or unresolved conflict. Four of the five have
homes in the existing tag set — `[databook]` and `[standard]`, `[source-observed]`, the target-OS
mapping section, and (once change 1 lands) an adjudication item.

**Inference has no home.** Nothing currently distinguishes "the hardware requires this" from "the
driver does this, and I concluded the hardware requires it." That distinction is the whole substance
of the proposal's first correction: `FEC_QUIRK_ERR006358` is set in one table and never tested,
while the recovery path runs unconditionally, so a reader who grades the flag table instead of the
control flow reaches a confident wrong answer. Without an inference tag there is nowhere to record
that a claim was reasoned rather than read.

An `[inference]` fact should carry: its **premises** (what was actually observed), the
**derivation** (why the conclusion follows), a **confidence**, and a **verification method** (what
would settle it — usually hardware). This is strictly more than the other tags carry, because an
inference is the one class whose support is an argument rather than a citation.

### 3. Recall needs a denominator the candidate cannot influence

No existing script computes recall, because nothing in the repository holds a requirement list
independent of a spec. The ledger format is therefore new work, and its first constraint is that
its IDs are assigned from the corpus, not from any document's headings — otherwise a candidate that
reorganizes its sections changes its own denominator.

## Where the proposal's other corrections land

- **Correction 1 — grade the control flow, not the flag table.** Already expressible:
  `cleanroom-spec`'s required structure marks `[source-observed]` orderings "order not known to be
  required" and `[source-observed]` constants "re-derive on hardware". The FEC erratum-to-code
  pairs become register-map and init-sequence content once the target SoC is frozen. This is the
  sharpest probe in the benchmark and should be scored explicitly rather than folded into a general
  precision number.
- **Correction 2 — absence from a vendor document does not prove the device unaffected.** Three
  separate applicability columns (vendor-confirmed, implementation-observed, unresolved) in the
  ledger. Unresolved never scores as a proven contradiction.
- **Correction 3 — related IP is not an interchangeable reference.** Matches the rule that a spec
  may not silently compose another part's facts; anything borrowed across parts needs a reviewed
  equivalence argument per behavior.
- **Correction 4 — an erratum scoped to one part number.** Shared device IDs make a software
  workaround apply more broadly than the hardware requirement does. This is precisely an
  `[inference]` versus `[databook]` distinction, and unrecordable until change 2 lands.
- **Correction 5 — edition-specific errata identifiers.** Belongs in the corpus manifest: every
  errata reference carries its document edition, and a comment's bare issue number is recorded
  literally rather than resolved against an assumed edition.

## Deferred, and deliberately so

The FEC target SoC and revision are chosen only once the matching reference manual, errata edition
and a demonstrated network setup are in hand — i.MX6Q first in the qualification order, then
i.MX8M Mini. Nothing above depends on that choice; the ENC28J60 pilot exists to calibrate the
ledger, the scoring and the test quality before the harder target is touched.

The pilot is a method check, not evidence about complex SoC drivers. Any claim about how the skill
performs on those waits for the main benchmark.
