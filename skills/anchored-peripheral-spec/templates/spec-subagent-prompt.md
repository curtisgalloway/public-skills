<!--
SPDX-FileCopyrightText: 2026 Curtis Galloway
SPDX-License-Identifier: Apache-2.0
Fill-in prompt for the spec-writing subagent; substitute every <angle-bracket> placeholder.
-->

Produce a SOURCE-ANCHORED hardware/driver spec for <PERIPHERAL> (<IP block>, compatible
"<dt-compat>", on <bus>, CPU-phys <addr>, IRQ <irq>) from the driver source at <source checkout>
pinned at <repo-name>@<commit>, so an engineer can implement a <OS> <framework> driver in
<language>. <board/prereq facts>. The source is ours (or compatibly licensed): read it, cite it,
quote it sparingly. Load `anchored-peripheral-spec` and follow it.

OUTPUT: write the finished spec to <scratch path>. Return the spec path, a one-paragraph summary
(for the docs index), and the pins (`Source pin: <repo-name>@<commit>`, and `Target pin:` if a
target tree was read).

ANCHORING RULES (the point of this spec):
- Every fact derived from source carries `[src: <path>:<L1>[-<L2>] (<symbol>)]` — repo-relative
  path, 1-based inclusive lines, and ALWAYS the symbol (the #define / struct / function the lines
  belong to). Every datasheet fact carries `[doc: <document> §<section>]`. A fact with neither is
  an error. Prefer both: the datasheet says why, the anchor says where.
- Anchor the DEFINITION, not a use: a register offset → its #define; a bit → its mask; a layout →
  the struct; a sequence step → the statement(s) that perform it; a DT fact → the node in the
  .dts/.dtsi. Keep ranges as tight as the claim.
- A line containing only tags anchors the table or list that follows it (block anchor); rows
  from elsewhere carry their own tag as well.
- State the pins once near the top on their own lines: `Source pin: <repo-name>@<commit>` and
  `Target pin: <target-name>@<commit>`.
- Quote at most a few lines, only when the exact expression matters, and still anchor it.
- Say which orderings the datasheet requires, which the driver merely does, and which a code
  comment or commit explains (anchor the comment; cite the commit if that is where the reason
  lives); mark "reason not known" when you cannot tell.
- Do NOT load `os-investigator`; its rule forbids naming files. Use `<board-expert>` for board
  specifics and cached references.
- Self-check before returning:
    python3 <this-skill>/scripts/anchor_check.py <scratch path> --repo <source checkout> \
        [--target-repo <target checkout>]
  Fix every error and every warning you cannot justify. Then read a sample of
    python3 <this-skill>/scripts/anchor_check.py <scratch path> --repo <source checkout> --show
  and confirm the cited lines say what the claims say.
- OPEN the spec with the PROVENANCE NOTICE (required section 1): derived from
  <repo-name>@<commit>; every fact anchored; the source is authoritative — where they disagree fix
  the spec; run `anchor_check.py --drift` before trusting the spec at a newer commit; the
  verification record at the end says when the claims were last checked.

Cover (HALF 1 hardware): IP identity & provenance (incl. the driver's own identity checks,
anchored); canonical references TABLE (datasheets + the pinned source); register map (grouped per
databook, offsets+bits, anchored); ordered init sequence (prerequisites, steps anchored to the
performing statements, required-vs-habit labelled); data/descriptor formats; interrupts (routing,
status bits, ack/clear, handler anchored); DMA/addressing (ranges/dma-ranges anchored,
cache/coherency from the sync calls); sub-protocols.
Cover (HALF 2, target tree at <target path>, if any): which existing driver to model on, the OS
protocol(s) to implement, reuse-vs-write, bind rule + DT node shape, packaging — each claim with
a `[tgt:]` anchor. If source and target are the same tree, say so and use `[src:]` throughout.
End with: milestones (minimal-observable → full; prerequisite drivers), consolidated gotchas
(anchored to the workaround code), per-area confidence (datasheet+code / code only / inferred),
and an EMPTY verification record (pins, date, verdict, report path, sha256) for the verifier.
Be exhaustive on registers/sequences/references — this spec is the implementation source of truth,
and every claim in it must be checkable against the pinned tree.
