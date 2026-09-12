---
name: rpi4-expert
description: >-
  Board expert for the Raspberry Pi 4 Model B (Broadcom BCM2711; family includes Pi 400 and
  Compute Module 4/4S). Use this skill for ANY question about Pi 4 / BCM2711 / CM4 hardware,
  low-level software, or bring-up: physical/MMIO addresses, the memory map and low- vs
  high-peripheral mode, the device tree, the boot chain and exception-level hand-off (BootROM →
  SPI-EEPROM bootloader → start4.elf → armstub/TF-A → kernel), PSCI/SMP and the 4×Cortex-A72
  topology, the GIC-400 (GICv2) interrupt controller, timers, clocks/power (VPU firmware mailbox
  vs CPRMAN), the PL011 debug UART/console and the mini-UART trap, GPIO/pinmux and the BCM2711
  pull registers, GENET Ethernet, EMMC2/SDHCI, the VL805 USB on PCIe, where to find the source,
  and which datasheets to cite. Trigger whenever "Raspberry Pi 4", "Pi 4", "Pi 4B", "BCM2711",
  "CM4", "Pi 400", or "GENET" appears in a hardware/software question, even if Linux isn't
  mentioned. This skill provides the board-specific MAP; for the investigation method and the
  clean-room no-source-code rule, also load and follow the `os-investigator` skill.
---

<!--
SPDX-FileCopyrightText: 2026 Curtis Galloway
SPDX-License-Identifier: Apache-2.0
-->

# Raspberry Pi 4 Model B Expert (BCM2711)

The Pi 4B is built on the Broadcom BCM2711: 4×Cortex-A72 in a single cluster, with the
VideoCore VI VPU co-running the firmware that owns boot, most clocks, and power. Unlike the
Pi 5 there is no southbridge — Ethernet (GENET v5), GPIO, UARTs, and SD are all on-SoC; the
only PCIe device is the VL805 USB3 xHCI. Peripherals documented at legacy bus `0x7Ennnnnn`
appear to the ARM at `0xFEnnnnnn` (low-peripheral mode, the default). The **BCM2711 ARM
Peripherals datasheet is public** — cite it as the authority; use the kernel/DT as the map.

## How to run this skill (delegate; don't inline)

**rpi4-expert is a *subagent* role.** Everything below — cloning sources, reading the cache,
walking driver code — is written for the agent that *is* the expert. If you are the
main/orchestrating agent, do **not** execute this skill body inline: **spawn a subagent, have
it load this skill, and pass it the question.** Only that subagent clones/reads/manages
`~/src/rpi4-resources`. The main agent never touches the cache, never reads GPL source, and
never micromanages the cache in the subagent's prompt (no paths, no `git`/`curl`/`ls` steps —
the expert handles its own resources). The main agent's entire job is: ask the question →
receive clean-room facts back.

This split is the whole point. Letting the main agent (which writes the differently-licensed
target-OS code) run the skill body inline would pull GPL source into its context and destroy
the clean-room boundary. When in doubt, delegate.

## Method and constraints live in `os-investigator`

**Load and follow the `os-investigator` skill** for the investigation method, the report
format, and — non-negotiably — the **clean-room discipline: return hardware facts and
mechanism descriptions in your own words, never source code**, even if asked to paste it.
This board skill supplies the *where* and *what* (sources, addresses, quirks);
`os-investigator` supplies the *how*. If for any reason that skill isn't loaded, still apply
the one rule that matters most: **no source code in the output** — describe behavior, give
addresses/sequences, and link the human to the upstream file instead.

---

## Local resource cache: `~/src/rpi4-resources`

Clone and cache all Pi 4 reference material (Linux tree, TF-A, datasheets, fetched source
files) under **`~/src/rpi4-resources/`**. Reuse what's already there before re-cloning or
re-fetching (a populated cache with `CACHE_NOTES.md` already exists).

**This cache is for the rpi4-expert agent ONLY.** The main agent must not read files in
`~/src/rpi4-resources` directly — it asks rpi4-expert, which returns clean-room facts (no
source code). Keeping the cache behind this skill is what preserves the clean-room boundary.

## Sources to clone and keep locally (into `~/src/rpi4-resources`)

**Linux — Raspberry Pi downstream:**
- Repo: `https://github.com/raspberrypi/linux` (branch `rpi-6.12.y` — the LTS branch
  Raspberry Pi OS ships; the repo default has moved on, verify before re-cloning).
