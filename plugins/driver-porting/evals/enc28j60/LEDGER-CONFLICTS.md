<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# ENC28J60 gold ledger: conflict log from merging blind drafts A and B

Merged 2026-09-19 from draft A (175 rows) and draft B (171 rows) into `ledger.yaml` (203 rows at
the merge, 205 after the corrections at the end of this file). The drafts themselves stay
unpublished: two of their `notes` fields quote the reference driver's comments verbatim, which the
clean-room rule does not allow in a repository artifact, and the merged rows paraphrase them. The merger added no rows and settled nothing by fiat: every item
below is for the adjudicator. IDs are the merged ledger's; a B-only row is named by its merged ID
with its draft-B ID in parentheses. "A x / B y" gives each reader's value.

Result in one line: 143 B rows paired with A rows (144 rows carry `readers: [A, B]`, because B is
also credited on RX-005, which B stated inside a compound row); 31 rows are A-only; 28 rows are
B-only; 31 weight disputes; 2 class disputes, neither involving a vendor-document claim; **no pair
disagreed on a fact**, so no `unresolved-conflict` row was created by the merge.

## 1. Class disagreements

Same requirement, both readers, class differs. Rule 4: neither side cites a vendor document for
the disputed claim, so the corpus cannot settle either; A's class is kept provisionally.

- ENC28J60-INIT-010 (B INIT-017): A implementation-choice / B observed-software-behavior. The
  driver's initialization order. A: one valid ordering, binds nobody. B: what the driver does.
  Kept implementation-choice; weight also disputed (A minor / B important, important taken).
  **Unsettled.** Both readings say a candidate must not present the order as required.
- ENC28J60-IRQ-015 (B IRQ-012): A observed-software-behavior / B implementation-choice. Which
  interrupt sources the driver enables. Kept observed-software-behavior. **Unsettled.**
  *Resolved 2026-09-19 by a split, not by fiat:* the row held two things. IRQ-015 now carries only
  the choice of enabled sources (implementation-choice, B's class fits); new ENC28J60-IRQ-019
  carries the count-based receive drain (observed-software-behavior, A's class fits). See
  "Corrections applied 2026-09-19".

Related rows, different requirement, classes differ (kept both; the sharpest kind, logged as the
brief asks):

- ENC28J60-INIT-018 (A, implementation-choice) vs ENC28J60-SPI-021 (B SPI-017,
  documented-hardware-requirement, critical). A's row: the driver's ECON2 write of AUTOINC is
  redundant (AUTOINC resets to 1). B's row: AUTOINC must be set for streamed buffer commands to
  auto-increment. Not merged because they state different things: the hardware semantics of the
  bit (which A also states inside SPI-013 and SPI-014) versus the driver's redundant write. A
  candidate that says "AUTOINC must be set" is right; one that says "the driver must write ECON2
  at initialization" is misstated. The adjudicator should confirm both rows stand as classed.
- ENC28J60-INIT-022 (A, observed-software-behavior) vs ENC28J60-INIT-021 (merged, both readers,
  implementation-choice) and ENC28J60-TX-023 (B TX-020, implementation-choice). Full reset on
  every open and on transmit timeout. A classes the behavior as observed; B splits the same
  behavior across two implementation-choice rows. Kept all three.
- ENC28J60-IRQ-014 (A, implementation-choice: the edge-trigger requirement is the handler's, not
  the hardware's) vs ENC28J60-IRQ-018 (B IRQ-013, observed-software-behavior, which folds the
  same point in). Kept both.
- ENC28J60-RX-025 (A, implementation-choice: the driver's 1518-byte and received-OK acceptance
  test) vs ENC28J60-RX-037 (B RX-026, observed-software-behavior, whole per-packet procedure
  including that test). Kept both.
- ENC28J60-REG-007 (A only, unresolved-conflict, minor): driver header names for addresses
  DS39662E marks reserved. B saw the same names and deliberately recorded them only in the notes
  of REG-002 and REG-003, reasoning that the data sheet edition the header targets is not in the
  corpus. A class-versus-no-row disagreement; kept A's row, readers [A].
- ENC28J60-ERR-007 (B ERR-003): B classed the edition renumbering of the errata as
  documented-hardware-requirement while its own notes say it is a citation rule, not a hardware
  requirement. Kept as B wrote it; the adjudicator should reclass or withdraw.
  *Withdrawn 2026-09-19* on the outside review's finding; see "Corrections applied 2026-09-19".

## 2. Weight disagreements

Provisional weight is the higher one (rule 5); `weight_disputed: {A, B}` is on each row.

- ENC28J60-SPI-002 (B SPI-011): A important / B critical -> critical. CS held low for one instruction.
- ENC28J60-SPI-003 (B SPI-012): A critical / B important -> critical. SPI clock DC to 20 MHz.
- ENC28J60-SPI-011 (B SPI-014): A critical / B important -> critical. Unbanked registers 0x1B to 0x1F.
- ENC28J60-SPI-013 (B RX-019): A critical / B important -> critical. Read Buffer Memory wraps ERXND to ERXST.
- ENC28J60-SPI-014 (B SPI-006): A important / B critical -> critical. Write Buffer Memory, EWRPT auto-increment and 0x1FFF wrap.
- ENC28J60-SPI-017 (B SPI-016): A critical / B important -> critical. MAC registers unreliable below 8 MHz asynchronous SPI (issue 1).
- ENC28J60-REG-010 (B REG-009): A critical / B important -> critical. ESTAT bit layout.
- ENC28J60-REG-024 (B RX-029): A important / B minor -> important. DMA copy programming.
- ENC28J60-INIT-009 (B INIT-016): A important / B minor -> important. MAC register order unimportant.
- ENC28J60-INIT-010 (B INIT-017): A minor / B important -> important. Driver initialization sequence (class also disputed).
- ENC28J60-INIT-012 (B INIT-009): A important / B critical -> critical. MACON3 padding, CRC, FULDPX.
- ENC28J60-INIT-019 (B INIT-019): A critical / B important -> critical. Entering power save.
- ENC28J60-INIT-020 (B INIT-020): A critical / B important -> critical. Leaving power save.
- ENC28J60-RX-016 (B RX-018): A important / B minor -> important. Reading ERXWRPT bracketed by EPKTCNT.
- ENC28J60-RX-029 (B RX-004): A important / B minor -> important. Program ERXST/ERXND before RXEN; even ERXST recommended.
- ENC28J60-TX-005 (B TX-001): A important / B critical -> critical. Hardware does not check ETXST/ETXND against the receive FIFO.
- ENC28J60-TX-012 (B TX-013): A important / B critical -> critical. Link pulse read as collision (issue 13).
- ENC28J60-PHY-004 (B PHY-005): A important / B minor -> important. PHY writes replace all 16 bits.
- ENC28J60-PHY-007 (B REG-022): A critical / B important -> critical. MICMD and MISTAT bits.
- ENC28J60-PHY-008 (B PHY-007): A critical / B important -> critical. PHCON1 bits.
- ENC28J60-PHY-010 (B PHY-010): A critical / B important -> critical. No autonegotiation.
- ENC28J60-PHY-011 (B PHY-009): A important / B critical -> critical. PDPXMD reset value from LEDB wiring.
- ENC28J60-PHY-014 (B PHY-022): A important / B minor -> important. Half-duplex loopback unreliable (issue 9).
- ENC28J60-PHY-016 (B PHY-014): A critical / B important -> critical. PHSTAT2 bits.
- ENC28J60-PHY-017 (B PHY-015): A important / B minor -> important. PHSTAT1 bits.
- ENC28J60-PHY-018 (B PHY-013): A important / B minor -> important. PHCON2 bits.
- ENC28J60-PHY-019 (B PHY-016): A critical / B important -> critical. PHIE and PHIR bits.
- ENC28J60-PHY-023 (B PHY-018): A important / B minor -> important. LED polarity misdetection (issue 16).
- ENC28J60-PHY-025 (B PHY-025): A important / B minor -> important. PHCON1.PRST.
- ENC28J60-ELEC-001 (B ELEC-001): A important / B minor -> important. 25 MHz clock, 50 ppm, duty cycle.
- ENC28J60-ELEC-003 (B ELEC-004): A important / B minor -> important. RESET pin pulse width.

Pattern worth the adjudicator's attention: reader A weights register bit layouts (PHCON1, PHSTAT2,
PHIE/PHIR, MICMD/MISTAT, ESTAT) critical; reader B weights them important. Reader B weights
"what the hardware does with the pointers" (TX-005, SPI-014, PHY-011, INIT-012) critical where A
says important. A single policy decision on bit-layout rows would settle nine of the 31.

## 3. Factual conflicts recorded as unresolved-conflict

None arose from the merge. Every paired row agreed on values, bit numbers, revision lists and
ordering once the issue-1 revision list was resolved (section 6). The one `unresolved-conflict`
row in the ledger, ENC28J60-REG-007, is reader A's own row about driver header names versus
DS39662E's reserved addresses, not a reader-versus-reader conflict.

Near-misses checked and found not to be conflicts:

- ENC28J60-PHY-020 (B PHY-017): PHLCON reset value, A "0x342x", B "0x3422". A left the low nibble
  unspecified; not a contradiction. Merged statement keeps A's; B's exact value is in B's text.
- ENC28J60-RX-005 / ENC28J60-RX-004 (B RX-008): both readers note that DS80349B and DS80349C phrase
  the ERXRDPT wrap test differently and that the driver uses the B form; both readers agree.
- ENC28J60-SPI-017 (B SPI-016): revision list disagreed (A [B5, B7], B [B1, B4]); resolved by the
  rendered PDF, see section 6.
- ENC28J60-ERR-002 (B ELEC-006): both readers read the errata's "PWRSV = 0" as a typographic slip.

## 4. Critical rows found by one reader only

Reader A only:

- ENC28J60-REG-005: ETH/MAC/MII register grouping by name prefix, and that EREVID, ECOCON, EFLOCON
  and EBST* in bank 3 are ETH registers (no dummy byte). B states group membership inside REG-003
  and REG-004 but has no row for the rule.
- ENC28J60-INIT-002: poll ESTAT.CLKRDY after Power-on Reset or wake before MAC/MII/PHY access. B
  folded the poll into INIT-001 (the OST row), so B did find it; the merge keeps A's atomic row.
- ENC28J60-RX-010: receive status vector byte count is little-endian and includes the CRC. B
  folded it into RX-011 (the status-vector bit row); same remark.

Reader B only:

- ENC28J60-SPI-019 (B SPI-001): instruction byte format, seven instructions and no others. A states
  the format as the opening clause of SPI-004 (a compound row).
- ENC28J60-SPI-020 (B SPI-002): Read Control Register opcode 000, ETH data MSb first immediately after
  the address. A states it inside SPI-004.
- ENC28J60-SPI-021 (B SPI-017): ECON2.AUTOINC must be set for streamed buffer commands to advance the
  pointers. A states the semantics inside SPI-013 and SPI-014; see section 1 for the class question.
- ENC28J60-REG-029 (B REG-011): EIR bit layout with per-bit access (PKTIF and LINKIF read-only). A
  states the layout in the second half of IRQ-001, without the access legend.
- ENC28J60-INIT-024 (B INIT-015): the local MAC address must be written into MAADR; it is used only
  by the unicast and magic packet filters and is never inserted as the source address. A has the
  not-inserted clause in TX-003 and the byte order in REG-020, but no row requiring MAADR to be
  programmed at all. **The one critical requirement with no A counterpart in substance.**
- ENC28J60-RX-032 (B RX-012): reception starts only when RXEN is set after configuration; accepted
  packets increment EPKTCNT, set PKTIF, advance ERXWRPT. A has the enabling clause in RX-018.

Recall note for the reader measurement: of the nine, only INIT-024 is a requirement the other
reader did not state anywhere. The other eight are atomicity differences (one reader's compound
row contains the other's atomic row).

## 5. Possible omissions, not added

Both readers mention these in `notes` without making a row. The merger is not an author; listed
for the adjudicator to decide whether a row is warranted.

- The driver sends the System Reset Command through its generic two-byte write helper, so a second
  0xFF follows on the wire; the data sheet describes a one-byte command (both readers, notes of
  SPI-008 / B SPI-009). Candidate observed-software-behavior row; no document says the extra byte
  is harmful or safe.
- The driver treats a timeout on its PHLCON write as PHY absence and aborts initialization (A,
  notes of PHY-021). Candidate implementation-choice row.
- Whether ECON1.TXRST clears ESTAT.TXABRT and ESTAT.LATECOL is not stated in the corpus; the driver
  never clears them explicitly and relies on the transmit-logic reset (A, notes of TX-007; B, notes
  of TX-009). Candidate unresolved gap row, since a candidate cannot recover it.
- The driver refuses a MAC address change while the interface is running (A, notes of RX-018; B,
  notes of RX-013). Candidate implementation-choice row.
- The driver's ERXFCON rewrite from its receive-mode handler while RXEN is set, against the data
  sheet's recommendation (both readers, notes of RX-018 / B RX-013). Recorded only as
  implementation_observed false on that row; a candidate that copies the driver here would be
  following the driver against the data sheet, which may deserve its own row.
- After a late-collision retry the driver's ETXND is at the region end rather than the frame end
  (B, notes of TX-022); whether the retried frame is transmitted correctly is not settled by the
  corpus. B's row records the rewrite; the consequence has no row.
- Neither draft has a row for the 5-bit width of MIREGADR (PHY address bits 7:5 unimplemented);
  PHY-006 lists the nine addresses but not the register width.

## 6. Corrections needed in corpus.yaml

- **Applied before this merge (confirmed in the file as read):** `errata_map.DS80349C.silicon_issues.1`
  now reads `affected: [B1, B4]`; the rendered Table 2 and issue 1's own box mark B1 and B4 only.
  Reader B was right; reader A had followed the map's original [B5, B7]. Every row citing issue 1
  (only ENC28J60-SPI-017) now carries [B1, B4], and A's note claiming Table 2 marks B5 and B7 is
  replaced.
- Issues 9, 10, 11, 12, 14, 15, 16, 17, 18 and 19 still have no `affected:` list in corpus.yaml.
  The brief says Table 2 marks every silicon issue other than 1, 3, 8 and 13 for all four
  revisions; both drafts record [B1, B4, B5, B7] for these. Add `affected: [B1, B4, B5, B7]` to
  each so the map, not the drafts, is the source.
- Issue 13 `affected: [B5, B7]` and issue 8 `affected: [B1, B4]` were added in the same correction;
  the merged rows TX-012, TX-013 and ELEC-007 match them.
- Table 3 (Ethernet Conformance Issues, three items, B1 and B4 only) is not represented in
  corpus.yaml's errata_map at all. Rows ERR-003, ERR-004, ERR-005 and ELEC-010 cite it; add a
  `conformance_issues` sequence under DS80349C with `affected: [B1, B4]`.
- `datasheet_clarifications` has no `affected` column; both drafts recorded all four revisions for
  clarification 1 on the reasoning that a clarification is not revision-specific. corpus.yaml
  should say so explicitly (or say the column does not apply) so future rows are consistent.
- The author brief (not corpus.yaml) says "Table 1 has the affected-revision matrix"; in DS80349C
  Table 1 is the EREVID value table and Table 2 is the Silicon Issue Summary. Reader B cited Table 2
  throughout; reader A cited Table 2 in notes. Fix the brief for the next pilot.

## 7. Rows a reviewer should double-check

Pairings made against the token-overlap aligner (each checked by hand):

- ENC28J60-REG-018 paired with B REG-016 (both critical, MACON3 layout), not A REG-019 as the
  aligner proposed; A REG-019 (PADCFG encodings, important) is A-only with a fold note. Avoids a
  spurious weight dispute.
- ENC28J60-TX-002 paired with B TX-003 (both critical, ETXST/ETXND placement), not B TX-006 as the
  aligner proposed; B TX-006 (the seven-byte gap, important) is ENC28J60-TX-021. Statement rewritten
  to carry both halves.
- ENC28J60-PHY-005 paired with B PHY-004 (BUSY restrictions, both important), not B PHY-027 (scan
  mode) as the aligner proposed; B PHY-027 is ENC28J60-PHY-029.
- Aligner's low-similarity match A RX-022 ~ B RX-020 rejected: A RX-022 is silicon issue 18, B
  RX-020 is filter combination logic (now ENC28J60-RX-034, overlapping A RX-019).
- Aligner's low-similarity match A TX-009 ~ B RX-004 rejected: ETXST versus ERXST. B RX-004 is
  merged into ENC28J60-RX-029.
- Cross-facet pairs kept under A's facet: SPI-013 (B RX-019), SPI-016 (B ELEC-002), REG-024 and
  REG-026 (B RX-029, RX-030), RX-019 (B REG-021), TX-019 (B REG-024), IRQ-001 (B REG-010), IRQ-009
  (B TX-017), PHY-007 (B REG-022), ERR-002 (B ELEC-006).

Atomicity: rows that overlap another row and could be withdrawn or split without losing a
requirement (each carries an overlap note):

- ENC28J60-SPI-004 is A's compound row (format, RCR, WCR); B's atomic SPI-019, SPI-020 and the
  merged SPI-004 (B SPI-005) cover the same ground. Split SPI-004 or withdraw the two B rows.
- ENC28J60-RX-036 (B RX-023) folds issue 18 and clarification 1, which A keeps as RX-022 and RX-023.
- ENC28J60-ELEC-010 (B ELEC-011) folds the three Table 3 items A keeps as ERR-003/004/005 (all out
  of scope, so harmless).
- B-only rows whose content sits inside an A row: REG-029 (in IRQ-001), REG-030 and REG-031 (in
  REG-023 and REG-014), RX-032 (in RX-018), RX-034 (in RX-019), RX-035 (in RX-020), RX-037 (in
  RX-025 and RX-030), TX-021 (in TX-002 and TX-005), IRQ-017 (in IRQ-009), IRQ-018 (in IRQ-014,
  IRQ-015, RX-030), PHY-028 (in PHY-009), PHY-029 (in PHY-005), ELEC-008 (in REG-017). A candidate
  could be scored twice on these until the adjudicator withdraws or splits.
- A-only rows whose content sits inside a B row (B is credited in notes, not in `readers`, except
  RX-005): REG-011, REG-012, REG-019, REG-025, REG-027, INIT-002, INIT-023, RX-010, RX-014, TX-009,
  ERR-003/004/005. The adjudicator may prefer to add B to `readers` on these for the recall
  measurement, as was done for RX-005.

Column decisions the merger made that are judgment calls:

- implementation_observed set false on ENC28J60-SPI-001 (A true / B false): the driver text has no
  SPI mode assignment (checked by search).
- implementation_observed set true on ENC28J60-IRQ-007 (A false / B true): the driver clears PKTIF
  the documented way (PKTDEC) even though it also includes PKTIF in a harmless Bit Field Clear.
- implementation_observed set false on ENC28J60-PHY-015 and ENC28J60-PHY-022 (A true / B false):
  not using a broken feature is not applying a workaround.
- implementation_observed set true on ENC28J60-ERR-001 (A true / B false): the workaround is to
  compute checksums in software, which the driver does by never starting a DMA checksum. The
  opposite call from PHY-015; the difference is that here the vendor names the software
  alternative as the workaround.
- unresolved kept true on ENC28J60-ERR-006 (A true / B false): the harmlessness of applying every
  workaround unconditionally is both readers' reasoning, not the vendor's. The two inference rows
  (A ERR-006, B ERR-002) were merged with premises unioned and a rewritten statement.
- vendor_confirmed on ENC28J60-INIT-004 unioned to all four (A empty, B all four): the row cites
  issue 2.
- in_scope kept true on ENC28J60-IRQ-016 (A true / B false, wake-on-LAN).
- ENC28J60-INIT-010: statement uses B's fuller sequence with A's closing sentence; class is A's.

Clean-room hygiene: reader B's INIT-004 notes quoted the driver's reset comment verbatim, and
reader A's INIT-003 and RX-004 notes came close. The merged notes for INIT-003 and RX-004
paraphrase them (bare issue number recorded, wording not). The drafts themselves still contain the
quotations and should not be published as they stand.

Statements taken from B where B's was fuller: SPI-014, REG-001, REG-003, INIT-007, RX-015. All
other merged rows keep A's statement, with B's notes appended as "Reader B adds".

## Corrections applied 2026-09-19

Applied after the outside review of the merged ledger (`codex-stageB-r1`, 2026-09-19) by a
preparer who is neither an author nor the adjudicator. Every change is a source-checked
correction or a clause-level overlap disposition. Nothing here settles a weight, a class
dispute or a one-sided critical row; those go to `ADJUDICATION.md`. IDs omit `ENC28J60-`.

### Review findings applied (brief Part 1, items 1 to 12)

- Header comment: "every other silicon issue: all four" now lists issue 3 (B1 and B4) with the
  other exceptions (review section 5; ELEC-006 already had it right).
- ERR-007: withdrawn, no replacement row. A citation convention is not a hardware requirement;
  the rule lives in corpus.yaml `errata_map` and in LEDGER-FORMAT.md's locator rule (review
  section 3, ERR-007).
- RX-029: statement narrowed to "program ERXST and ERXND before RXEN; even ERXST recommended". The
  section 6.1 advice to initialize ERXRDPT to ERXST moved to `notes` as superseded by DS80349C
  issue 14, with RX-031 named as the replacement and "a candidate that follows the section 6.1
  advice is misstated against RX-004" (review section 3, RX-029).
- ERR-006: class inference -> observed-software-behavior. Statement is now only that the driver
  applies every workaround it implements without consulting EREVID. The harmlessness claim and the
  "only marked issues apply" generalization moved to `notes` as an open question with
  `applicability.unresolved: true`; `premises`, `confidence`, `settled_by` dropped;
  `vendor_confirmed` emptied because the row no longer claims a vendor fact (review section 3,
  ERR-006).
- INIT-010: closing sentence replaced by "the corpus does not establish this complete sequence as
  mandatory", pointing at the rows that bind individual steps (INIT-001/002/006, RX-002,
  PHY-002/003). `class_disputed` marker added so the freeze gate counts the logged class dispute
  (review section 3, INIT-010).
