<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Evidence-driven hardware specification validation: ENC28J60 pilot

Status: revised after review, 2026-09-19. No implementation is authorized by this document.

## Terms

Definitions first, so a reader who has not used these tools can follow the proposal.

- **Ledger:** the answer key, atomic hardware requirements authored from frozen sources before
  reading a candidate.
- **Candidate:** the generated specification being evaluated.
- **Reference corpus:** the source documents and code, pinned to known editions and revisions, used
  to author the ledger.
- **Verification record:** the file of claim verdicts that `spec-verifier` writes beside a spec; its
  latest status is replaceable.
- **Checker:** `board-expert/scripts/spec_check.py`, the program that checks specs and verification
  records.
- **Overlay:** a file that adds facts or configuration to a baseline spec without copying it.
- **Layer:** an overlay's position in configuration merge order, not a confidentiality label.
- **Adjudication:** a human decision resolving conflicting readings; an adjudication item awaits
  that decision.
- **Capability graph:** a map of hardware functions and the prerequisites each depends on.
- **Evidence channel:** a means of collecting an observation, such as a serial connection or network
  peer.
- **Test envelope:** the allowed hardware configuration, operations, rates, duration, and other
  limits of a test.
- **Attempt:** one identified verification or execution try, with preserved inputs, scope, verdicts,
  and evidence references.
- **Strict acceptance:** the policy that separately decides whether a spec is ready, an
  implementation is validated, and hardware is validated.
- **Validation contract:** the reviewed test requirements, expected outcome and decision rule,
  setup, observations, and limits.
- **Disposition:** a recorded status and reason, scoped to the claim, capability, or observation it
  concerns.
- **Applicability:** the hardware revisions and operating conditions for which a requirement or
  verdict holds.
- **Provenance:** where a claim or artifact came from and the evidence supporting it.
- **Digest:** a content hash used to detect changes; it neither preserves the content nor grants
  access to it.
- **Precision:** the fraction of candidate claims that are correct and supported.
- **Recall:** the fraction of ledger requirements the candidate covers, measured separately from
  precision.
- **Fixture:** the connected equipment and configuration used to exercise and observe the hardware.
- **Mutation:** a deliberate fault or change used to check whether a test can detect it.
- **SoC / IP:** a system on a chip / a reusable hardware block, such as a peripheral controller.

## 1. Outcome and scope

Calibrate evidence-driven specification validation on the public-only ENC28J60 pilot: an independent
ledger, scored candidate specs, executable tests, and preserved evidence of what is established and
what remains unknown. Routine acceptance should not require reading generated specs. Experts can
challenge requirements, tests, and verdicts through recorded reviews.

Validation is scoped to a hardware configuration and capability. The public board, SoC, and IP
baseline supports later OS integration and private overlays; full vendor workflows and Fuchsia
integration are separately gated follow-ons. The requirements below describe the design direction;
section 10 limits pilot delivery.

Requirements:

| ID | Required outcome |
|---|---|
| R1 | Every implementation-critical requirement has a stable identity, applicability, provenance, and an explicit validation disposition. |
| R2 | Completeness is measured against a source-derived inventory established independently of the candidate spec. |
| R3 | Public-only and authorized private runs use the same engine and public baseline; private inputs cannot silently contaminate public artifacts. |
| R4 | Accepted specs pass independent accuracy and applicable clean-room checks; acceptance cannot be inferred from zero failures alone. |
| R5 | Tests have independently supported expected outcomes and link requirements to implementation and hardware evidence. |
| R6 | Hardware results identify the actual device, firmware, booted image, test, fixture, and run; inconclusive runs never pass. |
| R7 | Frozen evaluations compare models and skills; maintenance runs detect changes in sources, specs, target code, and equipment. |
| R8 | Expert feedback is optional, durable, actionable, and invalidates affected acceptance when warranted. |
| R9 | Fuchsia-specific integration stays in Fuchsia skills; contracts and evaluation machinery remain useful to other OS ports. |

Non-goals: universal hardware proof, a universal simulator, or automatic disclosure of restricted
information. Coverage is limited to declared capabilities and faults, with omissions visible.

