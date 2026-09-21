---
kind: soc
id: tensor-g5
name: Google Tensor G5 (Pixel 10 family SoC; codename laguna, lga in code)
triggers: [tensor g5, google tensor g5, laguna]
not_triggers: [tensor g4, tensor g3, tensor g2, pixel 10a]
aliases: [laguna, lga]
cache: pixel10-v4-resources
instances:
  - name: lsion_cli16_uart
    ip: dw-apb-uart
    reg: 0x0db62000
    irq: {kind: SPI, number: 688, intid: 720, trigger: level-high}
    clocks: []
    role: debug console
    note: >-
      serial@db62000 in the series (compatible google,lga-uart then snps,dw-apb-uart, size 0x100,
      clock-frequency = 200000000, no clock handle, so clocks is []); uart@db61000 in lga-b0.dtb
      (compatible goog,goog-dw-apb-uart, same reg and interrupt, clock-names baudclk and apb_pclk
      from the CPM clock controller, a reset from the LSIO-N bank, a power domain, pinctrl group
      cli16_uart). reg-shift = 2 and reg-io-width = 4: 16550 indices at a 32-bit stride, mmio32,
      LSR at 0x14. serial0 and stdout-path point here. The only UART wired straight to the GIC.
      Left disabled in the series DT: the bootloader enables it when its console is on and sets
      the baud (115200n8 in the production command line; the upstream flow requests 3000000
      only when the mux query does not report virtual selection, otherwise preserving the user's
      baud setup).
      earlycon=uart8250,mmio32,0xdb62000. TODO (verify on hardware): the baud a given unit is
      left at.
  - name: lsios_cli0_uart
    ip: dw-apb-uart
    reg: 0x3bf02000
    irq: {kind: extended, number: 0, parent: lsios_level_aggr_4, note: "GIA level aggregator at 0x3bd60400, its own GIC line is SPI 694"}
    clocks: [baudclk, apb_pclk]
    note: "uart0 alias; lga-b0.dtb only; reg-shift 2, reg-io-width 4; disabled"
  - name: lsios_cli1_uart
    ip: dw-apb-uart
    reg: 0x3bf12000
    irq: {kind: extended, number: 1, parent: lsios_level_aggr_4, note: "aggregator GIC line SPI 694"}
    clocks: [baudclk, apb_pclk]
    note: "uart1 alias; lga-b0.dtb only; disabled"
  - name: lsios_cli2_uart
    ip: dw-apb-uart
    reg: 0x3bf22000
    irq: {kind: extended, number: 2, parent: lsios_level_aggr_4, note: "aggregator GIC line SPI 694"}
    clocks: [baudclk, apb_pclk]
    note: "uart2 alias; lga-b0.dtb only; disabled"
  - name: lsios_cli3_uart
    ip: dw-apb-uart
    reg: 0x3bf32000
    irq: {kind: extended, number: 3, parent: lsios_level_aggr_4, note: "aggregator GIC line SPI 694"}
    clocks: [baudclk, apb_pclk]
    note: "uart3 alias; lga-b0.dtb only; disabled"
  - name: lsios_cli4_uart
    ip: dw-apb-uart
    reg: 0x3bf42000
    irq: {kind: extended, number: 4, parent: lsios_level_aggr_4, note: "aggregator GIC line SPI 694"}
    clocks: [baudclk, apb_pclk]
    note: "uart4 alias; lga-b0.dtb only; disabled"
  - name: lsios_cli5_uart
    ip: dw-apb-uart
    reg: 0x3bf52000
    irq: {kind: extended, number: 5, parent: lsios_level_aggr_4, note: "aggregator GIC line SPI 694"}
    clocks: [baudclk, apb_pclk]
    note: "uart5 alias; lga-b0.dtb only; disabled"
  - name: lsios_cli6_uart
    ip: dw-apb-uart
    reg: 0x3bf62000
    irq: {kind: extended, number: 6, parent: lsios_level_aggr_4, note: "aggregator GIC line SPI 694"}
    clocks: [baudclk, apb_pclk]
    note: "uart6 alias; lga-b0.dtb only; disabled"
  - name: lsioe_cli7_uart
    ip: dw-apb-uart
    reg: 0x3a302000
    irq: {kind: extended, number: 0, parent: lsioe_level_aggr_4, note: "GIA level aggregator at 0x3a160400, its own GIC line is SPI 704"}
    clocks: [baudclk, apb_pclk]
    note: "uart7 alias; lga-b0.dtb only; disabled"
  - name: lsioe_cli8_uart
    ip: dw-apb-uart
    reg: 0x3a312000
    irq: {kind: extended, number: 1, parent: lsioe_level_aggr_4, note: "aggregator GIC line SPI 704"}
    clocks: [baudclk, apb_pclk]
    note: "uart8 alias; lga-b0.dtb only; disabled"
  - name: lsioe_cli9_uart
    ip: dw-apb-uart
    reg: 0x3a322000
    irq: {kind: extended, number: 2, parent: lsioe_level_aggr_4, note: "aggregator GIC line SPI 704"}
    clocks: [baudclk, apb_pclk]
    role: serial2 alias
    note: "uart9 and serial2 aliases in lga-b0.dtb; disabled"
  - name: lsioe_cli10_uart
    ip: dw-apb-uart
    reg: 0x3a332000
    irq: {kind: extended, number: 3, parent: lsioe_level_aggr_4, note: "aggregator GIC line SPI 704"}
    clocks: [baudclk, apb_pclk]
    note: "uart10 alias; lga-b0.dtb only; disabled"
  - name: lsioe_cli11_uart
    ip: dw-apb-uart
    reg: 0x3a342000
    irq: {kind: extended, number: 4, parent: lsioe_level_aggr_4, note: "aggregator GIC line SPI 704"}
    clocks: [baudclk, apb_pclk]
    note: "uart11 alias; lga-b0.dtb only; disabled"
  - name: lsioe_cli12_uart
    ip: dw-apb-uart
    reg: 0x3a352000
    irq: {kind: extended, number: 5, parent: lsioe_level_aggr_4, note: "aggregator GIC line SPI 704"}
    clocks: [baudclk, apb_pclk]
    role: serial1 alias (UART logging)
    note: "uart12 and serial1 aliases in lga-b0.dtb, carries a google,uart-logging flag; disabled"
  - name: lsioe_cli13_uart
    ip: dw-apb-uart
    reg: 0x3a362000
    irq: {kind: extended, number: 6, parent: lsioe_level_aggr_4, note: "aggregator GIC line SPI 704"}
    clocks: [baudclk, apb_pclk]
    note: "uart13 alias; lga-b0.dtb only; disabled"
  - name: lsioe_cli14_uart
    ip: dw-apb-uart
    reg: 0x3a372000
    irq: {kind: extended, number: 7, parent: lsioe_level_aggr_4, note: "aggregator GIC line SPI 704"}
    clocks: [baudclk, apb_pclk]
    note: "uart14 alias; lga-b0.dtb only; disabled"
  - name: lsion_cli15_uart
    ip: dw-apb-uart
    reg: 0x0db52000
    irq: {kind: extended, number: 5, parent: lsion_level_aggr_4, note: "GIA level aggregator at 0x0d960400, its own GIC line is SPI 684"}
    clocks: [baudclk, apb_pclk]
    note: "uart15 alias; lga-b0.dtb only; disabled"
  - name: lsion_cli_int0_uart
    ip: dw-apb-uart
    reg: 0x0db02000
    irq: {kind: extended, number: 0, parent: lsion_level_aggr_4, note: "aggregator GIC line SPI 684"}
    clocks: [baudclk, apb_pclk]
    note: "uart17 alias; lga-b0.dtb only; disabled"
  - name: lsion_cli_int1_uart
    ip: dw-apb-uart
    reg: 0x0db12000
    irq: {kind: extended, number: 1, parent: lsion_level_aggr_4, note: "aggregator GIC line SPI 684"}
    clocks: [baudclk, apb_pclk]
    note: "uart18 alias; lga-b0.dtb only; its baud clock node lists no rates; disabled"
  - name: lsion_cli_int2_uart
    ip: dw-apb-uart
    reg: 0x0db22000
    irq: {kind: extended, number: 2, parent: lsion_level_aggr_4, note: "aggregator GIC line SPI 684"}
    clocks: [baudclk, apb_pclk]
    note: "uart19 alias; lga-b0.dtb only; disabled"
  - name: lsion_cli_int3_uart
    ip: dw-apb-uart
    reg: 0x0db32000
    irq: {kind: extended, number: 3, parent: lsion_level_aggr_4, note: "aggregator GIC line SPI 684"}
    clocks: [baudclk, apb_pclk]
    note: "uart20 alias; lga-b0.dtb only; disabled"
  - name: lsion_cli_int4_uart
    ip: dw-apb-uart
    reg: 0x0db42000
    irq: {kind: extended, number: 4, parent: lsion_level_aggr_4, note: "aggregator GIC line SPI 684"}
    clocks: [baudclk, apb_pclk]
    note: "uart21 alias; lga-b0.dtb only; disabled"
