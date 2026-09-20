<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Proposal: evidence-driven hardware specs and Fuchsia validation

Status: proposed for collaborator review, 2026-09-19. No implementation is authorized by this document.

## 1. Outcome and scope

Produce hardware specifications that support a Fuchsia port, executable tests that exercise the
resulting implementation, and reproducible evidence describing what is established and what remains
unknown. Routine acceptance should not require a person to read generated specs. Domain experts
must nevertheless be able to challenge any spec, requirement, skill, test, or verdict and contribute
corrections through the same recorded process.

One public set of board, SoC, and IP specs remains the baseline. Private vendor packages add evidence,
facts, and tool access without maintaining a second complete platform description. Validation is
always scoped to a hardware configuration and capability, never an unqualified claim that a platform
is correct.

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

Non-goals: proving arbitrary hardware correct, building a universal simulator, automatically making
restricted information public, or replacing instrument calibration with an agent's confidence.
Comprehensive means coverage of a declared capability and fault model, with omissions visible.

## 2. Existing machinery and specific gaps

This proposal extends [EVAL-PLAN.md](EVAL-PLAN.md); it does not replace its frozen-corpus pilot or
independent gold ledger. The [ENC28J60 ledger format](evals/enc28j60/LEDGER-FORMAT.md) already defines
stable IDs, independent authoring, applicability, precision, and recall. The pilot README says that
the ledger itself is not yet written. Complete that work before treating the pilot as an answer key.

Existing components to retain:

- `board-expert` resolves and composes hardware specs and vendor overlays.
- `board-spec-scaffold` authors those references and requests verification.
- `cleanroom-spec` and `anchored-peripheral-spec` produce peripheral implementation specs.
- `spec-verifier` checks claims against pinned authorities and records disagreement separately.
- Mechanical checkers and clean-room tooling enforce format, anchors, and transfer boundaries.
- Companion Fuchsia bench and boot-test skills provide useful procedures for collecting results.

Gaps that prevent the intended outcome today:

1. Most verifier claim identities follow document structure. They do not expose undisclosed omissions
   or remain stable enough for long-lived claim-to-test relationships.
2. A missing/stale verification record can be a warning; zero `FAIL` can coexist with unresolved
   critical claims. There is no capability-specific acceptance policy.
3. Independent verification and human adjudication exist, but there is no bounded automatic
   resolution workflow or first-class expert feedback artifact.
4. No shared contract connects requirements, test oracles, generated tests, fixture capabilities,
   execution evidence, and acceptance decisions.
5. Overlay precedence handles configuration, but cannot by itself establish which contradictory
   factual statement is correct or which derived artifact may be published.
6. Verification records are overwritten. Longitudinal model comparisons require immutable run
   records and preserved evidence, not just the latest verdict.

## 3. Architecture and ownership

Use small, composable skills around a deterministic validation tool. Agents research, draft,
interpret, and propose repairs; scripts resolve manifests, check schemas and links, calculate
coverage, verify hashes, and evaluate acceptance policy. A model never self-certifies by writing
`accepted: true` into a report.

Proposed changes in this plugin:

| Component | Change |
|---|---|
| `board-expert/SPEC-FORMAT.md`, reader, and checker | Add optional stable claim IDs, applicability, and references to validation manifests. Reject ambiguous composition in strict validation mode. |
| `board-spec-scaffold` | Produce claim mappings and source inventory references; preserve ordinary lightweight scaffolding. |
| `cleanroom-spec` | Require accuracy as well as boundary verification for acceptance; attach requirement and test mappings; bounded repair followed by unresolved status. |
| `anchored-peripheral-spec` | Emit the same requirement/test mappings while retaining source anchors and its different source-access rules. |
| `spec-verifier` | Retain per-claim checking; add independent-ledger coverage, stable identities, immutable run records, and a separate acceptance decision. |
| `board-expert/VENDOR-GUIDE.md` and vendor template | Define evidence classification, capability declarations, scoped factual overrides, and public-only execution. |
| New `hardware-validation` skill | Own shared schemas, checker/acceptance tooling, validation-plan generation, oracle review, execution contracts, and evidence ingestion. |
| New `hardware-spec-eval` skill | Own blind corpus/ledger construction, frozen campaigns, mutation cases, model comparison, and expert-feedback processing. |

