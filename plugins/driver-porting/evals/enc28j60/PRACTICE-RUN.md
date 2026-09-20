<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# First practice attempt — 2026-09-20

Run `enc28j60-practice-20260920-01` exercised generation, boundary verification, both review
passes, scoring and offline replay. **Documentary acceptance is blocked; the semantic review is
incomplete.** This completes a workflow trial, not a validated benchmark or a usable driver spec.
No implementation or hardware result is claimed.

The user chose a fresh Claude practice context. Claude Code 2.1.278 exposed model
`claude-opus-5[1m]`; its relationship to the ledger authors is unknown. Generation used skill
revision `42dab3ef6ef58340506bd71b6a0902954778947f`. The 120,897-byte candidate has SHA-256
`516b7854e97fca4577d67922d2a49d174a80ebae9df9956d3a0738788f76bd06` and was not repaired during
review. The frozen ledger, facts, policy and corpus manifest were not changed.

## Diagnostic results

All nine source pins matched on retrieval. The candidate passed the unfiltered mechanical scan
and a separate reviewer’s five-part clean-room boundary check. That establishes the recorded
boundary decision, not technical correctness.

The coverage reader judged all 194 roster rows and 670 facts, including 162 recall rows,
13 observed-behavior rows and 19 implementation-choice probes. After conservative reconciliation,
the recall rows have these dispositions:

| Weight | Covered | Partial | Missing | Pending | Total |
|---|---:|---:|---:|---:|---:|
| Critical | 61 | 2 | 0 | 1 | 64 |
| Important | 49 | 4 | 0 | 4 | 57 |
| Minor | 38 | 2 | 1 | 0 | 41 |
| All | 148 | 8 | 1 | 5 | 162 |

These are provisional reviewer judgments. Eight fact dispositions could not carry through to
settled coverage; pending rows earn no credit, including their otherwise supported facts.
The raw coverage reader found contradictions at RX-031 fact 1 (receive-pointer initialization)
and PHY-012 fact 1 (the duplex-programming condition). Both become pending in the aggregate:
the former lacks an inventoried claim, and the latter conflicts with the accuracy readers.
The aggregate’s zero settled `misstated` rows does not mean those findings disappeared or were
resolved. Original judgments and reconciliation reasons are retained.

The active precision inventory contains 522 claim records after retiring 16 parents and adding
62 children; unresolved overlaps and bundled assertions make this an unreliable proposition count.
The aggregate has six disagreements, 23 pending claims, two partial claims and no settled FAIL. One reader did identify an attribution error at C0443; the other did not agree.
The 23 pending claims include review citations to the manifest or a repository alias that the
scorer’s exact source-name contract cannot represent. Those records were preserved separately,
without inventing replacement citations.

**No precision ratio is reported here.** Both computed ratios in the archived JSON equal one,
because no FAIL was agreed by both readers. That arithmetic is not an accuracy measurement:
one-sided failures remain unresolved, and the inventory still contains compound, overlapping
and missing assertions. The incomplete inventory audit and unresolved coverage block acceptance.

## Process limitations and retained evidence

- The author did not receive the ledger. Its corpus manifest nevertheless contained existing
  errata and revision analysis, and its prompt repeated skill structure. This was a practice run,
  not a blind with/without-skill comparison; no skill-effect estimate is available.
- The second accuracy reader’s first 476 judgments were made without first-reader judgments.
  For the final 62 children, the orchestrator supplied a revision file whose notes inadvertently
  exposed first-reader verdict summaries. The exposed notes asserted PASS for all 62 children;
  the reader returned PASS on all 62 and states it did not use the summaries. Those second-pass
  verdicts provide no independent confirmation. The reviewer disclosed this exposure. The mapping
  continuation received the same file; its earlier semantic coverage judgments remained byte-identical.
- Coverage had one semantic reader, without a second independent coverage pass. Its table is
  provisional, regardless of the separate two-reader accuracy workflow.
- File tools were restricted, with shell, network tools, hooks, automatic skills and MCP disabled.
  Three outside-workspace reads used the CLI’s own cached results from the allowed checklist or
  neutral inventory. An attempted shell call was denied. This is recorded harness behavior,
  not proof of operating-system isolation or training independence.
- Mapping hit its invocation budget after writing all link files and its audit. Host validation
  confirmed the exact roster, fact counts and valid claim IDs; the failed invocation is retained.
- Reported generation and review cost was approximately $50.23, excluding the separate consult
  review. Resumed CLI costs were cumulative and counted once per session. Generation was $5.24.

Private artifacts are retained outside this public repository under the run ID: candidate,
source inputs, hashes, prompts, commands, raw sessions, original and revised inventories,
both readers’ judgments, coverage, mappings, reconciliation, access audits and scan reports.
Attempt `01` is preserved. Attempt `02` adds the independence disclosure to run metadata without
changing judgments. Its archived-tool replay reproduced the full result except the timestamp.
No raw sessions, vendor PDFs or driver sources are committed here.

## Work before another benchmark run

1. Generate neutral inventory packets from an explicit field allowlist. Do not forward reviewer
   notes or verdicts to a second reader or a mapping-only continuation.
2. Finalize claim segmentation and deduplication before accuracy review; audit against every
   candidate assertion, including conflicting repeated instructions.
3. Validate source-name vocabulary before launching reviewers, and decide explicitly how corpus
   metadata claims fit the review contract. Keep the original evidence when conversion is blocked.
4. Put frozen fact text beside dispositions and separate review disagreement, citation conversion
   gaps and candidate omissions in reports. Do not headline a precision ratio for an incomplete
   inventory or treat a pending contradiction as resolved.
5. For a real comparison, use a pins-only author manifest and the same operating envelope in both
   arms, with treatment instructions absent from the baseline. Retain model-relationship unknowns.

Candidate-informed ledger concerns are logged in the private coverage audit for a future version;
none changed this run’s answer key. Phase 3’s paired evaluation and phase 6’s verifier integration
remain pending. This practice result does not complete either phase.
