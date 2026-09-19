---
name: rpi4-expert
description: >-
  Board expert for the Raspberry Pi 4 Model B (Broadcom BCM2711; family includes Pi 400 and
  Compute Module 4/4S): physical/MMIO addresses and the low- vs high-peripheral memory map, the
  device tree, the boot chain and exception-level hand-off, PSCI/SMP, the GIC-400, timers,
  clocks/power, the PL011 debug UART and the mini-UART trap, GPIO/pinmux, GENET Ethernet,
  EMMC2/SDHCI, the VL805 USB on PCIe, plus sources and datasheets for bring-up. Trigger whenever
  "Raspberry Pi 4", "Pi 4", "Pi 4B", "BCM2711", "CM4", "Pi 400", or "GENET" appears in a hardware
  or low-level question, even if Linux isn't mentioned. A stub over the rpi4 board spec:
  board-expert does the work, os-investigator supplies the method and the clean-room
  no-source-code rule.
---

<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Raspberry Pi 4 Model B Expert (stub)

This skill is a pointer. The Pi 4 facts live in the **`rpi4` board spec**, composed from the
`bcm2711` SoC spec (which places the `pl011` IP spec as UART0), and **`board-expert`** is the skill
that reads specs.

**rpi4-expert is a subagent role.** If you are the main/orchestrating agent, do not run this inline:
spawn a subagent, have it load `board-expert` and `os-investigator`, and give it `spec: rpi4` along
with the question. The subagent clones and reads reference source in its own cache; you receive
clean-room facts back, never source. The reasons are in `board-expert` under "How to run this skill".

Keep this file a pointer. Facts go in the spec; procedure goes in `board-expert`.
