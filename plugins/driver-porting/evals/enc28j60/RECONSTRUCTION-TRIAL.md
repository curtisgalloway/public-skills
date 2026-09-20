<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# ENC28J60 reconstruction procedure trial: R1a draft 1

## Terms

- **R1a** — preparation and freezing of the experiment's design and input records.
- **R1b** — qualification of executable checks against reference material and deliberate defects.
- **Reference driver** — the pinned existing implementation, which can itself contain defects.
- **Fixture** — the controller, host, wiring, traffic peer, and measurement equipment.
- **Mutation** — a deliberate defect used to establish that a check can detect incorrect behavior.

See the [glossary](../../../../GLOSSARY.md), [run guide](RECONSTRUCTION-RUN.md), and
[shared protocol](../../RECONSTRUCTION.md). This record is evaluator-only. Do not give it to
an implementer: it contains requirement mappings and evaluation details.

## Decision and status

Prepare a procedure trial first, using the existing frozen practice specification. Prepare the
paired run afterward. The user selected this order on 2026-09-20 and requested that models,
spending caps, and reviewers remain pending. No paid session or hardware operation is authorized
by this draft. No environment, executable check, or isolation control is claimed qualified.

Proposed identity: `enc28j60-reconstruction-trial-01`, design revision `draft-1`.
This is a versioned preparation record outside the documentary lock, not a frozen run manifest.
Preserve this revision when a trial-informed revision is created. Trial code and results cannot
become one arm of the later paired run.

## Input identity and custody

| Input | Required identity or disposition |
| --- | --- |
| Practice specification | 120,897 bytes; SHA-256 `516b7854e97fca4577d67922d2a49d174a80ebae9df9956d3a0738788f76bd06`, as recorded in [PRACTICE-RUN.md](PRACTICE-RUN.md) |
| Retrieval | Pending: locate the archived artifact outside this repository and verify its bytes before packaging; do not reconstruct it from the report |
| Reference OS | Linux v6.12, commit `adc218676eef25575469234709c2d87185ca223a` |
| Reference files | `enc28j60.c` and `enc28j60_hw.h`; exact paths and hashes in [author-manifest.yaml](author-manifest.yaml), evaluator-only for this trial |
| Corpus | SHA-256 `73c74ecd63b2d0d048234eeb0e9f8b255275306de9f601e5971300a738fe4beb` |
| Documentary ledger | SHA-256 `3479587b9ee0f174209a956c7bebeca8e1d53001df8156908d05d1787db070b2`; policy `enc28j60-1.4`; retain [ledger.lock](ledger.lock) unchanged |
| Design freeze | Pending: record repository commit and SHA-256 of this record, exported brief, environment recipe, check definitions, scanner configuration, and all supplied inputs |
| Generation brief | Not applicable to this trial: no new author session and no retroactive change to the historical generation prompt |

The practice spec's documentary acceptance is blocked and its semantic review is incomplete.
This trial tests the reconstruction procedure; it does not certify that specification or resolve
its historical review. Do not show the implementer historical review findings or scores.
The evaluator preparing this record has read that report; do not claim candidate-blind trial
design. Later paired candidates have not been generated or inspected in this preparation.

## Proposed feature scope

Implement a Linux network driver for the ENC28J60 B7 revision, with initialization, ordinary
unicast/broadcast transmit and receive, standard untagged Ethernet frames, interrupt service,
interface stop/start, and bounded failure recovery. Exercise half duplex so the applicable
transmit-recovery requirements remain in scope. The traffic peer must be configured compatibly.

Exclude jumbo frames, VLAN-specific behavior, multicast hash filtering, promiscuous-mode
qualification, DMA/checksum offload, power-management optimization, suspend/resume, wake-on-LAN,
performance ranking, and other silicon revisions from execution acceptance. These exclusions
do not remove any requirement from documentary scoring. A valid alternative implementation
need not copy the reference's buffer split, symbols, retry count, or incidental operation order.

## Environment recipe and supplied facts

Use separate evaluator and implementer environments. Prepare a Linux build tree at the pinned
commit; export an ordinary directory with no version-control history for the implementer.
Keep the reference build and all hardware documents exclusively in the evaluator environment.

1. Select a host board capable of booting the pinned kernel and connecting the SPI controller;
   record architecture, board revision, SPI controller, interrupt routing, and boot procedure.
   These choices remain pending; a compile-only architecture is not a substitute for the fixture.
2. Pin build-image digest, compiler/binutils versions, dependencies, kernel configuration,
   target architecture and any cross-compiler prefix. Build the reference in the evaluator
   environment first. Record exact successful commands and resulting kernel/module hashes.
3. Remove the device sources and headers, device-specific bindings/nodes, registration entries,
   maintainer metadata, history, archives, and downloaded or installed source copies from the
   implementer export. Audit text references as well as filenames, symlinks and generated files.
4. Supply minimal build and binding scaffolding in their place. Record every external device
   fact in it, including compatible string, SPI speed/mode, interrupt configuration, reset wiring,
   and supplied network address policy. Scaffolding must not contain device behavior or tests.
