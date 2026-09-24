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

## Terms

- **Run store** — the private directory outside this repository that holds each run's raw
  inputs, drafts, transcript paths, and review reports, one directory per run ID.
- **Reading** — one verifier subagent's pass over a spec, producing a verdict per claim.
- **Adjudication** — settling a claim on which two readings disagree.

See the [glossary](../../GLOSSARY.md).

## Open

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