- IRQ-014: the causal clause (INTIE masking) moved from the statement to `notes`, labeled reader
  A's inference (review section 3, IRQ-014).
- IRQ-015: split. IRQ-015 keeps the enabled-source selection as implementation-choice; new
  IRQ-019 carries the count-based receive drain as observed-software-behavior with readers A and
  B (A from IRQ-015's second clause, B from IRQ-018's drain clause) (review section 3, IRQ-015).
- RX-006: statement conditioned on the RX-005 wrap procedure; odd ERXND is not asserted as a
  universal requirement (review section 3, RX-006).
- PHY-012: "always" narrowed to systems where the reset-derived duplex setting cannot be
  trusted; section 6.6's externally configured design named in the statement (review section 3,
  PHY-012).
- SPI-021: statement keeps the hardware fact only; the driver-write clause and its driver
  derivation moved to INIT-018's notes (review section 3, SPI-021).
- INIT-004: statement is the driver's 2 ms busy-wait as a margin over INIT-003's 1 ms;
  `vendor_confirmed` reverted from the unioned four revisions to empty. The vendor minimum keeps
  its applicability in INIT-003; the driver choice carries only the driver's (review section 3,
  INIT-004; section 2 on union of applicability).
- INIT-024: narrowed to "the host must program MAADR". The filter-only and never-inserted clauses
  were minted as INIT-027 and withdrawn at birth with `replaced_by: [TX-003, RX-020]` so the
  clause has a traceable ID (review section 3, INIT-024).

### Overlap pass (clause level, not mechanical)

Withdrawn, adding no clause absent from the counterpart; the withdrawn row's reader credited on
the counterpart:

- REG-030 -> REG-023, REG-014, INIT-014 (B added to REG-014).
- REG-031 -> REG-023, REG-014, INIT-017 (B added to REG-014).
- RX-034 -> RX-019 (already A and B).
- RX-035 -> RX-020 (B added).
- IRQ-017 -> IRQ-009 (already A and B).
- ELEC-010 -> ERR-003, ERR-004, ERR-005 (B added to each; all out of scope).

Kept, with clauses moved so no clause is stated twice. Where A's compound row and B's atomic row
covered the same ground, the compound row was narrowed and the atomic row keeps the clause with
the moving clause's reader credited (LEDGER-FORMAT rule 3):

- SPI-004 (A compound) narrowed to Write Control Register. Instruction format -> SPI-019 (A
  added); Read Control Register -> SPI-020 (A added); SPI-020's MSb-first clause -> SPI-018 (B
  added). The ETH-versus-MAC/MII timing of the returned byte was already SPI-009.
- IRQ-001 narrowed to EIE; the EIR layout with its per-bit access legend is REG-029. A not
  added: A stated the positions and each access fact across six IRQ rows, never the legend as
  one claim (ADJUDICATION.md group C).
