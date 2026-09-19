---
spec: tensor-g5
spec_file: tensor-g5.spec.md
spec_sha256: 18100d5dff76cce373f24ed4594dd00a6928732cb0ce948e5d48c1ca830f02b6
verified: 2026-09-18
verifier: >-
  Claude Opus 5 (1M context) under Claude Code, orchestrating spec-verifier. Two independent
  subagents with fresh contexts: a full-spec verifier over all 46 claims, and a second verifier
  over the bring-up-critical facts (addressing model, boot chain and entry state, debug UART) per
  the two-verifier rule. Neither saw the author's report, this conversation, or the other's work.
sources:
  - name: linux-mainline
    url: https://github.com/torvalds/linux
    commit: 17e7b8eacf4cac800a4fc89a28729df72a2dabda
    fetch: ok
  - name: laguna-kernel-prebuilts
    url: https://github.com/GrapheneOS/device_google_laguna-kernels_6.6
    commit: 80c104d7e5591ebc3cd413f54b076d972484ff0b
    fetch: ok
  - name: "Add Laguna/Tensor G5 SoC and Frankel, Blazer & Mustang boards (v4)"
    url: https://lore.kernel.org/all/20260918-contrib-pg-pixel10-initial-dts-v4-0-745eaca28b1a@linaro.org/
    fetch: ok
    fetch_via: "/raw and t.mbox.gz with a Wget user agent"
  - name: "arm64: google: Introduce frankel, blazer, and mustang boards (v1)"
    url: https://lore.kernel.org/linux-arm-kernel/20251111192422.4180216-1-dianders@chromium.org/
    fetch: ok
    fetch_via: "as above"
  - name: pixelscripts Makefile (Linaro)
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
  - name: Build Pixel kernels (source.android.com)
    url: https://source.android.com/docs/setup/build/building-pixel-kernels
    fetch: ok
  - name: android.googlesource.com project list
    url: https://android.googlesource.com/
    fetch: ok
  - name: "Arm architecture documents (IHI 0069, IHI 0070, DEN 0022, DDI 0487, 102484, 107652, 102517)"
    url: https://developer.arm.com/documentation/
    fetch: blocked
summary: {pass: 41, fail: 4, unverifiable: 0, gap: 0, adjudicate: 1}
---

# Verification of `tensor-g5`

First end-to-end run of `spec-verifier` against this spec. 46 claims: 15 Quick-facts, 9 Gotchas,
22 `instances` rows. Both verifiers re-decompiled the production DTBs themselves from the `.dtb`
files and confirmed their sha256 values against the spec's `resources` note; the full verifier also
confirmed that the GrapheneOS ref `17` resolves to the commit the note names.

- Quick-facts/1 "Addressing model": ADJUDICATE — **the two verifiers disagree; both readings are
  recorded and the claim is excluded from the pass/fail counts until a person settles it.** A
  disagreement means the two readers could not settle the question between them; it does not
  establish that the spec is wrong. If adjudication finds the spec wrong, or finds it stated more
  definitely than its evidence supports, that becomes a FAIL on the merits and this line is
  rewritten.
  Agreed and passing in both readings: root 2/2 cells; the `soc@0` identity `ranges`/`dma-ranges`
  spanning `0x0`–`0x10_0000_0000`; the debug UART base `0x0DB6_2000`; the GIC distributor base
  `0x0588_0000`; the production memory placeholder at `0x8000_0000`, `0x1000_0000` long; and the
  reserved-memory `alloc-ranges` reaching `0x9_8000_0000` plus `0x8000_0000`.
  *Full verifier (FAIL):* the spec says the production blob "has no bus node at all: every peripheral
  is a child of `/` with a 64-bit `reg`". The blob carries ten `simple-bus` nodes, and seven of them
  translate — each `sswrp` wrapper declares one address and one size cell with a non-identity
  `ranges` window, so a child `reg` under one is a block offset, not a CPU-physical address. The DMA
  wrappers nest the same way. Proposed correction: "the production blob has no single `soc` bus: most
  peripherals are children of the root with a 64-bit `reg`, but seven `sswrp` wrappers and a few DMA
  wrappers are translating `simple-bus` nodes whose children carry block offsets."
  *Second verifier (PASS):* read the root as 2/2 with no `ranges` and every peripheral a direct child
  of `/` with a 64-bit `reg`, and found UART, GIC and all four series reservations at identical
  addresses in both trees — not reaching the `sswrp` wrappers.
  Both verifiers independently flagged the same secondary defect: "The GIC node declares no
  `ranges`." holds for the series tree (the v4 changelog records its removal in v3) but is false of
  the production blob, whose interrupt-controller node carries an empty `ranges`. The sentence
  follows two sentences about the production blob, so which tree it means is ambiguous. Proposed
  correction: "the series GIC node declares no `ranges` (removed in v3 review); the production blob's
  carries an empty, identity `ranges`."
