<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# ENC28J60 reconstruction run guide

## Terms

- **Reference driver** — the existing driver pinned by this pilot's corpus.
- **Candidate driver** — an isolated implementer's replacement built from a generated spec.
- **Arm** — the with-skill or without-skill specification-generation condition.
- **SPI fixture** — the physical controller, bus connection, and network test setup.

See the repository [glossary](../../../../GLOSSARY.md) and the shared
[reconstruction protocol](../../RECONSTRUCTION.md). This guide supplies pilot-specific
preparation; it does not duplicate or relax that protocol.

## Status and scope

Planning only: no reconstruction runner, candidate driver, frozen execution manifest, or
reference smoke-test result is supplied by this guide. The paired specification run has not
happened. Reconstruction adds a separate measurement and leaves policy `enc28j60-1.4`, its
locked files, and all historical practice attempts unchanged.

The frozen corpus already selects Linux v6.12 source for ENC28J60 B7 (EREVID 0x06).
Use that reference OS for this pilot; qualify the build and execution environment before
running. This is a corpus choice, not evidence Linux always has the best driver. Another
OS reference requires a separately identified benchmark revision, not a silent substitution.

## Preparation record to complete before paired candidates are inspected

Create a versioned reconstruction manifest outside the documentary lock, with the following
fields. These are required records, not claims that the environment already exists. Mark
unknowns explicitly; resolve run-critical ones before authorizing the affected stage.

| Record | Required contents |
| --- | --- |
| Identity | Experiment ID/version, documentary lock digest, corpus identity, reference source commit and hashes |
| Build | OS revision, target architecture, compiler/toolchain versions, configuration, dependencies, build commands, sanitized tree digest |
| Inputs | Separate generation and implementation briefs, allowed OS API docs, scaffolding/edits, external facts, hashes and opaque candidate IDs |
| Isolation | Allowed access, excluded material, validation evidence, scanner thresholds/whitelist/overlap rules, isolation and audit limitations |
| Implementer | Model/version/settings, format-neutral implementation instructions, resource cap, stopping conditions, trial or paired status |
| Scope | Required features, exclusions, check IDs, ledger mappings, extra requirements with evidence, acceptance criteria |
| Fixture | Controller revision evidence, SPI configuration, OS binding/configuration, traffic peer role, capture method, reset procedure |
| Checks | Test code/version/hash, scenarios, timeouts/repetitions, fault method, mutation results, available versus awaiting hardware |
| Reference | Build/load/bind and smoke results, per-check outcomes, traces, unresolved discrepancies |
| Review | Two independent attribution reviewers, access record, blinding limits, adjudication method |
| Budget | Separate generation, documentary review, implementation, execution and optional repair estimates and authorization |

Before generation, follow ARMS.md's existing pin checks and author-manifest rules. The pins-only
author manifest goes to spec authors, not implementers. Implementers receive the resulting
frozen spec and only the allowed inputs defined by the shared protocol.

In the exclusion inventory, explicitly audit the original `enc28j60.c` and `enc28j60_hw.h`,
device-tree bindings and device nodes, driver registration/build entries, maintainer metadata,
source archives, and history. Remove excluded content or replace necessary build/binding
material with minimal shared scaffolding, recording every supplied device fact. A working OS
build cannot simply have all integration metadata deleted without an audited replacement.

Use neutral instructions and the shared protocol's validated hook/audit mechanisms, not the
full consumer skill's treatment-specific prose. Author the same target-OS task for both
spec-generation arms before writing their prompts.

## Initial scope to qualify and freeze

Start with initialization, ordinary transmit/receive, shutdown/reinitialization, and the
ledger's applicable boundary and recovery requirements. Before inspecting paired candidates,
turn these categories into concrete tests with cited evidence, expected behavior, and exact
conditions. Candidate areas include buffer wraparound, packet length boundaries, bank/register
access, interrupt handling, and reset/timeout recovery. These are test-design topics, not
already verified test cases or assertions that every fault is injectable on B7.

Freeze the feature subset and exclusions explicitly. Any requirement outside the chosen
execution subset remains visible in documentary scoring. Separately identify checks requiring
bus capture or fault injection and explain what cannot yet be provoked. An unexercised erratum
is not a passing recovery test. If a check exposes a reference defect or disputed requirement,
record adjudication rather than adjusting its expected result to match the reference.

## Order of work

1. Freeze the shared brief, scope, environment recipe, isolation, check definitions, and
   attribution rules (R1a). Build the sanitized environment for implementation. Separately
   implement and qualify execution/mutation checks (R1b) against evaluator-owned reference
   material without candidate access, before inspecting candidate execution results. Hardware
   delays do not block partial build/source-review work or the documentary run.
2. If needed, use the existing frozen practice spec for a separately budgeted procedure trial.
   Its artifacts never become one arm of the paired comparison. Version and freeze any protocol
   changes from that trial before inspecting paired candidates.
3. Generate the pair under [ARMS.md](ARMS.md). Freeze both specifications. Documentary review
   follows [SCORING-RUN.md](SCORING-RUN.md), including review of both before either is scored.
4. Run fresh implementers with identical settings and input rules. Implementation may overlap
   documentary review, but no findings or scores are supplied to implementers. Freeze both drivers.
5. Compare each with the reference through independent source review and shared tests. Use the
   same device/configuration and reset between runs; record execution order and repetitions.
6. Attribute failures and publish separate documentary and reconstruction results. Decide
   afterward whether optional repair, repeated pairs, or verifier integration earns its cost.

The modules were recorded as ordered on 2026-09-19; verify availability when scheduling.
Build checks and source review need not wait for the fixture. Record every physical check
without execution as awaiting fixture or otherwise blocked, with a reason. Do not report a
complete execution result while these remain outstanding.

## Result package

Archive the completed manifest, both frozen spec identities, candidate code and build logs,
exact prompts and access records, gap/assumption logs, reference and candidate per-check
results, mutation evidence, and requirement-linked findings. Sensitive raw records remain
outside public artifacts. Use role names and sanitized evidence in shared reports.

Report missing or ambiguous spec facts and justified uncertainty requiring hardware verification separately from
implementation mistakes despite clear
instructions, using permitted evidence to distinguish necessary verification from omitted
documented facts. Cross-tabulate checked requirements with documentary coverage. Report the
shared protocol's OS-integration citation and denominator caveat. Include unresolved attribution and forbidden-source exposure. Report resource
use and unavailable test coverage alongside results. One pair is a pilot observation, and a
working driver does not prove that its author obtained every hardware fact from the spec.
