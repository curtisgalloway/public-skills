<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Review of VALIDATION-PROPOSAL.md

Status: review for discussion, 2026-09-19. Reviewer: Claude Fable 5.1 in Claude Code, working
from the repository at `315b12b` plus the untracked proposal. Every claim about existing behavior
below was checked against the file it names; nothing was taken from the proposal's own description
of the machinery.

Revised the same day after a consultation with the proposal's author (Codex CLI 0.155.1, through
the `consult` skill). Paragraphs marked *revised* changed as a result; section 8 records what the
author corrected and where the two of us landed.

## Terms

- **Proposal** — `VALIDATION-PROPOSAL.md`, the document under review.
- **Ledger** — the answer key for one device: atomic hardware requirements with stable IDs,
  authored from the frozen corpus before any generated spec is read. Format in
  `evals/enc28j60/LEDGER-FORMAT.md`. Not yet written for any device.
- **Verification record** — the per-spec file of claim verdicts that `spec-verifier` writes in a
  `resources/` directory beside the spec.
- **Checker** — `board-expert/scripts/spec_check.py`, the mechanical gate on specs and records.
- **Expected outcome** — what a test asserts. The proposal calls this an "oracle"; this review does
  not, and recommends the proposal stop too (edit 6).
- **Strict acceptance** — the proposal's three-dimension policy (spec ready, implementation
  validated, hardware validated), as distinct from today's rule of zero `FAIL`.

## 1. Verdict

The direction is right and most of the individual rules are ones this plugin has already learned
the hard way. Three things need to change before the proposal is a plan:

1. **Its foundation is unbuilt.** Every stage depends on the ENC28J60 ledger, which
   `evals/enc28j60/README.md` says is not written. The proposal's stage A builds tooling against a
   ledger that does not exist. Write the ledger first (EVAL-PLAN phase 2), then build the smallest
   tool that scores against it.
2. **It is larger than the evidence supports.** Seven schema types, two new skills, six stages, and
   a whole vendor workstream, proposed before one device has been scored once. Half of the gaps it
   names can be closed by editing existing files (section 2). Stages E and F should be a second
   proposal written after stage D has produced a number.
3. **Two of its six gaps are overstated** (section 2, gaps 3 and 6), and section 7 contradicts the
   shipped vendor guide on what may leave a private root (section 4, scenario E).

Recommendation: accept the contracts in sections 4 and 5 of the proposal in principle, cut the
delivery to ENC28J60 stages B, A, C, D in that order, and hold the rest until there is a score.

## 2. The six gaps, checked against the code

| Gap | Verdict | Evidence |
|---|---|---|
| 1. Verifier claim IDs follow document structure | Confirmed, and already documented | `spec-verifier/SKILL.md` keys board claims as `<Section>/<ordinal>` (line 145), anchored claims by anchor text (194), clean-room claims as `<Section>/<table>/<row>` (226). `EVAL-PLAN.md` § "Why the answer key cannot come from the verifier" says exactly this. The proposal restates a known limitation as a discovery. |
| 2. Missing or stale record is a warning; zero `FAIL` coexists with unresolved critical claims | Confirmed | `spec_check.py`: no record or stale hash is a warning unless `--require-verified` (docstring lines 57 to 65, code line 821); only `summary.fail != 0` is an error (899). `unverifiable` and `adjudicate` never gate. A record reading `{pass: 0, fail: 0, unverifiable: 47}` passes the checker today. |
| 3. No bounded automatic resolution workflow | Confirmed for accuracy repair (*revised*) | `cleanroom-spec/SKILL.md` line 178 bounds repair at two FAILs per section, but that verifier checks the clean-room wall, not accuracy (`spec-verifier` lines 207 to 213 say so). Accuracy repair is unbounded for every kind: `spec-verifier` line 137, "after a fix, run again; the loop ends at zero FAIL." Agreed wording for the proposal: "Clean-room boundary repair already stops after two failures on the same section. Accuracy verification lacks a consistent bounded repair workflow across spec kinds; structured expert feedback is also absent." |
| 4. No contract linking requirements to tests and evidence | Confirmed | Nothing in the repository links a test to a requirement ID. `LEDGER-FORMAT.md` § "What this format cannot do" already concedes this. |
| 5. Overlay precedence cannot settle facts or publication | Confirmed | `VENDOR-GUIDE.md` line 21: "Later layers win on conflicting scalars." Line 55: two overlays in one layer produce a warning and an undefined order. Nothing distinguishes a configuration override from a factual contradiction. |
| 6. Verification records are overwritten; no longitudinal record | Partly overstated (*revised*) | `spec-verifier` step 7 says "replacing any earlier record," and `git log` shows seven verification rounds for `pixel10` and `tensor-g5` between `3a1a2ad` and `8313d9c`. But seven rounds is not seven archived attempts: `tensor-g5.verify.md` line 6 says the current record consolidates rounds 5 to 7, and `spec-verifier` line 241 makes committing conditional on the project. Agreed wording: "Git preserves committed verification snapshots. Validation must additionally identify and retain every attempt, its input revisions, scope, verdicts, and evidence references. A later attempt must not replace an earlier attempt's evidence." Git is an acceptable backend when the workflow keeps every attempt. |

