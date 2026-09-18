---
kind: ip
id: <ip-id>
name: <IP vendor and block name>
triggers: [<block name>, <driver name>]
cache: <ip-id>-resources
resources:
  repos:
    - name: linux-mainline
      url: https://github.com/torvalds/linux
      ref: master
      license: GPL-2.0-only
      files:
        - <driver path, read for behavior only>
        - <devicetree binding path>
      note: generic-mode map; record the commit actually read
  docs:
    - title: <IP databook or public proxy documenting the identical block>
      url: <URL>
      access: public
      cite: true
      note: <NDA status; if the databook is NDA, name the public proxy here and leave the databook to an ip-vendor overlay>
    - title: <public standard the block implements, e.g. xHCI, USB 3.2, IEEE 802.3>
      url: <URL>
      access: public
      cite: true
  tools: []
---

<!--
SPDX-FileCopyrightText: <year> contributors
SPDX-License-Identifier: Apache-2.0
-->

# <IP display name>

## Orientation

<One paragraph: what the block is, who makes it, which SoCs commonly carry it, whether it has a
public databook or only a proxy, and which public standards it implements. No instance facts.>

## Standards and databook

<Which standard governs which part of the block (the host-controller interface, the bus protocol,
the PHY interface), and which databook or proxy documents the registers. Each bullet ends with a tag.>

- <Standard or databook and what it covers.> `[standard]` / `[databook]`

## Programming model

<Register-map organization, the init / reset / teardown sequences at the databook's level of
detail, the DMA and interrupt model. Each bullet ends with a tag. Orderings taken only from a driver
are `[source-observed]` and say "order not known to be required".>

- **Register organization.** <...> `[databook]`
- **Init sequence.** <...> `[databook]`
- **Interrupts.** <...> `[databook]`
- **DMA.** <...> `[databook]`

## Known variants and quirks

<IP versions, configuration options an SoC may set (FIFO depth, port count, PHY type), public
errata. Each bullet ends with a tag; per-SoC values are `TODO (verify on hardware)`.>

## Gotchas

<Two to seven bullets. Each ends with a tag.>