resources:
  repos:
    - name: linux-mainline
      url: https://github.com/torvalds/linux
      ref: master
      license: GPL-2.0-only
      status: merged
      verified: 2026-09-18
      fetch: ok
      fetch_via: raw
      files:
        - Documentation/devicetree/bindings/serial/snps-dw-apb-uart.yaml
        - Documentation/devicetree/bindings/usb/google,lga-dwc3.yaml
        - Documentation/devicetree/bindings/phy/google,lga-usb-phy.yaml
        - drivers/usb/dwc3/dwc3-google.c
        - drivers/phy/phy-google-usb.c
        - Documentation/arch/arm64/booting.rst
        - {path: arch/arm64/boot/dts/google/lga.dtsi, status: unmerged, note: "lands with the Laguna series"}
        - {path: arch/arm64/boot/dts/google/lga-pixel-common.dtsi, status: unmerged, note: "lands with the Laguna series"}
        - {path: Documentation/devicetree/bindings/arm/google.yaml, status: merged, note: "present, but its lga entries land with the Laguna series"}
      note: >-
        At commit 17e7b8eacf4cac800a4fc89a28729df72a2dabda (2026-09-18) mainline carries the
        google,lga-uart compatible in the DesignWare UART binding, the Tensor G5 USB controller and
        PHY bindings and drivers, and no arch/arm64/boot/dts/google directory. The SoC and board
        device trees are the unmerged series below. Drivers are read for behavior only.
    - name: laguna-kernel-prebuilts
      url: https://github.com/GrapheneOS/device_google_laguna-kernels_6.6
      ref: "17"
      license: "unstated: the repository carries no licence file and its host reports none; prebuilt kernel binaries and device-tree blobs"
      verified: 2026-09-18
      fetch: ok
      fetch_via: raw
      files:
        - grapheneos/muzel/lga-b0.dtb
        - grapheneos/muzel/lga-a0.dtb
        - grapheneos/muzel/dtbo.img
        - grapheneos/muzel/System.map
        - grapheneos/muzel/modules.load
        - grapheneos/muzel/init.insmod.frankel.cfg
        - grapheneos/rango/lga-b0.dtb
        - grapheneos/rango/dtbo.img
      note: >-
        A third-party prebuilt repository for the Pixel 10 family, maintained by GrapheneOS
        (muzel = frankel, blazer, mustang, and a directory also carrying a module config for
        deepspace; rango = Pro Fold), read at commit
        80c104d7e5591ebc3cd413f54b076d972484ff0b. PROVENANCE: the artifacts here were obtained from
        this repository, which states its kernel builds are its own; identity with stock vendor
        artifacts is unverified. That statement covers the kernel builds and does not by itself
        establish whether each accompanying DTB or DTBO was rebuilt or copied, so every value drawn
        from these blobs inherits that caveat. The decompiled production blobs remain the most
        complete public map, and a value from them is
        tagged with this repository's name. lga-b0.dtb sha256
        f238c200f7cf7ae14265047af6a62fdc54ab39f58a4042e844564e39cfbca030, lga-a0.dtb
        5745204e715f376c58650133848c8d472a64161d3a3dd99d942d28bd582e20a7 (identical copies under
        rango). Module file names are source-observed, never facts.
  series:
    - title: "Add Laguna/Tensor G5 SoC and Frankel, Blazer & Mustang boards (v4)"
      url: https://lore.kernel.org/all/20260918-contrib-pg-pixel10-initial-dts-v4-0-745eaca28b1a@linaro.org/
      message_id: 20260918-contrib-pg-pixel10-initial-dts-v4-0-745eaca28b1a@linaro.org
      target: linux-mainline
      status: unmerged
      verified: 2026-09-18
      fetch: blocked
      fetch_via: "t.mbox.gz with a Wget user agent"
      files:
        - Documentation/devicetree/bindings/arm/google.yaml
        - arch/arm64/boot/dts/google/lga.dtsi
        - arch/arm64/boot/dts/google/lga-pixel-common.dtsi
        - arch/arm64/boot/dts/google/lga-frankel.dts
        - arch/arm64/boot/dts/google/lga-blazer.dts
        - arch/arm64/boot/dts/google/lga-mustang.dts
        - arch/arm64/configs/defconfig
      note: >-
        Peter Griffin, 2026-09-18, based on next-20260918 (3f2425f5b5bbbdd991ca9cdfd5502e68d8895998);
        the public SoC device tree. The HTML form is bot-challenged; the /raw suffix for one
        message and /t.mbox.gz for the thread, fetched with a Wget user agent, work. A map, never
        an authority.
    - title: "arm64: google: Introduce frankel, blazer, and mustang boards (v1)"
      url: https://lore.kernel.org/linux-arm-kernel/20251111192422.4180216-1-dianders@chromium.org/
      message_id: 20251111192422.4180216-1-dianders@chromium.org
      target: linux-mainline
      status: superseded
      verified: 2026-09-18
      fetch: blocked
      fetch_via: "/raw and t.mbox.gz with a Wget user agent"
      files:
        - arch/arm64/boot/dts/google/lga-b0.dts
        - arch/arm64/boot/dts/google/lga-frankel-mp1.dtso
        - Documentation/devicetree/bindings/arm/google.yaml
      note: >-
        Douglas Anderson, 2025-11-11: the first public posting, with one lga-b0.dts and per-board
        overlays (.dtso) selected by an Android dtbo board-id and board-rev, and a binding patch
        whose message documents the SoC-id and board-id encodings; superseded by the v4 series,
        which uses one .dts per board. Read for the id scheme only.
  docs:
    - title: Devicetree Specification v0.4, The Devicetree
      url: https://raw.githubusercontent.com/devicetree-org/devicetree-specification/v0.4/source/chapter2-devicetree-basics.rst
      access: public
      cite: true
      verified: 2026-09-20
      fetch: ok
      fetch_via: raw
      note: "sections 2.3.5 (#address-cells and #size-cells), 2.3.6 (reg), and 2.3.8 (ranges)"
    - title: Google Store, Pixel 10 tech specs
      url: https://store.google.com/us/product/pixel_10_specs?hl=en-US
      access: public
      cite: true
      verified: 2026-09-18
      fetch: ok
      note: "names the Google Tensor G5 and the Titan M2 security coprocessor; no register-level content"
    - title: Google blog, Pixel 10 introduces new chip, Tensor G5
      url: https://blog.google/products-and-platforms/devices/pixel/tensor-g5-pixel-10/
      access: public
      cite: true
      verified: 2026-09-18
      fetch: ok
      note: "the vendor's own statement of the TSMC 3 nm process and the TPU and ISP claims"
    - title: Android boot image header (source.android.com)
      url: https://source.android.com/docs/core/architecture/bootloader/boot-image-header
      access: public
      cite: true
      verified: 2026-09-18
      fetch: ok
      note: "boot header versions; v3/v4 keep the DTB in the vendor boot partition"
    - title: Android DTB and DTBO partitions (source.android.com)
      url: https://source.android.com/docs/core/architecture/dto/partitions
      access: public
      cite: true
      verified: 2026-09-18
      fetch: ok
      note: "the dt table header, the per-entry id and rev fields, and how a bootloader selects an overlay"
    - title: Android bootloader locking and unlocking (source.android.com)
      url: https://source.android.com/docs/core/architecture/bootloader/locking_unlocking
      access: public
      cite: true
      verified: 2026-09-18
      fetch: ok
      note: "the lock state reaches the kernel through bootconfig"
    - title: Linux arm64 booting.rst
      url: https://www.kernel.org/doc/Documentation/arch/arm64/booting.rst
      access: public
      cite: true
      verified: 2026-09-18
      fetch: ok
      note: "the entry-state contract a Linux Image expects; it does not say what this bootloader does"
    - title: Synopsys DesignWare ABP UART devicetree binding (snps-dw-apb-uart)
      url: https://www.kernel.org/doc/Documentation/devicetree/bindings/serial/snps-dw-apb-uart.yaml
      access: public
      cite: true
      verified: 2026-09-18
      fetch: ok
      note: "carries google,lga-uart at mainline head"
    - title: Google Tensor Series G5 (Laguna) DWC3 USB SoC Controller binding (google,lga-dwc3)
      url: https://raw.githubusercontent.com/torvalds/linux/master/Documentation/devicetree/bindings/usb/google,lga-dwc3.yaml
      access: public
      cite: true
      verified: 2026-09-18
      fetch: ok
      note: "the merged binding: interrupt, clock, reset, and power-domain names of the USB instance"
    - title: Google Tensor G5 USB PHY binding (google,lga-usb-phy)
      url: https://raw.githubusercontent.com/torvalds/linux/17e7b8eacf4cac800a4fc89a28729df72a2dabda/Documentation/devicetree/bindings/phy/google,lga-usb-phy.yaml
      access: public
      cite: true
      verified: 2026-09-18
      fetch: ok
      note: "the merged PHY binding: register windows and the phy-cells selector"
    - title: pixelscripts Makefile (Linaro)
      url: https://gitlab.com/LinaroLtd/googlelt/pixelscripts/-/raw/clo/main/Makefile
      access: public
      cite: true
      verified: 2026-09-18
      fetch: ok
      note: "the fastboot oem commands that enable the console UART, the earlycon it passes, how the DTB is packed into vendor_boot, and the ufs0 placeholder overlay it applies"
    - title: Build Pixel kernels (source.android.com)
      url: https://source.android.com/docs/setup/build/building-pixel-kernels
      access: public
      cite: true
      verified: 2026-09-18
      fetch: ok
      note: "the per-device kernel build table, which ends at the previous generation and lists no Pixel 10 row"
    - title: GrapheneOS source page
      url: https://grapheneos.org/source
      access: public
      cite: true
      verified: 2026-09-18
      fetch: ok
      note: "the laguna kernel prebuilt repository and, in the following section, the kernel source repository those prebuilts are built from"
    - title: android.googlesource.com project list
      url: https://android.googlesource.com/
      access: public
      cite: true
      verified: 2026-09-18
      fetch: ok
      note: "the public per-device kernel repositories: the list runs akita to zumapro and has no laguna entry"
    - title: ARM GICv3 and GICv4 architecture specification (IHI 0069)
      url: https://developer.arm.com/documentation/ihi0069/latest
      access: public
      cite: true
      fetch: blocked
    - title: Power State Coordination Interface, PSCI (DEN 0022)
      url: https://developer.arm.com/documentation/den0022/latest
      access: public
      cite: true
      fetch: blocked
    - title: Arm Architecture Reference Manual for A-profile (DDI 0487)
      url: https://developer.arm.com/documentation/ddi0487/latest
      access: public
      cite: true
      fetch: blocked
      note: exception levels, the generic timer, the MMU
    - title: Arm Cortex-X4 Core TRM (102484)
      url: https://developer.arm.com/documentation/102484/latest
      access: public
      cite: true
      fetch: blocked
    - title: Arm Cortex-A725 Core TRM (107652)
      url: https://developer.arm.com/documentation/107652/latest
      access: public
      cite: true
      fetch: blocked
    - title: Arm Cortex-A520 Core TRM (102517)
      url: https://developer.arm.com/documentation/102517/latest
      access: public
      cite: true
      fetch: blocked
  tools: []