The new skills would live under `plugins/driver-porting/skills/`; supporting schemas and scripts
belong beside their owning skill, with a versioned interface for consumers. Register them in both
READMEs and run the existing registration checker when implementation lands.

In the companion Fuchsia skill package, propose a `fuchsia-port-validation` skill that consumes
these contracts: surveys the pinned target tree, generates/builds appropriate Fuchsia tests, maps
capabilities to existing drivers and test facilities, and invokes existing bench tools. Exact APIs
and commands must be derived from that checkout, not hardcoded in this proposal. The existing
hardware-bench and boot-test skills remain execution adapters. Changes to that separate package
are a follow-on workstream, not edits implicitly authorized here.

## 4. Artifacts and schemas

Keep Markdown for readable hardware and implementation specs. Use versioned YAML for authoring
manifests and canonical JSON for machine-produced records. Reuse the ENC28J60 ledger vocabulary
and IDs; define an explicit schema migration rather than a second incompatible requirement format.

Proposed layout in a consuming target project:

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

This is a default for new projects, not a forced migration of existing `docs/<device>-spec.md`
files. The platform manifest points to existing locations. Existing clean-room provenance maps
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
  prerequisite IDs, applicability predicates, and validation obligations. Changes in meaning mint a
  new ID with `supersedes`; numbering never follows Markdown section order.
- **Claim mapping:** stable claim IDs mapped to Markdown anchors, requirement IDs, source locators,
  scope, and supporting evidence. Extra candidate claims still receive precision checks. Schema
  tooling detects missing/duplicate IDs and dangling links; semantic extraction audits detect prose
  claims the author failed to register.
- **Validation contract:** test ID, requirement IDs, purpose, expected outcome and its independent
  authority, stimulus, observations, tolerance, setup/cleanup, fixture capabilities, timeouts,
  repetition plan, failure modes, and generated test artifact/revision.
- **Run manifest:** all input digests, composed spec digest, policy version, model/provider/version
  identifier as exposed, prompts and skill revisions, tool versions, budget, timestamps, seeds where
  supported, access profile, and actor roles. Unknown model details remain unknown.
- **Results:** separate claim verdicts, coverage dispositions, test verdicts, and acceptance decisions.
  No blended confidence score substitutes for these.

A single register claim must not stand for an entire complex init sequence. Requirements and claims
are atomic enough to fail independently. Coverage includes boot chain, CPU/SMP, timers, interrupt
controllers, memory/DMA, clocks/resets/power, buses, peripheral behavior, and Fuchsia integration,
as applicable to the declared capability graph.

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
   A separate agent reviews whether each oracle could reject a plausible faulty implementation.
   Test implementers can consume accepted specs; they cannot silently change the oracle to make a
   failing implementation pass.
6. Build and execute tests, preserving raw results. Apply deterministic capability acceptance rules.
7. Publish the accepted revision or an explicit incomplete result with blocked capabilities and
   proposed next investigations. Subsequent edits create new revisions and invalidate dependent
   decisions until checked again.

Fresh contexts prevent shared drafting history, not correlated model errors. Use different model
families for critical independent checks when available, record when unavailable, and prioritize
different evidence channels over simply buying more votes. Agreement is never a substitute for a
located authority or a measured result.

Maintain separate acceptance dimensions:

| Dimension | Initial strict policy |
|---|---|
| Spec ready for implementation | All mandatory in-scope requirements covered; critical claims independently supported; no unresolved blocking conflicts or known factual failures; current hashes; applicable clean-room gate passed. |
| Implementation validated | Spec ready; required host and target integration tests pass against the recorded implementation revision. |
| Hardware validated | Required physical tests pass on the named configuration within the declared test envelope; instrument and image identity checks pass. |