5. Export only pinned general Linux API documentation needed for SPI, interrupts, locking,
   allocation, network interfaces, and module lifecycle. Audit examples for device leakage.
   Inventory and hash these files; authors of a later paired run need a separately frozen list.
6. Verify the sanitized tree builds with a neutral placeholder module. Record the exact build
   command, environment variables, configuration hash, tree-content hash, and build log. Supply
   that same build entry point to the implementer. It must not download dependencies at runtime.

No executable command recipe is frozen until the target and toolchain are selected and the
build succeeds. Board wiring and binding facts belong in the implementation packet only;
they must not silently migrate into the later generation brief.

## Neutral implementation packet

Export only this section's quoted task, the verified frozen spec renamed `spec.md`, the audited
environment and general API docs, build instructions, and a fixture-facts sheet. Hash each item.
Resolve the bracketed fields before launch; do not send this full evaluator record.

> Implement a Linux v6.12 driver for the ENC28J60 B7 using `spec.md` and the supplied environment.
> Support initialization, untagged unicast and broadcast transmit/receive in half duplex,
> interrupt handling, interface stop/start, and bounded failure recovery. Jumbo frames,
> VLAN-specific behavior, multicast hash filtering, promiscuous-mode qualification,
> DMA/checksum offload, power-management optimization, suspend/resume, wake-on-LAN,
> performance tuning, and other silicon revisions are outside this task.
>
> Use only the supplied files and build tools. Do not follow citations, fetch device sources,
> search for another implementation, or consult external device documentation. You may use
> the supplied general Linux API documentation. The fixture-facts sheet records wiring and
> binding information supplied separately from the specification.
>
> Keep a log of missing information, assumptions, clarification requests, and blockers, with
> links to relevant spec passages. Record a requirement for hardware verification explicitly;
> it is not automatically a specification defect. No new hardware facts will be supplied during
> this attempt. If a blocker prevents progress, preserve the partial implementation and explain it.
>
> Run the supplied build check and any offline checks you author within the allowed environment.
> Hardware access and evaluator tests are unavailable during implementation. Deliver source,
> build logs, your checks and their results, and the gap/assumption log. Stop at completion,
> an irreducible blocker, or [approved resource cap], whichever occurs first. Preserve failures.

The implementer model/version/settings, harness version, time/token/spending cap, and checkpoint
policy are pending. No supplementary implementation skill is selected. In particular, do not
load the treatment-specific cleanroom-implementer prose. Disable inherited personal instructions,
automatic skills, shared memory, connectors, and caches unless explicitly inventoried and allowed.

## Isolation validation and overlap review

Mount only audited input files, the sanitized build environment, and an empty writable output
directory. Deny network egress and access to host home directories, evaluator artifacts, shared
session stores, and external mounts. Provider transport, if needed, must not expose arbitrary
network requests to the implementer. Record how the chosen harness enforces this separation.

The existing clean-room policy blocks broad Linux paths and therefore cannot be reused unchanged.
Prepare and pin a trial-specific policy permitting the sanitized OS API/build inputs, with no
role escape for an implementer. Validate the hook and session audit against that policy; they
supplement filesystem/network restrictions rather than replacing them.

Before launch, test permitted file reads and compilation, and attempted access through absolute
paths, symlinks, shell subprocesses, history, package caches, source URLs, and citation downloads.
Record expected and actual outcomes. Use harmless canaries in evaluator-only storage for denied
reads. A failed isolation test blocks launch. Audit available tool and filesystem records after
the run; record blind spots instead of claiming complete access evidence.

Proposed scanner settings: `--min-run 10 --min-alpha 5 --k 8 --max-report 100000`, comparing the
candidate against both pinned reference files. Record the scanner file hash. If reporting reaches
the cap, disposition is incomplete until all hits are reviewed; never treat truncation as a pass.
Use an empty identifier whitelist for this trial and preserve all hits. Classify shared hardware
names and general Linux API names with explicit evidence from the frozen spec or allowed inputs;
do not suppress them automatically or change thresholds after seeing the implementation.
Other overlap triggers access review, not an automatic copying verdict. Established forbidden
access invalidates the spec-only interpretation. Unexplained overlap remains unresolved.

## Proposed independent checks

These are evaluator-owned definitions, not executable or qualified tests. Hardware checks are
awaiting fixture. Source/trace rules derive from the named rows of [ledger.yaml](ledger.yaml),
which retain exact document editions and locators; check those sources during R1b qualification.
Traffic counts and timeouts below are experiment choices, not vendor requirements. A failed
reference check requires investigation and adjudication, not automatic relaxation of a threshold.

