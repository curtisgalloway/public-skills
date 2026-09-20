---
spec: tensor-g5
spec_file: tensor-g5.spec.md
spec_sha256: e58871df4e9c4a127e9bec5eca4545dccd78f4bf02dc1487784691ed4a10819f
verified: 2026-09-19
verifier: >-
  Verification ran in three rounds, each by verifiers in fresh contexts that were given the spec,
  its declared sources, and the verifier procedure -- never a previous record, this repository's
  git history, nor each other's findings. Each wrote its own flattened-device-tree reader rather
  than trusting any cached extraction. Round 5 read both specs in full, round 6 re-read only the
  claims round 5's corrections had changed, and round 7 only those round 6's corrections had
  changed; the scope narrowed because every round's failures were defects introduced by the
  previous round's fixes rather than anything older. Each verdict line below names the round that
  established it and the spec hash it was established against. A line marked carried forward was
  established against an earlier hash on bullet text that has not changed since -- which is a
  mechanical diff against the commit named, not an assertion: regenerate it by extracting the fact
  bullets at that commit and at this one and comparing.
sources:
  - name: linux-mainline
    commit: 17e7b8eacf4cac800a4fc89a28729df72a2dabda
    fetch: ok
  - name: laguna-kernel-prebuilts
    commit: 80c104d7e5591ebc3cd413f54b076d972484ff0b
    fetch: ok
  - name: "Laguna/Tensor G5 SoC and Frankel, Blazer & Mustang boards (v4)"
    url: https://lore.kernel.org/all/20260918-contrib-pg-pixel10-initial-dts-v4-0-745eaca28b1a@linaro.org/
    fetch: ok
  - name: "arm64: google: Introduce frankel, blazer, and mustang boards (v1)"
    url: https://lore.kernel.org/linux-arm-kernel/20251111192422.4180216-1-dianders@chromium.org/
    fetch: ok
  - name: pixelscripts Makefile and lga-ufs-placeholder.dtso
    url: https://gitlab.com/LinaroLtd/googlelt/pixelscripts/-/raw/clo/main/Makefile
    fetch: ok
  - name: Android boot image header
    url: https://source.android.com/docs/core/architecture/bootloader/boot-image-header
    fetch: ok
  - name: Android DTB and DTBO partitions
    url: https://source.android.com/docs/core/architecture/dto/partitions
    fetch: ok
  - name: Android bootloader locking and unlocking
    url: https://source.android.com/docs/core/architecture/bootloader/locking_unlocking
    fetch: ok
  - name: Linux arm64 booting.rst
    url: https://www.kernel.org/doc/Documentation/arch/arm64/booting.rst
    fetch: ok
  - name: Build Pixel kernels
    url: https://source.android.com/docs/setup/build/building-pixel-kernels
    fetch: ok
  - name: android.googlesource.com project list
    url: https://android.googlesource.com/
    fetch: ok
  - name: GrapheneOS source page
    url: https://grapheneos.org/source
    fetch: ok
  - name: Synopsys DesignWare APB UART devicetree binding
    url: https://www.kernel.org/doc/Documentation/devicetree/bindings/serial/snps-dw-apb-uart.yaml
    fetch: ok
  - name: google,lga-dwc3 binding
    url: https://raw.githubusercontent.com/torvalds/linux/master/Documentation/devicetree/bindings/usb/google,lga-dwc3.yaml
    fetch: ok
  - name: google,lga-usb-phy binding
    url: https://raw.githubusercontent.com/torvalds/linux/17e7b8eacf4cac800a4fc89a28729df72a2dabda/Documentation/devicetree/bindings/phy/google,lga-usb-phy.yaml
    fetch: ok
  - name: ARM GICv3 and GICv4 architecture specification (IHI 0069)
    url: https://developer.arm.com/documentation/ihi0069/latest
    fetch: blocked
  - name: Power State Coordination Interface, PSCI (DEN 0022)
    url: https://developer.arm.com/documentation/den0022/latest
    fetch: blocked
  - name: Arm Architecture Reference Manual for A-profile (DDI 0487)
    url: https://developer.arm.com/documentation/ddi0487/latest
    fetch: blocked
  - name: Arm System MMU v3 architecture specification (IHI 0070)
    url: https://developer.arm.com/documentation/ihi0070/latest
    fetch: blocked
  - name: Arm Cortex-X4 / A725 / A520 Core TRMs (102484, 107652, 102517)
    url: https://developer.arm.com/documentation/102484/latest
    fetch: blocked
  - name: Google Store Pixel 10 tech specs
    url: https://store.google.com/us/product/pixel_10_specs?hl=en-US
    fetch: blocked
  - name: Google blog, Tensor G5
    url: https://blog.google/products-and-platforms/devices/pixel/tensor-g5-pixel-10/
    fetch: blocked
