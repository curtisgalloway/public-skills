<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Driver specification and validation: remaining implementation plan

Revision: 2026-09-20. No experiment launched by this plan.

## Terms

- **Spec and companion skill** — the hardware contract and agent instructions for using it,
  supporting documentation, and tools to implement and diagnose drivers.
- **Milestone** — a deliverable with acceptance criteria, tests, review, and a checkpoint.
- **Ledger** — the independently authored hardware-requirement answer key.
- **Arm** — one experimental condition, with or without the specification-authoring skill.
- **Validation contract** — a test's requirements, expected observations, decision rule, and limits.
- **Fixture** — the equipment and connections used for repeatable physical tests.
- **Mutation** — a deliberate defect used to check that a test detects incorrect behavior.

See the [glossary](../../GLOSSARY.md). Paths below are relative to this plugin unless stated
otherwise. Proposed files are explicitly labeled; their names are not working interfaces yet.

## Design authority and completion boundary

The user reprioritized this plan on 2026-09-20: prioritize the **Linux driver mechanism**
following an independent assessment of whether direct implementation and verification would
serve the practical goal better than the remaining experimental preparation. This revision
adopts that direction. The immediate deliverable is one Linux driver produced using the spec
and existing skills, independently reviewed and meaningfully tested, with demonstrated gaps
repaired in working copies of the driver and spec.

The [overview](DRIVER-QUALITY.md) defines success as less engineering time to a defined quality
bar. The active milestone below tests that useful development loop directly. It does not try
to establish that an authoring skill caused better results independently of model knowledge
or outside assistance. Controlled comparisons can follow after this mechanism demonstrates value.

Reuse the [design](DESIGN.md), [validation proposal](VALIDATION-PROPOSAL.md), and completed
preparation where useful. Preserve the [evaluation plan](EVAL-PLAN.md),
[reconstruction protocol](RECONSTRUCTION.md), and frozen trial artifacts as the authority for
any later **spec-only experiment**. Their isolation, scoring, pairing and attribution gates
remain binding for those experiments; they are not prerequisites for the separately labeled
Linux engineering pass. Do not relabel its outputs as M05, a paired arm, or a qualified
spec-only result. The original [plan review](evidence/PLAN-REVIEW.md) records the earlier scope;
this revision's review is recorded [separately](evidence/LINUX-PRIORITY.md).

The existing board-expert, authoring, implementation and verification skills remain the
companion-skill deliverable. Exercise the useful parts in the Linux pass and repair concrete
usability defects. No new general validation framework or skill is needed to start.

**Immediate completion:** one independently reviewed Linux driver with recorded behavior under
a declared test scope, a requirement-to-evidence table, and versioned spec/driver repairs.
A build-only result is partial. A failed behavior check or unresolved critical requirement is
not a pass; exhausting the agreed effort limit produces an incomplete checkpoint with findings.
Do not erase failed attempts. Completion establishes only the tested Linux behavior and the
observed usefulness of this development pass—not spec completeness, cross-OS portability,
absence of prior knowledge, or a causal skill advantage.

Full documentary acceptance and the wider experimental/workflow qualification decisions remain
separate, deferred outcomes. The current spec's incomplete documentary review remains visible;
using it diagnostically cannot change its frozen acceptance result.

## Conventions and authorization

- Name the working conversation after its active milestone: `L01 — Implement and verify the Linux driver`
  for the immediate engineering pass. If the harness offers no
  thread-renaming control, state the intended title without claiming it was changed.
- Execution uses a topic branch and a PR; never push directly to main. This revision authorizes
  planning and its Claude review, not a new paid implementation run, hardware operation or push.
  Record the starting revision and pre-existing changes; review and fixes precede local commits.
  Use `driver-porting: L01 —` for engineering checkpoints and `driver-porting: PLAN —` for this revision.
- The current branch contains the completed M02a export and source-audit checkpoints. Preserve
  them; do not rewrite their outcomes. Fetch and inspect the current target branch before any PR.
- The previous procedure-trial-then-pair sequence is deferred. L01 comes first; models and a
  bounded implementation/repair effort limit still need selection before launching that work.
  A separate experimental budget, two attribution reviewers and an adjudicator are not L01 gates.
- Complete one session-sized milestone or named unit, verify, review, checkpoint, and stop for
  inspection. Aim to retain ample context for fixes and handoff; split before execution if the
  scope cannot fit. Record unfinished work accurately if context is compacted.
  Sizing refers to the operator's session; separately launched sessions have their own agreed
  effort limits. Split long-running operations at preserved
  launch/collection boundaries without calling an unfinished attempt complete.
- Default implementation review: `review-swarm` for code, schemas, access controls, and execution
  machinery. For a documentation-only milestone, use `consult` with Claude. These methods are
  authorized by this plan when executing an authorized milestone. Experimental semantic reviewers
  and failure-attribution reviewers are separately selected and budgeted; a code-review swarm is
  not a substitute for their independence. If a method is unavailable, record the failure and
  leave required review incomplete; do not silently replace independent review with self-review.
  In L01, code review must also include a source/requirement-based driver review by someone other
  than the implementer; the general code-review swarm alone does not establish hardware correctness.
- Evidence location: proposed `evidence/<milestone-or-unit-id>.md`, with sanitized commands,
  outcomes, review findings and resolutions, and references to retained private/raw artifacts.
  Keep only status, evidence link, and limitations here after moving completed detail to evidence.
  Record model cost, operator time, and human review effort separately: reviewer sessions, active
  time when measurable, elapsed time and adjudications; unknown effort remains unknown. Distinguish
  human reviewers from agent reviewers and avoid double-counting overlapping or resumed sessions.
- Raw sessions, captures, equipment identifiers and private records live in a run-ID root outside
  this public repository, following the practice-run convention. Public evidence files are
  publishable artifacts, not a temporary raw-log store. The private-path checker catches home
  paths only; also review hostnames/addresses, user/account identifiers, MACs, instrument serials,
  secrets and transcript contents before staging. Record evidence availability and retention.
- Every unit inherits tests for its changed surface, design conformance, regressions, privacy,
  and a pre-commit review artifact. No milestone is complete on the strength of tests merely added.
  A required unavailable check leaves it blocked; a budget exhaustion is retained, not erased.

## Current state and inputs

