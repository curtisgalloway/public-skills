---
spec: tensor-g5
spec_file: tensor-g5.spec.md
spec_sha256: d159e12f6071b6c18b5488b4d52b8fe369d3a5a4ff6543470a18307f49eb0c86
verified: 2026-09-18
verifier: >-
  Claude Opus 5 (1M context) under Claude Code, orchestrating spec-verifier. Second pass, after the
  corrections the first pass proposed were applied. Two independent subagents with fresh contexts: a
  full-spec verifier over all 46 claims, and a second verifier over the bring-up-critical facts
  (addressing model, boot chain and entry state, debug UART) per the two-verifier rule. Neither saw
  the author's report, the previous record, this conversation, or the other's work; both were told a
  correction that overshot is as much a FAIL as the original defect.
sources:
  - name: linux-mainline
    url: https://github.com/torvalds/linux
    commit: 17e7b8eacf4cac800a4fc89a28729df72a2dabda
    fetch: partial
    fetch_via: "only the four bindings and booting.rst were needed and read; drivers/ deliberately left closed"
  - name: laguna-kernel-prebuilts
    url: https://github.com/GrapheneOS/device_google_laguna-kernels_6.6
    commit: 80c104d7e5591ebc3cd413f54b076d972484ff0b
    fetch: ok
  - name: "Add Laguna/Tensor G5 SoC and Frankel, Blazer & Mustang boards (v4)"
    url: https://lore.kernel.org/all/20260918-contrib-pg-pixel10-initial-dts-v4-0-745eaca28b1a@linaro.org/
    fetch: ok
  - name: "arm64: google: Introduce frankel, blazer, and mustang boards (v1)"
    url: https://lore.kernel.org/linux-arm-kernel/20251111192422.4180216-1-dianders@chromium.org/
    fetch: ok
  - name: Linux arm64 booting.rst
    url: https://www.kernel.org/doc/Documentation/arch/arm64/booting.rst
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
  - name: pixelscripts Makefile (Linaro)
    url: https://gitlab.com/LinaroLtd/googlelt/pixelscripts/-/raw/clo/main/Makefile
    fetch: ok
  - name: Build Pixel kernels (source.android.com)
    url: https://source.android.com/docs/setup/build/building-pixel-kernels
    fetch: ok
  - name: android.googlesource.com project list
    url: https://android.googlesource.com/
    fetch: ok
  - name: GrapheneOS source page
    url: https://grapheneos.org/source
    fetch: ok
  - name: Synopsys DesignWare ABP UART devicetree binding (snps-dw-apb-uart)
    url: https://www.kernel.org/doc/Documentation/devicetree/bindings/serial/snps-dw-apb-uart.yaml
    fetch: ok
  - name: "Google Tensor Series G5 (Laguna) DWC3 USB SoC Controller binding (google,lga-dwc3)"
    url: https://raw.githubusercontent.com/torvalds/linux/master/Documentation/devicetree/bindings/usb/google,lga-dwc3.yaml
    fetch: ok
  - name: "Google Tensor G5 USB PHY binding (google,lga-usb-phy)"
    url: https://raw.githubusercontent.com/torvalds/linux/17e7b8eacf4cac800a4fc89a28729df72a2dabda/Documentation/devicetree/bindings/phy/google,lga-usb-phy.yaml
    fetch: ok
  - name: "Arm architecture documents (IHI 0069, IHI 0070, DEN 0022, DDI 0487)"
    url: https://developer.arm.com/documentation/
    fetch: blocked
summary: {pass: 43, fail: 2, unverifiable: 0, gap: 0, adjudicate: 1}
---

# Verification of `tensor-g5`

Second verification pass. The first pass found five defects; every proposed correction was applied,
and this pass re-derived all 46 claims from the sources without reference to either. Both verifiers
regenerated the production DTS from the DTBs themselves and confirmed the blob hashes against the
spec's frontmatter.