- Quick-facts/2 "Boot chain and entry state" (two verifiers, agreed): PASS — the four series
  reserved-memory regions match by base, size and `no-map` (ramoops `0x9520_0000`/4 MiB; bootloader
  log `0x9560_0000`/1 MiB; GSA log `0xA61B_0000`/16 KiB; ABL `0xBE00_0000`/16 MiB); the BL31 log
  buffer at `0x8B60_0000` spanning 2 MiB is in the blob; the blob command line carries the earlycon,
  console, boot-devices and platform strings as quoted, plus the protected-KVM module list the TODO
  refers to. The Android pages support the v3/v4 split (the dtb fields left the boot image) and the
  dt table with per-entry `id` and `rev`. The pixelscripts Makefile builds with header version 4 with
  a dtb image passed into the vendor boot image, and erases `dtbo`. `booting.rst` is the entry
  contract (x0 = physical address of the DTB, MMU off, non-secure EL2 or EL1) and does not describe
  this bootloader, as the spec states.
- Quick-facts/3 "Silicon revisions and SoC id": FAIL — the id scheme is exact: the v1 binding message
  states the A0 and B0 ids and the split into a 16-bit product id plus a 4-bit major and 4-bit minor
  revision, and the v4 messages state only B0 is targeted while the tree also boots on A0 EVT
  devices. The chip-info compatibles differ as described. But the closing claim that "no address,
  interrupt, clock, or topology value differs" is falsified by a direct diff of the two decompiled
  blobs: the hardlockup-detector node is restructured (different compatible, child nodes instead of
  flat properties), the B0 version gains a clock input and a register window at `0x200C_0504` of
  `0x24` bytes that has no counterpart in A0, and the chip-info `major` field differs (0 versus 1).
  Proposed correction: "the two production blobs differ in DVFS and energy-model tables, chip-info
  compatibles and the `major` revision field, and in the hardlockup-detector node, which B0
  restructures and gives an extra register window and clock; no peripheral address, interrupt or
  clock differs."
- Quick-facts/4 "SMP topology": PASS — eight cpu nodes at the stated unit addresses (`0x000`…`0x700`,
  index << 8) with the stated core compatibles (two `arm,cortex-a520`, five `arm,cortex-a725`, one
  `arm,cortex-x4`); capacity 258 / 891 / 1024; `enable-method = "psci"` on every core and no
  spin-table in either tree; the psci node at `arm,psci-1.0` with `method = "smc"`, which the second
  verifier confirmed independently in the production blob; per-core C2 idle states carrying
  `local-timer-stop` and suspend parameter `0x40000003`; cluster domains covering cores 2–4 and 5–7
  with `0x40010033` under a top domain with `0x40020333`. The blob's cpu nodes use generic armv8
  compatibles and its Trusty node reserves an IPI range of SGIs 8–15. The Aff1 reading of the `reg`
  values follows from the MPIDR layout; DDI 0487 itself was not opened (Arm portal blocked, and the
  spec records it as such).
