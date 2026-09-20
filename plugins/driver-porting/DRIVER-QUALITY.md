<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Faster driver development with evidence we can test

The goal is to turn scattered hardware knowledge into a precise specification, then use that
specification to build drivers and repeatable tests. We want agents to do most of the research,
implementation, and checking, while confidence comes from evidence that can expose mistakes.
Success means less engineering time to reach a defined quality bar, including debugging and review.

## Terms

- **Driver** — software through which an operating system controls a device.
- **Specification (spec)** — the contract describing what the hardware requires and guarantees.
- **Requirement ledger** — an independently prepared checklist used to find missing requirements.
- **Reference driver** — an existing implementation used as evidence; it may have bugs.
- **Agent** — an AI assistant with tools, assigned an author, implementer, or reviewer role.
- **Mutation check** — deliberately introduce a defect to see whether a test catches it.

See the shared [glossary](../../GLOSSARY.md) for additional terminology.

## The problem

A device's programming interface includes commands, memory locations, timing constraints, and
rules about which operations may happen in which order. Its documentation may omit details or
describe behavior corrected by a later hardware-defect notice. Existing drivers contain useful
workarounds, mixed with choices specific to their operating system and their authors.

An agent can produce plausible code while missing a rare recovery rule. A successful build or
one successful packet transfer will not expose that omission. Reviewing every source document
and every generated line manually would consume much of the time automation was meant to save.

We therefore need to check three separate things: whether the spec contains the necessary
knowledge, whether its claims are supported, and whether an implementation actually behaves
correctly. Each can fail while the others look convincing.

## The proposed structure

| Stage | Output | Independent check |
| --- | --- | --- |
| Establish evidence | Exact editions of hardware documents and a fixed source revision | Verify identities; record conflicts and revision applicability |
| Describe the contract | A spec with evidence for its claims and explicit uncertainties | Check required facts against the spec, and all spec claims against sources |
| Implement from the contract | A driver, build results, and a log of assumptions or blockers | Keep original device source and review answers unavailable to the implementer |
| Exercise behavior | Results from normal operation, boundaries, failures, and recovery | Run independently defined checks; compare with the reference and physical observations |
| Diagnose and repair | A corrected, versioned artifact and repeatable checks | Attribute failures, preserve earlier results, and rerun affected checks |

The requirement ledger is prepared before the evaluated spec is seen. Otherwise a missing
requirement could disappear from both the answer and its grading checklist. The reverse check
matters too: extra claims need evidence even if the ledger never anticipated them.

Separating the implementer from the original device source tests whether the spec is usable
on its own. General operating-system documentation and recorded board wiring remain available.
The first reconstruction uses the reference driver's operating system to reduce integration
uncertainty; portability to another system is a separate test. The method is not Linux-specific.

## How confidence can converge with little human review

Convergence means resolving defects and uncertainty against acceptance conditions chosen in
advance. Repeated agent agreement is insufficient: different reviewers can inherit the same
mistaken assumption. Stronger evidence comes from checks with different ways of failing:

- **Mechanical checks** catch changed inputs, broken citations, missing review records, build
  failures, and incomplete coverage accounting.
- **Independent source readings** examine omissions and unsupported claims without seeing each
  other's judgments. Disagreement stays unresolved until evidence settles it.
- **Executable checks** challenge behavior at boundaries and during failures, including required
  operation order and timing. Comparing with a reference helps locate differences; disagreement
  does not automatically mean the new implementation is wrong.
- **Mutation checks** challenge the tests themselves. A test that passes correct code but also
  passes a relevant deliberate defect has not demonstrated that it protects that requirement.

For example, the pilot's evidence requires a delay of at least one millisecond after a particular
reset command. A source check can inspect the delay; a captured hardware transaction sequence
can measure it; a mutation removing it can test the detector. Merely observing that the device
started successfully would establish much less. The requirement and its source locators are
recorded as `ENC28J60-INIT-003` in the [pilot ledger](evals/enc28j60/ledger.yaml).

The proposed repair loop is: preserve the failure, determine whether it belongs to the spec,
implementation, test, environment, or reference, make a supported correction, then rerun the
affected checks and the existing regression suite. A regression test detects the return of a
previous defect. New discoveries become versioned requirements and tests; they do not silently
rewrite earlier benchmark results. Set resource limits so an unresolved loop escalates rather
than revising indefinitely.

Acceptance should require no unresolved critical requirements, successful qualified checks for
the declared scope, demonstrated detection of representative defects, and explicit accounting
for unavailable tests. Exact thresholds must be selected before evaluating the candidate.
Untested behavior remains untested; a growing pass count cannot cancel an important unknown.

Once a device's requirements and test environment are qualified, routine changes could advance
automatically through these gates. Humans would handle narrower exceptions: conflicting evidence,
unexplained hardware behavior, missing equipment, and changes to scope or accepted risk. Zero
human review is a possible operating mode for bounded, well-tested changes; it is not an
established property of this project or a guarantee for unfamiliar hardware.

## Why this could improve speed and testing

The initial evidence and test work costs time. Its return comes from reuse: later implementations
can consume the same contract, failures arrive with requirement-linked evidence, and previously
resolved defects are checked automatically. Research, independent review, and environment
preparation can proceed concurrently where their information boundaries allow it. Measure total
time, model cost, human review effort, and defects found after acceptance to establish whether
this actually speeds development.

The spec can also support tests below full-system operation: register-operation checks, packet
boundary cases, and simplified executable test models for failure paths that are hard to provoke
physically. Those models need validation against documents and hardware; code and tests generated
from the same mistaken spec can agree perfectly. Physical testing remains necessary for claims
about real timing and device behavior.

This approach extends to firmware and related software that manages hardware: preserve the
behavioral contract, test normal and failure paths, and retain the evidence connecting them.
The reusable deliverable is the contract together with qualified tests and their limitations.

## What we have established so far

The [evaluation plan](EVAL-PLAN.md) and [reconstruction protocol](RECONSTRUCTION.md) define the
method. The small Ethernet-controller pilot has a frozen ledger and documentary scoring tools.
Its first practice spec still has incomplete review; no reconstruction experiment has run.
The [procedure-trial draft](evals/enc28j60/RECONSTRUCTION-TRIAL.md) is the next preparation step.

We still need to demonstrate that reconstruction works, that the tests catch meaningful defects,
and that the process saves engineering effort. The proposed evaluator-authored tests do not yet
measure whether an implementer can derive good tests from the spec. That needs a separate test
of the generated tests against independently prepared defects. Later comparisons with and without
the skills, across repeated runs and more devices, must establish which gains are reproducible.
