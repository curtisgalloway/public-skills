<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# L02c recall measurement — e1000 spec revision 3

## Terms

- **Recall** — the share of the blind requirement list that the spec states: `covered / active`,
  and a looser `(covered + partial) / active`.
- **Blind requirement list** — [`requirements.yaml`](requirements.yaml), written from the Intel
  manual in unit L02a before the spec existed. **Active** rows count; a **withdrawn** row (here
  one duplicate) does not.
- **Critical / important** — the row's weight, set when the list was written.
- **SDM** — the Intel 8254x Software Developer's Manual, revision 4.0.
- **§** references in the "spec location" column point into the spec, which is kept in a private
  run store; paths such as `recall/…` and `docs/…` below are relative to that run, not to this
  repository.

See the [glossary](../../../../GLOSSARY.md) and the [L02c evidence](../../evidence/L02c.md).

## Measurement

- Requirement list: `recall/requirements.yaml`, SHA-256
  `3e016844af0006786c4ba2ee1da5380ad6d64770d1930f6c8308c67c2a5290a4` (checked before measuring;
  it matches the brief's `3e016844…90a4`). 67 rows: 66 active, 1 withdrawn (E1000-EEPROM-003,
  not scored).
- Spec measured: `docs/e1000-spec.md` (1530 lines, not edited).
- Manual consulted only for E1000-INIT-005 (SDM §14.4–14.5 text).
- Rule: credit only for what the spec says. A careful implementer's inference earns nothing.

