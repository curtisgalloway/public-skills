<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Driver reconstruction evaluation

## Terms

- **Reconstruction** — implement a driver from a frozen spec on the reference driver's OS.
- **Reference driver** — the existing implementation used as evidence, not assumed correct.
- **Arm** — one specification-generation condition, with or without the skill.
- **Differential testing** — compare implementations under the same scenarios.
- **Fixture** — the hardware and connections prepared for repeatable execution.

See the repository [glossary](../../GLOSSARY.md) for shared terms.

## Purpose and status

This is a proposed execution protocol, not a completed experiment or an implemented runner.
It complements the documentary recall and precision passes in [EVAL-PLAN.md](EVAL-PLAN.md):
can a different implementer turn the exact generated specification into a working driver?
The first run is a procedure trial. Freeze any improvements before the paired implementation
runs; trial results are diagnostic and cannot become one half of that pair.

## Select the reference OS per device

Choose the reference driver and operating system (OS) for hardware coverage, evidence quality,
build reproducibility, and execution access. Linux is a reasonable first place to look because
we expect broad coverage; verify that assumption per device. A BSD or other OS driver may be
better. Record the selection rationale and pin the source revision and configuration.

Give both spec authors the same declared target OS/revision and intended feature scope before
generation, in a shared generation brief that does not prescribe the treatment skill's
document structure. The separate implementation brief supplies identical board wiring and OS
binding configuration to both implementers; record those external facts. These fixture-specific
facts are not extra inputs to either spec author. Record any general OS development inputs
supplied to the authors identically and separately from the pinned hardware corpus.
Differences in useful OS-integration guidance are part of the generated-spec outcome; report
them separately from hardware-contract gaps.

Reconstruct on the reference OS first to reduce uncertainty introduced by porting. A later
cross-OS implementation tests portability separately. Reference-OS reconstruction may also
make remembered implementation patterns easier to reuse; changing OS does not establish that
prior knowledge was absent: recalled device facts are not OS-specific. This protocol's records and comparisons must accept any OS;
device-specific run guides supply its build and integration details.

## Freeze before inspecting paired candidates

An evaluator prepares the implementation brief, feature scope, environment, and checks from
the adjudicated reference corpus and independently authored ledger, without seeing paired
candidate specs or drivers. Record their versions and hashes in a separate reconstruction
manifest. Do not edit the documentary ledger, lock, policy, or historical scores. Additional
requirements never enter that frozen documentary denominator; report their discovery separately as possible
evidence of answer-key incompleteness.

Define required behavior and explicit exclusions, observable pass/fail criteria, timeouts,
repetition counts, and fixture requirements per check. Map checks to stable ledger requirement
IDs where applicable; identify any additional requirements and evidence separately. Unresolved
source conflicts remain adjudication items, not binary failures. Requirements excluded from
execution still count in documentary scoring under its existing policy.

Separate the design freeze (brief, scope, check definitions, environment recipe, isolation,
and attribution rules) from executable qualification. The design freeze can unblock spec
generation and implementation without hardware. Report build/source-review results as partial
until the execution suite and fixture are qualified.

Build and exercise the reference driver to establish the comparison baseline. Demonstrate
that checks discriminate using evaluator-owned mutations of the reference or an independently
prepared test fixture, without candidate access, before inspecting candidate execution results.
Introduce representative deliberate defects (for example an incorrect wrap operation or
recovery ordering). Record which checks have demonstrated this
and which have not. Do not invent acceptance thresholds after viewing candidate results.
A post-freeze correction to a test or requirement needs a new version, a stated reason, and an explicit rerun policy for
reference and both candidates; retain the original results. Candidate-informed checks are
supplemental and cannot silently replace the primary comparison.

## Implementer inputs and isolation

Give each fresh implementer only the frozen spec, identical task brief, general OS API
(application programming interface) documentation, and a prepared build environment. Inventory
and hash the supplied files, scaffolding, prompts, and tool configuration. Record every
hardware fact supplied outside the spec; keep device-specific behavior out of scaffolding.

