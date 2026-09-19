---
spec: tensor-g5
spec_file: tensor-g5.spec.md
spec_sha256: 0ceaac4d4b81d44abd02d6d68ff5c8c4f3105d2c73ec023404e5449e190bef19
verified: 2026-09-19
verifier: >-
  Two independent verifier subagents (Claude Opus 5 under Claude Code), fourth pass, run
  concurrently in fresh contexts. Neither was given the previous record, this repository's git
  history, nor the other's findings; each wrote its own flattened-device-tree reader rather than
  trusting any cached extraction. Pass A verified all 46 claims; pass B independently re-read the
  nine bring-up-critical ones. They agree on eight of the nine, including both readings of the
  addressing model, and disagree on one, which is recorded below as an adjudication item and left
  out of the pass/fail counts. This pass exists because the third-pass record went stale: the
  correction it proposed was applied to the spec afterwards.
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
    fetch: partial
  - name: "arm64: google: Introduce frankel, blazer, and mustang boards (v1)"
    url: https://lore.kernel.org/linux-arm-kernel/20251111192422.4180216-1-dianders@chromium.org/
    fetch: partial
  - name: Synopsys DesignWare ABP UART devicetree binding (snps-dw-apb-uart)
    url: https://www.kernel.org/doc/Documentation/devicetree/bindings/serial/snps-dw-apb-uart.yaml
    fetch: ok
  - name: Google Tensor Series G5 (Laguna) DWC3 USB SoC Controller binding (google,lga-dwc3)
    url: https://raw.githubusercontent.com/torvalds/linux/master/Documentation/devicetree/bindings/usb/google,lga-dwc3.yaml
    fetch: ok
  - name: Google Tensor G5 USB PHY binding (google,lga-usb-phy)
    url: https://raw.githubusercontent.com/torvalds/linux/17e7b8eacf4cac800a4fc89a28729df72a2dabda/Documentation/devicetree/bindings/phy/google,lga-usb-phy.yaml
    fetch: ok
  - name: Google DT platform binding (google.yaml)
    url: https://raw.githubusercontent.com/torvalds/linux/17e7b8eacf4cac800a4fc89a28729df72a2dabda/Documentation/devicetree/bindings/arm/google.yaml
    fetch: ok
  - name: Linux arm64 booting.rst
    url: https://www.kernel.org/doc/Documentation/arch/arm64/booting.rst
    fetch: ok
  - name: pixelscripts Makefile (Linaro)
    url: https://gitlab.com/LinaroLtd/googlelt/pixelscripts/-/raw/clo/main/Makefile
    fetch: ok
  - name: pixelscripts lga-ufs-placeholder.dtso (Linaro)
    url: https://gitlab.com/LinaroLtd/googlelt/pixelscripts/-/raw/clo/main/lga-ufs-placeholder.dtso
    fetch: ok
  - name: Android boot image header (source.android.com)
    url: https://source.android.com/docs/core/architecture/bootloader/boot-image-header
    fetch: ok
  - name: Android DTB and DTBO partitions (source.android.com)
    url: https://source.android.com/docs/core/architecture/dto/partitions
    fetch: ok
  - name: Android bootloader locking and unlocking (source.android.com)
    url: https://source.android.com/docs/core/architecture/bootloader/locking_unlocking
    fetch: ok
  - name: Build Pixel kernels (source.android.com)
    url: https://source.android.com/docs/setup/build/building-pixel-kernels
    fetch: ok
  - name: GrapheneOS source page
    url: https://grapheneos.org/source
    fetch: ok
  - name: android.googlesource.com project list
    url: https://android.googlesource.com/
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
  - name: Arm System Memory Management Unit Architecture Specification (IHI 0070)
    url: https://developer.arm.com/documentation/ihi0070/latest
    fetch: blocked
summary: {pass: 43, fail: 2, unverifiable: 0, gap: 0, adjudicate: 1}
---

# Verification of `tensor-g5`

Forty-six claims: Quick-facts/1-15, Gotchas/1-9, and 22 `instances:` rows. Nine were read twice by
verifiers who did not share a context.

**Two FAILs and one adjudication item.** Neither FAIL is a wrong number -- every value in both
bullets re-derived exactly. Both are sentences that generalize past what the tree supports, which is
the failure mode this spec keeps producing and the reason the addressing bullet has now been
rewritten three times.

## Adjudication item

`Quick-facts/2 "Boot chain and entry state"` -- **ADJUDICATE**, excluded from the pass/fail counts,
waiting on a person. The disagreement is over one clause, "the production command line enables
protected KVM".

