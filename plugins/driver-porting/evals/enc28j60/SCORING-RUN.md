<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Stage A: scoring a reviewed candidate

`score.py` calculates the frozen policy's recall and precision from explicit reviewer judgments.
It does not infer correctness from prose. `strict_accept.py`, beside `spec_check.py`, applies
`enc28j60-documentary-1` to this pilot's validated records; legacy board verification records
continue to use their existing checker. This is documentary acceptance only. Implementation and
hardware validation remain blocked as **not evaluated**.

No candidate has been generated or scored as part of building this tool. Tests manufacture
judgments to check arithmetic and rejection paths; their accepted result is not a hardware claim.
Before the first candidate run, decide its generating model's relationship to the ledger authors
and whether the run is practice or a blind benchmark. Record both even when unknown. A blind
label is a process assertion, not something this tool can establish.

## Commands and retained attempts

Requires Python 3.9+ and PyYAML. From this directory:

```sh
uv run --with pyyaml python3 score.py template \
  --candidate <candidate.md> --output <review.json>
# Complete the review file, following the contract below.
uv run --with pyyaml python3 score.py score \
  --candidate <candidate.md> --review <review.json> --output <new-attempt-directory>
```

Use a new output directory for every attempt. The tool refuses an existing directory, including a
partially written one. It retains the candidate, review, ledger, lock, corpus manifest, policy,
fact lists, format, and scoring/checking/acceptance scripts, with digests in `result.json`.
Canonical JSON uses sorted keys, UTF-8, two-space indentation and a final newline. No latest-status
file replaces historical evidence. The run ID identifies the candidate generation; directories
identify distinct scoring attempts against it. Failed schema validation exits without a score;
a blocked or stale valid review is preserved as an attempt.