- Highest-value files (on `rpi-6.12.y`):
  - `arch/arm/boot/dts/broadcom/bcm2711-rpi-4-b.dts` (board)
  - `arch/arm/boot/dts/broadcom/bcm2711.dtsi`, `bcm283x.dtsi`, `bcm2711-rpi.dtsi`,
    `bcm2711-rpi-ds.dtsi`, `bcm270x.dtsi`, `bcm2835-rpi.dtsi` (SoC + downstream deltas)
  - Drivers, read for *behavior* only: `drivers/pinctrl/bcm/pinctrl-bcm2835.c` (covers 2711),
    `drivers/mmc/host/sdhci-iproc.c`, `drivers/net/ethernet/broadcom/genet/bcmgenet.c`,
    `drivers/net/phy/broadcom.c`, `drivers/tty/serial/amba-pl011.c`
  - arm64 entry-state contract: `Documentation/arch/arm64/booting.rst`

**Boot / firmware:**
- Trusted Firmware-A (BL31-only port; PSCI via SMC): `https://github.com/ARM-software/arm-trusted-firmware`
  → `plat/rpi/rpi4`, `docs/plat/rpi4.rst` (BSD-3-Clause)
- Stock ARM stub (spin-table; BSD-3-Clause): `https://github.com/raspberrypi/tools`
  → `armstubs/armstub8.S`
- VPU firmware blobs + mailbox wiki: `https://github.com/raspberrypi/firmware`
  (start4.elf; wiki has the Mailbox property interface)
- Official docs source: `https://github.com/raspberrypi/documentation`
  (`legacy_config_txt/boot.adoc`, `configuration/interfaces.adoc`)

**Datasheets & specs (cite these, not the kernel):**
- **BCM2711 ARM Peripherals, release 4 (2022-01-18)** — PUBLIC:
  `https://datasheets.raspberrypi.com/bcm2711/bcm2711-peripherals.pdf`.
  §1.2 address maps · ch. 2 AUX/mini-UART · ch. 4 DMA · ch. 5 GPIO · ch. 6 interrupts/GIC ·
  ch. 10 system timer · ch. 11 PL011 · ch. 12 ARM timer.
- Pi 4B product datasheet: `https://datasheets.raspberrypi.com/rpi4/raspberry-pi-4-datasheet.pdf`
- Mailbox property interface: `https://github.com/raspberrypi/firmware/wiki/Mailbox-property-interface`
- The debug UART is an ARM PrimeCell **PL011** (32-deep FIFO variant) — TRM **DDI 0183**.
- ARM specs: GIC-400 TRM (**DDI 0471**) + GICv2 architecture (**IHI 0048B**); PSCI
  (**DEN 0022**); Cortex-A72 TRM (100095); ARMv8-A ARM (**DDI 0487**).
- SD Host Controller Standard Spec (SD Association) for EMMC2; IEEE 802.3 clauses 22/28/40
  for the GENET MDIO + BCM54213PE PHY.

---

## Board quick-facts (orient every investigation)

- **Addressing model.** Default is **low-peripheral mode**: main peripherals (legacy bus
  `0x7C00_0000–0x7FFF_FFFF`) appear to the ARM at `0xFC00_0000–0xFF7F_FFFF`; ARM-local
  peripherals + GIC at `0xFF80_0000–0xFFFF_FFFF`. Rule: datasheet legacy `0x7Enn_nnnn` →
  ARM `0xFEnn_nnnn` (and `0x4_7Enn_nnnn` in the full 35-bit map). The `scb` bus (GENET,
  PCIe RC) maps `0x7D5n_nnnn → 0xFD5n_nnnn`. DMA traps: legacy masters reach RAM only
  through a 1 GiB window at bus `0xC000_0000` (→ ZONE_DMA = 1 GiB); the `scb` masters
  (GENET) see RAM 1:1 with no limit; PCIe inbound is capped at **3 GiB**; `emmc2bus`
  dma-ranges are **patched by firmware per SoC stepping**. RAM starts at phys 0; the VPU's
  `gpu_mem` share is carved from the top of the first 1 GiB. `arm_peri_high=1` switches to
  high-peripheral mode (needs matching DT + armstub). Worked example: PL011 UART0 = legacy
  `0x7E20_1000` → ARM **`0xFE20_1000`** (matches the official
  `earlycon=pl011,mmio32,0xfe201000`).