- **Pass A reads it as supported.** The blob's command line carries the earlycon, console,
  boot-device and platform strings the bullet quotes, and it carries protected-KVM parameters;
  pass A took those as the command line enabling protected KVM and passed the bullet.
- **Pass B reads it as overstated.** Searching both production blobs, both overlay images and the
  second device's copies, it found protected-KVM *module* and SMMU-under-KVM options but no mode
  switch that turns protected mode on anywhere. Its reading: the options are strong evidence of a
  hypervisor and therefore of an EL2 entry, but "enables" says the command line is what turns it on,
  and nothing found says that.

Both agree the bullet's operational advice -- do not assume the level, read `CurrentEL` -- is right
and correctly hedged, so nothing bring-up depends on the outcome. What is being adjudicated is
whether the supporting clause is more definite than its evidence. Neither reading is credit or
blame until someone settles it.

## The two FAILs

`Quick-facts/1 "Addressing model"` -- **both passes failed it independently, on the same falsifier**,
found by two readers who each enumerated the tree themselves. 111 cell nodes under the fixed-layout
container inside the OTP shadow region carry a `reg` that is a byte offset and length into that
nvmem device, not a CPU-physical address, and they are not under any wrapper. Pass B adds the sharp
form: their container declares one address cell and no `ranges`, which is the same structural
signature the bullet uses two sentences earlier to argue the hardlockup windows *are* CPU-physical.
A reader applying the bullet's own rule to one of these nodes decodes a three-digit offset as a
physical address. Both passes also note the 8 cpu nodes (`reg` is an MPIDR affinity value) and the
44 graph `port@N`/`endpoint@N` nodes (21 under the wrappers, 23 outside) as further `reg` values
that are not addresses. Each pass proposes a correction below; they differ in scoping and a person
should pick, not average them.

`Quick-facts/5 "Interrupts"` -- **pass A only**; outside pass B's scope, so single-read. Everything
else in the bullet holds, including the 90 nodes carrying the level-aggregator compatible. The
clause "one GIC SPI each" does not: only 37 of the 90 present an interrupt to the GIC, and the other
53 name another aggregator as their interrupt parent. The fan-in is a tree, not one level, so an
aggregator line may have to be followed up a further level.

**No correction in this record is applied.** Applying one stales the record, and the addressing
bullet in particular has been corrected three times with each fix introducing a new defect.

## Pass A -- all forty-six claims

# Verification of `tensor-g5`

