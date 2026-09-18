---
kind: soc
id: badsoc
name: Bad SoC
triggers: [badsoc]
instances:
  - name: uart0
    ip: nosuchip
    reg: "0xfe201000"
    irq: "GIC_SPI 121"
  - name: uart1
    ip: badboard
    irq: {kind: GIC, number: x}
---

# Bad SoC

## Quick-facts

- Flat. `[DT]`
