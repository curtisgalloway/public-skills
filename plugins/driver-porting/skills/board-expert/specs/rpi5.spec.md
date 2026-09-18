---
kind: board
id: rpi5
name: Raspberry Pi 5 / Compute Module 5
triggers: [raspberry pi 5, pi 5, pi5, rpi5, cm5, compute module 5]
parts: [bcm2712, rp1]
cache: rpi5-resources
resources:
  repos:
    - name: linux-rpi
      url: https://github.com/raspberrypi/linux
      ref: rpi-6.12.y
      license: GPL-2.0-only
      files:
        - arch/arm64/boot/dts/broadcom/bcm2712-rpi-5-b.dts
      note: >-
        Raspberry Pi downstream kernel: the real Pi 5 board device tree. Shallow-clone at the ref.
        Read for behavior only; cite the datasheets.
    - name: rpi-firmware
      url: https://github.com/raspberrypi/firmware
      ref: master
      license: see LICENCE.broadcom in the repository
      note: precompiled boot firmware and device-tree overlays as shipped on the boot partition
    - name: rpi-arm-trusted-firmware
      url: https://github.com/raspberrypi/arm-trusted-firmware
      ref: master
      license: BSD-3-Clause
      note: Raspberry Pi's fork of TF-A; the armstub the board firmware loads as BL31
  docs:
    - title: config.txt options (Raspberry Pi documentation)
      url: https://www.raspberrypi.com/documentation/computers/config_txt.html
      access: public
      cite: true
      note: pciex4_reset and the other firmware options that change what the OS image inherits
  tools: []
---

<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Raspberry Pi 5 / Compute Module 5

## Orientation

The Pi 5 and CM5 pair the **BCM2712** SoC (see the `bcm2712` spec) with the **RP1** I/O southbridge
(see the `rp1` spec) across an internal x4 PCIe link. Almost every connector on the board hangs off
RP1: USB, Gigabit Ethernet, the 40-pin header, most UART/I²C/SPI, header SD. The on-SoC blocks an early
bring-up can reach without PCIe are the debug UART, the GIC, and the timer. The dedicated 3-pin debug
connector is the on-SoC PL011 `uart10`; the 40-pin header's console is RP1's `uart0`, unreachable
until PCIe is up.

## Quick-facts

- **Boot media and chain.** The BCM2712 VPU boot ROM runs the bootloader held in the on-board SPI
  EEPROM, which loads the armstub (TF-A BL31), the DTB, and the OS image from the boot partition;
  `config.txt` on that partition selects images and options. Entry state and secondary-core
  release are SoC facts: see `bcm2712`. `[doc]` (Raspberry Pi documentation, config.txt page; TF-A
  rpi5 platform page for the BL31 role)
- **Debug console.** The 3-pin debug connector is the on-SoC PL011 `uart10` at `0x10_7D00_1000`,
  which firmware leaves enabled; `earlycon=pl011,0x107d001000,115200n8`. `[DT]`
  (`bcm2712-rpi-5-b.dts`, `aliases { serial0 }`), `[doc]` (Raspberry Pi documentation).
  `TODO (verify on hardware)`: the earlycon string against a live boot.
- **40-pin header.** GPIO, UART, I²C, and SPI on the header are RP1 functions, not BCM2712 ones; their
  addresses live in the `rp1` spec. `[DT]` (`rp1.dtsi` as included by `bcm2712-rpi-5-b.dts`).
- **PCIe link to RP1 at hand-off.** By default the firmware resets the x4 link to RP1 before launching
  the OS image; `pciex4_reset=0` in `config.txt` leaves the root complex and RP1 BARs configured for
  bare-metal use. `[doc]` (config.txt page).
- **Power.** `TODO (verify on hardware)`: the PMIC part and its rails are not recorded here yet.

## Gotchas

- The "console" on the 40-pin header is RP1 `uart0`, behind PCIe. The early console is the debug
  connector, on-SoC `uart10`. Mixing these up is the most common Pi 5 bring-up dead end. `[DT]`
- Nothing on RP1 is reachable until PCIe is up; early bring-up uses on-SoC blocks only.
  `[databook]` (RP1 datasheet §2.3.1), `[DT]`
- Older Pi bring-up guides that poke per-core release addresses do not apply: secondary cores start
  via PSCI `CPU_ON` (see `bcm2712`). `[DT]` (`psci { method = "smc" }`)