---

<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Google Tensor G5 (laguna)

## Orientation

The Tensor G5 is the application processor of the Pixel 10, Pixel 10 Pro, Pixel 10 Pro XL, and
Pixel 10 Pro Fold: Google's first in-house SoC design (the Tensor G1 to G4, and the Pixel 10a's
chip, are Samsung Exynos derivatives), made on TSMC's 3 nm process. Eight Armv9 cores in one
DynamIQ cluster (2× Cortex-A520, 5× Cortex-A725, 1× Cortex-X4), a GICv3-family interrupt
controller, Arm generic timers, DesignWare 16550-class UARTs (22 of them, one the debug console),
a Synopsys DWC3 USB controller behind Google's own wrapper, and low-speed I/O grouped into
"islands" (LSIO-S, LSIO-E, LSIO-N, HSIO-N, HSIO-S) whose clocks, resets, and power domains are
requested from a firmware power manager (the "CPM") over a mailbox rather than programmed in MMIO.
There is no public datasheet or TRM, the vendor kernel source is not published, and the EL3
firmware and the Android bootloader (ABL) are closed. The public map is the unmerged mainline
device-tree series (v4, 2026-09-18), which boots to an initramfs shell, plus the decompiled
production device-tree blobs from a kernel prebuilt repository; the merged mainline USB bindings
are the only register-adjacent documentation Google has published. Press names an Imagination
DXT-48-1536 GPU and a Samsung Exynos 5400 modem; treat those as unverified.