summary: {pass: 47, fail: 0, unverifiable: 0, gap: 0, adjudicate: 0}
---

# Verification of `tensor-g5`

Forty-seven claims: sixteen Quick-facts, nine Gotchas, and twenty-two `instances:` rows.
Twenty-two of the twenty-five fact bullets are byte-identical to the text round 5 read in full.

`Quick-facts/1`, the addressing model, is the claim this record exists for. It had been rewritten
three times and falsified four, each time by a placement class its prose did not anticipate, and it
is now a decoding procedure plus a table that partitions every `reg`-bearing node in the production
blob into ten classes. Three verifiers across rounds 6 and 7 each wrote their own reader and each
reproduced 2774 nodes, 645 `reg`-bearing, and all ten class counts, and each confirmed the
partition is mutually exclusive and jointly exhaustive.

The arithmetic is what makes that checkable, and it caught its own defect: round 6 found that the
table's first-match rule was stated over rows ordered broadest-first, so the memory node was
claimed by the row above the one meant for it, yielding 410 and 0 rather than 409 and 1. Round 7
confirmed the corrected order reproduces all ten counts, that the two containments named are the
only overlaps among all ten rows, and that counting every match instead of the first gives 686 --
exactly 41 more than 645, from the 40 reserved-memory children and the one memory node the text
names.

`Quick-facts/2` settled an adjudication item from round 4 by restating the claim rather than
choosing between two readings: the production command line carries protected-KVM parameters, which
implies a hypervisor and an EL2 entry, and carries no parameter that switches protected mode on.
Round 7 established that negative across all four production blobs, which carry byte-identical
command lines, and all 45 overlay entries.

## Verdicts

