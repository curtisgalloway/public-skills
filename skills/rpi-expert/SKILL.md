---
name: rpi5-expert
description: >-
  Board expert for the Raspberry Pi 5 / Compute Module 5 (Broadcom BCM2712 SoC + RP1 southbridge):
  the board-specific map of MMIO addresses, the memory map, the device tree, the boot chain and
  exception-level hand-off, PSCI/SMP, interrupts, timers, clocks/power, UART/GPIO, PCIe and the RP1
  chip, source repos, and datasheets for bring-up work. Trigger whenever "Raspberry Pi 5", "Pi 5",
  "BCM2712", "RP1", or "CM5" appears in a hardware or low-level software question, even if Linux
  isn't mentioned. Pairs with `os-investigator`, which supplies the investigation method and the
  clean-room no-source-code rule.
---

<!--
SPDX-FileCopyrightText: 2026 Curtis Galloway
SPDX-License-Identifier: Apache-2.0
-->

# Raspberry Pi 5 Expert (BCM2712 + RP1)

You hold the board-specific knowledge for the Raspberry Pi 5 / Compute Module 5: the BCM2712 SoC and
the RP1 I/O southbridge. You answer bring-up and low-level questions by pointing at the right sources
and orienting the investigation with the facts below.

## How to run this skill (delegate; don't inline)

**rpi-expert is a *subagent* role.** Everything below — cloning sources, reading the cache, walking
driver code — is written for the agent that *is* the expert. If you are the main/orchestrating agent,
do **not** execute this skill body inline: **spawn a subagent, have it load this skill, and pass it
the question.** Only that subagent clones/reads/manages `~/src/rpi5-resources`. The main agent never
touches the cache, never reads GPL source, and never micromanages the cache in the subagent's prompt
(no paths, no `git`/`curl`/`ls` steps — the expert handles its own resources). The main agent's entire
job is: ask the question → receive clean-room facts back.

This split is the whole point. Letting the main agent (which writes the differently-licensed target-OS
code) run the skill body inline would pull GPL source into its context and destroy the clean-room
boundary. When in doubt, delegate.

## Method and constraints live in `os-investigator`

**Load and follow the `os-investigator` skill** for the investigation method, the report format, and —
non-negotiably — the **clean-room discipline: return hardware facts and mechanism descriptions in your
own words, never source code**, even if asked to paste it. This board skill supplies the *where* and
*what* (sources, addresses, quirks); `os-investigator` supplies the *how*. If for any reason that
skill isn't loaded, still apply the one rule that matters most: **no source code in the output** —
describe behavior, give addresses/sequences, and link the human to the upstream file instead.

---

## Local resource cache: `~/src/rpi5-resources`

Clone and cache all Pi 5 reference material (Linux tree, TF-A, datasheets, fetched
source files) under **`~/src/rpi5-resources/`**. Reuse what's already there before
re-cloning or re-fetching.

**This cache is for the rpi-expert agent ONLY.** The main agent must not read files
in `~/src/rpi5-resources` directly — it asks rpi-expert, which returns clean-room
facts (no source code). Keeping the cache behind this skill is what preserves the
clean-room boundary.

## Sources to clone and keep locally (into `~/src/rpi5-resources`)

**Linux — Raspberry Pi downstream (the real Pi 5 device trees + drivers):**
- Repo: `https://github.com/raspberrypi/linux`
- Current Pi 5 branch is `rpi-6.12.y`. Shallow clone:
  `git clone --depth 1 --branch rpi-6.12.y https://github.com/raspberrypi/linux.git ~/src/rpi5-resources/linux`
- Highest-value files (raw, on `rpi-6.12.y`):
  - `https://raw.githubusercontent.com/raspberrypi/linux/rpi-6.12.y/arch/arm64/boot/dts/broadcom/bcm2712.dtsi`
  - `.../broadcom/bcm2712-ds.dtsi`, `.../broadcom/bcm2712-rpi-5-b.dts`, `.../broadcom/rp1.dtsi` (same dir)
  - PL011 UART driver (read for *behavior* only): `.../drivers/tty/serial/amba-pl011.c`
  - DT address-translation reference (how `of_translate_address` walks `ranges`): `.../drivers/of/address.c`
  - arm64 entry-state contract: `.../Documentation/arch/arm64/booting.rst`
- Mainline Linux also carries BCM2712 (`https://github.com/torvalds/linux`,
  `arch/arm64/boot/dts/broadcom/bcm2712*`) — use it when you want cleaner upstream provenance.

**Trusted Firmware-A (BL31 / PSCI / the EL2 hand-off):**
- Upstream: `https://github.com/ARM-software/arm-trusted-firmware` → platform under `plat/rpi/rpi5/`
  (`git clone https://github.com/ARM-software/arm-trusted-firmware.git`)
- RPi5 platform docs: `https://trustedfirmware-a.readthedocs.io/en/latest/plat/rpi5.html`
- Raspberry Pi's shipped armstub fork: `https://github.com/raspberrypi/arm-trusted-firmware`

**Firmware blobs + boot configuration:**
- Precompiled boot firmware / overlays: `https://github.com/raspberrypi/firmware`
- `config.txt` options (e.g. `pciex4_reset=0` to leave the RP1 PCIe link configured for bare-metal):
  `https://www.raspberrypi.com/documentation/computers/config_txt.html`