Exit codes: **0** documentary acceptance, **1** blocked or stale, **3** invalid/unavailable inputs
or output collision; argparse usage errors use **2**. Template creation returns 0 but confers no
acceptance. Null recall/precision means **n/a**, never zero or perfect. Numerator terms, exact
fractional partial credit, verdict counts, and atomic/composite counts accompany every recall
bucket. Recall divides by scoring rows, never by facts. Pending coverage earns no credit and
makes the review incomplete. The frozen policy's `precision` is `(all claims - errors) / all
claims`. When unresolved claims remain it is a provisional upper bound, not an assertion that
those claims are correct. `settled_precision` separately applies the repository's adjudication
rule, excluding `ADJUDICATE` and `PENDING` from binary scoring. Unsupported and partial claims
stay in both denominators. Both figures and their denominators are reported; neither changes
acceptance. Measurements stay `provisional` (or `stale`); `review_status` separately records
whether the review is complete. Completing a review does not validate the answer key.

A review binds all input bytes, including the tools and acceptance policy. Changed bytes produce
a stale decision; incompatible policy versions are refused outright. Candidate quotes that no
longer match fail validation. Editing a candidate requires a new template and a renewed review;
copying new hashes onto old judgments is not a review. The benchmark's own lock must still pass
the freeze gate. Nothing edits the frozen scoring policy or answer key.

For offline replay, execute the archived `score.py`, pass its archived `candidate.md` and
`review.json`, and use another new output directory. The numeric results and decisions reproduce;
timestamps differ. Python and PyYAML must remain available. The corpus manifest pins source
content but does not archive vendor PDFs or driver sources: reacquire them using `corpus_check.py`
before semantic re-review, and report unavailability honestly. Run the corpus pin check before a
real scored run as described in `README.md`; offline arithmetic does not establish upstream
availability or re-verify the reviewers' source readings.

## Review contract: `enc28j60-review-1`

The generated JSON is the schema template. Unknown fields and duplicate JSON keys are errors.
The template starts with all facts pending, no claims and incomplete gates, so it cannot pass.

- `inputs`: generated hashes and policy versions. Preserve them throughout this review.
- `run`: generation ID, `practice` or `blind`, model identity as exposed, relationship to ledger
  author models, generation prompt, skill revision, tool versions, budget, seed, timestamp,
  author alias and `public-only` access profile. Store the actual prompt in `generation_prompt`;
  unknown generation details are recorded as `unknown`, never invented. Use nonpersonal actor
  aliases. Record budget/cost and tool versions as text. No model family is inferred from an alias.
- `reviewers`: distinct reviewer aliases, excluding the candidate author. Distinct strings do not
  prove independent minds or independent evidence. The operator must establish that relationship.
- `audit`: a registered reviewer, boolean `complete`, and notes documenting the semantic inventory
  audit. The reviewer walks the entire candidate, registers every falsifiable proposition,
  deduplicates repetitions at their strongest statement, checks weight and requirement mappings,
  and checks that each fact judgment is supported. Mechanical quote checking cannot do this audit.
- `cleanroom`: registered reviewer, `PASS`, `FAIL` or `PENDING`, and notes recording applicable
  boundary checks and their findings. A pass is a review attestation, not a scanner invocation.
  Record why the selected authoring workflow satisfies the boundary. This gate cannot be waived
  by setting the access profile to public-only.
- `claims`: every candidate proposition, including ones with no ledger row, and ones about excluded
  rows. Each has `id`, strongest `proposition`, `weight`, `verdict`, `error`, `requirements`,
  candidate `evidence`, and `reviews`. Exact duplicate propositions are rejected; semantic
  duplicates are the audit's responsibility. A mapped claim inherits the highest mapped weight.
- `coverage`: exactly one entry for every active, in-scope, recoverable row, including observed
  behavior and implementation-choice probes. Excluded rows never enter coverage but remain
  available for claim mappings. Each entry holds its `id` and its ordered `facts` list.

Each evidence item has one-based inclusive `start`/`end` line numbers and an exact `quote` of
those lines (joined with LF, with CRLF normalized to LF for quote matching; archived bytes stay
unchanged). Include all repeated occurrences needed to establish the strongest
reading, especially contradictions. Each claim review has `reviewer`, `verdict`, `sources` and
`rationale`. Each source has `source` (an exact pin name accepted by `ledger_check.py`) and a
nonempty `locator`. Corpus-wide unsupported judgments still cite what was checked. References
cannot point to an arbitrary local file, URL, or private source; the pilot reads only the explicit
candidate, review and its local benchmark files and never follows source strings.

Claim verdicts preserve the verifier vocabulary:

| Verdict | Meaning in this adapter |
|---|---|
| `PASS` | Correct, including correctly conditional claims and attributed observations |
| `FAIL` | Contradicted content or an attribution error; `error` must name which |
| `GAP` | A registered factual proposition that is true but underspecified |
| `UNVERIFIABLE` | Unsupported by the corpus and not contradicted |
| `ADJUDICATE` | Unresolved readings, retained outside settled-only binary precision |
| `PENDING` | Not reviewed yet, retained outside settled-only binary precision |

This adapter is not a parser for legacy verifier Markdown. An author TODO without a factual
proposition is not a precision claim. Coverage records its omission independently. Non-FAIL claims
use `error: none`; FAIL uses `contradicted` or `attribution_error`. Settled verdicts require
at least one agreeing review, and conflicting reviews must remain `ADJUDICATE`. Resolve
disagreements in a new attempt after review; preserve earlier attempts. Every critical claim
needs two agreeing independent reviews for acceptance.

Each fact has `number`, `state`, `claims` and `notes`. Numbers must follow the frozen order in
`SCORING-FACTS.md`; an atomic row has one fact. Allowed states are `correct`, `underspecified`,
`contradicted`, `absent` and `pending`. Stated facts require notes and links to claims, and each
claim must map back to the requirement. A `correct` fact needs at least one linked `PASS` claim
or a claim whose only error is attribution; unsupported, underspecified or unresolved claims
alone cannot establish full content coverage. The audit still checks that all parts of a fact
are supported. Absent/pending facts have no claim links. A contradicted
fact must link a contradicted precision claim, and that claim cannot support any fact marked
non-contradicted. Grouped sets earn credit only as entire facts.
An inference's correct content with wrong attribution stays `correct` here while its claim is
`FAIL` with `attribution_error`. For conflicts, stating both readings is correct; choosing a side
is underspecified, and presenting it as settled is contradicted.

For implementation-choice probes, assess only the selected policy/value's asserted necessity,
under the frozen policy's alternatives rule. Omitting a choice is `absent`, incurs no recall loss
and creates no precision claim. Corpus silence about necessity means an unsupported claim, not a
contradiction. Independently valid constituent hardware requirements are scored at their owner
rows. Observed behavior and implementation-choice verdict counts are reported separately and
never folded into recall. All claims are still judged independently for precision.

## Strict policy and limits

The pilot conservatively treats all 162 eligible ledger rows as mandatory for documentary
acceptance. Every row must be covered, every critical claim must PASS with two reviewers, there
must be no known factual/attribution failures or unresolved claims, both audit and clean-room gates
must pass, all probe judgments must be complete, and input hashes must be current. Noncritical
unsupported/partial claims are reported but do not themselves block; a matching mandatory row's
partial coverage still blocks. A future capability-specific mandatory subset requires a new
acceptance policy, not a candidate-selected denominator.

The public-only restriction is an input-contract boundary: arbitrary source references and private
profiles are rejected, and the scorer never fetches those references. It does not isolate an
agent's generation environment or detect private information pasted into prose. Real generation
still requires environment access controls and the workflow's clean-room checks before content is
placed in a public output root. No boolean written by a model proves those controls existed.

The suite checks synthetic false acceptance/rejection cases and replay. It does not certify the
answer key, reviewer accuracy, physical hardware, or independence of reviewers. Model-generated
judgments remain provisional evidence even when mechanically valid.

## First follow-up

Before repeated scoring campaigns, put the frozen fact text beside each numbered disposition in
the generated review template. The current review uses the full companion `SCORING-FACTS.md`;
inline text would reduce fact-number alignment mistakes. Preserve the frozen lists and validate
any generated text against them rather than making the copied text another scoring authority.
