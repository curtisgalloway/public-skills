---
name: indiedroid-nova-expert
description: >-
  Board expert for the Indiedroid Nova (ameriDroid / Ameridroid; same hardware as the 9Tripod Pico PC
  V2.0), built on the Rockchip RK3588S SoC — and more generally a reference for RK3588S / RK3588
  bring-up that applies to most Rockchip RK3588(S) boards (Radxa ROCK 5, Orange Pi 5, etc.). Use this
  skill for ANY question about Indiedroid Nova / Nova / RK3588S / RK3588 / Rockchip RK3588 hardware,
  low-level software, or bring-up: physical/MMIO addresses, the memory map, the device tree, the boot
  chain and exception-level hand-off (BootROM → SPL/DDR → TF-A/BL31 → U-Boot → kernel), PSCI/SMP and
  the A76/A55 topology, the GIC-600 (GICv3) interrupt controller, timers, clocks/power (CRU, SCMI,
  RK806 PMIC), the DesignWare-8250 debug UART/console, GPIO/pinmux via the GRF, PCIe/USB/eMMC, where
  to find the source, and which datasheets/TRM to cite. Trigger whenever "Indiedroid", "Nova",
  "RK3588S", "RK3588", or "Rockchip RK3588" appears in a hardware/software question, even if Linux
  isn't mentioned. This skill provides the board-specific MAP; for the investigation method and the
  clean-room no-source-code rule, also load and follow the `os-investigator` skill.
---

<!--
SPDX-FileCopyrightText: 2026 Curtis Galloway
SPDX-License-Identifier: Apache-2.0
-->

# Indiedroid Nova / Rockchip RK3588S Expert

The Indiedroid Nova (distributed by ameriDroid; identical hardware to the 9Tripod Pico PC V2.0) is a
Raspberry-Pi-4-form-factor SBC built on the **Rockchip RK3588S** SoC: an octa-core DynamIQ design with
4× Cortex-A76 (big) + 4× Cortex-A55 (little), a Mali-G610 GPU, an 8K VPU, and a ~6-TOPS NPU. The
quick-facts below are generic to RK3588S/RK3588 and apply to most RK3588(S) boards; board-specific
items (console baud, PMIC, storage) are called out as such.

## How to run this skill (delegate; don't inline)

**indiedroid-nova-expert is a *subagent* role.** Everything below — cloning the RK3588(S) sources,
reading the device trees and driver code, citing the TRM — is written for the agent that *is* the
expert. If you are the main/orchestrating agent, do **not** execute this skill body inline: **spawn a
subagent, have it load this skill, and pass it the question.** Only that subagent clones/reads/manages
the RK3588(S) source clones. The main agent never reads the GPL source itself and never micromanages
the clone/fetch steps in the subagent's prompt (no paths, no `git`/`curl`/`ls` steps — the expert
handles its own resources). The main agent's entire job is: ask the question → receive clean-room
facts back.

This split is the whole point. Letting the main agent (which writes the differently-licensed target-OS
code) run the skill body inline would pull GPL source into its context and destroy the clean-room
boundary. When in doubt, delegate.

## Method and constraints live in `os-investigator`

Load and follow the `os-investigator` skill for the investigation method, the report format, and the
clean-room discipline: return hardware facts and mechanism descriptions in your own words, never source
code, even if asked to paste it. If that skill isn't loaded, still obey the one rule that matters most:
no source code in the output — describe behavior, give addresses/sequences, link the human to the
upstream file instead.

---

## Sources to clone and keep locally

**Linux — mainline (the Indiedroid Nova is fully mainlined; cleanest provenance):**
- Repo: `https://github.com/torvalds/linux` (use `master`, or a stable branch like `linux-6.12.y`).
  `git clone --depth 1 https://github.com/torvalds/linux.git`
- Highest-value files (raw, under `arch/arm64/boot/dts/rockchip/`):
  - `https://raw.githubusercontent.com/torvalds/linux/master/arch/arm64/boot/dts/rockchip/rk3588s-indiedroid-nova.dts`
  - `.../rk3588s.dtsi` (RK3588S wrapper), `.../rk3588-base.dtsi` (most peripherals), `.../rk3588.dtsi`
    (full RK3588 extras), `.../rk3588-pinctrl.dtsi`
  - Drivers, read for *behavior* only: DesignWare 8250 UART `.../drivers/tty/serial/8250/8250_dw.c`
    (+ `8250_port.c`); GICv3 `.../drivers/irqchip/irq-gic-v3.c`; CRU clocks
    `.../drivers/clk/rockchip/clk-rk3588.c`; pinctrl `.../drivers/pinctrl/pinctrl-rockchip.c`
  - arm64 entry-state contract: `.../Documentation/arch/arm64/booting.rst`