- Quick-facts/1 "Addressing model": ADJUDICATE — **the two verifiers disagree, and the sides flipped
  between passes.** Both readings recorded; the claim is excluded from the pass/fail counts.
  Not in dispute: root 2/2 cells; `soc@0` a `simple-bus` with identity `ranges`/`dma-ranges` over
  `0x0`–`0x10_0000_0000`; the GIC distributor at `0x0588_0000` and the UART at `0x0DB6_2000` in both
  trees; the `memory@80000000` placeholder; the `alloc-ranges` high group reaching `0xA_0000_0000`;
  and that every bring-up-critical address (UART, GIC, the three GIA aggregators, the seven SMMUs,
  `reserved-memory`) is a direct child of `/` or sits under an identity `ranges`, so those `reg`
  values really are CPU-physical as written.
  *Full verifier (PASS):* reads the production blob as having no bus node, with peripherals directly
  under `/`.
  *Second verifier (FAIL):* walked all 2774 nodes and found ten `simple-bus` nodes, **eight of them
  translating**, tabulating each with its cell counts and window — `sswrp_dpu@ec00000`,
  `sswrp_g2d@3f200000`, `sswrp_aur@38000000`, `sswrp_codec3p@3f000000`, `sswrp_tpu@36000000` (1
  address cell), and `sswrp_ispfe@F000000`, `sswrp_ispbe@3E400000`, `sswrp_gsw@3EC00000` (2 address
  cells), all with 1 size cell, each mapping child address 0 onto the CPU-physical base in its own
  unit address. It reports **40 descendant nodes carrying `reg` values that are bus offsets**, with
  a worked translation: the display controller child reads `reg = 0x20_0000`, which is CPU-physical
  `0x0EE0_0000`. It also notes `simple_usb_bus` and `odm` are `simple-bus` with empty identity
  `ranges`, and that the production GIC node carries an empty `ranges;` where the series node has
  none — so the bullet's last sentence, placed after two production-blob sentences, reads as
  applying to both trees when it is true only of the series.
  Note for the adjudicator: the evidence is not symmetric. The FAIL side is a node-by-node table
  with a checkable worked example; the PASS side is an assertion that no bus node exists. In the
  first pass the same disagreement occurred with the sides reversed, which suggests the blob's
  structure is genuinely easy to misread rather than that either verifier is unreliable. The
  second verifier's proposed correction is in its report and names all eight wrappers.
- Quick-facts/2 "Boot chain and entry state": PASS — both verifiers. All four series reserved-memory
  regions by base, size and `no-map` (ramoops `0x9520_0000`/4 MiB with its crash-reset comment,
  bootloader log `0x9560_0000`/1 MiB, GSA log `0xA61B_0000`/16 KiB, ABL `0xBE00_0000`/16 MiB); the
  BL31 log buffer at `0x8B60_0000`/2 MiB in the blob; the four command-line strings verbatim from
  the blob's `chosen/bootargs` plus the protected-KVM arguments; the bootloader behaviors from the
  v4 cover letter and patch 3/4; `mkbootimg --header_version 4` and the `dtbo` erase from the
  Makefile; the DTB living in the vendor boot partition and the dt table's `id`/`rev` matching from
  the two Android pages; `booting.rst` fixing the entry contract without describing this bootloader.
  Recorded by the second verifier, not failed: `goog_bl31_mem_log_buff` proves a node *name*; that
  BL31 means a TF-A-style EL3 runtime is a reasonable conclusion from it, not a `[DT]` reading. With
  the `[inference]` class now available, that half would be better tagged as one.
