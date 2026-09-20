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
# Build the packet first; see "Preparing a review" below.
uv run --with pyyaml python3 score.py template \
  --candidate <candidate.md> --packet <packet.json> --output <review.json>
# Complete the review file, following the contract below.
uv run --with pyyaml python3 score.py score \
  --candidate <candidate.md> --review <review.json> --packet <packet.json> \
  --inventory <inventory.json> --output <new-attempt-directory>
```

Use a new output directory for every attempt. The tool refuses an existing directory, including a
partially written one. It retains the candidate, review, packet, inventory, ledger, lock, corpus
manifest, policy, fact lists, format, and the preparation/scoring/checking/acceptance scripts,
with digests in `result.json`.
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

## Preparing a review

`prepare.py` builds what the accuracy readers are given. The first practice run failed its
independence check here rather than in scoring: a hand-assembled revision file carried one
reader's verdict summaries into the second reader's packet, and the claim inventory was still
being segmented while the review ran. Both are now mechanical gates.

```sh
uv run --with pyyaml python3 prepare.py sources                      # the citable pin names
uv run --with pyyaml python3 prepare.py inventory \
  --candidate <candidate.md> --inventory <inventory.json>            # settle before review
uv run --with pyyaml python3 prepare.py packet \
  --candidate <candidate.md> --inventory <inventory.json> --output <packet.json>
