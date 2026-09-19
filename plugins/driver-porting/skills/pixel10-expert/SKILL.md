---
name: pixel10-expert
description: >-
  Board expert for the Google Pixel 10 (Google Tensor G5 SoC, codename laguna / lga; board codename
  frankel; family: Pixel 10 Pro and Pixel 10 Pro XL, which share the SoC and console, and the Pixel
  10 Pro Fold as far as public facts reach): memory map and MMIO addresses, device tree, the closed
  Android boot chain and boot-image layout, exception-level hand-off, PSCI/SMP across
  Cortex-X4/A725/A520, the GICv3, timers, clocks/power, the DesignWare debug UART, GPIO/pinmux,
  plus the public sources for bring-up. Use for any "pixel 10", "tensor g5", "laguna", "lga", or
  "frankel" hardware or low-level question, even if Linux isn't mentioned; not for the Pixel 10a,
  which is a different SoC. A stub over the pixel10 board spec (and the tensor-g5 SoC spec it
  composes): board-expert does the work, os-investigator supplies the method and the clean-room
  no-source-code rule.
---

<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Google Pixel 10 Expert (stub)

This skill is a pointer. The Pixel 10 facts live in the **`pixel10` board spec**, composed from the
`tensor-g5` SoC spec (which places the `dw-apb-uart` IP spec), and **`board-expert`** is the skill
that reads specs.

**pixel10-expert is a subagent role.** If you are the main/orchestrating agent, do not run this
inline: spawn a subagent, have it load `board-expert` and `os-investigator`, and give it
`spec: pixel10` along with the question. A question about the Pixel 10 Pro or Pro XL resolves the
same spec through its `variants:` rows; a question about the Pixel 10a does not resolve here at all
(different SoC). The subagent clones and reads reference source in its own cache; you receive
clean-room facts back, never source. The reasons are in `board-expert` under "How to run this
skill".

Keep this file a pointer. Facts go in the spec; procedure goes in `board-expert`.