- Quick-facts/3 "Silicon revisions and SoC id": FAIL — **the correction applied after the first pass
  overshot: it names two wrong nodes.** The substance of the first pass's finding stands (A0 and B0
  do differ beyond DVFS tables), but the corrected text sends a reader to nodes that do not carry
  the differences. (a) The spec says "the chip-info `major` field (0 versus 1)". The `goog_chip_info`
  node has no `major` property; the field that changes lives in the separate root-level
  `soc_compatible` node, whose single child is renamed `A0`→`B0` with `description` "LGA A0"→"LGA B0"
  and `major` 0→1 — and the spec's own cited authority, the v1 patch 1/4 message, quotes that node
  explicitly and places it outside chip-info. (b) The spec says "the hardlockup-detector node"; the
  node that changes is `pmu-ehld` on A0 becoming `ehld-coreinstr` on B0, while a differently named
  `hardlockup-watchdog` node exists in both blobs and is byte-identical.
  Correct and unchanged: product id `0x5` with major/minor nibbles, A0 = `0x000500`, B0 = `0x000510`
  and the 16-bit-product-id plus 4-bit-major plus 4-bit-minor split, all near-verbatim in the v1
  patch 1/4 message; the B0-only mass-production support and the A0 EVT boot claim from v4 patch
  3/4 and the cover letter; the restructuring into child nodes, the added `0x200C_0504`/`0x24`
  window and the added clock input with no A0 counterpart; and that no other peripheral address,
  interrupt or clock differs — the rest of the diff being DVFS and energy-model tables, per-core
  frequency votes and symbol ordering.
  Proposed correction: replace "the chip-info `major` field (0 versus 1)" with "the root-level
  `soc_compatible` node, whose child is renamed `A0` to `B0` with `major` 0 versus 1", and replace
  "the hardlockup-detector node" with "the early-hardlockup-detector node (`pmu-ehld` on A0,
  `ehld-coreinstr` on B0; the separately named `hardlockup-watchdog` node is identical in both)".
  Optionally note that `device_table` flips `google,lga_a0_ptde`→`google,lga_b0_ptde` alongside the
  dvfs pair, while `ids_table`, `hw_feature_table` and `serial` keep their `a0` compatibles in both.
- Quick-facts/4 "SMP topology": PASS — eight cpu nodes at the stated unit addresses with the stated
  compatibles and labels, capacities 258/891/1024, `enable-method = "psci"` throughout, the psci node
  at `arm,psci-1.0` with `method = "smc"` and no spin-table, all four idle-states carrying
  `local-timer-stop` and suspend parameter `0x40000003`, cpu_pd2–4 under the cluster-1 domain and
  cpu_pd5–7 under cluster-2 at `0x40010033` beneath a top domain at `0x40020333`; the blob's cpus
  carry `arm,armv8` and its Trusty node reserves IPI range 8–15. Recorded, not failed: the blob's cpu
  compatible list begins `gem5,armv8` before `arm,armv8`, which the bullet does not mention. The
  MPIDR-Aff1 mapping and the PSCI target convention rest on DDI 0487 and DEN 0022, both Arm-portal
  blocked, so only the DT side was re-derived.
- Quick-facts/5 "Interrupts": PASS — both verifiers. GICD `0x0588_0000`/64 KiB and GICR
  `0x0590_0000`/`0x20_0000` (`0x4_0000` per redistributor over eight cores, four 64 KiB frames),
  four interrupt cells, maintenance PPI 9 level-high, two `ppi-partitions` splitting seven cores
  from one. Aggregators `google,level-gia`, one interrupt cell, 16-byte windows: LSIO-S
  `0x3BD6_0400` → SPI 694, LSIO-E `0x3A16_0400` → SPI 704, LSIO-N `0x0D96_0400` → SPI 684. IHI 0069
  is Arm-portal blocked, so the INTID arithmetic and the system-register CPU interface rest on the
  document id.
- Quick-facts/6 "Debug UART": PASS — both verifiers, and **both corrections applied after the first
  pass verified independently.** The CLI block layout is I2C `+0x1000`, UART `+0x2000`, SPI
  `+0x3000`, I3C master `+0x4000` with a `0x2A0` window, all four personality nodes named after the
  `+0x1000` address, and the same layout at every other CLI block checked. The `earlycon` split
  holds: the production command line passes `earlycon=uart8250,mmio32,0xdb62000` with
  `console=ttyS0,115200n8`, while the pixelscripts Makefile passes a bare `earlycon`, leaves
  `console=` empty for this family, and asks the bootloader for 3000000 baud. Everything else in the
  bullet re-derived exactly: the series node and its properties, the `serial0` alias and
  `stdout-path`, `google,lga-uart` in mainline's binding at the pinned commit, LSR at `0x14`, the
  blob's node with its clocks, reset, power domain and pin group, and that it is the only one of the
  22 UARTs with a direct `interrupts` property.
  Recorded by both verifiers, not failed: the parenthetical expanding CLI as "configurable low-speed
  interface" appears in no consulted authority — an authorial gloss inside a `[DT]`-tagged bullet.
