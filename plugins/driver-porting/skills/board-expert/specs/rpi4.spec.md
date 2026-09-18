---
kind: board
id: rpi4
name: "Raspberry Pi 4 Model B (family: Pi 400, Compute Module 4 / 4S)"
triggers: [raspberry pi 4, pi 4, pi 4b, pi4, rpi4, cm4, pi 400, compute module 4]
parts: [bcm2711]
cache: rpi4-resources
resources:
  repos:
    - name: linux-rpi
      url: https://github.com/raspberrypi/linux
      ref: rpi-6.12.y
      license: GPL-2.0-only
      files:
        - arch/arm/boot/dts/broadcom/bcm2711-rpi-4-b.dts
        - arch/arm/boot/dts/broadcom/bcm2711-rpi.dtsi
        - arch/arm/boot/dts/broadcom/bcm2711-rpi-ds.dtsi
      note: >-
        Raspberry Pi downstream kernel: the board device tree and the downstream Pi deltas.
        rpi-6.12.y is the LTS branch Raspberry Pi OS ships; the repo default has moved on, verify
        before re-cloning. Read for behavior only; cite the BCM2711 datasheet.
    - name: rpi-firmware
      url: https://github.com/raspberrypi/firmware
      ref: master
      license: see LICENCE.broadcom in the repository
      note: start4.elf and the other VPU firmware blobs; the wiki holds the mailbox property interface
    - name: rpi-documentation
      url: https://github.com/raspberrypi/documentation
      ref: master
      license: CC-BY-SA-4.0
      files:
        - documentation/asciidoc/computers/config_txt/boot.adoc
        - documentation/asciidoc/computers/configuration/interfaces.adoc
      note: >-
        Source of the official documentation site (config.txt boot options, interface configuration).
        Paths TODO (verify): the old skill cited them as legacy_config_txt/boot.adoc and
        configuration/interfaces.adoc.
    - name: rpi-tools
      url: https://github.com/raspberrypi/tools
      ref: master
      license: BSD-3-Clause
      files:
        - armstubs/armstub8.S
      note: the stock ARM stub (spin-table release, EL3 to EL2 hand-off)
  docs:
    - title: Raspberry Pi 4 Model B product datasheet
      url: https://datasheets.raspberrypi.com/rpi4/raspberry-pi-4-datasheet.pdf
      access: public
      cite: true
    - title: Mailbox property interface (Raspberry Pi firmware wiki)
      url: https://github.com/raspberrypi/firmware/wiki/Mailbox-property-interface
      access: public
      cite: true
      note: clock, voltage, power-domain, and firmware GPIO-expander tags
  tools: []
---

<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Raspberry Pi 4 Model B

## Orientation

The Pi 4B (and the Pi 400 and Compute Module 4 / 4S, which share the SoC) is built on the Broadcom
**BCM2711** (see the `bcm2711` spec): four Cortex-A72 cores with the VideoCore VI VPU co-running the
firmware that owns boot, most clocks, and power. Unlike the Pi 5 there is no southbridge: Ethernet
(GENET v5), GPIO, UARTs, and SD are all on-SoC, and the only PCIe device is the VL805 USB 3 xHCI.
The BCM2711 ARM Peripherals datasheet is public, so it is the citation of record; the kernel and
device tree are the map. The bring-up trap on this board is the console: the 40-pin header carries
the mini UART by default, not the PL011.

## Quick-facts

- **Boot media and chain.** BootROM → the **SPI-EEPROM bootloader** (there is no `bootcode.bin` on a
  Pi 4) → `start4.elf` on the VPU, which loads the DTB, the armstub, and the kernel from the boot
  partition, patches the DTB, and releases the ARM cores. The 64-bit kernel is `kernel8.img`
  (`arm_64bit=1` is the default). Entry state, load addresses, and secondary-core release are SoC
  facts: see `bcm2711`. `[doc]` (Raspberry Pi documentation, boot and config.txt pages)