| Item | Observed state at the planning snapshot |
| --- | --- |
| Source investigation, spec authoring, board experts, implementation isolation helpers | Shipped skills and supporting tests; inspect their actual limits before reuse |
| Corpus and ledger | Frozen; 213 rows, 203 active; policy `enc28j60-1.4` |
| Documentary scoring | `prepare.py`, `score.py`, and `skills/board-expert/scripts/strict_accept.py` implemented; strict acceptance is documentary only |
| Practice candidate | Frozen hash in [PRACTICE-RUN.md](evals/enc28j60/PRACTICE-RUN.md); review incomplete and acceptance blocked |
| Reference build | Pinned Linux v6.12 reference kernel, module and Pi 4 DTB compiled after correcting case-colliding extraction; [evidence](evidence/M02a.md). No physical qualification implied. |
| Source sanitization | Export/transfer verified; five related-controller exclusions reviewed but not implemented; full audit and isolation incomplete. Deferred for L01. |
| Preparation gates and reconstruction design | Existing protocols retained for a later spec-only experiment; [R1a trial draft](evals/enc28j60/RECONSTRUCTION-TRIAL.md) remains unchanged |
| Paired generation, reconstruction, physical execution | Not run; no qualified runner or fixture established by these documents |
| Checks at `de2bb68` | All `.github/workflows/checks.yml` unit suites: 228 tests, one skipped, no failures; board checker: nine existing verification warnings. PR 68 CI also passed. These were observed before planning, not rerun by Claude and not evidence of driver behavior. |

Keep the corpus, ledger, scoring policy, fact lists, format, and lock unchanged. Additional
execution requirements live outside that lock. A correction to the answer key requires a new
benchmark version and explicit rescoring policy, preserving all old attempts.

## L01 — Implement and verify the Linux driver

**Priority:** active next milestone. A diagnostic engineering pass, not the frozen reconstruction
trial. Reuse the pinned ENC28J60 spec, Linux v6.12 source/toolchain and Pi 4 preparation. The
existing requirement ledger is a review checklist, not a new scoring project. Keep its locked
bytes and the historical spec intact; improvements go into separately versioned working copies.

Keep the working records small: one brief, one requirement-to-evidence table, a gap/repair log,
and source/build/test artifacts. Markdown and existing tools suffice; do not create generic
schemas, a runner framework, or a replay system before the driver can be exercised.
Choose the smallest feature scope that exercises the spec-to-driver-to-verification mechanism.
The Linux pass is a bounded proving step, not a prerequisite to completing every requirement
of this controller before useful work on another platform can start.

### First unit: implement, build and independently review

1. Write the short brief: target/revision assumptions, supported feature scope, build inputs,
   concrete acceptance checks, known fixture uncertainties, selected agent/model and a bounded
   implementation/repair effort limit. Reuse the trial's relevant requirements and reference
   preparation; do not wait for exhaustive documentary scoring. Establish expected outcomes
   from the ledger and source evidence before judging implementation output.
   The user selects the model and effort limit. The preparer and independent reviewer agree on
   the critical requirements and the few checks to challenge with deliberate defects before
   evaluating the driver. Justify feature exclusions against the relevant ledger requirements.
   If scope or checks change after observing results, version the brief, record why, and keep
   the original results visible. Keep driver code in a separate run working directory outside
   the skills repository; record its license and preserve notices on reused code before coding.
2. Start a fresh implementer with the spec and normal Linux development inputs. Ask it to work
   from the spec first and record missing information and assumptions. Permit deliberate,
   logged consultation of reference source, general documentation or operator clarification
   when needed. Record consulted inputs and any source-access uncertainty; source exposure
   limits claims about spec sufficiency but does not invalidate this engineering pass.
   Apply actual source-access restrictions if any separately exist; this public Linux pass
   does not waive requirements for a future cross-OS or restricted-source implementation.
   Record participant/context identities and source exposure so eligibility for later clean-side
   experimental roles can be checked. Reusing a model does not mean reusing an exposed context.
3. Build the driver with the pinned kernel/toolchain and preserve commands, configuration,
   artifacts and logs. Use fresh outputs and case-sensitive extraction with complete source
   identity checks, reusing the existing verifier where appropriate. The earlier extraction
   defect is a real build-integrity issue, independent of experimental isolation.
   L01 uses the ordinary upstream v6.12 tree, including the original target driver/header;
   record that access explicitly. It does not use the incomplete sanitized packet.
4. Have an independent reviewer compare the first driver revision against the relevant ledger
   requirements, source evidence and reference implementation. Cover initialization, receive
   and transmit paths, buffer management, shutdown and required errata/recovery behavior.
   Disagreement with the reference is investigated rather than automatically treated as a defect.
   Run the normal code-review procedure too. Record uncovered requirements and unavailable tests.

**First-unit checkpoint:** a buildable driver or a concrete blocked/failed attempt, independent
review findings, and a short list of spec gaps versus implementation errors. A buildable driver
with unresolved findings is ready for repair/testing, not declared correct. Do not finish the
1,010-path manufacturer audit or M02b harness qualification to reach this checkpoint.
At this checkpoint, explicitly decide whether the next useful step is Linux hardware testing,
a bounded repair, or applying the mechanism to another target. Physical Linux acceptance is
not a prerequisite for the latter; preserve the partial status and transfer only supported
conclusions. Do not let fixture delays trigger unrelated preparation work.

### Second unit: test real behavior and repair demonstrated gaps

- Confirm the actual module, power/wiring, board, boot path and test limits before hardware use.
  Reuse the Pi 4/netboot proposal; historical captures and a reference build do not verify wiring
  or prove the currently booted image. Record the reference/candidate module and image identities.
  Verify which built module is actually loaded and bound; only one driver controls the device
  at a time. Use a documented device-reset procedure between runs to prevent carried-over state.
- Exercise reference and candidate under the same documented configuration and test conditions.
  Changes to required kernel/fixture configuration require a corresponding reference check.
  Start with initialization and link, then bidirectional traffic, packet-size boundaries,
  receive-buffer wrap, repeated stop/start and selected observable error/recovery behavior.
  Select repetitions, traffic conditions and expected results before running each primary check.
  Record evidence that the intended condition occurred, such as actual frame sizes, a buffer
  wrap or the injected fault; a passing verdict without that evidence does not cover the case.