- Quick-facts/5 "Interrupts": PASS — distributor base `0x0588_0000` and 64 KiB window; redistributor
  base `0x0590_0000` and `0x20_0000` window (`0x4_0000` for each of eight cores); four interrupt
  cells; maintenance interrupt on PPI 9 level-high; two partitions of seven and one core. Identical
  in both trees, and both verifiers read the three `google,level-gia` aggregators the same way:
  16-byte windows, one interrupt cell, LSIO-S `0x3BD6_0400` → SPI 694, LSIO-E `0x3A16_0400` → SPI
  704, LSIO-N `0x0D96_0400` → SPI 684. IHI 0069 was not opened; the four-frame redistributor reading
  is consistent with the window size.
- Quick-facts/6 "Debug UART": FAIL — **both verifiers failed this bullet independently, on the same
  two defects. Highest-confidence finding in the set.**
  What checks out in both readings: node name and label `lsion_cli16_uart`, base `0x0DB6_2000`, the
  256-byte window, interrupt `GIC_SPI 688` level-high (INTID 720), `reg-shift = <2>` and
  `reg-io-width = <4>`, `clock-frequency = <200000000>` with no clock handle in the public tree,
  `status = "disabled"`, the `serial0` alias and `stdout-path`, the blob node at the same base and
  interrupt with the two named clocks from the CPM controller, a reset from the LSIO-N bank, a power
  domain and the cli16 pin group, the block base `0x0DB6_0000`, LSR at index 5 << 2 = `0x14`, the
  mainline binding carrying `google,lga-uart` in the enum whose second item is `const:
  snps,dw-apb-uart`, and patch 3/4's statement that the bootloader enables the UART when its console
  is on and never hardcodes the baud.
  (a) **Personality layout is wrong.** The spec places the I2C, SPI and I3C personalities all at
  `+0x1000` and the UART at `+0x2000`. Both verifiers read the blob for CLI block 16 as I2C
  `+0x1000`, UART `+0x2000`, SPI `+0x3000`, I3C `+0x4000` (window `0x2A0`), and each independently
  confirmed the same layout on three other CLI blocks — so the bullet's closing "every other CLI
  follows the same layout" is correct while the enumeration is not. The spec's grouping is true only
  of the *node names*. Proposed correction: "…the CLI block sits at `0x0DB6_0000`, its I2C
  personality at `+0x1000`, the UART at `+0x2000`, SPI at `+0x3000` and the I3C master at `+0x4000`;
  every personality node is named after the `+0x1000` address."
  (b) **`earlycon` misattributed.** The spec says `earlycon=uart8250,mmio32,0xdb62000` is "what the
  production command line and the upstream flow both pass". The production command line does carry
  it; the pixelscripts command line adds a bare `earlycon` with no argument for this target, the
  explicit console line being guarded to the two older boards. A recursive grep of the whole
  pixelscripts checkout for `uart8250` returns nothing — the only argumented `earlycon=` strings
  there are Pixel 6 / Exynos examples in its notes and README. Proposed correction: "…the production
  command line passes `earlycon` with the explicit mmio32 argument and that base, while the upstream
  flow passes a bare `earlycon` and lets the DT supply the console, and asks the bootloader for
  3000000 baud." The `instances:` note is unaffected — it states the earlycon string without
  attributing it to the upstream flow.
- Quick-facts/7 "Other UARTs": PASS — twenty-one further UART nodes, all at the stated bases, all
  with shift 2, width 4 and 256-byte windows, all with the two named clocks, a per-island reset and
  power domain and default/sleep/cli pin group names, all disabled, all routed through their island
  aggregator. The alias table gives uart0 through uart21 exactly as the spec groups them, with uart9
  and uart12 also aliased serial2 and serial1 and uart12 carrying the logging flag. No PL011 exists
  in either tree (the primecell matches in the blob are CoreSight and PL330 DMA blocks).