- Quick-facts/7 "Other UARTs": PASS — 22 `uart@` nodes, every one with `reg-shift = 2`,
  `reg-io-width = 4`, a `0x100` window, baudclk/apb_pclk clock names, an `s_rst_n` reset and
  default/sleep/cli pin groups, all disabled except the console (checked programmatically across all
  22, zero deviations); seven in LSIO-S aliased uart0–uart6, eight in LSIO-E aliased uart7–uart14
  with uart9 also `serial2` and uart12 also `serial1` carrying `google,uart-logging`, six in LSIO-N
  aliased uart15 and uart17–uart21; all 21 non-console nodes use `interrupts-extended` into their
  island aggregator. No `arm,pl011` compatible anywhere in the blob.
- Quick-facts/8 "Timers": PASS — `arm,armv8-timer` with PPIs 13, 14, 11, 10, all level-low with a
  zero partition cell; the blob encodes the same four lines with flag word `0x108` (level-low plus a
  legacy CPU-mask bit). Neither tree gives a counter frequency. The 38.4 MHz oscillator is the clock
  phandle of both `google,wdt` watchdogs at `0x200C_4000` and `0x200C_5000`, `0x1000` each, and the
  Makefile disables the watchdog from fastboot only for blazer and frankel. Nothing in either tree
  ties the oscillator to the counter.
- Quick-facts/9 "Clocks and power": PASS — `cpm_clk` is `google,cpm-clk` with no `reg`; the mailbox
  pair is `google,mba-ctrl` at `0x526_0000` (SPI 250, requests) and `0x526_1000` (SPI 251,
  responses); the five reset banks carry 16, 5, 45, 43 and 50 lines for HSIO-N, HSIO-S, LSIO-S,
  LSIO-N and LSIO-E; the power controller and the PMIC node have the stated compatibles, the PMIC
  reaching the same mailbox with its big-core and mid-core rails named as the spec says; the SPMI
  controller is at the stated base with a `0x300` window and 19 MHz; dtbo entry 12 carries the
  MAX77779 family and the MAX77759 TCPC; the three USB fixed clocks are 19.2 MHz, 250 MHz and
  200 kHz; the three OTP shadow syscons exist at the three stated bases and are the phandles the
  chip-info and PHY-trim nvmem layouts point at. Recorded, not failed: "Renesas/Dialog" is a vendor
  gloss on the DA9188 part number, not a DT string.
- Quick-facts/10 "GPIO and pinmux": PASS — all ten banks match by compatible, base and window size
  including the AoC bank's second window; nine are gpio-controllers with two cells and the HSIO-S
  standby bank is precisely the one that is not. A UART's pin group is three offset/value pairs under
  the island's CLI node. Per-signal groups and line names live in dtbo entry 12, not the SoC blob. No
  pinctrl node in the series, and the v1 thread says Laguna pinctrl and clock drivers are still to be
  written. Recorded, not failed: the banks' own compatibles are `google,lga-*-pinctrl` and it is the
  CLI blocks that literally carry `compatible = "pinctrl-single"`, so "pinctrl-single-style banks" is
  a characterization rather than a binding fact — which the bullet's own TODO already concedes.
- Quick-facts/11 "USB": PASS — the wrapper's three windows and their `reg-names`, the two PME wake
  interrupts (SPI 597 and 598), the core at its stated base with interrupt SPI 580, super-speed
  maximum, a role switch defaulting to peripheral, and the `amb` SMMU; the mainline `google,lga-dwc3`
  binding's example carries the same base, size and three SPIs and requires the clock, reset and
  power-domain names the spec lists; the PHY binding supplies the four windows and the phy-cells
  selector values; the production PHY node has nine windows plus a firmware file name and an nvmem
  trim list. The verifier read the USB facts from the two mainline binding YAMLs and deliberately
  left `linux/drivers/` closed.
