<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# ENC28J60 gold ledger: scoring policy

Version: enc28j60-1.4
Adopted: 2026-09-20 (superseding `enc28j60-1.3` of the same day; see "Version history")

This policy is read with `SCORING-FACTS.md`, which lists the credit-bearing facts of every
composite scoring unit and is frozen with it.

`LEDGER-FORMAT.md` says that whether `observed-software-behavior` and `inference` rows count
toward recall is a per-run decision, and that the decision is **versioned and named in the freeze
lock before any candidate is generated**. This file is that named policy for the ENC28J60 pilot,
adopted by the adjudicator as group A4 answer (a).

## Terms

- **Denominator** — the set of ledger rows a recall percentage is computed over. Frozen before any
  candidate exists, and the candidate cannot influence it.
- **Recall** — the fraction of the denominator a candidate covers.
- **Precision** — the fraction of the candidate's own claims that are not errors. Its denominator
  is the candidate's claims, not the ledger's rows.
- **Class** — what kind of claim a row is: `documented-hardware-requirement`,
  `observed-software-behavior`, `inference`, `implementation-choice`, `unresolved-conflict`.
- **Weight** — `critical` (a driver that misses it does not work, or corrupts data), `important`
  (degraded or fragile), `minor` (completeness). Recall is reported per weight.
- **Claim** — one independently falsifiable proposition in the candidate, as segmented below.

## The operating envelope the weights assume

`LEDGER-FORMAT.md` weighs a row's consequence **adjusted for necessity**, and `critical` means a
working driver cannot avoid the requirement. "Cannot avoid" is only meaningful against a stated
idea of what the driver is for, so this is that statement, and every `critical` weight in the
ledger is to be read against it:

> The envelope is a driver that brings up an ordinary Ethernet interface. It receives frames
> addressed to its own unicast address and frames addressed to broadcast, **using the device's own
> unicast filter programmed with the interface's address**; it transmits; it interoperates with a
> link partner in either duplex; and it **suppresses the internal half-duplex loopback** so that
> its own transmissions are not returned to it. Receiving promiscuously and filtering in software
> is outside the envelope, and so is leaving the loopback enabled and discarding the echoes.

The adjudicator chose that envelope on 2026-09-20, before the two weights below were re-examined
against it, rather than after. A requirement a driver can avoid **only by operating outside the
envelope** is still `critical`.

The two weights it decides, and the honest form of each argument:

- **`INIT-024`**, programming the MAC address. An earlier draft of this section argued that a
  promiscuous driver "never accepts its own unicast address", which is false: a promiscuous
  receiver accepts everything, including frames addressed to it. So promiscuous operation is a
  real way to run without the MAADR registers, and the weight does not rest on denying that. It
  rests on the envelope excluding it. The envelope names the device's unicast filter because that
  is what the part is for and what the reference driver does; a spec that omits the requirement
  leaves an implementer unable to build the driver the benchmark is about.
- **`PHY-018`**, the PHCON2 layout, which carries HDLDIS. The corpus does not establish that
  leaving the internal half-duplex loopback enabled necessarily breaks a driver. DS39662E section
  9.1 says looped frames are still subject to receive filtering, and DS80349C issue 9 describes
  the loopback as unreliable and recommends disabling it to avoid occasionally returned packets.
  The weight therefore rests on the envelope's suppression clause, not on a claim that every
  transmitted frame comes back. The other fields in PHCON2 are not necessary in their own right;
  they are scored with it because the row is one register definition, which the composite rule
  already accounts for.

Neither argument is a claim about Ethernet drivers in general. Both are claims about the driver
this benchmark is written to measure, which is what "cannot avoid" has to mean to be checkable.

The envelope bounds the necessity argument only. It is not a scope rule: `in_scope` is what
removes a row from a denominator, and a row about an optional feature still caps at `important`
under `LEDGER-FORMAT.md`'s rule whatever the envelope says.

## Eligibility

A row is in the recall denominator when **all four** hold: `status: active`, `in_scope: true`,
`recoverable: true`, and a class the table below includes. Nothing else filters the set. Not
silicon revision — a row affecting one revision counts the same as one affecting four. Not
`applicability.vendor_confirmed`, `implementation_observed` or `unresolved`; those columns are
reported, never subtracted. And never anything derived from a candidate: not its scope, its
headings, its stated assumptions, or what it turned out to cover.

| Class | In the recall denominator? |
|---|---|
| `documented-hardware-requirement` | **Yes.** |
| `unresolved-conflict` | **Yes.** Scored `covered` when the candidate states the conflict, not when it picks a side. |
| `inference` | **Yes.** A conclusion a careful reader of the corpus can reach is a conclusion a candidate is expected to reach. |
| `observed-software-behavior` | **No.** Reported as its own count, never folded into recall. |
| `implementation-choice` | **No.** A precision probe for the selected policy or value the row identifies; a candidate that omits it is scored nothing at all. A candidate that asserts it as necessary is judged by the necessity rule below. |