## Quick-facts

- **Addressing model.** A `reg` in this tree is not always an address, and the node's own unit
  address is not always its register base. **Decoding procedure:** (1) Size each `reg` entry using
  the parent's `#address-cells` and `#size-cells`, not the node's own declarations, and check that
  the property length divides evenly. A ragged result means the assumed encoding does not fit;
  it does not identify the cause. (2) Zero size cells omit the length field. Determine whether
  the remaining cells encode an address, index, or identifier from the applicable binding and
  node context. (3) Interpret the parent's `ranges`: an empty property supplies identity mapping;
  a nonempty property supplies child-to-parent mapping windows. An absent property does not
  establish a translation or prove that the value is an offset. (4) Follow established mappings
  to the root and record any unresolved step. The table below classifies this particular
  production blob; its convention-only cases are not universal decoding rules.
  **Every `reg`-bearing node in the production blob**, classified by what the value means. Apply the rows in order and take the first that matches. Two rows are contained in another -- the DRAM extent inside root-level MMIO, and the reserved-memory carve-out inside identity-container MMIO -- so each narrower row is listed above the row containing it; those are the only overlaps, and counting every match instead of the first double-counts exactly 41 nodes (the 40 reserved-memory children, plus the one memory node).
  | Class | `reg` means | Parent signature | Count |
  |---|---|---|---|
  | DRAM extent | base and length | root, plus `device_type = "memory"` | 1 |
  | Root-level MMIO | CPU-physical as written | root; 2/2; no `ranges` (root's space is the CPU space) | 409 |
  | Reserved-memory carve-out | CPU-physical region | `/reserved-memory`; 2/2; empty `ranges;` | 40 |
  | Identity-container MMIO | CPU-physical as written | a container with an empty `ranges;` (seven of them, one two hops deep) | 7 |
  | Translating-window offset | offset into the wrapper's window | a root-level `sswrp_*` `simple-bus`, 1/1, non-empty `ranges` | 11 |
  | Whole-aperture mapping | the wrapper aperture, **not** the device base | an `sswrp_*` wrapper, 2/1; node is `google,lwis-ioreg-device` with `reg-valid-ranges` | 8 |
  | NVMEM cell offset | byte offset and length into a 1152-byte OTP shadow, which is not a bus | `nvmem-layout` (`fixed-layout`), 1/1, no `ranges`, inside the carve-out at `0x053D_1000` | 111 |
  | Graph index | a port or endpoint index | `ports`/`in-ports`/`out-ports`/`port@N`; one cell; well-formed containers declare 1/0 | 44 |
  | CPU identifier | MPIDR affinity (`0x000`–`0x700`), the PSCI target | `/cpus`; 1/0; no `ranges` | 8 |
  | Convention-only absolute | CPU-physical, but no bus authority says so | parent has no `ranges` and is not root, `/cpus`, a graph container or a layout: `/ehld-coreinstr` and `/cap_sysfs` | 6 |
  These ten account for **645 of the 645** `reg`-bearing nodes among the blob's 2774, so a class
  this table omits shows up as arithmetic that no longer sums rather than as a sentence that is
  quietly wrong. **Five traps**, none of which the structure alone resolves. The two `pcie@*` nodes
  declare 3/2, so sizing from the node instead of the parent yields `0x0C50_0000_0000_0000` for
  `0x0C50_0000`, and their `ranges` need the three-cell PCI `phys.hi` tag separated before the
  identity shows; `device_type = "pci"` is the discriminator, and neither node has a `reg`-bearing
  child. Four containers of `reg`-bearing nodes declare no cell counts at all, and the 2/1 default is wrong for every one
  — for `/cap_sysfs`'s two children, whose `reg` is four cells, a 2/1 reader gets the address right
  (`0x2191_0008`, and `0x8B20_F000` for the second) and the size wrong at `0x0`, with a spare cell
  left over; 4 is not divisible by 3, which is exactly what the divisibility check catches. Both
  read cleanly as 2+2: `0x2191_0008`/`0x13F8` and `0x8B20_F000`/`0x1000`. For 87 nodes the unit address is not
  the register base, including 22 each of `uart@X`, `spi@X` and `i3c-master@X` whose registers sit
  at `X + 0x1000`, `X + 0x2000` and `X + 0x3000` because the three siblings share one combo-block
  unit address. The four children of `sswrp_ispbe@3E400000` carry byte-identical `reg` and
  `reg-names`, so anything keyed on `reg` silently loses three devices. And the GIC's `reg` has
  five entries whose last three are all zero — optional CPU-interface, HYP and VCPU slots, the only
  all-zero address-and-size entries in the blob — so it has two windows, not five, and must be indexed positionally
  per the binding. The **series** tree is a different shape and only 14 nodes carry `reg`: its
  peripherals sit under a `soc@0` `simple-bus` whose `ranges` is non-empty but 1:1 over
  `0x0`–`0x10_0000_0000`, a translation step the blob has no equivalent of, since the blob has no
  `soc` container at all. The same block is also named differently between them — series
  `serial@db62000` against blob `uart@db61000`, both with registers at `0x0DB6_2000` — so cross-
  referencing the two trees by node name fails where matching on `reg` succeeds. Where a node
  exists in both trees, the addresses agree. `[DT]`
  (`lga.dtsi`, series v4), `[DT]` (`lga-b0.dtb`, laguna-kernel-prebuilts; the full bus walk, tied
  to that blob's sha256, is in `resources/tensor-g5.addressing.txt`), `[standard]`
  (Devicetree Specification v0.4, sections 2.3.5, 2.3.6, and 2.3.8).

- **Boot chain and entry state.** The exact closed-firmware stage sequence is not established by
  the cited public material. The production blob reserves a region named "BL31 memory log" at
  `0x8B60_0000` (2 MiB); that name and allocation do not by themselves establish the runtime
  implementation or its exception level. The Android image layout distinguishes the
  kernel-bearing v4 boot image, the vendor boot image containing the DTB, vendor ramdisk and
  bootconfig, and the overlay table in `dtbo`, selected by board id and revision.
  The series device tree reserves DRAM for the closed stages: the ABL ramdump/log region at
  `0xBE00_0000` (16 MiB, `no-map`), bootloader logs at `0x9560_0000` (1 MiB, `no-map`), GSA
  (security core) logs at `0xA61B_0000` (16 KiB, `no-map`), and a ramoops region at
  `0x9520_0000` (4 MiB) that the ABL reads back after a crash reset. The bootloader adds the
  `/memory` node itself, patches UFS calibration data into the node the `ufs0` alias names (a
  missing alias is a fatal boot error on shipped bootloaders), enables the console UART only when
  its console is turned on. The cited flow describes the bootloader appending `console=`. It
  also supplies vendor bootconfig as an image-building input. The Android-prefixed values in the
  production command line establish their contents, not who adds each value at runtime. That
  command line carries `earlycon=uart8250,mmio32,0xdb62000`, `console=ttyS0,115200n8`,
  `androidboot.boot_devices=3c400000.ufs`, and `androidboot.hardware.platform=laguna`. The
  upstream flow packs whole DTBs into the vendor boot image (`mkbootimg --header_version 4`) and
  erases `dtbo`. `[DT]` (`lga.dtsi`, series v4, `reserved-memory`), `[DT]` (`lga-b0.dtb`,
  laguna-kernel-prebuilts, `reserved-memory` and `chosen`), `[doc]` (series v4 cover letter and
  patch 3/4 message; Android boot image header page; Android DTB/DTBO partitions page;
  pixelscripts Makefile), `[standard]` (arm64 `booting.rst`, the entry contract a Linux Image
  expects), `[inference]` (premises, `[source-observed]`, established by reading the production
  command line in every reachable public blob and searching every overlay entry besides: it
  carries a protected-KVM module list and SMMU-under-KVM options,
  and carries no parameter that switches protected mode on. Derivation: these options indicate
  an intended hypervisor configuration; they establish neither the kernel's build configuration
  nor the firmware's actual hand-off state. Confidence: an indication of intended configuration
  only. Establishing the build configuration requires evidence from the matching kernel build;
  establishing the entry exception level requires reading `CurrentEL` at entry).
  `TODO (verify on hardware)`: the exception level, MMU and cache state, and x0 at hand-off, none
  of which any public document states — read `CurrentEL` rather than assuming EL2.
- **Silicon revisions and SoC id.** B0 silicon is what mass-production phones carry and what the
  upstream device tree targets; A0 silicon shipped on EVT devices, and the same device tree boots
  on them so far. The bootloader identifies the SoC by a 16-bit product id `0x0005` plus a major
  and minor nibble: A0 = `0x000500`, B0 = `0x000510`. The two production blobs differ only in
  DVFS and energy-model tables, in chip-info compatibles (`google,lga_a0_dvfs` versus
  `google,lga_b0_dvfs`), in the root-level `soc_compatible` node, whose child is renamed `A0` to
  `B0` with `major` 0 versus 1, and in the early-hardlockup-detector node (`pmu-ehld` on A0,
  `ehld-coreinstr` on B0; the separately named `hardlockup-watchdog` node is identical in both),
  which B0 restructures into child nodes and gives an extra register
  window at `0x200C_0504` (`0x24` bytes) and a clock input that A0 has no counterpart for; no
  peripheral address, interrupt or clock differs. `[doc]` (series
  v4 cover letter and patch 3/4 message; series v1 patch 1/4 message), `[DT]` (`lga-a0.dtb` and
  `lga-b0.dtb`, laguna-kernel-prebuilts).
- **SMP topology.** Eight cores in one `cpu-map` cluster: `cpu@0`, `cpu@100` = Cortex-A520
  (`hayes`), `cpu@200`–`cpu@600` = Cortex-A725 (`hunter`), `cpu@700` = Cortex-X4 (`hunterelp`).
  DT `reg` = MPIDR with the core index in Aff1 (core N → `N << 8`, Aff0 = 0); pass that as the
  PSCI target. Every core has `enable-method = "psci"` and the `psci` node is `arm,psci-1.0`
  with `method = "smc"`: secondary cores start with PSCI `CPU_ON`, no spin-table. Idle is PSCI
  too: per-core C2 states (`local-timer-stop`, suspend parameter `0x40000003`), cluster power
  domains grouping cores 2–4 and 5–7 (`0x40010033`) under a top domain (`0x40020333`). Capacity
  ratios 258 / 891 / 1024. The production blob uses generic `arm,armv8` cpu compatibles and
  reserves SGIs 8–15 for the Trusty TEE's IPIs. `[DT]` (`lga.dtsi`, series v4, cpu, cpu-map,
  and psci nodes), `[DT]` (`lga-b0.dtb`, laguna-kernel-prebuilts, cpus and trusty nodes),
  `[standard]` (PSCI DEN 0022; DDI 0487, MPIDR_EL1). `TODO (verify on hardware)`: which core the
  bootloader hands off on.
- **Interrupts.** `arm,gic-v3`: GICD at `0x0588_0000` (64 KiB); the redistributor region at
  `0x0590_0000`, size `0x20_0000`, which for eight cores is `0x4_0000` per redistributor, the
  four-frame stride of a redistributor with the GICv4 VLPI/VSGI pages. `#interrupt-cells = 4`
  (type, number, flags, PPI partition or 0); SPI n → INTID `32 + n`, PPI n → `16 + n`. The
  maintenance interrupt is PPI 9. Two `ppi-partitions`: partition 0 is the seven A520/A725 cores,
  partition 1 the single Cortex-X4. GICv3 means a system-register CPU interface (`ICC_*`),
  per-core redistributor wake, and affinity routing; no GICv2 MMIO CPU interface exists. Most
  low-speed peripherals do not reach the GIC directly: Google "GIA" level aggregators
  (`google,level-gia`, one interrupt cell, a 16-byte register window, one upstream line each) fan
  them in, and a peripheral's `interrupts-extended` names the aggregator and a line. There are 90 of
  them in the production blob, all direct children of `/`, but the fan-in is a tree rather than a
  single level: 37 present their upstream line to the GIC, and the other 53 name another aggregator
  as their interrupt parent, so resolving a peripheral's interrupt means following the chain until
  it reaches the GIC rather than assuming the first aggregator is the last. The three that serve
  the low-speed UART islands reach the GIC directly: LSIO-S at `0x3BD6_0400` → SPI 694, LSIO-E at `0x3A16_0400` → SPI 704, and LSIO-N at
  `0x0D96_0400` → SPI 684.
  `[DT]` (`lga.dtsi`, series v4, gic node), `[DT]` (`lga-b0.dtb`, laguna-kernel-prebuilts, gic
  and aggregator nodes), `[standard]` (GICv3/v4 IHI 0069). `TODO (verify on hardware)`: the
  exact GIC product and version from GICD_PIDR2/GICR_TYPER, the redistributor stride, and the
  aggregator register model, which no public document describes.
- **Debug UART.** DesignWare 16550-class (`google,lga-uart`, falling back to
  `snps,dw-apb-uart`; the compatible is in mainline's binding), **not a PL011**: `serial@db62000`,
  label `lsion_cli16_uart`, base `0x0DB6_2000`, 256-byte window, IRQ SPI 688 (INTID 720,
  level-high), `reg-shift = 2`, `reg-io-width = 4` (16550 register indices at a 32-bit stride,
  mmio32; THR/RBR at `0x00`, LSR at `0x14`), `clock-frequency = 200000000` with no clock handle in
  the public tree. It is the only one of the 22 UARTs wired straight to the GIC, and it belongs to
  "CLI" (configurable low-speed interface) block 16 of the LSIO-N island: the CLI block sits at
  `0x0DB6_0000`, its I2C personality at `+0x1000`, the UART at `+0x2000`, SPI at `+0x3000` and
  the I3C master at `+0x4000` (a `0x2A0` window). Every personality node is named after the
  block's `+0x1000` address rather than its own base, which for the I2C personality happens to be
  its own base and for the UART, SPI and I3C nodes does not; every other CLI follows the same
  layout. The series leaves the node `status = "disabled"`: the
  bootloader enables the block when its console is on and programs the baud, so the DT never
  fixes one; `serial0` and `stdout-path` point at it. The production blob's node (`uart@db61000`,
  compatible `goog,goog-dw-apb-uart`, same `reg` and interrupt) names clocks `baudclk` (rates
  to 200 MHz) and `apb_pclk` from the CPM clock controller, a reset from the LSIO-N bank, a power
  domain, and a `cli16_uart` pin group. Console device `ttyS0`; `earlycon=uart8250,mmio32,0xdb62000`
  is what the production command line passes, at 115200n8; the upstream flow instead passes a
  bare `earlycon`, which `stdout-path` then resolves, alongside its own `console=pstore`; the real
  `console=` is appended by the bootloader (Quick-facts/2). The flow requests 3,000,000 baud
  only when the UART mux query does not report virtual selection. With virtual muxing this step
  preserves the user's existing baud setup. The production command line separately records
  115200n8; the baud of a particular live unit remains untested. Register model and
  the DesignWare busy quirk: see `dw-apb-uart`. `[DT]` (`lga.dtsi` and `lga-pixel-common.dtsi`,
  series v4), `[DT]` (`lga-b0.dtb`, laguna-kernel-prebuilts, `uart@db61000`, `aliases`, and
  `chosen`), `[standard]` (`snps-dw-apb-uart.yaml` binding at mainline head; 16550 register
  model), `[doc]` (series v4 patch 3/4 message, for the bootloader enabling it; pixelscripts
  Makefile, for the earlycon and baud it uses). `TODO (verify on hardware)`: the baud a given
  unit's bootloader leaves configured, the pinmux register values, and the earlycon string on a
  live boot.
- **Other UARTs.** 21 more DesignWare UARTs of the same shape (`reg-shift = 2`,
  `reg-io-width = 4`, 256-byte windows, `baudclk` and `apb_pclk` from the CPM, a per-island reset
  and power domain, `default`/`sleep`/`cli` pin groups, all disabled), one per CLI block: seven
  in LSIO-S (`0x3BF0_2000`–`0x3BF6_2000`, aliases `uart0`–`uart6`), eight in LSIO-E
  (`0x3A30_2000`–`0x3A37_2000`, `uart7`–`uart14`, with `uart9` = `serial2` and `uart12` =
  `serial1`, a UART-logging port), and six more in LSIO-N (`0x0DB0_2000`–`0x0DB5_2000`,
  `uart15`, `uart17`–`uart21`). All of them interrupt through the island's GIA aggregator, not the
  GIC. The `instances:` table places every one. No PL011 exists on this SoC. `[DT]`
  (`lga-b0.dtb`, laguna-kernel-prebuilts, `aliases` and the `uart@*` nodes).
- **Timers.** Arm generic timer (`arm,armv8-timer`), PPIs 13 / 14 / 11 / 10 = secure-physical /
  non-secure-physical / virtual / hypervisor, all level-low, partition cell 0 (the production
  blob encodes the same lines with the legacy CPU-mask flag bits set). No public tree gives a
  counter frequency; a 38.4 MHz fixed clock (`osc`) is the SoC's reference and clocks the two
  `google,wdt` watchdogs at `0x200C_4000` and `0x200C_5000` (4 KiB each; the upstream flow
  disables the watchdog from fastboot on frankel and blazer), but nothing ties it to the counter.
  Read `CNTFRQ_EL0`. `[DT]` (`lga.dtsi`, series v4, timer and osc nodes), `[DT]` (`lga-b0.dtb`,
  laguna-kernel-prebuilts, timer and watchdog nodes), `[standard]` (DDI 0487, the generic timer),
  `[doc]` (pixelscripts Makefile). `TODO (verify on hardware)`: the counter frequency.
- **Clocks and power.** Firmware-owned through a mailbox. The public series declares one fixed
  clock, `osc` at 38.4 MHz, and a fixed `clock-frequency` on the UART. The production blob's
  clock controller (`google,cpm-clk`) has no register window of its own: each clock is a
  request to the CPM power manager over a `google,mba-ctrl` mailbox pair at `0x0526_0000` (SPI
  250, requests) and `0x0526_1000` (SPI 251, responses), with per-island reset banks
  (`google,cpm-rst`: HSIO-N 16, HSIO-S 5, LSIO-S 45, LSIO-N 43, LSIO-E 50 lines) and a
  `google,lga-power-controller` for power domains shaped the same way. The main PMIC is a
  Renesas/Dialog DA9188 (`google,da9188mfd`) reached through the same mailbox, with its rails
  marked monitor-only for the OS (VDD_CPU2 for the big core, VDD_CPU1 for the mid cores, and
  so on); an SPMI controller (`smartdv,spmi`) at `0x053F_1000` (`0x300`, 19 MHz) carries the
  Maxim MAX77779-family PMIC, charger, fuel gauge, and the MAX77759 Type-C controller that the
  board overlays add. USB fixed clocks: 19.2 MHz reference, 250 MHz bus, 200 kHz suspend. OTP
  shadow syscons at `0x053D_1000` (CPM), `0x0DE2_6000`, and `0x3441_F000` carry chip id and
  PHY trims. So bringing a peripheral up means a mailbox transaction to firmware for its clock,
  reset, and power domain, not a register write, and the protocol is not public; the console UART
  is left running by the bootloader. `[DT]` (`lga.dtsi` and `lga-pixel-common.dtsi`, series v4),
  `[DT]` (`lga-b0.dtb`, laguna-kernel-prebuilts, cpm_clk, cpm_rst, mailbox, da9188mfd, spmi,
  and chip-info nodes; `dtbo.img` entry 12 for the SPMI clients), `[standard]`
  (`google,lga-dwc3.yaml` binding at mainline head, for the clock, reset, and power-domain names
  a USB instance needs). `TODO (verify on hardware)`: the mailbox protocol and the PMIC rails.
- **GPIO and pinmux.** Ten `pinctrl-single`-style banks, one per island, each a GPIO controller
  (two cells) except the HSIO-S standby bank: LSIO-E `google,lga-lsioe-pinctrl` at `0x3A20_0000`
  (`0x2_0000`), LSIO-N `google,lga-lsion-pinctrl` at `0x0DA0_0000` (`0x8000`), LSIO-S
  `google,lga-lsios-pinctrl` at `0x3BE0_0000` (`0x3_7000`), HSIO-S `google,lga-hsios-pinctrl` at
  `0x3C59_0000` (`0xF000`), HSIO-S standby `google,lga-hsios-stby-pinctrl` at `0x3C56_8000`
  (`0x2000`), HSIO-N `google,lga-hsion-pinctrl` at `0x0C58_0000` (`0xC000`), CPM
  `google,lga-cpm-pinctrl` at `0x0528_0000` (`0x3_9000`), AoC `google,lga-aoc-pinctrl` at
  `0x0B40_0000` (`0x5_B000`) plus `0x052B_9000` (`0x1_2000`), GDMC `google,lga-gdmc-pinctrl`
  at `0x0648_0000` (`0x1_5000`), DPU `google,lga-dpu-pinctrl` at `0x0EC7_E000` (`0x2000`). A
  UART's pin group is three registers under its island's CLI node; line names and per-signal
  groups come from the board overlay. No pin controller is in the public series or in mainline.
  `[DT]` (`lga-b0.dtb`, laguna-kernel-prebuilts, `pinctrl@*` nodes; `dtbo.img` entry 12), `[doc]`
  (series v1 thread, on upstream pinctrl being new work). `TODO (verify on hardware)`: the
  register model of a bank.
- **USB.** One Synopsys DWC3 dual-role controller (`snps,dwc3`, core at `0x0C40_0000`, size
  `0xD060`, SPI 580 level-high, super-speed, role-switch default peripheral, behind the `amb`
  SMMU) under Google's wrapper (`google,lga-dwc3` in mainline; the production node's wrapper
  windows are `0x0C45_0000`/`0x14` host-config CSR, `0x0C45_0020`/`0x8` USB-interrupt CSR,
  `0x0C45_0028`/`0x4` top config) with PME wake interrupts SPI 597 (high-speed) and 598
  (super-speed); the binding names its clocks `non_sticky`, `sticky`, resets `non_sticky`,
  `sticky`, `drd_bus`, `top`, and power domains `psw`, `top`. The PHY (`google,lga-usb-phy`, a
  Synopsys eUSB2 plus USB 3.2/DP combo) has windows `0x0C41_0000`/`0x2_0000` (USB3/DP core),
  `0x0C43_0000`/`0x1000` (TCA), `0x0C44_0000`/`0x1_0000` (USB2 core), `0x0C63_7000`/`0xA0` (DP
  top) in the binding and nine windows plus a firmware file and OTP trims in the production
  node; `#phy-cells = 1` (0 = HS, 1 = SS, 2 = DP). Both drivers are in mainline
  (`drivers/usb/dwc3/dwc3-google.c`, `drivers/phy/phy-google-usb.c`). `[standard]`
  (`google,lga-dwc3.yaml` and `google,lga-usb-phy.yaml` bindings at mainline head, whose
  examples place the same addresses), `[DT]` (`lga-b0.dtb`, laguna-kernel-prebuilts,
  `usb3@c450000`, `dwc3@c400000`, and `usb_phy@c410000`).