- Quick-facts/8 "Timers": PASS — the armv8 timer node carries PPIs 13, 14, 11 and 10, all level-low
  with a zero partition cell, in the stated order; the blob encodes the same four lines. The blob's
  38.4 MHz fixed clock is the clock input of both watchdogs, which sit at the two stated bases with
  4 KiB windows, and the upstream flow disables the watchdog from fastboot for exactly the two named
  boards. Neither tree gives a counter frequency, as the spec says. Citation nuance recorded: the
  `osc` node is declared in the SoC include but its 38.4 MHz value is set in the common board
  include; this bullet cites only the SoC file while the clocks bullet cites both.
- Quick-facts/9 "Clocks and power": PASS — the series declares the one fixed clock and the UART's
  fixed frequency. The blob's clock controller has the stated compatible, no register window and a
  mailbox reference; the mailbox pair sits at the two stated bases with request and response lines
  250 and 251; the five reset banks carry exactly 16, 5, 45, 43 and 50 lines for HSIO-N, HSIO-S,
  LSIO-S, LSIO-N and LSIO-E; the power controller has the stated compatible. The PMIC node has the
  stated compatible, reaches the same mailbox, and its rails are marked monitor-only with the
  big-core and mid-core rails named as the spec says. The SPMI controller is at the stated base with
  a `0x300` window and a 19 MHz frequency, and dtbo entry 12 carries the MAX77779 PMIC, fuel gauge
  and the MAX77759 Type-C controller. The three USB fixed clocks are 19.2 MHz, 250 MHz and 200 kHz.
  The three OTP shadow syscons exist at the three stated bases and the chip-info node reads its
  fields from them.
- Quick-facts/10 "GPIO and pinmux": PASS — all ten banks match by compatible, base and window size,
  including the AoC bank's second window; nine are GPIO controllers with two cells and the HSIO-S
  standby bank is not, exactly as the spec says. A UART pin group is three register entries under
  its island's CLI node. Neither the series nor mainline carries a pin controller, and the v1 thread
  carries the exchange the spec cites (the submitter says Laguna will need new pinctrl and clock
  drivers; the pinctrl maintainer remarks on the new pin control).
- Quick-facts/11 "USB": PASS — the blob places the core at the stated base with the stated window and
  interrupt 580, maximum speed super-speed, a role switch defaulting to peripheral, behind the `amb`
  SMMU; the wrapper node's three windows and sizes are exactly as written, with wake interrupts 597
  and 598 named for the high-speed and super-speed aggregates. The merged controller binding lists
  the two clock names, four reset names and two power-domain names as written and its example uses
  the same base, window and three interrupt numbers. The PHY binding's example places the four
  windows and sizes exactly as the spec lists them, names them core / TCA / USB2 core / top, fixes
  one phy cell and documents 0, 1, 2 as high-speed, super-speed, DisplayPort. The production PHY
  node has nine windows plus a firmware file name and OTP trim cells. Both driver paths resolve at
  the pinned commit; the PHY driver is at the flat path the spec gives (the nested `google/` path is
  404 there).
- Quick-facts/12 "UFS, PCIe, and the modem": PASS — the UFS node has the stated compatible, its
  first three windows are exactly the three listed, its clock names are the two given, it sits
  behind the `inf` SMMU, its lines are 542 through 557 plus one aggregator line, and it is the boot
  device named on the command line. Both root complexes have the stated compatible and bases, with
  lines 568–575 and 524, and 1 MiB configuration windows at the two stated addresses. The modem
  compatible appears in dtbo entry 12 and the three modem carveouts are at the three stated bases.
- Quick-facts/13 "Security, IOMMU, and interconnect": PASS — the security-core mailbox node has the
  stated compatible and base; a Trusty node sits over SMC; all seven SMMU instances carry the v3
  compatible and 256 KiB windows at exactly the seven bases listed; the protected-KVM region is at
  `0x1_0000_0000` and 4 GiB long; the mesh node has the stated compatible, a base property of
  `0x1000_0000` and four error lines 71 through 74. IHI 0070 was not opened; recorded: it is cited
  by document id but is the one Arm document not also listed in the spec's `docs` block.