Requirements may be satisfied through documentary checks instead of physical tests where physical
observation is infeasible, but the obligation and rationale are set before execution. Source-only
uncertainties remain visible; a platform may support exploratory bring-up without earning strict
acceptance. Unknowns cannot be removed from the denominator because the agent could not solve them.

Preserve `PASS`, `FAIL`, `GAP`, `UNVERIFIABLE`, and `ADJUDICATE` as claim verdicts. Hardware tests
use `PASS`, `FAIL`, `INCONCLUSIVE`, `UNAVAILABLE`, and `NOT_APPLICABLE` with reasons. Applicability
decisions are frozen inputs subject to review. A capability is `accepted`, `blocked`, or `stale` in
each dimension. Disagreement is not a factual failure, but it blocks a capability that requires the
unresolved claim. Zero `FAIL` alone is never an acceptance rule.

For automated repair, allow two repair/reverification rounds per issue per run by default, bounded
by a recorded cost/time budget. Persist unresolved findings after that. A fresh investigation may
use another authority or a safe distinguishing experiment; majority vote is not adjudication.
Preserve an optional expert resolution path. A clean-room boundary failure cannot be waived by
changing a verdict: repair/reverification or a separately authorized change of workflow is required.

## 6. Tests and actual hardware

Each capability gets normal, boundary, failure/recovery, repeated-operation, and interaction cases
where applicable. Examples include interrupt clearing/retriggering, queue wraparound, DMA alignment
and coherency, timeout handling, reset during traffic, and suspend/resume. Declare unsupported or
unobservable cases explicitly. A peripheral happy-path test cannot establish whole-system health.

Fixture adapters expose capabilities rather than machine identities: `power.cycle`, `serial.capture`,
`uart.peer`, `usb.capture`, `network.peer`, `scope.measure`, or a vendor reference instrument.
Their contract includes preflight, exclusive resource lease, operation, timeout, evidence capture,
cleanup, and recovery. Concrete hostnames and credentials stay in local/private configuration.
External instruments also need recorded configuration and calibration status where relevant.

Every physical run establishes an exclusive fixture lease and fresh capture window before boot,
records a unique run token and target/image identity, confirms the expected image actually booted,
then runs the test. If image identity cannot be established, the result is inconclusive. Preserve
serial logs, external captures, and instrument results. Retries are separate linked attempts; a
later pass does not erase an earlier failure. Report flakiness and repetition counts separately.

The runner may operate unattended within a preconfigured envelope: reset/power operations, allowed
interfaces, maximum duration/rate, and disposable test storage. Persistent-data destruction,
irreversible provisioning, and operation outside hardware limits require separate explicit scope.
Fixture loss and cleanup failure quarantine the fixture rather than trigger uncontrolled retries.

Test the tests with deliberate faults: wrong interrupt routing, missing acknowledgment, incorrect
length, stale serial verdict, wrong boot image, truncated capture, and broken recovery. Use host or
simulation mutations first; only safe faults within the envelope run on equipment. Count detected,
undetected, and invalid mutations, and report false alarms on known-good controls. A simulated
fault detected by a mock is useful evidence about the test, not proof of physical behavior.

## 7. Public and vendor composition

Keep `public → ip-vendor → soc-vendor → product → local` for configuration precedence. Add separate
fields for access classification and permitted output audience: layer is not a confidentiality
label, and ownership of a document does not determine its licensing.

Vendor packages supply overlay roots, access skills, evidence, test contracts, fixture adapters,
and optional reference implementations/tools. They depend on versioned public IDs; they do not
copy public specs. Generic IP behavior belongs in the IP spec, placement in the SoC instance,
connector/wiring in the board, and private evidence in the appropriate overlay.

Factual overrides name the replaced claim ID, evidence, and applicability predicate. Differing
values with overlapping applicability become a recorded conflict unless an explicit supported
supersession resolves them. No silent last-writer-wins for facts. Reject same-layer ambiguity in
strict composition. A vendor change to a public requirement's meaning gets a linked revision or
scoped additional requirement, not an invisible mutation of the baseline.

Two execution profiles use the same tooling:

