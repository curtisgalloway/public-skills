<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Process notes

Possible improvements to how the driver-porting work is run: the skills, briefs, review
gates, and bookkeeping. Progress on the project's goals goes in the
[plan](IMPLEMENTATION-PLAN.md) and the `evidence/` files, not here. Each note says what
happened, what it cost, and a proposed change. A note is a candidate, not a decision; when one
is acted on, record where and strike it through or remove it.

Since 2026-09-24T12:22-07:00 this file is also the project's process log under the
`lab-notebook` skill (the user chose this file before that skill was in use). Entries from
then on follow that skill's format under "Log entries" below, each with a status; the notes
under "Open" predate it and keep their form. Chapters of the lab notebook are in
[notebook/](notebook/index.md).

## Terms

- **Run store** — the private directory outside this repository that holds each run's raw
  inputs, drafts, transcript paths, and review reports, one directory per run ID.
- **Reading** — one verifier subagent's pass over a spec, producing a verdict per claim.
- **Adjudication** — settling a claim on which two readings disagree.
- **Operator** — the coordinating agent session that briefs and launches the other agents.
- **`consult`** — a skill that runs a review or discussion with the other coding agent (Codex
  from Claude Code), in a restricted read-only session.
- **Session auditor** — `cleanroom-implementer`'s `session_audit.py`, which scans an agent's
  transcript for forbidden reads and for source text that arrived by any route.
- **Antigravity** — Google's coding agent; several clean-room tools were written first for
  its file layout.

See the [glossary](../../GLOSSARY.md).

## Open

### 2026-09-24 (L02e)

- **The compiler was never pinned.** L02a pinned the kernel, the manual and QEMU, but not the
  toolchain. The test host's GCC 15 cannot build Linux v6.12 (ACPI header strings trip a
  warning GCC 15 makes an error), and finding that out cost a failed 32-core build plus a
  package install on the test host. Proposed: pin the compiler with the kernel, and make a
  kernel build a smoke test in the pinning unit, not the first unit that needs one.
- **A Claude subagent implementer has no enforcement layer that doesn't also bind the
  operator.** `cleanroom-implementer`'s hook is installed per workspace or per harness, so it
  would also apply to the operator and to every verifier that must read the source. Its
  transcript auditor reads the harness's transcript files, which agents here may not touch
  from the shell, so the audit has to be handed to the user. Proposed: a role-scoped way to
  launch the implementer (its own workspace with the hook, or a separate harness process) and
  an audit path the operator is allowed to run.
- **Operator files and implementer inputs share one run directory.** Review briefs and the
  audit policy name the paths the implementer must not open, so they had to be moved out of
  the run by hand while it worked; a file listing of the run root would otherwise have handed
  it the map. Proposed: a run layout with a separate operator directory the implementer brief
  never names, or an implementer-visible subdirectory that holds only its inputs.
- **The operator wrote a repair item from a verification-record label, not the spec.** Item H
  told the implementer that spec §5.1 requires a 32-bit mask unless the bus is PCI-X, taken from a
  verifier's claim key.
  The spec says a 64-bit mask is legal and gives a fallback; the implementer checked and
  declined the item, correctly. The operator had not opened the spec's text, although the
  landed spec is clean-side and fair for it to read. Proposed: a repair item that
  cites the spec quotes the spec sentence it relies on, checked by the operator before sending.
- **Three reviewers found one defect; one referee lowered its rating.** The transmit-stats double writer was found
  by the reference review, the requirements review, and the swarm; all three rated it
  medium, and the swarm referee lowered its arm's rating to low. Severity rubrics differ between the
  briefs (the swarm's is generic, the driver briefs' are hardware-specific). Proposed: give
  the swarm's arms and referee the same driver severity rubric as the other reviews.

### 2026-09-24 (L02c)

- **The run store's location is written down nowhere a new session can find it.** Evidence
  files name run IDs but not the root, and Spotlight does not index the directory, so finding it
  took several searches. Proposed: keep the root in a private discovery record (for example
  an environment variable or a local config file the skills read), and refer to it in public
  documents only by a placeholder such as `<run-store>`. A private location does not become
  fit to publish by dropping the username from its path.
- **Two readings of the same spec used different claim keys.** Only 277 of about 555 keys matched
  exactly, so merging the two readings needed a fuzzy, section-by-section comparison. Proposed:
  give both verifiers a mechanically extracted claim list with fixed keys, or ship a key
  extractor with `spec-verifier`.
- **The two-reading merge was an ad hoc scratch script.** It is the same step every time.
  Proposed: a `merge_records.py` in `spec-verifier` that aligns keys, marks disagreements
  ADJUDICATE, recounts the summary, and runs the leak scan.
- **The readers applied different verdicts to `[standard]` claims whose standard was not
  fetched.** One wrote PASS with a "not fetched" note, the other UNVERIFIABLE. That showed up as
  a disagreement although both readers saw the same thing. Proposed: `spec-verifier` should say
  a claim whose only authority was not read is UNVERIFIABLE, even when it is plausible.
- **Three of four adjudications were citation defects.** In one, both readers described the
  same wrong citation and differed only on whether it is a FAIL; in the other two, one reader
  passed the claim without mentioning the defect, so the records show differing verdicts, not
  necessarily differing policies. All three still went to the user. Proposed: when both readings
  describe the same discrepancy, treat it as a FAIL without adjudication; for a citation defect
  only one reader saw, a narrow third reader (next note) can confirm it before asking the user.
- **A narrowly briefed third reader settled the one factual disagreement cheaply.** It rendered
  one manual page and answered one question (about 78k tokens, under a minute). Proposed: make
  that the default first step for a factual disagreement, with the user deciding only if the
  third reader cannot settle it.