- Quick-facts/1 "Addressing model": **PASS**. Independently parsed the production blob with a
  reader written for this pass. Own totals: 2774 nodes counting the root (2773 excluding it),
  645 `reg`-bearing. Applying the ten rows in their printed order, first match wins, reproduces
  every stated count exactly: DRAM extent 1, root-level MMIO 409, reserved-memory carve-out 40,
  identity-container MMIO 7, translating-window offset 11, whole-aperture mapping 8, NVMEM cell
  offset 111, graph index 44, CPU identifier 8, convention-only absolute 6. The partition closes:
  the ten sum to 645 of 645 with zero nodes unclassified and zero nodes claimed twice.
  The containment claim holds in all three of its parts. Both pairs are genuine containments: the
  one `device_type = "memory"` node also satisfies the root-level MMIO signature (root declares
  2/2 and carries no `ranges`), and all 40 reserved-memory children also satisfy the
  identity-container signature (their parent carries an empty `ranges`). Each narrower row is
  printed above the row containing it — DRAM extent is row 1 above root-level MMIO at row 2,
  reserved-memory carve-out is row 3 above identity-container MMIO at row 4. Exhaustively
  testing every node against every row finds exactly two overlapping row pairs and no others, so
  "those are the only overlaps" is right. Counting every match instead of the first gives 686
  against 645, a double-count of exactly 41, and it comes from the rows named: 40 from the
  reserved-memory children and 1 from the memory node, with no third contributor.
  The specific regression named in the brief is absent: the current order yields 1 and 409, not
  the 0 and 410 the reversed order would give — 410 is what the all-match count for root-level
  MMIO is, which is what a reader who swapped the two rows would land on.
  Corroborating detail re-derived rather than assumed: the identity-container row's parenthetical
  "seven of them, one two hops deep" is right — seven containers with an empty `ranges` have
  `reg`-bearing children, and one of the seven sits two hops below the root. The convention-only
  row's two named parents are the two that survive: 2 nodes under `/cap_sysfs` and 4 under
  `/ehld-coreinstr`, totalling the stated 6. The sidecar the tag clause points at exists, pins the
  same blob sha256 this pass computed, and reports the same 2774-node total.
  The cell-count trap's opening clause is right and its scoping is load-bearing. Scoped to
  parents of `reg`-bearing nodes, exactly **four** containers declare no cell counts at all:
  `/cap_sysfs` and three `in-ports` containers under three funnel nodes. Unscoped — every
  container in the blob that declares neither, whatever its children carry — the figure is **404**,
  so "containers of `reg`-bearing nodes" is what makes the sentence true rather than off by two
  orders of magnitude. The 2/1 default is wrong for every one of the four: the two `/cap_sysfs`
  children carry four cells, which 2/1 cannot divide (4 is not a multiple of 3), and a 2/1 reader
  gets the addresses right at `0x2191_0008` and `0x8B20_F000` with the size wrong at `0x0` and one
  spare cell, exactly as written; read as 2+2 they give `0x2191_0008`/`0x13F8` and
  `0x8B20_F000`/`0x1000`, matching the spec's stated values. The five `port@N` children of the
  three `in-ports` containers carry one cell each, which a 2/1 reader cannot parse at all; 1/0 is
  the correct reading. Four for four.
  `[DT]` parentheticals on the bullet name both trees the values came from and the blob's origin
  repository, as the format requires.
  *(established pass 7, spec `e58871df`)*

- Quick-facts/2 "Boot chain and entry state": **PASS** on the two things in scope for this pass —
  the `[inference]` premise clause and the bullet's tag-clause tail. The premise clause describes
  its evidence accurately. The production command line is in fact read from the blobs: all four
  reachable production device-tree blobs (both silicon revisions in both device directories) carry
  a `/chosen` `bootargs` property, and all four are byte-identical — one distinct 539-character,
  19-token command line. Both positive premises hold in it: it carries a protected-KVM module list
  (one parameter whose value is a list of five module names) and two SMMU-under-KVM options (two
  further parameters sharing a common prefix). The negative premise holds too: no token in it switches protected mode on
  — there is no `kvm-arm.mode=` parameter of any value, in any of the four blobs.
  The overlay entries are a search scope, not where the production command line lives. All 45
  overlay entries across both device directories were parsed and searched. The production command
  line appears in none of them; it lives in `/chosen` of the production blobs. Two of the 45 do
  carry a `bootargs` property of their own, in an overlay fragment — one a development console
  overlay whose early console is a different UART type at a different address entirely, so plainly
  not a production line — and neither carries any KVM, protected-mode or SMMU token. A raw search
  of all 45 entries for KVM and protected-mode strings returns zero hits. So the clause's framing
  survives: the blobs are where the line was read, the overlays are what was searched besides, and
  the search changes none of the three premises. Worth recording for a future reader, since the
  clause does not say it: the overlay scope is not literally empty of command-line text, but what
  it holds is not the production line and not premise-relevant.
  Tag-clause placement, both bullets: correct. Quick-facts/1 ends on its tag clause — two `[DT]`
  tags, each with a parenthetical naming its tree — and carries no TODO sentence, which is within
  the format's "at most one" and is what a bullet with no `[source-observed]`, `[press]` or
  `[inference]` tag is entitled to. Quick-facts/2 ends on its tag clause — `[DT]`, `[DT]`,
  `[doc]`, `[standard]`, `[inference]` with its premises-and-derivation parenthetical — followed
  by exactly one `TODO (verify on hardware)` sentence, which contains no square brackets, so
  nothing in it can be misread as a tag. The `[source-observed]` token in the bullet sits inside
  the `[inference]` parenthetical, where it tags the premises, and not after the TODO. Neither
  bullet carries a stray tag token in its prose that would need the checker to ignore it.
  *(established pass 7, spec `e58871df`)*

