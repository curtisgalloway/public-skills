---
name: rpi-expert
description: >-
  Board expert for the Raspberry Pi 5 / Compute Module 5 (BCM2712 SoC + RP1 southbridge): memory
  map and MMIO addresses, device tree, boot chain and exception-level hand-off, PSCI/SMP,
  interrupts, timers, clocks/power, UART/GPIO, PCIe and the RP1, plus sources and datasheets for
  bring-up. Use for any Pi 5, CM5, BCM2712, or RP1 hardware or low-level question. A stub over the
  rpi5 board spec: board-expert does the work, os-investigator supplies the method and the
  clean-room no-source-code rule.
---

<!--
SPDX-FileCopyrightText: 2026 Curtis Galloway
SPDX-License-Identifier: Apache-2.0
-->

# Raspberry Pi 5 Expert (stub)

This skill is a pointer. The Pi 5 facts live in the **`rpi5` board spec**, composed from the
`bcm2712` SoC spec and the `rp1` chip spec, and **`board-expert`** is the skill that reads specs.

**rpi-expert is a subagent role.** If you are the main/orchestrating agent, do not run this inline:
spawn a subagent, have it load `board-expert` and `os-investigator`, and give it `spec: rpi5` along
with the question. The subagent clones and reads reference source in its own cache; you receive
clean-room facts back, never source. The reasons are in `board-expert` under "How to run this skill".

Keep this file a pointer. Facts go in the spec; procedure goes in `board-expert`.