- Quick-facts/1 "Addressing model": FAIL — every placement but one re-derived exactly, and then one
  sentence over-reaches. Confirmed: the series root is 2/2 and the `soc@0` bus is 2/2 with an
  identity `ranges` and `dma-ranges` of size `0x10_0000_0000`, so the debug UART (`0x0DB6_2000`) and
  the GIC distributor (`0x0588_0000`) are CPU-physical as written; the production blob has no `soc`
  container and 410 of its 645 `reg`-bearing non-root nodes are direct children of `/` with the
  root's 2/2 cells; the USB pair and the 40 reserved-memory regions sit under containers with an
  empty `ranges;`; the early-hardlockup container declares one address cell, one size cell and no
  `ranges` at all, and its four windows — including `0x200C_0504` for `0x24` bytes — are single
  32-bit cells that nothing maps; the eight wrappers each map child 0 onto the base in their unit
  address, five with one address cell and three with two, all with one size cell, and the display
  controller's `0x20_0000` resolves to `0x0EE0_0000`; 19 MMIO nodes and 21 graph nodes sit below the
  wrappers (40 `reg`-bearing descendants in total, which is where the spec's two counts come from);
  ten nodes are `simple-bus` and the two beyond the wrappers carry an empty `ranges;`; both PCI
  windows are identity once the three-cell `phys.hi` tag is separated, and are only misread as
  translating if it is not; the nodes present in both trees carry the same addresses; DRAM begins at
  `0x8000_0000` and the placeholder is 256 MiB; the series GIC node has no `ranges` (the v3
  changelog says so in as many words) while the blob's carries an empty one. The footnote is right
  too: exactly six `alloc-ranges` properties exist in the blob, all in the reserved-memory
  container, five of them twelve cells that decode sensibly only as two address cells plus one size
  cell — giving `0x8_8000_0000`–`0xA_0000_0000` — and the sixth, on the GEM DMA region, four cells
  that decode cleanly as 2+2; the `0xA_0000_0000` endpoint does follow only from the 2+1 reading.
  Discrepancy: the summary sentence "Only nodes under the eight wrappers carry a `reg` that is an
  offset" is false for the blob. 111 cell nodes under the fixed-layout container inside the OTP
  shadow region carry a `reg` that is a byte offset plus a length into that 1152-byte nvmem device
  (the first is offset `0xB5`, length 1), not a CPU-physical address and not under any wrapper; 8
  cpu nodes carry a `reg` that is an MPIDR affinity value; and 23 further port/endpoint graph nodes
  sit outside the wrapper subtree (44 such nodes exist in the blob, only 21 of them below a
  wrapper), so the spec's "a further 21" accounts for the wrapper subtree only. A reader applying
  the sentence as written would decode 0xB5 as a physical address. Proposed correction: replace the
  sentence with one that keeps its scope explicit, e.g. "Of the `reg` values that are bus addresses,
  only those under the eight wrappers are offsets; a `reg` elsewhere in the tree may still not be an
  address at all — the 111 fixed-layout cells under the OTP shadow region are byte offsets into that
  nvmem device, the 8 cpu nodes are MPIDR values, and 44 `port@N`/`endpoint@N` nodes (21 of them
  under `sswrp_dpu`) are graph indices." Do not narrow it further than the counts support.
- Quick-facts/2 "Boot chain and entry state": PASS — the series reserves the four regions at the
  stated bases and sizes with the stated `no-map` flags, and the blob carries the same four plus the
  2 MiB EL3 log buffer at `0x8B60_0000`; the blob's command line carries the earlycon, console,
  boot-device and platform strings quoted, and enables protected KVM; the cover letter and patch 3/4
  message say the bootloader adds the memory node, that a missing `ufs0` alias is a fatal error and
  that the bootloader enables the UART and sets the baud; the flashing Makefile packs whole DTBs into
  the vendor boot image with header version 4 and erases the overlay partition; the Android pages
  confirm that header versions 3 and 4 keep the DTB in the vendor boot partition and that the
  overlay table carries per-entry id and rev; `booting.rst` states the entry contract and says
  nothing about this bootloader, which is exactly how the bullet uses it.
- Quick-facts/3 "Silicon revisions and SoC id": PASS — the v1 binding message states the two
  revisions and their ids in the same words and gives the 16-bit product id plus 4-bit major and
  4-bit minor split; the v4 patch 3/4 message says only B0 is supported and that the trees boot on
  A0 EVT devices. A full property-level diff of the two blobs shows differences only in DVFS,
  energy-model and governor tables, two chip-info compatibles, the revision child of the root-level
  compatibility node (major 0 versus 1, product id 5 in both) and the early-hardlockup node; the
  separately named hardlockup watchdog node is byte-identical; B0 does add the `0x200C_0504` window
  of `0x24` bytes and a clock input with no A0 counterpart; and no `reg`, `interrupts`,
  `interrupts-extended`, `clocks` or `clock-names` property differs on any node present in both.
- Quick-facts/4 "SMP topology": PASS — the eight cpu nodes, their compatibles, `reg` values, capacity
  numbers, enable method and power domains match; the `cpu-map` has one cluster of eight cores; the
  psci node is 1.0 with the smc conduit; the per-core C2 states carry `local-timer-stop` and the
  stated suspend parameter; the two cluster domains group cores 2–4 and 5–7 under one top domain
  with the stated parameters; the blob uses generic armv8 cpu compatibles and reserves the stated
  SGI range for the TEE. The Arm documents cited alongside could not be opened (see sources), so the
  MPIDR and PSCI wording was checked only against the trees.
- Quick-facts/5 "Interrupts": FAIL — most of the bullet re-derives exactly: the distributor window is
  64 KiB at the stated base, the redistributor region is `0x20_0000` at the stated base, which is
  `0x4_0000` per redistributor for eight cores; four interrupt cells; the maintenance interrupt is
  PPI 9; the two partitions hold the seven small/mid cores and the single big core; 90 nodes carry
  the level-aggregator compatible, every one a direct child of `/`, every one with one interrupt cell
  and a 16-byte window; and the three island aggregators are at the stated addresses with the stated
  GIC lines. Discrepancy: "one GIC SPI each" does not hold. Only 37 of the 90 present an interrupt
  to the GIC; the other 53 name another aggregator as their interrupt parent and a line on it, so
  the fan-in is a tree, not one level. (Three further nodes carry a wide-aggregator compatible and
  are not counted in the 90; all three do go to the GIC.) Proposed correction: change the
  parenthetical to say each aggregator presents a single upstream line, and add that 37 of the 90
  go straight to the GIC while 53 cascade into another aggregator, so an aggregator line may itself
  have to be followed up a further level.
- Quick-facts/6 "Debug UART": PASS — the series node's compatibles, base, 256-byte window, SPI number
  and level-high trigger, shift and io-width, and fixed clock frequency with no clock handle all
  match, as does its disabled status and the alias and stdout path; it is the only one of the 22
  UARTs with an interrupt to the GIC; the CLI block sits at the stated base with its four
  personalities at +0x1000, +0x2000, +0x3000 and +0x4000, the last with a `0x2A0` window, and all
  four nodes are named after the +0x1000 address; the blob's node carries the stated compatible,
  the same base and interrupt, both clock names from the CPM controller (the baud clock's rate list
  tops out at 200 MHz), a reset from the LSIO-N bank, a power domain and the named pin group; the
  production command line passes exactly the quoted earlycon at 115200n8 on ttyS0, while the
  flashing Makefile passes a bare earlycon, adds no console argument for this SoC, and asks the
  bootloader for 3000000.
- Quick-facts/7 "Other UARTs": PASS — 21 further UART nodes, all with shift 2, io-width 4, 256-byte
  windows, the two named clocks, a per-island reset and power domain, the three named pin groups and
  disabled status; seven in LSIO-S over the stated address range with the stated aliases, eight in
  LSIO-E over the stated range with the two secondary serial aliases where the bullet puts them and
  the logging flag on the one it names, six more in LSIO-N over the stated range with the stated
  aliases; every one of the 21 interrupts through its island's aggregator; no PL011 compatible
  appears anywhere in the blob.
- Quick-facts/8 "Timers": PASS — the generic timer node carries the four PPIs in the stated order,
  all level-low with a zero partition cell in the series, and the blob encodes the same four lines
  with the legacy CPU-mask bits set in the flags cell; no tree gives a counter frequency; the 38.4
  MHz fixed clock is present in both trees and is what clocks both watchdogs, which sit at the two
  stated addresses with 4 KiB windows; the flashing Makefile disables the watchdog from fastboot for
  exactly the two boards named.
- Quick-facts/9 "Clocks and power": PASS — the clock controller node has no `reg` at all; the mailbox
  pair sits at the two stated addresses with the stated SPI numbers, request and response in that
  order; the five reset banks carry exactly the stated line counts; a power controller node of the
  stated compatible is present; the PMIC node has the stated compatible, is reached over the same
  mailbox, and its rails are marked monitor-only and named as the bullet says, with the big-core and
  mid-core rails exactly as stated; the SPMI controller is at the stated address with the stated
  window and 19 MHz; the three USB fixed clocks are 19.2 MHz, 250 MHz and 200 kHz; the three OTP
  shadow syscons are at the three stated addresses and the first is the nvmem device the PHY trims
  are drawn from; the USB controller binding names the clock, reset and power-domain names the
  bullet cites; and the overlay entry the bullet names carries the SPMI clients.
- Quick-facts/10 "GPIO and pinmux": PASS — exactly ten island pin controllers, each at the address
  and window size the bullet gives, each a two-cell GPIO controller except the standby bank, which is
  neither; the AoC bank does carry the stated second window; a UART's pin group under its island's
  CLI node is three register/value pairs; line names and per-signal groups appear in the board
  overlay, not the SoC blob; no pin controller node exists in the series, and mainline carries no
  such binding.
- Quick-facts/11 "USB": PASS — the core node is at the stated base with the stated size, SPI and
  trigger, super-speed maximum, peripheral role-switch default, and the AMB SMMU as its IOMMU; the
  three wrapper windows are at the stated addresses and sizes with names that match the roles given;
  the two PME lines are the stated SPIs with high-speed and super-speed names; the merged controller
  binding names the two clocks, four resets and two power domains exactly as quoted and its example
  places the same core address, size and three interrupts; the PHY binding's example places the four
  stated windows with the stated sizes and defines the phy-cell selector with the three stated
  values; the production PHY node has nine windows plus a firmware file and OTP trim cells; both
  driver paths exist at the recorded mainline commit.
- Quick-facts/12 "UFS, PCIe, and the modem": PASS — the UFS node carries the stated compatible and
  the three stated windows with the stated sizes, the two stated clock names, the INF SMMU, and
  sixteen consecutive GIC SPIs over the stated range plus one aggregator line; it is the node the
  production boot-device argument names. Both root complexes carry the stated compatible at the two
  stated bases with 1 MiB configuration windows at the two stated addresses, and their GIC lines are
  the eight stated for one and the single stated one for the other. The modem compatible appears in
  the board overlays and the modem-interface carveouts sit at the three stated addresses. One
  omission, not a discrepancy: a fourth carveout of the same compatible sits at `0x0900_C000`.
- Quick-facts/13 "Security, IOMMU, and interconnect": PASS — the security-core mailbox node carries
  the stated compatible at the stated address; a TEE-over-SMC node is present; exactly seven SMMUv3
  instances exist, each 256 KiB, at the seven stated addresses under the seven stated names; the
  protected-KVM SMMU block region is 4 GiB at the stated base; the coherent-mesh node carries the
  stated compatible and its base property is the stated address, with four interrupts over the
  stated SPI range (two named error and two named fault). The Arm SMMU specification could not be
  opened (see sources), so the register-model reference was not re-derived from it.
- Quick-facts/14 "Reserved memory beyond the series": PASS — every region named is present at the
  stated address with the stated size: the always-on core at 48 MiB, the security core at just under
  62 MiB, TPU firmware at 20 MiB, GPU firmware at 33 MiB, the DSP group beginning at the stated
  address, the EL3 log, the three xHCI DMA pools, and the modem carveouts.
- Quick-facts/15 "DTB runtime patching": PASS — the cover letter and patch 3/4 message state that
  the bootloader adds the memory node, that the calibration data goes into the alias-named node and
  that the console argument is appended by the bootloader; the blob's placeholder memory node is 256
  MiB at the DRAM base; the flashing Makefile applies the alias overlay; the Android locking page
  states that the lock-state variable must be carried in bootconfig rather than on the command line;
  the ramoops region is where the series puts it.
- Gotchas/1 "Google publishes no kernel for this part.": PASS — the public project list has no
  laguna entry, and its per-device kernel repositories do run from akita to zumapro with nothing
  after; the Pixel kernel build page mentions the previous generation and never mentions Pixel 10;
  the third-party source page lists both the prebuilt repository for this family and, in the
  following section, the monolithic kernel source repository for this generation.
- Gotchas/2 "Clocks, resets, and regulators are mailbox requests to firmware, not MMIO.": PASS — the
  clock controller node has no `reg`, its children are identified only by a controller id and a
  clock id, and the peripherals reach it through the mailbox node; nothing in either tree describes
  the transaction format.
- Gotchas/3 "GICv3-family with four interrupt cells": PASS — the series GIC declares four interrupt
  cells and every interrupt specifier in both trees is four cells, the fourth being a partition
  phandle or zero; the two partitions exist. The GIC specification could not be opened.
- Gotchas/4 "Only the console UART interrupts through the GIC.": PASS — of the 22 UART nodes exactly
  one carries a GIC interrupt; the other 21 name an aggregator and a line on it, and no public
  document describes the aggregator register model.
- Gotchas/5 "The console is a DesignWare 8250 at a 32-bit stride, left disabled in the DT.": PASS —
  the series node is disabled with shift 2 and io-width 4 and a DesignWare compatible pair, and the
  patch 3/4 message says in as many words that the bootloader enables the UART when its console is
  turned on.
- Gotchas/6 "Shipped bootloaders refuse a DTB without a `ufs0` alias": PASS — the cover letter says
  the alias was removed in v3 and that the bootloader treats a missing one as a fatal error, and the
  memory node was removed for the same reason; the flashing repository's overlay header states the
  same thing and the Makefile applies that overlay to every board DTB it builds.
- Gotchas/7 "Entry exception level is not published.": PASS — `booting.rst` fixes only what a Linux
  Image expects (a non-secure entry at EL2 or EL1, MMU off, the DTB address in the first argument
  register) and states nothing about this platform's firmware; no public source in the spec's
  resources gives the level, and the protected-KVM argument on the production command line is
  consistent with but does not establish EL2.
- Gotchas/8 "The production blob's node names lie about unit addresses.": PASS — the console node's
  name and its `reg` differ by `0x1000`, and every CLI's four personality nodes are named after the
  same +0x1000 address while their `reg` values are the block base plus 0x1000, 0x2000, 0x3000 and
  0x4000.
- Gotchas/9 "This is not the Pixel 10a's chip.": PASS — the cover letter groups the Pixel 10a with
  the Pixel 6 to Pixel 9 generation of Exynos-derived Tensor parts and names no specific one.
- instances/lsion_cli16_uart: PASS — base, SPI number, INTID (32 plus the DT number), level-high
  trigger and the empty clock list all match the series node, which gives only a fixed frequency; the
  note's description of the production node — same base and interrupt, the two named clocks, the
  LSIO-N reset, a power domain and the named pin group — matches the blob, as do the shift, io-width
  and the derived LSR offset, the aliases, and the earlycon string.
- instances/lsios_cli0_uart: PASS — base and aggregator line 0 match; the aggregator's address and
  its own GIC line match; both clock names present; disabled.
- instances/lsios_cli1_uart: PASS — base and aggregator line 1 match, clocks and status as stated.
- instances/lsios_cli2_uart: PASS — base and aggregator line 2 match, clocks and status as stated.
- instances/lsios_cli3_uart: PASS — base and aggregator line 3 match, clocks and status as stated.
- instances/lsios_cli4_uart: PASS — base and aggregator line 4 match, clocks and status as stated.
- instances/lsios_cli5_uart: PASS — base and aggregator line 5 match, clocks and status as stated.
- instances/lsios_cli6_uart: PASS — base and aggregator line 6 match, clocks and status as stated.
- instances/lsioe_cli7_uart: PASS — base and aggregator line 0 match; the LSIO-E aggregator's address
  and its own GIC line match; clocks and status as stated.
- instances/lsioe_cli8_uart: PASS — base and aggregator line 1 match, clocks and status as stated.
- instances/lsioe_cli9_uart: PASS — base and aggregator line 2 match; the node carries both the
  numbered alias and the secondary serial alias named in the row; clocks and status as stated.
- instances/lsioe_cli10_uart: PASS — base and aggregator line 3 match, clocks and status as stated.
- instances/lsioe_cli11_uart: PASS — base and aggregator line 4 match, clocks and status as stated.
- instances/lsioe_cli12_uart: PASS — base and aggregator line 5 match; the node carries the numbered
  alias, the other secondary serial alias and the logging flag named in the row; clocks and status as
  stated.
- instances/lsioe_cli13_uart: PASS — base and aggregator line 6 match, clocks and status as stated.
- instances/lsioe_cli14_uart: PASS — base and aggregator line 7 match, clocks and status as stated.
- instances/lsion_cli15_uart: PASS — base and aggregator line 5 match; the LSIO-N aggregator's
  address and its own GIC line match; clocks and status as stated.
- instances/lsion_cli_int0_uart: PASS — base and aggregator line 0 match, alias, clocks and status as
  stated.
- instances/lsion_cli_int1_uart: PASS — base and aggregator line 1 match, alias, clocks and status as
  stated; its baud clock node does indeed carry no rate list, unlike its siblings'.
- instances/lsion_cli_int2_uart: PASS — base and aggregator line 2 match, alias, clocks and status as
  stated.
- instances/lsion_cli_int3_uart: PASS — base and aggregator line 3 match, alias, clocks and status as
  stated.
- instances/lsion_cli_int4_uart: PASS — base and aggregator line 4 match, alias, clocks and status as
  stated.

## Pass B -- independent second reading

The nine bring-up-critical claims.
# Verification of `tensor-g5` — independent second pass (bring-up-critical facts only)

- Quick-facts/1 "Addressing model": **FAIL** — every enumerated value re-derives correctly, but
  one absolute sentence is falsified by a placement the bullet never covers.

  What re-derived correctly, from a fresh parse of the production blob (2774 nodes, 645 of them
  carrying `reg`) and from the series SoC include:
  - Root cell counts 2/2 in both trees; the series bus container is 2/2 with a `ranges` and a
    `dma-ranges` that map child 0 to parent 0 over a 64 GiB window, so the console UART base and
    the distributor base are CPU-physical as written. Both values check out.
  - The blob has no single bus container; 410 of the 645 `reg`-bearing nodes are direct children
    of the root, including the console UART, the interrupt controller, the aggregators and the
    seven SMMU instances. "Most" is right (63 %).
  - Exactly twenty nodes declare a `ranges`; exactly ten are `simple-bus`; exactly eight of those
    translate, and the eight named in the bullet are those eight, with the one-address-cell /
    two-address-cell split and the single size cell exactly as stated. Each maps child address 0
    onto the CPU-physical base in its own unit address. The display-controller example resolves to
    the stated CPU address.
  - Nineteen MMIO nodes sit below the eight wrappers, and a further twenty-one `reg`-bearing
    descendants of those wrappers are graph port/endpoint nodes whose `reg` is an index. Both
    counts are exact, and "a further 21" correctly means *below the wrappers* — there are 44 such
    graph nodes tree-wide, 21 of them under a wrapper.
  - The two other `simple-bus` nodes carry an empty `ranges`, as stated. The two root-complex
    nodes are the only non-`simple-bus` nodes with a non-empty `ranges`, and both are identity
    once the three-cell bus tag is separated from the address; a naive read would misclassify them.
    Confirmed.
  - The early-hardlockup detector's windows sit under a parent declaring one address cell and no
    `ranges`, and their values are genuinely CPU-physical: the largest of them is a per-core stride
    off the redistributor base that lands exactly on the redistributor SGI pages, which independently
    corroborates the reading. The `0x200C_0504` window, `0x24` bytes, is present as cross-referenced.
  - The DRAM base and the placeholder memory node check out. The footnote on `alloc-ranges` is
    correct and correctly attributed: there are exactly six such properties in that container, five
    of twelve cells carrying identical values and one of four cells on the region the footnote names.
    The five decode as four windows only under two address cells plus one size cell; the four-cell
    one decodes cleanly as two plus two; and the `0xA_0000_0000` top endpoint is produced by the
    2+1 reading alone — under 2+2 the first entry's size is nonsense. The attribution is exact.
  - The interrupt-controller node in the series carries no `ranges` and the blob's carries an empty
    one. Both confirmed. Addresses agree between the trees for every node present in both that was
    checked: the console UART, both interrupt-controller windows, all four reserved regions the
    series declares, and the eight core identifiers.

  The discrepancy: **"Only nodes under the eight wrappers carry a `reg` that is an offset" is
  false.** 111 `reg`-bearing nodes in the blob — the fixed-layout cell nodes beneath the OTP-shadow
  region whose base the spec itself gives elsewhere — carry a `reg` that is a byte offset plus a
  length inside that region, not a CPU-physical address. Their container declares one address cell
  and one size cell and no `ranges`, while its own parent declares neither and the grandparent
  declares two of each: exactly the "child cell counts differ from the parent's" shape, and exactly
  the structural signature the bullet attributes CPU-physical semantics to two sentences earlier for
  the hardlockup windows. A reader applying the bullet's rules to one of these nodes reads an offset
  in the low hundreds as a CPU address. All 111 offsets fall inside the named region's window, which
  settles what they are. This class is the single largest `reg`-bearing group in the tree after the
  direct children of the root, and neither the bullet nor the extraction artifact beside the spec
  mentions it.

  Proposed correction: replace the absolute sentence with a scoped one and add the missing class —
  for example: "Among the MMIO nodes, only those under the eight wrappers carry a `reg` that is an
  offset. Two further classes of `reg` are not addresses at all: the port and endpoint graph nodes
  (44 of them tree-wide, 21 under the wrappers), whose `reg` is an index, and the 111 fixed-layout
  cell nodes under the OTP-shadow region at `0x053D_1000`, whose `reg` is a byte offset and length
  inside that region — their container declares one address cell and no `ranges`, the same shape as
  the hardlockup windows, but nothing about that shape makes a value CPU-physical; what makes the
  hardlockup windows CPU-physical is that their parent is itself a root child with no region of its
  own." Keeping the core-identifier nodes out of the rule would also help, since their `reg` is an
  affinity value.

  Second, smaller discrepancy on the same bullet: the parenthetical attributing the series
  interrupt-controller's missing `ranges` to a named earlier review round is correct — the change
  is listed in the series' own changelog, with the reviewer named and the reason given — but that
  is a documentation-class fact and the bullet's tag clause offers only device-tree tags. Proposed
  correction: add the series cover letter / patch message to this bullet's tag clause, or drop the
  parenthetical.

- Quick-facts/2 "Boot chain and entry state": **FAIL** on the definiteness of one clause; every
  other element re-derived correctly.

  Correct: the EL3-runtime log buffer is reserved at the stated base with the stated size and is
  marked no-map; all four reserved regions the series declares match in base, size and no-map
  status, and the ramoops region is correctly the one without no-map; the bootloader adding the
  memory node, refusing a tree without the storage alias, and writing calibration into that node
  are each stated in the series' own changelog, cover letter and the overlay's header comment; the
  bootloader enabling the console only when its console is turned on, and the baud never being
  fixed in the tree, are stated in the patch message; the bootloader appending the console argument
  is stated in the flashing scripts; the production command line carries the four strings quoted,
  in that form; the upstream flow does pack whole trees into the vendor boot image with the stated
  tool and header version and does erase the overlay partition; the boot-image-header page does
  place the tree in the vendor boot image for that header version, and the overlay-partition page
  does document a table whose entries carry board id and revision fields that the bootloader checks.

  The discrepancy: the closing TODO says "the production command line enables protected KVM". It
  does not. The command line carries protected-KVM *module* and SMMU-under-KVM options; no mode
  switch that turns protected mode on appears anywhere in either production blob, either overlay
  image, or the second device's copies — searched for explicitly. The options are strong evidence
  that the hypervisor is in use, and therefore evidence for an EL2 entry, but "enables" says the
  command line is what turns it on, which the evidence does not support. Note that the bullet's
  actual operational advice — do not assume the level, read the current exception level — is right
  and is correctly hedged; this is a definiteness failure on the supporting clause only.

  Proposed correction: "the production command line carries protected-KVM options (a protected-
  modules list and SMMU-under-KVM parameters), which implies a hypervisor entry at EL2, but no
  mode switch appears in any public blob, so read `CurrentEL` before assuming it."