Net: gaps 2, 3, 4, 5 and 6 justify new rules and checks, though small ones. Gap 1 is already
documented and the proposal acknowledges it (its lines 43 to 46).

**One more checker finding, found by the author during the consultation.** In `spec_check.py`
the stale-hash check returns at line 896, before the nonzero-`fail` check at line 899. A stale
record that also carries failures therefore produces only the stale warning, and the checker
exits 0 without `--require-verified`. That is a bug independent of the proposal and should be
fixed in the checker now.

## 3. What can ship this week without any new schema

These close real gaps and none of them needs a claim ID, a manifest, or a new skill.

1. **Strict mode in the checker** (*revised*). `--require-verified` already exists. Add `--strict`
   that implies it and also errors when a bring-up-critical claim is `UNVERIFIABLE` or
   `ADJUDICATE`. The critical set for now is the one `spec-verifier` already names for two-verifier
   treatment (lines 159 to 161: addressing model, boot chain and entry state, debug UART, debug
   console). That set is a minimum for board bring-up, not the definition of critical; a DMA or
   reset claim can be critical to a capability without being on it, and the ledger's
   consequence-based `weight` is the general rule. One cost: the checker reads only the record's
   frontmatter (its line 817), so this needs a parser for the body's `<key>: <VERDICT>` lines, a
   reliable mapping from those keys to the critical set, and a check that every expected critical
   claim is present, since parsing the verdicts that exist says nothing about the ones that do not.
   Small, but not zero.
2. **The repair bound for every kind.** Copy `cleanroom-spec`'s two-FAILs rule into `spec-verifier`
   step 8, so the unbounded "run again until zero" loop ends the same way for board and anchored
   specs. The commit history is the argument: the fifth and sixth passes on `tensor-g5` found
   failures inside the previous pass's fixes (`7e7d9c2`, `a27ec94`).
3. **A run block in the record frontmatter.** Replace the free-text `verifier:` line with a mapping:
   model identifier as exposed, harness, skill file hashes, budget, timestamps, and any seed. Git
   keeps the history; the block makes each historical record comparable. This is the proposal's
   run manifest, minus the directory tree.
4. **The ledger.** EVAL-PLAN phase 2. Nothing in the proposal is measurable until it exists, and its
   authoring rule (blind, from `corpus.yaml` only) means it gets harder to author every time a
   candidate spec is generated and read.

## 4. Concrete failure scenarios

The proposal asked for these. Each names what breaks, and what exposes it.

**A. Spec and test share a false assumption (question 1).** The reference driver clears an
interrupt flag before reading the packet count. The ledger author, reading the driver under the
corpus, records it as `observed-software-behavior`; the candidate spec states it as a requirement;
the test author, working from the accepted spec, asserts the ordering. Hardware tolerates either
order. Every check is green and the spec is wrong about the hardware. The ledger's class field
only helps if the author classified it right, and both authors read the same driver.
*Exposure* (*revised*): the mutation "remove the requirement from the implementation, rerun the
hardware test." If the test still passes, that shows the test cannot distinguish the two orderings
under the tested conditions. It is a finding about the test, not proof that the hardware never
requires the ordering, which may depend on revision, timing, or load. Documentary evidence can
also expose the unjustified requirement, and `spec-verifier` line 214 already fails a
`[source-observed]` ordering stated without its "order not known to be required" marker. What
remains is correlated verifier error, and only an external observation under stated conditions
closes it. A second exposure is the errata-renumbering trap `corpus.yaml` already records: a ledger
row and a spec claim can both cite "issue 12" and mean different silicon, and agree with each
other.