```

The inventory (`enc28j60-inventory-2`) is the reviewed proposition list: per record `id`,
`proposition`, `weight`, `requirements`, candidate `evidence`, `status` (`active` or `retired`),
`supersedes`, `segmentation` and `notes`, plus a top-level `allowances` list. `inventory` refuses
one that does not describe this candidate, whose quotes do not match its lines, that repeats a
proposition, that cites an unknown row, or whose retirement links do not reach an active record;
it *warns* where a proposition reads as more than one assertion or a retirement leaves assertions
behind. A warning is an unanswered segmentation question, so `packet` refuses to build from one.

A compound warning clears when the record carries a `segmentation` disposition: a written reason
and the digest of the proposition it was written against. That is an **attestation that a person
looked**, not a mechanical finding that the segmentation is right, and rewording the proposition
invalidates it — the digest stops a reason from silently carrying forward onto text nobody
reviewed. The detector is a deliberately loose regex; tightening it would buy cosmetic rewording
rather than segmentation, and semantic overlap and completeness remain the audit's job.

Retirement links are flat: a retired record must be named by an **active** replacement. That
rejects a self-link and every cycle, since a cycle needs a retired record to do the superseding,
and it means later generations flatten their links onto the record that is live now rather than
chaining through intermediate retirements.

`packet` copies an explicit field allowlist — `id`, `proposition`, `weight`, `requirements`,
`evidence` — out of each active record. It builds by copying named fields, never by deleting
fields, so anything added to the inventory later is absent from the packet until someone adds it
here deliberately. Notes, status, retirement links and segmentation dispositions never reach a
reviewer.

The copied text is then scanned for judgment vocabulary (`PASS`, `FAIL`, `GAP`, `UNVERIFIABLE`,
`ADJUDICATE`, `PENDING`, and phrases like "first reader" or "verdict"), and a hit refuses the
packet. **This is a lint, not a proof of neutrality**: it catches the shape the practice run's
leak actually had, and an operator who paraphrases a verdict defeats it. Where one record
genuinely uses such a word, the inventory carries an allowance naming the record, the field, the
token and the reason. An allowance is scoped: a candidate that says `PASS` in one diagnostic
example does not license the word on an unrelated proposition, which is where a leaked outcome
would sit. The reason stays in the inventory — a justification reading "allowed because the first
reader marked this correct" would recreate the leak — and only `record.field:token` appears in
the packet.

### What binding the packet does and does not establish

`score.py` takes the packet and the inventory it was built from. It refuses a review whose claims
are not exactly the packet's active records, field for field, so a proposition discovered during
review needs a new inventory, a new packet and a retained new attempt rather than an edit to the
list a reader already answered. Each reviewer names the packet digest its instructions carried,
because a digest recorded once for the whole review cannot tell this round's answer from one
imported out of the last. The inventory is re-audited at scoring time and archived, so its
segmentation dispositions survive with the attempt instead of being named by a digest of bytes
nobody kept.

That is correspondence, not testimony. It establishes which propositions were judged and that
one artifact was built from another. **It does not establish that the readers saw only the
packet**, that their contexts were isolated, or that they are independent minds. Those remain
operator responsibilities that no artifact in this directory can check.

## What a review may cite

The review contract accepts exactly the pin names `corpus.yaml` declares: a data sheet or errata
edition id, a pinned driver path, or the driver commit. `prepare.py sources` prints them, and
`--check <names.json>` judges a proposed list and says what to cite instead.

A repository alias (`linux`) is not a source: cite the pinned path or commit.

**`corpus.yaml` is citable for a proposition about the manifest's own contents, and for nothing
else.** The distinction is the proposition's meaning, not a label an operator picks:

- "this benchmark pins DS39662E", "the manifest maps issue 12 of edition B to issue 14 of edition
  C" — the manifest is the evidence, with a manifest key as the locator.
- "these silicon revisions are affected" — a claim about the device. It cites the errata edition
  and locates the table, whatever the reviewer happened to read it in.

A claim whose reviews cite *only* the manifest therefore earns **no coverage credit**: the scorer
refuses it as evidence for any fact. It is still judged for precision like every other claim,
because the frozen policy evaluates every claim the candidate makes, and dropping a class of
claims after seeing a candidate would change a denominator that was fixed before it existed.

The reason a hardware claim may not rest on the manifest is derivative evidence, not a missing
freeze — the lock does pin `corpus.yaml`'s bytes. The manifest transcribes pages, and a
transcription can carry the reading error its source did not: the affected-revision correction in
`README.md` → "Input history" is the worked example, caught only because a reader went back to
the rendered table. Crediting the transcription would let it stand in for the reading the ledger
was authored from.

**An unreachable document leaves a claim `PENDING`.** It does not make it `UNVERIFIABLE`, which
means the corpus does not support it — a failure to look establishes neither support nor its
absence, and noncritical unsupported claims do not block acceptance while pending ones do. Record
the access failure in the rationale, keep any earlier valid evidence, and reacquire the document
with `corpus_check.py`. Never re-cite an edition you did not read.

## Review contract: `enc28j60-review-2`

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

Each fact has `number`, `text`, `state`, `claims` and `notes`. `text` is the frozen wording of that numbered fact, written by the template and re-derived from `SCORING-FACTS.md` when scoring: an edited copy is refused, so the text beside a judgment is never a second scoring authority. Numbers must follow the frozen order in
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

## Schema history

`enc28j60-review-3` adds the frozen wording of what is being judged, and the binding to what the
reviewers were given:

- every fact carries `text`, the frozen wording of that numbered fact, and every composite row
  carries `context`, the unit-level prose beside its list. The prose is not decoration:
  `SCORING-FACTS.md` assigns requirements in sentences as well as in entries, so INIT-015's two
  MABBIPG values carry an IEEE minimum gap that only the sentence below them names. Copying the
  entries alone would hand a reviewer a weaker obligation than the frozen one. Both strings are
  re-derived from the frozen file when scoring and a review whose copy differs is refused, so the
  wording stays informative without becoming a second authority. An atomic row's single fact
  takes the row's statement and carries no context. The general conventions — what `[pair]` and
  `[grouped set]` mean — stay in `SCORING-FACTS.md`, which a reviewer still reads.
- `preparation` records the packet and inventory digests and, per reviewer, the packet that
  reviewer answered.

Reviews written against an earlier schema are refused rather than migrated: a template is cheap
and copying old judgments onto a new schema is not a review. Attempts already archived keep their
own copy of the scorer and replay unchanged. The scoring policy, the answer key and every frozen
document are untouched by this change; `enc28j60-1.4` still binds them.