- **UFS, PCIe, and the modem.** UFS host `google,ufshc` at `0x3C40_0000` (`0x1000`; top
  `0x3C41_0000`/`0x504`; PHY SRAM `0x3C70_0000`/`0x1_4000`), SPIs 542–557 plus an aggregator
  line, clocks `ref_clk` and `aux_clk`, behind the `inf` SMMU; it is the boot device
  (`3c400000.ufs`) and the node the bootloader writes calibration into. Two PCIe root complexes
  (`google,lga-pcie`) at `0x0C50_0000` (HSIO-N, SPIs 568–575) and `0x3C50_0000` (HSIO-S, SPI
  524) with 1 MiB configuration windows at `0x4000_0000` and `0x6000_0000`; the modem is a
  Samsung Exynos modem on PCIe (`samsung,exynos-cp` in the board overlay; `exynos,modem_if`
  carveouts at `0xEA40_0000`, `0xE800_0000`, `0xF620_0000` in the SoC blob). `[DT]`
  (`lga-b0.dtb`, laguna-kernel-prebuilts, ufs, pcie, and reserved-memory nodes; `dtbo.img`
  entry 12). `TODO (verify on hardware)`: the modem part.
- **Security, IOMMU, and interconnect.** The GSA security core's mailbox at `0x0E01_0000`
  (`google,gs101-gsa-v1`); a Trusty TEE over SMC; seven `arm,smmu-v3` instances of 256 KiB each
  (`amb` `0x05B8_0000`, `dpu` `0x0ED8_0000`, `ispfe` `0x0FD0_0000`, `gpu` `0x34C0_0000`, `inf`
  `0x3510_0000`, `tpu` `0x3620_0000`, `aur` `0x385C_0000`) with a protected-KVM SMMU region at
  `0x1_0000_0000` (4 GiB); a coherent mesh (`google,booker-ci`) at `0x1000_0000` with error SPIs
  71–74. `[DT]` (`lga-b0.dtb`, laguna-kernel-prebuilts), `[standard]` (Arm SMMUv3 IHI 0070 for
  the SMMU register model).