| ID | Scenario and acceptance | Evidence and mutation to qualify |
| --- | --- | --- |
| T01 | Build with the frozen configuration; zero build errors. Load/bind and bring the interface up within 30 s, three cold starts. No kernel fault. | OS integration requirement outside hardware ledger. Missing registration or a compile error must be detected; boot/bind scaffolding still pending. |
| T02 | Capture reset and initialization on all three starts. At least 1 ms between SPI reset and subsequent device use; reads distinguish ETH from MAC/MII framing. | INIT-003, REG-005, SPI-009. Remove reset delay; remove a MAC/MII dummy byte. Reference's 2 ms delay is not the acceptance threshold. |
| T03 | Send 100 numbered frames at 10 frames/s for each length 60, 61, 127, 511, 1514 bytes, excluding FCS, in each direction; repeat three times. All addressed frames arrive once with matching bytes, within 5 s after each batch. No kernel fault. | End-to-end experiment requirement; RX-009/010 for receive layout and FCS accounting. Inject payload corruption and a receive length error. Validate peer capture excludes FCS consistently. |
| T04 | During T03, capture at least three actual receive-buffer wraps per repetition. Check each released receive pointer is odd and written low byte then high byte; buffer start is zero. Insufficient observed wraps means incomplete, not pass. | RX-001/003/004/007. Mutate an odd pointer to even and swap pointer write order. Apply RX-005/006 only if that wrap procedure is used. |
| T05 | Run simultaneous numbered TX/RX at 10 frames/s each for 60 s, three repetitions; all frames drain within 5 s. Source review and qualified fault fixture check processing when packets remain but PKTIF is clear. | IRQ-006/007, RX-012. Replace packet-count readiness with PKTIF-only readiness; omit packet decrement. Traffic alone cannot establish that the erratum was exercised. |
| T06 | Ten interface down/up cycles; after each up, complete 10 numbered frames each direction within 10 s. No stale work, kernel fault, or permanent queue stall; inspect stop/lifetime handling separately. | Lifecycle experiment requirement outside hardware ledger; RX-002/018 for receive-disabled reconfiguration. Deliberately omit needed restart initialization. |
| T07 | Qualify a half-duplex TX-abort injection, then provoke ten abort/recovery cycles. Within 10 s per cycle, complete the next valid frame or report a bounded terminal error without a hung queue. Verify reset/flag order from trace. | TX-010/011/012/014. Mutate flag clearing to precede reset; remove abort handling. Injection method pending; no claim that ordinary traffic triggers this. |

T01 source/build work can proceed before hardware; load/bind remains awaiting fixture. T02–T07
require capture, equipment, or executable qualification not supplied here. Register bank changes
and interrupt acknowledgment ordering also need requirement-linked source review; T02 and T05
must not be reported as exhaustive register/interrupt coverage. Unlisted ledger rows are not
execution-tested by this trial.

For each check record reference result, mutation result, candidate result, actual conditions,
trace/log hashes, and pass/fail/awaiting-fixture/blocked/not-applicable/unresolved with reasons.
Qualify against reference and mutations before viewing candidate execution results. Reset the
device between reference and candidate runs using the frozen fixture procedure; record run order.
Cold-reset method, capture sample rate, wiring, B7 revision evidence, and fault-injection method
are pending. If a method cannot provoke the stated condition, retain the unavailable check.

## Attribution and resource plan

Two independent reviewers receive the frozen spec, candidate, permitted-input inventory,
requirement evidence, and execution results, without each other's judgments. Reviewer identities,
relationships to authors, and adjudicator are pending. Classify discrepancies as spec omission,
error or ambiguity; implementation error despite adequate information; justified verification
requirement; environment/test limitation; reference discrepancy; or unresolved. Cite evidence
for recoverability before calling a deferral justified. Preserve disagreement and exclude it
from settled counts until adjudicated. Any single-reviewer attribution remains provisional.

| Stage | Trial resource estimate | Authorization |
| --- | --- | --- |
| Generation | Zero new author sessions; reuse exact historical bytes | No generation planned |
| Documentary review | No new full review included; the historical review remains incomplete | Fresh review is a separate pending work item |
| Reconstruction | One fresh implementer session plus build resources; dollar/time estimate pending model and environment selection | Pending |
| Execution | Reference plus candidate, three repetitions where specified, mutation qualification and manual capture review; duration pending fixture qualification | Pending |
| Attribution | Two independent reviews plus adjudication if needed; estimate pending reviewer selection | Pending |
| Optional repair | Zero sessions in the primary trial; separately version and budget any repair | Not authorized |

The historical $50.23 generation/review cost is not an estimate for this trial. Calculate model
costs from selected rates, input size, output cap and expected tool iterations before requesting
launch authorization. Keep compute, reviewer, equipment and operator time separate.

## Completion gates and next action

R1a remains draft until the artifact is retrieved and verified; fixture/architecture and API
inputs selected; build recipe and isolation validated; check definitions and scanner rules
reviewed; and all input hashes recorded. Model, budget, and reviewer fields remain pending at
the user's request and must be resolved before the stages they govern. Freeze a manifest that
records these choices, validations, and explicit R1b deferrals before implementation.

Next preparation action: select the target board/build environment and retrieve the archived
practice spec by its recorded hash. Do not inspect or repair its contents as part of retrieval.
After the trial, preserve code, unsuccessful attempts, costs, access records and partial results;
record procedural changes in a new revision before preparing either paired-generation prompt.