**B. `UNVERIFIABLE` laundering (question 2).** Under today's checker a record with every critical
claim `UNVERIFIABLE` passes. Under the proposal's strict policy the same record blocks. Neither is
right for an NDA platform where the debug UART's clock source is in a document the public run
cannot open. *Exposure:* run the strict policy against `tensor-g5.verify.md` with one critical claim
flipped to `UNVERIFIABLE (NDA)` and see what it blocks. If the answer is "everything," the
capability graph needs the evidence channel (serial console) as a prerequisite with its own
disposition, separate from the peripherals it reports on. Withholding strict acceptance for the
UART capability itself is correct; the failure is the propagation. (*revised*) Agreed rule:
"Evidence channels have run-scoped fitness dispositions separate from strict acceptance of the
hardware capability that implements them. A channel is usable for a named observation only when
its predefined checks establish the identity, freshness, integrity, and completeness needed for
that observation. Readable output alone is insufficient. An unresolved claim about the channel's
hardware implementation blocks dependent observations only when it undermines those checks or
their evidentiary assumptions." Channel dispositions: `usable`, `inconclusive`, `unavailable`,
with the observation scope recorded. A UART can hold both roles at once, and qualifying it as a
channel does not accept it as a capability.

**C. Platform-wide blocker from one source limitation (question 2).** Same shape as B, from the
other side. The proposal says documentary checks may substitute for physical tests when the
obligation is set before execution. Set it where? If it is set per run, every run re-litigates it.
*Proposed:* a `validation:` field on the ledger row (`physical`, `documentary`, `either`), authored
blind with the row. The proposal's claim mapping then inherits it.

**D. Stale-record laundering.** A spec is edited after verification. Today: a warning. The record's
`spec_sha256` is the only thing that catches it, and only when the checker runs. *Exposure:* edit
one byte of `pixel10.spec.md` and run the checker without `--require-verified`; it exits 0. Fix is
item 1 in section 3.

**E. Disclosure through a test expectation (question 3).** A public test for a vendor board asserts
a register reset value that appears only in an NDA databook. The test file is public; the value is
now published. The proposal's rule ("a public claim requires independent public support") covers
this. `VENDOR-GUIDE.md` § 5 says "May leave: hardware facts, addresses, sequences, and mechanism
prose, each cited to the internal document," and its one-way rule (line 112) forbids copying any
of that into a public spec. (*revised*) That is not a contradiction: the guide's classification
rule gives some protection to every artifact, but it does not explicitly extend its one-way rule
to tests, logs, or other derived artifacts. It is an omission. Agreed fix,
in the guide: "'May leave' means transfer into a report within the authorized private workflow,
subject to the source's restrictions. It does not authorize public disclosure. Reports, tests, logs,
and other derived artifacts retain those restrictions."

**F. Answer-key drift (question 7).** Expert feedback adds a row to the ledger. Old candidates are
rescored against the new revision and their recall drops. That is correct, and it will look like a
regression in the model. *Exposure:* the report must carry both scores, against the ledger revision
the run was frozen with and against current. The proposal says "rescore preserved old candidates"
but not "report both."

**G. Test-oriented drift.** The proposal's "test implementers cannot silently change the expected
outcome" has no enforcement named. *Exposure:* a hash of the validation contract in the run
manifest, checked at scoring. Cheap, and the same mechanism as `spec_sha256`.

## 5. Answers to the seven review questions

1. **Shared false assumption.** Yes, scenario A. The ledger's class field narrows it; only a
   hardware mutation closes it.
2. **Strict policy without platform-wide blocking.** Not as written. Scenarios B and C. The
   capability graph must distinguish evidence channels from capabilities under test, with the
   channel rule quoted in scenario B, and the validation obligation must be a versioned ledger
   field. The proposal already places obligations on ledger rows (its lines 145 to 147); make them
   explicit, and allow "both" where a documentary check and a physical test are each required.
3. **Disclosure.** Prose, reports, and test expectations are covered by section 7's rules, but the
   rules contradict the shipped vendor guide (scenario E). Logs and shared model contexts are named
   but not addressed; `cleanroom-spec` already has the enforcement pattern (`CLEANROOM_ROLE` in the
   environment, line 247) and the proposal should reuse it for a `public-only` role rather than
   describe a new one.