- Quick-facts/12 "UFS, PCIe, and the modem": PASS — the UFS node's compatible, its three named
  windows, its two clock names, the `inf` SMMU, its aggregator line plus GIC SPIs 542 through 557
  inclusive, and that it is the node `ufs0` names and the command line's boot device. Both root
  complexes carry their stated compatible, bases, 1 MiB configuration windows and interrupt sets
  (SPIs 568–575, and SPI 524). `samsung,exynos-cp` appears in the board overlays, not the SoC blob,
  while the three modem carveouts are in the SoC blob at the stated bases.
- Quick-facts/13 "Security, IOMMU, and interconnect": PASS — the security-core node and the Trusty
  node have the stated compatibles; all seven `arm,smmu-v3` instances are `0x4_0000` long at exactly
  the seven bases listed; the protected-KVM region spans `0x1_0000_0000` for 4 GiB; the mesh node
  carries its compatible, a `reg_base` of `0x1000_0000` and SPIs 71–74 named for non-secure/secure
  error and fault. Recorded, not failed: IHI 0070 is the only Arm document cited in the spec with no
  matching `resources.docs` entry. Under the format's "the document id is the citation" rule for Arm
  documents this passes; a stricter reading of "a page named in a tag clause must be a `docs` entry"
  would not. Every value in the bullet came from the blob; the Arm portal blocks the document.
- Quick-facts/14 "Reserved memory beyond the series": PASS — every region matches by base and size:
  the always-on-core region (48 MiB), the security-core region (about 62 MiB), TPU firmware
  (20 MiB), GPU firmware (33 MiB), the DSP regions from their stated base, the BL31 log, the three
  xHCI pools at their three bases, and the modem carveouts.
- Quick-facts/15 "DTB runtime patching": PASS — both verifiers. The cover letter and patch 3/4 state
  the bootloader adds the memory node (the blob's placeholder is 256 MiB), that a missing `ufs0`
  alias is fatal with the calibration-data reason repeated in the overlay's own header, and that the
  bootloader adds `console=`; the Android locking page states the lock state must reach the kernel
  through bootconfig from Android 12; the series reserves ramoops where the ABL expects it.
- Gotchas/1 "Google publishes no kernel for this part": PASS — **the correction applied after the
  first pass verified.** The android.googlesource.com project list has 19 `kernel/devices/google/`
  entries running akita to zumapro with no laguna entry and zero occurrences of the string; the
  Build Pixel kernels page's GKI branch table stops at Pixel 9a with no Pixel 10 row; the GrapheneOS
  source page lists the laguna prebuilts and, in the next section, `kernel_pixel_6.6`. Recorded, not
  failed: the first half rests on the android.googlesource.com project list, which is now a
  `resources.docs` entry but is not named in the tag clause; naming it would complete the citation.
- Gotchas/2 "Clocks, resets, and regulators are mailbox requests to firmware, not MMIO": PASS — both
  verifiers. `cpm_clk` carries no `reg`; the reset banks, power controller and regulator node all
  carry mailbox handles into the `google,mba-ctrl` pair; no consulted source describes that protocol
  at register level; the console UART is the one left `okay` in the blob. Carries the required TODO.
- Gotchas/3 "GICv3-family with four interrupt cells": PASS — both verifiers. Four cells in both
  trees, the fourth being the PPI-partition phandle, `arm,gic-v3` with no GICv2 CPU-interface window
  in either tree.
- Gotchas/4 "Only the console UART interrupts through the GIC": PASS — both verifiers. Of the 22
  `uart@` nodes only the console carries an `interrupts` property; the other 21 use
  `interrupts-extended` into an aggregator, as do the i2c, spi, i3c-master and pinctrl nodes checked.
  An aggregator line number is a line on a 16-byte window, not a GIC SPI.
- Gotchas/5 "The console is a DesignWare 8250 at a 32-bit stride, left disabled in the DT": PASS —
  both verifiers. The compatible pair, `reg-shift = 2`, `reg-io-width = 4` and `status = "disabled"`
  in the series, and patch 3/4's statement that the bootloader enables the UART when the console is
  turned on and never hardcodes the baud. Recorded by the second verifier, not failed: "if the
  bootloader's console is off the line is silent whatever the kernel does" is one derivation step
  past what patch 3/4 states.
- Gotchas/6 "Shipped bootloaders refuse a DTB without a `ufs0` alias": PASS — both verifiers, and
  **the citation correction applied after the first pass verified.** The v4 cover letter records the
  v3 removal, the fatal error and that the flashing scripts apply the node; the Makefile builds the
  placeholder overlay and merges it into each board DTB; the overlay's header states the
  fatal-error and calibration-data reason. The same changelog records the memory node's removal.
- Gotchas/7 "Entry exception level is not published": PASS — both verifiers, each re-establishing
  the negative independently. `booting.rst` fixes only what the Image requires and says nothing about
  what a given bootloader delivers; no consulted source states Laguna's hand-off level; the blob's
  command line does enable protected KVM, which is why the bullet warns against inferring from it.
  The second verifier additionally identified the one log printing "All CPU(s) started at EL2" as
  Pixel 6 material, not a Tensor G5 log.
- Gotchas/8 "The production blob's node names lie about unit addresses": PASS — both verifiers. The
  console node's name and `reg` differ by `0x1000`, and at every CLI block the i2c, uart, spi and
  i3c-master nodes are all named after the block's `+0x1000` address while their `reg` values are
  `+0x1000`/`+0x2000`/`+0x3000`/`+0x4000`.
- Gotchas/9 "This is not the Pixel 10a's chip": FAIL — the cited authority does not name the part.
  The v4 cover letter says only that "Tensor G1 to G4 SoCs (found in Pixel 6 to Pixel 9 and Pixel
  10a) were offshoots from the Samsung Exynos family": it places the Pixel 10a's SoC in the G1–G4
  Exynos-derived set but never says which one, and the v1 patch 1/4 message contrasts G4 with G5
  without mentioning the Pixel 10a at all. Naming it "a Tensor G4" is a conclusion drawn from the
  device ordering in that parenthetical, written as a `[doc]` fact — the definiteness case rather
  than a substance error. The spec is also internally inconsistent: Orientation says more carefully
  that the G1–G4 "and the Pixel 10a's chip" are Exynos derivatives, treating the 10a's chip as
  separate. The load-bearing half — that nothing in this spec applies to the Pixel 10a — is fully
  supported. Proposed correction: write "The Pixel 10a carries an Exynos-derived Tensor from the
  G1–G4 generation" and keep the `[doc]` tag; or keep the G4 attribution and retag it `[inference]`
  with its premises, derivation and `TODO (verify on hardware)`, as the format now requires for that
  class.
