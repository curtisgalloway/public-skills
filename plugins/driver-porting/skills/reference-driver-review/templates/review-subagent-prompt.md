<!--
SPDX-FileCopyrightText: 2026 Curtis Galloway
SPDX-License-Identifier: Apache-2.0
Fill-in prompt for the review-writing subagent; substitute every <angle-bracket> placeholder.
-->

Review the <PERIPHERAL> driver (<IP block>, compatible "<dt-compat>") at <impl checkout>, pinned
at <impl-repo-name>@<commit>, against the REFERENCE implementation at <ref checkout>, pinned at
<ref-repo-name>@<commit> (<how the reference was chosen: board expert / user; license>).
<board/revision facts>. Load `reference-driver-review` and follow it; its anchor rules are
`anchored-peripheral-spec`'s with `[impl:]`/`[ref:]` tags.

OUTPUT: write the finished review to <scratch path>. Return the review path, a one-paragraph
summary (the headline findings), and both pins (`Impl pin: <impl-repo-name>@<commit>`,
`Ref pin: <ref-repo-name>@<commit>`).

HOW TO READ (fan out, then draft): do not read both trees yourself. First have one investigator
build the CORRESPONDENCE MAP (implementation file/function ↔ reference counterpart, anchored both
sides, plus the unmapped remainder on each side); give it to the others. Then spawn paired-slice
investigators, each reading its slice of BOTH trees and returning findings that already carry
`[impl: path:L1-L2 (symbol)]` and `[ref: path:L1-L2 (symbol)]` anchors: constants (register
offsets, masks, magic values, both sides' headers), sequences (probe/init/reset/teardown ordering,
delays, timeouts), interrupts & DMA (enable/ack semantics, descriptor layouts), and error paths &
quirks (recovery, errata workarounds, revision gates — read these closely; workarounds encode
hardware facts no databook states). Run the CONSTANTS slice TWICE with independent investigators
and diff their findings before drafting: a divergence only one found gets a third look against
both headers. You synthesize; open a tree only to settle a conflict between investigators or to
tighten an anchor. NEVER write an anchor for lines you did not read or that an investigator did
not return — a plausible wrong line number resolves fine and is the one fabrication the checker
cannot catch. (For a small driver you may read both sides yourself.)

EVERY FINDING carries: a category — differs (both do it, differently) / missing (reference does
it, implementation does not) / extra (implementation only); exactly one verdict — [bug] (the
implementation is wrong for a reason that stands WITHOUT the reference: a [doc:] backs it, or the
defect is self-evident), [suspect] (nothing settles it — goes on the verify-on-hardware list),
[benign] (justification stated in the finding; "probably fine" is [suspect]), or [ref-issue] (the
reference looks wrong or serves a different revision); anchors on BOTH sides; and the consequence.
The implementation side of a MISSING finding cannot be anchored to presence: cite the function or
file extent and say the absence was established by search. The databook is the tie-breaker — keep
[doc: <document> §<section>] citations; "the reference does it differently" alone is never [bug].

Quote the reference sparingly (a few lines, only when the exact expression IS the finding) and
never paste reference code into the implementation.

SELF-CHECK before returning (fix every error and every warning you cannot justify):
    python3 <anchored-peripheral-spec>/scripts/anchor_check.py <scratch path> \
        --impl-repo <impl checkout> --ref-repo <ref checkout>
    python3 <anchored-peripheral-spec>/scripts/inventory_check.py <scratch path> \
        --repo <ref checkout>@<ref-commit> --headers <reference register header(s)>
    python3 <anchored-peripheral-spec>/scripts/inventory_check.py <scratch path> \
        --repo <impl checkout> --headers <implementation register header(s)>
The reference-header inventory run is the uncompared-register detector: cover each reported name
or list it as out of scope with a reason. Then read a sample of `anchor_check.py … --show` and
confirm the cited lines on each side say what the findings say. Recount every count you state
before you return it.

OPEN the review with the REVIEW NOTICE (required section 1): implementation pin vs reference pin;
how the reference was chosen and why it is authoritative; the evidence rule (databook outranks
both trees; the reference is evidence, not truth); run `anchor_check.py --drift` after fixes land;
verification record at the end.

Cover, in order: hardware identity & applicability (which IP revision(s) each side targets —
version checks, compatible strings, quirk tables, anchored both sides — and the risk if they do
not coincide); reference provenance (repo, revision, license, paths); the correspondence map
(every unmapped entry becomes a finding or an explicit out-of-scope entry); comparison coverage
(areas compared and not, with reasons — a zero-finding area must say what was read to earn it);
FINDINGS ([bug] first, then [suspect]); agreements worth recording (non-obvious values both sides
agree on — brief); the VERIFY-ON-HARDWARE LIST (every [suspect], with what to probe); OPEN
QUESTIONS; and an EMPTY verification record (pins, date, verdict, report paths, sha256).