4. **Two new skills.** Not yet. `hardware-validation` is schemas plus one deterministic script; the
   script belongs beside `spec_check.py` and the schemas beside the ledger. `hardware-spec-eval` is
   EVAL-PLAN phases 2 to 6, which already have a home under `evals/enc28j60/`. Mint the skills when
   a second device needs the same machinery and the duplication is visible.
5. **Smallest real Fuchsia slice.** Not answerable from this repository. The Fuchsia bench and
   boot-test skills live in another package, and no board spec here has a bench declared for it.
   The proposal should name the board, the image, and the peripheral before stage D is scheduled.
   (*revised*) Host-captured serial is independent capture, not independent evidence: a target
   printing `PASS` into the capture is still the target's assertion. The verdict has to come from
   something the host observed itself, such as traffic on a peer interface, a loopback the host
   drives, or an instrument reading.
6. **Which feedback suspends acceptance.** A review merged through a pull request, targeting a
   `critical`-weight row or claim, with either a reproduction or a located authority. Anything else
   becomes an `ADJUDICATE` item, which already exists and already blocks nothing. (*revised*)
   Authority comes from the repository's authorization controls (protected branch, required
   reviewers), not from the commit's author field, which anyone can set.
7. **Genuine improvement versus drift.** The proposal has the pieces (frozen campaigns, immutable
   evidence, separate reporting) but scenario F shows one gap: report against both ledger
   revisions. Selective retries are handled by "a later pass does not erase an earlier failure."
   Changed hardware is handled by the run manifest's fixture identity.

## 6. Proposed edits to the proposal

All eight were discussed with the author; the wording below is what both of us accept.

1. **Section 2, gap 3:** use the agreed wording from section 2 above. Keep the distinction between
   two failed checks and two repair-and-reverify rounds.
2. **Section 2, gap 6:** use the agreed wording from section 2 above. The `runs/<run-id>/` tree in
   section 4 becomes illustrative; the requirement is that every attempt and its inputs are kept,
   not the directory shape. The rule that reconciles this with today's replaceable record, agreed
   with the author: "Preserve each verification attempt and its input revisions, verification
   scope, verdicts, and evidence references before updating the replaceable latest-status record.
   The latest-status record identifies the attempt or attempts supporting its verdicts.
   Carried-forward verdicts retain their originating attempt and applicability to the current
   revision." Attempt files beside the record or retained commits both satisfy it; a git tag alone
   does not, since tags move and delete.
3. **Section 3:** for the pilot, put evaluation material under `evals/`, extend `spec-verifier` and
   `board-expert/scripts` in place, and keep the interface versioning sentence. Mint the two skills
   when a second device shows the reuse. This is packaging restraint, not removal of the
   responsibilities.
4. **Section 5, acceptance table:** the two-verifier set in `spec-verifier` is the minimum board
   bring-up set; criticality in general follows the ledger's consequence-based `weight`. Note that a
   selective strict check needs per-claim machine-readable dispositions or a record-body parser.
5. **Section 7 and `VENDOR-GUIDE.md` § 5:** add the agreed clarifying text (section 4, scenario E)
   to the guide, and have the proposal cite it rather than restate it.
6. **Throughout:** replace "oracle" (seven uses) with "expected outcome," or "expected outcome and
   decision rule" where tolerance and pass/fail logic matter; add a Terms block. The proposal leans
   on ledger, overlay, envelope, adjudication, and capability graph without defining them, and
   `EVAL-PLAN.md` sets the house pattern.
7. **Section 10:** deliver B, A, C, D with the ledger frozen before A. Defer the full vendor
   workflow, feedback automation, campaign infrastructure, and optimized dependency replay. The
   pilot keeps frozen input hashes, preserved attempts, explicit score versions, conservative
   invalidation, and freshness checks, because those cannot be reconstructed after the first score.
   The pilot is public-only. Stage D is two deliverables (ENC28J60 physical, Fuchsia UART) with
   separate gates.
8. **Title:** "Evidence-driven hardware specification validation: ENC28J60 pilot." Fuchsia
   integration becomes a separately gated follow-on that must name a board, image, peripheral,
   fixture, and external observation method. The proposal's Fuchsia content is in section 3,
   section 9, and stage D, not one paragraph as this review first said.