- **Reserved memory beyond the series.** The production blob also reserves, among others, an
  always-on-core region at `0x8D20_0000` (48 MiB), a security-core region at `0xA240_0000`
  (about 62 MiB), TPU firmware at `0x9FC0_0000` (20 MiB), GPU firmware at `0xB9F0_0000`
  (33 MiB), DSP regions from `0xA140_0000`, the BL31 log at `0x8B60_0000`, xHCI DMA pools at
  `0x0901_0000`, `0x0905_0000`, and `0x9700_0000`, and the modem carveouts above; treat the
  static list as a template and parse the live tree. `[DT]` (`lga-b0.dtb`,
  laguna-kernel-prebuilts, `reserved-memory`).
- **DTB runtime patching.** The bootloader inserts `/memory` (do not put a memory node in the
  static tree; the production placeholder is 256 MiB), writes UFS calibration data into the
  `ufs0`-aliased node, appends `console=` to the command line when its console is on, passes
  Android bootconfig (`androidboot.*`, including the lock state) rather than only `bootargs`, and
  expects the ramoops region where the tree puts it. Parse the live DTB and bootconfig. `[doc]`
  (series v4 cover letter and patch 3/4 message; pixelscripts Makefile; Android locking and
  unlocking page for bootconfig), `[DT]` (`lga.dtsi`, series v4, `reserved-memory`), `[DT]`
  (`lga-b0.dtb`, laguna-kernel-prebuilts, `memory@80000000` and `chosen`).