- **`config.txt` options that change what the OS inherits.** `enable_uart=1` pins the VPU core clock
  so the mini UART baud is stable; `dtoverlay=disable-bt` moves PL011 UART0 to the header;
  `arm_peri_high=1` selects high-peripheral mode and needs a matching DT and armstub; `enable_gic`
  (default 1) selects the GIC-400 over the legacy ARMC controller; `armstub=bl31.bin` ships TF-A
  instead of the stock stub. `[doc]` (Raspberry Pi documentation, config.txt)
- **Header console.** On a stock Pi 4B GPIO 14/15 carry **UART1, the mini UART** (AUX block at
  `0xFE21_5040`; baud = VPU core clock / (8 × (reg + 1)), unstable unless `enable_uart=1` pins the
  core clock). PL011 **UART0 is muxed to GPIO 32/33 for Bluetooth**; `dtoverlay=disable-bt` frees it
  for the header on GPIO 14/15 ALT0. The **CM4 differs**: UART0 is the primary UART there. `[DT]`
  (`bcm2711-rpi-4-b.dts`), `[databook]` (BCM2711 datasheet ch. 2 AUX / mini-UART), `[doc]`
  (Raspberry Pi documentation, UART configuration)
- **Ethernet PHY.** On-SoC GENET v5 (see `bcm2711`) drives an on-board **BCM54213PE** PHY at MDIO
  address 1 (PHY id `0x600d84a2`), `rgmii-rxid`, no PHY interrupt line. `[DT]`
  (`bcm2711-rpi-4-b.dts`), `[standard]` (IEEE 802.3 clauses 22/28/40 for the MDIO and autoneg
  registers)
- **Firmware GPIO expander.** Board power functions are wired to the VPU firmware's GPIO expander,
  reached through the mailbox: SD_PWR_ON, VDD_SD_IO_SEL (the 1.8 V SD I/O switch), BT_ON / WL_ON,
  and the power LED. `[DT]` (`bcm2711-rpi-4-b.dts`), `[doc]` (mailbox property interface wiki)
- **USB.** The four USB ports hang off a **VL805 USB 3 xHCI** on the BCM2711's PCIe root complex;
  it is the only PCIe device on the board. `[DT]` (`bcm2711-rpi-4-b.dts`), `[doc]` (Pi 4B product
  datasheet)
- **SD.** The microSD slot is served by **EMMC2** (`0xFE34_0000`); the Arasan SDHCI (`0xFE30_0000`)
  serves the SDIO WiFi; `sdhost` (`0xFE20_2000`) is disabled on the Pi 4B. Register-level facts
  live in `bcm2711`. `[DT]` (`bcm2711-rpi-4-b.dts`)
- **Power.** `TODO (verify on hardware)`: the PMIC part and its rails are not recorded here yet.

## Gotchas

- **The header console is the mini UART, not the PL011.** GPIO 14/15 default to UART1, whose baud
  tracks the VPU core clock (`enable_uart=1` pins it); UART0 goes to Bluetooth on GPIO 32/33.
  `dtoverlay=disable-bt` frees UART0 for the header. `[DT]`, `[doc]` (Raspberry Pi documentation)
- **Ethernet is on-SoC GENET, not Pi 5's RP1.** Do not port Pi 5 (`0x1F_...`, RP1) assumptions;
  Pi 4 peripherals live at `0xFE...` / `0xFD...`. Only the VL805 USB 3 xHCI is behind PCIe. `[DT]`
- **Low- vs high-peripheral mode must be consistent** across firmware, DT, and armstub; everything
  stock assumes low (`0xFE...`). `arm_peri_high=1` without a matching DT and stub does not boot.
  `[doc]` (Raspberry Pi documentation, config.txt), `[databook]` (BCM2711 datasheet §1.2)
- **A stock Pi 4 has no EL3 runtime.** PSCI needs TF-A BL31 shipped as `armstub=`; see `bcm2711`
  for what the stock stub does instead. `[doc]` (TF-A rpi4 platform page)