- instances/lsion_cli16_uart: PASS — both verifiers, clause by clause. `reg` `0x0DB6_2000` and SPI
  688 from the series node, confirmed by the blob's node carrying the same `reg` and interrupt word;
  INTID 720 = 32 + 688; level-high; `clocks: []` correct because the series gives `clock-frequency`
  and no phandle, with the blob's two names in the note; and every statement in the note verified.
- instances/lsios_cli0_uart: PASS — `reg` `0x3BF0_2000`, aggregator line 0 on LSIO-S (SPI 694), both
  clock names, `uart0` alias, disabled.
- instances/lsios_cli1_uart: PASS — `reg` `0x3BF1_2000`, line 1, both clock names, `uart1`, disabled.
- instances/lsios_cli2_uart: PASS — `reg` `0x3BF2_2000`, line 2, both clock names, `uart2`, disabled.
- instances/lsios_cli3_uart: PASS — `reg` `0x3BF3_2000`, line 3, both clock names, `uart3`, disabled.
- instances/lsios_cli4_uart: PASS — `reg` `0x3BF4_2000`, line 4, both clock names, `uart4`, disabled.
- instances/lsios_cli5_uart: PASS — `reg` `0x3BF5_2000`, line 5, both clock names, `uart5`, disabled.
- instances/lsios_cli6_uart: PASS — `reg` `0x3BF6_2000`, line 6, both clock names, `uart6`, disabled.
- instances/lsioe_cli7_uart: PASS — `reg` `0x3A30_2000`, line 0 on LSIO-E (SPI 704), both clock
  names, `uart7`, disabled.
