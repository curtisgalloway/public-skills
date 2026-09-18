---
kind: board
id: <id>
name: <Board display name>
triggers: [<keyword1>, <keyword2>, <keyword3>]
aliases: []
parts: [<soc-id>, <chip-id>]
cache: <short>-resources
resources:
  repos:
    - name: <repo short name>
      url: <repo URL>
      ref: <branch or tag>
      license: <SPDX identifier>
      files:
        - <path to the board .dts>
      note: <what this repo is for; read for behavior, cite the datasheet>
  docs:
    - title: <board documentation, schematic, or boot-configuration reference>
      url: <URL>
      access: public
      cite: true
  tools: []
---

<!--
SPDX-FileCopyrightText: <year> contributors
SPDX-License-Identifier: Apache-2.0
-->

# <Board display name>

## Orientation

<One paragraph: which SoC and companion parts, what is wired where, what an early bring-up can reach
without the companion parts, which connector is the debug console.>

## Quick-facts

<Every bullet ends with a provenance tag; mark anything unverified `TODO (verify on hardware)`.>

- **Boot media and chain.** <What runs the first-stage bootloader, where the next stages and the OS
  image are loaded from, which configuration file selects them. Entry state is an SoC fact: point at
  the SoC spec.> `[doc]`
- **Debug console.** <Connector, which UART instance, its address, the earlycon string.> `[DT]`, `[doc]`
- **Headers and board-level GPIO.** <Which chip owns the header pins; point at that spec.> `[DT]`
- **Power.** <PMIC part; rails the OS may need to touch.> `[databook]`
- **<Board-specific link or reset state at hand-off.>** `[doc]`

## Gotchas

<Two to seven bullets: the board-level deviations that bite during bring-up (console confusion,
mandatory firmware options, links reset before hand-off). Each ends with a tag.>
