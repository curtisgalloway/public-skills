---
kind: board
id: indiedroid-nova
name: Indiedroid Nova (ameriDroid; same hardware as the 9Tripod Pico PC V2.0)
triggers: [indiedroid nova, indiedroid, nova, pico pc v2]
parts: [rk3588s]
cache: rk3588-resources
resources:
  repos:
    - name: linux-mainline
      url: https://github.com/torvalds/linux
      ref: master
      license: GPL-2.0-only
      files:
        - arch/arm64/boot/dts/rockchip/rk3588s-indiedroid-nova.dts
      note: >-
        The Nova is fully mainlined; the board device tree is here. A stable branch such as
        linux-6.12.y also carries it. Read for behavior only; cite the TRM.
    - name: u-boot
      url: https://github.com/u-boot/u-boot
      ref: master
      license: GPL-2.0-or-later
      files:
        - arch/arm/dts/rk3588s-indiedroid-nova-u-boot.dtsi
      note: BL33; mainline U-Boot has RK3588 support and a Nova board file
    - name: rkbin
      url: https://github.com/rockchip-linux/rkbin
      ref: master
      license: Rockchip proprietary blobs; see the repository
      note: prebuilt DDR-init and BL31 blobs, required to assemble a bootable image
  docs: []
  tools: []
---

<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Indiedroid Nova

## Orientation

The Indiedroid Nova (distributed by ameriDroid; identical hardware to the 9Tripod Pico PC V2.0) is a
Raspberry-Pi-4-form-factor single-board computer built on the **Rockchip RK3588S** (see the
`rk3588s` spec). All I/O is on the SoC: there is no companion chip. The SoC spec carries the
addressing model, boot chain, GIC, UART, timers, clocks, and pinmux; this spec carries only what the
Nova board decides on top of that: the console pin group, its baud, and the power rails.

## Quick-facts

- **Boot media and chain.** The Rockchip BootROM → DDR-init and TPL/SPL → TF-A BL31 → U-Boot → kernel
  chain applies unchanged; assembling a bootable image needs the DDR-init and BL31 blobs from
  `rkbin` or a self-built TF-A. Mainline U-Boot carries a Nova board file. Entry state and
  secondary-core release are SoC facts: see `rk3588s`. `[doc]` (rkbin repository; U-Boot board file)
- **Debug console.** UART2 (the RK3588S debug UART, a DesignWare 8250; see `rk3588s` instance
  `uart2`) with the Nova default **`serial2:1500000n8`** (1.5 Mbaud). `[DT]`
  (`rk3588s-indiedroid-nova.dts`, `/chosen` stdout-path)
- **Console pin group.** The Nova routes UART2 through the **`uart2m0_xfer`** pin group, overriding
  the SoC base default of `uart2m1_xfer`; a from-reset bare-metal path must set the GRF IOMUX for
  the **m0** pins or the line stays silent. U-Boot normally muxes them already. `[DT]` (`rk3588s-indiedroid-nova.dts` pinctrl override). `TODO (verify on hardware)`: the exact
  pins and GRF registers, against the TRM GRF chapter and the RK3588S pinctrl DT.
- **Power.** Board voltage rails come from an external RK806-class PMIC; the Nova uses `rk8602` /
  `rk8603` regulators over I²C/SPI. `[DT]` (`rk3588s-indiedroid-nova.dts` regulator nodes)
- **Headers and board-level GPIO.** `TODO (verify on hardware)`: the 40-pin header assignment and
  the storage (eMMC / microSD / NVMe) wiring are not recorded here yet.
- **Product documentation.** `TODO (verify on hardware)`: no board-level datasheet or schematic URL is recorded
  here yet; the SoC spec's TRM and datasheet mirrors are the citable authorities.

## Gotchas

- The console is the SoC's DW 8250 at 1.5 Mbaud, not a PL011 at 115200; a terminal at the wrong baud
  shows garbage, not silence. `[DT]` (`rk3588s-indiedroid-nova.dts`, `chosen` and `uart2`)
- Silence despite a correct UART2 base address means the **m0** IOMUX is not set; the SoC default is
  **m1**. `[DT]` (`rk3588s-indiedroid-nova.dts`, `uart2` pinctrl)
- `rkbin` (DDR init + BL31) or a self-built TF-A is mandatory; the BootROM → SPL → BL31 → BL33 chain is Rockchip-specific and cannot be skipped. `[doc]` (rkbin repository README; TF-A
  Rockchip platform page)
