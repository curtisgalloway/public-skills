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