**An implementation choice asserted as necessary.** An `implementation-choice` row is a precision
probe for the selected policy or value that row identifies. Asserting its necessity is an error
**only where the corpus establishes an alternative**; where the corpus neither states the necessity
nor establishes an alternative, the unsupported rule under "Precision adjudication" applies and the
claim is not an error. **Constituent hardware requirements inside such a sequence remain
independently valid**: a driver's initialization ordering can be the driver's choice while
individual steps within it are requirements other rows state, and a candidate stating one of those
is judged against the row that owns it, not against this one. This replaces the automatic
`misstated` of `enc28j60-1.2`, which the composite rule then extended to "at least one" enumerated
fact — too broad in both places, because corpus silence about a prescribed check establishes the
absence of a prescription and not the presence of an alternative. PHY-030's notes are the row this
corrects.

**Scope, recoverability and withdrawal filter the ledger's recall and probe rosters only.
Precision evaluates every claim the candidate makes.** A row that is out of scope, not
recoverable, or withdrawn sits outside every *denominator* and is reported separately, because it
measures the corpus rather than the candidate — but a candidate claim about its subject is judged
like any other claim. An incorrect wake-on-LAN claim is a precision error even though `IRQ-016` is
out of scope; a correct one is a correct claim that earns no recall credit. Nothing about a row's
scope reaches precision.

**Rosters, as of 2026-09-20 and regenerated from the ledger at freeze.** Observed software
behavior, thirteen active rows, counted but not in recall: REG-007, TX-022, RX-026, RX-030,
RX-037, RX-039, IRQ-014, IRQ-018, IRQ-019, PHY-027, SPI-022, SPI-023, ERR-006. Inference, three
active rows, in recall: RX-006, RX-031, PHY-012. Their conditions and inference status survive
inclusion: RX-006 is not a universal odd-`ERXND` obligation and PHY-012 is not a universal
explicit-programming obligation. `unresolved-conflict`, no active rows: REG-007 was the only one
and was reclassed on 2026-09-20 (`ADJUDICATION.md` group E2), so the class stays in the table
above for a future row and contributes nothing to this run's denominator.

## The recall formula

    recall = (covered + partial credit) / eligible rows

A `partial` on an **atomic** row contributes 0.5. A `partial` on a **composite** scoring unit
contributes the fraction of that unit's frozen fact count the candidate stated correctly, as
"Composite scoring units" sets out; the count in that table is the denominator, not a scorer's own
reading of the row.

Reported **overall and within each weight bucket**, never blended into one number: 90% with every
`critical` row missing is not a good specification. `missing` and `misstated` contribute zero.
Each bucket prints its own numerator terms beside the percentage, because a specification that is
100% `partial` is a distinct failure from one that is 50% `missing` and both print the same
percentage. An empty weight bucket prints `n/a (0 eligible rows)` — never `0%`, and never `100%`.

## Composite scoring units

`LEDGER-FORMAT.md` authoring rule 3 says a row states one thing, and allows this policy to name a
**bounded** set of ids scored as composite units instead. The table below is that list, and the
number beside each id is how many facts that unit holds.

**The facts themselves are written down, in `SCORING-FACTS.md`.** That file holds one ordered list
per unit, and the list's length is the number in this table. A frozen count fixes a fraction's
denominator and nothing else, so without the lists two scorers can divide by the same number and
disagree about the top; the lists are what make the numerator reproducible. **A scorer records a
disposition against each listed fact and may not subdivide, combine or substitute facts.**
`SCORING-FACTS.md` is frozen with this file and the lock records its sha256, because a list anyone
can edit fixes nothing.

**How a row's facts were counted.** Every active row was walked and the independently checkable
facts it asserts were enumerated. A fact is one proposition a reviewer can mark right or wrong on
its own: one register's placement, one bit's position and meaning, one code in a table, one value,
one prohibition, one step of a sequence carrying its own value, one peer requirement. Four
conventions kept the walk consistent, and they are part of the frozen rule:

- **An attribute rides with the element it qualifies.** A register's width, a register's access, a
  bit's self-clearing behavior belong to that element's fact and are not facts of their own.
- **A mechanism, condition or consequence rides with the requirement it serves when contradicting
  it would falsify that requirement.** INIT-002 is the worked example: "CLKRDY becomes set when the
  start-up timer expires" is why the poll works, so a candidate that contradicts it has
  contradicted the poll, and the row holds one fact. A clause that survives its requirement's
  contradiction — a hardware behavior the requirement does not rest on — is its own fact, which is
  why INIT-003 holds three.
- **A clause entailed by another fact in the same row is not counted, and neither is a clause whose
  work is to record the row's class or provenance** — that the corpus permits alternatives, that a
  value is the driver's own, which document corrected which. Those make the row's class readable;
  they are not content a candidate is scored on.
- **A listed set may be designated one credit-bearing fact.** It earns credit only when every
  listed member and the shared property are stated correctly; naming some members earns nothing,
  and a scorer may not award part of it. Every such set is marked `[grouped set]` in
  `SCORING-FACTS.md` and its members are listed there, so grouping is visible where it is scored.
  Grouping is for a set the corpus presents as one thing — a block of consecutive registers, a run
  of reserved addresses, several registers sharing one reset value in one column. Where the corpus
  prints each member as its own row with its own outcome, the members are separate facts;
  `REG-019`'s eight PADCFG codes were split on 2026-09-20 for exactly that reason.

**Because grouping is in play, the fact total is not an inventory of independently checkable
propositions.** It is a count of credit-bearing units of judgment, some of which are sets judged
whole. The same goes for the smaller conventions `SCORING-FACTS.md` marks: a low/high register pair
is one placement, and a multi-bit field or a run of reserved bits described as one range is one
fact.