- **Public-only:** only public roots, sources, tools, and clean public-run contexts are available.
  Missing evidence is reported as a public limitation; private resource names need not be exposed.
- **Authorized-private:** explicitly allowlisted roots and tools contribute additional facts and
  tests. Outputs inherit all applicable restrictions of their inputs. Conflicting permissions block
  export; no single ordering of vendor layers is treated as a permission hierarchy.

Public artifacts are generated in a run without private context, with controlled source mounts and
tool/network access. Sanitizing private prose afterward is insufficient. Private findings may
motivate investigation, but a public claim requires independent public support and a clean public
derivation; vendor-authorized publication is a separate explicit process. Public and private test
results are reported separately, even when they implement the same logical test ID. A private pass
does not repair a missing public citation or make private evidence publicly reproducible.

Vendor model/tool approval rules are part of the private execution profile. Context separation
alone provides neither authorization nor confidentiality enforcement.

## 8. Expert feedback without mandatory expert review

An expert can submit a review against a spec, ledger, skill, test, or evidence record. The artifact
contains target IDs/revision, proposed correction, rationale, supporting reference or observation,
applicability, severity, and disclosure constraints. Private reviews remain private. Contributor
identity is recorded only as allowed by repository and visibility policy.

Feedback is processed as a versioned change proposal:

1. Check the target revision and preserve the original comment.
2. Reproduce the issue or record why it cannot yet be established. An expert observation is valid
   evidence with its stated limits; it is not silently relabeled as a documented universal fact.
3. Mark affected acceptance disputed while a credible critical challenge is unresolved; propagate
   to dependent tests/capabilities. Do not invalidate unrelated peripherals.
4. A separate author proposes a correction; independent checks and affected tests run again.
5. Record accepted, rejected-with-reason, or unresolved disposition and link the new evidence.

An authorized expert may settle an interpretation or explicitly accept a limited exception. Record
this as expert adjudication or waiver, never as an automated verification or hardware pass. The
default strict profile does not count waivers as satisfying its obligations. Expert changes to
skill text trigger skill regression cases, including a case demonstrating the reported failure.

For benchmark feedback, freeze a new ledger/corpus revision and rescore preserved old candidates.
Never improve a model's apparent performance by silently changing its answer key. Candidate-informed
findings go into a future benchmark revision, labeled as such, rather than the current blind ledger.

## 9. Repeatable evaluation and evidence lifetime

Retain the existing ENC28J60 pilot as the first calibration device; do not substitute a new UART
benchmark and discard its work. Add a Fuchsia UART slice afterward to test OS integration and the
board/SoC/IP composition path. Pixel 10 is a subsequent applicability/partial-evidence case, not a
prerequisite for proving the machinery works. Hardware availability must be established before
promising any physical campaign.

Two campaigns:

- **Frozen:** same corpus, scope, independently authored ledger, fixture configuration, budget, and
  scoring policy; compare model/skill versions and with-skill versus baseline. Repeat runs and
  report variation. Keep held-out error cases separate from examples used to tune skills.
- **Maintenance:** update selected inputs intentionally, calculate affected dependencies, reverify
  and rerun. Preserve the previous accepted snapshot and explain the changed result.

Report precision, recall per criticality, unresolved/unrecoverable requirements, test coverage,
mutation detection, false acceptance/rejection on adjudicated fixtures, hardware availability,
flakiness, and cost/time separately. Do not collapse them into a single score. Until a fixture or
answer key is independently established, label the corresponding measurement provisional.

Evidence is immutable by run ID. A small latest-status index may be replaced, but historical runs
and verdicts are retained. Invalidation includes changes to a dependency's content, applicability,
policy, test/oracle, relevant target implementation, firmware, and fixture configuration. Start with
conservative invalidation; optimize only with tested dependency mappings. Missing archived inputs
make replay unavailable, not successful. Record source/tool nondeterminism rather than promise
bit-identical agent outputs.