- TX-002 narrowed to pointer placement; the seven-byte space clause -> TX-021 (A added). TX-005
  now refers to TX-021 instead of restating "within seven bytes" (review section 2).
- PHY-009 narrowed to the agreement requirement; change-with-TX/RX-idle -> PHY-028 (A added).
- PHY-005 narrowed to the BUSY restriction; scan mode -> PHY-029 (A added).
- REG-001 narrowed to addresses; the 13-bit width is REG-012 only (B added) (review section 2).
- INIT-023 no longer restates 25 MHz (ELEC-001 states it); keeps the software consequence (B
  added).
- INIT-022 narrowed to reinit-on-open (B added, `class_disputed`); the transmit-timeout path is
  TX-023 (A added, `class_disputed`).

Kept and narrowed to the one clause no other row states (B's row, still B only):

- RX-032: keeps section 7.2.1's accepted/rejected-packet consequences; the enabling clause is
  RX-018 only. Weight stays B's critical for the adjudicator (group C).
- RX-036: keeps the pattern match mechanism (section 8.2); issue 18 is RX-022 and clarification 1
  is RX-023 (B added to both). No longer errata-derived, so `vendor_confirmed` is empty.
- RX-037: keeps "dropped frames are freed the same way as accepted ones"; the acceptance test is
  RX-025 (B added, `class_disputed`) and the batch loop RX-030 (B added).
- IRQ-018: keeps the handler's branch order and repeat-while-work loop; edge trigger is IRQ-014
  (B added), the drain is IRQ-019.
- ELEC-008: keeps CLKOUT start-up and prescaler-switching behavior (the "clock-switching" fact the
  review named); the ECOCON reset clause is REG-017 only.

A-only rows credited to B because section 7 above records that B stated the content inside a
compound row whose merged statement does not carry it: REG-011, REG-019, REG-025, REG-027,
INIT-002, RX-010, RX-014, TX-009 (plus REG-012, INIT-023 and ERR-003/004/005 above). Not
credited: REG-005 (B stated group membership, not the naming rule; group C).

Deferred to the adjudicator:

- SPI-021 stays one-sided critical. A states the conditional semantics in SPI-013/SPI-014 and
  the reset value in REG-009 but has no "must be set" row; fold into those or keep is group C.
- Register-layout rows stay as single rows: REG-008, REG-009, REG-010, REG-018, REG-021, REG-022,
  REG-029, RX-011, RX-019, IRQ-001, TX-008, PHY-007, PHY-008, PHY-016, PHY-017, PHY-018, PHY-019,
  PHY-020. Each holds many falsifiable claims; whether to split per bit is a policy question
  (group A), not a preparer's call.

### Class section update

- IRQ-015: resolved by the split (recorded in section 1 above), not by fiat.
- New `class_disputed` markers where the pass moved one reader's clause onto a row the other
  reader classed differently: INIT-022 (A observed / B choice), TX-023 (A observed / B choice),
  RX-025 (A choice / B observed), IRQ-014 (A choice / B observed), plus INIT-010 which was
  already logged. All five are one question: what separates observed-software-behavior from
  implementation-choice (ADJUDICATION.md group A).
- `in_scope_disputed` added to IRQ-016 (A true / B false), already a judgment call in section 7.

### Counts after this pass

203 -> 205 rows (2 minted: INIT-027 withdrawn at birth, IRQ-019 active); 197 active, 8 withdrawn
(REG-030, REG-031, INIT-027, RX-034, RX-035, IRQ-017, ELEC-010, ERR-007). Active rows with both
readers: 173 (was 144). Provisional markers on 36 rows (31 weight, 5 class, 1 scope; INIT-010
carries two). One-sided critical rows: REG-005, REG-029, INIT-024, RX-032, SPI-021.

## Adjudicated 2026-09-20 (group A)

The adjudicator answered `ADJUDICATION.md` group A; every answer was the sheet's proposed default,
and this pass applied them. Nothing outside group A was touched: groups B to E are still open, and
the 25 rows that still carry a provisional marker are theirs. IDs omit `ENC28J60-`.

### Decisions

- **A1 = (a) and (d).** Register bit-layout rows stay one row per register — no per-bit split.
  (The weight *rationale* below was withdrawn as unsound the same day; the weights themselves
  stand. See "Review corrections 2026-09-20", section 2.)
  Weight follows whether a driver must write the register to function: critical on REG-010,
  PHY-007, PHY-008 and PHY-019; important on PHY-016, PHY-017 and PHY-018. `weight_disputed` was
  removed from all seven. Six already carried the adjudicated weight from the provisional
  higher-of-the-two rule; only PHY-016 moved.
- **A2 = (a).** A behavior is an **implementation choice** when the driver picked one of several
  options the corpus allows (a value, a policy, a set of enabled sources, an ordering among valid
  orderings), and **observed software behavior** when it is a mechanism the driver executes where
  the corpus is silent (a recovery procedure, a handler structure, a restriction the design
  forces). (This wording was replaced the same day by a sharper rule with a precedence clause; the
  five classifications stand. See "Review corrections 2026-09-20", section 3.)
  The rule is now in LEDGER-FORMAT.md's class table. Applied to the five disputed rows:
  INIT-010, INIT-022, TX-023 and RX-025 implementation-choice, IRQ-014
  observed-software-behavior; `class_disputed` removed from all five, and each row's notes now
  record the adjudication instead of the dispute. Three of the five already carried the
  adjudicated class; INIT-022 and IRQ-014 moved.
- **A3 = (a).** The merged `implementation_observed` values stand: false on PHY-015 and PHY-022,
  true on ERR-001. No row changed. (Two of the reasons below were corrected the same day, and the
  rule's scope was limited to errata rows; the booleans stand. See "Review corrections
  2026-09-20", section 4.) **The rule for the next reader: `implementation_observed` is
  true only when the thing the driver does *is* the workaround the vendor names.** Not using a
  feature whose errata offer an external substitute (PHY-015's external loopback, PHY-022's
  alternate LED codes) is not applying a workaround, so those are false; computing checksums in
  software is the workaround issue 17 names, and the driver does it by never starting a DMA
  checksum, so ERR-001 is true.
- **A4 = (a).** Inference rows (RX-006, RX-031, PHY-012) count toward recall;
  observed-software-behavior rows (INIT-022 is no longer one of them — see A2 — leaving TX-022,
  RX-026, RX-030, RX-037, IRQ-014, IRQ-018, IRQ-019, PHY-027, SPI-022, ERR-006) are reported as
  their own counts and are not in the recall denominator. Because LEDGER-FORMAT.md requires the
  freeze lock to name a versioned policy, this is written up as `SCORING-POLICY.md`, version
  `enc28j60-1.0`, adopted 2026-09-20, and LEDGER-FORMAT.md's Scoring section points at it. No row
  changed.

### Rows whose weight or class moved

- PHY-016 (PHSTAT2 bit layout): weight critical -> important. (Reason superseded: "the driver
  only reads the register" was part of the withdrawn write-versus-read rule. The weight stands;
  its justification is now in the row's notes. See "Review corrections 2026-09-20", section 2.)
- INIT-022 (full reinitialization on every open): class observed-software-behavior ->
  implementation-choice, reader B's reading. A full reset on open is one re-entry policy among
  those the corpus allows.
- IRQ-014 (host interrupt must be edge-triggered): class implementation-choice ->
  observed-software-behavior, reader B's reading. (Reason superseded: "the handler's structure
  forces the restriction" is not established by the cited locators. The class stands, re-derived
  under the sharpened rule as an explicitly documented limitation of the reference implementation
  with no hardware obligation established. See "Review corrections 2026-09-20", section 3.)

### Counts after this pass

205 rows, 197 active, 8 withdrawn — unchanged, since group A added, withdrew and split nothing.
Provisional markers fall from 36 rows to 25 (24 weight, 1 scope; INIT-010 keeps its
`weight_disputed`, which is group B item 9). The freeze gate's error count falls from 41 to 30: 25
provisional-marker rows and the five one-sided critical rows (REG-005, REG-029, INIT-024, RX-032,
SPI-021), which are groups B, C and E.

## Review corrections 2026-09-20

An outside reviewer checked the four group A answers against the corpus and found the outcomes
mostly sound but several rationales unsupported, the format contract unamended, and clause overlap
still open. This pass applies those findings. **No outcome was re-decided: the seven layout weights
and the five classes are exactly as the adjudicator set them.** What changed is the reasoning
recorded for them, the contract that permits them, and the policy's precision. IDs omit
`ENC28J60-`.

### 1. The composite-row exception (A1's contract problem)

- **SCORING-POLICY.md** — new section "Composite scoring units". Answers: keeping independently
  falsifiable fields bundled contradicts `LEDGER-FORMAT.md` authoring rule 3 ("if a reviewer can
  agree with half a row, split it"), and owner approval cannot make the existing text consistent
  without an amendment. The section names REG-010, PHY-007, PHY-008, PHY-016, PHY-017, PHY-018 and
  PHY-019 explicitly — no open-ended "any layout row" exception — gives one denominator unit each
  and the deterministic `covered`/`partial`/`missing`/`misstated` rule, and says precision still
  evaluates the candidate's individual claims independently.
- **SCORING-POLICY.md** — the same section records that the set is not strictly one row per
  register: PHY-007 covers MICMD and MISTAT, PHY-019 covers PHIE and PHIR. Answers the reviewer's
  note that the proposal was described as one row per register.
- **LEDGER-FORMAT.md** authoring rule 3 — cross-reference added: the run's scoring policy may name
  bounded exceptions, this ledger's are the seven, and every other composite row is still governed
  by the rule. Answers the same finding from the format's side.

### 2. A1's weighting rationale, replaced with per-row justifications

The stated rule — critical where the driver must write the register, important where it only reads
or never touches it — **is withdrawn as unsound.** The reviewer showed it fails three ways: the
driver writes PHCON2 in both duplex branches, so PHY-018 is not a register it only reads; the
driver reads ESTAT without writing it, so REG-010's critical weight does not follow either; and
PHY interrupt enables serve the chosen link-interrupt design rather than any driver, DS39662E
section 12.1.5 permitting polling instead. A wrong read-only status bit can also break operation,
so write-versus-read is not a consequence test at all.

**The seven weights stand unchanged as the adjudicator's explicit judgments**, and each row now
carries a one-sentence consequence justification in `notes`, derived from the corpus — what
happens to a driver written from a specification that omits or misstates the row — not from
whether the driver writes the register:

- **REG-010** (critical): cannot locate ESTAT.CLKRDY, which DS39662E section 2.2 requires be
  polled before transmitting, enabling reception or touching any MAC, MII or PHY register.
- **PHY-007** (critical): reads MIRDL/MIRDH before MISTAT.BUSY clears, so every PHY value is
  unreliable.
- **PHY-008** (critical): PDPXMD disagreeing with MACON3.FULDPX leaves the device in the
  indeterminate state DS39662E sections 9.1 and 9.2 describe.
- **PHY-016** (important): wrong carrier from LSTAT and wrong duplex from DPXSTAT; link management
  misinformed, data path intact.
- **PHY-017** (important): LLSTAT and JBSTAT latch since the last read, so a present-tense reading
  reports a recovered link as down.
- **PHY-018** (important): without HDLDIS the half-duplex reset default loops transmitted packets
  back into the receive buffer (DS39662E section 9.1).
- **PHY-019** (critical): LINKIF is never set by reset default and clears only on an MII read of
  PHIR, so the driver either never learns of a link change or cannot clear the assertion.

**PHY-018 is flagged for the owner.** It is the one row whose placement rested on the withdrawn
fact — it was called a register the driver never writes, and the driver writes it in both duplex
branches. Its weight is unchanged at important and the justification above stands on its own, but
the owner may wish to revisit it.

### 3. The A2 rule, sharpened

- **LEDGER-FORMAT.md** class table — the two clarifying sentences are replaced by the reviewer's
  rule: classify the proposition the row asserts; a selected value, ordering, acceptance policy or
  recovery policy is an implementation choice when the corpus supports alternatives; a description
  of internal execution, or an explicitly documented limitation of the reference implementation, is
  observed software behavior when no hardware obligation is established; choice takes precedence
  for a proposition about a selected policy; record the evidence that alternatives exist and never
  infer hardware necessity from corpus silence. Answers: "policy" and "mechanism" overlapped, so
  TX-023 was simultaneously a recovery policy and a recovery procedure and the rule reached both
  answers on one row. **The five rows keep their classes.**
- **IRQ-014** — statement rewritten to the narrow form: the reference driver documents that board
  configuration must provide an edge-triggered host interrupt and that level triggering is
  unsupported by this implementation, and the corpus does not establish the cause of that
  limitation or any universal prohibition on level-sensitive hosts. Answers: the probe comment
  supports reporting the restriction, not the proposed explanation of it.
- **IRQ-014** — the causal explanation about the handler masking INTIE is **deleted from `notes`
  and not replaced**. Masking and restoring INTIE does not by itself demonstrate failure with a
  level-sensitive host. The notes now say only that it was withdrawn as unestablished, and that
  DS39662E section 12.0 does discuss falling-edge hosts and INTIE masking — so the corpus is not
  silent about level behavior generally, only about why this implementation cannot support it.

### 4. A3's rationales, corrected

- **PHY-022** `notes` — issue 11's workaround is **alternate LED programming codes** (0011 in half
  duplex, 0101 in full duplex), not external hardware. The driver selects different LED functions,
  so it neither uses the broken code nor implements the vendor's named alternative, which is why
  `implementation_observed` is false. The boolean is unchanged.
- **ERR-001** `notes` — the pinned driver files do not establish that the driver computes checksums
  in software. The row is observed because the driver follows the vendor's explicit DMA-checksum
  avoidance instruction; where checksums are computed is not established by those files. The
  boolean is unchanged.
- **ERR-001** `statement` — the clause claiming the host cannot reliably exclude reception windows
  is dropped. Issue 17 states the abort and prescribes the avoidance; it does not establish that
  causal premise.
- **Scope of the A3 rule.** The workaround-specific reading of `implementation_observed` — true
  only when the thing the driver does *is* the workaround the vendor names — **applies to errata
  rows.** It does not redefine the field for non-errata rows, which also use it and where it means
  only whether the reference driver applies the requirement.

### 5. SCORING-POLICY.md completed

New or rewritten sections, each answering a gap the reviewer listed: **Eligibility** (active,
in-scope, recoverable, included class, and nothing else — not silicon revision, not the
applicability columns, never anything derived from a candidate); **The recall formula**
(`(covered + 0.5 x partial) / eligible rows`, overall and per weight, with `n/a (0 eligible rows)`
for an empty bucket); **Precision adjudication** (claim segmentation and deduplication, and
contradicted versus unsupported versus partial versus conditional versus a correctly attributed
observation of driver behavior); **Uncertainty** (an inference presented as an inference, an
unresolved conflict, and that `applicability.unresolved` or a hedge in notes never silently removes
a row from the denominator); **Composite units** (section 1 above); **Binding** (the freeze lock
records this file's sha256 as well as the version string, and a run cites the lock, because a
version label on a mutable file binds nothing); **Changes after a candidate has been read** (a new
ledger or policy version and a declared rescoring procedure; the original result is never silently
altered).

**Rosters regenerated from the settled ledger**, not copied. After A2 the observed list loses
INIT-022 and gains IRQ-014: observed software behavior is TX-022, RX-026, RX-030, RX-037, IRQ-014,
IRQ-018, IRQ-019, PHY-027, SPI-022 and ERR-006 (ten active rows, counted but not in recall);
inference is RX-006, RX-031 and PHY-012 (three, in recall). Corrected in **ADJUDICATION.md group
A4**, whose list was stale, and written into **SCORING-POLICY.md**, which had not carried them.
RX-006's condition and PHY-012's inference status are preserved explicitly there: neither becomes
a universal obligation by entering recall.

### 6. One factual error in ADJUDICATION.md group B

- **B14 (RX-029)** — the reason "the reset defaults are a working FIFO" is replaced by the
  duplication argument alone (RX-002 and RX-018 already bind pointer programming). The original is
  wrong: the reset ERXST is 0x05FA (REG-013) while DS80349C issue 5 requires the receive buffer to
  start at 0x0000 (RX-003), so the reset layout does not satisfy the errata. The proposed weight is
  unchanged.

### 7. Residual overlap: marked, not resolved

The reviewer rejected the claim that every clause overlap is closed. Resolving these changes the
recall denominator, so it is the owner's decision. Each row below now carries `overlaps:` with
`replaced_by` deliberately unset — exactly what the freeze gate refuses — so the error count
carries the work until group F is answered.

- **SPI-021** `overlaps: [SPI-013, SPI-014, REG-009]` — AUTOINC streaming semantics in SPI-013 and
  SPI-014, reset value in REG-009.
- **REG-029** `overlaps: [IRQ-007 … IRQ-012]` — the per-bit read-only and host-clearable access
  facts. Being the only row that states the EIR legend as one claim does not remove the
  duplication.
- **RX-032** `overlaps: [RX-013, RX-015, IRQ-007]` — the accepted-packet consequences. "No other
  row states these as one claim" is not a deduplication argument.
- **SPI-014** `overlaps: [SPI-005]` — the Write Buffer Memory command encoding.
- **RX-029** `overlaps: [RX-002, RX-018]` — pointer-before-enable.

**ADJUDICATION.md group F, "Residual overlap"** — one numbered decision per row, naming the
duplicated clause, the rows that hold it, and options (a) withdraw with `replaced_by`, (b) narrow
to the clause no other row states, (c) keep both and accept the double count. Option (c) is
written as an explicit authorization of duplicated recall contribution for the named clause,
recorded as its own exception in the scoring policy, and is distinguished from the group A1
composite-unit exception: one row's several facts scoring as one unit is a different problem from
two rows sharing a clause. A default with a one-clause reason is proposed for each.

**ADJUDICATION.md Terms** — the "Overlap" entry claimed none were open; corrected to name the five
and point at group F, and the freeze progress number is updated.

### 8. The other composite layout rows

From the reviewer's follow-up: eleven more rows bundle independently falsifiable facts the way the
seven do, and the unchanged atomic-row rule still applies to them. They are carried as unresolved
work rather than swept into the exception.

- **ADJUDICATION.md group G, "Remaining composite layout rows"** — REG-008, REG-009, REG-018,
  REG-021, REG-022, REG-029, RX-011, RX-019, IRQ-001, TX-008 and PHY-020, each with the facts it
  bundles and options (a) enumerate as an additional composite scoring unit, (b) split into atomic
  rows, (c) narrow — with a proposed default and a one-clause reason. REG-029 is in both F and G,
  and G says to answer F first; REG-009's reset-value clause is likewise F1's.
- **SCORING-POLICY.md** "Composite scoring units" — says explicitly that the exception covers the
  seven listed ids and no others, that other composite rows remain subject to the atomic-row rule
  pending adjudication, and points at group G.

### 9. README

- **README.md** — the open-work note on checker enforcement now says that requiring and validating
  the scoring policy's version string and sha256 in `ledger_check.py` is a **prerequisite to
  freezing and to generating any candidate**, not a later improvement. `README.md` was also added
  to the documented leak-scan command, since it is now scanned with the other clean-side files.

### Counts after this pass

205 rows, 197 active, 8 withdrawn — unchanged; nothing was added, withdrawn or split. Provisional
markers stay on 25 rows. **The freeze gate rises from 30 errors to 35**: 25 provisional-marker
rows, the five one-sided critical rows (REG-005, REG-029, INIT-024, RX-032, SPI-021) and the five
newly marked undisposed overlaps (SPI-021, REG-029, RX-032, SPI-014, RX-029). REG-029, RX-032 and
SPI-021 each contribute two errors; that is intended, since each needs both a second reading and
an overlap disposition. Open groups are now B, C, D, E, F and G.

## Adjudicated 2026-09-20 (groups B to G)

The repository owner answered the rest of `ADJUDICATION.md`, and this pass applied the answers.
Nothing here was re-decided by the preparer. Two rows were held back on the owner's instruction:
**INIT-024 and REG-005 are untouched** and stay one-sided critical, because independent
derivations for both are being produced separately and will be wired in afterwards. IDs omit
`ENC28J60-`.

### The weight principle (group B's answer, and now a standing rule)

Weight measures consequence **adjusted for necessity**. The rule, added to `LEDGER-FORMAT.md`
beside the `weight` field description:

> Weigh the consequence of a driver written from a spec that omits the row, adjusted for
> necessity. `critical` is for a requirement a working driver cannot avoid: omitting it means the
> driver does not work or corrupts data. A requirement that only bites when a driver uses an
> optional feature caps at `important`, however severe it is inside that feature.

It is the rule the format's definition of `critical` already implied, written down. The cap is a
ceiling and not a floor: an optional-feature row whose omission costs only completeness is still
`minor`, which is why INIT-019 and INIT-020 (power save) land on `important` while REG-024 (the
DMA copy) and PHY-025 (PHY-only reset) land on `minor` from the same observation that the feature
is optional.

**Every one of the 28 proposals was checked against the rule and every one follows it; none was
overridden.** The check that could have overturned one runs in two directions — a `critical`
proposal for something that only bites inside an optional feature, or a lower weight for
something unavoidable whose omission breaks the driver or corrupts data — and no item tripped
either. Where the cap is what does the work rather than the raw consequence, that is noted below.

### Group B, item by item

24 rows lost `weight_disputed`; items 25 to 28 never carried one (the weight was inherited across
a 2026-09-19 split) and are confirmed or set outright. Consequence clauses are the sheet's, which
is what the rule asks for.

| Item | Row | Weight | Why it follows |
|---|---|---|---|
| 1 | SPI-002 | critical (unchanged) | CS raised mid-instruction abandons the byte; every multi-byte command fails, and no driver avoids those. |
| 2 | SPI-003 | critical -> important | Exceeding 20 MHz fails, but a spec that omits the ceiling more often leaves a slower bus than a broken one. |
| 3 | SPI-011 | critical -> important | A driver that switches banks for the unbanked registers still works, only slower: degraded, not broken. |
| 4 | SPI-013 | critical (unchanged) | A driver unaware that reads wrap at ERXND corrupts every frame spanning the end of the FIFO, and AUTOINC is set after reset. |
| 5 | SPI-014 | critical (unchanged) | Without the write-buffer path and its auto-increment nothing can be transmitted. |
| 6 | SPI-017 | critical (unchanged) | On the marked silicon with a slow asynchronous SPI every MAC register write can silently fail; a revision-limited row is not an optional feature, and the policy's eligibility rule says so. |
| 7 | REG-024 | important -> minor | The DMA copy is optional and the driver never uses it; capped at `important` and below the cap on consequence. |
| 8 | INIT-009 | important -> minor | Order among MAC registers is unimportant, so omitting the statement costs nothing. |
| 9 | INIT-010 | important -> minor | Set as proposed; the row is an `implementation-choice`, whose weight never enters recall, so the field is filled for consistency only. |
| 10 | INIT-012 | critical (unchanged) | Without padding and CRC generation configured the MAC transmits frames as given, and a FULDPX mismatch leaves the device indeterminate. |
| 11 | INIT-019 | critical -> important | Power save is optional (INIT-021); a driver that never enters it works. The cap does the work. |
| 12 | INIT-020 | critical -> important | Same; a driver that never sleeps never wakes. The cap does the work. |
| 13 | RX-016 | important -> minor | Only the free-space computation needs it, and the driver uses that only to classify an error. |
| 14 | RX-029 | important -> minor | Duplication only: RX-002 and RX-018 already bind pointer programming, and after the F5 narrowing what is left is an alignment recommendation. The sheet's original reason, "the reset defaults are a working FIFO", was corrected before this pass and is not used: ERXST resets to 0x05FA (REG-013) while DS80349C issue 5 requires the buffer to start at 0x0000 (RX-003). |
| 15 | TX-005 | critical (unchanged) | A transmission overlapping the receive FIFO corrupts received data. |
| 16 | TX-012 | critical (unchanged) | On the marked silicon in half duplex TXRTS never clears and transmit hangs; half duplex is the device's reset default, not an optional feature. |
| 17 | PHY-004 | important (unchanged) | A driver that writes a PHY register expecting bit-level semantics clears bits it did not mean to, including PHLCON's reserved-as-1 bits. |
| 18 | PHY-010 | critical -> important | A driver assuming autonegotiation ends in a duplex mismatch: a degraded link rather than none. |
| 19 | PHY-011 | critical -> important | A driver relying on the reset PDPXMD gets the wrong duplex on some boards; PHY-012 is the fix. |
| 20 | PHY-014 | important -> minor | A diagnostic mode a driver need not use; HDLDIS itself is PHY-013. |
| 21 | PHY-023 | important -> minor | A board workaround; the software consequence is PHY-012. |
| 22 | PHY-025 | important -> minor | The driver never resets the PHY alone, and no driver has to. |
| 23 | ELEC-001 | important -> minor | A board fact a driver cannot act on; INIT-023 carries the software side. |
| 24 | ELEC-003 | important -> minor | The driver has no reset pin. |
| 25 | TX-021 | important -> critical | Inherited across the 2026-09-19 split from A's compound row: the seven-byte status vector overwrites the receive buffer, and every transmit writes one. |
| 26 | PHY-028 | important (confirmed) | Changing duplex at all is optional, so the cap applies to A's compound-row `critical`. |
| 27 | PHY-029 | minor (confirmed) | Scan mode is an optional MII feature and its omission costs completeness. |
| 28 | REG-012 | important (confirmed) | Every legal buffer address fits in 13 bits, so a driver that stays in range works; the width matters to a reader reasoning above 0x1FFF. |

### PHY-018 becomes critical

The owner's separate answer, outside the list above. **PHY-018 (PHCON2 layout): `important` ->
`critical`**, with the consequence recorded in the row's `notes`: PHCON2 holds HDLDIS, and a
driver written from a spec that omits the layout leaves half-duplex loopback enabled, so every
transmitted packet is looped back into the receive path (DS39662E Register 6-5: with PHCON1<8>
and PHCON1<14> clear, HDLDIS = 0 loops transmitted data back to the MAC). The earlier
justification placing the row by whether the driver only reads the register is gone from the row:
that rule was withdrawn as unsound on 2026-09-20 and was factually wrong here, since the driver
writes PHCON2 in both duplex branches. PHY-018 carries both readers, so the new `critical` weight
raises no two-reader question. It is one of the seven group A1 composite scoring units and stays
one.

### Group F, residual overlap

All five the proposed default; **no row took option (c)**, so no duplicated-recall exception was
written into `SCORING-POLICY.md` and that section still says the composite exception is about
something else.

- **F1 = (a). SPI-021 withdrawn**, `replaced_by: [SPI-013, SPI-014, REG-009]`, notes recording
  that no clause survives the narrowing: the conditional streaming semantics are SPI-013 and
  SPI-014 and the set-after-reset value is REG-009, and the "must be set" framing is the same
  fact as SPI-013's conditional rather than an additional one. All three replacements carry both
  readers. **This also settles C4**, whose answer is "w": the one-sided critical question
  disappears with the row rather than being answered.
- **F2 = (b). REG-029 narrowed** to the EIR bit positions and the reserved bit. The per-bit
  access facts stay with IRQ-007 to IRQ-012, which own them one bit at a time, and are cited in
  the notes. `overlaps` cleared.
- **F3 = (b). RX-032 narrowed** to the silent-discard clause: a frame that fails the filters is
  discarded with no indication to the host. The accepted-packet consequences are RX-013, IRQ-007
  and RX-015. `overlaps` cleared. Weight follows the narrowing; see C5 below.
- **F4 = (b). SPI-014 narrowed** to the streaming behavior: MSb-first data bytes, storage at
  EWRPT, the AUTOINC advance and the 0x1FFF-to-0x0000 wrap. SPI-005 owns every opcode encoding.
  `overlaps` cleared. Weight stays `critical`, since what is left is still the only way to put a
  frame in the transmit buffer.
- **F5 = (b). RX-029 narrowed** to the data sheet's even-ERXST recommendation, the only
  receive-buffer placement rule the data sheet itself states; pointer-before-enable is RX-002 and
  RX-018. `overlaps` cleared. Weight `minor`, which is group B item 14 and now follows from what
  is left rather than from the duplication alone.

Each narrowed row keeps its id and its `readers`.

### Group C, the three that could be touched

- **C3 = (a).** Reader A added to REG-029's `readers`. A stated the EIR bit positions inside
  IRQ-001 before that row was narrowed to EIE, and the crediting rule confirmed in E5 makes that a
  reading of the atomic row. What A never stated as one claim was the access legend, and after F2
  the legend is not this row's content. REG-029 stops being a one-sided critical row.
- **C5 = (d).** RX-032 takes `important`. **The reason is the narrowed content, not the two-reader
  rule**: what remains is that a filtered frame leaves no trace, so a driver built from a spec
  that omits it waits on a count or a flag that will not move for dropped frames, which is a
  fragile receive path rather than a broken one. Downgrading a row to dodge the two-reader rule
  would not be acceptable; the rule simply stops applying once the row is not critical, and that
  is a consequence of the weight, not a reason for it.
- **C4** is settled by F1 above.
- **C1 (INIT-024) and C2 (REG-005) untouched**, on instruction. Both keep `weight: critical` with
  one reader and no `independent_review`, and they are the entire remaining freeze count.

### Group D, five rows minted

Added: D1, D2, D4, D5, D7. Not added: D3 and D6, whose content stays in the notes of TX-007 and
TX-022 as the sheet proposed. Each new row continues its facet's numbering, cites the corpus,
carries `readers` naming the reader whose notes proposed it (this log's section 5), and takes a
weight under the rule above.

- **SPI-023** (D1, `observed-software-behavior`, minor, readers A and B): the driver sends the
  System Reset Command through its two-byte write path, so a second byte follows on the wire where
  the data sheet describes a one-byte command; the corpus does not say whether that matters. The
  row states the behavior and the gap and claims no consequence, which is why it is minor.
- **PHY-030** (D2, `implementation-choice`, minor, reader A): the driver treats a timeout writing
  PHLCON as the PHY being absent and aborts initialization. A precision probe: a candidate that
  presents the timeout as the documented way to detect a missing PHY, or as a required
  initialization step, is misstated.
- **RX-038** (D4, `implementation-choice`, minor, readers A and B): the driver refuses a MAC
  address change while the interface is running. A precision probe: DS39662E section 7.2.1
  recommends clearing RXEN before such a change, and RX-018 carries that; a candidate that states
  the hardware forbids the change is misstated.
- **RX-039** (D5, `observed-software-behavior`, minor, readers A and B): the driver rewrites
  ERXFCON from its receive-mode path while reception is enabled. **The notes correct the sheet on
  what this probes.** Reporting accurately that the driver does this is not itself a misstatement,
  because section 7.2.1 recommends rather than prohibits, and a correctly attributed observation
  of driver behavior is judged as that claim. What is wrong is a candidate presenting the rewrite
  as following the vendor's recommendation, or as a hardware requirement; either is misstated
  against RX-018, which records `implementation_observed` false because of this behavior.
- **PHY-031** (D7, `documented-hardware-requirement`, minor, no readers): MIREGADR is five bits
  wide, bits 7-5 unimplemented, so thirty-two PHY addresses are addressable and nine implemented.
  `readers` is empty and the notes say why: neither draft made a row for it, so the row is the
  adjudicator's, derived from DS39662E Table 3-2 and section 3.3. PHY-006 already says the
  addresses above 0x14 are unimplemented, so a driver that writes a whole byte still reaches the
  register it meant to, which is why it is minor.

### Group E

- **E1 = (b).** IRQ-016 (wake-on-LAN) is `in_scope: false`, with notes saying why: outside the
  pilot's declared coverage, which is reader B's objection and the authoring brief's coverage
  list. `in_scope_disputed` removed. The row stays **active**, so a candidate that states
  wake-on-LAN is not penalized; out-of-scope rows sit outside every denominator and are reported
  separately.
- **E2 = (b).** REG-007 reclassed `unresolved-conflict` -> `observed-software-behavior`, and its
  statement reworded to say what it now is: the driver's header names four control-register
  addresses DS39662E shows as reserved or unimplemented, the names are the driver's, and the
  corpus does not establish that a register exists at any of them. That is a fact about the
  driver, not a disagreement between the two readers, and the reword clears the checker warning
  that the statement did not present both readings — a warning the row could never have satisfied.
  The ledger now has **no `unresolved-conflict` rows**; the class stays in the format and the
  policy for a future one. The applicability columns were not touched, `unresolved: true`
  included: E3 shows those are decided on their own.
- **E3 = (a).** ERR-006 keeps `applicability.unresolved: true`. No change to the row; logged.
- **E4 = y.** INIT-004 keeps the driver-only applicability (`vendor_confirmed` empty). No change
  to the row; logged.
- **E5 = y.** The crediting rule stands and is now written into `LEDGER-FORMAT.md` beside
  authoring rule 4, so the next merge applies it: *a reader who stated a clause inside a compound
  row is a reader of the atomic row that clause ends up in.* Every `readers` list the earlier pass
  set under it was re-checked and is right: REG-011, REG-012, REG-019, REG-025, REG-027, INIT-002,
  INIT-023, RX-010, RX-014, TX-009, ERR-003, ERR-004 and ERR-005 (A-only rows credited to B),
  SPI-019, SPI-020, TX-021, PHY-028 and PHY-029 (B rows credited to A after a compound row was
  narrowed), plus RX-005, REG-014, RX-020, IRQ-009, SPI-018 and IRQ-019 from the same pass. All
  carry `[A, B]`.

### Group G, remaining composite layout rows

- **(a) for G1 to G5 and G7 to G10.** Nine rows are now additional composite scoring units, named
  explicitly in `SCORING-POLICY.md` beside the original seven and under the same verdict rule:
  **REG-008, REG-009, REG-018, REG-021, REG-022, RX-011, RX-019, IRQ-001, TX-008.** Sixteen in
  all. No ledger row changed: the exemption lives in the policy, which is where a bounded
  exception to `LEDGER-FORMAT.md` authoring rule 3 belongs.
- **The policy version is bumped to `enc28j60-1.1`.** The id list is part of the frozen policy
  text, so lengthening it is a new version, not an edit. The policy carries a new **Version
  history** section saying what changed between 1.0 and 1.1 and why a bump was needed: a run
  scored under 1.0 puts one denominator unit where a run under 1.1 puts one for nine further rows,
  and the two recall numbers are not comparable. The lock's sha256 would have caught an edit, but
  a changed hash says "this file moved", not "these results mean something different"; the version
  string is what carries the second meaning. The same bump carries the roster change below. Live
  references to the version string were updated in `LEDGER-FORMAT.md` and in the policy's own
  Binding section; the two `enc28j60-1.0` references inside the group A records here and in
  `ADJUDICATION.md` are left alone, because they record what group A adopted at the time.
- **G6 = (c), which is F2.** REG-029 was narrowed there and nothing extra was needed here. It is
  **not** in the list of nine: what is left of it is the EIR bit positions and one reserved bit,
  and the owner enumerated the nine without it.
- **G11 = (c).** PHY-020 is narrowed to PHLCON's layout, reset value and reserved-as-1 bits. The
  table of common LED codes moves to the new row **PHY-032** (`documented-hardware-requirement`,
  the data sheet's own table in Register 2-2; weight `minor`, because LED display is a feature a
  driver need not configure and a driver that omits the codes still moves frames; `readers`
  inherited from PHY-020; `supersedes` unset; notes saying it was split out of PHY-020). PHY-020
  is not enumerated as a composite unit either, for the same reason as REG-029.

### Roster and denominator effects

Recorded so the policy and the ledger cannot drift apart:

- `observed-software-behavior` goes from ten active rows to **thirteen**: REG-007 (reclassed by
  E2), SPI-023 and RX-039 (minted by D) join TX-022, RX-026, RX-030, RX-037, IRQ-014, IRQ-018,
  IRQ-019, PHY-027, SPI-022 and ERR-006. Counted, never in recall.
- `inference` is unchanged at three: RX-006, RX-031, PHY-012. In recall.
- `implementation-choice` gains PHY-030 and RX-038. Precision probes, never in recall.
- REG-007 leaves the recall denominator, which is a denominator change and part of why the policy
  version moved.
- IRQ-016 leaves every denominator on `in_scope: false` while staying active and reportable.

### Counts after this pass

**205 -> 211 rows; 197 -> 202 active, 8 -> 9 withdrawn.** Six rows minted (SPI-023, PHY-030,
PHY-031, PHY-032, RX-038, RX-039) and one withdrawn (SPI-021). Classes: 176
documented-hardware-requirement, 19 implementation-choice, 13 observed-software-behavior, 3
inference, 0 unresolved-conflict. Weights: 66 critical, 63 important, 82 minor. 178 rows carry
both readers. Provisional markers: **25 rows -> 0**. Undisposed overlaps: **5 -> 0**.

**The freeze gate falls from 35 errors to 2**, and both are the rows held back on instruction:
REG-005 and INIT-024, each a critical active row with one reader and no structured
`independent_review`. Nothing else remains — no provisional marker, no undisposed overlap, and
`ledger_check.py` without `--freeze` reports 0 errors and 0 warnings (the REG-007 warning is gone
with the reclass). The leak scan over `ledger.yaml`, `SCORING-POLICY.md`, `LEDGER-CONFLICTS.md`,
`ADJUDICATION.md` and `README.md` against the pinned driver files is clean. Every group of
`ADJUDICATION.md` is now answered.

## Pre-freeze repairs 2026-09-20

An outside reviewer read the ledger at commit `01ca0ae` read-only, reproduced the clean mechanical
gate and the 161-row denominator, and **refused the freeze on semantic grounds**: the atomic-row
contract, the overlap contract, and several claims stronger than their evidence. This pass clears
those blockers. Every change below names the row or file it touches and the finding it answers.
IDs omit `ENC28J60-`. No row's weight or class was changed by this pass.

### 1. The composite inventory

**The finding.** `SCORING-POLICY.md` exempted sixteen ids by name and said the atomic-row rule
still bound every other row. The reviewer found that untrue in practice — it named REG-029,
PHY-020, PHY-032, REG-015, and as further examples REG-001 to REG-004, REG-013 to REG-015,
REG-017, REG-019, REG-020, REG-023, PHY-006 and RX-020 — and said its own list was not
exhaustive. A scorer therefore had no authorized rule for a partially correct version of those
rows.

**What was done.** Every active row was walked, not only the rows the reviewer named, and each
was judged against a test now written into the policy: a row is composite when it states two or
more facts that can each be checked, and found right or wrong, on their own; a row is atomic when
it states one requirement, even where the statement also carries the mechanism that produces it,
its value, its condition or its consequence. **202 rows walked, 113 composite, 89 atomic**; after
the two splits below the ledger holds 204 active rows, 113 composite and 91 atomic.

- **`SCORING-POLICY.md`, bumped to `enc28j60-1.2`** — the composite list goes from 16 ids to 113,
  with the test written down, the per-facet counts printed so a reader can check the list against
  `ledger.yaml`, and a sentence saying the inventory was made by walking every active row on
  2026-09-20 and is meant to be exhaustive rather than illustrative. Every row's verdict rule can
  change with the list, so the bump is mandatory, not cosmetic. Per facet: REG 25, INIT 12, TX 13,
  RX 15, IRQ 10, PHY 20, SPI 10, ELEC 7, ERR 1.
- **`SCORING-POLICY.md`** — the verdict rule now also says what it means for the eleven composite
  units no recall denominator contains (REG-007, RX-026, IRQ-018, INIT-010, RX-021, RX-025,
  TX-018, IRQ-016, ELEC-004, ELEC-005, ELEC-007): a precision probe is `misstated` when at least
  one enumerated fact is asserted as a hardware requirement, on the same threshold, and not only
  when the whole row is.
- **`LEDGER-FORMAT.md` authoring rule 3** — its live reference to "the sixteen register bit-layout
  rows" and to policy version `enc28j60-1.1` is now the 113-id list and `enc28j60-1.2`, with the
  walk named as what makes a row's absence from the list a judgment rather than an oversight. The
  `enc28j60-1.0` and `enc28j60-1.1` references inside historical records here and in
  `ADJUDICATION.md` are left alone; the three live references inside `ledger.yaml` row notes were
  updated.

**Enumerated, 95 rows.** Every row that is one register's definition, one document table, or one
mechanism a reader looks up in one place, which is the shape the owner approved for the original
seven. REG-029 (EIR bit positions), PHY-020 (PHLCON layout), PHY-032 (LED codes) and REG-015
(EREVID with its revision-code table) are in this group, which is where the reviewer's four named
blockers land.

**Split, 2 rows, each leaving its remainder enumerated.** Splitting was used only where a row
bundled things a reader would look up in different places:

- **PHY-006 to PHY-033.** The reserved-bit write rule is read in a register's own definition, not
  in the PHY register summary that lists implemented addresses. PHY-033 is a new atomic row
  (`documented-hardware-requirement`, `important`, readers inherited from PHY-006, `supersedes`
  unset because PHY-006 survives).
- **TX-019 to TX-024.** Half-duplex backpressure is a different mechanism from the pause frames
  the rest of the row describes. TX-024 is a new atomic row
  (`documented-hardware-requirement`, `minor`, readers inherited from TX-019, `supersedes` unset).

**Deliberately not split.** REG-023 bundles five MAC timing and limit registers, but the
2026-09-19 merge folded the withdrawn REG-030 and REG-031 into it, so splitting would reopen a
settled merge; the same reason already protects RX-019 from being split back into RX-034. Both
are enumerated instead, and the policy says why.

### 2. The remaining clause overlaps

The reviewer's six pairs, resolved by giving each clause one owner and leaving a cross-reference
rather than a second scored clause:

- **REG-005 / SPI-009 / SPI-016, and REG-003.** REG-005 is narrowed to the grouping rule: group
  membership follows the data sheet's name prefixes, and bank 3 holds members of different groups.
  SPI-009 owns the dummy byte and the read framing; SPI-016 owns the 210 ns CS hold time; REG-003
  loses the clause saying every bank 2 register needs a dummy read byte and keeps the bank 2
  address map. REG-005's structured `independent_review` is kept intact and its **disposition
  gains a clause** saying which part of reader C's reading supports the narrowed row: the section
  3.1 name-prefix rule with the bank 3 column of Table 3-1 and Register 3-4 settle membership,
  while the framing that reading took from Figures 4-3 and 4-4 and the hold times from Table 16-6
  now support SPI-009 and SPI-016.
- **INIT-007 / INIT-008.** INIT-007 owns the sequence. INIT-008 is restated as post-reset
  verification and retry, referring to INIT-007 for the preceding steps.
- **TX-004 / IRQ-008 / TX-007.** TX-004 loses the success clause, the abort path and — the
  reviewer's table names this too — the clause setting EIR.TXIF. IRQ-008 owns judging success
  including the condition that the host did not itself clear TXRTS; TX-007 owns what an abort
  does. Both gained a note recording the ownership.
- **RX-012 / IRQ-007.** IRQ-007 owns that PKTIF clears only when PKTDEC brings EPKTCNT to zero.
  RX-012 keeps the decrement the host owes after each packet.
- **PHY-031 / PHY-006.** PHY-006 owns the nine implemented PHY addresses; PHY-031 keeps
  MIREGADR's width and reset value, with the rest in notes.
- **SPI-014 / SPI-018.** SPI-018 owns the most-significant-bit-first rule for every command;
  SPI-014 keeps the streaming behavior.

**The sweep beyond the named list.** Clauses were compared rather than `overlaps` markers read, as
the reviewer asked. Nine more duplications were found and resolved the same way:

- **INIT-002 / INIT-001** — both listed the operations forbidden before the device is ready.
  INIT-001 owns the list; INIT-002 refers to it and owns the CLKRDY poll.
- **INIT-007 / INIT-003** — both stated the 1 ms post-reset wait. INIT-003 owns the figure;
  INIT-007 keeps the step and cites it, so the sequence stays complete.
- **INIT-005 / REG-011 and REG-017** — the System Reset exception list repeated each register's
  own reset behavior. INIT-005 names the two exempt registers and cites their rows.
- **INIT-014 / TX-016** — both stated that an oversize frame is aborted on transmit unless huge
  frames are enabled. TX-016 owns the transmit case and its two overrides; INIT-014 keeps the
  programming requirement and the receive side.
- **INIT-019 / REG-011** — both stated that setting PWRSV clears CLKRDY. REG-011 owns it.
- **IRQ-006 / IRQ-007** — IRQ-006 restated that PKTIF still clears the documented way. Removed;
  what IRQ-006 keeps of the erratum's limits is the INT pin's continued reliability.
- **RX-008 and RX-013 / IRQ-010** — both set out when RXERIF is set. IRQ-010 owns the flag's set
  conditions; the two RX rows cite it and keep their own rules.
- **PHY-011 / PHY-012** — both carried the obligation to program PDPXMD explicitly. PHY-012, the
  `inference` row whose whole subject it is, owns it; PHY-011 keeps the reset-value derivation.
- **IRQ-011 / PHY-016 and PHY-017** — IRQ-011 said where the present link state is read, which
  those two rows define. Now a cross-reference.

Also from the reviewer's corpus sample rather than its overlap table: **RX-017 / RX-008**, whose
one-unused-byte explanation repeats RX-008's write-boundary rule. Kept as a cross-reference, not
a scored clause, as the reviewer asked.

**Examined and left, with the reason.** REG-019 / INIT-012 — one states the PADCFG encodings and
the TXCRCEN pairing rule, the other recommends a configuration; they touch but neither restates
the other. TX-001 / TX-016 — TX-016 uses the per-packet override as a condition rather than
restating the control byte's layout. SPI-013 / SPI-015 — two different wrap cases, not one clause
twice.

### 3. Claim corrections the reviewer established from the corpus

- **PHY-006** — "reserved bits are written as 0" contradicts Register 2-2, which requires PHLCON
  bits 13-12 written as 1; section 3.3's general wording does not override a register's own
  definition. Withdrawn and replaced by PHY-033, which defers to the register-specific rule and
  names PHLCON as the case in point.
- **PHY-030** — restated: the driver aborts initialization when its PHLCON write does not complete
  before its own timeout. The diagnosis of an absent PHY was a reading of intent rather than of
  behavior, and the clause saying any check or none is permitted went with it, because the corpus
  prescribing no check does not establish that every check is permitted.
- **TX-004** — the bare "success is judged by TXABRT being clear" is removed; DS39662E section
  12.1.4 also requires that the host did not clear TXRTS, and IRQ-008 states the two together.
- **INIT-008** — the ESTAT check keeps its status as issue 19's *example* of a verification, with
  the row stating the general obligation (verify an expected reset state, retry if it fails) and
  saying the issue does not exclude other state a host could check.
- **REG-026** notes — now point at ERR-001's unqualified vendor instruction not to use the DMA
  module for checksum calculations at all, instead of paraphrasing it as a prohibition only while
  reception is possible.
- **TX-010** notes — calling the driver's full-duplex application of the TXRST workaround
  "harmless" exceeds the evidence. Both the merged note and reader B's note now mark it
  unresolved: nothing in the corpus says what pulsing TXRST costs outside issue 12's conditions.
- **PHY-024** — "software cannot compensate" is stronger than issue 7 supports. Now: the published
  workaround is correct TPIN wiring, and the corpus supplies no software workaround.
- **PHY-020** — the reset value was `0x342x`, which leaves the whole low nibble unknown. Table 3-3
  prints `0011 0100 0010 001x`, so the row now gives the binary form and says 0x3422 with bit 0
  alone unknown.
- **RX-038** — the vendor recommendation is context referring to RX-018, not a second scored
  hardware clause. The statement keeps the driver's policy and that alternatives are permitted;
  the notes carry the recommendation as the evidence that they are.

### 4. The operating envelope behind two critical weights

**The finding.** Under the necessity-adjusted weight rule, `critical` means a working driver
cannot avoid the requirement — but INIT-024's own third-reader derivation notes that reception
does not depend on MAADR in promiscuous mode, which is a counterexample to the universal
consequence. PHY-018's half-duplex rationale has the same gap.

**Neither weight changed.** The envelope the weights assume is now explicit in two places:

- **`SCORING-POLICY.md`** gains "The operating envelope the weights assume", beside the weight
  discussion: a driver that brings up an ordinary Ethernet interface, receiving frames addressed
  to its own unicast address and to broadcast, transmitting, and interoperating with a link
  partner in either duplex. A requirement a driver can avoid only by operating outside that
  envelope, such as running permanently in promiscuous mode, is still `critical`. The section also
  says what the envelope is not: it bounds the necessity argument, it is not a scope rule, and the
  optional-feature cap still applies.
- **INIT-024** and **PHY-018** each gained a `notes` clause naming that envelope clause as what
  their weight rests on — for INIT-024 the unicast reception the envelope requires against the
  promiscuous counterexample, for PHY-018 that half duplex is inside the envelope and is the
  device's reset default.

### 5. Scoring policy ambiguities

All six the reviewer listed are applied in `SCORING-POLICY.md`, in its own voice:

- **Out-of-scope precision** (Eligibility) — scope, recoverability and withdrawal filter the
  ledger's recall and probe rosters only; precision evaluates every claim the candidate makes. An
  incorrect wake-on-LAN claim is a precision error although IRQ-016 is out of scope.
- **Unsupported, contradicted, misattributed** (Precision adjudication) — a necessity claim is
  contradicted when the corpus establishes a valid alternative, unsupported when the corpus is
  silent, and an attribution error when credited to a named source that does not state it,
  whether or not the requirement is true.
- **Inference versus `misstated`** (Uncertainty) — correct inference content presented as
  documented fact is covered content with a separate precision attribution error, explicitly not a
  `misstated` recall row.
- **Table segmentation** (Precision adjudication) — count semantic assertions independent of
  formatting; a label and its value form one assertion, so a candidate cannot move its precision
  by reformatting.
- **Context and implication** (Precision adjudication) — a row's `statement` is the scoring
  target and its `notes`, locators and cross-references are not; and a candidate stating a
  concrete value from which a row's content follows covers that row, with RX-029 and
  `ERXST = 0x0000` as the worked example.
- **The precision formula** (Precision adjudication) — written out as `(N - errors) / N`, with
  unsupported and partial claims staying in `N` and not counted as errors, and `n/a (0 claims)`
  for `N = 0`.

### 6. Stale statements

- **`README.md`** open-work paragraph and **`SCORING-POLICY.md`** Binding paragraph both still
  said the checker does not enforce the policy version and hash. Both now say what it does
  enforce, including that two absent versions no longer compare equal, that `LEDGER-FORMAT.md`'s
  bytes are pinned, and that a repository revision is required.
- **`README.md`** freeze instructions now list every field the lock must carry, as a table:
  `frozen`, `revision`, `sha256`, `corpus_sha256`, `policy_version`, `policy_sha256`,
  `format_sha256`.
- **`README.md`** attestation takes the reviewer's revised opening, which acknowledges authorized
  composites — "Each scored proposition has one active scoring representation, except any
  duplicated contributions explicitly enumerated by the frozen policy. Multi-proposition scoring
  units are explicitly enumerated and use that policy's verdict rule." The rest of the attestation
  is unchanged.

### Counts after this pass

**211 -> 213 rows; 202 -> 204 active, 9 withdrawn.** Two rows minted (PHY-033, TX-024), none
withdrawn. Twenty-four rows had a statement narrowed or corrected and twenty-two gained notes
recording why. Classes: 178 documented-hardware-requirement, 19 implementation-choice, 13
observed-software-behavior, 3 inference, 0 unresolved-conflict. Weights: 66 critical, 64
important, 83 minor; 180 rows carry both readers. Composite scoring units: **16 -> 113**, against
91 atomic rows. Scoring policy: `enc28j60-1.1` -> `enc28j60-1.2`.

**The recall denominator moves from 161 rows to 163** — 64 critical, 58 important, 41 minor —
because PHY-033 and TX-024 are new in-scope `documented-hardware-requirement` rows. Recall
percentages under `enc28j60-1.2` are not comparable with any computed under the earlier versions,
which is what the version bump records. No candidate has been scored under any of them.

`ledger_check.py ledger.yaml` and `ledger_check.py ledger.yaml --freeze` both report 0 errors and
0 warnings; the leak scan over `ledger.yaml`, `SCORING-POLICY.md`, `LEDGER-CONFLICTS.md`,
`ADJUDICATION.md` and `README.md` against the pinned driver files is clean; the checker's unit
tests pass. `ledger.lock` was **not** written: the freeze is a separate step, and the attestation
it carries is the adjudicator's to sign.

## Pre-freeze repairs, second pass 2026-09-20

The same outside reviewer read the ledger again at commit `f70e1ac`, read-only, reproduced the
clean mechanical gate and the 163-row denominator, and **again refused the freeze**: the atomic
inventory had counterexamples under its own written test, PHY-033 duplicated PHY-020, INIT-014 had
acquired a factual regression during the first pass's narrowing, TX-016's formulation contradicted
Figure 7-1, two precision rules still conflicted, and cross-referenced clauses were still written
out beside their cross-references. This pass clears those. IDs omit `ENC28J60-`.

**Held back deliberately.** The weights of INIT-024 and PHY-018, and the operating-envelope section
of `SCORING-POLICY.md` the two rest on, are untouched: the owner is deciding the benchmark profile
first and the weights follow from it. The review's finding that the envelope's promiscuous
worked example is wrong on its own terms — promiscuous reception includes frames addressed to the
interface itself, so "never accepts its own unicast address" does not describe a promiscuous
driver — is recorded here and left for that decision. Nothing else in this pass depends on it.

### 1. Proportional partial credit, and the fact-count inventory it rests on

**The finding.** A composite row earned a flat 0.5 whatever fraction of it was right, so one
correct field and every field but one scored the same; and the atomic/composite boundary was
applied inconsistently, which matters because the two verdict rules give different outcomes for
the same incomplete candidate. The reviewer named nine rows it believed misclassified.

**What was done.** The classification problem is subsumed rather than argued: **every active row
was walked and the independently checkable facts it asserts were enumerated and counted**, and the
count decides the class by construction — 1 is atomic, 2 or more is a composite unit whose count is
the denominator of its partial credit. The counting conventions are written into the policy so the
walk is reproducible: an attribute rides with the element it qualifies; a mechanism, condition or
consequence rides with the requirement it serves when contradicting it would falsify that
requirement; a clause entailed by another fact in the same row, or one whose work is to record the
row's class or provenance, is not counted.

- **203 active rows, 689 facts, 141 composite units and 62 atomic rows.** Distribution: 62 rows at
  1 fact, 30 at 2, 42 at 3, 20 at 4, 18 at 5, 11 at 6, 20 at 7 or more. The largest are TX-008 at
  21, INIT-010 at 17, RX-011 at 15, REG-003 at 14, RX-019 at 12 and REG-001 at 12. Per facet the
  composite units are REG 26, INIT 13, TX 17, RX 21, IRQ 13, PHY 27, SPI 16, ELEC 7, ERR 1.
- **Twenty-eight rows moved from atomic to composite; none moved the other way.** REG-005;
  INIT-014; TX-016, TX-017, TX-020, TX-024; RX-008, RX-010, RX-013, RX-033, RX-036, RX-037;
  IRQ-002, IRQ-003, IRQ-005; PHY-005, PHY-010, PHY-023, PHY-024, PHY-025, PHY-027, PHY-028;
  SPI-007, SPI-009, SPI-010, SPI-017, SPI-018, SPI-022.
- **The counts live in the policy's composite table as a third column**, not in `ledger.yaml`: the
  ledger stays readable and the counts are frozen policy text that only a new policy version can
  change. For an atomic row nothing is recorded, and the absence of an entry is the claim that the
  row holds one fact.
- **The verdict rule** is now `covered` when every enumerated fact is stated correctly; `partial`
  when at least one is correct, the rest omitted or underspecified and none contradicted, earning
  the fraction correct over the row's frozen count; `missing` when none is stated; `misstated` when
  at least one is contradicted, earning zero. The policy says explicitly that the frozen count and
  not a scorer's own segmentation is the denominator. Atomic rows keep the ordinary 0.5, since
  dividing one correct fact by a count of one would turn every partial into a coverage.

**The reviewer's nine named rows: agreement on all nine.** REG-005 is three prefix mappings (the
bank 3 examples follow from them and are not counted). PHY-005 is three prohibitions while BUSY.
SPI-018 is read and write bit order. RX-010 is field position, byte order and what the count
includes. PHY-027 is link-state reading and duplex reporting. TX-024 is FCEN0's mechanism and the
vendor's deployment advice. INIT-014 is the programming requirement, the standard-frame value and
the receive-side rejection, at 3. INIT-008 is atomic **after** the ESTAT example moved to notes, as
the reviewer conditioned it. PHY-033 is withdrawn rather than classified. The walk also found
nineteen further rows the review had not named, which is what an enumeration buys over a sample.

**Two narrative errors corrected.** The "enumerated rather than split" paragraph said 111 of 113
took the enumeration disposition; the table enumerates **all** of them, because PHY-006 and TX-019
stayed composite after a clause was split out of each and the split rows joined the population
rather than replacing entries. And "splitting would reopen a settled merge" is gone as a rationale:
REG-023 is kept whole because the intended unit is the block of MAC timing and limit values a
driver programs in one step from one table, and RX-019 because ERXFCON's bit positions and the
combination semantics those bits select are read in one register definition and the ANDOR rule
cannot be stated apart from the bits it combines.

**Added, adapted from the review**: recall measures coverage of the frozen scoring units and not
the fraction of independent hardware facts recovered, and atomic and composite verdict counts are
reported separately alongside the weight buckets. It appears in both the composite section and
"Reporting".

**`SCORING-POLICY.md` is bumped to `enc28j60-1.3`** with the version history extended. Every
partially covered row's contribution moves, so no recall number under it is comparable with one
computed under `enc28j60-1.2`.

### 2. Row repairs the review established from the corpus

- **PHY-033, withdrawn into PHY-020** (`replaced_by`). Its hardware content is PHLCON's
  reserved-as-1 rule, which PHY-020 already states and scores, so the pair put one proposition in
  the denominator twice. What remained was an instruction about reading documentation — look a
  register's write rule up in that register's own definition — which is authoring guidance and is
  now in `LEDGER-FORMAT.md` beside the derivation rules. **The provenance point**: PHY-033's
  `readers` were inherited from the PHY-006 clause that asserted the incorrect universal-zero rule,
  and credit for a wrong statement does not establish independent derivation of its correction, so
  the withdrawal credits no reader to PHY-020; PHY-020 keeps the readers its own statement earned.
  Whether the original drafts support crediting a reader there is a separate finding to be made
  from the drafts.
- **INIT-014**, regression fixed. It said oversized frames are rejected on receive without
  qualification; DS39662E Register 6-2 allows oversized reception when MACON3.HFRMEN is set. Now:
  rejected on receive when HFRMEN is clear, with the transmit-side selection rule owned by TX-016.
- **TX-016**, factual error fixed. The OR formulation permitted oversized transmission whenever
  HFRMEN was set, including with POVERRIDE set and PHUGEEN clear, while Figure 7-1 makes the
  per-packet setting override MACON3. Now a selection: PHUGEEN controls permission when POVERRIDE
  is set, otherwise MACON3.HFRMEN does, and transmission aborts at the MAMXFL limit when the
  selected control disallows huge frames.
- **TX-004** says "on successful completion", so the row no longer silently re-covers the aborts
  TX-007 owns.
- **INIT-012** drops the parenthetical TXCRCEN pairing requirement and refers to REG-019, which
  owns it.
- **INIT-008** moves the ESTAT example register values into notes; the scored statement is the
  verification-and-retry procedure alone.

### 3. The two policy rules that were still wrong

- **Implementation choices and necessity.** Eligibility made asserting an implementation choice as
  necessary automatically `misstated`, and the composite rule extended that trigger to "at least
  one" enumerated fact. Replaced, in the review's terms: an implementation-choice row is a
  precision probe for the selected policy or value that row identifies; asserting its necessity is
  an error only where the corpus establishes an alternative, and otherwise the unsupported rule
  applies; constituent hardware requirements inside such a sequence remain independently valid and
  are judged against the rows that own them. **PHY-030's notes** are corrected with it: they called
  a required-initialization claim `misstated` categorically, although the corpus prescribing no
  liveness check establishes the absence of a prescription, not the presence of an alternative.
- **Cross-references.** Both halves of the review's proposal are applied. The policy now says a
  clause explicitly assigned to another row is scored only in the owner row, even where it is
  reproduced beside its cross-reference, and is not an enumerated fact of the row reproducing it.
  And the restated wording is removed where the sentence still reads without it: **INIT-007** now
  says to observe the post-reset wait INIT-003 specifies instead of writing out the 1 ms, and
  **INIT-005** cites the exceptions REG-011 and REG-017 state instead of naming them again.

### Counts after this pass

**213 rows, 203 active (was 204), 10 withdrawn.** One row withdrawn (PHY-033), none minted. Seven
rows had a statement corrected or narrowed (INIT-005, INIT-007, INIT-008, INIT-012, INIT-014,
TX-004, TX-016) and eleven gained or changed notes recording why. Classes over all
rows are unchanged at 178 documented-hardware-requirement, 19 implementation-choice, 13
observed-software-behavior, 3 inference; active rows are 168, 19, 13 and 3. Weights over all rows
are unchanged at 66 critical, 64 important, 83 minor; 180 rows carry both readers. Composite
scoring units: **113 -> 141**, against 62 atomic rows. Scoring policy: `enc28j60-1.2` ->
`enc28j60-1.3`.

**The recall denominator moves from 163 rows to 162** — 64 critical, 57 important, 41 minor —
because PHY-033 was withdrawn. Of the 162, 127 are composite units and 35 atomic; fourteen of the
141 composite units sit outside every recall denominator and are scored only for precision.
Recall percentages under `enc28j60-1.3` are not comparable with any computed under an earlier
version, which is what the bump records. No candidate has been scored under any of them.

`ledger_check.py ledger.yaml` and `ledger_check.py ledger.yaml --freeze` both report 0 errors and 0
warnings, and the checker reads 141 composite ids from the new three-column table, so the added
column did not trip the list-versus-total check. The leak scan over `ledger.yaml`,
`SCORING-POLICY.md`, `LEDGER-CONFLICTS.md`, `ADJUDICATION.md` and `README.md` against the pinned
driver files is clean, and the checker's unit tests pass. `ledger.lock` was **not** written: the
freeze is the adjudicator's step, and the two held-back weights are still open.

## Pre-freeze repairs, third pass 2026-09-20

The same outside reviewer read the ledger again at commit `4516643`, read-only, reproduced the
clean mechanical gate and the arithmetic (203 active rows, 141 composites, 62 atomic, 689 declared
facts, 162 recall-eligible rows), accepted the row repairs and the explicit operating profile, and
**again refused the freeze** — this time entirely about the new scoring scheme. The finding that
drove this pass: **a frozen count does not freeze the numerator.** For many rows the policy
announced a quantity without saying which facts it was counting, so two scorers could divide by the
same denominator and disagree about the top. Alongside it, several counts contradicted the policy's
own counting conventions, the grouping some counts relied on was nowhere stated, and the composite
verdict rule had an uncovered case. IDs omit `ENC28J60-`.

### 1. `SCORING-FACTS.md`, the fact lists

**What was done.** Every one of the 141 composite units now has an ordered, numbered list of its
credit-bearing facts in a new file, `SCORING-FACTS.md`; the list's length is the unit's count, and
the count is printed at the end of each unit so the two can be checked against each other and
against the policy's table by eye or by script. Each entry is one clause and a short corpus locator
taken from the row's own `derivation`. A scorer records a disposition against each listed fact and
**may not subdivide, combine or substitute**.

The lists are a separate file on purpose: `ledger.yaml` stays readable and `SCORING-POLICY.md`
stays short enough to be read whole. The policy names the file, says the lists are the numerator
side of every composite fraction, and requires the lock to carry the file's sha256 as
`facts_sha256` — a list anyone can edit fixes nothing. `LEDGER-FORMAT.md` authoring rule 3 and the
README's file table and freeze instructions name it too, and the leak scan now covers it.

**The lists were reconstructed from the frozen counts wherever the count reconstructed into a
defensible list, which was 133 of the 141 units.** Eight did not, and in each the count moved to
match the list rather than the list being padded to match the count. **The fact total moves from
689 to 687** (625 in composite units plus 62 atomic rows). The unit count does not move: no unit
fell to one fact, so the composite roster is still 141 ids and the recall denominator is still 162
rows.

### 2. The six counts that contradicted the attribute convention

The policy says an attribute rides with the element it qualifies. Six counts violated it, and all
six are corrected as the reviewer proposed; none of them was a case where the convention looked
wrong rather than the count, so no convention change is proposed in their place.

- **RX-012, 3 to 2.** PKTDEC's self-clearing rides with the write-and-decrement fact.
- **IRQ-007, 4 to 2.** The read-only access and the ineffective Bit Field Clear both ride with the
  clearing rule, leaving the set condition and the clearing rule.
- **PHY-016, 7 to 6.** The six status fields' read-only access rides with the fields.
- **PHY-026, 3 to 2.** The read-only constancy rides with the two identifier values, and the OUI
  and part-number reading follows from them.
- **PHY-031, 3 to 2.** In an eight-bit register the implemented five-bit field and the
  unimplemented upper three bits are one mask stated from both ends; the reset value is separate.
- **PHY-032, 7 to 6.** "The fields select a function from a code table" is the frame for the six
  mappings, not a seventh fact beyond them.

**A consequence worth stating, because it decides scores.** Folding an attribute into its element's
fact would delete the attribute from the scoring surface if the fact could then be earned without
it. So the folded attribute is **required**: `SCORING-FACTS.md` carries it in the entry, and a
candidate that gives PHY-016's six bit positions without their read-only access earns zero of that
row rather than all of it. See item 4.

**One superficially similar count kept.** REG-022's "all three bits apply to half duplex only" was
left as its own fact. It is a condition on when the three bits act, not a width, an access or a
self-clearing behavior, and contradicting it would not falsify any of the three bit definitions —
which is the test the second convention states. The count stays at 5.

### 3. The grouping convention, now stated

**The finding.** Several counts treated a set as one fact while the policy elsewhere promised one
register placement or one code per fact. That is a defensible scoring choice and it was not the
stated rule.

**Added to the policy**, as a fourth counting convention: a listed set may be designated one
credit-bearing fact; it earns credit only when every listed member and the shared property are
stated correctly; naming some members earns nothing and a scorer may not award part of it. Every
such set is marked `[grouped set]` in `SCORING-FACTS.md` with its members written out. The policy
also stops describing the total as an inventory of independently checkable propositions and says
what it is: a count of credit-bearing units of judgment, some of which are sets judged whole. Two
smaller conventions are marked the same way — a low/high register pair is one placement, and a
multi-bit field or a run of reserved bits described as one range is one fact.

**Kept as grouped sets**, each now explicit: REG-002's two eight-register blocks; REG-003's seven
reserved addresses; REG-004's six-address MAC address block; REG-013's three-register 0x05FA group
and eight-register zero group; REG-014's six zero-reset registers; RX-011's reserved bits 17 and
19; PHY-008's reserved pair, PHY-018's three reserved ranges and PHY-020's two reserved-bit
rules; INIT-010's receive-pointer and transmit-pointer steps; INIT-011's pause-enable pair; INIT-017's two
collision registers; RX-018's ERXST/ERXND pair; RX-021's two unprogrammed filters; RX-026's three
reprogrammed pointers; IRQ-011's two PHY enables; IRQ-016's CRCEN/MPEN and PKTIE/INTIE pairs;
TX-007's two clearable bits. The test they pass: the corpus presents the set as one thing — a block
of consecutive addresses, a column of identical reset values, a pair that cannot be written singly.

**REG-017's `11x` kept as one fact, not a group.** Register 2-1 prints `11x` as a single row, so it
is one code-pattern fact rather than two codes grouped. The count stays at 10.

**Split: REG-019, 6 to 10.** The reviewer named it the least defensible grouping and the corpus
agrees: Register 6-2 prints each of the eight PADCFG codes as its own row with its own outcome —
including four separate rows that each say no automatic padding. Grouping them into four outcome
groups would mean a candidate naming three of the four no-padding codes earns nothing for them. The
eight codes are now eight facts, with the TXCRCEN pairing and the TXCRCEN-clear behavior, giving
10. This is the one count in this pass that grew for a reason other than an uncounted proposition.

### 4. The verdict rule, and what "fully correct" means

**The uncovered case.** A candidate can state recognizable content for a composite while getting no
single fact fully right. That was neither `partial` ("at least one correct") nor `missing` ("none
stated"). The rule is replaced, adapted from the review: let n be the number of listed facts and k
the number the candidate states fully correctly; an underspecified fact contributes zero; any
contradicted fact makes the row `misstated` and the test comes first; otherwise all n is `covered`,
no recognizable content for the unit is `missing`, and everything else is `partial` earning k/n,
**including k = 0**. The two zero-scoring verdicts stay distinct because they are different
failures and are reported as separate counts.

**"Fully correct" is decided, not left open.** A listed fact is fully correct when everything its
entry names is stated correctly — the element and every attribute the entry carries. A correct
address with a named access **omitted** is underspecified: zero for that fact, and the row is not
`misstated`. The same attribute stated **wrongly** is a contradiction, and the row is `misstated`.
An attribute the entry does not name is not required. The strict reading is what keeps item 2's
folding from erasing content, and it is applied consistently in the lists: an entry carries the
attributes that are credit-bearing for that unit and no others.

### 5. The four partitions the reviewer wanted reconciled

Writing the lists settled all four. Where a convention decided it, the convention is named.

- **RX-008, 3 kept.** Boundary, the abort of the offending packet, and the host's advance
  obligation. The obligation is a requirement on the host, not a consequence whose contradiction
  would falsify the boundary, so the second convention leaves it standing as its own fact.
- **RX-033, 2 kept.** In-order processing, and the copy-to-keep rule. The single read pointer is
  the mechanism behind the first and rides with it; the second is a separate obligation, and a
  candidate denying it has not denied in-order processing.
- **PHY-010, 2 kept, relabeled.** The facts are the absence of autonegotiation and what an
  autonegotiating partner detects. "Full duplex works only when both ends are manually configured"
  follows from the two and is not counted; the table's "manual-configuration consequence" was the
  ambiguous wording the reviewer objected to and is gone.
- **SPI-017, 2 kept, each carrying its condition.** Both entries state the remedy **and** the
  operating condition it remedies, so a candidate recommending a clock arrangement without the
  erratum's condition has not stated either fact fully and earns nothing ambiguous.

### 6. INIT-010's seventeenth step, and the eighteenth

The seventeen reconstruct exactly as the reviewer guessed — receive pointers grouped, transmit
pointers grouped, MAIPG and MABBIPG separate, the three PHY writes separate — and those groups are
now declared rather than implied. The statement's remaining clause, that interrupts and RXEN are
enabled in a later step, is a proposition about the driver's order that none of the seventeen
entails, so it is **fact 18**. The count moves 17 to 18. INIT-010 is an implementation-choice row,
so this changes probe scoring only, never recall.

### 7. Two wording alignments

- **`LEDGER-FORMAT.md`'s definition of `critical`.** Added, adapted from the review: for this
  pilot, "does not work" includes failing to satisfy a behavior the operating profile in
  `SCORING-POLICY.md` explicitly requires, and it does not imply that an implementation outside the
  profile is nonfunctional. A promiscuous software-filtering driver works; it is not the driver
  this benchmark measures.
- **Reporting.** A score report now names **which** critical facts a candidate missed, by their
  numbers in `SCORING-FACTS.md`, for every `critical` unit scored `partial` — because a candidate
  can earn four fifths of PHY-018 while omitting HDLDIS, the fact the profile makes that row
  critical for, and the fraction alone hides it. The same section states that the outer denominator
  is the 162 eligible rows and not 687 facts.

### Counts after this pass

**213 rows, 203 active, 10 withdrawn — unchanged.** No row was minted, withdrawn, or had its
statement, class, weight or scope changed: this pass touched scoring policy only. Composite scoring
units: **141, unchanged**; atomic rows 62, unchanged; the recall denominator stays at 162 rows, 127
of them composite.

**Facts: 689 to 687**, 625 of them inside composite units. Eight counts moved — REG-019 6 to 10,
INIT-010 17 to 18, RX-012 3 to 2, IRQ-007 4 to 2, PHY-016 7 to 6, PHY-026 3 to 2, PHY-031 3 to 2,
PHY-032 7 to 6 — and the distribution is now 62 rows at 1 fact, 34 at 2, 39 at 3, 19 at 4, 18 at 5,
12 at 6 and 19 at 7 or more; the largest are TX-008 at 21, INIT-010 at 18, RX-011 at 15, REG-003 at
14, REG-001 and RX-019 at 12. Scoring policy: `enc28j60-1.3` -> **`enc28j60-1.4`**, with the
version history extended. Recall numbers under 1.4 are not comparable with any computed under 1.3,
which is what the bump records; no candidate has been scored under any version.

`ledger_check.py ledger.yaml` and `ledger_check.py ledger.yaml --freeze` both report 0 errors and 0
warnings, the leak scan over `ledger.yaml`, `SCORING-POLICY.md`, the new `SCORING-FACTS.md`,
`LEDGER-CONFLICTS.md`, `ADJUDICATION.md` and `README.md` against the pinned driver files is clean,
and the checker's 18 unit tests pass. The checker as it stood at the end of this pass does not yet
read `SCORING-FACTS.md`; the fact lists were verified against the policy's table by a throwaway
script — 141 units present, every list numbered from 1 with no gap, every list length equal to its
printed count and to the policy's, and the per-facet composite counts unchanged. `ledger.lock` was
**not** written: the freeze is the adjudicator's step.