- **Units stack, but the one-branch-per-unit convention does not say how.** L02c needed L02b's
  plan updates before L02b's PR merged, so its branch was cut from L02b's. Proposed: say in the
  plan's conventions that a unit may branch from its predecessor's unmerged branch, and that its
  PR is rebased onto main after the predecessor merges.
- **Line-range citations into `include/` and `Documentation/` keep going wrong.** Across both
  rounds, three of the seven accuracy FAILs were `file:line` citations that pointed at the wrong
  lines or stopped one line short (a fourth mislabeled page numbers), and the fix for one of
  them introduced another. Each costs a
  reader round trip. Proposed: a mechanical checker that, for every HALF 2 citation with a quoted
  phrase, confirms the phrase lies inside the cited range at the pinned tree. This is the
  clean-room counterpart of `anchor_check.py`.
- **Copying a spec's sidecars into a new run leaves their headers pointing at the old run.**
  The provenance map copied into the L02c run still named the L02b run directory and draft
  path, which could send a later reader to another run. Proposed: a small "start run from
  previous run" helper that copies inputs and sidecars, rewrites run-relative headers, and
  rechecks hashes.
- **`leak_scan.py` silently skips files without a source extension.** The e1000 map lists a
  Makefile, which the scanner skips without saying so; the transfer reviewer scanned it by hand.
  Proposed: the scanner reports each skipped file, or scans every file the map names.
- **The recall assessor found a blind-list row that asks for more than the manual says**
  (INIT-005, transmit enable order). The list is frozen and has no way to record that. Proposed:
  a sidecar of post-freeze row notes, kept out of the recall denominator's definition, so a
  known-weak row is visible without rewriting the frozen list.

## Log entries

### 2026-09-24T12:22-07:00 — instruction gap: notebook opened mid-unit
Chapter: [L02e](notebook/L02e.md)
What happened: the `project-plan` skill gained a lab-notebook requirement during L02e; the
reload came after the implementation, reviews, and repair had run, so the chapter's first
entries were reconstructed from the run's ledger instead of written as they happened.
Cost: reconstructed entries carry the opening timestamp, not their real times; failed
attempts are recorded only as far as the ledger kept them.
Prevention: none needed going forward; the next unit opens its chapter at the start.
Fix belongs in: project-plan (already fixed upstream by adding the requirement)
Status: open

### 2026-09-24T12:22-07:00 — failed command: status poll matched the wrong field
Chapter: [L02e](notebook/L02e.md) (during L02c's `consult` review)
What happened: a shell wait loop grepped the `consult` status JSON for a "ready" status;
the first job's status matched while the consultation was still running, so the loop exited
early and the follow-up read failed with a `TypeError`.
Cost: one extra turn and a re-armed wait.
Prevention: parse the JSON and test the top-level `status` field, as the re-armed loop did.
Fix belongs in: consult (an example wait loop in its SKILL.md)
Status: open

### 2026-09-24T12:27-07:00 — surprise: build logs could not show their own flags
Chapter: [L02e](notebook/L02e.md)
What happened: the build wrapper printed its warning summary only to the screen and wrote
no record of its arguments, so the default and W=1 logs were byte-identical and a reviewer
could not tell from them that W=1 had been used.
Cost: one verbose rebuild on the test host to prove the W=1 claim.
Prevention: every build log records the command's arguments, the input hash, and the summary.
Fix belongs in: project instructions (the run layout's build wrapper); applied to this run's
wrapper
Status: fixed in the L02e run's build.sh

### 2026-09-24T12:52-07:00 — failed command: long command handed to the user wrapped on paste
Chapter: [L02e](notebook/L02e.md)
What happened: the operator gave the user a single 400-character `!` command for the
transcript audit; it wrapped into four lines when pasted, and the shell ran each line as a
separate command ("the following arguments are required", "permission denied").
Cost: one user round trip.
Prevention: a command handed to the user is one short line; put long invocations in a
script in the run directory and hand over `bash <script>`.
Fix belongs in: user instructions (the note on commands the user must run) or
cleanroom-implementer (ship an audit wrapper)
Status: open

### 2026-09-24T13:00-07:00 — surprise: the session auditor flags a clean Claude Code session
Chapter: [L02e](notebook/L02e.md)
What happened: `session_audit.py` reported 8 findings on the implementer's transcript, all
from reading its own driver, the allowed kernel headers, and a brief that asked for GPL
headers. Its workspace exemption and marker rules assume an Antigravity layout; on a Claude
Code transcript it cannot tell the implementer's workspace or allowed inputs from a leak.
Cost: a user decision and a triage subagent (reading records one at a time with the file-read
tool, which could not open the largest record at all).
Prevention: let the policy name allowed input roots and the workspace, and exempt results of
tool calls whose targets lie under them; report each finding with its tool call's target.
Fix belongs in: cleanroom-implementer (session_audit.py and the policy format)
Status: open

### 2026-09-24T13:09-07:00 — correction: two earlier log entries
Chapter: [L02e](notebook/L02e.md)
What happened: the entry "status poll matched the wrong field" describes an event during
L02c's review, earlier in the session; its 12:22 timestamp is when it was written, not when
it happened. The entry "the session auditor flags a clean Claude Code session" says the
auditor exempts workspace reads; it exempts results by tool name and has no notion of a
workspace. Found by the L02e public-changes review.
Cost: none beyond this correction.
Prevention: write log entries when the event happens, and name the mechanism from the code.
Fix belongs in: lab-notebook practice (no instruction change)
Status: open
