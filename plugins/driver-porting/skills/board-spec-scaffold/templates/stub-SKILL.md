---
name: <board>-expert
description: >-
  Board expert for the <Board display name> (<SoC part number>; family: <the sibling models the
  board facts cover, e.g. "Pixel 10 Pro and Pro XL">): memory map and MMIO
  addresses, device tree, boot chain and exception-level hand-off, interrupts, timers,
  clocks/power, debug UART, GPIO/pinmux, plus sources and datasheets for bring-up. Use for any
  "<keyword1>", "<keyword2>", or "<keyword3>" hardware or low-level question, even if Linux isn't
  mentioned. A stub over the <id> board spec: board-expert does the work, os-investigator supplies
  the method and the clean-room no-source-code rule.
---

<!--
SPDX-FileCopyrightText: <year> contributors
SPDX-License-Identifier: Apache-2.0
-->
<!-- In this repository the header is exactly the two lines above with the year; another repo
     carries whatever its neighbors do. Keep the description's "Board expert for" prefix and its
     "A stub over the <id> board spec" sentence: consumers match the first, the checker finds
     stubs by the second. For a device family, list in the description the sibling models whose
     board facts this spec covers (the `variants:` rows); a model whose facts differ has its own
     `variant_of` spec and, if wanted, its own stub. -->

# <Board display name> Expert (stub)

This skill is a pointer. The <board> facts live in the **`<id>` board spec**<, composed from the
`<soc-id>` SoC spec and the `<chip-id>` chip spec>, and **`board-expert`** is the skill that reads
specs.

**<board>-expert is a subagent role.** If you are the main/orchestrating agent, do not run this
inline: spawn a subagent, have it load `board-expert` and `os-investigator`, and give it
`spec: <id>` along with the question. The subagent clones and reads reference source in its own
cache; you receive clean-room facts back, never source. The reasons are in `board-expert` under "How
to run this skill".

Keep this file a pointer. Facts go in the spec; procedure goes in `board-expert`.
