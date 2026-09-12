<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Planning document templates

Use these when creating new artifacts. Replace placeholders with project-specific content,
adapt paths to project conventions, and omit inapplicable sections. Do not replace an
existing authoritative document just to match these headings.

## Design

```markdown
# <Project or feature> — Design

Revision: <date or revision identifier>

## Goal and non-goals
Who benefits, observable outcomes, scope, and exclusions.

## Current behavior and constraints
Relevant source, existing tests/build setup, compatibility, and platform constraints.
Distinguish observations from assumptions.

## Requirements and acceptance criteria
- R1: <observable requirement and how success is checked>

## Architecture and behavior
Components, responsibilities, interfaces, data formats, and important flows.
Include error handling and recovery. Identify proposed file/module locations.

## Key decisions
Decision, alternatives considered, rationale, and consequences.

## Cross-cutting concerns
Applicable migration, security, performance, and operational behavior.

## Verification strategy
Test levels, known commands, expected outcomes, and manual/hardware checks.

## Risks and open questions
Unknown, impact, investigation/decision needed, and dependent work blocked by it.
```

## Implementation plan

```markdown
# <Project or feature> — Implementation Plan

Design: [design](design.md), revision <identifier>
Project checks: <known commands and prerequisites>

## Conventions
Working branch: <branch>
Checkpoint commit prefix: <prefix>
Design gate: <approved revision/date, unchanged authoritative design, or explicit waiver>
User overrides: <scope and duration of any waiver or execution override; otherwise none>
Review method: <review-swarm / reviewer subagent / self-review; note any milestone that
differs. Naming it here authorizes it; executing sessions do not re-decide.>
Review order: review and fixes precede the checkpoint commit, which is the last step.

## Status
| ID | Outcome | Dependencies | Status |
|----|---------|--------------|--------|
| M1 | <cohesive capability> | <prerequisites> | pending |

## Design coverage
| Requirement | Milestones | Verification |
|-------------|------------|--------------|
| R1 | M1 | <test/check> |

## M1 — <Outcome>
**Design coverage:** R1
**Dependencies:** <milestones, decisions, tools, or environment>
**In scope:** <functionality>
**Out of scope:** <exclusions>

### Implementation steps
1. <Concrete change to a component/interface; label proposed files as proposed.>

### Acceptance criteria
- [ ] <Observable pass/fail condition>

### Testing and review
- Tests to add or update: <behavior, errors, edge cases, integration>
- Verify with: <known commands/manual steps and expected results>
- Review focus: <design contracts, regressions, coverage, scope>
- Review method: <inherit the conventions block, or name a different one and why>

### Session sizing
Files/context needed to start, uncertainty, and a safe split/checkpoint if work grows.
Budget for implementation, tests, review, fixes, and handoff before compaction.

### Evidence and findings
Status: pending
Evidence: [M1 evidence](evidence/M1.md)
Limitations and blockers: <record any unmet requirements>

When complete, move this milestone's detailed entry into its evidence file and retain
only ID, outcome, dependencies, status, evidence link, and open limitations here.

## Final system verification
Cross-milestone scenarios, full-design acceptance checks, and required regressions.
Assign these to a milestone or explicit final gate with recorded evidence.

## Discovered work / backlog
Out-of-scope finding, impact, and proposed follow-up. Completion blockers stay with
their milestone; this section cannot be used to waive acceptance criteria.

## Next session
- Current milestone and status: <complete / in_progress / blocked>
- Completed work and evidence: <summary and links>
- Commits for this milestone and any uncommitted state: <expected: none for milestone
  work; identify unrelated pre-existing changes separately>
- Remaining work, blockers, and decisions: <specifics>
- Context boundary: <normal completion / early stop / unexpected compaction>
- Resume action: <resume unfinished milestone OR begin next eligible milestone>
- Read first: <design, milestone, evidence, and a small set of relevant files>
```

## Milestone evidence

Create `docs/evidence/<milestone-id>.md`, adapting the path to project conventions.
Keep output excerpts relevant to the verdict rather than copying entire logs.

```markdown
# M1 — <Outcome> evidence

Design: <relative link and revision>
Starting revision and pre-existing changes: <record at execution start>

## Milestone definition
Preserve the detailed plan entry here on completion, including design coverage,
implementation steps, acceptance criteria, and verification requirements.

## Verification
Commands/checks, outcomes, relevant output excerpts, and manual/hardware results.

## Review
Review method actually used, and where the review happened: a run directory, the
reviewer's returned findings, or the per-criterion checklist for a self-review. Then
findings with severity, fixes, and subsequent verification/review. A section asserting
a review without an artifact or a named reviewer means the review did not happen.
Record when the review ran relative to the checkpoint commit; it should precede it.

## Limitations and blockers
Unmet requirements, pre-existing failures, and explicit nonblocking follow-ups.
```