- Quick-facts/6 "Debug UART": **PASS** — every element re-derived. The series node's compatible is
  the vendor string with the DesignWare fallback, and the vendor string is present in mainline's
  DesignWare APB UART binding at the pinned commit, in the enum whose branch ends with that
  fallback. Base, 256-byte window, interrupt kind and number, the level-high flag and the trailing
  partition cell, the register shift and I/O width, and the fixed clock frequency with no clock
  handle all match the series file. The derived INTID is the number plus 32. The 16550 index at the
  stated shift puts the line-status register at the stated offset and the transmit/receive holding
  register at zero. It is the only one of 22 UART nodes in the blob using a direct interrupt
  property; the other 21 use extended interrupts naming one of three aggregators. The block base and
  the four personality offsets, including the I3C window size, are exactly as stated, and every
  personality node in that block, and in all 22 blocks, is named after the block base plus 0x1000
  regardless of its own base. The series leaves the node disabled, and the series' common include
  does set both the first serial alias and the standard-output path to it. In the blob, the node's
  clock names, the baud clock's rate list topping out at the stated frequency, the reset from the
  island bank, the power domain and the pin group all resolve to nodes named as the spec says. The
  production command line's console device and early-console string match. The flashing scripts do
  pass a bare early-console argument for this target (the console argument is empty for anything but
  the two older boards) and do ask the bootloader for the higher baud. No PL011 compatible exists
  anywhere in the blob.

  One nit, not a failure: the blob's chosen node has no standard-output path, only the alias. The
  bullet's sentence is scoped to the series, where both exist, so it is correct as written; the
  instances row states it unscoped.

