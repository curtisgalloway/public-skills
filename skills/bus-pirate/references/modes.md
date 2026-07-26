<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Bus Pirate modes reference

Companion to `SKILL.md`. Everything here is Bus Pirate 5/6 firmware. Enter a
mode with `m <name>`; `help mode` lists the current mode's extra commands, and
`<command> -h` prints the authoritative, firmware-current flags.

Reminder on the shared syntax: `[` `{` START/alt-START, `]` `}` STOP/alt-STOP,
`>` run bus commands with no START, `r`/`r:N` read, `0x`/`0b`/decimal/`"str"`
write, `:N` repeat, `.N` bit count, `d`/`D` delay. What `[`, `{`, `]`, `}` and
`r` *do* is mode-specific — that is what the tables below pin down.

---

## HiZ

Bus: high impedance. Connections: none. Outputs: not allowed. Pull-ups: not
allowed. Max 5 V.

The boot state and the safe state. All hardware disabled so nothing on a
connected board can be driven out of spec. Two things only happen here: the
self-test (`~`), and general-purpose logic-analyzer capture where every pin is
an input.

---

## 1WIRE

Bus: 1-Wire. Pins: **OWD (IO0)** + GND. Open-drain. **Pull-ups always required
(2 k–10 k).** Max 5 V.

| Syntax | Effect |
|---|---|
| `[` or `{` | 1-Wire reset; reports device presence |
| `r`, `r:N` | read byte(s) |
| `0x`/`0b`/dec | write byte, partial bytes allowed (`0b1001`) |

1-Wire devices never drive high — without pull-ups (`P`) there is no logic 1 at
all, and nothing will ever respond.

Mode commands:

- `scan` — 1-Wire ROM search; prints every device's 8-byte ROM ID and decodes
  known family codes (`28 …` → DS18B20).
- `ds18b20` — read temperature directly.
- `eeprom` — read/write/erase/verify/test/dump GX/DS243x 1-Wire EEPROMs
  (same verb+flag grammar as the I2C `eeprom` command below).

```
1WIRE> P
1WIRE> scan
1WIRE> [0xcc 0x44]          # SKIP ROM, convert T
1WIRE> [0xcc 0xbe r:9]      # SKIP ROM, read scratchpad
```

---

## UART

Bus: asynchronous serial (also MIDI at 31250 8N1, which needs an opto-isolated
adapter). Pins: **TX (IO4) → target RX**, **RX (IO5) ← target TX**, GND.
Push-pull 1.65–5 V. Max 5 V.

**Not RS-232.** A PC serial port swings ±13 V and will destroy the Bus Pirate
without an RS-232 level adapter.

Config prompts on `m uart`: baud (default 115200), data bits 5–8 (8), parity
none/even/odd (none), stop bits 1/2 (1), flow control none/RTS-CTS (none),
signal inversion normal/inverted (normal). It prints the achieved baud.

| Syntax | Effect |
|---|---|
| `[` | open UART; use `r` to poll for bytes |
| `{` | open UART and print data as it arrives asynchronously |
| `]` or `}` | close UART |
| `r`, `r:N` | read a byte if one is waiting, else fail |

Mode commands:

- `bridge [-t] [-s]` — transparent USB↔UART bridge; **exit by pressing the
  physical button**. `-t` keeps the toolbar, `-s` suppresses local echo.
- `gps` — decode NMEA sentences.
- `glitch [-c]` — UART glitch-injection framework. Times are in units of 10 ns
  (a setting of 3 = 30 ns). Exit with the button.

---

## HDUART

Bus: half-duplex UART — RX and TX share one wire. Pins: **RXTX (IO0)**,
**RST (IO2)**, GND. Open-drain, **pull-ups always required (2 k–10 k)**. Max 5 V.

This is the mode for phone SIM cards and bank IC cards. Config prompts: baud,
data bits, parity, stop bits (no flow control or inversion).

| Syntax | Effect |
|---|---|
| `[` | open UART, print data as it arrives |
| `]` | close UART |
| `{` | RST pin (IO2) **high** |
| `}` | RST pin (IO2) **low** |
| `r`, `r:N` | read a byte if waiting, else fail |

`bridge` works here too and is the documented way to drive SIM cards with
external tooling such as pySim.

---

## I2C

Bus: I2C. Pins: **SDA (IO0)**, **SCL (IO1)**, GND. Open-drain, **pull-ups always
required (2 k–10 k)**. 1.2–5 V. Typical speeds 100 kHz / 400 kHz / 1 MHz.

Config prompts on `m i2c`: speed 1–1000 kHz (default 400 kHz), clock stretching
off/on (off).

