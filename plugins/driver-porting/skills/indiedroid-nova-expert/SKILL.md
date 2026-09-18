---
name: indiedroid-nova-expert
description: >-
  Board expert for the Indiedroid Nova (ameriDroid; same hardware as the 9Tripod Pico PC V2.0) and
  for Rockchip RK3588S/RK3588 bring-up generally (Radxa ROCK 5, Orange Pi 5, …): memory map and
  MMIO addresses, device tree, boot chain and exception-level hand-off, PSCI/SMP, GIC-600, timers,
  clocks/power (CRU, SCMI, RK806), debug UART, GPIO/pinmux via the GRF, plus sources and datasheets
  for bring-up. Use for any Indiedroid Nova or RK3588(S) hardware, low-level software, or bring-up
  question. A stub over the indiedroid-nova board spec (and the rk3588s SoC spec it composes):
  board-expert does the work, os-investigator supplies the method and the clean-room
  no-source-code rule.
---

<!--
SPDX-FileCopyrightText: 2026 Curtis Galloway
SPDX-License-Identifier: Apache-2.0
-->

# Indiedroid Nova / Rockchip RK3588S Expert (stub)

This skill is a pointer. The Nova facts live in the **`indiedroid-nova` board spec**, composed from
the `rk3588s` SoC spec (which places the `dw-apb-uart` IP spec), and **`board-expert`** is the skill
that reads specs.

**indiedroid-nova-expert is a subagent role.** If you are the main/orchestrating agent, do not run
this inline: spawn a subagent, have it load `board-expert` and `os-investigator`, and give it
`spec: indiedroid-nova` along with the question. A question about another RK3588(S) board (ROCK 5,
Orange Pi 5, …) resolves the `rk3588s` SoC spec on its own, with the board-level facts reported as
missing. The subagent clones and reads reference source in its own cache; you receive clean-room
facts back, never source. The reasons are in `board-expert` under "How to run this skill".

Keep this file a pointer. Facts go in the spec; procedure goes in `board-expert`.