- Quick-facts/14 "Reserved memory beyond the series": PASS — every region named matches the blob by
  base and size: the always-on-core region (48 MiB), the security-core region (about 62 MiB), TPU
  firmware (20 MiB), GPU firmware (33 MiB), the DSP regions beginning at the stated base, the BL31
  log, the three xHCI pools at the three stated bases, and the modem carveouts.
- Quick-facts/15 "DTB runtime patching": PASS — the cover letter and patch 3/4 state that the
  bootloader adds the memory node (which is why the series dropped it), that a missing `ufs0` alias
  is a fatal error and the bootloader writes calibration into that node, and that the bootloader
  adds the console argument when its console is on. The blob's placeholder memory node is 256 MiB.
  The Android locking page states the lock state must reach the kernel through bootconfig rather
  than the command line. The series ramoops region is where the spec says. Both verifiers agree.
- Gotchas/1: FAIL — on the citation, not the substance. The substance was confirmed independently:
  the public project list on the Google source host has no `laguna` entry at all (its per-device
  kernel list runs akita…zumapro and stops), and the Build Pixel kernels page's device table ends at
  the previous generation with no Pixel 10 row. But the bullet's tag clause names a "GrapheneOS
  source page" and an "Android Build Pixel kernels page", and neither is an entry in the spec's
  `docs` block nor a document id, so neither citation can be located from the spec alone. Proposed
  correction: add both pages to `resources.docs` with their URLs and a `verified` date
  (`https://source.android.com/docs/setup/build/building-pixel-kernels`, and the GrapheneOS page
  actually relied on), and point the parenthetical at those entries.
  Cross-reference: the `pixel10` record's Quick-facts/7 FAIL bears on this bullet's substance — the
  GrapheneOS source page does list a kernel *source* repository for this generation.
- Gotchas/2: PASS — the blob's clock controller genuinely has no register window and reaches the
  power manager through a mailbox, as do the reset banks, the power controller and the PMIC; the
  protocol appears nowhere in either public tree, so the TODO is correctly placed. The console UART
  is the one left enabled in the blob. The second verifier independently resolved the mailbox handle
  to the request/response pair at SPIs 250 and 251. Both verifiers agree.
- Gotchas/3: PASS — the interrupt controller declares four cells on `arm,gic-v3` in both trees and
  the fourth cell is the partition selector, with two partitions declared; a three-cell parser would
  misread every specifier. IHI 0069 was not opened. Both verifiers agree.
- Gotchas/4: PASS — exactly one UART node carries a direct distributor interrupt; the other
  twenty-one carry an extended specifier naming an island aggregator and a line on it, and those
  line numbers overlap heavily across islands, so reading one as a distributor line would be wrong.
  The second verifier independently enumerated all 22 UART nodes with interrupt parents resolved and
  reached the same count (7 LSIO-S, 8 LSIO-E, 7 LSIO-N including the console). Both verifiers agree.
- Gotchas/5: PASS — the series node is disabled, the compatible pair is the Google one falling back
  to the DesignWare one, the width and shift make the registers 32-bit at a four-byte stride, and
  patch 3/4 states the bootloader is what turns the line on. Both verifiers agree.
- Gotchas/6: FAIL — on one of two citations. The v4 cover letter states plainly that the bootloader
  treats a missing `ufs0` alias as a fatal error, that the memory node is added by the bootloader,
  and that the flashing scripts apply the alias; the pixelscripts tree confirms it with an overlay
  whose own header comment says the same and a rule that merges it into each board blob. But the
  bullet cites a "pixelscripts README", which contains no mention of the alias, the UFS node or the
  memory node, and which is not an entry in the spec's `docs` block. Proposed correction: change the
  second citation to the pixelscripts Makefile, which is already a `docs` entry, or name the UFS
  placeholder overlay in that repository. **Both verifiers flagged this citation independently**; the
  second verifier passed the claim on the cover letter's support alone while recording the same
  misdirection.