The classification follows from the count instead of preceding it. **A row whose count is 1 is
atomic by construction. A row whose count is 2 or more is a composite scoring unit, and its count
is the denominator of its partial credit.** For atomic rows nothing is recorded: the absence of an
entry in the table below is the claim that the row holds one fact.

**The walk covered all 203 active rows in `ledger.yaml` on 2026-09-20**, and every composite unit's
facts were written out as a list the same day. It found **141 composite units and 62 atomic rows**,
holding 687 facts between them, 625 of them in the composite units. Per facet the composite units
are REG 26, INIT 13, TX 17, RX 21, IRQ 13, PHY 27, SPI 16, ELEC 7, ERR 1. The distribution of
counts is 62 rows at 1, 34 at 2, 39 at 3, 19 at 4, 18 at 5, 12 at 6 and 19 at 7 or more; the
largest units are TX-008 at 21, INIT-010 at 18, RX-011 at 15 and REG-003 at 14.

| Scoring unit | The facts it enumerates | Facts |
|---|---|---|
| REG-001 | twelve bank 0 pointer registers, one placement each | 12 |
| REG-002 | six bank 1 filter-register placements | 6 |
| REG-003 | thirteen bank 2 MAC and MII placements, and the reserved-address list | 14 |
| REG-004 | the MAC address block and eight further bank 3 placements | 9 |
| REG-005 | the E, MA and MI prefix mappings | 3 |
| REG-006 | address 0x1A, other reserved registers, unimplemented addresses | 3 |
| REG-007 | four driver-defined names at addresses the corpus leaves reserved | 4 |
| REG-008 | seven ECON1 fields and the all-zero reset | 8 |
| REG-009 | five ECON2 fields and the unimplemented low bits | 6 |
| REG-010 | seven ESTAT bit positions | 7 |
| REG-011 | the Power-on Reset rule and the PWRSV effect | 2 |
| REG-013 | three reset-value groups | 3 |
| REG-014 | five MAC configuration reset values | 5 |
| REG-015 | the register's identity and four revision codes | 5 |
| REG-017 | the prescaler field, seven codes, and two reset behaviors | 10 |
| REG-018 | six MACON3 fields | 6 |
| REG-019 | eight PADCFG codes, the TXCRCEN pairing, the TXCRCEN-clear behavior | 10 |
| REG-020 | six octet-to-register mappings | 6 |
| REG-021 | four MACON1 bits and the reserved bit | 5 |
| REG-022 | three MACON4 bits, the half-duplex restriction, the reserved bits | 5 |
| REG-023 | five MAC timing and limit registers | 5 |
| REG-024 | three pointer loads, the CSUMEN precondition, the start, two wrap rules, completion, cancellation | 9 |
| REG-025 | the equal-pointer case, the unreachable-end case, the no-modify rule | 3 |
| REG-026 | the start condition, the result location, the algorithm, the odd-length pad, the absent side effects | 5 |
| REG-027 | the copy rate and the checksum rate | 2 |
| REG-029 | seven EIR bit positions | 7 |
| INIT-001 | the start-up window, what may be accessed, three prohibitions | 5 |
| INIT-003 | the stopped PHY clock, CLKRDY's unchanged state, the 1 ms wait | 3 |
| INIT-005 | the reset-value rule, the transmit-only and receive-only resets, buffer contents through a System Reset, buffer state after a Power-on Reset | 4 |
| INIT-007 | the PWRSV precondition, the Bit Field Clear, the 300 us regulator wait | 3 |
| INIT-010 | seventeen steps of the driver's initialization order, and the enable it defers | 18 |
| INIT-011 | MARXEN, and the pause-enable pair for full duplex | 2 |
| INIT-012 | the padding and CRC configuration, the host's fallback obligation, FULDPX, FRMLNEN | 4 |
| INIT-014 | the MAMXFL programming requirement, the standard-frame value, the receive-side rejection | 3 |
| INIT-015 | the full-duplex and half-duplex MABBIPG values | 2 |
| INIT-016 | MAIPGL, and MAIPGH in half duplex | 2 |
| INIT-017 | the half-duplex defaults, the long-cable exception, the full-duplex case | 3 |
| INIT-019 | five power-save steps and what PWRSV makes inaccessible | 6 |
| INIT-020 | clearing PWRSV, the 300 us wait, re-enabling RXEN, the link re-establishment delay | 4 |
| TX-001 | the control byte's position, four bit positions, the two POVERRIDE cases | 7 |
| TX-002 | ETXST, ETXND, and where the status vector is written | 3 |
| TX-003 | what the host writes, what the MAC generates, and that MAADR is not inserted | 3 |
| TX-004 | the start, the TXRTS clear, the status-vector write, the untouched pointers | 4 |
| TX-006 | two prohibitions while TXRTS is set and the cancellation rule | 3 |
| TX-007 | four abort effects and two host obligations | 6 |
| TX-008 | twenty status-vector fields and the vector's little-endian packing | 21 |
| TX-010 | the TXRST pulse and the order of clearing TXERIF | 2 |
| TX-012 | the late-collision treatment, the stalled state machine, three host obligations | 5 |
| TX-014 | the reset's effect, the in-progress abort, the resume, what is unaffected | 4 |
| TX-015 | automatic retransmission, the MACLCON1 abort, the late-collision abort, the full-duplex case | 4 |
| TX-016 | the POVERRIDE case, the MACON3 case, the abort at MAMXFL | 3 |
| TX-017 | transmission waiting for the DMA, and the DMA waiting for transmission | 2 |
| TX-018 | the zero control byte, the single transmit slot, one packet outstanding | 3 |
| TX-019 | the 0x02 and 0x03 EFLOCON values, FULDPXS, the FCEN bits | 4 |
| TX-020 | the silent transmit delay and what PASSALL exposes | 2 |
| TX-024 | FCEN0's backpressure mechanism and the vendor's deployment advice | 2 |
| RX-001 | the buffer extent, the FIFO range, the wrap, the containment rule, the transmit remainder | 5 |
| RX-007 | the low-byte-first write order, and that reads need no order | 2 |
| RX-008 | the write boundary, the abort that preserves data, the host's advance obligation | 3 |
| RX-009 | the next-packet pointer, the status vector, the frame bytes, even packet starts, the pad byte | 5 |
| RX-010 | the field position, its byte order, and what the count includes | 3 |
| RX-011 | thirteen status bits, the zero bit, the reserved bits | 15 |
| RX-012 | the PKTDEC write with its self-clearing, the ignored underflow | 2 |
| RX-013 | the saturation at 255, the abort at 255, the host's decrement obligation | 3 |
| RX-015 | the internal write pointer load, and ERXWRPT's update rule | 2 |
| RX-017 | three free-space cases and the permanently unusable byte | 4 |
| RX-018 | the enable ordering and three restrictions once RXEN is set | 4 |
| RX-019 | eight ERXFCON bits, the two ANDOR modes, CRCEN's ordering, the promiscuous value | 12 |
| RX-020 | the unicast, multicast, broadcast and hash-table criteria | 4 |
| RX-021 | three filter settings the driver uses, and the two filters it never programs | 4 |
| RX-024 | the hardware's 18-byte rejection, the 18-to-63 acceptance, the host's 64-byte obligation | 3 |
| RX-025 | two drop conditions and the separate error counting | 3 |
| RX-026 | the corruption test and five recovery steps | 6 |
| RX-027 | the reset's effect, the aborted packet, the cleared RXEN, the resume, what is unaffected | 5 |
| RX-033 | the in-order processing requirement and the copy-to-keep rule | 2 |
| RX-036 | the masked checksum, the EPMO window, the EPMCS comparison | 3 |
| RX-037 | the ERXRDPT advance, the saved pointer, the PKTDEC write | 3 |
| IRQ-001 | eight EIE bit positions | 8 |
| IRQ-002 | the pin's level behavior and its edge-triggered intent | 2 |
| IRQ-003 | flags set regardless of the enables, and the clear-before-enable obligation | 2 |
| IRQ-005 | clearing INTIE on entry, and what re-setting it with an event pending does | 2 |
| IRQ-006 | PKTIF's unreliability with the EPKTCNT obligation, and the pin's continued reliability | 2 |
| IRQ-007 | set while EPKTCNT is non-zero, and the clearing rule with its read-only access and ineffective Bit Field Clear | 2 |
| IRQ-008 | TXIF's set condition, its clearing, the success test | 3 |
| IRQ-009 | five abort causes, the simultaneous TXIF, the full-duplex case, the clearing | 8 |
| IRQ-010 | two set conditions, the permanent loss, two host obligations | 5 |
| IRQ-011 | the two PHY enables, the shadowing, read-only in EIR, clearing by reading PHIR, change rather than state | 5 |
| IRQ-012 | the completion case, the cancellation case, the clearing | 3 |
| IRQ-016 | four preconditions and the wake effect | 5 |
| IRQ-018 | ten steps of the driver's handler loop | 10 |
| PHY-001 | the 16-bit width, the inaccessibility to control commands, the MII path | 3 |
| PHY-002 | five steps of the PHY read procedure | 5 |
| PHY-003 | three write steps, the transaction timing, the no-scan rule | 5 |
| PHY-005 | three operations prohibited while BUSY | 3 |
| PHY-006 | nine implemented addresses and the behavior of the rest | 10 |
| PHY-007 | two MICMD bits and four MISTAT positions | 6 |
| PHY-008 | four PHCON1 bits and the reserved pair | 5 |
| PHY-010 | the absence of autonegotiation and what an autonegotiating partner detects | 2 |
| PHY-011 | the sampling mechanism and three wiring outcomes | 4 |
| PHY-013 | the half-duplex loopback default, HDLDIS, when HDLDIS is ignored | 3 |
| PHY-014 | the unreliable half-duplex loopback, the external-cable recommendation, the HDLDIS advice, its default | 4 |
| PHY-015 | the unreliable full-duplex loopback, the external connector, PLOOPBK's effect on the link | 3 |
| PHY-016 | six PHSTAT2 bits, each with its read-only access | 6 |
| PHY-017 | two capability bits and two latching bits | 4 |
| PHY-018 | four PHCON2 bits and the reserved-as-zero rule | 5 |
| PHY-019 | two PHIE bits, two PHIR bits, the read-to-clear rule, the reserved bits | 6 |
| PHY-020 | four PHLCON fields, two reserved-bit rules, the reset value | 7 |
| PHY-022 | the 1110 code's behavior and the two substitute codes | 3 |
| PHY-023 | the LED misdetection, its effect on PDPXMD, the resistor workaround | 3 |
| PHY-024 | the ineffective polarity correction and the wiring workaround | 2 |
| PHY-025 | PRST's effect and the poll-until-clear obligation | 2 |
| PHY-026 | the two identifier values, with their read-only constancy | 2 |
| PHY-027 | reading link state from PHSTAT2, and reporting DPXSTAT's duplex | 2 |
| PHY-028 | the transmit-quiescent and receive-disabled conditions | 2 |
| PHY-029 | the scan's rate, NVALID, the unpaired halves, the stop procedure | 4 |
| PHY-031 | the five-bit field with its unimplemented upper bits, the reset value | 2 |
| PHY-032 | six common LED configuration codes | 6 |
| SPI-001 | mode 0,0 with SCK idle low, the sampling edge, the drive edge | 3 |
| SPI-002 | CS low for the whole instruction, the framing edge, the abandoned partial byte | 3 |
| SPI-004 | the opcode, the address argument, the single data byte | 3 |
| SPI-005 | two opcodes, the fixed argument, the buffer-only rule | 4 |
| SPI-006 | the set opcode's OR, the clear opcode's AND-inverse, the operand format | 3 |
| SPI-007 | the ETH-only restriction and the read-modify-write alternative | 2 |
| SPI-009 | the dummy byte on MAC and MII reads, and the ETH read | 2 |
| SPI-010 | the four banks of 32, and the address's bank dependence | 2 |
| SPI-013 | the ERDPT advance, the ERXND-to-ERXST wrap, the continued stream | 3 |
| SPI-014 | the unbounded stream, the EWRPT destination, the auto-increment, the single wrap point | 4 |
| SPI-016 | the ETH hold time and the MAC and MII hold time | 2 |
| SPI-017 | the fast-clock remedy and the synchronous-clock remedy | 2 |
| SPI-018 | the read bit order and the write bit order | 2 |
| SPI-019 | the instruction byte's shape, the argument's two meanings, the closed set of seven | 3 |
| SPI-020 | the opcode, the address argument, the returned contents | 3 |
| SPI-022 | the split 16-bit write and the split 16-bit read | 2 |
| ELEC-001 | the frequency and tolerance, the duty cycle, the swing | 3 |
| ELEC-002 | six SPI timing figures | 6 |
| ELEC-003 | the minimum low time, the minimum high time between resets, the untouched pin | 3 |
| ELEC-004 | the supply slew rate and the operating range | 2 |
| ELEC-005 | the 5 V tolerant inputs, the 3.3 V outputs, the internal pull-ups | 3 |
| ELEC-007 | the B1 and B4 value, and the B5 and B7 value | 2 |
| ELEC-008 | the held-low start, the ECOCON frequency, the prescaler gap, the minimum pulse | 4 |
| ERR-001 | the aborted packet with its flags, the vendor instruction, the unaffected copy mode | 3 |
| **Total** | | **141** |