- Rockchip vendor BSP kernel (more drivers, downstream/messier): `https://github.com/rockchip-linux/kernel`
  (branches `develop-6.1`, `develop-5.10`).

**Boot / firmware:**
- Trusted Firmware-A (BL31 = EL3 runtime; provides PSCI **and** the SCMI-over-SMC server):
  `https://github.com/ARM-software/arm-trusted-firmware` → `plat/rockchip/rk3588`
- U-Boot (BL33; mainline has RK3588 + a Nova board file `rk3588s-indiedroid-nova-u-boot.dtsi`):
  `https://github.com/u-boot/u-boot`
- **rkbin** — Rockchip's prebuilt **DDR-init and BL31 blobs**, required to assemble a bootable image:
  `https://github.com/rockchip-linux/rkbin`

**Datasheets & specs (cite these, not the kernel):**
- **Rockchip RK3588 TRM V1.0** (Part 1 + Part 2) — the authoritative register reference; Rockchip
  copyright, community-mirrored. GitHub: `https://github.com/FanX-Tek/rk3588-TRM-and-Datasheet`
  (also has the **RK3588 Datasheet V1.3** and the **RK806 PMIC** datasheet). Clean PDF mirror:
  `https://www.scs.stanford.edu/~zyedidia/docs/rockchip/rk3588_part1.pdf` and `.../rk3588_part2.pdf`.
- The debug UART is a standard **16550-compatible** DesignWare DW_apb_uart — any 16550/8250 register
  reference works; the Synopsys DW_apb_uart databook is the IP source.
- ARM specs: GICv3/4 architecture (ARM IHI 0069); PSCI (ARM DEN 0022); SCMI (ARM DEN 0056);
  ARMv8-A Architecture Reference Manual (exception levels, generic timer, MMU).

---

## Board quick-facts (orient every investigation)

- **Addressing is flat/direct — no high window, no southbridge.** Root is `#address-cells=2`/
  `#size-cells=2`, but peripheral `reg` entries are `<0x0 ADDR 0x0 SIZE>`, so the physical address is
  the literal value (e.g. UART2 = `0xFEB5_0000`). On-SoC peripherals sit in `0xFD00_0000–0xFEFF_FFFF`;
  DRAM starts at `0x0`. There is **no** `0x10_0000_0000`-style offset and **no** off-SoC I/O chip —
  all I/O (USB, GbE, PCIe, eMMC, GPIO) is on the SoC. (Still check any sub-bus that declares its own
  `ranges`, e.g. PCIe controllers and the GIC node.)
- **Boot chain ends in TF-A BL31; OS entered at EL2.** BootROM → DDR-init + TPL/SPL (Rockchip DDR blob
  from rkbin) → **TF-A BL31** (EL3; installs PSCI-over-SMC and an **SCMI-over-SMC** server) → U-Boot
  (BL33) → kernel, entered **AArch64, EL2, MMU off, D-cache off, DTB pointer in `x0`** (standard arm64
  boot protocol). Secondary cores start via **PSCI `CPU_ON`** (DT `method = "smc"`, all CPUs
  `enable-method = "psci"`); no spin-table.
- **SMP topology: 8 cores, big.LITTLE DynamIQ.** CPU0–3 = Cortex-**A55** (cluster0); CPU4–7 =
  Cortex-**A76** (clusters 1–2). DT cpu `reg` = `0x0,0x100,…,0x700` → MPIDR **Aff1 = 0..7, Aff0 = 0**
  (core N → `MPIDR = N<<8`); pass that as the PSCI target. The boot core is normally an A55 (CPU0).
- **Interrupts: GIC-600 = GICv3 (NOT GICv2).** GICD `0xFE60_0000` (0x10000); GICR redistributors
  `0xFE68_0000` (0x100000 = 8 × 0x20000); two ITS for MSI at `0xFE64_0000` and `0xFE66_0000`; MBI
  alias `0xFE61_0000` (`mbi-ranges <424 56>`). **DT `#interrupt-cells = 4`** (type, number, flags,
  PPI-partition/affinity). SPI n → INTID `32+n`; PPI n → INTID `16+n`. GICv3 means the CPU interface
  is via **system registers (`ICC_*_EL1`)**, each core must wake its **redistributor** (clear
  `GICR_WAKER.ProcessorSleep`, enable SGIs/PPIs in `GICR_ISENABLER0`), and SPIs use **affinity
  routing** — a larger, different init than a GICv2 MMIO CPU interface. Do not reuse a GICv2 driver.