## 2. Existing machinery and specific gaps

This proposal extends [EVAL-PLAN.md](EVAL-PLAN.md); it does not replace its frozen-corpus pilot or
independent gold ledger. The [ENC28J60 ledger format](evals/enc28j60/LEDGER-FORMAT.md) already
defines
stable IDs, independent authoring, applicability, precision, and recall. The pilot README says that
the ledger itself is not yet written. Complete that work before treating the pilot as an answer key.

Gaps and the resolved checker finding:

1. Most verifier claim identities follow document structure, a limitation already documented in
   EVAL-PLAN.md. Stable IDs support lasting claim-to-test links but alone do not detect omissions;
   an independent inventory and coverage scoring do.
2. A missing/stale verification record can be a warning; zero `FAIL` can coexist with unresolved
   critical claims. There is no capability-specific acceptance policy.
3. Clean-room boundary repair already stops after two failures on the same section. Accuracy
   verification lacks a consistent bounded repair workflow across spec kinds; structured expert
   feedback is also absent.
4. No shared contract connects requirements, expected outcomes and decision rules, generated tests,
   fixture capabilities, execution evidence, and acceptance decisions.
5. Overlay precedence handles configuration, but cannot by itself establish which contradictory
   factual statement is correct or which derived artifact may be published.
6. Git preserves committed verification snapshots. Validation must additionally identify and retain
   every attempt, its input revisions, scope, verdicts, and evidence references. A later attempt
   must not replace an earlier attempt's evidence.
7. The checker returned on a stale hash before checking the FAIL count, hiding failures behind a
   stale-record warning. This bug was fixed in this branch in commit `4e4069a`; it is not open work.

## 3. Architecture and ownership

Agents research, draft, interpret, and propose repairs. Deterministic scripts check schemas and
links, calculate coverage, verify hashes, and apply acceptance policy. A model cannot self-certify
by writing `accepted: true`.

For the pilot, evaluation material lives under `evals/`; extend `spec-verifier` and
`board-expert/scripts` in place with versioned interfaces for consumers. Shared schemas belong
beside the ledger, and checking scripts beside `spec_check.py`. Do not create `hardware-validation`
or `hardware-spec-eval` now; mint those skills only when a second device shows the reuse.

| Component | Responsibility |
|---|---|
| `evals/enc28j60/` | Blind corpus/ledger construction, scoring, validation contracts, and mutation cases. |
| `spec-verifier` | Accuracy checks, coverage against the independent ledger, per-claim dispositions, preserved attempts, and bounded repair. |
| `board-expert/scripts` | Mechanical checks, strict acceptance, freshness, and policy-version checks. |
| Existing spec authoring skills | Claim mappings and applicable accuracy and clean-room checks, preserving their source-access rules. |
| `board-expert/VENDOR-GUIDE.md` | Clarify derived-artifact restrictions in section 5; full vendor workflow remains deferred. |

In the companion Fuchsia skill package, a separately gated follow-on could consume these contracts,
survey a pinned checkout, generate/build Fuchsia tests, and invoke the existing hardware-bench and
boot-test adapters. It must first name a board, image, peripheral, fixture, and external observation
method. Derive APIs and commands from that checkout. Neither changes to that package nor a new
Fuchsia skill are authorized here.

## 4. Artifacts and schemas

Keep Markdown for readable hardware and implementation specs. Use versioned YAML for authoring
manifests and canonical JSON for machine-produced records. Reuse the ENC28J60 ledger vocabulary
and IDs; define an explicit schema migration rather than a second incompatible requirement format.

Illustrative layout in a consuming target project, including the `runs/<run-id>/` tree:

```text
docs/hardware/<platform>/
  platform.yaml
  sources.lock.json
  requirements.yaml
  claims.yaml
  specs/<peripheral>-spec.md
  validation/<peripheral>.yaml
  reviews/<review-id>.yaml
  runs/<run-id>/
    manifest.json
    claim-verdicts.json
    coverage.json
    test-results.json
    acceptance.json
    artifacts.json
```