**The verdict rule, for all 141.** Each contributes one denominator unit, and the unit's frozen
count is what its partial credit is computed over. Let **n** be the number of facts
`SCORING-FACTS.md` lists for the unit — the number in the table above — and **k** the number of
them the candidate states **fully correctly**. An underspecified fact contributes zero:

- `misstated` — any listed fact is contradicted. Earns zero, whatever else is right, and this test
  comes first.
- `covered` — all n facts are correct (k = n). Earns 1.
- `missing` — the candidate states no recognizable content for the unit at all. Earns zero.
- `partial` — everything else. Earns **k/n**, **including k = 0**: a candidate that writes about
  the unit's subject while getting no single listed fact fully right is `partial` earning zero, not
  `missing`. A candidate with three of RX-020's four filter criteria earns 0.75 of that row.

The k = 0 case is why `partial` and `missing` are not the same verdict at the same score: they are
different failures, they are reported as separate counts, and a `missing` unit is one the candidate
never addressed.

**What "fully correct" means for a fact that carries attributes.** A listed fact is fully correct
when everything its entry names is stated correctly — the element **and** every attribute the entry
carries with it. A correct address with the access the entry names **omitted** is underspecified
and earns zero for that fact, without making the row `misstated`; the same attribute stated
**wrongly** is a contradiction and does make the row `misstated`. An attribute the entry does not
name is not required. The strict reading follows from the attribute convention: an attribute is
folded into its element's fact instead of being counted separately, and if it were then not
required for credit, folding it in would have removed it from the scoring surface altogether.
`SCORING-FACTS.md` therefore carries in each entry the attributes that are credit-bearing for that
unit, and only those.