- **Boot chain & entry state.** BootROM → **SPI-EEPROM bootloader** (no bootcode.bin on
  Pi 4) → start4.elf (VPU) loads DTB + armstub (at phys 0) + kernel, patches the DTB,
  releases the ARM cores into the stub at **EL3**. Stock stub: sets CNTFRQ_EL0 = 54 MHz,
  SCR_EL3 = {NS=1, RW=1, HCE=1, **SMD=1 — SMC disabled, no EL3 runtime**}, then ERETs to
  the kernel at **EL2, AArch64, MMU off, caches off, DAIF masked, x0 = DTB physical
  address**, x1–x3 = 0 (the arm64 booting.rst contract). 64-bit kernel (`kernel8.img`,
  `arm_64bit=1` default) loads at `0x20_0000` on current firmware (older: `0x8_0000`;
  firmware honors the Image header text_offset — don't hard-code). Firmware patches the
  stub's DTB-pointer word at stub offset `0xF8` and entry word at `0xFC` (stub magic
  `0x5AFE570B` at `0xF0`). **Secondary cores: spin-table** — cores 1–3 WFE-poll 64-bit
  release words at phys **`0xD8`/`0xE0`/`0xE8`/`0xF0`** (= DT `cpu-release-addr`); write the
  entry address, barrier, SEV; secondary enters at EL2, MMU/caches off, x0 = 0. **PSCI only
  with TF-A** (`PLAT=rpi4`, `armstub=bl31.bin`): BL31 resides at `0x1000–0x8_0000` (keep the
  low 512 KiB clear), adds the PSCI + reserved-memory nodes to the live DTB.
- **SMP topology.** 4×Cortex-A72, one cluster; cpu DT `reg` = 0–3 = **MPIDR Aff0** (Aff1 =
  Aff2 = 0 — unlike Pi 5 where the core index is in Aff1). Boot core 0. L1D 32 KiB, L1I
  48 KiB, shared L2 1 MiB.
- **Interrupts.** **GIC-400 (GICv2)**, 192 SPIs: GICD **`0xFF84_1000`**, GICC
  **`0xFF84_2000`** (GICC_DIR at +0x1000), GICH `0xFF84_4000`, GICV `0xFF84_6000`.
  DT `#interrupt-cells = 3` ⟨type, n, flags⟩: SPI INTID = n + 32, PPI INTID = n + 16.
  Allocation: VideoCore IRQ *v* → DT SPI **64 + v** (e.g. VC 57 = all-PL011s → SPI 121;
  VC 62 = both SDHCIs → SPI 126); ETH_PCIe block L2 IRQ *i* → DT SPI **128 + i** (GENET =
  157/158); ARMC IRQs at SPI 32–47 (VPU mailbox = 33). Legacy ARMC controller still exists
  at `0xFE00_B000` and takes over when `enable_gic=0` (Pi 4 default is 1).
- **Debug UART / console.** PL011 **UART0 at `0xFE20_1000`**, DT GIC_SPI **121**
  (level-high, shared OR of all five PL011s at `0x7E201000/400/600/800/a00`), 32-deep
  FIFOs (AMBA periphid `0x00341011`), **UARTCLK = 48 MHz** (firmware `init_uart_clock`),
  default 115200. `earlycon=pl011,mmio32,0xfe201000`. Pinmux: GPIO 14/15 **ALT0** =
  TXD0/RXD0. **Trap:** on a stock Pi 4B the header/primary UART is the **mini UART**
  (`0xFE21_5040`, AUX block, baud = VPU core clock / (8×(reg+1)) — unstable unless
  `enable_uart=1` pins the core clock); UART0 is muxed to GPIO 32/33 for Bluetooth. Use
  `dtoverlay=disable-bt` to put UART0 on the header. (CM4 differs: UART0 is primary.)
- **Timers.** ARM generic timer at **54 MHz** (stub-programmed; read `CNTFRQ_EL0`, don't
  hard-code). Timer PPIs ⟨GIC_PPI n → INTID⟩: secure-phys 13→29, nonsec-phys 14→30,
  virt 11→27, hyp 10→26, all level-low. BCM **system timer** at `0xFE00_3000`: 64-bit
  1 MHz free-running counter, four compare channels → DT SPI 64–67; channels 0/2
  conventionally VPU-owned, use 1/3 — TODO (verify on hardware).
- **Clocks / power.** Split ownership. **VPU firmware mailbox** (property channel 8,
  registers at **`0xFE00_B880`**, IRQ DT SPI 33) owns clock rates, voltages, power
  domains, and the **firmware GPIO expander** (SD_PWR_ON, VDD_SD_IO_SEL for the 1.8 V SD
  switch, BT_ON/WL_ON, power LED). **CPRMAN** at **`0xFE10_1000`** (`brcm,bcm2711-cprman`)
  is OS-programmed for peripheral clocks (EMMC2, PWM, GP clocks; one shared PL011 clock).
  Bring-up costs: UART0 — none (48 MHz already running); EMMC2 — CPRMAN EMMC2 clock +
  firmware-expander voltage switching; GENET — **nothing** (no clock handle; always on).