The directory shape is not required; the platform manifest can point to existing locations.

Preserve each verification attempt and its input revisions, verification scope, verdicts, and
evidence references before updating the replaceable latest-status record. The latest-status record
identifies the attempt or attempts supporting its verdicts. Carried-forward verdicts retain their
originating attempt and applicability to the current revision.

Attempt files beside the record or retained commits both satisfy this rule. A git tag alone does
not, since tags can move or be deleted. Existing clean-room provenance maps
retain their restricted location and access rules. Large logs/captures can live in an artifact
store referenced by digest; run metadata must record availability and retention rather than promise
that a hash makes missing evidence reproducible. Private runs and their artifacts live in separate
private output roots, not beneath a public repository awaiting a final scrub.

Minimal contracts:

- **Platform manifest:** board/SoC/variant/revision, capability graph and prerequisites, spec roots,
  target checkout/revision, source-access mode, visibility profile, acceptance policy/version,
  approved test envelope, and evidence locations. An omitted peripheral is recorded as out of scope,
  not mistaken for a supported one.
- **Source lock:** immutable repository commits, document edition and digest, firmware identifiers,
  acquisition status, classification, access adapter, and redistribution constraints. A digest pins
  content but does not grant access or copying rights.
- **Requirement ledger:** existing immutable IDs and classes, augmented with capability links,
  prerequisite IDs, applicability conditions, and explicit, versioned `validation` fields:
  `documentary`, `physical`, `either`, or `both`, with rationale. `both` requires a documentary
  check
  and a physical test. Changes in meaning mint a new ID with `supersedes`; numbering never follows
  Markdown section order.
- **Claim mapping:** stable claim IDs mapped to Markdown anchors, requirement IDs, source locators,
  scope, and supporting evidence. Extra candidate claims still receive precision checks. Schema
  tooling detects missing/duplicate IDs and dangling links; semantic extraction audits detect prose
  claims the author failed to register.
- **Validation contract:** test ID, requirement IDs, purpose, expected outcome and decision rule
  with independent
  authority, stimulus, observations, tolerance, setup/cleanup, fixture capabilities, timeouts,
  repetition plan, failure modes, and generated test artifact/revision.
- **Run manifest:** all input digests, composed spec digest, validation contract digest, acceptance
  and scoring policy versions, model/provider/version identifier as exposed, prompts and skill
  revisions, tool versions, budget, timestamps, seeds where
  supported, access profile, and actor roles. Unknown model details remain unknown.
- **Results:** separate claim verdicts, coverage dispositions, test verdicts, and acceptance
  decisions.
  No blended confidence score substitutes for these.

Check the validation contract's digest at scoring. Changing the contract requires renewed review.

Requirements and claims must fail independently; one register claim cannot cover an entire
initialization sequence. Coverage follows the declared capability graph.

## 5. Independent generation and acceptance

The workflow has explicit boundaries:

1. Resolve the platform and visibility profile; freeze source inputs and capability scope.
2. Build the requirement ledger from the corpus without reading a candidate spec. Independently
   derive critical rows twice; preserve disagreements. Freeze the ledger before candidate scoring.
3. Generate the candidate spec with the existing clean-room or anchored workflow. In evaluation,
   hide the scoring ledger from the author. In ordinary production, giving the author the ledger
   improves coverage, but that run is not reported as a blind benchmark.
4. Run mechanical checks, independent accuracy verification, ledger-to-spec coverage, and applicable
   clean-room checks. Continue to check claims outside the ledger.
5. Author validation expectations from the independently established requirements and authorities.
   A separate agent reviews whether each expected outcome and decision rule could reject a
   plausible faulty implementation. Test implementers can consume accepted specs; they cannot
   silently change the expected outcome and decision rule to make a failing implementation pass.
6. Build and execute tests, preserving raw results. Apply deterministic capability acceptance rules.
7. Publish the accepted revision or an explicit incomplete result with blocked capabilities and
   proposed next investigations. Subsequent edits create new revisions and invalidate dependent
   decisions until checked again.