**The frozen count is the denominator, never a scorer's own segmentation.** A scorer who reads
RX-020 as three criteria rather than four, or TX-008 as one layout rather than twenty-one fields,
still divides by the number printed in this table; that is what freezing it is for, since two
scorers reading one candidate must not be able to reach different numbers by segmenting a row
differently. The same holds for the numerator: the facts are the ones `SCORING-FACTS.md` lists, in
its order, and a scorer marks each one rather than counting up its own. **A count, and the list
behind it, change only with a new policy version**, exactly as the id list does: changing any of
them changes every recall number computed under it.

Atomic rows keep the ordinary rule, where `partial` earns 0.5. Their one fact stated but
underspecified is half a row by convention rather than by count — dividing one correct fact by a
count of one would turn every partial into a coverage.

Precision evaluates the candidate's individual claims independently, so one wrong bit is one
precision error whatever the row verdict is.

**Recall measures coverage of the frozen scoring units**, not the fraction of independent hardware
facts a candidate recovered: a unit holding twenty-one facts and a unit holding two each contribute
one to the denominator. Proportional partial credit makes an incomplete unit's contribution
proportionate *within* the unit; it does not make units comparable to one another. **Atomic and
composite verdict counts are reported separately, alongside the weight buckets**, so a reader can
see which kind of unit a recall number is made of.