- Quick-facts/3 "Silicon revisions and SoC id": **PASS** — the v1 binding patch message states both
  revision ids and their decomposition into a 16-bit product id plus a 4-bit major and a 4-bit minor
  in the exact form the bullet gives; the v4 messages state B0 is what mass-production phones carry
  and what the upstream tree targets, and that the same trees boot on EVT devices with A0 silicon.
  I diffed the two production blobs node by node with my own reader: A0 has 2778 nodes and 641
  `reg`-bearing, B0 2774 and 645. The only structural differences are the hardlockup-detector node
  (present as a PMU-flavored node with eight per-CPU children on A0, replaced on B0 by a
  core-instruction-counter node with four register-window children) and the revision child under the
  root-level SoC-compatible node, renamed A0 to B0 with the major field empty versus 1. Every other
  difference is a DVFS, energy-model, governor or frequency-vote table, plus the two chip-info
  compatibles (which change on both the device table and the DVFS table; the bullet names the DVFS
  pair). The B0 node does carry an extra window at `0x200C_0504` of `0x24` bytes and one clock input
  with no A0 counterpart, and the separately named hardlockup-watchdog node is byte-identical in
  both. No peripheral address, interrupt or clock differs anywhere in the diff.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- Quick-facts/4 "SMP topology": **PASS** — eight CPU nodes at `0x000`–`0x700` under one `cpu-map`
  cluster with eight cores; two cores compatible with the A520 and labeled after the little core's
  codename, five with the A725, one with the X4, capacities 258 / 891 / 1024 exactly; every core
  `enable-method = "psci"`; the PSCI node is `arm,psci-1.0` with `method = "smc"` and no spin-table
  anywhere. Per-core C2 idle states carry `local-timer-stop` and suspend parameter `0x40000003`; two
  cluster power domains carry `0x40010033` and group cores 2–4 and 5–7 respectively (cores 0 and 1
  attach straight to the top domain), and the top domain carries `0x40020333`. The production blob
  uses generic `arm,armv8` CPU compatibles (with a simulator-model string ahead of it, which the
  bullet does not mention and does not need to) and reserves an IPI range of SGIs 8–15 under its
  Trusty node. The MPIDR reading (core N in Aff1, Aff0 zero) follows from the values and matches the
  cpu-map ordering; the Arm architecture manual itself could not be fetched this pass.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- Quick-facts/5 "Interrupts": **PASS** — GIC distributor at `0x0588_0000` for 64 KiB and
  redistributors at `0x0590_0000` for `0x20_0000`, which over eight cores is `0x4_0000` each, four
  64 KiB frames; `#interrupt-cells = 4`; the maintenance interrupt is PPI 9 level-high; two
  PPI partitions, the first listing seven cores and the second one. I counted the aggregators
  independently: **90** nodes of the level-aggregator compatible, every one a direct child of the
  root, each with one interrupt cell and a 16-byte register window. Resolving each one's interrupt
  parent — including inheritance from the root, which is what makes this count right — gives
  **37** that reach the GIC and **53** that name another aggregator, exactly the split the bullet
  states; the 53 divide into nine naming another node of the same compatible and 44 naming a
  wide-aggregator variant. The three island aggregators are at `0x3BD6_0400` → SPI 694,
  `0x3A16_0400` → SPI 704 and `0x0D96_0400` → SPI 684, all correct. The GICv3/v4 architectural
  gloss (system-register CPU interface, redistributor wake, affinity routing, the VLPI/VSGI pages
  behind the four-frame stride) rests on an Arm document that could not be fetched; the stride
  arithmetic itself is confirmed from the tree.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- Quick-facts/6 "Debug UART": **PASS** — both changed clauses hold, and so does the rest of the
  bullet. Personality naming: across all 22 CLI blocks the `i2c@`, `uart@`, `spi@` and `i3c-master@`
  nodes share one unit address, which is the block base plus `0x1000`; measured offsets from that
  shared unit address are `0x0` (i2c, 22/22), `0x1000` (uart, 22/22), `0x2000` (spi, 22/22) and
  `0x3000` (i3c-master, 22/22) — so every personality node is named after the block's `+0x1000`
  address, which is the I2C personality's own base and is not the UART's, SPI's or I3C's. Window
  sizes are `0x100` for i2c/uart/spi and `0x2A0` for i3c-master, matching the bullet. Upstream flow:
  the flow's kernel command line appends a bare `earlycon` with no argument and its own
  `console=pstore`, and the `console=<tty>,<baud>` fragment is set only for the two previous-
  generation targets, so for this SoC no real `console=` is passed — the flow documents in place that
  this is deliberate, leaving that fragment to the bootloader, which supplies the tty and the rate
  from its own console and baud settings. The bare
  `earlycon` resolves through `stdout-path`, which the series' common `.dtsi` sets to `serial0`,
  aliased to the console UART label. The flow asks the bootloader for 3000000 via a fastboot oem
  uart config step. Rest of the bullet: base `0x0DB6_2000`, 256-byte window, `interrupts` cell tuple
  decoding to SPI 688 level-high (INTID 720), `reg-shift = 2`, `reg-io-width = 4` (so RBR/THR at
  `0x00` and LSR, 16550 index 5, at `0x14`), `clock-frequency = 200000000` and no clock handle in the
  series; `google,lga-uart` present in mainline's DesignWare UART binding in the enum whose fallback
  is `snps,dw-apb-uart`; the node is `status = "disabled"` in the series; it is the only one of the
  22 UARTs with a plain GIC `interrupts` (the other 21 use `interrupts-extended`); CLI block base
  `0x0DB6_0000`. Blob side: `uart@db61000`, compatible `goog,goog-dw-apb-uart`, same `reg` and same
  interrupt, clocks `baudclk` and `apb_pclk` with the baud clock's rate list topping out at
  200000000, both from the CPM clock controller, a reset from the LSIO-N reset bank, a power domain,
  and a `cli16_uart` pin group under the block node. Console device `ttyS0` and
  `earlycon=uart8250,mmio32,0xdb62000` with `console=ttyS0,115200n8` in the production command line.
  *(established pass 6, spec `c6807acd`; byte-identical since)*