- Verify a few important checks by introducing relevant deliberate defects in disposable test
  copies. For example, a receive-pointer defect must be detected by a suitable wrap test; a
  required delay can be checked through source or trace evidence when timing cannot be faulted
  reliably on the fixture. Do not claim a test is effective because a mutation merely exists.
- Use the compact requirement-to-evidence table to distinguish tested behavior, source-reviewed
  requirements, failures, untested/unobservable cases and explicitly out-of-scope requirements.
  A successful ping is only a smoke test.
  Missing critical evidence keeps the corresponding acceptance decision incomplete.
- Repair demonstrated driver and spec gaps within the agreed effort limit, independently review
  affected changes, and rerun affected checks. Preserve original failures and each repair.
  Record whether a successful behavior was supported by the original spec, outside information,
  or remains unattributable. This is an engineering explanation, not blinded causal attribution.

**Accept L01:** the agreed behavior checks pass; relevant critical source-review findings are
resolved; representative negative controls actually fail as expected; hardware/boot identities
and unavailable coverage are recorded; and the final driver/spec revisions and evidence are
retained. Claims are scoped to those checks. If hardware is unavailable, finish the first unit
and report a partial result; do not substitute simulated or documentary evidence for physical
success. A bounded failure is useful evidence but is not L01 acceptance.

**Measure:** implementation, debugging, review and repair effort where available; model cost;
spec gaps discovered; tested requirements and residual uncertainty. This is one observation of
engineering usefulness, not a measured speedup without a comparison baseline.
L01 supplies scoped evidence toward R1 (requirement records), R5 (supported tests), R6 (physical
identity/results) and R8 (actionable repairs); it does not discharge the proposal's full
requirements or establish R2/R3/R4/R7 experimental acceptance.

**At each checkpoint:** inspect whether the spec/skill helped, what caused actual failures, and what the
next device or OS port needs. Choose further experiments only for an unanswered question worth
their cost. L01 outputs do not retroactively satisfy frozen trial or paired-run requirements.

## What is deferred from the immediate path

| Work | Disposition |
| --- | --- |
| Complete source sanitization, related-controller removals and harness isolation (remaining M02) | Preserve the current artifacts and audit findings. Resume only for an explicitly selected spec-only experiment; not required for L01. |
| Generic execution contracts and synthetic replay (M03–M04) | Use a brief, evidence table and ordinary build/test logs for L01. Build shared machinery only after demonstrated need. |
| Frozen spec-only trial and dual blinded attribution (M05/M08) | L01 permits logged outside assistance and repairs; keep these experimental conditions separate. |
| Fixture and meaningful test qualification (parts of M06–M07) | Keep the necessary hardware identity, expected outcomes and negative controls in L01; do not require the generic experimental infrastructure. |
| Paired authoring/implementation and complete documentary scoring (M09–M13, P01) | Optional follow-on to answer comparative questions; no immediate gate. |
| Test-authoring experiments and companion-skill ablation (M14–M15) | Exercise useful existing skills in L01; defer controlled comparisons. |
| Automated maintenance/invalidation and full pilot qualification (M16–M17) | Preserve versioned evidence now; defer general machinery and broader claims. |

## Deferred experimental plan

The remaining D1–D6 decisions, M01–M17/P01 dependency table, detailed milestone acceptance
criteria and wider follow-ons below preserve the earlier **experimental** plan. They apply
only if that work is explicitly resumed. None is an implicit prerequisite for L01. Deferred
means unfinished, not waived or complete. In particular, L01 cannot be scored or published as
an instance of the frozen spec-only trial. Completed evidence remains valid for its stated scope.

## Decisions and bounded investigations

| ID | Resolve before | Question and required evidence |
| --- | --- | --- |
| D1 | M02/M06 | Target board, architecture, toolchain and boot path: demonstrate the pinned reference kernel builds and the selected SPI host is usable; record fixture availability without assuming ordered parts arrived |
| D2 | Harness before M02; caps/roles before any paid run | Harness and version, models/settings, tools/access, per-stage resource caps, independent reviewers, adjudicator, and authorization; keep user choices pending until selected |
| D3 | M03/M04 | Exact record/schema placement and status mapping: inspect existing score/replay interfaces; approve a compatible sidecar design with separate result dimensions, no changed frozen denominator |
| D4 | M07/M08 | Which faults and traces can the fixture actually produce? Establish a finite capability inventory and report each unavailable check; do not infer recovery coverage from ordinary traffic |
| D5 | M14/M15 | Generated-test and companion-skill experiment conditions: freeze tasks, allowed inputs, independent expected outcomes, defect sets, and acceptance thresholds before inspecting outputs |
| D6 | M16 | Maintenance and feedback representation: select versioned records and conservative dependency invalidation without migrating legacy records into accepted status |

Investigations end with evidence-backed choices or explicit blockers, not open-ended exploration.
Do not invent commands, tool APIs, pin names, or equipment capabilities. A necessary material
design amendment returns to the design approval gate before dependent implementation.

## Sequence and dependencies

| ID | Outcome | Depends on | Status |
| --- | --- | --- | --- |
| M01 | Trial inputs located and design choices recorded | Existing trial draft; D1–D3 investigations | complete; launch blockers retained ([evidence](evidence/M01.md)) |
| M02 | Sanitized implementation environment and tested isolation | M01, D1 | deferred, incomplete; M02a source-export unit ([evidence](evidence/M02a-export.md)); baseline [build evidence](evidence/M02a.md) |
| M03 | Versioned execution contracts and result fixtures | M01, D3 | deferred |
| M04 | One complete synthetic execution/replay path | M03 | deferred |
| M05 | Frozen offline trial implementation | M02, M03, D2 authorization | deferred |
| M06 | Qualified physical fixture and reference smoke path | D1, approved hardware envelope | deferred |
| M07 | Independent offline and physical check qualification | M03/M04 for offline; M06/D4 additionally for physical | deferred |
| M08 | Trial results and independent attribution | M05/M07-offline for partial result; M07-physical for full result; D2 | deferred |
| M09 | Post-trial paired design freeze | M08-offline; retain all trial findings and physical deferrals | deferred |
| M10 | Two frozen specifications | M09, D2 author authorization | deferred |
| M11 | Both documentary reviews completed before either score | M10, D2 reviewer authorization | deferred |
| M12 | Two frozen implementations, no evaluation feedback | M10, M02 as refrozen by M09, D2 implementer authorization | deferred |
| M13 | Paired execution, attribution, and separate results | M08-physical, M11, M12, physical check qualification from M07/M09 | deferred |
| M14 | Independent assessment of implementer-authored tests | M02/M04 environment; M05/M07-offline for diagnostic trial, or M13 for paired inputs; D5 and separate authorization | deferred, design-gated |
| M15 | Companion-skill use and bounded repair demonstrated | M05/M07-offline for diagnostic use; M08 or M13 attribution for repair; D5 and separate authorization | deferred, design-gated |
| M16 | Maintenance/feedback invalidation and replay | M03, M04, D6; reconstruction prioritized | deferred, design-gated |
| M17 | Final pilot verification and qualification decision | M13–M16 and required physical evidence | deferred |
| P01 | Fresh review of the same frozen practice spec | Own D2 budget/reviewers | deferred, independent work |

