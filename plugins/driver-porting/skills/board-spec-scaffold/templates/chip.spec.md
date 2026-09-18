---
kind: chip
id: <chip-id>
name: <Chip vendor and part name>
triggers: [<part name>]
cache: <short>-resources
resources:
  repos:
    - name: <repo short name>
      url: <repo URL>
      ref: <branch or tag>
      license: <SPDX identifier>
      files:
        - <the chip's device-tree fragment>
      note: <what this repo is for>
  docs:
    - title: <chip datasheet>
      url: <URL>
      access: public
      cite: true
      note: <which section covers the host-visible address mapping>
  tools: []
---

<!--
SPDX-FileCopyrightText: <year> contributors
SPDX-License-Identifier: Apache-2.0
-->

# <Chip display name>

## Orientation

<One paragraph: what the chip is, which bus connects it to the SoC, what it carries, whether it has a
public datasheet.>

## Quick-facts

<Every bullet ends with a provenance tag; mark anything unverified `TODO (verify on hardware)`.>

- **How it is reached.** <Bus or link; what must be up before any register is reachable.> `[databook]`, `[DT]`
- **Address window.** <The chip's internal space, how it maps into CPU physical, which parts are
  host-accessible.> `[databook]`, `[DT]`
- **What it carries.** <Blocks; where their offsets are documented.> `[databook]`
- **State at hand-off.** <Whether firmware leaves the link configured; point at the board spec for the
  option that controls it.> `[doc]`

## Gotchas

<Two to seven bullets. Each ends with a tag.>