- Quick-facts/7 "Other UARTs": **PASS** — 22 UART nodes in total, 21 besides the console. Every one
  of the 22 has `reg-shift = 2`, `reg-io-width = 4`, a `0x100` window, clock names `baudclk` and
  `apb_pclk`, one reset name and the three pin groups the bullet lists; 21 are disabled and only the
  console is enabled. Seven sit in LSIO-S from `0x3BF0_2000` to `0x3BF6_2000` under aliases 0–6,
  eight in LSIO-E from `0x3A30_2000` to `0x3A37_2000` under aliases 7–14 with 9 and 12 also aliased
  as the second and first serial ports, and six in LSIO-N from `0x0DB0_2000` to `0x0DB5_2000` under
  alias 15 and aliases 17–21 (16 is the console). All 21 interrupt through their island aggregator,
  never the GIC. No PL011-compatible node exists anywhere in either tree.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- Quick-facts/8 "Timers": **PASS** — generic timer node with PPIs 13 / 14 / 11 / 10, all level-low
  with partition cell 0 in the series; the production blob encodes the same four lines with the
  legacy CPU-mask bits set in the flags cell. Neither tree gives a counter frequency and the timer
  node has no clock. The 38.4 MHz fixed oscillator is declared in the series and twice in the blob,
  and both watchdogs — at `0x200C_4000` and `0x200C_5000`, 4 KiB each — take it as their clock. The
  flashing flow disables the watchdog from fastboot for exactly two of the three boards, the two the
  bullet names.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- Quick-facts/9 "Clocks and power": **PASS** — the CPM clock controller node has no `reg` at all,
  only a mailbox reference and power domains, which is the whole point of the bullet. The mailbox
  pair is at `0x0526_0000` on SPI 250 and `0x0526_1000` on SPI 251. The five reset banks declare
  exactly 16, 5, 45, 43 and 50 lines for HSIO-N, HSIO-S, LSIO-S, LSIO-N and LSIO-E. The power
  controller carries the stated compatible and likewise no register window. The main PMIC node
  carries the stated compatible and no `reg`; its rails are named by schematic and subsystem, with
  the big-core and mid-core rails exactly as the bullet's parenthetical gives them, and most rails
  (not quite all) carry the monitor-only flag. The SPMI controller is at `0x053F_1000` for `0x300`
  at 19 MHz, and overlay entry 12 adds the MAX77779-family PMIC, charger, fuel gauge and the
  MAX77759 Type-C controller on it. USB fixed clocks are 19.2 MHz, 250 MHz and 200 kHz. The three
  OTP shadow syscons are at `0x053D_1000`, `0x0DE2_6000` and `0x3441_F000`. The merged USB
  controller binding supplies the clock, reset and power-domain names as cited.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- Quick-facts/10 "GPIO and pinmux": **PASS** — ten island pin-control banks, every address and
  window size matching the bullet exactly, including the two-window AoC bank; each declares two GPIO
  cells and is a GPIO controller except the HSIO-S standby bank, which is neither. A UART's pin
  group is a child of its island's CLI node, whose own window is 16 bytes. No pin controller appears
  in the series or in mainline, and the v1 thread contains the exchange the bullet cites about
  upstream pin control being new work.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- Quick-facts/11 "USB": **PASS** — core at `0x0C40_0000` for `0xD060` on SPI 580 level-high, maximum
  speed super-speed, role switch with default mode peripheral, behind the first-named SMMU; the
  wrapper's three windows and their roles match the production node's own window names; the PME wake
  interrupts are SPI 597 and 598 and the merged binding names them high-speed and super-speed in
  that order. The binding's clock, reset and power-domain names are exactly as listed. The PHY
  binding's four windows and sizes match the four given, `#phy-cells` is 1 and the binding documents
  the three selector values as high-speed, super-speed and DisplayPort; the production PHY node has
  nine windows, a firmware file name and 36 OTP trim cells. Both driver paths resolve at the
  recorded mainline commit.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- Quick-facts/12 "UFS, PCIe, and the modem": **PASS** — UFS host at `0x3C40_0000` (4 KiB), top at
  `0x3C41_0000` (`0x504`) and PHY SRAM at `0x3C70_0000` (`0x1_4000`), with clocks named as given and
  behind the second-named SMMU; its interrupts are exactly SPIs 542–557 plus one aggregator line. It
  is the node the `ufs0` alias names and the device the command line names as the boot device. Two
  root complexes at `0x0C50_0000` on SPIs 568–575 and `0x3C50_0000` on SPI 524, with 1 MiB
  configuration windows at `0x4000_0000` and `0x6000_0000`. The modem compatible appears in the
  board overlays and its carve-outs sit at the three addresses given (a fourth, smaller one exists
  that the bullet does not list, which does not contradict it).
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- Quick-facts/13 "Security, IOMMU, and interconnect": **PASS** — the security core's mailbox node is
  at `0x0E01_0000` with the stated compatible; the Trusty node is the SMC variant; seven SMMU
  instances at the seven addresses given, each 256 KiB; the protected-KVM SMMU block region is at
  `0x1_0000_0000` and 4 GiB long; the coherent-mesh node carries error SPIs 71–74. Its address
  `0x1000_0000` comes from a base property rather than a `reg`, and a mesh performance-monitor node
  sits at the same address with a 32 MiB window; the bullet says "at", not "with a `reg` of", so it
  stands. The SMMUv3 specification itself could not be fetched and no value is claimed from it.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- Quick-facts/14 "Reserved memory beyond the series": **PASS** — always-on-core region at
  `0x8D20_0000` is 48 MiB; the security-core region at `0xA240_0000` is 61.6 MiB, which "about
  62 MiB" fairly describes; TPU firmware at `0x9FC0_0000` is 20 MiB; GPU firmware at `0xB9F0_0000`
  is 33 MiB; the DSP regions begin at `0xA140_0000`; the BL31 log is where the boot-chain bullet
  puts it; the three xHCI DMA pools are at `0x0901_0000`, `0x0905_0000` and `0x9700_0000`; the modem
  carve-outs are as above. The "among others" hedge and the instruction to parse the live tree are
  warranted — the container holds around forty entries.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- Quick-facts/15 "DTB runtime patching": **PASS** — same evidence as the boot-chain bullet, all of
  it located: the memory node is absent upstream and the production placeholder is 256 MiB; the
  calibration-into-the-aliased-node behavior is stated verbatim in the placeholder overlay's header
  comment; the `console=` appending is stated in the flashing repository's comment; the locking page
  states the lock state must be set in bootconfig rather than on the command line; and the ramoops
  region is where the tree puts it in both trees.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- Quick-facts/16 "DRAM extent": **PASS**, and the caveat is the right shape. DRAM base `0x8000_0000`
  confirmed; the production memory node declares `0x1000_0000`, i.e. 256 MiB, which the bullet
  correctly refuses to read as a hardware fact. I re-derived the allocation ranges independently:
  the container declares two address and two size cells, five properties in it are twelve cells long
  and one is four. The twelve-cell ones decode sensibly only as two address cells plus **one** size
  cell, giving four regions that together span `0x8000_0000`–`0x1_0000_0000` and
  `0x8_8000_0000`–`0xA_0000_0000`; under the container's declared 2+2 they would decode as three
  entries with absurd sizes. The four-cell one decodes cleanly as 2+2. So the `0xA_0000_0000`
  endpoint does rest on the 2+1 reading alone, exactly as the bullet warns, and an implementer is
  told why.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- Gotchas/1 "Google publishes no kernel for this part.": **PASS** — I fetched the project list live:
  the per-device kernel directory runs from a first entry to a last one alphabetically, the first
  and last being the two the bullet names, and there is no laguna entry anywhere on the page. The
  Build Pixel kernels page, also fetched live, contains no occurrence of "Pixel 10", "laguna" or
  "Tensor G5" while carrying thirteen for the previous generation. The third-party source page lists
  both the prebuilt repository for this SoC and, in the immediately following section, the
  monolithic kernel source repository for this Pixel generation.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- Gotchas/2 "Clocks, resets, and regulators are mailbox requests to firmware, not MMIO.": **PASS** —
  the clock controller node genuinely has no `reg`; its only bus-facing properties are a mailbox
  reference and power domains, and the reset and power-domain controllers are shaped the same way.
  The protocol is nowhere described publicly, so the advice to use what the bootloader leaves
  running is sound; the console UART is the node left enabled in the production tree.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- Gotchas/3 "GICv3-family with four interrupt cells": **PASS** — `#interrupt-cells` is 4 in both
  trees and the fourth cell is a partition phandle or zero throughout (both PPI partitions exist and
  are referenced). The GICv2-versus-v3 consequence rests on an Arm document that could not be
  fetched, but the blob's own GIC `reg` has no non-zero CPU-interface window, which is the
  observable half of the same fact.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- Gotchas/4 "Only the console UART interrupts through the GIC.": **PASS** — of the 22 UART nodes,
  exactly one carries a direct `interrupts` property and the other 21 carry `interrupts-extended`
  naming their island aggregator and a line on it. The warning that a number copied from such a node
  is an aggregator line, not a GIC SPI, is exactly right, and the aggregators' own register model is
  undocumented.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- Gotchas/5 "The console is a DesignWare 8250 at a 32-bit stride, left disabled in the DT.":
  **PASS** — series node status is disabled, `reg-shift = 2` and `reg-io-width = 4` give 16550
  indices at a 32-bit stride, and the v4 patch message states the bootloader is what enables the
  UART when the console is turned on.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- Gotchas/6 "Shipped bootloaders refuse a DTB without a `ufs0` alias": **PASS** — the cover letter
  states the bootloader treats a missing alias as a fatal error and that the flashing repository
  applies the node; the repository's Makefile compiles and applies the placeholder overlay to every
  DTB for this SoC, and the overlay's header comment states both the fatal-error behavior and the
  calibration reason. The upstream tree omits both the alias and the memory node by design.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- Gotchas/7 "Entry exception level is not published.": **PASS** — nothing in any reached authority
  states the exception level, MMU or cache state at hand-off, and the arm64 boot document fixes only
  what an Image expects of its loader. The instruction not to infer EL2 from the protected-KVM
  command line is consistent with what I found in the blobs (a protected-modules list, no switch).
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- Gotchas/8 "The production blob's node names lie about unit addresses.": **PASS** — the console
  node's name is one personality below its `reg`, and 87 nodes in the tree share this property,
  including every UART, SPI and I3C master. Trusting `reg` over the node name is the correct advice.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- Gotchas/9 "This is not the Pixel 10a's chip.": **PASS** — the v4 cover letter groups that model
  with the four preceding generations as Samsung-derived and does not say which of them it is.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- instances/lsion_cli16_uart: **PASS** — `0x0DB6_2000` in both trees; SPI 688 level-high in both, so
  INTID 720; `clocks: []` is the right encoding, because the upstream tree gives only
  `clock-frequency` and no handle while the production blob names two clocks, and the note records
  both, the size, the 32-bit stride, the aliases and the earlycon.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- instances/lsios_cli0_uart: **PASS** — `0x3BF0_2000`, LSIO-S aggregator line 0, both clocks.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- instances/lsios_cli1_uart: **PASS** — `0x3BF1_2000`, line 1.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- instances/lsios_cli2_uart: **PASS** — `0x3BF2_2000`, line 2.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- instances/lsios_cli3_uart: **PASS** — `0x3BF3_2000`, line 3.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- instances/lsios_cli4_uart: **PASS** — `0x3BF4_2000`, line 4.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- instances/lsios_cli5_uart: **PASS** — `0x3BF5_2000`, line 5.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- instances/lsios_cli6_uart: **PASS** — `0x3BF6_2000`, line 6.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- instances/lsioe_cli7_uart: **PASS** — `0x3A30_2000`, LSIO-E aggregator line 0.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- instances/lsioe_cli8_uart: **PASS** — `0x3A31_2000`, line 1.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- instances/lsioe_cli9_uart: **PASS** — `0x3A32_2000`, line 2; both the numbered and the second
  serial alias point at it.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- instances/lsioe_cli10_uart: **PASS** — `0x3A33_2000`, line 3.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- instances/lsioe_cli11_uart: **PASS** — `0x3A34_2000`, line 4.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- instances/lsioe_cli12_uart: **PASS** — `0x3A35_2000`, line 5; both the numbered and the first
  serial alias point at it.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- instances/lsioe_cli13_uart: **PASS** — `0x3A36_2000`, line 6.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- instances/lsioe_cli14_uart: **PASS** — `0x3A37_2000`, line 7.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- instances/lsion_cli15_uart: **PASS** — `0x0DB5_2000`, LSIO-N aggregator line 5.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- instances/lsion_cli_int0_uart: **PASS** — `0x0DB0_2000`, line 0.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- instances/lsion_cli_int1_uart: **PASS** — `0x0DB1_2000`, line 1; its baud clock node does indeed
  carry no rates property, unlike the console's.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- instances/lsion_cli_int2_uart: **PASS** — `0x0DB2_2000`, line 2.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- instances/lsion_cli_int3_uart: **PASS** — `0x0DB3_2000`, line 3.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*

- instances/lsion_cli_int4_uart: **PASS** — `0x0DB4_2000`, line 4.
  *(carried forward from pass 5, spec `e53e4fb3`; byte-identical since)*
