---
kind: soc
id: badirq
name: Bad IRQ shapes
triggers: [badirq]
instances:
  - name: uart2
    ip: nosuchip
    irq: {kind: extended, number: 3}
  - name: uart3
    ip: nosuchip
    irq: {kind: SPI, number: 3, parent: gia}
  - name: uart4
    ip: nosuchip
    irq: {kind: extended, number: 3, parent: gia, intid: 40}
resources:
  repos:
    - name: linux
      url: https://example.com/linux
      ref: main
      files:
        - a/b.c
        - {path: c/d.dtsi, status: bogus}
        - {status: unmerged}
---

# Bad IRQ shapes

## Quick-facts

- Flat. `[DT]` (`badirq.dtsi`)