Fresh contexts do not prevent correlated errors. Prefer different evidence channels and, when
available, model families; record limitations. Agreement cannot replace authority or measurement.

Maintain separate acceptance dimensions:

| Dimension | Initial strict policy |
|---|---|
| Spec ready for implementation | All mandatory in-scope requirements covered; critical claims independently supported; no unresolved blocking conflicts or known factual failures; current hashes; applicable clean-room gate passed. |
| Implementation validated | Spec ready; required host and target integration tests pass against the recorded implementation revision. |
| Hardware validated | Required physical tests pass on the named configuration within the declared test envelope; instrument and image identity checks pass. |

Criticality follows the ledger's consequence-based weight. For board specs, the minimum critical
set is the two-verifier set already named by `spec-verifier`: addressing model, boot chain and entry
state, debug UART, and debug console. A selective strict check needs per-claim machine-readable
dispositions or a record-body parser, a mapping to the critical set, and detection of missing
expected claims. `--strict` implies `--require-verified` and rejects missing or stale verification
and critical `UNVERIFIABLE` or `ADJUDICATE` claims.

Documentary checks can substitute for physical tests only as allowed by the ledger's versioned
validation obligation and rationale, established before execution. A `both` obligation requires
each.
Exploratory bring-up need not earn strict acceptance; unresolved requirements stay in the
denominator.

Preserve `PASS`, `FAIL`, `GAP`, `UNVERIFIABLE`, and `ADJUDICATE` as claim verdicts. Hardware tests
use `PASS`, `FAIL`, `INCONCLUSIVE`, `UNAVAILABLE`, and `NOT_APPLICABLE` with reasons. Applicability
decisions are frozen inputs subject to review. A capability is `accepted`, `blocked`, or `stale` in
each dimension. Disagreement is not a factual failure, but it blocks a capability that requires the
unresolved claim. Zero `FAIL` alone is never an acceptance rule.

Evidence channels have run-scoped fitness dispositions separate from strict acceptance of the
hardware capability that implements them. A channel is usable for a named observation only when its
predefined checks establish the identity, freshness, integrity, and completeness needed for that
observation. Readable output alone is insufficient. An unresolved claim about the channel's hardware
implementation blocks dependent observations only when it undermines those checks or their
evidentiary assumptions.

Channel dispositions are `usable`, `inconclusive`, or `unavailable`, with observation scope
recorded.
A UART can hold both roles; qualifying it as a channel does not accept it as a capability.

For automated accuracy repair, stop after two failed checks on the same section, consistently across
spec kinds, with a recorded cost/time budget. Two failed checks are not two repair-and-reverify
rounds; the clean-room boundary workflow already uses the former bound. Preserve unresolved findings
for expert resolution or a fresh investigation. Boundary failures require repair/reverification or
a separately authorized workflow change, not a relabeled verdict.

## 6. Tests and actual hardware

Test normal, boundary, recovery, repeated-operation, and interaction behavior per capability.
Declare unsupported or unobservable cases; a peripheral happy path cannot establish system health.

Fixture adapters expose operations such as `power.cycle`, `serial.capture`, and `network.peer`.
Contracts cover preflight, exclusive leases, timeouts, capture, cleanup, and recovery. Keep
hostnames
and credentials in local/private configuration; record instrument configuration and calibration.

Every physical run establishes an exclusive fixture lease and fresh capture window before boot,
records a unique run token and target/image identity, confirms the expected image actually booted,
then runs the test. If image identity cannot be established, the result is inconclusive. Preserve
serial logs, external captures, and instrument results. Retries are separate linked attempts; a
later pass does not erase an earlier failure. Report flakiness and repetition counts separately.

Host-captured serial is independent capture, not independent evidence. A verdict must rest on
something the host observed, such as traffic on a peer interface, a loopback the host drives, or an
instrument reading, never on a target-printed pass marker.

Unattended operations stay within the approved test envelope. Destruction of persistent data,
irreversible provisioning, or exceeding hardware limits requires separate explicit scope.
Fixture loss or cleanup failure quarantines the fixture.

