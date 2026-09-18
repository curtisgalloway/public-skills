---
kind: board
id: <id>
name: <Board display name>
triggers: [<keyword1>, <keyword2>, <keyword3>]
aliases: []
parts: [<soc-id>, <chip-id>]
cache: <short>-resources
variants: []                  # optional: sibling models sharing these facts; see SPEC-FORMAT § Variants
# variant_of: <base-id>       # instead of variants, when THIS spec is a variant with differing facts
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

<Every bullet ends with its tag clause: tags, each with a parenthetical citation where one exists,
then at most one `TODO (verify on hardware)` sentence. `[doc]` always names its page. Drop bullets
that do not apply; use the set that fits the device.>

<Single-board computers and dev boards:>

- **Boot media and chain.** <What runs the first-stage bootloader, where the next stages and the OS
  image are loaded from, which configuration file selects them. Entry state is an SoC fact: point at
  the SoC spec.> `[doc]` (<page>)
- **Debug console.** <Connector, which UART instance, its address, the earlycon string.> `[DT]`
  (<node>), `[doc]` (<page>)
- **Headers and board-level GPIO.** <Which chip owns the header pins; point at that spec.> `[DT]` (<node>)
- **Power.** <PMIC part; rails the OS may need to touch.> `[databook]` (<datasheet>)
- **<Board-specific link or reset state at hand-off.>** `[doc]` (<page>)

<Handsets and other closed devices:>

- **Partitions and boot images.** <Boot-image format and version, which image carries the DTB,
  which carries the overlays, how the bootloader selects them.> `[doc]` (<page>)
- **Unlock and boot policy.** <Whether the bootloader can be unlocked, what it enforces, what a
  custom kernel must satisfy to boot.> `[doc]` (<page>)
- **Physical console access.** <How to reach a serial console at all: debug cable, test points,
  a bootloader command that enables the UART; baud.> `[doc]` (<page>), `[DT]` (<chosen node>)
- **Per-revision device trees.** <Board id / revision ids and the overlay each selects.> `[DT]` (<node>)
- **Kernel family and branch.** <Which public kernel tree and branch carry this device, and which
  device-tree files.> `[DT]` (<files>)

## Gotchas

<Two to seven bullets: the board-level deviations that bite during bring-up (console confusion,
mandatory firmware options, links reset before hand-off). Each ends with a tag.>