- Gotchas/7: PASS — verified as a negative. Nothing in either tree, in the series messages or in the
  Android pages states the exception level, MMU or cache state at hand-off; `booting.rst` permits
  either EL1 or EL2 and fixes only what the kernel Image requires, which is what the bullet claims
  of it. The blob's command line does enable protected KVM, which is why the bullet warns against
  inferring the level from it. The second verifier re-established the negative independently across
  all nine v4 thread messages, the v1 thread, the pixelscripts README and notes and the three
  Android pages, and identified the one log printing "All CPU(s) started at EL2" as Pixel 6 material
  (its machine-model line names Oriole DVT and its command line is the Exynos early console), not a
  Tensor G5 log.
- Gotchas/8: PASS — the console node's name and its register base differ by `0x1000` in the blob, and
  every CLI's UART node is named for the block's first personality address while its register base is
  one window higher; the SPI and I3C nodes are named the same way. Both verifiers agree, each
  spot-checking a different set of blocks.
- Gotchas/9: PASS, with a precision caveat — the v4 cover letter states that the previous four Tensor
  generations, in the phones through the previous generation and in the Pixel 10a, were offshoots of
  the Samsung line and that this SoC is entirely in-house; the v1 binding message repeats that the
  previous generation was such an offshoot while this one is not. The cover letter does not name the
  Pixel 10a's generation as the fourth — that is an inference from the enumeration's ordering. The
  load-bearing claim, that the Pixel 10a is not this chip, is directly supported. Consider softening
  to "an Exynos-derived Tensor of the earlier generations".
- instances/lsion_cli16_uart: PASS — base, the direct distributor line 688 with the resulting INTID
  720 and the level trigger, and the empty clock list all match: the series node gives a fixed
  frequency and no clock handle, so `[]` with the blob's names in the `note` is what the format asks
  for. Every statement in the note checks out against both trees. Verified independently by both
  verifiers, clause by clause.
- instances/lsios_cli0_uart: PASS — base and extended line 0 on the LSIO-S aggregator, whose own base
  and distributor line 694 match the note, and both clock names.
- instances/lsios_cli1_uart: PASS — base, extended line 1 on the same aggregator, both clock names.
- instances/lsios_cli2_uart: PASS — base, extended line 2 on the same aggregator, both clock names.
- instances/lsios_cli3_uart: PASS — base, extended line 3 on the same aggregator, both clock names.
- instances/lsios_cli4_uart: PASS — base, extended line 4 on the same aggregator, both clock names.
- instances/lsios_cli5_uart: PASS — base, extended line 5 on the same aggregator, both clock names.
- instances/lsios_cli6_uart: PASS — base, extended line 6 on the same aggregator, both clock names.
- instances/lsioe_cli7_uart: PASS — base and extended line 0 on the LSIO-E aggregator, whose own base
  and distributor line 704 match the note, and both clock names.
- instances/lsioe_cli8_uart: PASS — base, extended line 1 on the same aggregator, both clock names.
- instances/lsioe_cli9_uart: PASS — base, extended line 2 on the same aggregator, both clock names,
  and the serial2 alias the row records.
- instances/lsioe_cli10_uart: PASS — base, extended line 3 on the same aggregator, both clock names.
- instances/lsioe_cli11_uart: PASS — base, extended line 4 on the same aggregator, both clock names.
- instances/lsioe_cli12_uart: PASS — base, extended line 5 on the same aggregator, both clock names,
  the serial1 alias and the logging flag the row records.
