---
kind: soc
id: <soc-id>
name: <SoC vendor and part number>
triggers: [<part number>, <family alias>]
cache: <short>-resources
resources:
  repos:
    - name: <linux repo short name>
      url: <repo URL>
      ref: <branch>
      license: GPL-2.0-only
      files:
        - <SoC .dtsi>
        - <pinctrl .dtsi>
        - <console UART driver; read for behavior only>
        - <irqchip driver>
        - <clock driver>
        - Documentation/arch/arm64/booting.rst
      note: <vendor/downstream or mainline, and why this one>
    - name: arm-trusted-firmware
      url: https://github.com/ARM-software/arm-trusted-firmware
      ref: master
      license: BSD-3-Clause
      files:
        - plat/<vendor>/<platform>
      note: BL31 (the EL3 runtime), PSCI<, and the SCMI server if applicable>
    - name: u-boot
      url: <U-Boot repo URL>
      ref: <branch>
      license: GPL-2.0-or-later
      note: BL33
  docs:
    - title: <Primary TRM / datasheet>
      url: <URL or mirror>
      access: public
      cite: true
      note: <NDA status; the public proxy part if the exact one is NDA>
    - title: <UART IP databook (16550 / PL011 / DesignWare DW_apb_uart, ...)>
      url: <URL>
      access: public
      cite: true
    - title: <GIC architecture specification (IHI 0048 for GICv2, IHI 0069 for GICv3)>
      url: <URL>
      access: public
      cite: true
    - title: Power State Coordination Interface, PSCI (DEN 0022)
      url: https://developer.arm.com/documentation/den0022/latest
      access: public
      cite: true
    - title: ARMv8-A Architecture Reference Manual (DDI 0487)
      url: https://developer.arm.com/documentation/ddi0487/latest
      access: public
      cite: true
      note: exception levels, the generic timer, the MMU
  tools: []
---

<!--
SPDX-FileCopyrightText: <year> contributors
SPDX-License-Identifier: Apache-2.0
-->

# <SoC display name>

## Orientation

<One paragraph: core topology, where peripherals sit, who owns clocks, what is on-SoC versus
off-SoC, whether a public datasheet exists.>

## Quick-facts

<Every bullet ends with a provenance tag. Drop bullets that don't apply, but cover at least these
dimensions. Mark anything unverified `TODO (verify on hardware)`.>

- **Addressing model.** <Flat versus high window; `#address-cells`/`#size-cells` at the root and on
  the peripheral bus; any `ranges` translation trap; a worked example address (the debug UART).> `[DT]`
- **Boot chain and entry state.** <BootROM → … → OS image; the entry exception level, MMU/cache
  state, DTB-pointer register; resident firmware regions to avoid.> `[doc]`, `[standard]`
- **SMP topology.** <Core count and clusters; cpu `reg` → MPIDR mapping; secondary-core release (PSCI
  `CPU_ON` versus spin-table); the boot core.> `[DT]`, `[standard]`
- **Interrupts.** <GIC version; GICD/GICR/GICC addresses; DT `#interrupt-cells`; SPI→INTID and
  PPI→INTID base.> `[DT]`, `[standard]`
- **Debug UART.** <IP type; base address; IRQ; `reg-shift`/`reg-io-width`; default baud; the
  `earlycon=` string; the TX-ready flag; pinmux requirement.> `[DT]`, `[databook]`
- **Timers.** <Arch timer frequency (read `CNTFRQ_EL0`); the PPIs; any on-SoC timer block.> `[standard]`
- **Clocks and power.** <Firmware-owned (mailbox/SCMI) versus OS-managed (CRU/PMIC); what bringing a
  peripheral up requires (ungate clock, deassert reset); the PMIC part.> `[DT]`, `[databook]`
- **GPIO and pinmux.** <Bank addresses; the syscon/GRF for IOMUX/drive/pull; the pinctrl compatible.> `[DT]`
- **DTB runtime patching.** <What firmware/BL31 fills in; parse the live DTB.> `[doc]`

## Gotchas

<Two to seven bullets: the SoC-level deviations from common assumptions (wrong base region,
GICv3-not-GICv2, console IP confusion, clocks the OS must program itself, mandatory blobs, entry
EL). Each ends with a tag.>