| Syntax | Effect |
|---|---|
| `[` or `{` | (repeated) START |
| `]` or `}` | STOP |
| `r`, `r:N` | read byte and send ACK |
| `0x`/`0b`/dec | write byte and check for ACK |

**Addresses are 8-bit here.** 7-bit `0x50` is `0xA0` to write, `0xA1` to read.

```
I2C> [0xa0 0x00 [0xa1 r]
I2C START
TX: 0xA0 ACK 0x00 ACK
I2C REPEATED START
TX: 0xA1 ACK
RX: 0x48 NACK
I2C STOP
```

Mode commands:

- `scan [-v]` — brute-force address scan; `-v` guesses part numbers. For write
  addresses it sends START/addr/ACK?/STOP; for read addresses it also reads one
  byte and NACKs it, specifically so the chip does not miss the STOP and produce
  ghost addresses.
- `sniff [-q] [-r] [-7]` — passive I2C sniffer up to 500 kHz (based on
  jjsch-dev/pico_i2c_sniffer). `-q` hides ACKs, `-r` raw output with no
  `[`/`]`/`R`/`W` decoration, `-7` prints 7-bit addresses.
- `i2c dump|read -a <7-bit addr> -w <1..4> -r <start reg> [-b <bytes>] [-f file] [-q] [-c]`
  — the generic "write register pointer, then stream reads" pattern that most
  I2C devices implement. `-w` is the register-address width in bytes: small
  parts (≤256 B) usually 1, EEPROMs and sensors usually 2.
- `eeprom dump|read|write|verify|erase|test|list -d <device> [-f file] [-a addr] [-s start] [-b bytes] [-v] [-q] [-c]`
  — 24x-series EEPROMs. There is **no safe autodetect**, you must pass `-d`
  (`eeprom list` shows supported parts). Default address 0x50.
- `ddr5` / `ddr4` — probe, dump, read, write, verify, lock/unlock blocks, and
  CRC check/patch SPD data on RAM modules.
- `usbpd` — USB Power Delivery via an AP33772S sink adapter: list profiles,
  request fixed or programmable profiles, reset.
- Sensor one-liners: `tcs3472` (colour), `sht4x`, `sht3x`, `si7021`
  (temp/humidity), `ms5611` (temp/pressure), `tsl2561` (lux).

---

## SPI

Bus: SPI. Pins: **MOSI (IO5)**, **MISO (IO6)**, **CLK (IO4)**, **CS (IO7)**,
GND. Push-pull 1.65–5 V. Max 5 V. No pull-ups needed.

Config prompts on `m spi`: speed 1–62500 kHz (default 100 kHz), data bits 4–8
(8), clock polarity idle LOW/HIGH (low), clock phase leading/trailing edge
(leading), chip select active HIGH/LOW (active low). It prints the achieved speed.

| Syntax | Effect |
|---|---|
| `[` | CS active |
| `{` | CS active **and** show the byte read back while writing (full-duplex view) |
| `]` or `}` | CS inactive |
| `r`, `r:N` | read by clocking out a dummy `0xFF` |

```
SPI> [0x9f r:3]
CS Enabled
TX: 0x9F
RX: 0xEF 0x40 0x14
CS Disabled
```

Mode commands:

- `flash probe|dump|read|write|verify|erase|test [-f file] [-e] [-v] [-s start] [-b bytes] [-q] [-c] [-o]`
  — NOR flash via a universal SFDP-driven driver, falling back to a built-in
  chip database. `probe` tries RESID (0xAB), REMSID (0x90), and RDID (0x9F),
  then parses SFDP. `-e` erases before write, `-v` verifies, `-o` reads with a
  plain 0x03 command and no chip detection.
- `eeprom …` — same verb/flag grammar as I2C, for 25x/93x/95x SPI EEPROMs, plus
  `eeprom protect` style operations for the BP1/BP0/WPEN block-protection bits.

Need per-bit control of clock and data? Use **3WIRE** (or **2WIRE**) instead.

---

## 2WIRE

Bus: generic 8-bit clock+bidirectional-data bus that is *I2C-shaped but not I2C*
(no ACK/NACK bit). Pins: **SDA (IO0)**, **SCL (IO1)**, **RST (IO2)**, GND.
Open-drain, **pull-ups always required**. Max 5 V. Config: speed 1–1000 kHz
(default 400 kHz).

Used for SLE4442 smart cards, half-duplex SPI-ish parts, and anything that
almost-but-not-quite speaks I2C.

