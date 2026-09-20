<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# ENC28J60 ledger: adjudication sheet

For one person to work through top to bottom in one sitting. Every decision is answered with a
letter or a number; someone else applies the answers to `ledger.yaml`. IDs omit `ENC28J60-`.
State of the ledger this sheet was written against: 205 rows, 197 active, 8 withdrawn, 36 rows
with provisional markers, 5 one-sided critical rows (`LEDGER-CONFLICTS.md`, "Corrections applied
2026-09-19").

## Terms

- **Ledger** — the answer key: one row per hardware requirement, in `ledger.yaml`.
- **Reader** — one of the two blind authors (A, B) of the drafts merged into the ledger. A row's
  `readers` lists who stated it; a critical row needs two, or a recorded independent review.
- **Weight** — `critical` (a driver that misses it does not work, or corrupts data), `important`
  (degraded or fragile), `minor` (completeness). Recall is reported per weight.
- **Class** — what kind of claim a row is: `documented-hardware-requirement` (a vendor document
  says it), `observed-software-behavior` (the reference driver does it), `inference`,
  `implementation-choice` (the driver's decision; a candidate is penalized for calling it a
  requirement, never for omitting it), `unresolved-conflict`. Class decides which denominator a
  row is in.
- **Overlap** — two active rows that state the same clause, so a candidate would be scored twice.
  The 2026-09-19 pass removed the overlaps the log and the first review named, but **five are
  open**: a second review on 2026-09-20 found clause-level duplication still in SPI-021, REG-029,
  RX-032, SPI-014 and RX-029. Each now carries an `overlaps:` list with no `replaced_by`, which
  is exactly what the freeze gate refuses, and each is a decision in **group F**.
- **Composite row** — one row that enumerates several independently falsifiable facts, usually a
  register's bit layout. Seven are exempt from the atomic-row rule by name in `SCORING-POLICY.md`
  (group A1); eleven more are unresolved and are **group G**.
- **Freeze** — the point after which the ledger's hash is recorded and candidates may be graded.
  `ledger_check.py --freeze` refuses while any provisional marker, one-sided critical row or
  undisposed overlap remains; its error count is the progress number (41 when this sheet was
  written, 30 after group A was applied, 35 once the five overlaps above were marked).

## A. Policy decisions that settle many rows

**Answered 2026-09-20: A1 = (a) and (d), A2 = (a), A3 = (a), A4 = (a)** — every one the proposed
default. Applied to `ledger.yaml` (weights and `weight_disputed` on the seven layout rows, classes
and `class_disputed` on the five disputed rows), to `LEDGER-FORMAT.md` (the A2 rule in the class
table, a pointer to the policy in the Scoring section) and in the new `SCORING-POLICY.md`
(`enc28j60-1.0`, the A4 denominator rule). The pass is logged in `LEDGER-CONFLICTS.md` under
"Adjudicated 2026-09-20 (group A)"; the freeze gate went from 41 errors to 30. Groups B to E are
still open.

**Second review, 2026-09-20.** An outside reviewer checked the four decisions and kept every
outcome: the seven layout weights and the five classes are unchanged. Three of the four
*rationales* did not survive, and were replaced rather than re-argued (`LEDGER-CONFLICTS.md` →
"Review corrections 2026-09-20"). What that means for this sheet: A1's stated rule — critical
where the driver must write the register — **was withdrawn as unsound** and the seven weights now
stand as the adjudicator's explicit judgments, each with its own consequence justification in the
row's `notes`; A1's exception to the atomic-row rule is now written down in `SCORING-POLICY.md`
instead of contradicting `LEDGER-FORMAT.md` silently; A2's rule was sharpened for the
policy/mechanism overlap; A3's reasons for PHY-022 and ERR-001 were corrected. Two new groups
follow from it: **F** (residual overlap) and **G** (the other composite layout rows). One error in
group B, item 14, was corrected in place.

**A1. Weight of register bit-layout rows.** Seven weight disputes are the same disagreement:
reader A weights a register's bit layout critical, reader B important. Rows: REG-010 (ESTAT),
PHY-007 (MICMD/MISTAT), PHY-008 (PHCON1), PHY-016 (PHSTAT2), PHY-019 (PHIE/PHIR) at A critical /
B important; PHY-017 (PHSTAT1), PHY-018 (PHCON2) at A important / B minor. The log said nine;
the other two in its pattern (SPI-011, INIT-012) are not layouts and appear in group B.
Corpus: each is one register definition in DS39662E. Consequence: under (a) a candidate that
omits a layout takes a critical miss; under (b) an important one. A candidate with a wrong bit
number is misstated either way. The review adds that a layout row holds many independently
falsifiable claims, so one wrong bit fails the whole row.
Choose one: (a) layouts are critical where the driver must write the register to function
(REG-010, PHY-007, PHY-008, PHY-019) and important where it only reads or never touches it
(PHY-016, PHY-017, PHY-018); (b) all seven take B's lower weight; (c) all seven take A's
higher weight. Then: (d) keep one row per register, or (e) split every layout row per bit
(about 18 rows become roughly 100; deferred atomicity, larger denominators).
Proposed default: (a) and (d).

**A2. What separates `observed-software-behavior` from `implementation-choice`.** Five rows
carry `class_disputed` and they are one question: INIT-010 (driver init sequence: A choice /
B observed), INIT-022 (full reinit on every open: A observed / B choice), TX-023 (timeout ->
close and reopen: A observed / B choice), RX-025 (accept only Received-OK and <= 1518 bytes: A
choice / B observed), IRQ-014 (edge-triggered host interrupt required: A choice / B observed).
Corpus: no vendor document requires any of the five. Consequence: an implementation-choice row
is never in a recall denominator and scores `misstated` when a candidate calls it required; an
observed row is scored for recall only under the run's policy (A4). Choose a rule: (a) a
behavior is a *choice* when the driver picked one of several options the corpus allows (a
value, a policy, a set of enabled sources, an ordering among valid orderings) and *observed*
when it is a mechanism the driver executes where the corpus is silent (a recovery procedure, a
handler structure); (b) A's class on all five; (c) B's class on all five. Under (a): INIT-010
choice, INIT-022 choice, TX-023 choice, RX-025 choice, IRQ-014 observed (the handler forces it;
the driver did not pick it among options). Proposed default: (a).

**A3. Applicability when the driver never uses the broken feature.** The merge set
`implementation_observed` false on PHY-015 (full-duplex loopback unreliable, issue 10) and
PHY-022 (LED code 1110, issue 11) because not using a feature is not applying a workaround, but
true on ERR-001 (DMA checksum aborts reception, issue 17) because the vendor names the software
alternative as the workaround. Corpus: issue 17's workaround is to compute checksums in
software; issues 10 and 11 offer an external loopback and alternate LED codes. Consequence:
the column feeds the "driver applies it" report, not recall. Choose: (a) keep the distinction
(true only when the vendor's workaround is the thing the driver does); (b) false on all three;
(c) true on all three. Proposed default: (a).

**A4. Scoring policy for observed-software-behavior and inference rows.** LEDGER-FORMAT scores
these for recall only when the run's policy says so. Active rows, regenerated from the settled
ledger after A2 moved INIT-022 out and IRQ-014 in: 10 observed (TX-022, RX-026, RX-030, RX-037,
IRQ-014, IRQ-018, IRQ-019, PHY-027, SPI-022, ERR-006) and 3 inference
(RX-006, RX-031, PHY-012). Consequence: (a) adds up to 13 rows to the recall denominator, with
RX-031 and RX-006 the two a working driver needs; (b) reports them as their own counts only.
Choose: (a) recall for inference rows, counts only for observed rows; (b) counts only for
both; (c) recall for both. Proposed default: (a).

## B. Remaining weight disputes (A's weight / B's weight -> proposed)

One clause of consequence each; the reason is what happens to a driver written from a spec
that misses the row.

1. SPI-002 (important / critical -> critical): CS raised mid-instruction abandons the byte;
   every multi-byte command fails.
2. SPI-003 (critical / important -> important): exceeding 20 MHz fails, but a missing ceiling
   more often means a slower bus than a broken one.
3. SPI-011 (critical / important -> important): a driver that switches banks for the unbanked
   registers still works, only slower.
4. SPI-013 (critical / important -> critical): a driver unaware that reads wrap at ERXND
   corrupts every frame that spans the end of the FIFO.
5. SPI-014 (important / critical -> critical): without the write-buffer command and its
   auto-increment nothing can be transmitted.
6. SPI-017 (critical / important -> critical): on B1/B4 with a slow asynchronous SPI every MAC
   register write can silently fail, which is a driver that does not work on that silicon.
7. REG-024 (important / minor -> minor): the DMA copy is optional and the driver never uses it.
8. INIT-009 (important / minor -> minor): order among MAC registers is unimportant; omitting the
   statement costs nothing.
9. INIT-010 (minor / important -> minor): implementation-choice; weight never enters recall.
10. INIT-012 (important / critical -> critical): without padding and CRC generation configured
    the MAC transmits frames as given; FULDPX mismatch leaves the device indeterminate.
11. INIT-019 (critical / important -> important): power save is optional (INIT-021); a driver
    that never enters it works.
12. INIT-020 (critical / important -> important): same; a driver that never sleeps never wakes.
13. RX-016 (important / minor -> minor): only the free-space computation needs it, and the
    driver uses that only to classify an error.
14. RX-029 (important / minor -> minor): duplication only — RX-002 and RX-018 already bind
    pointer programming. (Corrected 2026-09-20: the original reason, "the reset defaults are a
    working FIFO", is wrong. ERXST resets to 0x05FA (REG-013) while DS80349C issue 5 requires the
    receive buffer to start at 0x0000 (RX-003), so the reset layout does not satisfy the errata.)
15. TX-005 (important / critical -> critical): a transmission overlapping the receive FIFO
    corrupts received data.
16. TX-012 (important / critical -> critical): on B5/B7 in half duplex TXRTS never clears;
    transmit hangs.
17. PHY-004 (important / minor -> important): a driver that writes a PHY register expecting
    bit-level semantics clears bits it did not mean to, including PHLCON's reserved-as-1 bits.
18. PHY-010 (critical / important -> important): a driver assuming autonegotiation ends in a
    duplex mismatch, a degraded link rather than none.
19. PHY-011 (important / critical -> important): a driver relying on the reset PDPXMD gets the
    wrong duplex on some boards; PHY-012 is the fix.
20. PHY-014 (important / minor -> minor): a diagnostic mode; HDLDIS itself is PHY-013.
21. PHY-023 (important / minor -> minor): board workaround; the software consequence is PHY-012.
22. PHY-025 (important / minor -> minor): the driver never resets the PHY alone.
23. ELEC-001 (important / minor -> minor): a board fact; INIT-023 carries the software side.
24. ELEC-003 (important / minor -> minor): the driver has no reset pin.

Weights inherited across a split, for confirmation (the moving clause was never weighted by
the other reader): 25. TX-021 seven-byte status space, B important; A's compound row was
critical (proposed: critical, the vector overwrites the receive buffer). 26. PHY-028 change
duplex only with TX/RX idle, B important; A's row critical (proposed: important). 27. PHY-029
scan mode, B minor; A's row important (proposed: minor). 28. REG-012 13-bit pointer width, A
important; B's row critical (proposed: important).

## C. One-sided critical rows

Options for each: (a) the counterpart's compound row counts as the second reading, add the
reader; (b) a second reader derives it from the corpus before freeze; (c) a structured
`independent_review` (the checker now requires a mapping with a reviewer not among the readers,
the locators consulted and a disposition); (d) downgrade to important, which drops the
two-reader rule.

1. INIT-024 (program MAADR; B only). No A row states it at all. Proposed: (b) or (c).
2. REG-005 (ETH/MAC/MII grouping by name prefix; bank 3's E registers take no dummy byte; A
   only). B stated membership inside REG-003/REG-004, not the rule. Proposed: (c).
3. REG-029 (EIR layout with per-bit access legend; B only). A stated the bit positions in
   IRQ-001 and every access fact across IRQ-007/008/009/010/011/012. Proposed: (a).
4. SPI-021 (AUTOINC must be set for streaming; B only). A stated the conditional in
   SPI-013/SPI-014 and the reset value in REG-009. Proposed: (a); alternatively withdraw into
   those three rows with `replaced_by` (answer "w").
5. RX-032 (accepted packet increments EPKTCNT, sets PKTIF, advances ERXWRPT; rejected packets
   discarded without indication; B only, narrowed). The pieces appear in RX-013, RX-015 and
   IRQ-007 from other angles. Proposed: (d), since the enabling clause that made B's original
   row critical now lives in RX-018.

## D. Possible omissions (log section 5): add a row, or not

1. Driver sends the System Reset Command through its two-byte write helper, so a second 0xFF
   follows on the wire. Add as observed-software-behavior, minor? (y/n) Proposed: y.
2. Driver treats a PHLCON write timeout as PHY absence and aborts initialization. Add as
   implementation-choice, minor? Proposed: y (a precision probe).
3. Whether ECON1.TXRST clears ESTAT.TXABRT/LATECOL is not in the corpus; the driver relies on
   it. Add as unresolved-conflict with `recoverable: false`? Proposed: n (TX-007's notes record
   the gap; no class fits a fact no source states).
4. Driver refuses a MAC address change while the interface is running. Add as
   implementation-choice, minor? Proposed: y.
5. Driver rewrites ERXFCON from its receive-mode handler while RXEN is set, against section
   7.2.1's recommendation. Add as observed-software-behavior, minor? Proposed: y (a candidate
   that copies the driver here is misstated against RX-018; a row makes that visible).
6. After a late-collision retry the driver's ETXND is at the region end, not the frame end.
   Add? Proposed: n (TX-022's notes already carry it as unresolved).
7. MIREGADR is 5 bits wide (PHY address bits 7:5 unimplemented). Add as
   documented-hardware-requirement, minor? Proposed: y.

## E. What Part 1 could not settle

1. IRQ-016 scope (wake-on-LAN): A in scope, B out (not in the brief's coverage list). Marker
   `in_scope_disputed` added. Choose: (a) in scope; (b) out of scope. Proposed: (b), matching the
   brief; the row stays so a candidate that mentions it is not penalized.
2. REG-007 (driver header names registers DS39662E marks reserved; A's unresolved-conflict row,
   minor). B chose notes over a row, and the checker warns the statement does not present two
   readings because it is a driver-versus-datasheet gap, not a reader conflict. Choose: (a) keep
   as is and accept the warning; (b) reclass observed-software-behavior; (c) withdraw with the
   content left in REG-002/REG-003 notes. Proposed: (b).
3. ERR-006 open question (`unresolved: true`): whether any of the driver's unconditional
   workarounds degrades a revision the errata do not mark. Leave unresolved (a) or drop the flag
   because the row now claims only the observation (b)? Proposed: (a).
4. INIT-004 applicability was reverted to the driver's alone (vendor_confirmed empty); confirm
   (y/n). Proposed: y.
5. The A-only rows credited to B on the log's own evidence (REG-011, REG-012, REG-019, REG-025,
   REG-027, INIT-002, INIT-023, RX-010, RX-014, TX-009, ERR-003/004/005) and the B rows credited
   to A after a compound row was narrowed (SPI-019, SPI-020, TX-021, PHY-028, PHY-029): confirm
   the crediting rule "a reader who stated the clause inside a compound row is a reader of the
   atomic row" (y/n). Proposed: y. If n, INIT-002 and RX-010 return to group C.
6. Still open from the log, for the record: the drafts' verbatim driver quotations (section 7;
   the drafts stay unpublished in the session scratchpad and are not in this repository). The
   corpus.yaml section 6 corrections landed in commit `dfecb61`, and the checker gaps the review
   listed landed in `a8c7b9b` and `c16d628`; neither needs a decision here.

## F. Residual overlap

Five active rows still state a clause another active row states, so a candidate that writes the
clause once is credited — or penalized — more than once. Each row now carries an `overlaps:` list
with no `replaced_by`, which the freeze gate refuses, so the count carries the work until these
are answered. Precision deduplication does not fix this: it merges the candidate's claims, not the
ledger's recall units.

Options for each: **(a)** withdraw this row into the named rows with `replaced_by`; **(b)** narrow
this row to the clause no other row states; **(c)** keep both and accept the double count — which
means **explicitly authorizing duplicated recall contribution for the named clause**, recorded as
its own named exception in `SCORING-POLICY.md` listing the row pair and the clause. Option (c) is
not the composite-unit exception of group A1: that one says a single row's several facts score as
one unit, and says nothing about two rows sharing a clause. They are different problems and need
separate text.

1. **SPI-021** (AUTOINC must be set for streaming). Duplicated: the AUTOINC-advances-the-pointer
   semantics, in SPI-013 and SPI-014; the reset value, in REG-009. Nothing is left over — the
   "must be set" framing is the same fact as SPI-013's conditional. Proposed: **(a)**, because no
   clause survives the narrowing, and it also settles C4.
2. **REG-029** (EIR layout with per-bit access legend). Duplicated: the read-only and
   host-clearable access facts, across IRQ-007 to IRQ-012. Unique: the EIR bit positions and the
   reserved bit, which no active row states since IRQ-001 was narrowed to EIE. Proposed:
   **(b)**, narrow to the bit positions and cite the IRQ rows for access.
3. **RX-032** (accepted-packet consequences plus silent discard). Duplicated: EPKTCNT increments
   (RX-013), PKTIF is set (IRQ-007), the write pointer advances (RX-015). Unique: a packet that
   fails the filters is discarded with no indication to the host. Proposed: **(b)**, narrow to
   the silent-discard clause, which is the part a driver author can get wrong nowhere else.
4. **SPI-014** (Write Buffer Memory). Duplicated: the command encoding (opcode 011, constant
   0x1A, byte 0x7A), in SPI-005. Unique: MSb-first data bytes, storage at EWRPT, the AUTOINC
   advance, and the 0x1FFF-to-0x0000 wrap. Proposed: **(b)**, narrow to the streaming behavior
   and let SPI-005 own every opcode encoding.
5. **RX-029** (program ERXST/ERXND before enabling reception). Duplicated: pointer-before-enable,
   in RX-002 and RX-018. Unique: the data sheet's recommendation that ERXST be even. Proposed:
   **(b)**, narrow to the even-ERXST recommendation — the only placement rule the data sheet
   itself states — which also makes B14's minor weight follow from what is left.

## G. Remaining composite layout rows

Group A1 exempted seven rows from the atomic-row rule by name. Eleven more bundle independently
falsifiable facts the same way and were not covered by that decision, so `LEDGER-FORMAT.md`
authoring rule 3 still applies to them unamended: today a candidate that gets one bit wrong in any
of these fails the whole row, and no written rule says that is intended. `SCORING-POLICY.md` says
the exception covers the seven ids and no others, and points here.

Options for each: **(a)** enumerate it as an additional composite scoring unit in
`SCORING-POLICY.md` (one denominator unit, the group A1 verdict rule); **(b)** split it into
atomic rows; **(c)** narrow it, moving the clauses that are not layout to rows of their own.
Answering **(a)** for a row requires a new policy version, since the id list is part of the frozen
policy text.

1. **REG-008** (ECON1). Seven bit positions and meanings plus the all-zero reset. Proposed:
   **(a)**, one register definition read as one unit, exactly the shape of the seven.
2. **REG-009** (ECON2). Four bit positions and meanings, AUTOINC's set-after-reset value, VRPS's
   dependence on PWRSV, one reserved bit. Proposed: **(a)**; note the reset-value clause is also
   F1's duplicated clause, so answer F1 first.
3. **REG-018** (MACON3). The PADCFG field plus five single-bit configuration flags. Proposed:
   **(a)**; the PADCFG encodings already live apart in REG-019, so what is left is one layout.
4. **REG-021** (MACON1). Four bit positions and one reserved bit. Proposed: **(a)**, same shape.
5. **REG-022** (MACON4). Three bit positions, their half-duplex-only scope, two reserved bits.
   Proposed: **(a)**, same shape.
6. **REG-029** (EIR). Bit positions plus a per-bit access legend. Proposed: **(c)**, which is F2;
   answer it there, and whatever remains takes (a) with the rest of this group.
7. **RX-011** (receive status vector). Thirteen status-bit positions plus the reserved and
   always-zero bits. Proposed: **(a)**; a vector is one table and a candidate reproduces it or
   does not.
8. **RX-019** (ERXFCON). Eight bit positions, the ANDOR any/all combination rule, CRCEN's
   ordering after the other filters, and the promiscuous all-zero value. Proposed: **(a)**, since
   the 2026-09-19 pass deliberately withdrew RX-034 into this row; splitting would undo that.
9. **IRQ-001** (EIE). Eight bit positions including the global enable and one reserved bit.
   Proposed: **(a)**, same shape.
10. **TX-008** (transmit status vector). Roughly twenty fields across seven bytes, plus the
    little-endian packing. Proposed: **(a)**; the largest of the set, and the strongest case that
    the verdict rule needs `partial` to mean something, which group A1's rule supplies.
11. **PHY-020** (PHLCON). Four bit fields, the reserved-as-1 bits 13-12, the reset value, and a
    table of six common LED codes. Proposed: **(c)**, moving the code table to its own row: the
    codes are a lookup a driver selects from, not part of the register's layout, and PHY-022
    already turns on which code is programmed.

Answer format: A1 letter+letter, A2 to A4 letter, B1 to B28 a weight word, C1 to C5 letter
(or "w" on C4), D1 to D7 y/n, E1 to E5 letter or y/n, F1 to F5 letter, G1 to G11 letter.
