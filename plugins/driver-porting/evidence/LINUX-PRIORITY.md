<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Plan revision: prioritize the Linux driver mechanism

## Terms

- **Engineering pass** — implement, review, test and repair a driver to a declared quality bar.
- **Spec-only experiment** — test implementation from a spec under controlled input restrictions.
- **Negative control** — a deliberately faulty case that a relevant check must reject.

See the [glossary](../../../GLOSSARY.md) and [revised plan](../IMPLEMENTATION-PLAN.md).

## Decision

On 2026-09-20 the user requested an independent assessment of whether directly writing and
verifying the Linux driver would serve the goal as well as the extensive verification
preparation. After receiving the assessment, the user directed a revision of the larger plan
to prioritize the Linux driver mechanism. Starting revision: `2e6fc69`, after the source-audit
checkpoint; no production code changes are part of this revision.

The assessment distinguished practical confidence from causal comparison. Independent driver
review and meaningful behavior tests directly address whether the spec and skills help produce
a useful driver. Exhaustive input sanitization, paired runs, blinded attribution and full
documentary scoring principally support narrower experimental claims. Neither one successful
Linux driver nor one controlled pair establishes universal spec completeness or a stable skill
advantage. The [project overview](../DRIVER-QUALITY.md) makes total engineering effort to a
defined quality bar the practical goal.

The user selected practical progress first. L01 therefore leads the implementation plan:

1. Implement from the spec initially, log gaps and outside assistance, build, and independently
   review important hardware requirements.
2. Test reference and candidate under comparable conditions, exercise boundaries and observable
   recovery, demonstrate selected checks detect deliberate defects, and repair demonstrated gaps.

Keep source/build identities, independent expected outcomes, a compact coverage table, actual
hardware evidence, unresolved cases and versioned failures/repairs. Defer exhaustive sanitization,
generic execution/replay infrastructure and controlled comparative experiments. Existing artifacts
and their acceptance rules remain intact for a later experiment; L01 is separately labeled and
cannot retroactively become the frozen trial. The incomplete documentary result stays incomplete.

The plan permits deliberate logged reference/documentation consultation during L01. It therefore
does not establish strict spec-only sufficiency or waive source restrictions for future ports.
It does not require a full semantic audit of the kernel before a driver can be written. The
five reviewed related-controller exclusions remain unimplemented experimental preparation.
The first independently reviewed build is a decision point: continue useful Linux tests/repairs
or apply the mechanism elsewhere with explicitly partial Linux evidence. Completing the entire
controller or waiting on a Linux fixture is not a general prerequisite to the next application.

## Review and limits

A separate read-only agent assessed the tradeoff and recommended this priority change. It
inspected project plans and evidence; it did not implement or test a driver. Its recommendation
is architectural judgment, not measured evidence that the simpler process is equally effective.
No measured comparison of effort exists yet. A practical pass must still go beyond compilation
and a successful ping; L01 keeps boundary, recovery and independently supported requirements.

The user approved a read-only Claude review of the public plan after automatic approval review
initially rejected the follow-up disclosure. The review used `claude-opus-5[1m]`, followed by
explicit confirmation of the amended plan and this evidence text. No blocking objections remained.

The review produced twelve corrections, all resolved: predeclare critical requirements and
negative controls; version changed checks; identify the ordinary source tree; record context
exposure; verify the loaded driver and reset between runs; record that test conditions occurred;
locate/license driver artifacts; update command-discovery references; state limited requirement
coverage; link the deferred audit; track the overview's older scope; and make model/effort selection
explicitly the user's decision. The coverage table also separates excluded scope from untested cases.
The reviewer accepted a documented reset procedure instead of a universal power-cycle requirement,
and artifact/license recording without an unsupported legal conclusion about all kernel modules.

The peer reviewed document content and consistency; it did not execute checks, verify Git state,
read the independent agent's full assessment, or re-review every deferred milestone. The primary
agent compared the revision with that assessment. Confirmation is agreement on the plan, not proof
of driver correctness or evidence that this approach saves time. No new implementation run,
hardware operation, fixture qualification or experimental result is claimed here.

CLI-reported `total_cost_usd` values for the reopened review and confirmation were 3.9865245 and
4.714029; these resumed-session reports are not summed. Operator active time and the separate
agent's cost are unmeasured. Public-document privacy, local link targets, registration and
whitespace checks passed. No production code changed; build/test suites were not rerun.
The public-only review brief and exact responses are retained in local scratch consultation
records. Permanent/off-host custody is not established.