**Datasheets & specs (clean-room authority — cite these, not the kernel):**
- RP1 peripherals (authoritative for all RP1 I/O; see §2.3.1 "PCIe and 40-bit to peripheral address
  mapping"): `https://datasheets.raspberrypi.com/rp1/rp1-peripherals.pdf`
- **There is no public BCM2712 peripherals datasheet** — the commonly-cited
  `datasheets.raspberrypi.com/bcm2712/bcm2712-peripherals.pdf` is a dead link (confirmed by RPi staff).
  For on-SoC BCM2712 blocks the **device tree is the primary public address map**; for register-level
  detail of shared IP (PL011, system timer, mailbox, SDHCI) use the **BCM2711** datasheet:
  `https://datasheets.raspberrypi.com/bcm2711/bcm2711-peripherals.pdf`
- ARM PL011 UART TRM (ARM DDI 0183); GIC-400 / GICv2 spec (ARM IHI 0048); PSCI spec (ARM DEN 0022);
  ARMv8-A Architecture Reference Manual (exception levels, generic timer, MMU).

---

## Board quick-facts (orient every investigation with these)

- **Peripherals sit very high in the physical map.** The on-SoC peripheral window is exposed to the
  ARM cores at base `0x10_0000_0000`; legacy `0x7x_xxxxxx` numbers are *offsets*, so
  `physical = 0x10_0000_0000 + offset`. The debug UART (PL011 `uart10`) is at `0x10_7D00_1000`
  (verify against `earlycon=pl011,0x107d001000,115200n8`). All address math must be ≥40-bit-clean.
- **`soc` `ranges` cell trap.** Root node is `#address-cells=2`/`#size-cells=2`; the `soc` node is
  `1`/`1`. A `ranges` tuple is [child:1 cell][parent:2 cells][size:1 cell]. Mis-counting cells (e.g.
  assuming the child inherits the root's 2 cells) silently yields a wrong/identity translation — a
  classic bring-up bug. Do the arithmetic explicitly.
- **Most I/O is on RP1, across PCIe.** USB, Gigabit Ethernet, 40-pin-header GPIO, most UART/I²C/SPI,
  header SD — all on the RP1 chip behind the internal x4 PCIe (`pcie2`). RP1's internal
  `0xc0_4000_0000` space maps through the PCIe outbound window to CPU physical **`0x1F_0000_0000`**
  (peripheral block `0x4000_0000–0x4040_0000`; not all registers are accessible). Nothing on RP1 is
  reachable until PCIe is up — early bring-up uses on-SoC blocks only (debug UART, GIC, timer).
- **Boot chain ends in TF-A BL31; hand-off at NS-EL2.** VPU boot ROM → bootloader in SPI EEPROM →
  loads armstub (TF-A BL31), DTB, and OS image (BL33); BL31 (EL3) installs PSCI-over-SMC, patches the
  DTB (PSCI node + reserved-memory for itself), and ERETs to your image at **EL2, AArch64, MMU off,
  D-cache off, `HCR_EL2.VM=0` (no stage-2), DTB pointer in `x0`**. Low 512 KiB (`0x0–0x80000`) is
  resident TF-A — don't overwrite/map-cacheable. Secondary cores start via PSCI `CPU_ON` (no
  spin-table); CPU `reg` values `0x000/0x100/0x200/0x300` are MPIDR affinities (Aff1 = core).
- **Interrupts: standard GIC-400 (GICv2).** GICD `0x10_7FFF_9000`, GICC `0x10_7FFF_A000`. DT IRQ
  encoding `<type number flags>`: SPI → INTID `32+number`, PPI → INTID `16+number`.
- **Firmware owns clocks/power.** Most clocks/voltages/power-domains are managed by the VideoCore
  firmware via the mailbox property channel (`0x10_7C01_3880`); only a few fixed clocks are in DT
  (e.g. `clk_osc` 54 MHz, `clk_uart` 9.216 MHz). The architected-timer frequency is firmware-set —
  read `CNTFRQ_EL0` (54 MHz today) rather than hard-coding.
- **The DTB is patched at runtime.** `/memory` (real RAM size), `/chosen` (`bootargs`, `stdout-path`),
  `aliases` (`serial0` → debug UART), the PSCI node, and `reserved-memory` are injected/filled by
  firmware/BL31. Parse the live DTB; don't trust the static `.dts` for these.

---

## Common gotchas (Pi 5-specific)

- Don't look for peripherals at `0xFExxxxxx` — that's Pi 4 (BCM2711). Everything moved high.
- The 40-pin-header "console" UART is RP1's `uart0` (behind PCIe). Early console = the dedicated 3-pin
  debug connector = on-SoC PL011 `uart10` at `0x10_7D00_1000`, which firmware leaves enabled.
- No spin-table for SMP — PSCI only. Older Pi bring-up guides that poke per-core release addresses do
  not apply.
- You run at EL2, not EL1: use `*_EL2` system registers (`VBAR_EL2`, `CNTHP_*`, `SCTLR_EL2`, `TCR_EL2`,
  `MAIR_EL2`); verify `CurrentEL` rather than assuming.
- After BL31 hand-off the MMU is off and there's no stage-2, so accesses are flat physical — if two
  code paths disagree about whether an address works, suspect different computed addresses, not a
  translation regime.
- By default the x4 PCIe link to RP1 is reset before the kernel launches; set `pciex4_reset=0` to have
  firmware leave the RC + RP1 BARs configured for bare-metal use.

---

## Report

Produce the report in the format defined by `os-investigator`, ending with the clean-room attestation.
This skill's job is to make sure the addresses, sources, and quirks above are reflected accurately —
and that no BCM2712/RP1 driver source ends up in the output.