- **DRAM extent.** DRAM starts at `0x8000_0000`. The production blob's `memory@80000000` node
  declares only 256 MiB, which is a bootloader-patched placeholder rather than a hardware fact —
  the bootloader inserts the real `/memory` (see Quick-facts/2), so do not read a size from it.
  DRAM does extend above the 32-bit boundary: reserved-memory `alloc-ranges` reach
  `0x8_8000_0000`–`0xA_0000_0000`. That endpoint rests on a reading the blob is not consistent
  about, and an implementer sizing DRAM from it should know why. Five 12-cell `alloc-ranges`
  properties in that container decode sensibly only as two address cells plus **one** size cell,
  while a sixth in the same container, on `google_gem_dma_region`, is four cells and decodes
  cleanly as 2+2, under a container declaring two of each. The `0xA_0000_0000` top follows from the
  2+1 reading alone. `[DT]` (`lga-b0.dtb`, laguna-kernel-prebuilts, `memory` and `reserved-memory`).
  `TODO (verify on hardware)`: the DRAM map beyond its base.

## Gotchas

- **Google publishes no kernel for this part.** No `laguna` repository exists on
  android.googlesource.com (its per-device kernel list runs akita to zumapro and stops) and the
  Build Pixel kernels page lists no Pixel 10 row; what exists publicly is a third-party source
  repository and the prebuilt kernels and DTBs built from it. The public map is an unmerged
  series plus decompiled production blobs, and a value taken from a blob must say so. `[doc]`
  (Android Build Pixel kernels page; GrapheneOS source page)