| id | weight | verdict | spec location | note |
| --- | --- | --- | --- | --- |
| E1000-PCI-001 | critical | covered | §2 table "PCI device IDs (82540EM) 0x100E, 0x1015"; §10.2 bind rule | Both IDs, vendor 0x8086. |
| E1000-PCI-002 | critical | partial | §4.0 "memory-mapped through BAR0 (plus BAR1 as the upper half when BAR0 is a 64-bit BAR) … 128 KB … non-prefetchable"; BAR32 bullet; §10.3 probe step 3 | States 128 KB, non-prefetchable, BAR32-dependent 32/64-bit forms with BAR1 as the upper half. Missing: the type field (bits 2:1, 10b = 64-bit) as the way to tell the forms apart, and an instruction to read it. Config offsets 10h/14h appear only as the names BAR0/BAR1. |
| E1000-PCI-003 | critical | covered | §5.1 P1 "Enable the PCI function (memory decoding…)" citing Command bit 1; order note "memory decoding (P1) must be on before any register access" | The initial value 0b is not stated, but the rule to set bit 1 before any access is. |
| E1000-PCI-004 | critical | covered | §5.1 P3 "Set PCI Command bit 2 (Bus Master) so the device can DMA descriptors and buffers" | |
| E1000-PCI-005 | critical | covered | §8.2 "64-bit addresses … Program the high register (RDBAH/TDBAH) even when it is 0"; §4.4/§4.5 RDBAH/TDBAH Init X | |
| E1000-REG-001 | critical | covered | §4.0 "Every register is 32 bits wide and must be accessed as an aligned 32-bit dword. Partial writes are ignored" | |
| E1000-INIT-001 | critical | covered | §4.1 CTRL bit 26 RST "self-clearing … Wait approximately 1 µs"; §5.2 R5–R6 "wait at least 1 µs … then poll until CTRL.RST reads 0" | |
| E1000-INIT-002 | critical | covered | §5.2 "Not reset: RAL/RAH (except RAH.AV bits, which are cleared) … program all of them"; §4.6 rules; §5.6 X1 AV = 1; G-8; §5.10 "every open after a close runs the full §5.2–5.8 sequence" | |
| E1000-INIT-003 | critical | covered | §4.1 CTRL bit 31 PHY_RST "Hardware reset to the internal PHY: set, wait … clear"; §5.4 G1 clears PHY_RST | |
| E1000-INIT-004 | critical | covered | §4.1 CTRL bit 11 FRCSPD Init **1b** "software must clear it"; §5.4 G1 clears FRCSPD and ASDE; G-1 | Prescribed action matches the row. One side statement differs: the SPEED row says SPEED is "used only when FRCSPD = 1 and ASDE = 0", which follows the manual's SPEED field text; the row holds that FRCSPD forces speed whatever ASDE says. The spec never relies on ASDE, so this does not change what gets built. |
| E1000-INIT-005 | critical | partial | §5.6 X12 "Write RCTL last, after the ring is ready" and order paragraph (RX, stated as required); §5.7 T3 before T7 (TDH before TCTL.EN, required); §5.7 order paragraph "writing it last … is this spec's choice … order not known to be required" | RX half is covered. On TX the spec requires only TDH before TCTL.EN. It still writes TCTL last, but it says base, length and tail before EN is not known to be required. The manual's §14.5 text supports the spec: it lists TCTL.EN before TIPG and states no enable-last rule for transmit. That makes the row's TX half an overstatement of §14.5, so this is `partial`, not `contradicts`. |
| E1000-INIT-006 | critical | covered | §5.10 D2–D4 (RCTL.EN = 0, TCTL.EN = 0, IMC = 0xffffffff), D7 global reset via §5.2 R5–R9 (includes the 1 µs wait), D8 free; "D7 before D8 is required" | |
| E1000-INIT-007 | critical | covered | §5.2 "Not reset: … RDBAL/RDBAH, TDBAL/TDBAH … program all of them"; §5.6 X6; §5.7 T2; §8.2; G-8 | |
| E1000-INIT-008 | critical | covered | §4.1 CTRL bit 7 ILOS "must be 0 with the internal PHY"; §5.4 G1 clears ILOS | |
| E1000-EEPROM-001 | critical | covered | §4.1 EERD table (82540EM layout, START bit 0, ADDR 15:8); §5.3 E2 "write EERD = (A << 8) \| START" | |
| E1000-EEPROM-002 | critical | covered | §4.1 EERD table DONE bit 4, DATA 31:16; §5.3 E2 "poll EERD until DONE (bit 4) = 1; the word is EERD bits 31:16" | |
| E1000-EEPROM-003 | critical | withdrawn | — | Not scored. |
| E1000-EEPROM-004 | critical | covered | §5.3 E4 "words 0, 1, 2 … for address 12-34-56-78-90-AB, word 0 = 0x3412, word 1 = 0x7856, word 2 = 0xAB90"; G-14 | |
| E1000-PHY-001 | critical | covered | §4.1 MDIC table (DATA 15:0, REGADD 20:16, PHYADD 25:21, OP 27:26 01/10, R 28, I 29, E 30) | |
| E1000-PHY-002 | critical | covered | §2 table "Internal PHY management address 1"; §4.1 MDIC PHYADD; §9.1 "Only PHY address 1 responds" | |
| E1000-PHY-003 | critical | covered | §4.1 MDIC R "software writes it 0 with the command"; §9.1 read steps 2–4, write steps 2–3; MDAC alternative noted | |
| E1000-PHY-004 | important | covered | §4.8 reg 1 "2 Link Status, latched-low … read twice (or read PSSTAT bit 10)"; §5.9 closing note; G-15 | |
| E1000-PHY-005 | critical | covered | §4.1 CTRL bit 6 SLU Init "0 (EE)", "Must be 1 for the MAC to recognize the internal PHY's link signal"; §5.4 G1 and ordering note; G-2 | |
| E1000-PHY-006 | critical | covered | §4.1 STATUS table (FD bit 0, LU bit 1, SPEED 7:6 00/01/10 or 11); §5.9 L1 | |
| E1000-PHY-007 | important | covered | §9.1 read step 1 "make sure E (bit 30) is 0 before issuing the command"; step 4 "If E = 1 → error" | |
| E1000-RX-001 | critical | covered | §6.1 table (offsets 0/8/10/12/13/14, sizes 8/2/2/1/1/2) | |
| E1000-RX-002 | critical | covered | §4.4 RDBAL "31:4 address, 3:0 ignored … 16-byte aligned"; §8.3 | |
| E1000-RX-003 | critical | covered | §4.4 RDLEN "Ring size in bytes, a multiple of 128 (so descriptor count is a multiple of 8)"; §8.3 | |
| E1000-RX-004 | critical | covered | §6.3 "Head/tail: 16-bit descriptor indices (not byte offsets); byte address = base + index × 16" | |
| E1000-RX-005 | critical | covered | §4.4 RDT "one beyond the last descriptor hardware may fill"; §6.1 Ownership "hardware owns every descriptor from RDH up to but not including RDT"; §6.3 "When the receive head reaches the tail … hardware stops storing packets" | |
| E1000-RX-006 | critical | covered | §5.6 X8 "RDT = N − 1 … keep one slot empty"; §6.3 "Keep at least one slot unused … Same rule on RX" | |
| E1000-RX-007 | critical | partial | §8.4 ordering rule 2 "Read the status byte (DD) first"; §6.1 Ownership ("scans memory for completion") | DD-in-memory detection appears as an ordering rule and in the status-clearing note. For receive the spec never says not to find completions by reading RDH, and never says the manual calls an RDH read unreliable. It says that only for transmit (§6.2 citing §13.4.39). |
| E1000-RX-008 | critical | covered | §6.1 status paragraph "For multi-descriptor packets, status and errors are valid only in the EOP descriptor; in non-EOP descriptors only address, length and DD are valid"; errors "valid only when DD and EOP are both set"; §6.4 "RX buffer fit" | |
| E1000-RX-009 | critical | covered | §6.1 Length "including the CRC unless RCTL.SECRC = 1"; §4.4 RCTL SECRC bit 26; §5.6 SECRC paragraph | |
| E1000-RX-010 | critical | covered | §4.4 RCTL BSIZE 17:16 / BSEX 25 (2048/1024/512/256); §5.6 X5 "The buffer must really be 2048 bytes: hardware may write up to BSIZE bytes"; G-4 | |
| E1000-RX-011 | critical | covered | §4.6 RAL/RAH table (AS 00, AV bit 31) and "Address byte order" RAL = b1 \| b2<<8…; §5.6 X1 | |
| E1000-RX-012 | critical | covered | §4.4 RCTL bit 15 BAM Init 0, "1 in scope"; §5.6 X12 | |
| E1000-RX-013 | critical | covered | §6.1 Ownership "Software should clear the status byte before handing a descriptor back if it scans memory for completion"; §5.6 X5 zero status | |
| E1000-RX-014 | critical | covered | §4.4 RCTL bit 1 EN "the receiver must be reset (device reset) before it is re-enabled, because disabling does not reinitialize the FIFO packet-delimiting logic"; §5.10 rule; G-3 | |
| E1000-RX-015 | critical | covered | §4.4 RDH "Software writes it only after a reset and before RCTL.EN = 1"; §6.3; §5.6 order paragraph | The reason (on-chip descriptor state) is not given; the rule is. |
| E1000-TX-001 | critical | covered | §6.2 table (address 0–7, length 8–9, CSO 10, CMD 11, STA bits 3:0 of 12, CSS 13, special 14–15) | |
| E1000-TX-002 | critical | covered | §4.5 TDBAL "31:4 address, 3:0 read 0 … 16-byte aligned"; §8.3 | |
| E1000-TX-003 | critical | covered | §5.7 T3 "TDH = 0, TDT = 0"; §4.5 TDH "software writes only after reset, before TCTL.EN"; §6.3 | |
| E1000-TX-004 | critical | covered | §4.5 TDT "one beyond the last descriptor hardware may process"; §6.2 Ownership "hardware processes descriptors from TDH up to but not including TDT; head = tail means the queue is empty"; §10.3 ndo_start_xmit "fill one descriptor … write TDT" | |
| E1000-TX-005 | critical | covered | §8.4 "Ordering rule 1 (publish before doorbell)" including the §3.4.1 cache-coherency quote; "on-chip descriptor caches … prefetch aggressively" | |
| E1000-TX-006 | critical | covered | §6.2 CMD bit 0 EOP; Rules "VLE, IFCS and IC are interpreted only in the EOP descriptor"; recommended CMD = EOP \| IFCS \| RS | |
| E1000-TX-007 | critical | covered | §6.2 CMD bit 1 IFCS "insert FCS/CRC; qualified by EOP"; recommended CMD 0x0B | |
| E1000-TX-008 | critical | covered | §6.2 Rules "Hardware sets DD only for descriptors with RS set"; CMD bit 3 RS | |
| E1000-TX-009 | critical | covered | §6.2 Ownership "detect that through DD in memory, not by reading TDH ('… is not reliable', §13.4.39 …)" | |
| E1000-TX-010 | critical | covered | §4.5 TCTL bit 3 PSP Init 0 "1 in scope"; §5.7 T7; §6.4 software padding to 60; G-17 | Relies on both PSP and a software pad, which the row's note accepts. |
| E1000-TX-011 | critical | covered | §4.5 TCTL bit 1 EN Init 0; §5.7 T7 sets EN | |
| E1000-TX-012 | critical | covered | §4.5 TIPG Init X "undefined at power-on … always program it"; TIPG values IPGT = 10; §5.7 T4 0x0060200A | |
| E1000-TX-013 | critical | covered | §4.5 TDLEN "Ring size in bytes, multiple of 128"; §8.3 | |
| E1000-TX-014 | critical | covered | §4.5 TCTL COLD 21:12 Init 0 "0x40 for full duplex and for 10/100 half duplex; 0x200 for gigabit half duplex"; §5.7 T7 | |
| E1000-TX-015 | critical | covered | §6.2 heading "(TDESC.DEXT = 0)"; CMD "bit 5 DEXT (must be 0 for legacy)" | What DEXT = 1 selects is not described; the requirement (0 for legacy) is stated. |
| E1000-TX-016 | critical | covered | §6.2 Ownership "Software must not modify a descriptor until the head has passed it — detect that through DD" | |
| E1000-TX-017 | critical | covered | §6.3 "if software filled every slot, the new tail would equal the head and the ring would look empty. Keep at least one slot unused" | |
| E1000-IRQ-001 | critical | covered | §4.3 ICR "All bits clear on read … Writing 1 to a bit also clears it; writing 0 has no effect" | |
| E1000-IRQ-002 | critical | covered | §4.3 "asserted … only while some bit is 1 in both ICR and the mask. The cause bit latches even while masked"; §7.2 | |
| E1000-IRQ-003 | critical | covered | §4.3 IMS "Writing 1 enables … writing 0 has no effect. Reading returns the current mask" | |
| E1000-IRQ-004 | critical | covered | §4.3 IMC "W … Writing 1 disables"; IMS "writing 0 has no effect"; §7.2 "Mask = write 1s to IMC" | |
| E1000-IRQ-005 | critical | covered | §4.3 bit-layout table "common to all four" (TXDW 0, TXQE 1, LSC 2, RXDMT0 4, RXO 6, RXT0 7) | |
| E1000-IRQ-006 | critical | covered | §4.3 LSC "Link status changed (up→down or down→up)"; §5.9 L1 "Read STATUS. LU (bit 1) = link state" on each LSC | |
| E1000-IRQ-007 | important | covered | §4.3 ITR "bits 15:0 INTERVAL … units of 256 ns; 0 disables throttling (reset value 0)" | |
| E1000-STAT-001 | important | covered | §4.7 "All statistics registers reset when read"; G-10 "Accumulate periodically"; §10.3 periodic accumulator | |
| E1000-STAT-002 | important | covered | §4.7 "64-bit counters … reset when their high register is read — read low, then high"; G-10 | |
| E1000-STAT-003 | important | covered | §4.7 table MPC 0x04010, RNBC 0x040A0; §6.3 "RX descriptor exhaustion and overrun recovery" | |

## Totals

| Scope | Active | covered | partial | missing | contradicts |
| --- | --- | --- | --- | --- | --- |
| All active rows | 66 | 63 | 3 | 0 | 0 |
| Critical rows | 60 | 57 | 3 | 0 | 0 |
| Important rows | 6 | 6 | 0 | 0 | 0 |

## Recall

| Scope | covered / active | (covered + partial) / active |
| --- | --- | --- |
| All active rows | 63 / 66 = 95.5 % | 66 / 66 = 100.0 % |
| Critical rows | 57 / 60 = 95.0 % | 60 / 60 = 100.0 % |

## Non-covered critical rows

- **E1000-PCI-002** (partial): no mention of the BAR type field (bits 2:1, 10b) or of reading it
  to tell the 32-bit and 64-bit BAR forms apart.
- **E1000-INIT-005** (partial): for transmit, only TDH before TCTL.EN is stated as required. The
  spec calls base, length and tail before EN "not known to be required", although its sequence
  does write them first. The manual's §14.5 supports the spec on this point.
- **E1000-RX-007** (partial): for receive, completion by DD appears only as an ordering rule. The
  spec never says not to use RDH reads or that the manual calls them unreliable (it says so only
  for TDH).
