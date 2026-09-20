<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# ENC28J60 gold ledger: the credit-bearing facts

Version: enc28j60-1.4 (frozen with `SCORING-POLICY.md` of the same version; the lock records this
file's sha256 as `facts_sha256`)

`SCORING-POLICY.md` gives every composite scoring unit a frozen fact count, and a composite
`partial` earns the fraction of that count the candidate stated. A frozen count fixes the
denominator of that fraction and nothing else: two scorers can divide by the same number and still
disagree about the top, because a count on its own does not say *which* facts it counted. This file
says which. **One ordered list per composite unit, and the list's length is the count.**

A scorer records a disposition against each listed fact and **may not subdivide, combine or
substitute facts**. A row that is not in this file is atomic and keeps the ordinary verdict rule.

## How a list works

- **The order is fixed** so two scorers can compare fact by fact. Entry *n* means the same thing to
  both of them.
- **Each entry is one clause and its corpus locator.** Locators are short forms of the row's own
  `derivation` in `ledger.yaml`: `DS39662E` and `DS39662C` are the data sheet editions, `DS80349C`
  and `DS80349B` the errata editions, `Reg` a register definition, `T` a table, `§` a section.
  `driver` means the pinned reference driver at the commit `corpus.yaml` names — a locator only,
  never a quotation.
- **The count printed at the end of each unit equals the list length**, and equals the number in
  `SCORING-POLICY.md`'s composite table. The three are the same frozen number.
- **Nothing here is new scoring surface.** A fact is listed only where the row's `statement`
  already asserts it; `notes` and `derivation` are context and are never scored
  (`SCORING-POLICY.md` → "What a verdict is given against").

## What "fully correct" means

A listed fact is **fully correct** when everything the entry names is stated correctly: the
element, and every attribute the entry carries with it — a width, an access, a self-clearing
behavior, a condition, a unit.

- A candidate that states a register's address correctly but **omits** an access the entry names
  has stated that fact **underspecified**. It earns zero for that fact and does not make the row
  `misstated`.
- A candidate that states a named attribute **wrongly** has contradicted the fact, and a
  contradicted fact makes the whole row `misstated`, earning zero.
- An attribute the entry does **not** name is not required and its absence costs nothing.

The strict reading is deliberate. The counting conventions fold an attribute into its element's
fact rather than counting it separately; if the folded attribute were then not required for credit,
folding it in would have deleted it from the scoring surface altogether. So the entries carry the
attributes that are credit-bearing for that unit, and only those.

## Grouped sets

A listed set may be designated **one** credit-bearing fact. Such an entry is marked `[grouped set]`
and states its members. It earns credit **only when every listed member and the shared property are
stated correctly**; naming some members earns nothing, and a scorer may not award a part of it.

Because grouping is in play, the totals below are **not** an inventory of independently checkable
propositions. They are a count of credit-bearing units of judgment, some of which are sets judged
whole.

Two smaller conventions with the same effect, marked the same way:

- `[pair]` — a register that the corpus places as a low/high byte pair is **one** placement, and
  both halves are required. `[field]` — a multi-bit field or a run of reserved or unimplemented bits
  described as one range is one fact, not one per bit.
- `[code pattern]` — a table row whose code carries a don't-care bit (`11x`) is one fact, because
  the corpus prints it as one row, not two codes.

Where the corpus prints each member as its own row with its own outcome, grouping is **not**
applied; `REG-019` was split for exactly that reason on 2026-09-20 (`LEDGER-CONFLICTS.md`,
third pass).

## REG

### REG-001 — bank 0 buffer pointer placements

1. ERDPT at 0x00/0x01 [pair] — DS39662E T3-1 bank 0.
2. EWRPT at 0x02/0x03 [pair] — DS39662E T3-1 bank 0.
3. ETXST at 0x04/0x05 [pair] — DS39662E T3-1 bank 0.
4. ETXND at 0x06/0x07 [pair] — DS39662E T3-1 bank 0.
5. ERXST at 0x08/0x09 [pair] — DS39662E T3-1 bank 0.
6. ERXND at 0x0A/0x0B [pair] — DS39662E T3-1 bank 0.
7. ERXRDPT at 0x0C/0x0D [pair] — DS39662E T3-1 bank 0.
8. ERXWRPT at 0x0E/0x0F [pair], read-only — DS39662E T3-1 bank 0, T3-2.
9. EDMAST at 0x10/0x11 [pair] — DS39662E T3-1 bank 0.
10. EDMAND at 0x12/0x13 [pair] — DS39662E T3-1 bank 0.
11. EDMADST at 0x14/0x15 [pair] — DS39662E T3-1 bank 0.
12. EDMACS at 0x16/0x17 [pair] — DS39662E T3-1 bank 0.

Bank membership (bank 0, BSEL = 00) rides with each placement; an address without its bank is not
a placement. **Count: 12**

### REG-002 — bank 1 filter register placements

1. EHT0 to EHT7 at 0x00 to 0x07 [grouped set: all eight, consecutive from 0x00] — DS39662E T3-1 bank 1.
2. EPMM0 to EPMM7 at 0x08 to 0x0F [grouped set: all eight, consecutive from 0x08] — DS39662E T3-1 bank 1.
3. EPMCSL/EPMCSH at 0x10/0x11 [pair] — DS39662E T3-1 bank 1.
4. EPMOL/EPMOH at 0x14/0x15 [pair] — DS39662E T3-1 bank 1.
5. ERXFCON at 0x18 — DS39662E T3-1 bank 1.
6. EPKTCNT at 0x19 — DS39662E T3-1 bank 1.

**Count: 6**

### REG-003 — bank 2 MAC and MII placements

1. MACON1 at 0x00 — DS39662E T3-1 bank 2.
2. MACON3 at 0x02 — DS39662E T3-1 bank 2.
3. MACON4 at 0x03 — DS39662E T3-1 bank 2.
4. MABBIPG at 0x04 — DS39662E T3-1 bank 2.
5. MAIPGL at 0x06 — DS39662E T3-1 bank 2.
6. MAIPGH at 0x07 — DS39662E T3-1 bank 2.
7. MACLCON1 at 0x08 — DS39662E T3-1 bank 2.
8. MACLCON2 at 0x09 — DS39662E T3-1 bank 2.
9. MAMXFLL/MAMXFLH at 0x0A/0x0B [pair] — DS39662E T3-1 bank 2.
10. MICMD at 0x12 — DS39662E T3-1 bank 2.
11. MIREGADR at 0x14 — DS39662E T3-1 bank 2.
12. MIWRL/MIWRH at 0x16/0x17 [pair] — DS39662E T3-1 bank 2.
13. MIRDL/MIRDH at 0x18/0x19 [pair] — DS39662E T3-1 bank 2.
14. Addresses 0x01, 0x0C, 0x0D, 0x0E, 0x10, 0x11 and 0x15 are reserved [grouped set: all seven] — DS39662E T3-1 bank 2.

**Count: 14**

### REG-004 — bank 3 placements

1. The MAC address registers occupy 0x00 to 0x05 [grouped set: all six addresses; the octet order is ENC28J60-REG-020's fact, not this one] — DS39662E T3-1 bank 3.
2. EBSTSD at 0x06 — DS39662E T3-1 bank 3.
3. EBSTCON at 0x07 — DS39662E T3-1 bank 3.
4. EBSTCSL/EBSTCSH at 0x08/0x09 [pair] — DS39662E T3-1 bank 3.
5. MISTAT at 0x0A — DS39662E T3-1 bank 3.
6. EREVID at 0x12 — DS39662E T3-1 bank 3.
7. ECOCON at 0x15 — DS39662E T3-1 bank 3.
8. EFLOCON at 0x17 — DS39662E T3-1 bank 3.
9. EPAUSL/EPAUSH at 0x18/0x19 [pair] — DS39662E T3-1 bank 3.

**Count: 9**

### REG-005 — register group prefixes

1. A name beginning `E` identifies an ETH register — DS39662E §3.1.
2. A name beginning `MA` identifies a MAC register — DS39662E §3.1.
3. A name beginning `MI` identifies an MII register — DS39662E §3.1.

The bank 3 examples in the statement follow from the three mappings and are not counted.
**Count: 3**

### REG-006 — reserved and unimplemented addresses

1. Address 0x1A in every bank is reserved and must be neither read nor written — DS39662E §3.1.
2. Other reserved registers may be read but their contents must not be changed — DS39662E §3.1.
3. Unimplemented addresses ignore writes and read as zero — DS39662E §3.1.

**Count: 3**

### REG-007 — names the reference driver defines at reserved addresses

1. Bank 2 address 0x01 is named as a MACON2 carrying reset bits — driver header, bank 2 definitions; DS39662E T3-1.
2. Bank 2 address 0x0D is named MAPHSUP — driver header, bank 2 definitions; DS39662E T3-1.
3. Bank 2 address 0x11 is named MICON — driver header, bank 2 definitions; DS39662E T3-1.
4. Bank 1 addresses 0x16/0x17 [pair] are named as wake-on-LAN enable and flag registers — driver header, bank 1 definitions; DS39662E T3-1.

That the corpus does not establish a register at those addresses records the row's class and is not
counted. **Count: 4**

### REG-008 — ECON1 layout

1. TXRST at bit 7, holding the transmit logic in reset — DS39662E Reg 3-1.
2. RXRST at bit 6, holding the receive logic in reset — DS39662E Reg 3-1.
3. DMAST at bit 5, starting the DMA and reading as its busy flag — DS39662E Reg 3-1.
4. CSUMEN at bit 4, selecting DMA checksum mode instead of copy — DS39662E Reg 3-1.
5. TXRTS at bit 3, the transmit request — DS39662E Reg 3-1.
6. RXEN at bit 2, receive enable — DS39662E Reg 3-1.
7. BSEL1:BSEL0 at bits 1:0 [field], the bank select — DS39662E Reg 3-1.
8. Every bit is zero after reset — DS39662E Reg 3-1, T3-2.

**Count: 8**

### REG-009 — ECON2 layout

1. AUTOINC at bit 7, buffer pointer auto-increment, set after reset — DS39662E Reg 3-2.
2. PKTDEC at bit 6: writing 1 decrements EPKTCNT, and the bit clears itself — DS39662E Reg 3-2.
3. PWRSV at bit 5, power save — DS39662E Reg 3-2.
4. Bit 4 reserved and to be kept 0 — DS39662E Reg 3-2.
5. VRPS at bit 3, regulator low-current mode, effective only while PWRSV is set — DS39662E Reg 3-2.
6. Bits 2 to 0 unimplemented [field] — DS39662E Reg 3-2.

**Count: 6**

### REG-010 — ESTAT layout

1. INT at bit 7, an enabled interrupt is pending — DS39662E Reg 12-1.
2. BUFER at bit 6, buffer overrun or underrun, clearable — DS39662E Reg 12-1.
3. Bit 5 reserved — DS39662E Reg 12-1.
4. LATECOL at bit 4, a collision after 64 bytes, clearable — DS39662E Reg 12-1.
5. RXBUSY at bit 2, a packet is being received — DS39662E Reg 12-1.
6. TXABRT at bit 1, transmit aborted, clearable — DS39662E Reg 12-1.
7. CLKRDY at bit 0, the oscillator start-up timer expired — DS39662E Reg 12-1, T3-2 note 1.

**Count: 7**

### REG-011 — what clears CLKRDY

1. ESTAT.CLKRDY is cleared by a Power-on Reset only; a System Reset (pin or SPI command) leaves it unchanged — DS39662E T3-2 note 1.
2. Setting ECON2.PWRSV also clears it — DS39662E §14.0 step 5.

**Count: 2**

### REG-013 — buffer pointer reset values

1. ERDPT, ERXST and ERXRDPT reset to 0x05FA [grouped set: all three registers and the shared value] — DS39662E T3-2 reset column.
2. ERXND resets to 0x1FFF — DS39662E T3-2 reset column.
3. EWRPT, ETXST, ETXND, ERXWRPT, EDMAST, EDMAND, EDMADST and EDMACS reset to 0x0000 [grouped set: all eight registers and the shared value] — DS39662E T3-2 reset column.

That the receive FIFO therefore occupies 0x05FA to 0x1FFF until the host reprograms it follows from
facts 1 and 2 and is not counted. **Count: 3**

### REG-014 — MAC configuration reset values

1. MAMXFL resets to 0x0600 (1536) — DS39662E T3-2 reset column.
2. MACLCON1 RETMAX resets to 0x0F — DS39662E T3-2 reset column.
3. MACLCON2 COLWIN resets to 0x37 (55) — DS39662E T3-2 reset column.
4. MABBIPG, MAIPGL, MAIPGH, MACON1, MACON3 and MACON4 reset to 0 [grouped set: all six registers and the shared value] — DS39662E T3-2 reset column.
5. ERXFCON resets to 0xA1 — DS39662E T3-2 ERXFCON row.

The reading of 0xA1 as unicast, CRC-check and broadcast filtering with OR logic follows from the
value and ENC28J60-RX-019's bit layout, and is not counted here. **Count: 5**

### REG-015 — EREVID and the silicon revision codes

1. EREVID is a read-only 5-bit register at bank 3 address 0x12 holding the silicon revision — DS39662E T3-2 EREVID row and note 2, §3.3.5.
2. Revision B1 reads 0x02 — DS80349C T1.
3. Revision B4 reads 0x04 — DS80349C T1.
4. Revision B5 reads 0x05 — DS80349C T1.
5. Revision B7 reads 0x06 — DS80349C T1.

That the value does not track the revision letter's number follows from facts 2 to 5 and is not
counted. **Count: 5**

### REG-017 — ECOCON and the CLKOUT prescaler

1. ECOCON at bank 3 address 0x15 selects the CLKOUT prescaler in bits 2:0 [field] — DS39662E Reg 2-1, §2.3.
2. Code 000: CLKOUT disabled and the pin driven low — DS39662E Reg 2-1.
3. Code 001: divide by 1 (25 MHz) — DS39662E Reg 2-1.
4. Code 010: divide by 2 — DS39662E Reg 2-1.
5. Code 011: divide by 3 — DS39662E Reg 2-1.
6. Code 100: divide by 4 (6.25 MHz) — DS39662E Reg 2-1.
7. Code 101: divide by 8 — DS39662E Reg 2-1.
8. Code 11x: reserved [code pattern: the corpus prints one row for both values] — DS39662E Reg 2-1.
9. The field resets to 100 on a Power-on Reset — DS39662E T3-2 note 3.
10. It is unchanged by a System Reset — DS39662E T3-2 note 3.

**Count: 10**

### REG-018 — MACON3 layout

1. PADCFG<2:0> at bits 7:5 [field] — DS39662E Reg 6-2.
2. TXCRCEN at bit 4 — DS39662E Reg 6-2.
3. PHDREN at bit 3, excluding a 4-byte proprietary header from the CRC — DS39662E Reg 6-2.
4. HFRMEN at bit 2, allowing frames larger than MAMXFL — DS39662E Reg 6-2.
5. FRMLNEN at bit 1, checking the type/length field against the actual length — DS39662E Reg 6-2.
6. FULDPX at bit 0 — DS39662E Reg 6-2.

**Count: 6**

### REG-019 — PADCFG encodings and the TXCRCEN pairing

1. Code 001: short frames padded to 60 bytes with a CRC appended — DS39662E Reg 6-2 PADCFG.
2. Code 011: short frames padded to 64 bytes with a CRC appended — DS39662E Reg 6-2 PADCFG.
3. Code 111: short frames padded to 64 bytes with a CRC appended — DS39662E Reg 6-2 PADCFG.
4. Code 101: VLAN frames padded to 64 bytes and others to 60, with a CRC appended — DS39662E Reg 6-2 PADCFG.
5. Code 000: no automatic padding — DS39662E Reg 6-2 PADCFG.
6. Code 010: no automatic padding — DS39662E Reg 6-2 PADCFG.
7. Code 100: no automatic padding — DS39662E Reg 6-2 PADCFG.
8. Code 110: no automatic padding — DS39662E Reg 6-2 PADCFG.
9. Whenever PADCFG selects CRC generation, TXCRCEN must also be set — DS39662E Reg 6-2 TXCRCEN.
10. With TXCRCEN clear the MAC appends nothing and reports a CRC error in the transmit status vector when the last four bytes are not a valid CRC — DS39662E Reg 6-2 TXCRCEN.

The corpus prints each of the eight codes as its own row with its own outcome, so they are eight
facts and not four outcome groups. **Count: 10**

### REG-020 — MAC address octet order

1. The first octet on the wire (MAADR<47:40>) is MAADR1 at bank 3 address 0x04 — DS39662E T3-2 MAADR rows.
2. The second octet is MAADR2 at 0x05 — DS39662E T3-2 MAADR rows.
3. The third octet is MAADR3 at 0x02 — DS39662E T3-2 MAADR rows.
4. The fourth octet is MAADR4 at 0x03 — DS39662E T3-2 MAADR rows.
5. The fifth octet is MAADR5 at 0x00 — DS39662E T3-2 MAADR rows.
6. The last octet is MAADR6 at 0x01 — DS39662E T3-2 MAADR rows.

That the address is not stored in ascending register-address order follows from the six mappings
and is not counted. **Count: 6**

### REG-021 — MACON1 layout

1. TXPAUS at bit 3, allowing pause frame transmission — DS39662E Reg 6-1.
2. RXPAUS at bit 2, honoring received pause frames — DS39662E Reg 6-1.
3. PASSALL at bit 1, delivering control frames to the buffer — DS39662E Reg 6-1.
4. MARXEN at bit 0, MAC receive enable — DS39662E Reg 6-1.
5. Bit 4 reserved and to be kept 0 — DS39662E Reg 6-1.

**Count: 5**

### REG-022 — MACON4 layout

1. DEFER at bit 6, waiting indefinitely for the medium instead of aborting at the excessive-deferral limit — DS39662E Reg 6-3.
2. BPEN at bit 5, backoff control after collisions — DS39662E Reg 6-3.
3. NOBKOFF at bit 4, backoff control after collisions — DS39662E Reg 6-3.
4. All three bits apply to half duplex only — DS39662E Reg 6-3.
5. Bits 1:0 reserved and kept 0 [field] — DS39662E Reg 6-3.

Fact 4 is a condition on when the three bits act, not an access or width attribute, and
contradicting it would not falsify any of facts 1 to 3, so it is counted separately. **Count: 5**

### REG-023 — MAC timing and limit registers

1. MABBIPG<6:0> is the back-to-back inter-packet gap in nibble times, programmed as the desired period minus 3 in full duplex and minus 6 in half duplex — DS39662E Reg 6-4.
2. MAIPGL<6:0> and MAIPGH<6:0> together form the non-back-to-back gap [pair] — DS39662E T3-2 MAIPGL/MAIPGH rows.
3. MAMXFL is a 16-bit maximum frame length spanning MAMXFLL and MAMXFLH [pair] — DS39662E T3-2 MAMXFL rows.
4. MACLCON1<3:0> is the retransmission maximum — DS39662E T3-2 MACLCON1 row.
5. MACLCON2<5:0> is the collision window in bytes — DS39662E T3-2 MACLCON2 row.

**Count: 5**

### REG-024 — programming a DMA copy

1. EDMAST is loaded with the first source byte — DS39662E §13.1.
2. EDMAND is loaded with the last source byte — DS39662E §13.1.
3. EDMADST is loaded with the first destination byte — DS39662E §13.1.
4. ECON1.CSUMEN must be verified clear — DS39662E §13.1.
5. The copy starts on setting ECON1.DMAST — DS39662E §13.1.
6. The source pointer follows the receive FIFO wrap, from ERXND to ERXST — DS39662E §13.1.
7. The destination is linear and wraps only from 0x1FFF to 0x0000 — DS39662E §13.1.
8. On completion the hardware clears DMAST and sets EIR.DMAIF — DS39662E §13.0, §13.1.
9. Clearing DMAST cancels the operation — DS39662E §13.1.

**Count: 9**

### REG-025 — DMA programming prohibitions

1. EDMAST must not equal EDMAND: a one-byte operation overwrites the whole buffer and may never terminate — DS39662E §13.0 note 1.
2. If EDMAND cannot be reached because of receive FIFO wrapping the operation never ends — DS39662E §13.0 note 2.
3. The DMA pointers and CSUMEN must not be modified while DMAST is set — DS39662E §13.1 step 1.

**Count: 3**

### REG-026 — the DMA checksum

1. A checksum is started by setting both ECON1.CSUMEN and ECON1.DMAST with EDMAST and EDMAND bounding the data — DS39662E §13.2.
2. The result appears in EDMACSH:EDMACSL — DS39662E §13.2.
3. It is the 16-bit one's complement of the one's complement sum of the data taken as big-endian 16-bit words — DS39662E §13.2.
4. An odd-length range is padded with a trailing 0x00 — DS39662E §13.2.
5. No memory is written and the pointers are unchanged — DS39662E §13.2.

**Count: 5**

### REG-027 — DMA throughput

1. A DMA copy takes two main clock cycles per byte — DS39662E §13.1 last paragraph.
2. A DMA checksum takes one main clock cycle per byte — DS39662E §13.2 last paragraph.

The 1518-byte worked duration follows from fact 1 and is not counted. **Count: 2**

### REG-029 — EIR layout

1. PKTIF at bit 6 — DS39662E Reg 12-3.
2. DMAIF at bit 5 — DS39662E Reg 12-3.
3. LINKIF at bit 4 — DS39662E Reg 12-3.
4. TXIF at bit 3 — DS39662E Reg 12-3.
5. Bit 2 reserved — DS39662E Reg 12-3.
6. TXERIF at bit 1 — DS39662E Reg 12-3.
7. RXERIF at bit 0 — DS39662E Reg 12-3.

**Count: 7**

## INIT

### INIT-001 — the oscillator start-up window

1. After a Power-on Reset or wake from power-down an oscillator start-up timer runs for 7500 clock cycles (300 microseconds) — DS39662E §2.2.
2. During that window ETH registers and buffer memory may be accessed — DS39662E §2.2, §11.1.
3. Software must not set ECON1.TXRTS during it — DS39662E §2.2 note.
4. Software must not set ECON1.RXEN during it — DS39662E §2.2 note.
5. Software must not access any MAC, MII or PHY register during it — DS39662E §2.2 note, §6.4.

**Count: 5**

### INIT-003 — after an SPI System Reset Command

1. The PHY clock is stopped after the reset command — DS80349C issue 2.
2. ESTAT.CLKRDY is not cleared, so polling it cannot detect readiness — DS80349C issue 2.
3. Software must wait at least 1 ms after the reset command before using the device — DS80349C issue 2.

That the device may still not be ready at 300 microseconds is the reason for fact 3 and rides with
it. **Count: 3**

### INIT-005 — what a reset leaves behind

1. A System Reset (RESET pin or SPI reset command) returns all registers to their reset values apart from the exceptions ENC28J60-REG-011 and ENC28J60-REG-017 state — DS39662E §11.2, T3-2 notes 1 and 3.
2. A System Reset performs the transmit-only and receive-only resets — DS39662E §11.2.
3. Buffer memory keeps its contents through a System Reset — DS39662E §11.2.
4. Buffer memory is undefined after a Power-on Reset — DS39662E §11.1.

**Count: 4**

### INIT-007 — resetting a device that may be in power save

1. The SPI System Reset Command has no effect while ECON2.PWRSV is set — DS80349C issue 19.
2. The host must clear PWRSV with a Bit Field Clear before issuing the reset — DS80349C issue 19.
3. The host must then wait at least 300 microseconds for the regulator to stabilize — DS80349C issue 19.

The post-reset wait belongs to ENC28J60-INIT-003 and is not a fact of this unit. **Count: 3**

### INIT-010 — the reference driver's initialization order

1. Soft reset first — driver, hardware initialization routine.
2. ECON1 written to zero — driver, hardware initialization routine.
3. ECON2 written with AUTOINC and VRPS — driver, hardware initialization routine.
4. The receive buffer pointers ERXST, ERXRDPT and ERXND are programmed next [grouped set: all three, as one step] — driver, hardware initialization routine.
5. ETXST and ETXND are programmed next [grouped set: both, as one step] — driver, hardware initialization routine.
6. EREVID is read — driver, hardware initialization routine.
7. ERXFCON is written — driver, hardware initialization routine.
8. MACON1 is written — driver, hardware initialization routine.
9. MACON3 is written — driver, hardware initialization routine.
10. MACON4 is written in half duplex only — driver, hardware initialization routine.
11. MAIPG is written — driver, hardware initialization routine.
12. MABBIPG is written — driver, hardware initialization routine.
13. MAMXFL is written — driver, hardware initialization routine.
14. PHLCON is written — driver, hardware initialization routine.
15. PHCON1 is written — driver, hardware initialization routine.
16. PHCON2 is written — driver, hardware initialization routine.
17. The MAC address is programmed last in this routine — driver, the MAC-address routine called from open.
18. Interrupt enable and RXEN are not part of this sequence; the driver sets them in a later step — driver, the hardware-enable routine called from open.

That this is one valid ordering the corpus does not make mandatory records the row's class, and the
binding constraints are cross-referenced to the rows that own them; neither is counted.
**Count: 18**

### INIT-011 — MAC receive enable

1. MACON1.MARXEN must be set for the MAC to receive frames — DS39662E §6.5 step 1.
2. For full duplex with IEEE flow control TXPAUS and RXPAUS should also be set [grouped set: both bits] — DS39662E §6.5 step 1, §10.2.

**Count: 2**

### INIT-012 — MACON3 at initialization

1. MACON3 should be programmed for automatic padding to at least 60 bytes with a CRC appended — DS39662E §6.5 step 2, §5.1.7.
2. If it is not, the host must supply padding and CRC itself, because the MAC transmits undersize or CRC-less frames as given — DS39662E §5.1.6, §5.1.7.
3. FULDPX must be set for a full-duplex link and clear otherwise — DS39662E §6.5 step 2.
4. FRMLNEN may be set for length status reporting — DS39662E §6.5 step 2.

The TXCRCEN pairing belongs to ENC28J60-REG-019. **Count: 4**

### INIT-014 — MAMXFL

1. MAMXFL must be programmed with the maximum frame length to be transmitted or received — DS39662E §6.5 step 4.
2. 1518 bytes accommodates standard frames — DS39662E §6.5 step 4.
3. Frames larger than MAMXFL are rejected on receive when MACON3.HFRMEN is clear — DS39662E Reg 6-2 HFRMEN.

The transmit-side selection rule belongs to ENC28J60-TX-016. **Count: 3**

### INIT-015 — the back-to-back inter-packet gap

1. MABBIPG 0x15 is recommended in full duplex — DS39662E §6.5 step 5, Reg 6-4.
2. MABBIPG 0x12 is recommended in half duplex — DS39662E §6.5 step 5, Reg 6-4.

That both represent the IEEE minimum gap of 9.6 microseconds rides with the two values.
**Count: 2**

### INIT-016 — the non-back-to-back inter-packet gap

1. MAIPGL 0x12 is recommended — DS39662E §6.5 step 6.
2. In half duplex MAIPGH should additionally be programmed, with 0x0C recommended — DS39662E §6.5 step 7.

**Count: 2**

### INIT-017 — collision registers at initialization

1. In half duplex MACLCON1 and MACLCON2 are normally left at their reset values [grouped set: both registers] — DS39662E §6.5 step 8.
2. MACLCON2 may need increasing only for exceptionally long cabling — DS39662E §6.5 step 8.
3. In full duplex both are unused — DS39662E §9.2.

**Count: 3**

### INIT-019 — entering power save

1. Clear ECON1.RXEN — DS39662E §14.0 step 1.
2. Wait for ESTAT.RXBUSY to clear — DS39662E §14.0 step 2.
3. Wait for ECON1.TXRTS to clear — DS39662E §14.0 step 3.
4. Set ECON2.VRPS if desired — DS39662E §14.0 step 4.
5. Set ECON2.PWRSV — DS39662E §14.0 step 5.
6. With PWRSV set, all MAC, MII and PHY registers are inaccessible while ETH registers and buffer memory remain accessible and keep their state — DS39662E §14.0, paragraph after the steps.

The effect on ESTAT.CLKRDY belongs to ENC28J60-REG-011. **Count: 6**

### INIT-020 — leaving power save

1. Clear ECON2.PWRSV — DS39662E §14.0 wake-up step 1.
2. Wait at least 300 microseconds, for which polling ESTAT.CLKRDY until set is the documented way — DS39662E §14.0 wake-up step 2.
3. Set ECON1.RXEN again — DS39662E §14.0 wake-up step 3.
4. A new link takes many milliseconds to establish afterwards, so software may poll PHSTAT2.LSTAT or use the link change interrupt before transmitting — DS39662E §14.0 last paragraph.

**Count: 4**

## TX

### TX-001 — the per-packet control byte

1. Every packet to transmit must be preceded in the buffer by one per-packet control byte, which ETXST points at — DS39662E §7.1, Fig 7-1.
2. POVERRIDE at bit 0 — DS39662E Fig 7-1.
3. PCRCEN at bit 1 — DS39662E Fig 7-1.
4. PPADEN at bit 2 — DS39662E Fig 7-1.
5. PHUGEEN at bit 3 — DS39662E Fig 7-1.
6. With POVERRIDE clear the other three bits are ignored and MACON3 governs padding, CRC and huge frames — DS39662E Fig 7-1.
7. With POVERRIDE set the three bits override MACON3 for that packet — DS39662E Fig 7-1.

**Count: 7**

### TX-002 — the transmit pointers

1. ETXST must point at the per-packet control byte — DS39662E §7.1 step 1.
2. ETXND must point at the last byte of the frame data, not at the control byte and not past the data — DS39662E §7.1 step 3, Fig 7-2.
3. When transmission ends the hardware writes the transmit status vector starting at ETXND plus 1 — DS39662E §7.1, Fig 7-2.

The space that write needs belongs to ENC28J60-TX-021. **Count: 3**

### TX-003 — what the host supplies and what the MAC generates

1. The host must write the destination address, source address, type/length and payload into the transmit buffer itself — DS39662E §7.1 first paragraph and step 2.
2. The MAC generates only the preamble, the start-of-frame delimiter and, if configured, padding and CRC — DS39662E §7.1, §5.1.6.
3. The MAADR registers are not inserted as the source address — DS39662E §5.1.3.

**Count: 3**

### TX-004 — starting and completing a transmission

1. Transmission is started by setting ECON1.TXRTS — DS39662E §7.1 step 4.
2. On successful completion the hardware clears TXRTS — DS39662E §7.1 step 5, §12.1.4.
3. On successful completion the hardware writes the transmit status vector — DS39662E §7.1 completion paragraph.
4. ETXST and ETXND are left unchanged — DS39662E §7.1 completion paragraph.

**Count: 4**

### TX-006 — while TXRTS is set

1. The host must not modify the transmit-related registers other than ECON1 — DS39662E §7.1, T7-2.
2. The host must not read or write the bytes being transmitted through the SPI — DS39662E §7.1, T7-2.
3. Clearing TXRTS cancels the transmission — DS39662E §7.1, §12.1.4.

**Count: 3**

### TX-007 — after a transmit abort

1. TXRTS is cleared — DS39662E §7.1 completion paragraph.
2. ESTAT.TXABRT is set — DS39662E §12.1.3.
3. The status vector is written — DS39662E §12.1.3.
4. The MAC does not retry by itself — DS39662E §12.1.3.
5. The host should read the status vector and ESTAT.LATECOL for the cause — DS39662E §12.1.3.
6. The host should clear the clearable TXABRT and LATECOL bits so the next abort can be detected [grouped set: both bits] — DS39662E §12.1.3.

**Count: 6**

### TX-008 — the transmit status vector

1. Bits 15:0, transmitted byte count excluding collided bytes — DS39662E T7-1.
2. Bits 19:16, collision count — DS39662E T7-1.
3. Bit 20, CRC error — DS39662E T7-1.
4. Bit 21, length check error — DS39662E T7-1.
5. Bit 22, length out of range — DS39662E T7-1.
6. Bit 23, transmit done — DS39662E T7-1.
7. Bit 24, multicast — DS39662E T7-1.
8. Bit 25, broadcast — DS39662E T7-1.
9. Bit 26, packet deferred — DS39662E T7-1.
10. Bit 27, excessive defer — DS39662E T7-1.
11. Bit 28, excessive collisions — DS39662E T7-1.
12. Bit 29, late collision — DS39662E T7-1.
13. Bit 30, giant — DS39662E T7-1.
14. Bit 31, underrun, always 0 — DS39662E T7-1.
15. Bits 47:32, total bytes on the wire including collided attempts — DS39662E T7-1.
16. Bit 48, control frame — DS39662E T7-1.
17. Bit 49, pause frame — DS39662E T7-1.
18. Bit 50, backpressure applied — DS39662E T7-1.
19. Bit 51, VLAN tagged — DS39662E T7-1.
20. Bits 55:52, zero [field] — DS39662E T7-1.
21. The multi-byte fields are packed little-endian — DS39662E §7.1, the remark preceding T7-1.

The vector's seven-byte extent follows from the complete bit 0 to 55 layout and is not counted.
**Count: 21**

### TX-010 — the transmit logic reset before transmitting

1. Before transmitting, or at least after any EIR.TXERIF, software must reset the transmit logic by setting and then clearing ECON1.TXRST — DS80349C issue 12.
2. Clearing TXRST may itself set TXERIF, so the flag must be cleared after the reset, not before — DS80349C issue 12.

The half-duplex stall that makes the reset necessary is the reason for fact 1 and rides with it.
**Count: 2**

### TX-012 — link pulses read as late collisions

1. In half duplex with some link partners the PHY may read a received link pulse as a collision and, past MACLCON2 bytes, treat it as a late collision and abort without retrying — DS80349C issue 13.
2. The abort may fail to reset the transmit state machine, so TXRTS stays set and TXIF never comes — DS80349C issue 13.
3. Software must detect completion by checking both TXIF and TXERIF — DS80349C issue 13.
4. Software must clear TXRTS itself when TXIF did not occur — DS80349C issue 13.
5. Software must implement its own retransmission on a late collision — DS80349C issue 13.

**Count: 5**

### TX-014 — the transmit-only reset

1. Setting ECON1.TXRST holds the transmit logic in reset — DS39662E §11.3.
2. A packet in progress is aborted and the hardware clears TXRTS — DS39662E §11.3.
3. Clearing TXRST resumes normal operation — DS39662E §11.3.
4. Buffer management and the host interface are unaffected — DS39662E §11.3.

**Count: 4**

### TX-015 — collisions and retransmission

1. In half duplex a collision before MACLCON2 bytes have been sent causes automatic backoff and retransmission with no host involvement — DS39662E §9.1 case 1.
2. Retransmission continues until the MACLCON1 retransmission maximum is reached, after which the packet is aborted with TXABRT set — DS39662E §9.1 case 1.
3. A collision after MACLCON2 bytes, a late collision, aborts immediately with no retransmission — DS39662E §9.1 case 2.
4. In full duplex collisions cannot occur and MACLCON1 and MACLCON2 are unused — DS39662E §9.2.

**Count: 4**

### TX-016 — permission to transmit an oversized frame

1. PHUGEEN controls permission when the per-packet control byte sets POVERRIDE — DS39662E Fig 7-1.
2. Otherwise MACON3.HFRMEN controls it — DS39662E Reg 6-2 HFRMEN.
3. Transmission aborts at the MAMXFL limit when the selected control disallows huge frames — DS39662E §12.1.3 condition 5.

**Count: 3**

### TX-017 — the DMA and the transmit engine

1. If TXRTS is set while a DMA operation is running, transmission waits for the DMA to finish — DS39662E §7.1 paragraph on the DMA.
2. If DMAST is set while TXRTS is set, the DMA waits for the transmission — DS39662E §13.1.

The shared memory port is the mechanism behind both and is not counted. **Count: 2**

### TX-018 — the reference driver's transmit slot

1. The driver writes a control byte of 0x00, no per-packet override, so MACON3 decides padding and CRC for every packet — driver, the packet write helper.
2. It keeps one fixed transmit slot at the start of its transmit region — driver, the packet write helper.
3. It allows one outstanding packet at a time — driver, the transmit path that stops the queue per packet.

**Count: 3**

### TX-019 — full-duplex flow control

1. With MACON1.TXPAUS and RXPAUS set, writing 0x02 to EFLOCON makes the MAC send pause frames periodically with the EPAUS timer value — DS39662E §10.2, Reg 10-1.
2. Writing 0x03 sends one final zero-timer pause frame and turns flow control off — DS39662E §10.2, Reg 10-1.
3. EFLOCON bit 2, FULDPXS, is a read-only shadow of MACON3.FULDPX — DS39662E Reg 10-1.
4. EFLOCON bits 1:0 are FCEN [field] — DS39662E Reg 10-1.

**Count: 4**

### TX-020 — a received pause frame

1. With MACON1.RXPAUS set, a received pause frame with a non-zero timer silently delays any pending TXRTS until the timer expires — DS39662E §10.2 RXPAUS paragraph.
2. The host is not told unless it sets MACON1.PASSALL and interprets the control frames itself — DS39662E §10.2 RXPAUS paragraph.

**Count: 2**

### TX-024 — half-duplex backpressure

1. Half-duplex flow control, selected by the FCEN0 bit of EFLOCON, applies backpressure by jamming the medium with preamble — DS39662E §10.0, Reg 10-1 FCEN.
2. The data sheet does not recommend it outside a closed network — DS39662E §10.0.

**Count: 2**

## RX

### RX-001 — the buffer and the receive FIFO

1. The Ethernet buffer is 8 KB at 0x0000 to 0x1FFF — DS39662E §3.2.
2. The receive FIFO is the range from ERXST to ERXND inclusive — DS39662E §3.2.1.
3. Hardware manages it as a circular buffer that wraps from ERXND back to ERXST — DS39662E §3.2.1.
4. Hardware never writes outside that range — DS39662E §3.2.1.
5. Every byte not in that range is transmit buffer — DS39662E §3.2.2, Fig 3-2.

**Count: 5**

### RX-007 — writing ERXRDPT

1. ERXRDPT must be written low byte first and then high: the low byte is held in an internal buffer and takes effect only when ERXRDPTH is written, so the wrong order moves the pointer to an unintended value — DS39662E §7.2.4 ERXRDPTL paragraph.
2. Reads return the live register values in either order — DS39662E §6.1 last paragraph.

**Count: 2**

### RX-008 — the write boundary at ERXRDPT

1. The receive hardware writes up to but never into the byte addressed by ERXRDPT — DS39662E §3.2.1 last paragraph.
2. A packet that would reach ERXRDPT is aborted, and previously received data is preserved — DS39662E §3.2.1, §7.2.4.
3. The host must advance ERXRDPT as it consumes packets or reception stops — DS39662E §7.2.4 opening paragraph.

Fact 3 is a host obligation, not a consequence that the boundary's contradiction would falsify, so
it is counted separately; the flag reporting such an abort belongs to ENC28J60-IRQ-010.
**Count: 3**

### RX-009 — the received packet layout

1. Each received packet begins with a two-byte next-packet pointer — DS39662E §7.2.2, Fig 7-3.
2. The pointer is little-endian — DS39662E §7.2.2, Fig 7-3.
3. A four-byte receive status vector follows it, then the frame bytes from destination address through CRC — DS39662E §7.2.2, Fig 7-3.
4. Packets always begin on an even address — DS39662E §7.2.2.
5. If a frame ends on an odd address the hardware skips one pad byte before the next packet — DS39662E §7.2.2.

**Count: 5**

### RX-010 — the received byte count

1. Bits 15:0 of the receive status vector are the received byte count [field] — DS39662E T7-3.
2. The count is stored little-endian — DS39662E T7-3.
3. It counts destination address, source address, type/length, data, padding and the four CRC bytes, all of which are present in the buffer — DS39662E T7-3, §5.1.1.

**Count: 3**

### RX-011 — the receive status vector's status bits

1. Bit 16, long event or drop event — DS39662E T7-3.
2. Bit 18, carrier event seen — DS39662E T7-3.
3. Bit 20, CRC error — DS39662E T7-3.
4. Bit 21, length check error — DS39662E T7-3.
5. Bit 22, length out of range, the type field — DS39662E T7-3.
6. Bit 23, received OK: a valid CRC and no symbol errors — DS39662E T7-3.
7. Bit 24, multicast — DS39662E T7-3.
8. Bit 25, broadcast — DS39662E T7-3.
9. Bit 26, dribble nibble — DS39662E T7-3.
10. Bit 27, control frame — DS39662E T7-3.
11. Bit 28, pause control frame — DS39662E T7-3.
12. Bit 29, unknown opcode — DS39662E T7-3.
13. Bit 30, VLAN tagged — DS39662E T7-3.
14. Bit 31 is zero — DS39662E T7-3.
15. Bits 17 and 19 are reserved [grouped set: both bit positions] — DS39662E T7-3.

**Count: 15**

### RX-012 — freeing a packet with PKTDEC

1. After processing a packet the host must write 1 to ECON2.PKTDEC, which decrements EPKTCNT by one; the bit clears itself — DS39662E §7.2.4 PKTDEC paragraph, Reg 3-2.
2. Attempts to decrement below zero are ignored — DS39662E §7.2.4.

PKTDEC's self-clearing is an attribute of the write and rides with fact 1; it was counted
separately until 2026-09-20. **Count: 2**

### RX-013 — EPKTCNT saturation

1. EPKTCNT counts accepted packets and saturates at 255 — DS39662E §7.2.4 last paragraph.
2. Once it reaches 255 every new packet is aborted even if buffer space is free — DS39662E §12.1.2.
3. The host must decrement it as packets are consumed — DS39662E §7.2.4.

The flag that reports the abort belongs to ENC28J60-IRQ-010. **Count: 3**

### RX-015 — the internal write pointer and ERXWRPT

1. Writing ERXST or ERXND loads the receive hardware's internal write pointer with ERXST — DS39662E §3.2.1, §6.1 note.
2. The readable ERXWRPT registers are updated only when a packet is successfully received, so software cannot verify initialization by checking ERXWRPT against ERXST — DS39662E §6.1 note.

**Count: 2**

### RX-017 — receive buffer free space

1. With ERXWRPT greater than ERXRDPT, free space is (ERXND minus ERXST) minus (ERXWRPT minus ERXRDPT) — DS39662E §7.2.5, Ex 7-2.
2. With the two equal, free space is ERXND minus ERXST — DS39662E §7.2.5, Ex 7-2.
3. Otherwise free space is ERXRDPT minus ERXWRPT minus 1 — DS39662E §7.2.5, Ex 7-2.
4. One byte of the FIFO is always unusable — DS39662E §7.2.5.

The write-boundary reason for fact 4 belongs to ENC28J60-RX-008. **Count: 4**

### RX-018 — enabling reception

1. Reception is enabled by setting ECON1.RXEN after the FIFO pointers, the MAC and the filters are configured — DS39662E §7.2.1.
2. Once RXEN is set the duplex mode must not be modified — DS39662E §7.2.1.
3. Once RXEN is set ERXST and ERXND must not be modified [grouped set: both pointers] — DS39662E §7.2.1.
4. It is recommended to clear RXEN before changing ERXFCON or the MAC address, so that no unexpected packets are accepted — DS39662E §7.2.1.

**Count: 4**

### RX-019 — ERXFCON and filter combination

1. UCEN at bit 7 — DS39662E Reg 8-1.
2. ANDOR at bit 6 — DS39662E Reg 8-1.
3. CRCEN at bit 5 — DS39662E Reg 8-1.
4. PMEN at bit 4 — DS39662E Reg 8-1.
5. MPEN at bit 3 — DS39662E Reg 8-1.
6. HTEN at bit 2 — DS39662E Reg 8-1.
7. MCEN at bit 1 — DS39662E Reg 8-1.
8. BCEN at bit 0 — DS39662E Reg 8-1.
9. With ANDOR clear a packet is accepted if any enabled filter accepts it — DS39662E Reg 8-1, §8.0.
10. With ANDOR set a packet must pass every enabled filter — DS39662E Reg 8-1, §8.0.
11. CRCEN is applied after the other filters and discards packets with a bad CRC — DS39662E §8.0, Figs 8-1 and 8-2.
12. Writing 0 accepts every packet, which is promiscuous mode — DS39662E Reg 8-1.

**Count: 12**

### RX-020 — the filter criteria

1. The unicast filter matches the destination address exactly against the MAADR registers — DS39662E §8.1.
2. The multicast filter matches when the least significant bit of the first destination byte is set — DS39662E §8.4.
3. The broadcast filter matches FF-FF-FF-FF-FF-FF — DS39662E §8.5.
4. The hash table filter indexes the 64 EHT bits with a CRC of the destination address — DS39662E §8.6.

**Count: 4**

### RX-021 — the filter settings the reference driver uses

1. Unicast plus broadcast with CRC check, 0xA1, the reset value, for normal mode — driver, the initialization ERXFCON write.
2. The same value plus MCEN for any multicast membership — driver, the receive-mode work handler.
3. 0x00 for promiscuous mode — driver, the receive-mode work handler.
4. It never programs the hash table or pattern match filters [grouped set: both filters] — driver, the receive-mode work handler and the initialization write.

**Count: 4**

### RX-024 — short frames on receive

1. The receive hardware automatically rejects frames shorter than 18 bytes — DS39662E §5.1.6 receive paragraph.
2. Frames of 18 to 63 bytes are accepted subject to the filters — DS39662E §5.1.6 receive paragraph.
3. The host must itself discard frames shorter than 64 bytes to conform to IEEE 802.3 — DS39662E §5.1.6 receive paragraph.

**Count: 3**

### RX-025 — the reference driver's drop policy

1. It drops a received packet when the status vector's received-OK bit is clear — driver, the hardware receive function.
2. It drops a received packet when the byte count exceeds 1518, a cutoff of the driver's own and independent of MAMXFL — driver, the hardware receive function.
3. It counts CRC and length-check errors separately — driver, the hardware receive function.

**Count: 3**

### RX-026 — the reference driver's FIFO corruption recovery

1. The corruption test: the saved next-packet pointer lies beyond the driver's receive buffer end — driver, the invalid-packet-address branch.
2. Clear RXEN — driver, the invalid-packet-address branch.
3. Set and then clear ECON1.RXRST — driver, the invalid-packet-address branch.
4. Reprogram ERXST, ERXRDPT and ERXND [grouped set: all three] — driver, the invalid-packet-address branch.
5. Clear EIR.RXERIF — driver, the invalid-packet-address branch.
6. Set RXEN again — driver, the invalid-packet-address branch.

**Count: 6**

### RX-027 — the receive-only reset

1. Setting ECON1.RXRST holds the receive logic in reset — DS39662E §11.4.
2. Any packet being received is aborted — DS39662E §11.4.
3. RXEN is cleared by hardware — DS39662E §11.4.
4. Clearing RXRST returns to normal operation — DS39662E §11.4.
5. Buffer management and the host interface are unaffected — DS39662E §11.4.

**Count: 5**

### RX-033 — processing order and retention

1. Packets must be processed in the order received — DS39662E §7.2.4 right column.
2. A packet to be kept for later must be copied elsewhere, for which the DMA can be used — DS39662E §7.2.4 right column.

The single read pointer governing buffer ownership is the mechanism behind fact 1 and rides with
it. Fact 2 is a separate host obligation: a candidate that denies it has not denied in-order
processing. **Count: 2**

### RX-036 — the pattern match filter

1. It computes an IP checksum over up to 64 bytes of the incoming packet, selected by the EPMM mask bytes — DS39662E §8.2.
2. The 64-byte window starts EPMO bytes after the beginning of the destination address field — DS39662E §8.2.
3. The packet is accepted when the checksum equals EPMCS — DS39662E §8.2.

**Count: 3**

### RX-037 — how the reference driver frees a packet

1. After its per-packet acceptance test it advances ERXRDPT to the odd-adjusted next-packet pointer, whether or not it accepted the frame — driver, the hardware receive routine.
2. It saves that pointer for the next call — driver, the hardware receive routine.
3. It sets PKTDEC — driver, the hardware receive routine.

**Count: 3**

## IRQ

### IRQ-001 — EIE layout

1. INTIE at bit 7, the global enable for the INT pin — DS39662E Reg 12-2.
2. PKTIE at bit 6 — DS39662E Reg 12-2.
3. DMAIE at bit 5 — DS39662E Reg 12-2.
4. LINKIE at bit 4 — DS39662E Reg 12-2.
5. TXIE at bit 3 — DS39662E Reg 12-2.
6. Bit 2 reserved and kept 0 — DS39662E Reg 12-2.
7. TXERIE at bit 1 — DS39662E Reg 12-2.
8. RXERIE at bit 0 — DS39662E Reg 12-2.

**Count: 8**

### IRQ-002 — the INT pin

1. INT is driven low when any flag whose enable bit is set is pending and INTIE is set, and stays low until every such flag is cleared or its enable is cleared — DS39662E §12.0, Fig 12-1.
2. The pin is intended for a host that detects falling edges, and a host using a level-sensitive input must cope with the pin staying low — DS39662E §12.0.

**Count: 2**

### IRQ-003 — flags and enables

1. Except for LINKIF, each interrupt flag is set when its condition occurs regardless of the enable bits, so the flags can be polled — DS39662E §12.0 note.
2. A flag must be cleared before its interrupt is enabled, to avoid a stale assertion — DS39662E §12.0 note.

**Count: 2**

### IRQ-005 — INTIE across a handler

1. On entering the handler the host should clear EIE.INTIE, which returns the INT pin high — DS39662E §12.0.
2. Re-setting INTIE with an event pending drives the pin low again, producing a fresh falling edge — DS39662E §12.0.

**Count: 2**

### IRQ-006 — PKTIF is unreliable

1. EIR.PKTIF does not reliably report whether packets are pending, so software must read EPKTCNT to learn whether a packet is waiting, in the handler and when polling — DS80349C issue 6.
2. The INT pin itself still asserts reliably on packet arrival when PKTIE is enabled — DS80349C issue 6 note.

**Count: 2**

### IRQ-007 — how PKTIF behaves

1. PKTIF is set whenever EPKTCNT is non-zero — DS39662E §12.1.7.
2. It clears only when EPKTCNT is decremented to zero through PKTDEC: the flag is read-only, and a Bit Field Clear on it has no documented effect — DS39662E Reg 12-3 PKTIF, §12.1.7.

The read-only access and the ineffective Bit Field Clear are attributes of the clearing rule and
ride with fact 2; they were counted separately until 2026-09-20. **Count: 2**

### IRQ-008 — TXIF

1. TXIF is set whenever TXRTS goes from 1 to 0, whether by completion, abort or host cancellation — DS39662E §12.1.4.
2. It can only be cleared by the host with a Bit Field Clear, or by a reset — DS39662E §12.1.4.
3. A completion with TXABRT clear, and TXRTS not cleared by the host, means success — DS39662E §12.1.4.

**Count: 3**

### IRQ-009 — TXERIF

1. TXERIF is set on an abort from excessive collisions, the MACLCON1 limit — DS39662E §12.1.3 condition 1.
2. On an abort from a late collision, past MACLCON2 — DS39662E §12.1.3 condition 2.
3. On an abort from a collision after 64 bytes, which also sets LATECOL — DS39662E §12.1.3 condition 3.
4. On an abort from excessive deferral with DEFER clear — DS39662E §12.1.3 condition 4.
5. On an abort from a frame larger than MAMXFL without huge-frame enable — DS39662E §12.1.3 condition 5.
6. TXIF is set at the same time as TXERIF — DS39662E §12.1.3.
7. In full duplex only the oversize case can occur — DS39662E §12.1.3.
8. The flag is cleared by the host with a Bit Field Clear — DS39662E §12.1.3.

**Count: 8**

### IRQ-010 — RXERIF

1. RXERIF is set when an incoming packet is aborted because the receive buffer is out of space — DS39662E §12.1.2.
2. It is set when an incoming packet is aborted because EPKTCNT is 255 — DS39662E §12.1.2.
3. The packet is lost permanently — DS39662E §12.1.2.
4. The host should free buffer space: advance ERXRDPT low byte first and decrement EPKTCNT — DS39662E §12.1.2.
5. The host should clear the flag with a Bit Field Clear — DS39662E Reg 12-3 RXERIF.

**Count: 5**

### IRQ-011 — the link change interrupt

1. LINKIF is never set unless both PHIE.PLNKIE and PHIE.PGEIE are set [grouped set: both enables] — DS39662E §12.1.5, Reg 12-4.
2. LINKIF then shadows PHIR.PGIF — DS39662E §12.1.5.
3. LINKIF is read-only in EIR — DS39662E Reg 12-3.
4. LINKIF is cleared, together with PGIF and PLNKIF, by reading PHIR through the MII interface — DS39662E §12.1.5, Reg 12-5.
5. The interrupt reports a change and not the present state — DS39662E §12.1.5.

Where the present state is read belongs to ENC28J60-PHY-016 and ENC28J60-PHY-017. **Count: 5**

### IRQ-012 — DMAIF

1. DMAIF is set when a DMA copy or checksum completes, DMAST going 1 to 0 — DS39662E §12.1.6.
2. It is set when the host cancels the operation by clearing DMAST — DS39662E §12.1.6.
3. The host clears it with a Bit Field Clear — DS39662E §12.1.6.

**Count: 3**

### IRQ-016 — wake-on-LAN

1. The device must not be in power save — DS39662E §12.2.
2. Reception must be enabled — DS39662E §12.2.
3. ERXFCON.CRCEN and MPEN must be set [grouped set: both bits] — DS39662E §12.2.1.
4. PKTIE and INTIE must be enabled [grouped set: both enables] — DS39662E §12.2.1.
5. A received Magic Packet then increments EPKTCNT and asserts INT to wake the host — DS39662E §12.2.1.

**Count: 5**

### IRQ-018 — the reference driver's handler loop

1. It masks INTIE on entry — driver, the threaded interrupt handler.
2. It reads EIR at the top of each pass — driver, the threaded interrupt handler.
3. It handles DMAIF by clearing it only — driver, the threaded interrupt handler.
4. It handles LINKIF — driver, the threaded interrupt handler.
5. It handles TXIF without TXERIF as a completion — driver, the threaded interrupt handler.
6. It handles TXERIF as an error, with a retry — driver, the threaded interrupt handler.
7. It handles RXERIF — driver, the threaded interrupt handler.
8. It then runs the receive drain — driver, the threaded interrupt handler.
9. It repeats while any branch did work — driver, the threaded interrupt handler.
10. It re-enables INTIE at the end — driver, the threaded interrupt handler.

The drain's own steps belong to ENC28J60-IRQ-019. **Count: 10**

## PHY

### PHY-001 — how PHY registers are reached

1. PHY registers are 16 bits wide — DS39662E §3.3.
2. They are not reachable with the control register commands — DS39662E §3.3.
3. They are accessed only through the MII registers in bank 2 (MIREGADR, MIWRL/MIWRH, MIRDL/MIRDH, MICMD) and MISTAT in bank 3 — DS39662E §3.3, §3.0.

**Count: 3**

### PHY-002 — reading a PHY register

1. Write the register's address to MIREGADR — DS39662E §3.3.1 step 1.
2. Set MICMD.MIIRD, at which MISTAT.BUSY goes high — DS39662E §3.3.1 step 2.
3. Wait for the 10.24 microsecond transaction by polling MISTAT.BUSY until clear — DS39662E §3.3.1 step 3.
4. Clear MICMD.MIIRD — DS39662E §3.3.1 step 4.
5. Read MIRDL and MIRDH, in either order — DS39662E §3.3.1 step 5.

**Count: 5**

### PHY-003 — writing a PHY register

1. Write the register's address to MIREGADR — DS39662E §3.3.2 step 1.
2. Write the low data byte to MIWRL — DS39662E §3.3.2 step 2.
3. Write the high byte to MIWRH, which starts the transaction, so it must come after MIWRL — DS39662E §3.3.2 step 3.
4. MISTAT.BUSY is set and clears after 10.24 microseconds — DS39662E §3.3.2.
5. No MII scan or read should be started while BUSY is set — DS39662E §3.3.2 last paragraph.

**Count: 5**

### PHY-005 — prohibited while MISTAT.BUSY is set

1. The host must not start an MIISCAN operation — DS39662E §3.3.1 step 3.
2. The host must not start an MIIRD operation — DS39662E §3.3.1 step 3.
3. The host must not write MIWRH — DS39662E §3.3.2 last paragraph.

**Count: 3**

### PHY-006 — the implemented PHY addresses

1. PHCON1 at 0x00 — DS39662E T3-3.
2. PHSTAT1 at 0x01 — DS39662E T3-3.
3. PHID1 at 0x02 — DS39662E T3-3.
4. PHID2 at 0x03 — DS39662E T3-3.
5. PHCON2 at 0x10 — DS39662E T3-3.
6. PHSTAT2 at 0x11 — DS39662E T3-3.
7. PHIE at 0x12 — DS39662E T3-3.
8. PHIR at 0x13 — DS39662E T3-3.
9. PHLCON at 0x14 — DS39662E T3-3.
10. Writes to any other PHY address are ignored and reads return 0 — DS39662E §3.3.

**Count: 10**

### PHY-007 — MICMD and MISTAT layouts

1. MICMD.MIISCAN at bit 1 — DS39662E Reg 3-3.
2. MICMD.MIIRD at bit 0 — DS39662E Reg 3-3.
3. MISTAT.NVALID at bit 2, MIRD not yet valid — DS39662E Reg 3-4.
4. MISTAT.SCAN at bit 1 — DS39662E Reg 3-4.
5. MISTAT.BUSY at bit 0 — DS39662E Reg 3-4.
6. MISTAT bit 3 reserved — DS39662E Reg 3-4.

**Count: 6**

### PHY-008 — PHCON1 layout

1. PRST at bit 15, a software reset that clears itself — DS39662E Reg 11-1.
2. PLOOPBK at bit 14, looping transmitted data back to the MAC and disabling the twisted-pair interface — DS39662E Reg 11-1.
3. PPWRSV at bit 11, PHY power-down — DS39662E Reg 11-1.
4. PDPXMD at bit 8: 1 is full duplex, 0 is half duplex — DS39662E Reg 11-1.
5. Bits 10 and 7 reserved and kept 0 [grouped set: both bit positions] — DS39662E Reg 11-1.

**Count: 5**

### PHY-010 — no autonegotiation

1. The device does not autonegotiate — DS39662E §9.0.
2. A partner using autonegotiation detects it as half duplex — DS39662E §9.0.

That full duplex therefore works only when both ends are manually configured follows from facts 1
and 2 and is not counted; the table's "manual-configuration consequence" is fact 2, the behavior of
an autonegotiating partner. **Count: 2**

### PHY-011 — the LEDB duplex strap

1. The reset value of PHCON1.PDPXMD, and therefore of PHSTAT2.DPXSTAT, is sampled from the LEDB pin wiring at reset — DS39662E §2.6, §6.6, T3-3 note 1.
2. An LED the pin sources current into gives half duplex — DS39662E §2.6, Fig 2-7.
3. An LED the pin sinks from gives full duplex — DS39662E §2.6, Fig 2-7.
4. No LED gives an indeterminate value — DS39662E §2.6.

Whether a driver may rely on the sampled value belongs to ENC28J60-PHY-012. **Count: 4**

### PHY-013 — the half-duplex loopback default

1. In half duplex the reset default loops every transmitted packet back into the receive path, where it is written to the receive buffer unless filtered out — DS39662E §9.1 last paragraph.
2. Setting PHCON2.HDLDIS stops this — DS39662E §6.6, Reg 6-5 HDLDIS.
3. HDLDIS is ignored when PDPXMD or PLOOPBK is set — DS39662E Reg 6-5 HDLDIS.

**Count: 3**

### PHY-014 — the half-duplex loopback is unreliable

1. The half-duplex loopback mode does not reliably loop packets back — DS80349C issue 9.
2. Loopback testing should instead be done in full duplex with an external loopback cable — DS80349C issue 9.
3. PHCON2.HDLDIS should be set by the host to avoid occasional packets being looped back — DS80349C issue 9 work around.
4. HDLDIS is clear by default — DS80349C issue 9.

**Count: 4**

### PHY-015 — the full-duplex loopback is unreliable

1. The full-duplex loopback mode, PDPXMD and PLOOPBK both set, does not reliably loop packets back — DS80349C issue 10.
2. Loopback diagnostics should use an external loopback connector instead — DS80349C issue 10.
3. Enabling PLOOPBK also disables the twisted-pair driver and drops any link — DS39662E §9.2 last paragraph, Reg 11-1 PLOOPBK.

**Count: 3**

### PHY-016 — PHSTAT2 layout

1. TXSTAT at bit 13, read-only — DS39662E Reg 3-6.
2. RXSTAT at bit 12, read-only — DS39662E Reg 3-6.
3. COLSTAT at bit 11, read-only — DS39662E Reg 3-6.
4. LSTAT at bit 10, a non-latching link-up indication, read-only — DS39662E Reg 3-6.
5. DPXSTAT at bit 9, mirroring PDPXMD, read-only — DS39662E Reg 3-6.
6. PLRITY at bit 5, TPIN polarity reversed, read-only — DS39662E Reg 3-6.

The read-only access rides with each field rather than being a seventh fact; it was counted
separately until 2026-09-20, and because it now rides, it is required for each field's credit.
**Count: 6**

### PHY-017 — PHSTAT1 layout

1. PFDPX at bit 12, a capability bit that always reads 1 — DS39662E Reg 3-5.
2. PHDPX at bit 11, a capability bit that always reads 1 — DS39662E Reg 3-5.
3. LLSTAT at bit 2, latching low: clear if the link was down at any time since the last read — DS39662E Reg 3-5, §3.3.4.
4. JBSTAT at bit 1, latching high: a jabber condition occurred since the last read — DS39662E Reg 3-5, §3.3.4.

**Count: 4**

### PHY-018 — PHCON2 layout

1. FRCLNK at bit 14, forcing link up — DS39662E Reg 6-5.
2. TXDIS at bit 13, disabling the twisted-pair transmitter — DS39662E Reg 6-5.
3. JABBER at bit 10, disabling jabber correction — DS39662E Reg 6-5.
4. HDLDIS at bit 8 — DS39662E Reg 6-5.
5. Bits 12-11, 9 and 7-0 reserved and written as 0 [grouped set: all three ranges] — DS39662E Reg 6-5.

**Count: 5**

### PHY-019 — PHIE and PHIR layouts

1. PHIE.PLNKIE at bit 4, the link change enable — DS39662E Reg 12-4.
2. PHIE.PGEIE at bit 1, the PHY global enable — DS39662E Reg 12-4.
3. PHIR.PLNKIF at bit 4 — DS39662E Reg 12-5.
4. PHIR.PGIF at bit 2 — DS39662E Reg 12-5.
5. Both PHIR flags clear themselves when PHIR is read — DS39662E Reg 12-5.
6. PHIR's reserved bits read as unknown and are ignored — DS39662E Reg 12-5.

**Count: 6**

### PHY-020 — PHLCON layout

1. LACFG<3:0> at bits 11-8, configuring LEDA [field] — DS39662E Reg 2-2.
2. LBCFG<3:0> at bits 7-4, configuring LEDB [field] — DS39662E Reg 2-2.
3. LFRQ<1:0> at bits 3-2, selecting the stretch length [field] — DS39662E Reg 2-2.
4. STRCH at bit 1, enabling pulse stretching — DS39662E Reg 2-2.
5. Bits 13-12 must be written as 1 [grouped set: both bits] — DS39662E Reg 2-2.
6. Bits 15-14 and bit 0 must be written as 0 [grouped set: all three bits] — DS39662E Reg 2-2.
7. The reset value is 0011 0100 0010 001x binary, that is 0x3422 with bit 0 alone unknown — DS39662E T3-3 reset value.

**Count: 7**

### PHY-022 — the 1110 LED code

1. The PHLCON code 1110, duplex status and collision activity on one LED, shows only the duplex status — DS80349C issue 11.
2. To display collisions, program 0011 in half duplex — DS80349C issue 11.
3. To display duplex, program 0101 in full duplex — DS80349C issue 11.

**Count: 3**

### PHY-023 — LED polarity misdetection

1. With some LEDs the polarity auto-detection at reset misdetects the connection, so the LED appears inverted — DS80349C issue 16.
2. If LEDB is misdetected, PHCON1.PDPXMD also resets to the wrong state — DS80349C issue 16.
3. The vendor workaround is a 1 k to 100 k resistor in parallel with the LED — DS80349C issue 16.

**Count: 3**

### PHY-024 — receive polarity correction does not work

1. The automatic receive polarity detection and correction on TPIN+/TPIN- does not work as described, so reversed wiring gives poor or no reception with some partners — DS80349C issue 7.
2. The published workaround is to wire TPIN+ and TPIN- correctly — DS80349C issue 7.

**Count: 2**

### PHY-025 — the PHY reset

1. Setting PHCON1.PRST resets the PHY and all its registers to defaults — DS39662E §11.5.
2. The bit clears itself after a delay, and the host must poll PRST until clear before using the PHY — DS39662E §11.5.

**Count: 2**

### PHY-026 — the PHY identifier registers

1. PHID1 reads 0x0083 — DS39662E T3-3 PHID1 row.
2. PHID2 reads 0x1400 — DS39662E T3-3 PHID2 row.

Both values are read-only and constant, which rides with them, and their encoding of the Microchip
OUI with part number 0 and revision 0 follows from them; the read-only constancy was counted as a
third fact until 2026-09-20. **Count: 2**

### PHY-027 — how the reference driver reports the link

1. It reads PHSTAT2 on every link change interrupt and at open to report link state — driver, the link status check function.
2. It reports the duplex as whatever DPXSTAT says rather than what it configured — driver, the link status check function.

**Count: 2**

### PHY-028 — changing duplex mode

1. There must be no transmit in progress, TXRTS clear — DS39662E §9.1, §9.2.
2. Reception must be disabled, RXEN clear and RXBUSY clear — DS39662E §9.1, §9.2.

The indeterminate state the transition passes through is the reason for both and rides with them.
**Count: 2**

### PHY-029 — scanning a PHY register

1. MICMD.MIISCAN starts continuous reads of the register at MIREGADR into MIRD every 10.24 microseconds — DS39662E §3.3.3.
2. MISTAT.NVALID indicates the first result is not yet in — DS39662E §3.3.3.
3. MIRDL and MIRDH are not guaranteed to come from the same sample — DS39662E §3.3.3.
4. The scan is stopped by clearing MIISCAN and polling BUSY clear — DS39662E §3.3.3.

**Count: 4**

### PHY-031 — MIREGADR

1. MIREGADR<4:0> carries the PHY register address and bits 7-5 are unimplemented [field] — DS39662E T3-2 MIREGADR row, §3.3.
2. The implemented bits reset to 0 — DS39662E T3-2 reset column.

In an eight-bit register the implemented five-bit field and the unimplemented upper three bits are
one mask stated from both ends, so they are one fact; that thirty-two PHY addresses are addressable
follows from it. They were counted as two facts until 2026-09-20. **Count: 2**

### PHY-032 — the common LED configuration codes

1. Code 0100, link status — DS39662E Reg 2-2 LACFG/LBCFG descriptions.
2. Code 0101, duplex status — DS39662E Reg 2-2 LACFG/LBCFG descriptions.
3. Code 0111, transmit and receive activity — DS39662E Reg 2-2 LACFG/LBCFG descriptions.
4. Code 0011, collision activity — DS39662E Reg 2-2 LACFG/LBCFG descriptions.
5. Code 1000, on — DS39662E Reg 2-2 LACFG/LBCFG descriptions.
6. Code 1001, off — DS39662E Reg 2-2 LACFG/LBCFG descriptions.

That LACFG and LBCFG select a function from a code table is the frame for the six mappings and not
a seventh fact; it was counted as one until 2026-09-20. The fields' own bit positions belong to
ENC28J60-PHY-020. **Count: 6**

## SPI

### SPI-001 — the SPI mode

1. The host SPI must use mode 0,0 only, with SCK idle low; other clock polarities or phases are not supported — DS39662E §4.1.
2. The device samples SI on the rising edge of SCK — DS39662E §4.1, Figs 4-1 and 4-2.
3. The device drives SO on the falling edge of SCK — DS39662E §4.1, Figs 4-1 and 4-2.

**Count: 3**

### SPI-002 — CS framing

1. CS must be held low for the whole of one instruction, including any streamed data bytes, and raised to terminate it — DS39662E §4.1.
2. Each instruction starts with CS falling — DS39662E §4.1.
3. If CS rises before all eight bits of a data byte have been clocked in, that byte's write, bit-field-set or bit-field-clear is abandoned — DS39662E §4.2.3, §4.2.5, §4.2.6.

**Count: 3**

### SPI-004 — Write Control Register

1. Opcode 010 — DS39662E T4-1, §4.2.3.
2. The 5-bit register address as the argument — DS39662E §4.2.3.
3. One data byte follows, sampled on the rising SCK edges — DS39662E §4.2.3, Fig 4-5.

**Count: 3**

### SPI-005 — the buffer memory commands

1. Read Buffer Memory uses opcode 001 — DS39662E T4-1, §4.2.2.
2. Write Buffer Memory uses opcode 011 — DS39662E T4-1, §4.2.4.
3. Each is followed by the fixed 5-bit constant 0x1A, making the complete command bytes 0x3A and 0x7A — DS39662E T4-1.
4. The Ethernet buffer can be reached only through these two commands — DS39662E §3.0.

**Count: 4**

### SPI-006 — the bit field commands

1. Bit Field Set uses opcode 100 and ORs the supplied data byte into the addressed register — DS39662E §4.2.5, T4-1.
2. Bit Field Clear uses opcode 101 and ANDs the inverse of the data byte into it — DS39662E §4.2.6, T4-1.
3. Each takes the 5-bit register address as its argument and one data byte — DS39662E §4.2.5, §4.2.6.

**Count: 3**

### SPI-007 — where the bit field commands may be used

1. Bit Field Set and Bit Field Clear work only on ETH registers, and must not be used on MAC registers, MII registers, PHY registers or buffer memory — DS39662E §4.2.5, §4.2.6.
2. Changing bits in those requires a full read-modify-write through the control register commands — DS39662E §4.2.5.

**Count: 2**

### SPI-009 — the dummy byte on MAC and MII reads

1. A Read Control Register of a MAC or MII register returns a dummy byte before the register value, so the host must clock 16 bits after the command byte and keep the second — DS39662E §4.2.1, Fig 4-4.
2. A read of an ETH register returns the value in the first byte after the command — DS39662E §4.2.1, Fig 4-3.

**Count: 2**

### SPI-010 — banking

1. Control registers live in four banks of 32 addresses, selected by ECON1.BSEL<1:0> — DS39662E §3.1, Fig 3-1, Reg 3-1.
2. The 5-bit address in a command names a register within the currently selected bank, so the host must set the bank before touching a banked register — DS39662E §3.1, T3-1.

**Count: 2**

### SPI-013 — streaming a packet out of the receive FIFO

1. With ECON2.AUTOINC set, each byte returned by Read Buffer Memory advances ERDPT by one — DS39662E §4.2.2.
2. When ERDPT equals ERXND the next address is ERXST, so a packet can be streamed out in one command without the host handling the wrap — DS39662E §7.2.3.
3. Continuing to clock SCK with CS low returns successive bytes — DS39662E §4.2.2.

**Count: 3**

### SPI-014 — streaming into the buffer

1. Any number of data bytes may be streamed after the Write Buffer Memory command — DS39662E §4.2.4, Fig 4-6.
2. Each byte is stored at EWRPT — DS39662E §4.2.4.
3. EWRPT auto-increments after every byte when ECON2.AUTOINC is set — DS39662E §4.2.4.
4. EWRPT wraps from 0x1FFF to 0x0000 only — DS39662E §3.2.3.

**Count: 4**

### SPI-016 — the CS hold time

1. At least 10 ns after the last SCK edge for ETH registers and buffer memory — DS39662E T16-6 parameter 2.
2. At least 210 ns for MAC and MII registers — DS39662E T16-6 parameter 2.

**Count: 2**

### SPI-017 — the slow asynchronous SPI clock erratum

1. Clocking SPI at 8 MHz or faster is one remedy for the unreliable MAC-register access the erratum describes on the revisions it marks, which occurs when the SPI clock is below 8 MHz and asynchronous to the device's 25 MHz clock — DS80349C issue 1.
2. Deriving the SPI clock synchronously from the same 25 MHz source, or from CLKOUT, at an integer division (12.5, 8.333, 6.25, 5 MHz and so on) is the other remedy for that same condition — DS80349C issue 1.

Each remedy carries the operating condition it remedies: a candidate that recommends a clock
arrangement without the erratum's condition has not stated either fact fully. **Count: 2**

### SPI-018 — bit order

1. A Read Control Register command clocks the register contents out most significant bit first — DS39662E §4.2.1, Fig 4-3.
2. Data bytes for the write and bit-field commands are sent most significant bit first — DS39662E §4.2.3, Fig 4-5.

**Count: 2**

### SPI-019 — the instruction byte

1. Every SPI instruction begins with one byte made of a 3-bit opcode in the top three bits and a 5-bit argument in the low five — DS39662E §4.2, T4-1.
2. The argument is a control register address for the register instructions and a fixed constant for the buffer and reset instructions — DS39662E §4.2, T4-1.
3. Seven instructions exist and no others — DS39662E T4-1.

**Count: 3**

### SPI-020 — Read Control Register

1. Opcode 000 — DS39662E §4.2.1, Fig 4-3.
2. The 5-bit register address follows — DS39662E §4.2.1.
3. The addressed register's contents are returned on SO — DS39662E §4.2.1.

**Count: 3**

### SPI-022 — how the reference driver moves 16-bit registers

1. It issues a 16-bit pointer register write as two separate one-byte Write Control Register instructions, low byte then high — driver, the word write register helper.
2. It issues a 16-bit read as two separate reads, low then high — driver, the word read register helper.

**Count: 2**

## ELEC

### ELEC-001 — the clock input

1. The clock input must be exactly 25 MHz with a tolerance of 50 ppm — DS39662E T16-2.
2. An external clock must have a duty cycle between 40 and 60 percent — DS39662E T16-2.
3. An external clock must swing to 3.3 V levels — DS39662E §2.1, Fig 2-2.

**Count: 3**

### ELEC-002 — SPI timing beyond the clock rate

1. CS setup at least 50 ns before the first clock — DS39662E T16-6 parameter 1.
2. CS disable at least 50 ns between commands — DS39662E T16-6 parameter 3.
3. Data setup 10 ns — DS39662E T16-6 parameter 4.
4. Data hold 10 ns — DS39662E T16-6 parameter 5.
5. SO valid within 10 ns of the falling SCK edge, at a 30 pF load — DS39662E T16-6 parameter 6.
6. SO disabled within 10 ns of CS rising, at a 30 pF load — DS39662E T16-6 parameter 7.

**Count: 6**

### ELEC-003 — the RESET pin

1. The pin must be held low for at least 400 ns, and shorter pulses are filtered out — DS39662E T16-3.
2. The pin must be high for at least 2 microseconds between reset events — DS39662E T16-3.
3. Internal resets, including the SPI reset command, never drive the pin — DS39662E §11.2, T1-1 note 4.

**Count: 3**

### ELEC-004 — the supply

1. VDD must rise at 0.05 V/ms or faster for the internal Power-on Reset, oscillator start-up timer and CLKOUT to reset properly — DS39662E §16.1 D003, §11.1.
2. Operating VDD is 3.10 to 3.60 V — DS39662E §16.1 D001.

**Count: 2**

### ELEC-005 — I/O levels

1. The SPI inputs CS, SCK, SI and the RESET pin are 5 V tolerant — DS39662E §2.5, T1-1 notes 3 and 4.
2. SO and INT are 3.3 V CMOS outputs, so a 5 V host needs a unidirectional level translator on those two signals — DS39662E §2.5, §16.1 D004 to D007.
3. CS and RESET have internal weak pull-ups of 74 k to 173 k ohm — DS39662E §16.1 RPU.

**Count: 3**

### ELEC-007 — the RBIAS resistor

1. 2.7 k ohm 1 percent for revisions B1 and B4 — DS80349C issue 8.
2. 2.32 k ohm 1 percent, the data sheet value, for revisions B5 and B7 — DS80349C issue 8; DS39662E §2.4.

That a wrong value makes the transmit waveform violate IEEE 802.3 is the consequence both facts
serve and is not counted. **Count: 2**

### ELEC-008 — CLKOUT behavior

1. CLKOUT is held low from power-up until the oscillator start-up timer expires after a Power-on Reset — DS39662E §2.3.
2. It then starts at the frequency ECOCON selects — DS39662E §2.3.
3. When the prescaler is changed, a gap of two to eight OSC1 periods with no clock pulses occurs — DS39662E §2.3, Fig 2-3.
4. No pulse shorter than the configured period is produced — DS39662E §2.3.

**Count: 4**

## ERR

### ERR-001 — the DMA checksum aborts a packet being received

1. Running the DMA in checksum mode, CSUMEN and DMAST set, at any moment while a packet is being received with RXBUSY set, aborts that packet permanently and sets RXERIF and BUFER — DS80349C issue 17.
2. The vendor's instruction is not to use the DMA module for checksum calculations and to compute checksums in software instead — DS80349C issue 17.
3. The DMA copy mode, CSUMEN clear, is unaffected — DS80349C issue 17.

**Count: 3**
