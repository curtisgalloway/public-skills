---
kind: ip
id: dw-apb-uart
name: Synopsys DesignWare DW_apb_uart (16550-compatible)
triggers: [dw-apb-uart, dw_apb_uart, snps dw-apb-uart, designware uart, 8250_dw]
cache: dw-apb-uart-resources
resources:
  repos:
    - name: linux-mainline
      url: https://github.com/torvalds/linux
      ref: master
      license: GPL-2.0-only
      files:
        - drivers/tty/serial/8250/8250_dw.c
        - drivers/tty/serial/8250/8250_port.c
        - Documentation/devicetree/bindings/serial/snps-dw-apb-uart.yaml
      note: >-
        Generic-mode map. 8250_dw.c is the DesignWare-specific layer over the generic 8250 port
        code; read both for behavior only. Record the commit actually read. An anchored resolution
        uses the board's tree instead and reads this for provenance.
  docs:
    - title: Synopsys DesignWare DW_apb_uart product page
      url: https://www.synopsys.com/dw/ipdir.php?c=DW_apb_uart
      access: public
      cite: true
      note: >-
        The DW_apb_uart databook itself is under NDA; this product page is the public pointer. An
        ip-vendor overlay may add the databook.
    - title: Synopsys DesignWare ABP UART devicetree binding (snps-dw-apb-uart)
      url: https://www.kernel.org/doc/Documentation/devicetree/bindings/serial/snps-dw-apb-uart.yaml
      access: public
      cite: true
      note: the compatible string and the reg-shift / reg-io-width properties an instance provides
  tools: []
---

<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Synopsys DesignWare DW_apb_uart

## Orientation

The DW_apb_uart is Synopsys's licensable UART, a 16550-compatible block found as the debug and
peripheral UART on Rockchip SoCs (RK3588 among them) and across many other ARM SoCs. Its register
model is the industry-standard 16550 one, so any 16550/8250 register reference describes it; the
Synopsys databook is the IP source and is under NDA, with the public product page as the pointer. An
SoC places one or more instances at addresses of its choosing, with a register stride and access
width of its choosing; those placements, their interrupts, clocks, `reg-shift`, and `reg-io-width` are
instance facts and live in the SoC's `instances:` table, not here.

## Standards and databook

- The register model is the 16550 UART's: the same register indices, the same line-status bits, and
  the same FIFO control. `[standard]` (16550 UART register model)
- The devicetree binding fixes the `snps,dw-apb-uart` compatible string and the `reg-shift` and
  `reg-io-width` properties that describe how an instance is wired. `[standard]`
  (`snps-dw-apb-uart.yaml` binding)
- DesignWare-specific behavior beyond the 16550 model (the busy detection, the soft reset, the `USR`
  register) is documented in the DW_apb_uart databook. `[databook]` (DW_apb_uart databook, NDA)

## Programming model

- **Register organization.** 16550 register *indices*: THR (transmit holding, write) / RBR (receive
  buffer, read) at index 0, IER at index 1, FCR (write) at index 2, LCR at index 3, LSR at index 5.
  The byte offset of an index is `index << reg-shift`, and each register is accessed at
  `reg-io-width` bytes; both are instance facts (an RK3588 instance uses `reg-shift = 2`,
  `reg-io-width = 4`, so LSR sits at byte offset `0x14`). `[standard]` (16550 register model;
  `snps-dw-apb-uart.yaml`)
- **Transmit readiness.** Poll LSR: **THRE (bit 5)** set means the transmit holding register is
  empty and a byte may be written to THR. `[standard]` (16550 register model)
- **Line configuration.** Word length, stop bits, parity, and the divisor-latch access bit are in
  LCR, as on any 16550. `[standard]` (16550 register model)
- **Interrupts and FIFOs.** Per-source enables in IER and FIFO enable / trigger levels in FCR, as on
  any 16550. FIFO depth is a configuration option of the IP: `TODO (verify on hardware)` per
  instance. `[standard]` (16550 register model)
- **Reconfiguration while busy.** The DesignWare block ignores a write to `LCR` while a transfer is
  in progress. Reconfigure only when idle, or after the DW soft reset / a read of the `USR` (UART
  status) register. `[databook]` (DW_apb_uart databook)

## Known variants and quirks

- **Stride and width vary by integration.** The same block appears with a byte stride and 8-bit
  accesses on one SoC and a 32-bit stride with mmio32 accesses on another; never hard-code offsets
  without the instance's `reg-shift` and `reg-io-width`. `[standard]` (`snps-dw-apb-uart.yaml`)
- **The busy quirk is DesignWare-specific.** A driver written for a plain 16550 that writes `LCR`
  during traffic will have the write silently dropped on this block. `[databook]` (DW_apb_uart
  databook)
- **Baud clock is an instance fact.** The reference clock and therefore the divisor for a given baud
  come from the SoC's clock tree: `TODO (verify on hardware)` per instance.

## Gotchas

- PL011 offsets (FR, DR, …) do not apply; this is a 16550. Use THR/RBR/LSR/LCR/IER/FCR at
  `index << reg-shift`. `[standard]`
- A silent line with a correct base address is usually pinmux, not the UART: the block does nothing
  until the SoC's IOMUX routes it to pins. `[standard]` (`snps-dw-apb-uart.yaml` describes the
  block, not the pins)
- An `LCR` write that seems to have no effect was dropped by busy detection; wait for idle or use the
  soft reset / `USR` path before retrying. `[databook]` (DW_apb_uart databook)