Fourteen of the 141 are rows no recall denominator contains: the `observed-software-behavior` rows
REG-007, RX-026, RX-037, IRQ-018, PHY-027 and SPI-022, the `implementation-choice` rows INIT-010,
RX-021, RX-025 and TX-018, and the out-of-scope rows IRQ-016, ELEC-004, ELEC-005 and ELEC-007. They
are listed because the rule still has work to do wherever the row is scored at all: an
implementation-choice probe is judged fact by fact, on the necessity rule under "Eligibility", and
not only as a whole row.

**Enumerated rather than split.** Enumeration is the disposition for a row that is one register's
definition, one document table, or one mechanism a reader looks up in one place — the shape the
adjudicator approved for the original seven, and the disposition **all 141** of the units below
took. Splitting is for a row bundling things a reader would look up in different places; every row
was put to that second question and two met it, on 2026-09-20. PHY-006's reserved-bit write rule
became PHY-033, which was withdrawn into PHY-020 later the same day once its duplication of
PHY-020 was found, and TX-019's half-duplex backpressure clause became TX-024. Neither split took a
row out of this table: PHY-006 and TX-019 are still composite after losing a clause, and TX-024 is
itself a two-fact unit.

Two rows were considered for splitting and kept whole, for the unit they are meant to be rather
than for the cost of reopening the merge that made them:

- **REG-023** is the block of MAC timing and limit values a driver programs in one initialization
  step, read from one table. That block is the intended unit: a candidate that gets the
  inter-packet gap encodings right and MAMXFL's width wrong has one partly correct unit, which its
  count of five now expresses directly.
- **RX-019** is ERXFCON's definition. The bit positions and the combination semantics those bits
  select are read in the same register definition, and the ANDOR rule cannot be stated apart from
  the bits it combines, so splitting would produce two units neither of which can be scored on its
  own.

The set is not one row per register. PHY-007 covers MICMD **and** MISTAT and PHY-019 covers PHIE
**and** PHIR; TX-008 is the seven-byte transmit status vector and RX-011 the four-byte receive one;
RX-019 carries the ANDOR combination rule and CRCEN's ordering alongside ERXFCON's bit positions;
REG-001 to REG-004 are the four bank columns of one register map.

**The exception covers these 141 ids and no others.** A row not in the table is atomic and governed
by authoring rule 3, and the walk that produced the table is the evidence that a row's absence from
it is a judgment rather than an oversight. Adding an id, removing one, changing a count, or
changing what a unit's facts are in `SCORING-FACTS.md` takes a decision in `ADJUDICATION.md` and a
new policy version, because the list, its counts and the fact lists behind them are frozen policy
text. Two rows stating the same clause is a different problem — that is overlap, disposed of
in the ledger with `overlaps` and `replaced_by`, adjudicated in group F and swept again before the
freeze.

## Precision adjudication

- Precision is computed over **the candidate's own claims, including claims with no ledger row**. A
  claim the ledger never anticipated is still judged, and a wrong one is still an error.
- **The formula.**

      precision = (N - errors) / N

  `N` is every claim the candidate makes, after the deduplication below. Unsupported and partial
  claims **stay in `N`** and are not errors: they are counted and reported separately, beside
  precision, precisely because they do not move it. `N = 0` prints `n/a (0 claims)`, never `0%`
  and never `100%`.
- **Segmentation.** A claim is one independently falsifiable proposition: one value, one ordering,
  one access rule, one consequence. **Count semantic assertions independent of formatting: a label
  and its value form one assertion.** The same register mapping is the same number of claims
  whether the candidate prints it as a sentence, a bullet or a table row, so a candidate cannot
  move its own precision by reformatting. A candidate sentence carrying three assertions is three
  claims, and a table row is a claim per cell that asserts something.
- **Deduplication.** The same proposition asserted more than once in the candidate is one claim,
  judged once, at its strongest statement. A candidate claim that matches several ledger rows is
  also one claim and counts once — overlapping ledger rows do not multiply a single error, which
  is why the freeze gate refuses undisposed overlaps.
- **Contradicted** — the corpus says otherwise. An error.
- **Unsupported** — the corpus neither states it nor contradicts it. Not an error; recorded as its
  own count, because a specification full of unsupported claims is a distinct failure from an
  accurate one and the number has to be visible.