Exclude the reference device source and headers, alternate implementations, hardware source
documents, the author manifest and source downloads, answer key, documentary review findings,
and the other arm's artifacts. The spec may contain citations; following them is disallowed
in this spec-only experiment. Prepare a sanitized OS tree or software development kit (SDK),
including any necessary
build-system edits, so the original driver cannot be recovered from history, caches, installed
source packages, or alternate paths. Reference builds live in a separate evaluator environment.

Enforce filesystem and network restrictions and validate them before the run. Use the same
neutral isolation instructions for both arms. Any implementation skills or supplementary
instructions must be identical and pinned; do not introduce a second treatment accidentally.
Record actual access controls and available access evidence. File hashes and packet binding
do not prove context isolation, reviewer independence, or absence of training familiarity.
A detected forbidden-source exposure invalidates the primary spec-only interpretation; preserve
and label the result rather than quietly rerunning it as though nothing happened.

Use the existing [hook](skills/cleanroom-implementer/scripts/cleanroom_hook.py),
[policy](skills/cleanroom-implementer/assets/cleanroom-policy.json), and
[session audit](skills/cleanroom-implementer/scripts/session_audit.py) where the chosen harness
supports them, with validated OS-neutral and spec-only settings. The evaluator can also use
[leak_scan.py](skills/os-investigator/scripts/leak_scan.py) against reference source. These
checks detect some prohibited access or text overlap; they do not prove absence of exposure.
The filesystem/network restrictions remain necessary and must be tested in the chosen harness.
Freeze scanner settings, thresholds, allowed identifier overlap, and whitelist/disposition rules
in R1a. Shared hardware register names or scanner hits alone do not establish source exposure.
Review hits against those rules and access evidence; unresolved hits remain unresolved, while
established forbidden-source access invalidates the primary interpretation. Do not tune the
whitelist after seeing a candidate without a declared new version and re-evaluation procedure.

Do not load the full `cleanroom-implementer` skill or its treatment-specific prose templates
into these runs: their tags and reading instructions can teach the baseline how to use the
treatment's structure. Use a neutral brief and validated mechanical controls. Any other
supplementary instructions must be format-neutral, identical, pinned, and listed in the manifest.

## Paired implementation runs

Use the exact frozen spec from each generation arm, with an opaque candidate ID. Do not disclose
arm labels, scores, review findings, or the other implementation. Spec style may reveal the
condition; record blinding as an attempt, not a guarantee.

Hold model/version/settings, tool access, environment, prompt, implementation skills, budget,
and stopping criteria constant. Record unknowns as unknown and material differences as unpaired.
The implementer model may differ from the spec-author model, but must be held constant across
implementation arms. Run separate contexts, without shared memory or cross-arm feedback.

Require a missing-information and assumptions log. Clarification requests receive no new
hardware facts during the primary run. A blocker is a result. Distinguish missing information
from justified uncertainty: a spec that correctly requires hardware verification has not thereby
made an erroneous claim. The neutral brief must explain this in ordinary language without
teaching the treatment's tags. Record such blockers as verification required, not automatically
as spec omission or ambiguity. Evaluators must check whether the fact was recoverable from
the author's permitted evidence: deferring a plainly documented, applicable fact is an omission,
not justified uncertainty. Use the frozen ledger and corpus to support this distinction; a
source-observed or inferred classification alone does not prove deferral necessary, and disputed
evidence remains an adjudication item. Before freezing the design, decide which can be checked by the
evaluator's fixture. Those checks may establish behavior after code freeze; any new facts or
changes supplied to an implementer belong to a separately reported repair experiment. Permit the same declared build
and smoke checks to both implementers; keep evaluator checks and their feedback unavailable
until both implementations are frozen. Archive unsuccessful and budget-exhausted attempts too.
No source-comparison feedback reaches the primary implementers.

Freeze code and logs at the declared stopping point. Both documentary reviews must finish
before either documentary score is computed, as ARMS.md requires; implementation can run in
parallel provided review feedback never crosses the boundary. Complete and freeze both
implementations before comparative evaluation or any repair experiment.

## Evaluate and attribute