- **Clocks, resets, and regulators are mailbox requests to firmware, not MMIO.** The clock
  controller has no register window; a bare-metal bring-up cannot ungate a clock by poking a
  CRU, and the mailbox protocol is undocumented. Use what the bootloader leaves running (the
  console UART) until the protocol is established. `[DT]` (`lga-b0.dtb`, laguna-kernel-prebuilts,
  cpm_clk and mailbox nodes). `TODO (verify on hardware)`: the protocol.
- **GICv3-family with four interrupt cells**, not GICv2 and not three cells: the fourth cell is a
  PPI-partition phandle (or 0). A GICv2 driver or a three-cell interrupt parser will not work.
  `[DT]` (`lga.dtsi`, series v4, gic node), `[standard]` (IHI 0069)
- **Only the console UART interrupts through the GIC.** Every other UART, and most low-speed
  I/O, sits behind a GIA aggregator with its own undocumented register window; an interrupt
  number copied from a `uart@` node is a line on the aggregator, not a GIC SPI. `[DT]`
  (`lga-b0.dtb`, laguna-kernel-prebuilts, `interrupts-extended` on the `uart@*` nodes)
- **The console is a DesignWare 8250 at a 32-bit stride, left disabled in the DT.** PL011 offsets
  do not apply, and if the bootloader's console is off the line is silent whatever the kernel
  does. `[DT]` (`lga.dtsi`, series v4, `serial@db62000`), `[doc]` (series v4 patch 3/4 message)
- **Shipped bootloaders refuse a DTB without a `ufs0` alias**, and they add the memory node
  themselves; the upstream tree deliberately omits both, and the flashing scripts patch the alias
  in. `[doc]` (series v4 cover letter; pixelscripts Makefile, which applies the overlay, and
  the `lga-ufs-placeholder.dtso` header in that repository)
- **Entry exception level is not published.** Verify `CurrentEL`; do not assume EL2 from other
  Android phones or from the protected-KVM command line. `[standard]` (arm64 `booting.rst`, which
  only fixes what an Image expects). `TODO (verify on hardware)`: the level and the MMU/cache
  state at hand-off.
- **The production blob's node names lie about unit addresses.** The console is `uart@db61000`
  with `reg` `0xDB62000`; every CLI's UART node is named after the block's `+0x1000` personality
  address. Trust `reg`, not the node name. `[DT]` (`lga-b0.dtb`, laguna-kernel-prebuilts)
- **This is not the Pixel 10a's chip.** The Pixel 10a carries an Exynos-derived Tensor from the
  G1–G4 generation; the cover letter groups it with those and does not say which. Nothing here
  applies to it. `[doc]` (series v4 cover letter)
