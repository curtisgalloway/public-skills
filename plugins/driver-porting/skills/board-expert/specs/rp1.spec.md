---
kind: chip
id: rp1
name: Raspberry Pi RP1 I/O southbridge
triggers: [rp1]
cache: rpi5-resources
instances:
  - name: uart0
    ip: pl011
    reg: null
    irq: null
    clocks: []
    role: 40-pin header console
    note: >-
      PL011 inside RP1, reached only through PCIe. Offset within the RP1 window, IRQ routing, and
      clock TODO (verify on hardware); the other RP1 UART instances TODO (verify on hardware).
resources:
  repos:
    - name: linux-rpi
      url: https://github.com/raspberrypi/linux
      ref: rpi-6.12.y
      license: GPL-2.0-only
      files:
        - arch/arm64/boot/dts/broadcom/rp1.dtsi
      note: the RP1 device-tree fragment included by every Pi 5 board .dts
  docs:
    - title: RP1 peripherals datasheet
      url: https://datasheets.raspberrypi.com/rp1/rp1-peripherals.pdf
      access: public
      cite: true
      note: authoritative for all RP1 I/O; §2.3.1 covers PCIe and the 40-bit-to-peripheral mapping
  tools: []
---

<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# RP1 I/O southbridge

## Orientation

RP1 is the I/O chip on the Raspberry Pi 5 and Compute Module 5, connected to the BCM2712 over an
internal x4 PCIe link (`pcie2`). It carries USB, Gigabit Ethernet, the 40-pin-header GPIO, most
UART/I²C/SPI instances, and the header SD interface. It has a public datasheet, which is the citation
of record for everything on it.

## Quick-facts

- **How it is reached.** Behind the SoC's internal x4 PCIe root complex (`pcie2`); nothing on RP1 is
  reachable until that link is trained and the BARs are set up. `[databook]` (RP1 datasheet §2.3.1),
  `[DT]` (`bcm2712-rpi-5-b.dts`, `rp1.dtsi`).
- **Address window.** RP1's internal `0xc0_4000_0000` space maps through the PCIe outbound window to
  CPU physical **`0x1F_0000_0000`**; the peripheral block is `0x4000_0000`–`0x4040_0000` inside RP1,
  and not every register is accessible from the host. `[databook]` (RP1 datasheet §2.3.1), `[DT]`
  (`ranges` on the rp1 node).
- **What it carries.** USB, Gigabit Ethernet, GPIO for the 40-pin header, UART/I²C/SPI, header SD.
  Per-block offsets: RP1 datasheet. `[databook]`
- **Link state at hand-off.** Whether the link is left up for the OS image is a board/firmware
  setting (`pciex4_reset`); see the `rpi5` spec. `[doc]` (config.txt page)

## Gotchas

- The 40-pin header "console" UART is RP1's `uart0`, behind PCIe; it is not the early debug console.
  `[DT]`
- Early bring-up cannot touch RP1 at all. Use the on-SoC PL011, GIC, and timer until PCIe is up.
  `[databook]`, `[DT]`
