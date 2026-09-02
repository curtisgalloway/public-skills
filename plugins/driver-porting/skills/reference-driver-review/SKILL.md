---
name: reference-driver-review
description: >-
  Review a driver implementation against a reference implementation of the same hardware and
  produce an anchored findings report — missing init steps, wrong constants, absent errata
  workarounds, ordering/timing divergences — where every finding cites the file:line on both
  sides at pinned commits, so a reader can open either tree and check it. Defaults to the driver
  in the current directory as the implementation under review; locates the reference via a
  matching board-expert skill, or by asking the user (e.g. "the Pixel 10 USB PHY driver from the
  public kernel source release"). Use when asked to review, compare, diff, cross-check, or
  sanity-check a driver against an upstream, vendor, or original implementation. Reuses
  anchored-peripheral-spec's checkers via [impl:]/[ref:] anchors. Output is a review, never
  driver code — to write a driver from encumbered source use cleanroom-spec instead.
---

<!--
SPDX-FileCopyrightText: 2026 Curtis Galloway
SPDX-License-Identifier: Apache-2.0
-->

# Driver review against a reference implementation

You produce one **review report per driver**: the implementation under review compared against a
**reference implementation** of the same hardware — the upstream kernel driver, the vendor's BSP
driver, the original the port was made from. The report is a list of **findings** (divergences,
omissions, additions), and its discipline comes from `anchored-peripheral-spec`: every finding
cites the exact lines it was derived from **on both sides**, at pinned commits. A reader can open
the report, the implementation, and the reference side by side and confirm each finding is telling
the truth; the checker can tell you which findings need re-reading when either tree moves.

The anchors into the reference are the point, not a liability. A review that says "the upstream
driver waits after reset" is an opinion; a review that says it with
`[ref: drivers/phy/foo.c:412-415 (foo_reset)]` is a checkable claim that leads the reader straight
to the evidence. Maximize them.

This skill **reviews**; it does not spec and it does not port. To produce an implementation spec
from source you own, use `anchored-peripheral-spec`. To write a new driver from encumbered source,
use `cleanroom-spec` — a review of an *existing, independently written* implementation is exactly
the case where that wall is not needed.

## Intake: the implementation under review

**Default: the driver in the current directory.** When the user does not name an implementation,
take the driver source in and under the working directory; find its enclosing git repository
(`git rev-parse --show-toplevel`) and pin the current commit. If the directory holds more than one
driver, ask which one — do not review a bus's worth of drivers because a glob matched.

Before any comparison, identify the hardware from the implementation itself: `compatible` strings,
register `#define` names and base addresses, DT bindings, file and symbol names, build rules. Name
the **peripheral, the silicon IP block + vendor, and the SoC/board** it serves. Everything
downstream — choosing the reference, judging applicability — hangs on getting this right.

## Finding the reference

In order:

1. **A board-expert skill.** Check the available-skills listing for a board expert covering the
   SoC/board you identified (they describe themselves as "Board expert for <board/SoC>", e.g.
   `rpi-expert` for BCM2712/RP1). Spawn a subagent that loads it and ask one question: *what is
   the authoritative reference driver source for <IP block / peripheral> on <board> — repository
   or URL, branch/tag/release, driver file paths, and license?* Board experts maintain their own
   resource caches; let the expert (or the investigators below) fetch into that cache.
2. **The user.** If no board expert matches, or the expert does not know, ask the user which
   reference to compare against. Accept anything resolvable: a local checkout path, a repo URL and
   tag, or a description like "the Pixel 10 USB PHY driver from the public kernel source release"
   — in that case find the source release, fetch it, and locate the driver files yourself, then
   confirm the paths with the user if the match is ambiguous.

Check the reference out **outside the implementation repo** (a board-expert's cache or a scratch
directory), pin the commit, and never copy reference files into the implementation tree. Record in
the report how the reference was chosen and why it is authoritative for this hardware.

**License posture:** reading and citing a reference — including a GPL kernel release — to review
your own independently written driver is ordinary engineering, and this report is a critique with
citations, not a derived work of the reference. Two rules keep it that way: quote the reference as
sparingly as the parent skill quotes anything (a few lines, only when the exact expression is the
finding); and when a finding leads to a fix, the fix states *facts* (register, value, ordering,
delay) — reference code is never pasted into an incompatibly-licensed implementation.

## The reference is evidence, not truth

The reference driver can be wrong, stale, or aimed at a different silicon revision. **"The
reference does it differently" is a question, never by itself a verdict.** The tie-breaker is the
databook: keep `[doc:]` citations exactly as in `anchored-peripheral-spec`, and let a document
settle every divergence it can. A divergence the document settles in the implementation's favor is
`[benign]` (record it — it is cheap confidence); one it settles against the implementation is a
`[bug]`; one nothing settles is `[suspect]` and goes on the verify-on-hardware list.

Section 2 of the report exists to bound this risk: state which IP revision(s) each side targets,
from version-register checks, compatible strings, and quirk tables on both sides — anchored. A
review against the wrong-revision reference manufactures false findings at scale.

## Anchor grammar

The grammar, tightness rules, block anchors, negative-claim rule, and quoting ration are
`anchored-peripheral-spec`'s — read its "The anchor grammar" section and apply it with two renamed
tags and pins:

```
[impl: <path>:<L1>[-<L2>] [(<symbol>)]]     resolves in the IMPLEMENTATION repo at the Impl pin
[ref:  <path>:<L1>[-<L2>] [(<symbol>)]]     resolves in the REFERENCE repo at the Ref pin
[doc: <document> §<section>]                a document citation; not resolved mechanically

Impl pin: <repo-name-or-url>@<commit>
Ref pin:  <repo-name-or-url>@<commit>
```

`anchor_check.py` accepts these as aliases (`impl`≡`src`, `ref`≡`tgt`, and the pin lines
likewise): `--repo`/`--impl-repo` resolves `[impl:]`, `--target-repo`/`--ref-repo` resolves
`[ref:]`, and `--drift` tracks the implementation side — the side that moves as fixes land.

## Findings

Every finding carries a **category**, exactly one **verdict**, anchors on **both sides**, and a
stated **consequence** (what goes wrong, or why nothing does). The categories:

- **differs** — both do it, differently: a value, a width, an ordering, a delay, an ack sequence.
  Anchor both sides.
- **missing** — the reference does something the implementation does not: an errata workaround, a
  quiesce step, a bounds check. Anchor the reference; the implementation side of an absence cannot
  be anchored to presence — cite the file or function extent and say the absence was established
  by search, so the verifier knows to repeat the search.
- **extra** — the implementation does something the reference does not. Often fine (target-OS
  idiom); still a finding, because it is where an implementation invents hardware behavior.

The verdicts:

```
[bug]      the implementation is wrong, for a reason that stands without the reference:
           a [doc:] backs it, or the defect is self-evident (acks the wrong bit, uses a
           register's offset as its mask). State the consequence.
[suspect]  a divergence nothing settles — no document found, both plausibly work. Goes on
           the verify-on-hardware list with what to probe.
[benign]   a divergence with a stated justification: the document permits both, the feature
           is unused on this board, a deliberate policy. The justification is part of the
           finding — "probably fine" is [suspect], not [benign].
[ref-issue] the reference looks wrong, or serves a different revision/configuration; noted
           so nobody "fixes" the implementation toward it.
```

## Required structure of every review

1. **Review notice (top of the document)** — implementation `<repo>@<commit>` reviewed against
   reference `<repo>@<commit>`; how the reference was chosen (board expert / user) and why it is
   authoritative; the evidence rule (the databook outranks both trees; the reference is evidence,
   not truth); every finding anchored on both sides; before trusting the review after fixes land,
   run `anchor_check.py --drift`; the verification record at the end says when the findings were
   last checked.
2. **Hardware identity & applicability** — the peripheral and IP block; which revision(s) each
   side targets (version checks, compatible strings, quirk tables), anchored both sides; the
   stated risk if they do not exactly coincide.
3. **Reference provenance** — repository, revision, license, how obtained, driver file paths.
4. **Correspondence map** — a table pairing implementation files/functions with their reference
   counterparts (probe↔probe, init↔init, ISR↔ISR…), anchored both sides, plus the unmapped
   remainder on each side — every unmapped entry either becomes a missing/extra finding or is
   explicitly out of scope with a reason.
5. **Comparison coverage** — which areas were compared (register offsets/masks/values; init,
   reset, and teardown ordering; delays and timeouts; interrupt enable/ack semantics;
   DMA/descriptor layouts; error and recovery paths; power/suspend/resume; quirks and errata;
   sub-protocols such as PHY tuning) and which were not, with reasons. A zero-finding area is a
   claim; say what was read to earn it.
6. **Findings** — `[bug]` first, then `[suspect]`, then the rest; each with category, verdict,
   both-side anchors, consequence, and the `[doc:]` that settles it when one exists.
7. **Agreements worth recording** — non-obvious values and sequences where both sides
   independently agree (brief; this is the review's positive evidence).
8. **Verify-on-hardware list** — every `[suspect]`, with what to probe.
9. **Open questions** — what neither tree nor any document settles.
10. **Verification record** — pins, date, verdict, checker/verifier report paths, spec sha256 at
    PASS; filled by the verifier/orchestrator, not the reviewer.

## How to run it

Fan out for the same reason the parent skill does — a reviewer holding two whole drivers in one
context writes a thin review — and delegate the reference reading so the drafting context stays
small:

1. The orchestrator resolves intake and the reference (above), then spawns one **review
   subagent** (`templates/review-subagent-prompt.md`, every `<angle-bracket>` placeholder
   filled). It writes the review to a scratch path and returns the path, a one-paragraph summary,
   and both pins.
2. The review subagent spawns **paired-slice investigators**, each reading its slice of *both*
   trees and returning findings that already carry `[impl:]` and `[ref:]` anchors with symbols:
   a **constants investigator** (register offsets, masks, magic values, from both sides'
   headers), a **sequences investigator** (probe/init/reset/teardown ordering, delays,
   timeouts), an **interrupts & DMA investigator** (enable/ack semantics, descriptor layouts),
   and an **error-path & quirks investigator** (recovery, errata workarounds, revision gates —
   where reference value is densest, because workarounds encode hardware facts no databook
   states). One investigator builds the **correspondence map first**; the others receive it.
   **Run the constants slice twice, independently**, and diff the two findings lists before
   drafting — a divergence only one investigator found is where an error was about to be written.
3. **Anchors are never invented at the drafting layer** — not for a line the drafter did not
   read and no investigator returned. A plausible wrong line number resolves fine; it is the one
   fabrication the checker cannot catch.

Single-context is fine for a small driver (a GPIO bank, a LED controller) where both sides fit
comfortably beside the review.

### Check, verify, land

1. **Mechanical check** (every review, before any human reads it):
   ```
   python3 <anchored-peripheral-spec>/scripts/anchor_check.py <review> \
       --impl-repo <impl checkout> --ref-repo <reference checkout> \
       -o docs/review-reports/<driver>-check-<date>.txt
   ```
   Then run the inventory check **against the reference headers** — it is the uncompared-register
   detector: every name in the reference's register headers that the review never mentions is a
   candidate missing finding, or must be listed as out of scope with a reason. Run it again
   against the implementation's headers for the mirror-image check. (`inventory_check.py` reads
   the `Impl pin:` for its default revision; pass `PATH@REV` explicitly for the reference run.)
   ```
   python3 <anchored-peripheral-spec>/scripts/inventory_check.py <review> \
       --repo <reference checkout>@<ref-rev> --headers <reference register header(s)>
   ```
2. **Independent verification** (a fresh subagent, `templates/verifier-prompt.md`): it re-runs
   the checker, reads the `--show` review sheet with both repos, and judges whether the cited
   lines on **each side** actually support each finding — including re-running the searches
   behind every `missing` finding, recomputing every count, and checking that each verdict is
   earned (`[bug]` backed by a document or self-evident; `[benign]` actually justified;
   `[suspect]` on the verify-on-hardware list). Verdict: `PASS + report path` or `FAIL + report
   path + {finding, spec line, anchor, one-line reason}` list.
3. **PASS** → move the review to `docs/<driver>-review.md` (or the project's review location),
   fill the verification record (pins, date, report paths, `sha256sum` at PASS).
4. **FAIL** → hand the verdict back to a review subagent to fix the flagged findings, then
   re-verify. A finding the verifier could not confirm from the cited lines is fixed by finding
   the right lines — or by deleting the finding — never by widening the anchor until it "fits".

### The review's lifecycle

A review drives fixes, and the fixes invalidate its `[impl:]` anchors. When implementation fixes
land: mark each addressed finding with its resolution and the fixing commit, then re-pin —
```
python3 <anchored-peripheral-spec>/scripts/anchor_check.py docs/<driver>-review.md \
    --impl-repo <impl checkout> --drift <new-rev> [--rewrite]
```
— exactly as the parent skill re-pins a spec: moved anchors are rewritten, changed ones gain
`[stale:]` markers that fail every later check until the finding is re-verified or closed. The
reference side rarely moves; if it does (a new upstream release worth re-reviewing against),
that is a new review, not a re-pin.

## Quality bar

- Every finding carries both-side anchors (or an extent-plus-search statement for an absence),
  exactly one verdict, and a consequence; nothing is `[bug]` on the reference's word alone.
- Anchors follow the parent's tightness rules: definitions and performing statements, ranges as
  tight as the claim, symbols always.
- The correspondence map covers every implementation entry point, and every unmapped reference
  function is a finding or an explicit out-of-scope entry.
- Hardware identity (section 2) states the revision-match risk before any finding depends on it.
- The inventory check reports no unexplained reference-header names; counts were recomputed.
- Reference quoting is rationed, and no reference code was pasted into the implementation.
- The checker reports zero errors at both pins, the verifier PASSed, and the verification
  record's hash matches the file.
