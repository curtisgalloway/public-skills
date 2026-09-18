---
kind: soc
id: <soc-id>
name: <SoC vendor and part number>
triggers: [<part number>, <family alias>]
not_triggers: []              # optional: names that extend a trigger but are another part
aliases: []                   # codenames, normalized like ids
cache: <board-id>-resources   # inherit the board's cache; name your own only for a shared SoC
instances: []                 # required, may be empty: one row per IP-block placement whose ip spec exists
#  - name: <instance label as the DT names it>
#    ip: <ip-id>
#    reg: <base address as an integer>
#    irq: {kind: SPI, number: <n>, intid: <32 + n>, trigger: level-high, note: "<quoted>"}
#    clocks: [<clock-names values>]   # [] when the DT gives only clock-frequency; say so in note
#    role: <what it is for>
#    note: "<quirks, or TODO (verify on hardware): what is missing>"
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
      note: "<vendor/downstream or mainline, and why this one>"   # quote: may hold ': '
    - name: arm-trusted-firmware   # omit when the platform's EL3 firmware is closed; say so in Boot chain
      url: https://github.com/ARM-software/arm-trusted-firmware
      ref: master
      license: BSD-3-Clause
      files:
        - plat/<vendor>/<platform>
      note: BL31 (the EL3 runtime), PSCI<, and the SCMI server if applicable>
    - name: u-boot                 # omit when the platform's bootloader is closed; say so in Boot chain
      url: <U-Boot repo URL>
      ref: <branch>
      license: GPL-2.0-or-later
      note: BL33
  # series:                        # unmerged patch series that are the public map; never cite: true
  #   - title: <series subject>
  #     url: <list archive URL>
  #     message_id: <message-id>
  #     target: <linux repo short name>
  #     status: unmerged
  #     files: [<paths the series adds or changes>]
  #     note: <what it establishes that the merged tree does not>
  docs:
    - title: <Primary TRM / datasheet>
      url: <URL or mirror>
      access: public
      cite: true
      note: <NDA status; the public proxy part if the exact one is NDA>
    # The UART's databook belongs to its ip spec (pl011, dw-apb-uart, ...): reference the IP spec
    # from the instances: row instead of repeating its docs here.
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

<Every bullet ends with its tag clause: tags, each with a parenthetical citation where one exists,
then at most one `TODO (verify on hardware)` sentence; `[doc]` always names its page. Drop bullets
that don't apply, but cover at least these dimensions. When the platform's firmware is closed, say
so in Boot chain and cite what the vendor publishes.>

<A `[DT]` parenthetical names the file. When the map is a series file AND a shipped blob, cite each
where it was read; the two names can differ by one letter, so spell them out:
`[DT]` (`lga.dtsi`, series v4) for the mailing-list source, `[DT]` (`lga-b0.dtb`, <prebuilt repo
name>) for the decompiled production blob, where the origin is the `name` of the repos entry.>

- **Addressing model.** <Flat versus high window; `#address-cells`/`#size-cells` at the root and on
  the peripheral bus; any `ranges` translation trap; a worked example address (the debug UART).>
  `[DT]` (`<soc>.dtsi`, series v<n>), `[DT]` (`<soc>-b0.dtb`, <prebuilt repo name>)
- **Boot chain and entry state.** <Public firmware: BootROM → … → OS image; the entry exception
  level, MMU/cache state, DTB-pointer register; resident firmware regions to avoid. Closed firmware
  and handsets: boot ROM → the vendor's closed stages (name what the DT reserves for them) → the
  product bootloader → the boot-image layout it loads (which image carries the kernel, the DTB, the
  overlays); the exception level at hand-off from the vendor's platform documentation, or
  `TODO (verify on hardware)` when it is only inferred.> `[doc]` (<page>), `[standard]` (arm64
  `booting.rst`)
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
- **DTB runtime patching.** <What firmware/BL31 fills in; parse the live DTB.> `[doc]` (<page>)

## Gotchas

<Two to seven bullets: the SoC-level deviations from common assumptions (wrong base region,
GICv3-not-GICv2, console IP confusion, clocks the OS must program itself, mandatory blobs, entry
EL). Each ends with a tag.>