Test the tests with deliberate faults: wrong interrupt routing, missing acknowledgment, incorrect
length, stale serial verdict, wrong boot image, truncated capture, and broken recovery. Use host or
simulation mutations first; only safe faults within the envelope run on equipment. Count detected,
undetected, and invalid mutations, and report false alarms on known-good controls. A simulated
fault detected by a mock is useful evidence about the test, not proof of physical behavior.

## 7. Public and vendor composition

The pilot is public-only. Reuse the three enforcement layers ranked by `cleanroom-spec`:
environment restrictions first, then hooks, then instructions. Controlled source mounts and tool
and network access must exclude private inputs; an environment role alone is not enough. Generate
public artifacts in clean public contexts. Sanitizing private prose afterward is insufficient.

For restrictions on what may leave a private root, including derived artifacts, see
[board-expert/VENDOR-GUIDE.md section
5](skills/board-expert/VENDOR-GUIDE.md#5-classify-what-may-leave).
The full authorized-private workflow is deferred; its composition design remains:

- Keep `public → ip-vendor → soc-vendor → product → local` for configuration precedence. Access
  classification and permitted output audience are separate fields; layer is not confidentiality.
- Vendor packages add overlays, evidence, and tools through versioned public IDs without copying
  baseline specs. IP behavior belongs in IP specs, placement in SoC instances, wiring in boards.
- Factual overrides name the replaced claim, evidence, and applicability. Overlapping contradictory
  facts remain conflicts unless supported supersession resolves them. Strict composition rejects
  same-layer ambiguity; configuration precedence cannot decide factual truth.
- Public and private results remain separate. A private pass cannot repair a missing public
  citation.
  Private profiles must enforce source restrictions and model/tool approvals; context separation
  alone supplies neither authorization nor confidentiality enforcement.

## 8. Expert feedback without mandatory expert review

An expert can submit a review against a spec, ledger, skill, test, or evidence record. The artifact
contains target IDs/revision, proposed correction, rationale, supporting reference or observation,
applicability, severity, and disclosure constraints. Private reviews remain private. Contributor
identity is recorded only as allowed by repository and visibility policy.

Feedback is processed as a versioned change proposal:

1. Check the target revision and preserve the original comment.
2. Reproduce the issue or record why it cannot yet be established. An expert observation is valid
   evidence with its stated limits; it is not silently relabeled as a documented universal fact.
3. A merged review targeting a critical-weight row or claim, with a reproduction or located
   authority, suspends dependent acceptance. Authority comes from repository authorization controls
   (protected branch, required reviewers), not the commit author field. Anything else is an
   adjudication item. Do not invalidate unrelated peripherals.
4. A separate author proposes a correction; independent checks and affected tests run again.
5. Record accepted, rejected-with-reason, or unresolved disposition and link the new evidence.

Record expert resolutions as adjudication or waivers, never automated or hardware passes. Strict
acceptance does not count waivers. Skill corrections require a regression case for the failure.

For benchmark feedback, freeze a new ledger/corpus revision and rescore preserved old candidates.
Never improve a model's apparent performance by silently changing its answer key. Candidate-informed
findings go into a future benchmark revision, labeled as such, rather than the current blind ledger.

## 9. Repeatable evaluation and evidence lifetime

ENC28J60 remains the first calibration device. Fuchsia UART is a separately gated follow-on under
section 3's five prerequisites; Pixel 10 is a later partial-evidence case. Establish hardware
availability before promising physical campaigns.

Evaluation modes, with full campaign infrastructure deferred:

- **Frozen:** same corpus, scope, independently authored ledger, fixture configuration, budget, and
  scoring policy; compare model/skill versions and with-skill versus baseline. Repeat runs and
  report variation. Keep held-out error cases separate from examples used to tune skills.
- **Maintenance:** update selected inputs intentionally, calculate affected dependencies, reverify
  and rerun. Preserve the previous accepted snapshot and explain the changed result.

Refuse comparisons across acceptance or scoring policy versions with an explicit version check.
After a ledger revision, report scores against both the run's frozen revision and the current one;
label candidate-informed corrections. A changed answer key must not appear as a model regression.

Report precision, recall per criticality, unresolved/unrecoverable requirements, test coverage,
mutation detection, false acceptance/rejection on adjudicated fixtures, hardware availability,
flakiness, and cost/time separately. Do not collapse them into a single score. Until a fixture or
answer key is independently established, label the corresponding measurement provisional.

Evidence is immutable by run ID. A small latest-status index may be replaced, but historical runs
and verdicts are retained. Invalidation includes changes to a dependency's content, applicability,
policy, tests, expected outcome and decision rule, implementation, firmware, and fixture
configuration.
Start with conservative invalidation; optimize only with tested dependency mappings. Missing
archived inputs
make replay unavailable, not successful. Record source/tool nondeterminism rather than promise
bit-identical agent outputs.

Offline CI checks schemas, links, composition, policy, and synthetic fixtures without vendor
credentials. Paid campaigns require scheduling or explicit invocation; reuse plugin-eval where
it fits with harness-neutral manifest/result contracts.

## 10. Proposed delivery sequence and acceptance experiments

Delivery is B, A, C, D. This document authorizes neither implementation nor a paid campaign. The
public-only pilot retains frozen input hashes, preserved attempts, explicit score versions,
conservative invalidation, and freshness checks from the first score onward.

| Stage | Deliverable and entry condition | Decisive experiment |
|---|---|---|
| B | Complete the existing ENC28J60 independent ledger, authored blind and frozen | Independently derive critical rows; adjudicate conflicts and freeze the inventory before reading candidates. |
| A | Smallest ledger scoring and strict acceptance tools in existing locations; entry condition: ledger authored blind and frozen | Remove a functional section and recall falls; insert a wrong constant and precision falls; zero failures with a missing critical requirement is blocked, as are stale or unresolved critical verdicts. |
| C | Validation contracts, test generation/review, synthetic fixture adapter | An independently supported expected outcome and decision rule reject a plausible fault; wrong image, stale log, missing tool, and truncated capture never pass. |
| D, ENC28J60 | Physical validation, gated on an established fixture | Observe traffic externally, detect a safe injected fault, reproduce a cold-start result, and retain every attempt. |
| D, Fuchsia | Separately gated UART follow-on, after naming board, image, peripheral, fixture, and external observation method | Build and execute real Fuchsia tests; host observations establish the verdict under the same identity and freshness checks. |

Stages E and F are deferred to a follow-on proposal written after the first score exists. E contains
the full vendor workflow and feedback automation; F contains campaign infrastructure and optimized
dependency replay. Their deferral does not remove the pilot's evidence retention or version checks.

Test public-only access boundaries synthetically in A. Each stage includes relevant contract checks
and adversarial cases. Hardware absence can leave either D deliverable pending without blocking
earlier work, but cannot be described as hardware validation.

Existing specs continue in legacy reader mode. Strict acceptance requires IDs, mappings, locks,
policy, and the missing checks; converting an old record cannot confer acceptance. Preserve
EVAL-PLAN history and reconcile its manual scoring/adjudication steps during implementation design.

## 11. Alternatives and open design choices

Markdown plus reviewer prompts cannot reliably enforce coverage or freshness. Fully structured
register specifications impose modeling work too early. Keep structured identities, dependencies,
policies, and results alongside prose, with versioned interfaces between existing components.

Open design choices:

- **Board and SoC claim IDs:** choose facets and who assigns them, beyond the ENC28J60 vocabulary.
- **Acceptance policy location:** platform manifest, repository, or checker defaults. Refusing
  comparisons across policy versions is settled; storage is not.
- **Record compatibility:** sidecar or in-place migration for run metadata and per-claim
  dispositions,
  preserving every attempt while keeping the latest record replaceable.
- **Public-only enforcement:** choose the concrete environment restrictions, hooks, and
  instructions;
  the three-layer order and insufficiency of an environment role alone are settled.
- **Stage D equipment:** establish the ENC28J60 host and fixture, including how the SPI host is
  qualified, and separately name all five prerequisites for the Fuchsia UART slice.