- **The three ways a claim about hardware necessity can go wrong**, which the two rules above are
  otherwise read as deciding differently:
  - **Contradicted** when the corpus establishes a valid alternative — that the requirement can be
    met another way, or need not be met at all. An error.
  - **Unsupported** when the corpus neither states the necessity nor establishes an alternative.
    Not an error. Corpus silence never makes a necessity claim wrong, in either direction.
  - **An attribution error** when the claim is credited to a named source that does not state it.
    An error whether or not the requirement itself turns out to be true, and counted once, against
    the claim it attaches to.
  A candidate asserting a behavior the reference driver chose as a hardware requirement is the
  first of these where the corpus shows the alternative — which is what the `implementation-choice`
  probes measure — and the second where it does not.
- **Partial** — true but underspecified (a value without its constraint, a sequence without its
  ordering). Not an error; counted separately, and it may still leave the matching row `partial`.
- **Conditional** — true under a condition the candidate states (a silicon revision, a duplex
  mode, a configuration). Judged against the condition: correct with it, an error without it if
  the unconditional form is false.
- **An observation of driver behavior, correctly attributed** — "the reference driver does X" — is
  judged as that claim and is not an error when true.
- **What a verdict is given against.** A row's `statement` is the scoring target. Its `notes`, its
  `derivation` locators and any cross-reference either of them carries are context for the scorer
  and are never content a candidate is expected to reproduce: a candidate loses nothing by omitting
  them and gains nothing by restating them. Where a clause was moved to another row and left behind
  as a cross-reference, the row named in the cross-reference is the one that scores that clause.
- **A clause explicitly assigned to another row is scored only in that owner row**, even where it
  is reproduced beside its cross-reference for readability, and it is not an enumerated fact of the
  row that reproduces it. The rule exists so that a restatement cannot double a clause's weight in
  the denominator; the ledger nonetheless removes the restated wording wherever the sentence still
  reads without it, because a scorer should not have to work out which words in a `statement` are
  not scored.
- **Content that follows from a concrete value.** A candidate that states a concrete value from
  which a row's content follows **covers** that row, without also stating it in the row's terms.
  RX-029 is the worked example: a candidate specifying `ERXST = 0x0000` has satisfied the
  even-address recommendation and does not have to repeat the recommendation to earn the row.
- `misstated` counts as `missing` for recall **and** as an error for precision.

## Uncertainty

- **An inference presented as an inference** — stated with its premises and marked as a conclusion
  rather than a reading — scores `covered` on an `inference` row and is not a precision error.
- **The same content asserted as documented fact** is **`covered` for recall and a separate
  precision attribution error**. It is explicitly *not* a `misstated` recall row: the content is
  right and the sourcing is wrong, those are two different failures, and the general `misstated`
  rule — which would zero the row — does not apply. Scoring it both ways would punish one mistake
  twice and hide which one it was.
- **An unresolved conflict** scores `covered` when the candidate states that the sources disagree
  and names both readings; picking a side, however defensible, is `partial`, and picking one while
  presenting it as settled is `misstated`.
- **Uncertainty never shrinks the denominator.** `applicability.unresolved: true`, a hedge in a
  row's `notes`, or a reviewer's open question leaves the row eligible exactly as it was.
  Excluding a row takes `in_scope: false` or `recoverable: false`, with the reason in `notes`,
  recorded before the freeze.

## Reporting

Recall per weight and unweighted, never one blended number, with `partial` also as its own count
and with **atomic and composite verdict counts reported separately** beside the weight buckets,
because recall measures coverage of the frozen scoring units and a reader has to see which kind of
unit the number is made of;
the observed-software-behavior counts beside recall, never inside it; the implementation-choice
probes as a count of `misstated` out of the probes, which is a precision result and not a recall
one; the unsupported-claim count beside precision.

**A report names the critical facts the candidate missed, not only the fraction.** For every
`critical` unit scored `partial`, the report lists by number the facts of `SCORING-FACTS.md` the
candidate did not state fully correctly. Proportional credit makes this necessary: a candidate can
earn four fifths of PHY-018 while omitting HDLDIS, the fact the envelope makes that row critical
for, and the fraction alone hides it. Critical recall is coverage of critical units; it is not
proof that the essential behavior is specified, and the list of missed facts is what lets a reader
see the difference.

**The outer denominator is scoring units, not facts.** A unit's facts decide that unit's
contribution; the denominator a recall percentage divides by is the 162 eligible rows. A report
says so rather than presenting 687 as the thing recall is computed against.

## Binding

The freeze lock records this file's **sha256 as well as the version string** `enc28j60-1.4`,
beside the ledger and corpus digests, and every run cites the lock rather than the version. It
records `SCORING-FACTS.md`'s sha256 as `facts_sha256` for the same reason: that file holds the
numerator of every composite fraction, so a score computed under this policy is only reproducible
if its bytes are pinned too. A
version label on a mutable file binds nothing: the label can stay while the text moves.
`ledger_check.py --lock` now enforces that. It requires a `Version:` line in this file and a
non-empty `policy_version` and `policy_sha256` in the lock, and fails when either side is missing
or the two disagree — two absent versions no longer agree by accident. The lock additionally pins
`LEDGER-FORMAT.md`'s bytes as `format_sha256`, because the verdict definitions and the authoring
rules this policy builds on live there, and carries a `revision` identifying the repository state
that holds the checker, the adjudication record and the authoring brief: a digest identifies
bytes, and a revision is what makes them recoverable.

## Version history