## 7. Unresolved design choices for discussion

- **Claim IDs for board and SoC specs.** The ledger's `ENC28J60-<FACET>-<NNN>` scheme has a facet
  vocabulary for one device class. What are the facets for an SoC (`IRQ`, `CLK`, `MEM`, `BOOT`?),
  and who mints them: the spec author, the ledger author, or the scaffold?
- **Where the acceptance policy lives.** Per platform manifest, per repository, or in the checker's
  defaults. The proposal's frozen campaign already requires one scoring policy across compared runs
  (its line 318); what is missing is a check that refuses a comparison across policy versions.
- **Record format compatibility.** Adding a run block and per-claim IDs to the verification record
  changes a format `spec_check.py` validates. Sidecar or in-place migration. The agreed attempt
  rule (edit 2) keeps the latest record replaceable, so the reader is unaffected either way.
- **Enforcement for public-only runs.** The proposal names controlled mounts and tool and network
  access (its line 272) but no implementation. `cleanroom-spec` line 237 already ranks the layers:
  environment restrictions first, then hooks, then instructions. An environment role alone is not
  enough; the public-only profile needs the same three layers.
- **Hardware for stage D.** The ENC28J60 modules were ordered 2026-09-19 (EVAL-PLAN). Nothing in
  the proposal says what host drives them, and the SPI host is itself a device under test. Every
  shipped board spec declares `tools: []`, so no bench exists in the repository for any board.

## 8. Consultation record

The proposal's author was consulted through the `consult` skill (Codex CLI 0.155.1, read-only
sandbox, one assessment, one comparison round, one confirmation). Transcript in the helper's
state directory under the user's home, not in this repository.

What the author corrected in this review, each checked against the file before it was accepted:

- The clean-room two-FAIL bound covers the wall, not accuracy (gap 3).
- Seven verification rounds are not seven archived attempts; the Tensor G5 record consolidates
  rounds 5 to 7 (gap 6).
- The checker returns on a stale hash before it checks the failure count (section 2, new finding).
- The strict check needs a record-body parser, a mapping to the critical set, and missing-claim
  detection (section 3, item 1).
- Scenario A's mutation inference was invalid as first written.
- Scenario E is an omission in the vendor guide, not a contradiction.
- Host-captured serial is independent capture, not independent evidence (question 5).
- Commit authorship is not authorization (question 6).
- The proposal's Fuchsia content is in three places, not one (edit 8).

What the author accepted from this review: the delivery order B, A, C, D with the ledger frozen
first; holding the two new skills; the "latest record replaceable, attempts append-only" rule; the
distinction between evidence channels and capabilities under test, with the author's stricter
wording for when a channel is usable; the title; the Terms block; replacing "oracle."

Outcome: consensus. The author explicitly agreed to the joint recommendation below with no
remaining objections, noting that agreement authorizes neither implementation nor a paid campaign.

### Joint recommendation, as confirmed

1. **Delivery.** Stages B, A, C, D in that order. The ENC28J60 ledger is authored blind and frozen
   before stage A begins. The pilot is public-only and retains frozen input hashes, preserved
   attempts, explicit score versions, conservative invalidation, and freshness checks. Stages E
   and F are deferred to a follow-on proposal written after the first score exists. The two new
   skills are not created now; evaluation material goes under `evals/`, and `spec-verifier` and
   `board-expert/scripts` are extended in place with versioned interfaces. Stage D is two
   separately gated deliverables: ENC28J60 physical validation when its fixture is established,
   and a Fuchsia UART slice that must first name a board, image, peripheral, fixture, and external
   observation method.
2. **Text changes to the proposal.** Edits 1 to 8 in section 6 above, plus: an explicit check that
   refuses comparison across acceptance or scoring policy versions; scores after a ledger revision
   reported against both the frozen and the current revision, with candidate-informed corrections
   labeled; the validation contract's digest recorded in the run manifest, with a change requiring
   renewed review.
3. **Checker work, independent of the proposal.** Fix the stale-before-fail ordering in
   `spec_check.py`. Add `--strict`, implying `--require-verified`, that errors when a critical claim
   is `UNVERIFIABLE` or `ADJUDICATE`, with a record-body parser, a mapping to the critical set, and
   missing-claim detection.
4. **Corrections to this review.** Applied, and listed at the top of this section.
