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

HOW TO READ (fan out, then draft): do not read the whole tree yourself. Spawn investigators, each
owning one slice and returning ANCHORED facts — tables and steps that already carry
`[src: path:L1-L2 (symbol)]` tags: a register-map investigator (headers, register typedefs,
device tree), a sequences investigator (probe, init, power on/off, teardown, error paths), a
firmware/tuning investigator if there is a blob or a table path, and a target-tree surveyor for
HALF 2 (returns `[tgt:]` anchors). Run the REGISTER-MAP slice TWICE with two independent
investigators (same brief, no shared context) and diff their tables before drafting: every
disagreement — an offset, a width, a bit, a register only one of them found — gets a third look
against the header before it is written down. You synthesize; open the source only to settle a
conflict between investigators or to tighten an anchor. NEVER write an anchor for lines you did not read or
that an investigator did not return — a plausible wrong line number resolves fine and is the one
fabrication the checker cannot catch. (For a small single-file peripheral you may read it all
yourself.)

ANCHORING RULES (the point of this spec):
- Every fact derived from source carries `[src: <path>:<L1>[-<L2>] (<symbol>)]` — repo-relative
  path, 1-based inclusive lines, and ALWAYS the symbol (the #define / struct / function the lines
  belong to). Every datasheet fact carries `[doc: <document> §<section>]` with a section, chapter,
  or table number. A fact with neither is an error. Prefer both: the datasheet says why, the
  anchor says where.
- Anchor the LOAD-BEARING lines, as tight as the claim: a register offset → its #define; a bit →
  its mask; a layout → the struct; a sequence step → the statement(s) that perform it, not the
  guard above them, not the helper's body, not the enclosing function; a claim about how a
  register is accessed (readw/readb) → an accessor call; a claim resting on a call site → the call
  site. A negative claim ("never written", "no handler in the file") cannot be anchored to
  presence: cite the file's extent and say it was established by search.
- A line containing only tags anchors the table or list that follows it (block anchor). Blank
  lines between are fine; a sentence between is not. Rows from elsewhere carry their own tag.
- State the pins once near the top on their own lines: `Source pin: <repo-name>@<commit>` and
  `Target pin: <target-name>@<commit>`.
- Quote at most a few lines, only when the exact expression matters, and still anchor it.

HARDWARE VS DRIVER: a `[src:]`-only fact says what the driver does, not what the silicon
requires. Label every sequence step and hardware-behavior claim with exactly one of
`[hw-required]` (a document says so — must also carry `[doc:]`), `[comment-explained]` (the
code's own comment or commit gives the reason — anchor it), `[driver-choice]` (policy; hardware
permits alternatives), or `[as-implemented]` (nothing found says why — unverified against the
hardware). Registers the driver never touches may appear with `[doc:]` only, so the register map
covers the block, not just the driver's footprint. Do NOT load `os-investigator`. Use
`<board-expert>` for board specifics and cached references.

SELF-CHECK before returning (fix every error and every warning you cannot justify):
    python3 <this-skill>/scripts/anchor_check.py <scratch path> --repo <source checkout> \
        [--target-repo <target checkout>]
    python3 <this-skill>/scripts/inventory_check.py <scratch path> --repo <source checkout> \
        --headers <the register header(s), repo-relative> \
        --dt <the board .dtsi, repo-relative> --dt-node <the node label>
The inventory check lists header names and device-tree items (names, SPIs, reg bases, phandles,
constants, boolean properties) the spec never mentions: cover each, or list it explicitly as out
of scope with a reason. Then read a sample of `anchor_check.py … --show` and confirm the
cited lines say what the claims say. Recount every count you state ("eight entry points", "a
3-word hole") against the code before you return it.

OPEN the spec with the PROVENANCE NOTICE (required section 1): derived from <repo-name>@<commit>;
every fact anchored; the source is authoritative — where they disagree fix the spec; run
`anchor_check.py --drift` before trusting the spec at a newer commit; the verification record at
the end says when the claims were last checked.

Cover (HALF 1 hardware): IP identity & provenance (incl. the driver's own identity checks,
anchored); canonical references TABLE (datasheets + public proxies + the pinned source); register
map (grouped per databook, offsets+bits, anchored; untouched registers from documents); ordered
init sequences (prerequisites, steps anchored to the performing statements, every step labelled);
data/descriptor formats; interrupts (routing, status bits, ack/clear, handler anchored — or the
evidence of absence); DMA/addressing; sub-protocols.
Cover (HALF 2, target tree at <target path>, if any): which existing driver to model on, the OS
protocol(s) to implement, reuse-vs-write, bind rule + board node shape, packaging — each claim
with a `[tgt:]` anchor. If source and target are the same tree, say so and use `[src:]`.
End with: milestones; consolidated gotchas (anchored to the workaround code); per-area confidence
(datasheet+code / code only / inferred); the VERIFY-ON-HARDWARE LIST (every `[as-implemented]`
claim and every register whose width, reset value, or bit position rests on code alone); OPEN
QUESTIONS (what neither code nor documents settle — an empty list is a claim the verifier will
test); and an EMPTY verification record (pins, date, verdict, report paths, sha256).
Be exhaustive on registers/sequences/references — every claim must be checkable against the
pinned tree.