- instances/lsioe_cli8_uart: PASS — `reg` `0x3A31_2000`, line 1, both clock names, `uart8`, disabled.
- instances/lsioe_cli9_uart: PASS — `reg` `0x3A32_2000`, line 2, both clock names, `uart9` and
  `serial2` aliases present, disabled; the row's recorded role is correct.
- instances/lsioe_cli10_uart: PASS — `reg` `0x3A33_2000`, line 3, both clock names, `uart10`,
  disabled.
- instances/lsioe_cli11_uart: PASS — `reg` `0x3A34_2000`, line 4, both clock names, `uart11`,
  disabled.
- instances/lsioe_cli12_uart: PASS — `reg` `0x3A35_2000`, line 5, both clock names, `uart12` and
  `serial1` aliases, `google,uart-logging` present, disabled; the row's recorded role is correct.
- instances/lsioe_cli13_uart: PASS — `reg` `0x3A36_2000`, line 6, both clock names, `uart13`,
  disabled.
- instances/lsioe_cli14_uart: PASS — `reg` `0x3A37_2000`, line 7, both clock names, `uart14`,
  disabled.
- instances/lsion_cli15_uart: PASS — `reg` `0x0DB5_2000`, line 5 on LSIO-N (SPI 684), both clock
  names, `uart15`, disabled.
- instances/lsion_cli_int0_uart: PASS — `reg` `0x0DB0_2000`, line 0, both clock names, `uart17`,
  disabled.
- instances/lsion_cli_int1_uart: PASS — `reg` `0x0DB1_2000`, line 1, both clock names, `uart18`,
  disabled, and its baud clock node does carry no `rates` property while its neighbours do.
- instances/lsion_cli_int2_uart: PASS — `reg` `0x0DB2_2000`, line 2, both clock names, `uart19`,
  disabled.
- instances/lsion_cli_int3_uart: PASS — `reg` `0x0DB3_2000`, line 3, both clock names, `uart20`,
  disabled.
- instances/lsion_cli_int4_uart: PASS — `reg` `0x0DB4_2000`, line 4, both clock names, `uart21`,
  disabled.

## Process notes

Not verdicts.

1. **The `instances/*` parent labels drop a suffix, systematically.** The aggregators' DT labels are
   `lsios_level_aggr_4_intr`, `lsioe_…_intr`, `lsion_…_intr`; the spec writes them without `_intr`
   on all 21 extended rows. `SPEC-FORMAT.md` says `parent` "names that controller by its DT label".
   The full verifier recorded this rather than failing, because each row's note gives the
   aggregator's address unambiguously and the label resolves by prefix — and flagged it as the
   likeliest thing a stricter second reader would score differently. Worth settling deliberately:
   the fix is either 21 label edits or one sentence in the format.
2. **Three authorial glosses sit inside `[DT]`-tagged bullets** — "configurable low-speed interface"
   (Quick-facts/6), "pinctrl-single-style banks" (Quick-facts/10) and "Renesas/Dialog"
   (Quick-facts/9). None is wrong; none is read from a cited authority. These are what the
   `[inference]` class exists for.
3. **Two frontmatter observations, outside verdict scope.** The prebuilts repository reports
   `fork: false` with no parent on its host, although the `repos` note calls it "a third-party fork
   of the AOSP prebuilt repository" — related to the `pixel10` Quick-facts/7 adjudication. And the
   muzel directory also contains an `init.insmod.deepspace.cfg`, a fourth device the note's
   "muzel = frankel, blazer, mustang" does not list.
4. **Leak scan: findings, reviewed and cleared.** The full verifier's scan returned 0 shared token
   runs, with 57 lowercase and 2 ALL-CAPS identifiers, every one a device-tree node name, label,
   `reg-names`/`clock-names`/`reset-names` value, alias or regulator schematic name — `[DT]`
   hardware description. Three (`DesignWare`, `drd_bus`, `non_sticky`) were attributed to a driver
   file by the scanner but are equally present in the mainline `google,lga-dwc3.yaml` binding, which
   is where the verifier read them; it left `linux/drivers/` closed on purpose. The second
   verifier's scan returned 0 shared runs with five lowercase hits on the same grounds. Nothing was
   rewritten to satisfy the scanner.