Normal offline CI checks schemas, graph links, composition, policy decisions, and synthetic fixture
parsing. Scheduled or explicitly invoked campaigns pay for models and hardware. Public CI must not
depend on vendor credentials. Model campaigns use the existing plugin-eval entry point where it fits,
with a harness-neutral manifest/result contract around it; additional harnesses need adapters.

## 10. Proposed delivery sequence and acceptance experiments

This is a proposed ordering for review, not an executable milestone plan. Detailed implementation
tasks follow agreement on the contracts and boundaries.

| Stage | Deliverable | Decisive experiment |
|---|---|---|
| A | Shared schemas, ledger integration, deterministic acceptance tool, immutable records | A candidate with zero failures but one missing critical requirement is blocked; stale or unresolved evidence cannot pass. |
| B | Complete existing ENC28J60 independent ledger and evaluation path | Remove a whole functional section and show recall falls; introduce a wrong constant and show precision falls; preserve disagreement separately. |
| C | Validation contracts, test generation/review, synthetic fixture adapter | An independent oracle rejects a plausible faulty implementation; wrong image, stale log, missing tool, and truncated capture never pass. |
| D | ENC28J60 physical campaign and a Fuchsia UART integration slice | Capture externally observed traffic, detect a safe injected fault, reproduce a cold-start result, and retain every attempt. Fuchsia test build/execution must be real, not a prose plan. |
| E | Public/private profiles and expert feedback | Synthetic private overlay composes without duplication; public run cannot access it; a critical expert correction invalidates only dependent acceptance. |
| F | Frozen campaigns and maintenance replay | Compare repeated model/skill runs; change one pinned input and show the correct dependent results become stale. |

Classification and access boundaries are designed and tested synthetically in A; E adds the complete
vendor workflow. Do not run real private evidence through an interim system without enforcement.
Each stage includes unit/contract tests and adversarial cases. Hardware absence can leave D pending
without preventing useful earlier work, but must never be described as hardware validation.

Existing specs continue to work in legacy reader mode. Strict acceptance requires explicit migration
to IDs, mappings, locks, and policy. Legacy verification records remain historical evidence; no
conversion script upgrades them to strict acceptance without doing the missing checks. Preserve the
current EVAL-PLAN history, and reconcile its human-only adjudication/manual scoring steps with this
proposal once the design is agreed.

## 11. Alternatives and review questions

Markdown plus additional reviewer prompts is cheaper initially, but cannot reliably enforce links,
coverage, or evidence freshness. Fully structured register specifications would enable more code
generation but impose substantial modeling work too early. The proposed compromise is structured
identities, dependencies, policies, and results alongside prose specs.

A large autonomous controller could own everything; small skills with a deterministic contract tool
fit the existing repository and permit different harnesses and vendor adapters. The tradeoff is
explicit versioning between components. Multiple model votes alone are simpler than evidence-driven
adjudication, but cannot resolve shared errors or missing public information.

Questions for the colleague reviewing this proposal:

1. Can the independent ledger/oracle workflow still allow a spec and test to share an undetected
   false assumption? Which concrete mutation or external observation would expose it?
2. Is the strict acceptance policy implementable without turning every source limitation into a
   platform-wide blocker? Are capability boundaries and dependency propagation specific enough?
3. Do the public/private execution and composition rules prevent disclosure through reports, test
   expectations, logs, and shared model contexts, as well as through spec prose?
4. Are the shared schemas and two new generic skills justified, or should an existing owner absorb
   one responsibility? Avoid both a monolithic skill and unnecessary micro-skills.
5. What is the smallest real Fuchsia/hardware slice that can validate the full chain with available
   equipment? What instrumentation is needed to make its verdict independent of driver self-report?
6. Which expert feedback should immediately suspend acceptance, and what authenticated project
   policy prevents an arbitrary comment from invalidating all results?
7. Are model comparison, benchmark corrections, and evidence retention strong enough to distinguish
   genuine improvement from answer-key drift, selective retries, or changed hardware?

The requested review should return concrete failure scenarios, proposed edits, and unresolved design
choices. No implementation or paid model/hardware campaign is implied by reviewing this document.