A version is a name for one exact set of scoring rules. The id list under "Composite scoring
units", and each unit's fact count beside it, are part of that set, so lengthening the list or
changing a count is a new version and not an edit: a run scored under
`enc28j60-1.0` put one denominator unit where a run scored under `enc28j60-1.1` puts one for nine
further rows, and the two recall numbers are not comparable. Nothing forces the bump
mechanically — the freeze lock pins the file's sha256, so an unversioned edit would be caught as a
changed hash rather than as a changed policy, which says "this file moved" and not "these results
mean something different". The version string is what carries that second meaning, so it moves
whenever the rules do.

| Version | Adopted | What changed, and why the bump |
|---|---|---|
| `enc28j60-1.0` | 2026-09-20 | First named policy: the group A4 denominator rule, eligibility, the recall formula, precision adjudication, uncertainty, binding, and seven composite scoring units. |
| `enc28j60-1.1` | 2026-09-20 | Nine more composite scoring units (REG-008, REG-009, REG-018, REG-021, REG-022, RX-011, RX-019, IRQ-001, TX-008), from `ADJUDICATION.md` group G. The id list is frozen policy text and each addition moves a row from "one wrong bit fails the row" to the composite verdict rule, so the denominator and the per-row verdicts both change. The observed-software-behavior roster also grew from ten rows to thirteen (REG-007 reclassed by group E2; SPI-023 and RX-039 added by group D), which changes the recall denominator by removing REG-007 from it; the same bump carries it. |
| `enc28j60-1.2` | 2026-09-20 | The composite inventory, made by walking every active row: **16 ids to 113**, with the test that decided each row written down and the per-facet counts printed. Every row's verdict rule can change with it, so the bump is mandatory. The same version carries five other rule changes a scorer would feel: the operating envelope the `critical` weights assume, stated so the necessity argument is checkable; that scope filters rosters only while precision covers every candidate claim; the contradicted / unsupported / attribution-error distinction for necessity claims; that correct inference content presented as documented fact is covered content with a precision attribution error and not a `misstated` row; formatting-independent segmentation; what a verdict is given against and when a concrete value earns coverage; and the precision formula written out with its denominator and its `n/a` case. Two rows were split rather than enumerated (PHY-006 to PHY-033, TX-019 to TX-024), so the ledger's active row count moves from 202 to 204. |
| `enc28j60-1.3` | 2026-09-20 | Proportional partial credit, and the fact-count inventory that makes it computable. Every active row was walked again and the independently checkable facts it asserts were enumerated and frozen, with the counting conventions written down: **141 composite units, from 113**, against 62 atomic rows, each unit's count printed beside it. A composite `partial` now earns the fraction of that unit's frozen count the candidate stated correctly instead of a flat half, so every partially covered row's contribution moves and no recall number is comparable with one computed under `enc28j60-1.2`. Twenty-eight rows moved from atomic to composite and none the other way, which changes their verdict rule as well. The same version carries four other rule changes a scorer would feel: an implementation choice asserted as necessary is an error only where the corpus establishes an alternative, replacing the automatic `misstated` and its "at least one" extension; a clause explicitly assigned to another row is scored only in the owner row; recall is stated as coverage of the frozen scoring units, with atomic and composite verdict counts reported separately; and REG-023 and RX-019 are kept whole for the unit they are meant to be rather than because splitting would reopen a merge. `ENC28J60-PHY-033` was withdrawn into PHY-020 as a duplicate of its reserved-bit rules, so the active row count moves from 204 to 203 and the recall denominator from 163 to 162. |
| `enc28j60-1.4` | 2026-09-20 | The fact lists, in a new frozen file `SCORING-FACTS.md`: one ordered list of credit-bearing facts per composite unit, the list's length being the unit's count, so the numerator of a proportional score is as fixed as its denominator. A scorer marks each listed fact and may not subdivide, combine or substitute. The same version carries the rule changes the lists forced. **Eight counts moved** and the fact total goes from 689 to 687: REG-019 6 to 10 (the corpus prints each of the eight PADCFG codes as its own row, so they are not four outcome groups) and INIT-010 17 to 18 (the deferred interrupt and RXEN enable is its own ordering fact); RX-012 3 to 2, IRQ-007 4 to 2, PHY-016 7 to 6, PHY-026 3 to 2, PHY-031 3 to 2 and PHY-032 7 to 6, each applying a convention the counts had contradicted. **A fourth counting convention** authorizes a designated grouped set as one fact, earning credit only when every member and the shared property are stated, and the total is no longer described as an inventory of independently checkable propositions. **The composite verdict rule is restated as k/n** with the uncovered case closed: any contradiction is `misstated`, all n correct is `covered`, no recognizable content is `missing`, and everything else is `partial` earning k/n including k = 0. **"Fully correct" is defined** for a fact carrying attributes: everything the entry names must be stated, so an omitted named access earns zero for that fact and a wrong one makes the row `misstated`. Reporting gains the requirement to name which critical facts a candidate missed. Every partially covered row's contribution can move, so no recall number is comparable with one computed under `enc28j60-1.3`. |

No candidate has been read under any version, so nothing needs rescoring; the rule below is for
when that stops being true.

## Changes after a candidate has been read

A correction found after any candidate has been read gets a **new ledger or policy version and a
declared rescoring procedure**. The original result is never silently altered: it keeps its own
version beside the new one, and a rescore is a new run with its own record. A denominator chosen
after seeing a candidate is not a measurement.