Compare functionality and hardware requirements, not text similarity, symbol names, code
organization, or incidental ordering. Accept different valid implementations. Match exact
traces only where the hardware contract requires that sequence. Use the same declared tests,
configuration, and fixture conditions for reference and candidate drivers. Record ordering and
reset procedures to avoid state carried over from the previous driver.

| Evidence | Report | Limit |
| --- | --- | --- |
| Build and integration | Build, load/bind, initialization, shutdown results | Compilation alone does not establish hardware behavior |
| Ordinary operation | In-scope traffic or device operations | Does not exercise untriggered recovery paths |
| Boundary and recovery checks | Each scenario's result and exercised fault | Does not establish behavior outside those conditions |
| Bus/register traces | Required operations, order, timing, and side effects | Exact equality is not generally necessary |
| Source review | Requirement-linked differences with anchors on both sides | Linux, BSD, or any reference can contain defects |
| Implementer log | Blockers, assumptions, clarification requests, effort | Agents may omit assumptions or recall hardware facts from training |

Classify each discrepancy as spec omission/error/ambiguity, implementation error despite an
adequate spec, environment/test limitation, reference discrepancy, justified uncertainty requiring verification, or unresolved attribution.
Cite the spec passage or absence, requirement and source evidence, candidate behavior, and
reference behavior. Do not equate disagreement with the reference to failure. An evaluator
who has read source must not become the clean-side implementer in a repair run.

Report per-check pass, fail, awaiting fixture, blocked, not applicable, or unresolved, with
reasons and execution evidence. Keep unavailable checks visible. Report build success, tested
behavior, spec gaps, implementation errors, access violations, and resource use separately
from documentary recall/precision; do not average them into a single score. A successful driver
cannot erase a missing fact from the documentary result.

Two evaluators independently attribute each discrepancy without seeing each other's judgments
or the generation-arm labels. Preserve both readings; disagreements remain adjudication items
and are excluded from binary attribution counts until resolved. If independence is unavailable,
label the attribution provisional rather than claiming the protocol is complete.

Cross-tabulate each checked requirement's documentary coverage with its implementation outcome.
Correct behavior despite absent spec coverage suggests inference, prior knowledge, or an
outside-spec input; it does not by itself identify which. Keep implementation capability and
spec completeness distinct. This stage does not establish that an implementer can author
meaningful tests from the spec: evaluator-authored tests measure driver behavior only. That
part of the broader objective remains unmeasured here.

OS-integration guidance introduces a documentary interpretation limit. The frozen recall ledger
scores hardware requirements, while precision includes every claim. The existing citation
contract may not admit the general OS API evidence needed to verify added integration claims.
Keep the policy's denominators and citation rules unchanged; explicitly report this asymmetry
and any evidence-access limitations alongside the scores. More integration claims can increase
or decrease precision depending on their verdicts; do not infer a directional effect from claim
counts alone. This protocol does not promise a new partitioned precision metric or schema.
A future diagnostic partition needs its own defined, auditable claim classification and must
not replace frozen acceptance results.

## Repair, reproducibility, and scope of conclusions

After freezing primary results, an optional separately budgeted repair experiment may provide
a corrected spec passage to an isolated implementer. Preserve the original candidate, code,
failures, and scores; version the changed inputs and identify the additional information.
Improvement is diagnostic evidence about attribution, not a replacement primary result.

Archive the reconstruction manifest, spec hashes, exact prompts, allowed inputs, environment
pins, access records, candidate code, build commands/logs, tests and mutation evidence,
reference results, execution traces, gap log, findings, and costs. Keep sensitive environment
and session records outside public artifacts; publish sanitized role-based evidence.

One pair is a pilot observation, not a general effect estimate. One implementation per spec
adds implementation variability to generation variability without estimating either within-arm
variance; read results as per-check evidence, not a stable ranking of the two conditions. Repeated runs are needed before
claiming stable differences, and success cannot establish that the model lacked prior hardware
knowledge. Report the spec-author and implementer models and known relationships to evaluators.
Budget generation, documentary review, reconstruction, execution, and optional repair separately;
get run authorization before launching paid agent sessions or hardware operations.