| Syntax | Effect |
|---|---|
| `[` | I2C-style START |
| `]` | I2C-style STOP |
| `{` | RST pin high |
| `}` | RST pin low |
| `r`, `r:N` | read byte(s) |
| `^` | one clock tick (low→high→low) |
| `/` `\` | clock pin high / low |
| `-` `_` | data pin high / low |
| `.` | read the data pin |

Mode commands:

- `sniff` — sniffs 8-bit I2C-like protocols with no ACK/NAK, up to 500 kHz.
- `sle4442` — ATR, dump card memory, unlock with a PSC, write data, change the
  passcode, and inspect/modify protection memory.

---

## 3WIRE

Bus: SPI-like with explicit clock/data control. Pins: **MOSI**, **MISO**,
**CLK**, **CS**, GND. Push-pull 1.65–5 V. Config: speed 1–3900 kHz (default
100 kHz), chip select active HIGH/LOW (active low).

Same table as SPI for `[` `{` `]` `}` `r`, plus the bitwise set: `^` tick,
`/` `\` clock high/low, `-` `_` MOSI high/low, `.` read MISO.

---

## DIO

Bus: none — plain digital IO. All eight pins free. Tristate push-pull /
high-impedance, 1.65–5 V.

| Line | Effect |
|---|---|
| `>0x00` | drive every free pin low |
| `>0xff` | drive every free pin high |
| `>0b10101010` | pattern across the pins |
| `>r` | read all pins as one byte |
| `>@.0` | return pin 0 to input (bus-syntax form) |
| `@ 0` | return pin 0 to input (terminal-command form) |

Pins currently used by a frequency generator or counter are left alone. This is
the mode to use for `G`/`F` experiments and for the SUMP capture-during-use demo.

---

## LED

Three submodes, chosen at `m led`:

1. **WS2812/SK6812/NeoPixel** — one wire. Pins: **SDO (IO0)**, GND.
   `[` or `{` = reset (data low > 280 µs); `]`/`}` unused. Write GRB bytes.
2. **APA102/SK9822** — clock + data. Pins: **SDO (IO0)**, **SCL (IO1)**, GND.
   `[` or `{` = start frame (`0x00000000`); `]` or `}` = end frame (`0xffffffff`).
3. **Onboard LEDs** — the 18 SK6812s on the board itself; no wiring, good for
   smoke-testing syntax or the scope tutorial.

Serial LEDs draw up to 60 mA each at full brightness and the PSU is rated
300 mA — power a strip externally.

---

## INFRARED

Three protocol submodes at `m infrared`: **RAW (aIR format)**, **NEC**, **RC5**.
Also prompts for TX modulation 20–60 kHz (default 38 kHz) and which RX sensor to
listen on (38 kHz barrier / 36–40 kHz demodulator / 56 kHz demodulator).
Compatible with the IR Toy v3 plank.

| Pin | Signal |
|---|---|
| IO1 | LERN — 20–60 kHz IR learner receiver |
| IO3 | BARR — 38 kHz IR barrier receiver |
| IO4 | IRTX — IR transmitter LED |
| IO5 | 38K — 36–40 kHz demodulator |
| IO7 | 56K — 56 kHz demodulator |

Mode commands: `tvbgone` (TV-B-Gone power-off sweep), `irtx` (transmit aIR),
`irrx` (receive/record/retransmit aIR), `test` (exercise the IR Toy plank).
For host-side capture and analysis there is an `aIR`/AnalysIR binmode.

---

## JTAG

Bus: JTAG. Connections vary. Push-pull 1.65–5 V.

**This is not a JTAG engine** — it cannot yet drive scan chains. What it hosts
is **blueTag**, an open-source JTAG/SWD pin finder:

```
JTAG> bluetag jtag -c 8
[ Pinout ] TDI=IO0 TDO=IO3 TCK=IO4 TMS=IO2 TRST=N/A
[ Device 0 ] 0x59602093 (mfg: 'Xilinx', part: 0x9602, ver: 0x5)

JTAG> bluetag swd -c 8
[ Pinout ] SWDIO=IO5 SWCLK=IO6
[ Device 0 ] 0x0BC12477 (mfg: 'ARM Ltd', part: 0xbc12, ver: 0x0)
```

`bluetag [jtag|swd] [-c <channels>] [-v] [-d]` — `-c` is how many IO pins to
search, starting at IO0; `-d` disables pin pulsing, which sometimes finds
stubborn ports.

Procedure: connect IO0 upward to the suspected debug pads, avoid ground pours
and supply pins, tie grounds together, power the target, and **match the IO
voltage** — either set it with `W` or feed the target's supply into VOUT/VREF
and skip `W`. Bonus trick from the docs: wire IO0–IO2 to the Bus Pirate's own
underside SWD header and run `bluetag swd -c 3` to see it find itself.