M06 can proceed alongside M01–M05 when authorized. Hardware delays need not block offline
qualification, a partial trial report, M09–M12, diagnostic M14/M15, P01, or bounded M16 design work.
M09 can proceed only when the offline trial has established its declared procedure-readiness
criteria; it cannot call the physical trial complete. Freeze physical check definitions, record
qualification as pending, and qualify tests before inspecting candidate execution results.
Later changes require a new version and a rerun policy for reference and both candidates.
M11 and M12 may overlap only with enforced information
separation. This sequencing does not require shared contexts or simultaneous agent sessions.

## Design coverage

R labels refer to [VALIDATION-PROPOSAL.md](VALIDATION-PROPOSAL.md#1-outcome-and-scope).
Coverage below names the pilot subset and leaves broader obligations visible.

| Requirement | Milestones and verification | Remaining scope outside pilot |
| --- | --- | --- |
| R1 identities/applicability/dispositions | M01, M03, M16; stable IDs, full scoped inventories, stale/unknown rejection | General board/SoC identity vocabulary |
| R2 independent completeness | Existing frozen ledger; M11, P01; whole-prose audit and ledger coverage | New independently authored ledgers per device |
| R3 source access and public/private separation | M02, M04, M17; deny-access and private-input negative fixtures | Authorized private runs and full vendor workflow |
| R4 accuracy and clean-room gates | M02, M11, M15; independent review and unchanged acceptance policy | Generalized strict acceptance for legacy board specs |
| R5 independently supported tests | M03, M07, M14; expected-outcome review, mutations, known-good controls | Additional devices and unobservable faults |
| R6 physical identity/freshness | M04, M06–M08, M13; wrong-image, stale/truncated capture and cleanup failures | Each additional board and fixture |
| R7 comparison and maintenance | M09–M13, M16; paired conditions, preserved attempts, dependency invalidation | Repeated-device campaigns and optimized replay |
| R8 actionable optional feedback | M15, M16; bounded repair and recorded feedback disposition | Full feedback automation and private expert workflow |
| R9 OS-neutral core | M03, M04, M17; target-specific adapter boundary and interface review | Separate Fuchsia follow-on |

The reconstruction protocol additionally requires separate generation and implementation briefs,
trial/pair separation, no feedback until both drivers freeze, two independent failure attributions,
and source-isolation auditing. M01/M02/M09 establish these; M10–M13 verify them in use.

## M01 — Make trial preparation executable

**Coverage/dependencies:** R1/R2/R5; existing R1a draft, D1–D3. No paid implementation.
**Steps:** Retrieve the historical spec without repairing it; verify its recorded size/hash.
Inventory current scripts and artifact locations. Resolve target/build inputs and general OS
documentation. Complete separate allowed-input and exclusion inventories, neutral brief, model
and budget placeholders, source-access controls, scope, and check definitions in a versioned
manifest outside the documentary lock. Record which choices remain launch blockers.
**Accept:** Every preparation field has a value or a stage-specific blocker; candidate identity
matches; no trial result can be labeled a paired arm; generation is explicitly not part of trial.
The versioned manifest declares the offline procedure-readiness criteria for M09 before the
trial launches; they must not be chosen after its result is visible.
**Verify/review:** Check hashes, links and ledger references; review trial definitions against
RECONSTRUCTION.md and source locators, including ambiguity and reference defects.
**Sizing:** One input/decision record; if board investigation expands, checkpoint it as M01a and
finish the manifest in M01b. [Preparation manifest](evals/enc28j60/reconstruction/M01-PREPARATION-v1.md)
and [evidence](evidence/M01.md) now record verified custody, D1–D3 investigations and launch
blockers; Claude review confirmed the final text after fixes. M01 is complete at this checkpoint.
No build, isolation or physical result is implied.

## M02 — Build and prove the isolated environment

**Coverage/dependencies:** R3/R4; M01 and D1. Excludes any implementer run.
**Steps:** Export a sanitized pinned OS tree and minimal shared integration scaffolding; remove
device sources, bindings, metadata, archives, history and caches. Inventory every outside-spec
fact. Pin tools, general API documentation and neutral instructions. Adapt and test the existing
hook/policy/audit helpers; do not load the treatment-specific consumer prose into benchmark runs.
**Accept:** A neutral placeholder builds offline; forbidden file/network/subprocess/symlink/cache
access fails in the selected harness; output/access records are retained; scanner settings and
overlap dispositions are frozen. Mechanical scans alone do not establish isolation.
**Verify/review:** Positive compilation/read controls and negative access canaries; regression
tests for changed helpers. Review environment mounts, provider transport and inherited context.
**Sizing:** Separate M02a sanitized-build and M02b harness-isolation sessions, each with tests and
review. [M02a evidence](evidence/M02a.md) records the incomplete entry/build checkpoint and
netboot/wiring decisions; the [source-export unit](evidence/M02a-export.md) adds archive
transformation and transfer verification. Sanitized build and full isolation remain open.
M02b evidence is still proposed as `evidence/M02b.md`.

## M03 — Freeze execution contracts without changing documentary scoring

**Coverage/dependencies:** R1/R5/R6/R9; M01/D3. No hardware claims.
**Steps:** Propose `evals/enc28j60/reconstruction/` for pilot contracts and fixtures; reuse existing
IDs and archive conventions. Define manifest, test contract, result, artifact and attribution
records; explicitly translate reconstruction statuses to the proposal's execution dispositions.
Record independent authority for each expected outcome, tolerance and decision rule. Keep new
execution requirements separate from the frozen ledger and OS-specific adapters out of the core.
**Accept:** Valid records retain independent spec/implementation/hardware results; missing IDs,
duplicate IDs, unresolved applicability, incompatible versions and dangling evidence are rejected
or explicitly blocked. An execution pass cannot manufacture documentary acceptance.
Review an explicit status mapping: retain the original protocol label alongside the canonical
execution disposition; awaiting-fixture/blocked never becomes not-applicable. Keep unresolved
attribution separate from execution verdicts. No lossy mapping may hide missing coverage.
Keep `score.py`, `prepare.py`, `ledger_check.py`, and `strict_accept.py` unchanged for this
sidecar addition. Any unavoidable later tool change requires explicit versioning and staleness
analysis; demonstrate archived results replay with their own archived tool copies. The five
locked artifacts remain unchanged; their corrections require a new benchmark revision.
**Verify/review:** Schema and transition fixtures, including unknown/unavailable versus failure;
review compatibility with `score.py`, `strict_accept.py`, and preserved historical attempts.
**Sizing:** Contract and fixtures only, one session; resolve D3 before coding. Evidence proposed
`evidence/M03.md`; status pending.

## M04 — One synthetic attempt from preflight through replay

**Coverage/dependencies:** R3/R6/R7/R9; M03. Excludes physical validation.
**Steps:** Implement the smallest pilot runner/adapter path at M03's approved location. Record
exclusive ownership, run identity, preflight, execution timeout, capture, cleanup and immutable
attempt archive. Refuse output collisions and missing artifacts; replay deterministic decisions.
**Accept:** A simulated successful observation passes; wrong image, stale log, truncated capture,
missing tool, unavailable channel and untrusted target-only PASS cannot pass. Cleanup failure
quarantines the fixture abstraction. A retry gets a new linked attempt.
Inherit M03's tool-byte compatibility and archived-replay requirements; a new execution runner
must not silently alter documentary decisions.
**Verify/review:** Integration tests through the complete path, injected failures at each state,
archive/replay test and a private-input publication rejection. Review evidence identity and error
paths. CLI/API commands remain to be defined under D3, not asserted here.
**Sizing:** One fake adapter and one contract only; split archive/replay if needed. Evidence
proposed `evidence/M04.md`; status pending.

## M05 — Run and freeze the offline procedure trial

**Coverage/dependencies:** R4/R5; M02/M03 and explicit D2 launch authorization.
**Steps:** Package the exact old spec and permitted inputs; start one fresh implementer with
recorded settings. Allow identical declared offline checks only. Stop on completion, blocker or
cap; freeze code, prompts, logs, assumption/gap records and actual resource use. Audit access and
scan overlap before interpretation. No source or reviewer feedback goes to this implementer.
**Accept:** A complete preserved attempt exists even if the code does not build; exposed or
incomplete isolation is explicitly disqualifying for a spec-only interpretation. Compile success
is reported independently from hardware behavior and spec quality.
**Verify/review:** Reproduce build result in the sanitized environment and audit inputs, stopping
condition and output identity. Do not repair the spec or candidate in this attempt.
**Sizing:** One capped implementation attempt; evidence proposed `evidence/M05.md`; pending.

## M06 — Qualify fixture and reference observation

**Coverage/dependencies:** R6; D1, equipment, explicit hardware envelope/authorization.
**Steps:** Record device revision evidence, wiring, SPI configuration, image/firmware/tool pins,
traffic-peer role, capture settings and reset procedure privately as needed. Establish the
reference build/load/bind and externally observed smoke test. Verify exclusive access, fresh
capture window and booted-image identity using M04's adapter contract when available.
**Accept:** Repeatable cold starts and externally observed reference traffic; a target printout
alone cannot pass. Channel suitability is scoped to an observation, not universal hardware trust.
**Verify/review:** Positive reference control; deliberately stale/wrong-identity records refused;
cleanup and recovery exercised within the approved envelope. Record every attempt and failure.
**Sizing:** One host/device/peer configuration; board bring-up may require an incomplete checkpoint.
Evidence proposed `evidence/M06.md`; status pending until real equipment checks run.

## M07 — Qualify each independent behavior check

**Coverage/dependencies:** R5/R6; M03/M04 for offline qualification, M06/D4 for physical checks.
No candidate execution inspection before the affected test is qualified.
**Steps:** Implement the frozen T01–T07 design from the trial record, correcting the design only
through versioned, reviewed changes. Inspect cited source evidence. Exercise each test against
the reference and representative evaluator-owned mutations; report false alarms on known-good
controls, invalid mutations and undetected faults. Capture actual boundary/fault conditions.
**Accept:** Each test has an independently supported decision rule and measured detection result;
unprovokable faults remain unavailable. Reference disagreements receive adjudication rather than
an expectation edited to make the reference pass. Primary checks freeze before candidate results.
**Verify/review:** Test-code unit/integration checks and physical evidence for physical claims;
review discriminating power and observability, including frame lengths, wraps and recovery order.
**Sizing:** M07-offline covers T01 build/registration checks, source-review criteria, and host or
simulated mutation checks; split by check family and record actual units before starting if needed.
It does not claim silicon behavior. M07-physical contains one check
or tightly coupled pair per session, `M07-T01` through `M07-T07`, including T01 load/bind.
Each unit has its own proposed evidence file. Offline completion can unblock a partial trial;
M07 as a whole remains incomplete for missing required physical checks.

## M08 — Evaluate the trial and attribute failures

**Coverage/dependencies:** R4/R5/R6; M05/M07-offline and D2 for partial results;
M07-physical additionally for physical results.
**Steps:** Execute frozen candidate checks with controlled reset/order and preserve unsuccessful
attempts. Give two fresh attribution reviewers requirement evidence, spec passages, candidate
behavior and reference behavior, never each other's decisions. Adjudicate conflicts; report
spec gaps, implementation mistakes, environment limits, reference discrepancies and justified
verification requirements separately. Log procedure changes for M09; no silent repairs.
**Accept:** Requirement-linked results and both independent judgments retained; disagreement is
unresolved rather than a binary failure. Any repair is separately versioned and budgeted.
**Verify/review:** Replay result decisions; check all T01–T07 dispositions and actual resource use.
Review specifically whether facts deferred to hardware were recoverable from permitted evidence.
**Sizing:** M08-offline comprises offline execution, two independent source/build/procedure
readings and reconciliation in separate sessions. It records every physical check as awaiting
fixture or qualification and states whether the implementation procedure is ready for M09.
M08-physical later supplies execution, two attributions and reconciliation in separate sessions.
Evidence proposed per unit; status pending. A partial report does not complete the physical trial.

## M09 — Freeze the paired experiment after the trial

**Coverage/dependencies:** R2/R3/R5/R7; M08-offline, with physical limitations explicit.
**Steps:** Version trial-informed procedure changes. Freeze shared generation scope and general
OS inputs separately from implementation wiring/binding facts. Write the baseline prompt before
the treatment prompt. Pin skills, environments, checks, access rules, scanner rules, reviewer
protocols, resource caps and attribution procedure before paired candidates are inspected.
**Accept:** Trial artifacts cannot become an arm; both planned conditions differ only as ARMS.md
permits; unknown settings and material mismatches have explicit unpaired dispositions. Resolve
run-critical decisions while retaining unresolved execution limitations honestly.
Record evaluator exposure to the practice candidate, its reviews and treatment instructions.
Use a fresh baseline-prompt author context that has not read a skill-produced ENC28J60 spec or
its review, and independently audit the prompt for treatment-specific structure. If this cannot
be achieved, disclose the exposure and investigate the prompt; actual treatment leakage invalidates
the intended baseline. Familiarity alone is a recorded limitation, not proof of leakage.
Freeze the semantic-review batching plan before launching reviewers: expected scale, named units,
disjointness rules and per-batch completeness audits; adapt counts to each frozen inventory.
**Verify/review:** Run corpus, ledger-lock and author-manifest gates; compare input inventories;
review information flow and precommitment. Requalify affected M07 tests before execution use.
**Sizing:** One freeze record and prompt pair; evidence proposed `evidence/M09.md`; pending.

## M10 — Generate and freeze the specification pair

**Coverage/dependencies:** R2/R7; M09, D2 author authorization.
**Steps:** Execute ARMS.md in separate contexts with identical recorded settings; send only the
pins-only author manifest, never the interpretive corpus manifest or ledger. Preserve exact
prompts, input/output hashes, source access records and cost. Assign opaque candidate IDs.
**Accept:** Both specs frozen; failed/budget-exhausted attempts retained; any material condition
difference makes the comparison unpaired. No retrospective prompt reconstruction.
**Verify/review:** Source pin checks before runs, packet/access inspection, artifact identity and
pairing review. Source-access controls are stage-specific: authors legitimately read sources.
M10c carries the evaluator-exposure and baseline-prompt audit record from M09 into the report.
**Sizing:** M10a and M10b are separate generation sessions followed by M10c pairing audit;
proposed evidence per unit. Status pending.

## M11 — Review both specs before scoring either

**Coverage/dependencies:** R1/R2/R4; M10/D2. Preserve frozen scoring and citation rules.
**Steps:** Audit each entire spec into a complete, nonoverlapping claim inventory. Prepare neutral
packets with `prepare.py`; perform fresh accuracy readings and ledger-to-spec coverage under
SCORING-RUN.md. Preserve full fact/unit prose and disagreements. Finish both reviews before
running either score; archive and replay each attempt. Report the existing OS-integration citation
and denominator limitation without inventing a new precision partition.
**Accept:** Reviews account for every claim and ledger requirement; unavailable evidence remains
pending; no inherited contaminated verdicts. Completed measurement can conclude acceptance is
blocked. Incomplete semantic review leaves this milestone incomplete, regardless of arithmetic.
**Verify/review:** Inventory/packet gates, independent access records, scorer tests and archived
replay. Review quotes and source locators as well as schema validity.
**Sizing:** Create named units per candidate for inventory, each accuracy reader, coverage, and
reconciliation; split large inventories into stable disjoint batches before launch. Each batch
has a completeness audit; reviewers never receive another reader's findings. Score-pair is the
last unit. Evidence proposed per named unit; status pending.
Use the historical practice workload as a sizing warning: 194 roster rows, 670 facts and 522
active claim records were reviewed, and a mapping invocation exhausted its budget. These are
historical counts, not new frozen denominators or prescribed batch sizes. Record actual batch
counts and coverage before each reviewer launch; reconcile the full prose across batch boundaries.

## M12 — Implement both frozen specs without evaluation feedback

**Coverage/dependencies:** R3/R4/R7; M10, refrozen M02 environment, D2 authorization.
**Steps:** Execute separate fresh implementations using opaque spec IDs and identical neutral
brief, environment, model/settings, caps and permitted checks. Record gaps and assumptions; no
citations fetched, source recovered, scores disclosed, or facts added through clarifications.
Freeze both drivers and logs before evaluator comparison or any repair.
**Accept:** Both attempts preserved and access audited; material differences make implementation
unpaired independently of generation pairing. Style-based inference of arm identity is a limit.
**Verify/review:** Repeat the declared build check, scan/audit access and compare input/settings
manifests. Review artifact and feedback boundaries without sending findings to implementers.
**Sizing:** M12a/b implementation sessions, M12c pairing/access audit; proposed per-unit evidence;
pending. May overlap M11 only with enforced separation.

## M13 — Produce the paired reconstruction result

**Coverage/dependencies:** R4–R7; M08-physical/M11/M12 and independently qualified M07/M09 checks.
**Steps:** Run identical reference/candidate scenarios with recorded reset, order and repetitions.
Obtain two independent attributions without arm labels or each other's findings; adjudicate
disagreements. Cross-tabulate documentary coverage and implementation outcomes. Report build,
behavior, access, omissions, implementation errors, unresolved cases, cost and time separately.
**Accept:** Reproducible per-check results with limitations; no blended quality score, no discarded
failed attempt, no claim that one pair estimates variability or proves absence of prior knowledge.
**Verify/review:** Replay, both reviews, evidence availability and per-requirement reconciliation;
check capture freshness and hardware identity across candidates, not merely within one run.
**Sizing:** Separate execution per implementation, two attribution sessions and one synthesis
unit; proposed evidence per unit. Pending; physical gaps prevent full execution completion.

## M14 — Measure whether agents can write meaningful tests

**Coverage/dependencies:** R5; M02/M04 supply the build/execution environment.
Use M05/M07-offline for a diagnostic trial using the old spec, or
M13 for a study of paired inputs; D5 and separately approved design/budget in either case.
**Steps:** Freeze a small test-authoring task, permitted inputs and an independently prepared
defect/control set. Have a fresh implementer derive tests from the spec, then assess those tests
against the hidden defects and valid alternative implementations. Keep evaluator tests and
expected judgments out of the author packet. Start with one bounded normal/boundary/recovery slice.
**Accept:** Report detected, undetected and invalid mutations, false alarms, requirement coverage,
and resource use. A test that merely repeats a mistaken spec is not independent corroboration.
Do not claim success from test compilation or the existing evaluator-authored test results.
A trial-spec test-authoring result cannot become a paired arm or a skill-effect estimate.
**Verify/review:** Validate defect/control correctness independently, then execute all generated
tests against them; physical claims need qualified hardware. Review task leakage and overfitting.
**Sizing:** M14a approved design, M14b authoring, M14c assessment; evidence proposed per unit.
Status pending/design-gated; exact metrics and thresholds must precede candidate tests.

## M15 — Validate companion-skill use and bounded repair

**Coverage/dependencies:** R4/R5/R8; M05/M07-offline for diagnostic usability, or M13 for paired
inputs; attributed M08 or M13 failures for repair; D5 and separate procedure/budget approval.
**Steps:** Reuse `board-expert`, authoring/implementation skills and `spec-verifier`; avoid a new
umbrella skill without demonstrated reuse. Freeze representative spec-navigation, tool-selection,
implementation and diagnosis tasks. Test correct revision selection, permitted-source use,
expected-versus-observed reasoning, and missing-tool/evidence handling. Demonstrate one separately
versioned repair through the appropriate source-reader/implementer boundary and add a regression
case for any skill correction. Stop after two failed accuracy checks on the same section, as the
proposal specifies, with unresolved findings and cost preserved.
**Accept:** Usability and failure-handling evidence for the declared tasks; successful source
reading cannot contaminate a clean-side repair implementer. No change to primary benchmark
specs, code or scores. A failed repair remains blocked and is not counted as qualification.
Diagnostic usability on the old spec cannot establish a skill effect or become a paired arm.
Skill changes from early diagnostics must precede M09's freeze; later changes require a new
experimental version and cannot be spliced into the frozen pair.
**Verify/review:** Independent task expectations, negative cases, before/after evidence and
reverification of affected requirements. Review tool instructions against actual tool interfaces.
**Sizing:** M15-diagnostic covers one approved usability task family per session. M15-repair
separately exercises the bounded repair using attributed failures. Separate skill edit/review
from fresh task evaluation. Evidence proposed per task; pending/design-gated. No new general
interface assumed.

## M16 — Preserve confidence when inputs change

**Coverage/dependencies:** R1/R7/R8; M03/M04/D6. Lower priority than reconstruction; no hardware gate
on purely documentary work. Excludes optimized replay and full vendor automation.
**Steps:** Define compatible evidence sidecars and a small latest-status index. Preserve every
attempt before replacing latest status. Conservatively invalidate dependents when sources,
applicability, policy, spec, code, tests, expected outcomes or fixture change. Record expert
feedback with target IDs, evidence, disclosure constraints and accepted/rejected/unresolved
disposition; reproduce one supported correction and suspend affected acceptance.
**Accept:** Changed or unavailable evidence cannot retain unqualified acceptance; incompatible
policy versions cannot be compared; unrelated capabilities stay scoped; old results still replay.
Legacy verification records remain legacy, never upgraded by format conversion alone.
Apply M03's versioning/staleness rules to any change in archived documentary tools; demonstrate
old attempts still replay using their archived versions, rather than attaching new hashes to old
judgments.
**Verify/review:** Synthetic dependency-change matrix, missing archives, rejected feedback,
critical supported feedback, and replay of old attempts using archived tools. Review authorization
of feedback and conservative invalidation before attempting optimization.
**Sizing:** M16a record/invalidation design and tests, M16b feedback and replay; proposed evidence
per unit; pending/design-gated. Optional verifier integration is a separately justified extension.

## M17 — Final verification and handoff

**Coverage/dependencies:** All pilot subsets of R1–R9; M13–M16 and required hardware evidence.
**Steps:** From a fresh session/environment, follow the published instructions to locate inputs,
replay documentary and execution decisions, exercise a selected qualified physical path, and
demonstrate a dependency change withdrawing acceptance. Verify companion-skill tasks and a
failure/repair history. Audit every requirement-to-evidence link and all outstanding limitations.
**Accept:** Separate evaluation-complete and workflow-qualified decisions with reasons; no
missing mandatory check hidden as a successful skip. Publish only sanitized evidence and identify
the next authorized scope. Negative results may close the campaign but not a qualification gate.
Report measured human-review effort per stage as a baseline for any future reduced-review claim;
unknown effort is not zero. OS neutrality has interface-review evidence only in this pilot,
not a demonstrated second-OS port.
**Verify/review:** All configured CI checks, replay, fresh hardware observation, cross-milestone
identity/isolation/version tests, and review-swarm against this plan's full coverage matrix.
**Sizing:** M17a offline replay/audit, M17b physical closure, M17c final review/report, separately
checkpointed. Proposed per-unit evidence; status pending.

## P01 — Independent historical practice re-review

Re-review the same frozen spec with fresh reviewers and neutral packets, preserving all old
attempts. Follow M11's inventory, independent reading, coverage and replay gates in separate
session-sized units. Pending D2 authorization; does not block the reconstruction trial or replace
either paired arm. A later correction belongs to a new attempt/version, never the old record.
Record reviewer identities, contexts and exposure. Use fresh contexts for M11 and disclose any
reviewer-model/person reuse across P01 and M11 or between arms. Do not carry P01 judgments into
either paired review. Match reviewer assignment across arms and freeze that assignment in M09;
different model families per arm would introduce another experimental difference. Blinding
limits remain explicit even with fresh contexts.
Prefer a pool without prior candidate exposure when equally capable reviewers are available;
choose the pool before matching its assignment across arms and disclose remaining limitations.
Proposed evidence `evidence/P01.md`; status pending.

## Checks to use during execution

From the repository root, run registration/privacy checks and `git diff --check` for documentation.
For code changes, run the affected suites and the configured `.github/workflows/checks.yml` steps
before pushing. Known commands include:

```sh
python3 utilities/check-skill-registration.py
python3 utilities/check-no-private-paths.py
python3 -m unittest discover -s plugins/driver-porting/skills/os-investigator/tests
python3 -m unittest discover -s plugins/driver-porting/skills/cleanroom-implementer/tests
python3 -m unittest discover -s plugins/driver-porting/skills/board-expert/tests
python3 plugins/driver-porting/skills/board-expert/scripts/spec_check.py plugins/driver-porting/skills/board-expert/specs --stubs-from plugins/driver-porting/skills
uv run --with pyyaml python3 -m unittest discover -s plugins/driver-porting/evals/enc28j60/tests
uv run --with pyyaml python3 plugins/driver-porting/evals/enc28j60/author_manifest.py --check plugins/driver-porting/evals/enc28j60/author-manifest.yaml
uv run --with pyyaml python3 plugins/driver-porting/evals/enc28j60/ledger_check.py plugins/driver-porting/evals/enc28j60/ledger.yaml --lock plugins/driver-porting/evals/enc28j60/ledger.lock
```

Before generation, from `plugins/driver-porting/evals/enc28j60/`, run
`python3 corpus_check.py` with source access: require zero drifted pins. The other ARMS.md gates
must pass too. Scoring commands and expected exit codes remain authoritative in
[SCORING-RUN.md](evals/enc28j60/SCORING-RUN.md). A valid blocked result is not a tool failure or
permission to claim acceptance. Build, runner and hardware commands are discovered and recorded
in the relevant milestone (L01 for the active engineering pass); none exist by assertion in this plan.

## Conditional follow-ons and unresolved wider scope

| Work | Entry decision and acceptance experiment |
| --- | --- |
| Repeat pairs and test larger devices | Review pilot usefulness and cost; freeze sample plan before runs. Qualify a precisely scoped FEC target only after matching documents and execution setup are available. Measure variability before claims of stable advantage. |
| Dedicated reusable validation/companion skill | A second device demonstrates reuse, as VALIDATION-PROPOSAL section 3 requires; extract shared procedures instead of copying the existing skills. |
| Reduce routine human review | Use M17's effort baseline; approve a held-out comparison of reduced-review decisions against independently adjudicated good/bad cases. Measure false acceptance, false rejection, unresolved cases and effort before changing a review gate. No current acceptance rule is waived by this goal. |
| Held-out transfer | Freeze skill tuning before independent held-out tasks; separately approve device, sources, model/execution reference and budget. Historical OpenTitan proposal is a candidate, not an executable task in this plan. |
| Fuchsia UART | Name board, image, peripheral, fixture and external observation method; design in the companion Fuchsia package and verify against its pinned source. No generic plan invents its APIs. |
| General strict board-spec acceptance | Approve stable claim IDs, critical-set mapping and migration design; test missing/stale/unresolved critical claims. Existing `--require-verified` is not this feature. |
| Integrate optional verifier coverage pass | Decide value after paired review experience; preserve two-direction measurement and frozen scoring contracts. Not blocked on hardware availability. |
| Vendor overlays and private evidence | Approve the proposal's deferred stage E design, source authorization and publication policy; test conflicting facts and private/public separation before use. |
| Campaign infrastructure and optimized replay | Approve deferred stage F after repeated runs demonstrate need; retain conservative invalidation and complete attempt history from the pilot. |

These are required decisions before broadening the project's claims, not hidden implementation
authorization. Derive session-sized milestones after the corresponding design gate, rather than
pretending the pilot plan completes an unspecified platform-wide system.

## Discovered work and backlog

- **M02/M05 input-transfer identity:** M02a found that a Mac extraction merged 13 pairs of
  case-distinct Linux paths even though all M01 spot checks passed. The original archive and
  corrected ext4 extraction matched the pinned Git tree. Require complete tree/manifest
  equality after every sanitized export or packet transfer; retain archives when staging on
  case-insensitive filesystems. This is a build/input gate, not a change to the frozen ledger.
- **M11 prerequisite — scoring-contract heading:** `SCORING-RUN.md` still titles its review
  contract `enc28j60-review-2`, while `score.py` declares `enc28j60-review-3` and the same document
  describes version 3 later. Correct the heading in a reviewed documentation change before
  freezing reviewer instructions; use the actual script/schema and version-3 contract meanwhile.
  No change to the locked policy is implied.
- **Historical status text:** DESIGN.md and VALIDATION-PROPOSAL.md contain older ledger/scorer
  status descriptions; DRIVER-QUALITY.md describes the controlled evaluation now deferred.
  Current pilot artifacts and this priority revision govern; refresh those descriptions when publishing
  the next status update, without changing their design decisions or calling new work complete.
- Record further discoveries with impact and owner milestone. A completion blocker stays in its
  milestone; this backlog cannot be used to waive a failed acceptance criterion.

## Next session

- **Start L01's first unit.** Prepare the short Linux engineering brief and requirement-to-evidence
  table from the existing spec, ledger and reference build. Obtain the user's selection of implementer/model and
  bounded effort limit before launching a separate implementation session. Then implement,
  build and independently review the driver. Do not resume the manufacturer-path audit first.
- Reuse [reference-build evidence](evidence/M02a.md), including the corrected case-sensitive
  source identity. Pi 4/netboot and module wiring remain proposals pending physical confirmation;
  qualify those before the hardware unit, not before offline implementation/review.
- Preserve the [export](evidence/M02a-export.md) and
  [related-controller audit](evidence/M02a-source-audit.md). Five removals/edits are reviewed,
  not implemented; 1,010 other `microchip` name/content matches and broader source review remain
  pending for the deferred experimental path. No implementer packet was approved by that audit.
- The historical spec remains diagnostically usable but documentary acceptance is still blocked.
  Version working repairs separately; never edit the frozen corpus, ledger or historical score.
- This revision is planning authorization. No implementation experiment, hardware launch or push
  occurred. Record actual implementation/hardware authorization at the relevant launch boundary.
- Checkpoint the first useful Linux result and stop for inspection before expanding scope.
