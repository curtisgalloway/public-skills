<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Trial preparation manifest: M01 version 1

## Terms

- **Preparation manifest** — an input and decision record; not permission to launch a run.
- **Sidecar** — a separate execution record linked to documentary artifacts by their hashes.
- **Fixture** — the board, controller module, wiring, peer, and capture equipment.
- **Qualification** — demonstrating a check works using reference cases and deliberate defects.

See the [glossary](../../../../../GLOSSARY.md). This evaluator-only record implements
[M01](../../../IMPLEMENTATION-PLAN.md#m01--make-trial-preparation-executable).
Do not supply it, its pin inventory, or its evidence record to an implementer.

## Identity and custody

- Experiment: `enc28j60-reconstruction-trial-01`; preparation revision `M01-v1`.
- Kind: historical-spec procedure trial. No generation, paired arm, repair, or fresh documentary
  review is included. Trial artifacts can never become either later paired arm.
- Starting repository revision: `3d7eb2913551e0d462f0e22f4541c970b25af679`, clean topic branch.
- Predecessor: [R1a draft 1](../RECONSTRUCTION-TRIAL.md), preserved byte-for-byte; its check
  definitions, feature scope, exclusions, and attribution rules are incorporated below.
- Candidate: historical run `enc28j60-practice-20260920-01`,
  `generation/workspace/output/candidate.md`; 120,897 bytes;
  SHA-256 `516b7854e97fca4577d67922d2a49d174a80ebae9df9956d3a0738788f76bd06`.
  Read-only byte hashing matched the generation archive and both `scores/attempt-01/candidate.md`
  and `scores/attempt-02/candidate.md`. No content inspection or repair was part of retrieval.
- Archive locator: private driver-porting run store, identified by the historical run ID and
  relative paths above. Available on the preparation host on 2026-09-20; no off-host retention
  or indefinite availability claim. Recheck availability and digest when packaging M02 inputs.
  Supply a byte-identical copy under the neutral name `spec.md`, never the archive directory.
- Documentary state: incomplete review and blocked acceptance, unchanged. This is an exploratory
  trial despite that state; completing it cannot manufacture spec or workflow qualification.
- Pin inventory: [M01-INPUTS-v1.json](M01-INPUTS-v1.json), metadata only, outside the documentary
  lock. It records the lock digest, five locked file digests, current documentary/control tools,
  candidate copies, archived result/tools/reference files, retrieved board/configuration evidence,
  and general API documentation. Repository revision identifies the starting snapshot; the new
  brief template is identified by its digest and the M01 checkpoint, not by that earlier commit.

The preparer has read the historical report and evaluator material. This trial design is not
candidate-blind. No paired candidates exist in this work. A fresh context and input export are
mandatory for implementation; this preparer cannot be the clean-side implementer.

## D1: target, build, and general OS inputs

The user confirmed that the controller modules have arrived and selected Raspberry Pi 4 Model B
for this trial. The proposed build architecture is arm64; exact board revision and fixture
qualification remain pending.
The pinned source supports its SPI/GPIO path; Pi 5 at that pin lacks the RP1/SPI device-tree
support needed for the straightforward header-SPI setup. The bounded investigation and sources
are in the M01 evidence record. Receipt is not evidence of module pinout, B7 revision or behavior.
Use Linux v6.12 at `adc218676eef25575469234709c2d87185ca223a` as already selected by the corpus.
A vendor kernel carrying a similar version string is not an interchangeable reference.

The local source checkout inspected during preparation did not contain that exact commit.
The archived `enc28j60.c` and `enc28j60_hw.h` do match the corpus pins. These two files are
enough to establish reference-file custody, not a full kernel checkout or a successful build.
Start from upstream arm64 `defconfig`, an AArch64 GNU/Linux toolchain, and microSD boot with
explicit Image/DTB selection; these are qualification candidates, not working recipes.
Build environment, compiler/binutils versions, dependency/image digests, configuration,
boot firmware, root filesystem, SPI binding, IRQ/reset routing, and build commands are
**B01/B02 blockers**, not guessed working values. M02 must obtain the exact tree and demonstrate
the reference build, then build a sanitized placeholder with the same configuration.

Seven upstream API documents at the exact commit were retrieved and hashed: SPI, network-device
lifecycle, memory allocation, mutexes, generic interrupts, external modules, and driver lifecycle.
Their source paths and hashes are in the pin inventory. This is the selected initial subject
list, not an audited, self-contained implementation packet. A text search found no `enc28j60`
or `microchip` matches in these files. That narrow search is not a semantic leakage audit.
SPI and interrupt documents contain `kernel-doc` directives that pull API documentation from
other files. M02 must render or explicitly export those dependencies from the pinned sanitized
tree, audit examples and transitive content, and hash the final supplied documents. Raw `.rst`
stubs cannot be called complete API documentation. Necessary additions need their own inventory,
audit, and pin before launch; no links may be followed from the implementation environment.

## D2: isolation investigation and decision

Observed local CLI: Claude Code `2.1.278`; a container executable is available. Neither observation
qualifies an execution environment. Harness selection is an operator/D2 decision at M02 entry
(**B03**); M02 then validates it before implementation. Candidate arrangements are Claude Code
`2.1.278` in an isolated Linux guest, or Codex in such a guest with its version still to be
recorded. These are candidates, not claims that either supports the needed transport arrangement.
Select only after reviewing filesystem enforcement, egress control, provider transport separation,
configuration control and available access logs; record why the alternative was rejected. If no
candidate meets those criteria, M02 cannot start its dependent work. An isolated
Linux build environment is the required outcome; this record does not choose a container engine
or authorize installing one. Model, settings, caps, attribution reviewers, and adjudicator remain
pending at the user's request (**B06/B07**).

Existing helpers are usable starting points, with these inspected limitations:

- `cleanroom_hook.py` matches argument strings; it is not filesystem enforcement. Its default
  policy blocks broad Linux paths needed by the sanitized build. Missing/malformed policy falls
  back to defaults, role exemptions exist, and log writes are best effort.
- `session_audit.py` recognizes several transcript formats but flags general Linux include/license
  markers as well as forbidden access. Allowed API/header hits require explicit dispositions;
  do not suppress all Linux markers or treat a zero count as complete access evidence.
- The historical practice run's tool restrictions did not prove OS isolation. Cached outside
  reads and denied shell access in that run are reasons to test this environment afresh.

M02 must pin a trial-specific policy, disable role escape, protect it against implementer edits,
and reject missing/invalid configuration before launch. Keep default helpers unchanged in M01.
Filesystem mounts and egress controls are primary; hooks and scans supplement them. Test allowed
read/build/write controls and denied absolute-path, symlink, shell, history, cache, citation URL,
external-mount and evaluator-canary access. Test inherited settings, memory, skills, connectors,
subagents and provider transport too. Preserve expected/actual results and known logging gaps.
This enumeration is the minimum test set: M02 may add cases, not remove categories. Also test
that the evaluator repository and all its clones, worktrees, package caches and editor/agent
indexes are neither mounted nor reachable, including without network access.
Any failed isolation case blocks M05; platform selection alone cannot close B03.

Scanner settings remain `--min-run 10 --min-alpha 5 --k 8 --max-report 100000`, no whitelist;
compare against both pinned reference files. Reaching the report cap means incomplete review.
Disposition every hit against frozen allowed inputs and access evidence. Shared register/API
names alone do not prove copying; unexplained overlap remains unresolved. No threshold tuning
after seeing the candidate without a new version and a declared rerun policy.

## Allowed implementation inputs and exclusions

This is a closed inventory by input class. Each unresolved member blocks packet export;
it does not grant access to a whole directory while the inventory is being completed.

| Allowed item | Identity or required completion | Gate |
| --- | --- | --- |
| `spec.md` | Exact historical candidate digest above | Rehash copy at export |
| Neutral task | [IMPLEMENTER-BRIEF-v1.md](IMPLEMENTER-BRIEF-v1.md); cap placeholder unresolved | B06 |
| Sanitized kernel/build inputs | Exact upstream commit; full exported inventory and tree digest missing | B02/B03 |
| General OS API docs | Seven selected source pins; rendered dependency and leakage audits missing | B04 |
| Minimal scaffolding/build entry point | No device behavior or evaluator tests; files, commands, hashes uncreated | B02 |
| Fixture-facts sheet | Explicit external-fact inventory below; values not yet verified | B01/B05 |
| Outputs | Empty writable directory, build logs, implementer-authored checks, gap/assumption log | M02 access tests |

Fixture-facts sheet must enumerate board/model/revision, architecture, SPI instance/chip select,
mode and maximum clock, interrupt GPIO/polarity/trigger, reset wiring and procedure, power and
logic-voltage requirements, OS compatible/binding string, network-address policy, and boot/build
configuration. Each fact needs its authority and a supplied/not-supplied disposition. Give only
the minimal integration facts; no reference behavior, device register algorithm, evaluator
expectation, or historical finding. These facts never silently enter a later generation brief.

The brief itself supplies outside-spec facts: target part ENC28J60, B7 revision, Linux v6.12 and
half-duplex operating mode. Their authority is the pre-existing trial/corpus target and feature
scope, not a measurement of the received module. Part/revision may cue training familiarity;
record that limit. Half duplex keeps the transmit-recovery requirements in scope. Freeze these
task facts alongside the fixture-facts sheet, including its feature inclusions and exclusions.

Explicitly exclude original device driver/header; device-specific bindings/nodes; original
registration and build entries; maintainer metadata; source archives, Git history, installed
source packages, caches and symlink paths; hardware documents and citation retrieval; reference
builds and binaries; ledger/fact lists/scoring policy, interpretive corpus and author manifests;
historical prompts, reports, reviews and all session stores; evaluator checks/mutations/traces;
other candidates and implementations; personal instructions, automatic skills, memory and
connectors; network/package downloads; and hardware access. Replace necessary integration
metadata with inventoried minimal scaffolding, not an unbuildable tree. Audit text, paths,
generated files and indirect access. The full consumer skill is excluded to avoid a second
treatment; no supplementary implementation skill is selected.
Exclude this entire evaluator repository (`public-skills`) and every clone, worktree, package
cache or editor/agent index of it. Export audited allowed files individually; never mount the
repository as a convenient source for the packet.

Generation brief: not applicable. Preserve the historical author prompt in its original archive;
do not retroactively rewrite it or create a fresh candidate for this trial.

## D3: compatible execution records

Decision: keep execution contracts under `evals/enc28j60/reconstruction/`, outside `ledger.lock`.
M03 will define versioned manifest, check-contract, result, artifact, attribution and
outside-ledger-discovery records (with evidence, affected scope and possible answer-key
incompleteness explicitly recorded);
M04 will implement validation/replay. This Markdown manifest and JSON pin inventory are preparation
artifacts, not those runtime schemas or a working execution API.

The inspected `score.py` enforces exact review fields (`enc28j60-review-3`), hashes documentary
tools into input identity, archives attempts exclusively, and emits `enc28j60-score-1` with separate
acceptance dimensions. It has no execution-input extension. Do not add execution keys to that
review or rewrite archived result JSON. Link a sidecar to run/attempt ID, candidate hash, lock
digest, documentary-result digest, its archived tool identities, implementation/environment/check
digests and its own schema version. Preserve original attempts, including invalid/partial writes.
Extra OS integration requirements use a separate namespace, never new documentary denominator rows.

Historical attempt 02 archives older scorer/checker bytes and no `prepare.py`; the current scorer
does use `prepare.py`. Preserve the historical contract and replay with its archived tools.
Do not retrofit missing current-format artifacts into the old attempt or relabel it current.
M01 neither reruns scoring nor changes any documentary tool bytes.
The archived and current `strict_accept.py` are byte-identical; the scorer and ledger checker
are not. That distinction is recorded in the pin inventory for later replay analysis.

| Protocol execution label | Canonical test disposition | Required meaning |
| --- | --- | --- |
| pass | PASS | Complete, current qualified evidence satisfies the check |
| fail | FAIL | Qualified observation contradicts the declared expectation |
| awaiting fixture | UNAVAILABLE | Required physical evidence unavailable; retain fixture reason |
| blocked | UNAVAILABLE | Check not executable due to an unmet named prerequisite |
| unresolved | INCONCLUSIVE | Execution/evidence exists but cannot support a settled verdict |
| not applicable | NOT_APPLICABLE | Predeclared, reviewed applicability exclusion only |

Always retain original label, canonical disposition, reason and applicability. If a check ran
but its evidence is unusable, record `unresolved`/`INCONCLUSIVE`, not `blocked` merely to fit the
table. Keep attribution uncertainty separate: a clear execution failure can have unresolved cause.
Missing or stale artifacts block acceptance (or make previous acceptance stale); they never
become pass or not applicable. `accepted/blocked/stale` capability decisions remain separate
for documentary, implementation and hardware dimensions. Channel fitness likewise remains
`usable/inconclusive/unavailable`, not a test verdict. Strict implementation qualification still
requires spec readiness under the proposal; exploratory trial behavior may be reported separately.
M03 must test lossless mapping, dangling IDs, duplicate IDs, missing evidence, incompatible versions,
and stale digests before any result format is used.

Execution decisions belong to the sidecar's distinct `execution_acceptance` namespace.
The documentary result's `implementation_validated` and `hardware_validated` fields retain their
original `blocked/not evaluated` meaning within `enc28j60-score-1`; they are not current execution
verdicts and must never be overwritten. Reports label both namespaces and their scopes. Any
unified acceptance calculator is a separately versioned tool change under M03's staleness and
archived-replay rules, not an implicit precedence rule or edit to `strict_accept.py`.

## Scope and independent check definitions

Inherit the unchanged R1a scope: B7, half duplex, initialization, ordinary untagged unicast and
broadcast TX/RX, interrupts, stop/start and bounded recovery. Its exclusions and full T01–T07
definitions remain normative and are pinned by digest. No execution exclusion changes scoring.

| Check | Independent authority and current disposition | Qualification prerequisite |
| --- | --- | --- |
| T01 build / load-bind | OS experiment requirement; build blocked B02, physical portion B05 | Split component results; compile/registration negative controls; three cold starts |
| T02 reset/framing | INIT-003, REG-005, SPI-009; awaiting B05/B08 | Source-locator review, removed delay/dummy-byte mutations, timing capture |
| T03 traffic/length | Experiment counts plus RX-009/010; awaiting B05/B08 | Corruption/length mutations; peer FCS convention and broadcast observation |
| T04 RX wraps | RX-001/003/004/007 and conditional RX-005/006; awaiting B05/B08 | Odd-pointer/order mutations; three actual wraps per repetition |
| T05 concurrency/IRQ | IRQ-006/007, RX-012; awaiting B05/B08 | Packet-count/decrement mutations and demonstrable PKTIF fault |
| T06 stop/start | OS lifecycle plus RX-002/018; awaiting B05/B08 | Missing-reinitialization mutation and source/lifetime inspection |
| T07 abort recovery | TX-010/011/012/014; awaiting B05/B08 | Qualified abort injection, reset/flag-order mutation, bounded-error observation |

IDs above abbreviate the ledger's `ENC28J60-` prefix. M01 verifies all references resolve;
M07 must read exact source locators and independently adjudicate expected outcomes before
qualifying tests. The documentary answer key is frozen, not infallible. Preserve reference defects
and unresolved source conflicts; never relax expectations solely to make the reference pass.
Do not count a source check or ordinary traffic as a physical erratum test. Register-bank and
interrupt-acknowledgment source review remains required; T02/T05 are not exhaustive coverage.
Before qualification, make T03's addressed-unicast and broadcast observations explicit without
changing its frame sizes/counts/rate/repetitions, and define loss/duplicate capture accounting.
These details, cold reset, capture rate, B7 identity and fault recipes are B08, not executable claims.
The mapped rows are authority links, not a promise of full row coverage. In particular, T07's
bounded terminal-error alternative cannot establish TX-012's late-collision retransmission rule,
and ordinary abort injection does not establish TX-011's status-vector interpretation. M03/M07
must record the observed sub-obligation and leave those unexercised clauses unavailable or add
independently qualified checks before claiming them. RX-005/006 remain conditional; valid buffer
management alternatives are not failures merely because they differ from the reference.

## Predeclared offline procedure-readiness criteria for M09

Declare these before M05; they are not a success threshold chosen after seeing driver behavior.
M09 may start only when every criterion has evidence, required review, and a settled gate decision:

1. M02 has a reproducible reference and sanitized-placeholder build at the pinned target/config,
   and all isolation cases pass, including every minimum category in this record's D2 section
   and the evaluator-repository exclusion test. M02 may extend, not shrink, that floor.
   Final allowed-input inventory, hashes and neutral brief
   are frozen before implementation. No later clarification supplies new hardware facts.
2. M03/M04 validate and replay a complete synthetic attempt; missing/stale/wrong-identity evidence
   and truncated logs never pass. Archived documentary results/tools remain separate and unchanged.
3. M07-offline qualifies the T01 build check using a valid control and a compile-error mutation,
   plus a declared source-review slice for reset/framing and receive-pointer rules (T02/T04).
   Independently supported expected outcomes, valid alternatives, defect cases and reviewer
   decisions must be frozen before candidate evaluation. Offline review cannot satisfy physical
   timing, traffic, wrap, or recovery obligations.
4. M05 preserves the frozen implementation, logs, authored checks, assumptions and stopping
   reason, even for an unsuccessful or budget-exhausted attempt. Access audit and overlap
   dispositions establish whether the spec-only interpretation is admissible. Forbidden exposure
   or unresolved access evidence prevents procedure readiness; preserve the attempt and revise
   the procedure separately rather than laundering it into a valid run.
5. M08-offline produces per-check results and two independent failure attributions with
   adjudication or explicit unresolved reasons. A candidate failure does not itself fail procedure
   readiness: evidence collection, checks and reporting must work. Before M09 planning begins,
   the operator records a criterion-by-criterion decision with the independent attribution
   reviewers and D2-selected adjudicator's findings. Reviewer/adjudicator identities remain B07;
   the decision procedure is fixed now. Readiness is blocked if isolation cannot be established,
   the recorded build outcome cannot be reproduced by the evaluator, required evidence is
   missing/truncated/unusable, or readers disagree on check validity rather than only failure
   cause. Other unresolved causes are permitted only when reviewers agree that all readiness
   criteria have evidence and the uncertainty is confined to spec-versus-implementation cause.
   An adjudicator may resolve a dispute with evidence but cannot waive a criterion; unresolved
   gate disagreement blocks readiness. Preserve the decision and reasons before designing the pair.
6. The partial report preserves every physical deferral, costs and human effort separately,
   evidence availability, procedure defects and required fixes. Required procedural fixes are
   verified and reviewed in a new revision before M09 freezes paired conditions. No physical
   completion or workflow qualification is asserted. M13 still requires the physical trial.

## Stage-specific blockers and resource placeholders

| ID | Missing value/evidence | Owner and stage blocked |
| --- | --- | --- |
| B01 | Pi 4 Model B selected; exact board revision, finalized architecture/boot path and module identity/pinout remain unverified | Operator + M02/M06; target-specific export and wiring |
| B02 | Full pinned tree; build image/compiler/binutils/dependencies/config/commands/hashes; successful reference and sanitized builds | M02; M05 launch |
| B03 | Harness/version selection; enforced provider/access boundary, policy/negative tests and audit coverage | Operator/D2 selects before dependent M02 work; M02 validates; M05 launch blocked |
| B04 | Complete audited general-API export including rendered dependencies and hashes | M02; M05 packet freeze |
| B05 | Fixture availability beyond received modules; B7 evidence, wiring/voltage/IRQ/reset, peer, capture, boot/image identity and lease/cleanup | M06; physical M07/M08/M13 |
| B06 | Implementer model/version/settings, time/token/spending caps, checkpoint policy and explicit launch authorization | User + D2 before M05 |
| B07 | Two attribution reviewers, independence/exposure, adjudicator, per-stage estimates/caps/authorization | User + D2 before M08 reviews |
| B08 | Executable check contracts, source-locator adjudication, mutation/control qualification, observable fault/capture recipes | M03/M07; affected evaluations |
| B09 | Execution schemas, validated mappings, synthetic replay and artifact retention contract | M03/M04; result recording and M05 manifest freeze |

Generation: zero new sessions. Documentary re-review: separate P01, not included. Reconstruction:
one future implementer plus builds, estimate pending B02/B06. Execution: reference/candidate and
qualified controls/mutations, duration pending fixture. Attribution: two independent readings plus
adjudication, estimate pending B07. Repair: zero primary-trial sessions; separate authorization.
Keep model cost, build compute, equipment, operator active/elapsed time and human/agent review
effort separate; unknown time is unknown. No historical practice cost is a trial estimate.
Trial implementer-authored checks are incidental artifacts, not an M14 measurement. M14 requires
its own predeclared task, independent defect/control set, authorization and fresh authoring.
The paired run freezes its own brief under M09; this brief is trial-scoped. `corpus_check.py` and
`author_manifest.py` are not trial execution inputs: no generation occurs here. Their generation
gates still apply to M10; the existing author-manifest consistency check is a repository check.

## Completion boundary

M01 can finish when custody matches, every required preparation field has a value or a named
stage blocker, design/inputs/check references pass review, and the reviewed record is checkpointed.
R1a design freeze, M02 isolation/build qualification, M03 schemas and M07 check qualification
remain separate gates. Freeze this record's revision plus the final briefs, environment, inputs,
check definitions, policy and scanner hashes in a later run manifest before implementation.
Never use M01 completion as launch authorization. See [M01 evidence](../../../evidence/M01.md).