- **GPIO / pinmux.** Single block at **`0xFE20_0000`**, **58 GPIOs**. GPFSEL0–5 at
  `0x00–0x14`, 3 bits/pin (000 in, 001 out, 100/101/110/111 = ALT0–3, 011 = ALT4,
  010 = ALT5). GPSET/GPCLR/GPLEV pairs at `0x1C/0x28/0x34`; event/edge registers
  `0x40–0x8C`. **Pulls are BCM2711-specific:** GPIO_PUP_PDN_CNTRL_REG0–3 at
  **`0xE4/0xE8/0xEC/0xF0`**, 2 bits/GPIO (00 none, **01 up, 10 down**), 16 GPIOs/reg —
  the BCM2835 GPPUD/GPPUDCLK dance does nothing on 2711. Map ≥ `0xF4` (classic DT size
  `0xB4` misses the pull registers). Bank IRQs DT SPI 113–116.
- **DTB runtime patching.** start4.elf fills `/memory@0` (placeholder in the source DT),
  assembles `/chosen/bootargs`, patches **`emmc2bus` dma-ranges per SoC stepping**, writes
  the GENET MAC address (via the `ethernet0` alias), places `blconfig`/`blpubkey`
  reserved-memory, and merges `dtoverlay=` overlays; TF-A adds the PSCI node. **Parse the
  live DTB passed in x0** — the static `.dts` is a template, not the contract.
- **Key peripheral identities.** UART0: `arm,pl011` @ `0xFE20_1000`, SPI 121. GPIO:
  `brcm,bcm2711-gpio` @ `0xFE20_0000`, SPI 113–116. Ethernet: GENET v5,
  `brcm,bcm2711-genet-v5` @ **`0xFD58_0000`** (64 KiB, `scb` bus), SPI **157/158**,
  internal MDIO at **+0xE14** (`brcm,genet-mdio-v5`), BCM54213PE PHY at MDIO addr 1
  (id `0x600d84a2`), `rgmii-rxid`, no PHY IRQ. SD: **EMMC2** `brcm,bcm2711-emmc2`
  (SDHCI-class) @ **`0xFE34_0000`**, SPI **126** — owns the microSD slot; the Arasan
  SDHCI (`0xFE30_0000`, also SPI 126) serves SDIO WiFi; sdhost (`0xFE20_2000`, SPI 120)
  is disabled on Pi 4B. PCIe RC: `brcm,bcm2711-pcie` @ `0xFD50_0000`, outbound CPU
  `0x6_0000_0000` (64 MiB), inbound capped 3 GiB — hosts only the VL805 xHCI.

---

## Common gotchas (Pi 4-specific)

- **The header console is the mini UART, not the PL011.** GPIO 14/15 default to UART1
  (mini UART), whose baud tracks the VPU core clock (`enable_uart=1` pins it); UART0 goes
  to Bluetooth on GPIO 32/33. `dtoverlay=disable-bt` frees UART0 for the header.
- **BCM2711 changed pull-resistor programming silicon-wide.** Use GPIO_PUP_PDN_CNTRL_REG0–3
  (`0xE4–0xF0`, 01=up, 10=down); BCM2835-style GPPUD/GPPUDCLK code silently no-ops, and an
  `0xB4`-sized MMIO mapping doesn't even cover the new registers.
- **Ethernet is on-SoC GENET — not Pi 5's RP1.** Don't port Pi 5 (`0x1F_...`/RP1)
  assumptions; Pi 4 peripherals live at `0xFE.../0xFD...`. Only the VL805 USB3 xHCI is
  behind PCIe.
- **PCIe inbound DMA caps at 3 GiB** (wrapper bug) — USB DMA buffers must sit below 3 GiB
  on 4/8 GiB boards. Legacy-master DMA caps at 1 GiB (bus `0xC000_0000` window); EMMC2's
  reach is whatever the **firmware-patched** live `emmc2bus` dma-ranges say.
- **Stock armstub = spin-table and no EL3 runtime: SMC is disabled** (SCR_EL3.SMD) and
  faults as undefined. PSCI requires shipping TF-A BL31 as `armstub=` (it then owns
  `0x1000–0x8_0000`).
- **Interrupt lines are shared pervasively:** one SPI for all five PL011s (121), one for
  both SDHCI controllers (126), one for SPI3–6 (118), one for I2C3–6 (117) — demux via
  per-block status registers.
- **Low- vs high-peripheral mode must be consistent** across firmware, DT, and armstub;
  everything stock assumes low (`0xFE...`). `arm_peri_high=1` without a matching DT+stub
  does not boot.

---

## Report

Produce the report in the format defined by `os-investigator`, ending with the clean-room
attestation. This skill's job is to make sure the addresses, sources, and quirks above are
reflected accurately — and that no BCM2711 driver source ends up in the output.