- Gotchas/4 "Only the console UART interrupts through the GIC": **PASS** — 22 UART nodes, one with a
  direct interrupt property and 21 with extended interrupts naming an aggregator and a line.

- Gotchas/5 "The console is a DesignWare 8250 at a 32-bit stride, left disabled in the DT": **PASS**
  — register shift 2 and I/O width 4 in the series node, status disabled, and the patch message
  states the bootloader is what enables it.

- Gotchas/6 "Shipped bootloaders refuse a DTB without a `ufs0` alias": **PASS** — the cover letter
  states the alias was removed in the named review round and that its absence is a fatal bootloader
  error pending a bootloader release, and the flashing repository's placeholder overlay header
  states the same reason; the flashing Makefile applies that overlay to every board tree it builds.

- Gotchas/7 "Entry exception level is not published": **PASS** — nothing in any cited authority
  states the level, the MMU/cache state, or the register contract for this bootloader, and the
  kernel's arm64 boot document states only what an Image expects. The caution is correctly scoped.

- Gotchas/8 "The production blob's node names lie about unit addresses": **PASS** — verified for all
  22 UART nodes and for all four personalities of the console's block.

- instances/lsion_cli16_uart: **PASS** — base, interrupt kind/number/derived INTID/trigger, empty
  clock list, and the debug-console role all match; every assertion in the row's note re-derived,
  with the one nit above (the standard-output path exists in the series tree, not in the blob).

## Notes for the orchestrator

- The extraction artifact beside the spec was read as a claim and re-derived from the blob with a
  parser written for this pass. Its totals reproduce exactly: node count, number of nodes declaring
  a `ranges`, number of `simple-bus` nodes, how many of those translate, the count of `reg`-bearing
  descendants of translating nodes and its split into MMIO windows and graph indices, and the
  identity classification of the two root complexes. Its blob hash matches the file on disk. Its
  scope, however, is *translating* nodes and direct root children, so it does not cover the class
  that falsifies the bullet either.
- Two things in that artifact are worth the orchestrator's attention, both outside this pass's
  scope. Its header records an absolute home-directory path from the machine that produced it,
  which does not belong in a public repository. And one of its section headings refers to "the
  claim under adjudication", which disclosed to this verifier that an earlier round adjudicated
  something about the aggregator count — a bullet outside this scope, so no in-scope reading was
  affected, but the artifact is not as neutral as its name suggests.
- No source code, device-tree text, or firmware text is reproduced here; values and structure only.
