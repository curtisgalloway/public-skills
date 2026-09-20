<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Remaining implementation plan: review evidence

## Terms

- **Plan** — the [remaining implementation plan](../IMPLEMENTATION-PLAN.md).
- **Consultation** — a persistent exchange with a read-only counterpart agent.
- **Checkpoint** — the local commit preserving reviewed planning work.

See the [glossary](../../../GLOSSARY.md). This is planning evidence, not evidence that any
implementation milestone or experiment has run.

## Scope and starting state

Planning started at `7068a53` with a clean working tree. The changes are the plan, its plugin
README link, shared glossary additions, and this record. The existing explanation commits are
ancestors of this branch; they are not changes authored by this planning task.

The user requested the project-plan skill and a Claude review before committing. Existing
designs were reused without material architectural changes. Pending models, budgets and
experiment reviewers were preserved. The review did not authorize new experiments or hardware
operations. PR 68 was separately verified merged with only the three trial-preparation files.

## Review method and retained artifact

The `consult` skill launched a read-only Claude Code session. The provider result reports
`claude-opus-5[1m]`; no model override was supplied. The reviewer could read and search project
files but could not run shell commands or tests. Its own answer explicitly disclosed that limit.

Consultation ID: `b711844f-38f5-451d-ba6f-41e34bf0a701`. Full prompts, returned findings,
confirmation and provider records are retained outside this public repository under that ID.
This public record preserves the substantive findings and dispositions without local paths or
raw session content. Temporary local storage is not a promise of indefinite transcript retention.

Review ran before the planning checkpoint. The first assessment read the plan and design/protocol
references plus relevant scoring/checking code. The operator then revised the plan and returned
the disputed points and verification evidence for a second reading.

## Findings and resolutions

| Finding | Severity assigned by reviewer | Resolution in the plan |
| --- | --- | --- |
| Hardware blocked the entire downstream path | High | M07/M08 split into offline and physical qualification/reporting. An adequate offline procedure trial can unblock M09–M12; M13 still requires physical trial results and qualified tests. |
| Human-review effort unmeasured; companion deliverable implicit | High | Separate human/agent effort accounting, M17 baseline, existing skill-set deliverable, and independently gated reduced-review/dedicated-skill follow-ons. |
| Practice-review exposure could influence baseline prompts | High | M09 records exposure, uses a fresh baseline-prompt author and independent prompt audit; M10c retains that evidence. Familiarity is a disclosed limitation; actual treatment leakage invalidates the intended baseline. |
| Starting state and branch publication topology unclear | High | The operator supplied the clean starting status and plan-only README diff. Current edits were authored during planning, not pre-existing. Branch ancestry and publication-base restrictions are explicit. PR 68's scope was checked separately. |
| Tool-byte changes could stale historical judgments | Medium-high | M03/M04 preserve documentary tool bytes for sidecar additions; later changes require versioning, staleness analysis and replay using archived tools. M16 inherits that rule. |
| Execution status translation could hide missing checks | Medium-high | Preserve protocol label and canonical disposition; awaiting/blocked cannot become not-applicable; unresolved attribution stays separate. |
| Generated-test measurement unnecessarily followed the full pair | Medium-high | M14 can use the practice spec and offline qualification in a separately authorized diagnostic trial, never as a paired arm. |
| Semantic-review sizing lacked a measured basis | Medium | Historical workload and budget exhaustion recorded; batch inventory, disjointness and completeness audits required before reviewer launch. |
| Privacy checks were narrower than evidence risks | Medium | Raw records stay outside the public repo. The plan states the path check's limits and additional evidence-review categories before staging. |
| Practice reviewer exposure could compromise later blinding | Medium | Fresh contexts, exposure disclosures and matched reviewer assignment; no historical judgments carried into the pair. No blanket ban on a reviewer model across arms, which could itself confound the comparison. |
| Missing commands, harness owner, OS-neutrality limit, backlog and operator sizing | Minor | Added missing suites/board check, D2 harness selection, interface-only OS-neutrality claim, schema-heading backlog item and operator-session sizing rule. |

The operator did not accept two factual/inferential shortcuts: this turn's uncommitted work was
not pre-existing, and using the same reviewer model across arms is not itself evidence of leaked
judgments. The consultation received the evidence and narrower controls rather than a request
to agree without resolving the distinction.

In the second assessment, Claude explicitly withdrew the starting-state finding and the proposed
unconditional reviewer ban. It accepted the substantive fixes and requested two further changes:
declare offline procedure-readiness criteria before the trial, and separate early companion-skill
usability checks from repair that needs attributed failures. Both were applied. Smaller fixes
clarified environment dependencies, offline check sizing, planning commit prefix, merged-PR
wording, patch-equivalence checks before dropping duplicate commits, and preference for an
equally capable reviewer pool without prior candidate exposure.

## Verification

Documentation-only changes; no implementation code or frozen input was edited.

- `git diff --check`: passed before final review.
- `python3 utilities/check-skill-registration.py`: 36 skills registered.
- Private-path check: passed, including the newly created plan explicitly; supplemented by
  review for private infrastructure, account identifiers and raw session content.
- Local Markdown targets: resolved; all M01–M17 definitions and R1–R9 coverage rows present.
- Direct SHA-256 checks against `ledger.lock`: all five locked artifacts unchanged.
- Scoring-schema discrepancy verified by reading: the document heading says review version 2;
  `score.py` and the later contract text name version 3. Assigned to the M11 prerequisite backlog.
- PR 68 scope verified through GitHub: merged, head `docs/reconstruction-trial-preparation`,
  exactly the trial README, run guide, and trial preparation record.

Historical checks at `de2bb68`, supplied to Claude as operator evidence: all 228 configured unit
tests ran, one skipped, no failures; registration/privacy/author-manifest/ledger checks passed;
the board check had nine existing missing-verification warnings. GitHub CI run `35542319847`
passed. These were not rerun for the planning-only edit and were not executed by Claude.

## Final disposition

Consensus recorded before the planning checkpoint. Claude's exact-text confirmation stated:

> I agree with this exact plan text. No material objections remain.

It also inspected this evidence record and reported no inaccurate attribution. The second-round
resolutions and withdrawn findings are preserved above. The operator verified that the on-disk
plan is byte-for-byte identical to the complete text supplied for confirmation, with SHA-256:

`64e47adce1523cfb65c30a9c84c09375005f27c47a2395b14cdde87572dfa923`

Claude could inspect the text but could not compute that hash; the byte check was performed by
the operator. Consultation closed with outcome `consensus` after the confirmation. The local
checkpoint message is `driver-porting: PLAN — structure remaining work and record Claude review`.
Agreement establishes a reviewed plan, not experimental validity or permission to launch
milestones. Implementation remains pending; next eligible work is M01.