- instances/lsioe_cli13_uart: PASS — base, extended line 6 on the same aggregator, both clock names.
- instances/lsioe_cli14_uart: PASS — base, extended line 7 on the same aggregator, both clock names.
- instances/lsion_cli15_uart: PASS — base and extended line 5 on the LSIO-N aggregator, whose own
  base and distributor line 684 match the note, and both clock names.
- instances/lsion_cli_int0_uart: PASS — base, extended line 0 on the same aggregator, both clock
  names.
- instances/lsion_cli_int1_uart: PASS — base, extended line 1 on the same aggregator, both clock
  names, and its baud clock node indeed lists no rates while the console's lists one.
- instances/lsion_cli_int2_uart: PASS — base, extended line 2 on the same aggregator, both clock
  names.
- instances/lsion_cli_int3_uart: PASS — base, extended line 3 on the same aggregator, both clock
  names.
- instances/lsion_cli_int4_uart: PASS — base, extended line 4 on the same aggregator, both clock
  names.

## Process notes

Not verdicts; they concern the spec's format use and this run's mechanics.

1. **Aggregator `parent` naming.** The `instances:` rows name the aggregators `lsios_level_aggr_4`,
   `lsioe_level_aggr_4`, `lsion_level_aggr_4`. Labels do not survive into a decompiled blob, so
   these correspond to node names with an `-intr` suffix dropped. The identification is unambiguous;
   worth a one-line note in the spec so the next reader does not search for a label that is not
   there.
2. **`[standard]` on DT bindings.** Quick-facts/6, /9 and /11 tag kernel device-tree binding
   documents `[standard]`. By the format's own definition those are a project's published
   documentation, i.e. `[doc]`. The checker does not catch it (the parenthetical is present and the
   `docs` entries exist), but the class is arguably wrong on three bullets.
3. **`alloc-ranges` cell parse.** The blob's `alloc-ranges` property under `reserved-memory`
   (declared 2/2 cells) parses sensibly only as address-2 / size-1 entries, giving four well-formed
   entries ending at `0xA_0000_0000`. The spec's stated span is right under any reading, but the
   property itself looks malformed in the vendor tree. Both verifiers noticed this independently.
4. **Leak scan: clean.** Full verifier: against `linux/drivers`, the v4 series tree and the
   decompiled blob — 0 shared token runs, 0 ALL-CAPS, 18 lowercase identifiers, all device-tree node
   labels (the `instances/<name>` keys this format requires) plus the vendor name "DesignWare";
   re-run with those whitelisted, exit 0. Second verifier: against ten files including its own
   decompile, the series DT directory, the pixelscripts Makefile and README, the mainline UART
   binding and `booting.rst` — 0 shared token runs, 0 ALL-CAPS, two lowercase hits
   (`lsion_cli16_uart`, a required record key, and `LinaroLtd`, a public URL path segment). Neither
   verifier read driver or firmware C source this pass: device trees, a binding YAML, kernel
   documentation, mailing-list messages, a Makefile and vendor documentation pages only.
   The orchestrator then scanned **this record** against the cache's `linux/`, `lore/` and the
   verifier scratch trees: `FINDINGS - review required`, 0 shared runs, 18 high-signal identifiers
   and 1 ALL-CAPS. Reviewed one by one and cleared:
   - seventeen `ls{ios,ioe,ion}_cli*_uart` hits are device-tree node labels, and are the
     `instances/<name>` keys this record format requires — they cannot be removed without breaking
     the format;
   - `DesignWare` is a vendor name, matched in a driver file only because the vendor is named there
     too; the record uses it as the IP family's name, which the spec's own `[standard]` tag needs;
   - `GIC_SPI` (ALL-CAPS) is a device-tree binding macro from the published interrupt-controller
     bindings — standard nomenclature, which is the case the scanner's own message says belongs in
     a whitelist, not a failure.
   All are device-tree or standard nomenclature, which the format explicitly admits as `[DT]`
   hardware description. No driver or firmware source is reproduced. Nothing was rewritten to
   satisfy the scanner; the findings are recorded here as judged.