- **Debug UART/console: DesignWare 8250 (NOT PL011).** `snps,dw-apb-uart`, **UART2 @ `0xFEB5_0000`**,
  IRQ SPI 333 (INTID 365). **`reg-shift = 2`, `reg-io-width = 4`** → 16550 register *indices* at a
  32-bit stride, accessed as mmio32 (so LSR, index 5, is at byte offset `0x14`; THR/RBR at `0x00`).
  Nova console default: **`serial2:1500000n8`** (1.5 Mbaud). earlycon: `earlycon=uart8250,mmio32,0xfeb50000`.
  Polled TX: wait for **LSR.THRE (bit 5)** clear-to-send, write **THR (index 0)**. **Pins need IOMUX**
  via the GRF/pinctrl — the **Nova board uses the `uart2m0_xfer` group** (it overrides the SoC base
  default of `uart2m1_xfer`), so mux the **m0** pins. U-Boot normally muxed them already, but a
  from-reset bare-metal path must set the GRF IOMUX or the line stays silent. Note the DesignWare
  "busy" quirk: writing `LCR` mid-transfer is ignored — reconfigure only when idle or after the DW
  soft-reset / `USR` read.
- **Timers: 24 MHz arch timer (NOT 54 MHz).** `arm,armv8-timer`, PPIs 13/14/11/10/12 =
  sec-phys / phys / virt / hyp-phys / hyp-virt. Frequency from the `xin24m` crystal →
  `CNTFRQ_EL0 = 24,000,000` (read it, don't hard-code). At EL2 use `CNTHP_*` (PPI 10 → INTID 26).
  On-SoC Rockchip timers also exist (`timer@feae0000`); the architected timer is preferred.
- **Clocks/power are OS-managed (unlike the Pi's firmware-owned clocks).** The on-SoC **CRU** (clock +
  reset unit) `clock-controller@fd7c0000` (`rockchip,rk3588-cru`) programs most peripheral clocks and
  resets directly — bringing a peripheral up usually means **ungating its CRU clock and deasserting its
  CRU reset** first. **CPU/GPU/NPU DVFS** clocks and a few resets go through **SCMI over SMC**
  (`arm,scmi-smc`, `arm,smc-id = 0x82000010`, shared memory ≈ `0x10F000`; clock protocol `0x14`, reset
  `0x16`), served by BL31. Board **voltage rails** come from an external **RK806-class PMIC** (the Nova
  uses `rk8602`/`rk8603` regulators) over I²C/SPI.
- **GPIO/pinmux via the GRF.** Five banks: `gpio0@fd8a0000`, `gpio1@fec20000`, `gpio2@fec30000`,
  `gpio3@fec40000`, `gpio4@fec50000` (32 pins each). IOMUX/drive/pull are set through the **GRF**
  syscons (`sys_grf@fd58c000`, PMU GRFs `@fd58a000`, plus per-PHY/VO GRFs) and `rockchip,rk3588-pinctrl`.
- **DTB runtime patching.** U-Boot fills `/memory` with the real DRAM size and may set `/chosen`
  bootargs / fix up MACs. Parse the live DTB for memory extents rather than trusting static values.

---

## Common gotchas (RK3588S-specific)

- **GICv3, not GICv2** — system-register CPU interface, per-core redistributor wake, affinity routing,
  and DT IRQ cells = 4. A GICv2 (GICC MMIO) driver will not work.
- **Console is a DW 8250, not a PL011** — 16550-style registers, `reg-shift=2`, mmio32, 1.5 Mbaud
  default. PL011 offsets (FR/DR/etc.) do not apply; use THR/RBR/LSR/LCR/IER/FCR at index×4.
- **Program the CRU yourself.** Peripherals often need their CRU gate ungated and CRU reset deasserted
  before they respond; this is not done by a GPU firmware as on the Pi.
- **SCMI-over-SMC for CPU DVFS** is firmware-served (BL31) — don't expect to find a self-contained CPU
  PLL programming path in the OS for the big/little clocks; voltages are the PMIC's job.
- **UART2 IOMUX** must be set (GRF) if you start truly from reset; otherwise silence despite a correct
  base address. On the Nova the console is the **`uart2m0_xfer`** pin group (board override of the SoC
  base default `m1`) — confirm exact pins/registers in the TRM GRF chapter + the RK3588S pinctrl DT.
- **You need rkbin (DDR init + BL31) or a self-built TF-A** to produce a bootable image; the
  BootROM → SPL → BL31 → BL33 chain is mandatory and Rockchip-specific.
- **24 MHz arch timer** (read `CNTFRQ_EL0`), and you enter at **EL2** — use `*_EL2` registers and
  verify `CurrentEL`.

---

## Report

Produce the report in the format defined by `os-investigator`, ending with the clean-room attestation.
Keep the addresses/sources/quirks above accurate and keep RK3588(S) driver source out of the output.
