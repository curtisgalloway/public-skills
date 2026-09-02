---
name: bus-pirate
description: >-
  Drive a Bus Pirate 5/5XL/6 (buspirate) from its terminal or a host script: transaction syntax,
  mode selection, IO pinout, programmable power supply and pull-ups, per-pin voltage measurement,
  logic analyzer, and the BPIO2 binary scripting port. Use when probing, sniffing, scanning, or
  bit-banging an I2C, SPI, UART, 1-Wire, 2-wire, 3-wire, or JTAG/SWD bus, dumping an EEPROM or
  flash chip, or figuring out which of the two serial ports is which. Covers Bus Pirate 5 and
  later only — classic v3.x is entirely different firmware.
---

<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Bus Pirate

The Bus Pirate is a USB-attached serial-protocol multi-tool: you type a short
bracket expression at its terminal and it drives I2C/SPI/UART/1-Wire/etc. on
eight buffered IO pins, with a programmable power supply, switchable pull-ups,
per-pin voltage measurement, and a logic analyzer built in. It is the fastest
way to answer "is this chip alive and what does it say" without writing firmware.

This skill covers **Bus Pirate 5, 5XL, and 6** (the RP2040/RP2350 generation).
Detail lives in two companion files, read them when the task needs them:

- `references/modes.md` — every bus mode: pins, config prompts, what `[` `{` `]`
  `}` `r` mean *in that mode*, and the mode-specific commands (`scan`, `sniff`,
  `eeprom`, `flash`, `ddr5`, `sle4442`, `bluetag`, `bridge`, `glitch`, …).
- `references/automation.md` — driving it from a host script: the BPIO2 binary
  port, on-device `script`/`macro` files, binmodes for PulseView/flashrom/
  AVRDUDE, and how to cope with the interactive ANSI terminal from pyserial.

## Identify the hardware first

| | Bus Pirate 5 | Bus Pirate 5XL | Bus Pirate 6 | Bus Pirate v3.x (classic) |
|---|---|---|---|---|
| MCU | RP2040, 125 MHz | RP2350A | RP2350B, 133/150 MHz | PIC24FJ64 + FT232R |
| RAM | 264 KB | 520 KB | 512 KB | tiny |
| Follow-along logic analyzer | No | No | **Yes** | No |
| USB | native CDC, 2 ports + mass storage | same | same | FTDI, **one** port |
| Firmware file | `bus_pirate5_rev10.uf2` | (discontinued) | `bus_pirate6_rev2.uf2` | `.hex` via PIC bootloader |
| Status | volume production, primary dev platform | **discontinued** (RP2350 E9 errata; owners swapped to 6) | limited/"luxury" production | legacy, different codebase |

- 5 vs 6 is a small difference: same firmware features today; 6 has more RAM/PIO
  and the extra pins needed for the follow-along logic analyzer (a second buffer
  that watches the *bus* rather than what the MCU drives).
- **v3.x is not this tool.** It runs unrelated firmware with a different command
  set and the old BBIO1 binary protocol, and it appears as an FTDI serial port
  (`/dev/ttyUSB*` on Linux, `/dev/cu.usbserial-*` on macOS) — a single port, not
  two. If the device you found is one FTDI port, stop and treat it as v3;
  nothing on docs.buspirate.com applies verbatim.
- Confirm with `i` at the prompt: it prints e.g. `Bus Pirate 5 REV10`, the
  firmware build date, the MCU, the serial number, the available modes, and the
  active binmode.

## Quick start: plugged in to a first measurement

```
# 1. find the two CDC ports (macOS)
ls /dev/cu.usbmodem*
# 2. attach to the LOWER-numbered one (the terminal)
screen /dev/cu.usbmodem1234567890121        # or: tio /dev/ttyACM0   (Linux)
```

Then in the terminal:

```
                      <enter>      # wake it; answer the VT100 prompt (y, or n for dumb terminals)
HiZ> i                             # who am I, what firmware, which modes
HiZ> m i2c                         # pick a mode by NAME (menu numbers move between builds)
I2C> W 3.3 100                     # PSU on: 3.3 V, 100 mA fuse  (lowercase w = off)
I2C> P                             # pull-ups on (10 k to VOUT/VREF) — mandatory for I2C
I2C> v                             # voltage report: VOUT + all 8 IO pins
I2C> scan                          # who is on the bus
I2C> [0xa0 0x00 [0xa1 r:8]         # write addr+reg, repeated start, read 8 bytes
I2C> w                             # power down when done
```

`v` is the one-shot answer to "what voltage is on that pin"; `V` repeats it
continuously until a key is pressed. `v.<pin>` does it *inside* a transaction.

## Connecting

Plugging in a Bus Pirate 5/6 presents **three** USB devices, no drivers needed:

| USB function | What it is |
|---|---|
| CDC serial #0 | the **user terminal** (the VT100 command line) |
| CDC serial #1 | the **binary/scripting port** (BPIO2, SUMP, FALA, legacy binmodes) |
| Mass storage | the onboard NAND as a FAT16 disk (config, scripts, dumps) |

Serial settings do not matter — it is USB CDC, the baud rate is ignored.
115200 8N1 is the customary thing to type when a program demands a value.

**Which port is which:**

- **macOS** — `ls /dev/cu.usbmodem*` shows two (plus matching `tty.*`). The name
  ends in the USB interface number: the **lower** suffix (e.g. `…121`) is the
  terminal, the **higher** (`…123`) is the binary port. Prefer `cu.*` over
  `tty.*` (`cu` allows multiple openers, `tty` is exclusive).
- **Linux** — two `/dev/ttyACM*` nodes. `/dev/serial/by-id/` disambiguates
  stably; the lower interface number is the terminal. (`by-id` naming is not in
  the official docs — verify by pressing enter and looking for a prompt.)
- **Windows** — two COM ports; the lower number is *usually* the terminal, but
  the docs explicitly warn Windows is inconsistent. Try both.
- Universal test: open a port and press enter. The terminal answers with a
  prompt (`HiZ>`); the binary port stays silent.

Terminal emulators the docs bless: Tera Term (Windows), `tio` (best on Linux —
defaults to 115200 8N1 and reconnects across replugs), `screen`, `minicom`,
`cu`. On macOS only iTerm2 + `cu` renders full colour; `screen`/Terminal come up
monochrome (switch to ANSI-256 under `c` → 2 if you want colour).

Exit incantations: `screen` → `ctrl-a k y` (or `ctrl-a ctrl-\`); `cu` → newline
then `~.`; `minicom` → `Esc q`; `tio` → `ctrl-t q`.

## The terminal

- **Prompt is the mode**: `HiZ>`, `I2C>`, `SPI>`, `LED-(WS2812)>`,
  `INFRARED-(RAW)>`. It always boots into **HiZ** — every output disabled, a
  deliberately safe state. Nothing happens on the wires until you `m` into a mode.
- **VT100 vs ASCII**: on reset it asks `VT100 compatible color mode? (Y/n)>`.
  Yes gives colour plus a live status bar (voltage/current/pin state) redrawn
  with ANSI escapes. Say **n** for dumb terminals and for scripted use — the
  status bar is exactly the "garbage characters" people report. Changeable later
  under `c`.
- **Line editing**: left/right cursor, up/down history, home/end, backspace/delete.
- **Up to 255 characters** per line; press enter to execute.
- **Chaining**: `;`, `&&`, `||` chain commands on one line
  (`a 0; a 1; a 2; a 3`).
- **Menus**: defaults appear in `( )` or marked `*` — bare enter accepts them,
  `x` + enter exits a menu without changes. Most settings persist to
  `bpconfig.bp` on the internal disk and are offered back as
  "Use previous settings?" next time.
- **Help is authoritative and newer than any doc**: `?` / `help` (all commands),
  `help mode` (current mode's commands), and `<command> -h` (per-command usage,
  e.g. `W -h`, `logic -h`, `scan -h`). When this skill and `-h` disagree, trust `-h`.

## Global commands

| Command | Does |
|---|---|
| `i` | version/hardware info; in a mode, also mode info, bit order, display format |
| `c` | config menu: language, ANSI colour, ANSI toolbar, LCD screensaver, LED effect/colour/brightness → saved to `bpconfig.bp` |
| `m` / `m <mode>` | mode menu / jump straight to a mode (`m i2c`, `m hiz`) |
| `l` / `L` | bit order MSB-first (default) / LSB-first |
| `o` | number display format: Auto (mirrors your input), HEX, DEC, BIN, ASCII |
| `d` | LCD display mode: Default (pin labels + voltages) or Scope |
| `~` | factory self-test — **HiZ only, disconnect everything first** |
| `reboot` | restart (you may need to reattach the terminal) |
| `$` | jump to the UF2 bootloader; prints the exact firmware filename you need |
| `cls` | clear/redraw + re-init the VT100 terminal (use after attaching late) |
| `ovrclk [-m MHz\|-k kHz] [-v mV]` | CPU overclock — disabled unless compiled in |
| `w` / `W [v] [mA] [-u pct]` | power supply off / on |
| `v` / `V` | voltage report once / continuously |
| `p` / `P` | pull-up resistors off / on |
| `g` / `G` | PWM frequency generator off / on |
| `f` / `F` | frequency + duty measurement once / continuously |
| `= <n>` | show `<n>` as HEX/DEC/BIN |
| `\| <n>` | reverse the bits of `<n>` |
| `a <pin>` / `A <pin>` / `@ <pin>` | drive pin low / high / make it an input and read it |
| `logic [start\|stop\|show\|hide\|nav] [-f Hz] [-o N]` | logic analyzer core + in-terminal graph |
| `jep106 <bank> <id>` | JEDEC JEP106 vendor lookup (flash/NAND manufacturer IDs) |
| `binmode` | pick what the *second* USB serial port speaks |
| `ls` `cd` `mkdir` `rm` `cat` `hex` `dump` `label` `format` `image` | onboard flash disk |
| `macro` `script` `button` `pause` | on-device scripting (see `references/automation.md`) |

## Bus transaction syntax

This is the heart of the tool. **A line is a bus transaction only if it starts
with `[`, `{`, or `>`.** Everything else is parsed as a terminal command — a
bare `r` is not a read, `>r` is.

| Token | Meaning |
|---|---|
| `[` | START (I2C start, 1-Wire reset, SPI CS active, …) — mode-specific |
| `{` | **alternate** START (e.g. SPI CS active *and* echo the byte read while writing) |
| `]` | STOP (I2C stop, SPI CS inactive, close UART, …) |
| `}` | alternate STOP |
| `>` | execute the rest of the line as bus commands with **no** START |
| `r` | read one byte |
| `r:N` | read N bytes (1–255) |
| `0b1001` | write binary; padding zeros optional (`0b1` == `0b00000001`) |
| `0x5a` / `0h5a` | write hex, case-insensitive; `0x5` == `0x05` |
| `0`–`255` | write decimal (anything with no `0x`/`0b`/`0h` prefix) |
| `"abc"` | write the ASCII bytes `0x61 0x62 0x63` |
| ` ` (space) | value delimiter — required between numbers, not between other tokens |
| `d` / `d:N` | delay 1 µs / N µs |
| `D` / `D:N` | delay 1 ms / N ms |
| `:N` | repeat the preceding token N times (`0x55:2`, `r:3`, `D:3`) |
| `.N` | operate on N bits instead of 8 (`0x5a.4` writes `0x0a`; `r.4`; `0x5432.12`); combines with repeat: `0x5a.4:2` |
| `v.<pin>` | measure and print the voltage on IO`<pin>` mid-transaction |
| `a.<pin>` / `A.<pin>` / `@.<pin>` | drive pin low / high / input+read, mid-transaction |
| `^` | one clock tick (2WIRE/3WIRE only) |
| `/` `\` | clock pin high / low (2WIRE/3WIRE only) |
| `-` `_` | data (MOSI) pin high / low (2WIRE/3WIRE only) |
| `.` | read the data (MISO) pin (2WIRE/3WIRE only) |

Note the two different `.` uses — as a *suffix* on a value it is a bit count; as
a *standalone token* in 2WIRE/3WIRE it reads the data pin. And note
`a.<pin>` (bus syntax, dot) vs `a <pin>` (terminal command, space).

Worked examples:

```
I2C>  [0xa0 0x00 [0xa1 r:8]     # write reg addr, repeated START, read 8 — addresses are 8-bit!
SPI>  [0x9f r:3]                # JEDEC ID: CS low, cmd 0x9F, read 3, CS high
SPI>  [ 0x55:2 D:3 r:3]         # write 0x55 twice, wait 3 ms, read 3
SPI>  >0x5a.4                   # write only 4 bits, no chip select change
1WIRE> [0xcc 0x44]              # reset, SKIP ROM, start DS18B20 conversion
UART> [ "AT\r" r:16 ]           # open, send, read up to 16 bytes, close
DIO>  >0b10101010               # drive all free pins in one write
DIO>  >r                        # read all pins as one byte
2WIRE> >^^^ / \ - _ .           # hand-clock a non-standard bus
```

**I2C addresses in Bus Pirate syntax are 8-bit** (`0xA0` write / `0xA1` read for
the 7-bit address `0x50`). `scan` prints both forms; datasheets usually print
the 7-bit one. Getting this wrong is the single most common I2C mistake.

## Modes

Select by name (`m i2c`); the numeric menu ordering has changed between firmware
builds, so `m 5` is not portable.

| Mode | Pins used | Notes |
|---|---|---|
| `HiZ` | none | boot state, everything disabled, only mode where `~` self-test runs |
| `1WIRE` | OWD (IO0) | open-drain, **pull-ups mandatory**; `scan` = ROM search |
| `UART` | TX (IO4), RX (IO5) | push-pull; `[`=open+`r` to read, `{`=open+async echo; `bridge`, `gps`, `glitch` |
| `HDUART` | RXTX (IO0), RST (IO2) | half-duplex on one wire, open-drain, **pull-ups mandatory**; SIM/bank cards |
| `I2C` | SDA (IO0), SCL (IO1) | open-drain, **pull-ups mandatory**; `scan`, `sniff`, `i2c dump`, `eeprom`, `ddr4/5`, sensors |
| `SPI` | MOSI(IO5)/MISO(IO6)/CLK(IO4)/CS(IO7) | push-pull, 1–62500 kHz; `flash`, `eeprom` |
| `2WIRE` | SDA (IO0), SCL (IO1), RST (IO2) | I2C-like but no ACK bit; bitwise `^ / \ - _ .`; `sniff`, `sle4442` |
| `3WIRE` | MOSI/MISO/CLK/CS | SPI with the same bitwise primitives, 1–3900 kHz |
| `DIO` | all 8 | no protocol; `>0xff` writes all pins, `>r` reads all pins |
| `LED` | SDO (IO0) [+ SCL (IO1)] | WS2812/SK6812/NeoPixel, APA102/SK9822, or the 18 onboard LEDs |
| `INFRARED` | LERN IO1, BARR IO3, IRTX IO4, 38K IO5, 56K IO7 | RAW (aIR) / NEC / RC5; `tvbgone`, `irtx`, `irrx` |
| `JTAG` | probe pins IO0…IO7 | **not a JTAG engine** — it hosts `bluetag`, a JTAG/SWD pin finder |

Pin assignments above are the BP5 defaults; the LCD and the `i` output print the
live labels for the current mode — trust those over this table if they disagree.
Full per-mode configuration prompts and command flags: `references/modes.md`.

## Pinout

Main connector, 10-pin 2.54 mm keyed (also fine with DuPont jumpers):

| Pin | Name | Description |
|---|---|---|
| 1 | VOUT/VREF | 1–5 V, 300 mA PSU output **or** an external reference voltage that powers the buffers and pull-ups |
| 2–9 | IO0–IO7 | buffered IO, 1.65–5 V, analog voltage measurement, optional 10 kΩ pull-up |
| 10 | GND | signal ground |

Auxiliary connector, 9-pin 1.0 mm: pins 1–8 = IO0–IO7, pin 9 = GND. It is a tap
point for an external logic analyzer, so you don't stack probes on the main header.

Per-pin capability (Bus Pirate 5 / RP2040):

| IO | GPIO | PWM slice | Measure V | Measure freq | Generate freq | UART | I2C | SPI | LED |
|---|---|---|---|---|---|---|---|---|---|
| IO0 | GPIO8 | 4A | yes | no | yes (tied to IO1) | | SDA | | SDO |
| IO1 | GPIO9 | 4B | yes | **yes** | yes (tied to IO0) | | SCL | | SCL |
| IO2 | GPIO10 | 5A | yes | no | yes (tied to IO3) | | | | |
| IO3 | GPIO11 | 5B | yes | **yes** | yes (tied to IO2) | | | | |
| IO4 | GPIO12 | 6A | yes | no | yes (tied to IO5) | TX | | SCLK | |
| IO5 | GPIO13 | 6B | yes | **yes** | yes (tied to IO4) | RX | | MOSI | |
| IO6 | GPIO14 | 7A | yes | no | yes (tied to IO7) | | | MISO | |
| IO7 | GPIO15 | 7B | yes | **yes** | yes (tied to IO6) | | | CS | |

Consequences: **frequency measurement only works on odd pins (1, 3, 5, 7)**, and
a PWM slice's two pins share one frequency (independent duty cycles). Using the
'B' pin of a slice for measurement blocks the 'A' pin as a generator.

A 3-pin SWD header (GND / SWDIO / SWCLK, GND furthest from the board edge) is
exposed on the underside for firmware development.

## Power supply and pull-ups

```
W                 # interactive: prompts for volts then current limit
W 3.3             # 3.3 V, default 300 mA fuse
W 5 50            # 5 V, 50 mA fuse
W 3.3 0           # 3.3 V, no current limit
W 3.3 100 -u 20   # …with a 20% undervoltage trip instead of the default 10%
w                 # off
```

- Programmable PSU: 0.8–5.0 V capable, **1–5 V is the usable range** (limited by
  the Vgs of the reverse-protection MOSFET); 0–500 mA current sense and digital
  fuse; default limit 300 mA (which is also the rated maximum — the extra
  headroom is for spikes); adjustable undervoltage trip, default 10%.
- A tripped limit disables the supply, inverts the terminal colours, rings the
  bell, prints an error, and **halts command execution**. Re-arm with `W`.
- The VOUT/VREF pin is a one-way valve: you can instead feed the target's own
  supply *into* it and the Bus Pirate buffers and pull-ups will run at that
  voltage. **5 V DC absolute maximum** — more damages the Bus Pirate and your
  computer.
- Pull-ups are 10 kΩ to whatever is on VOUT/VREF. `P` on, `p` off. They are
  **required** for I2C, 1-Wire, HDUART, and 2WIRE — those buses only ever pull
  low, so without pull-ups there is no logic 1 at all. Classic symptom: the I2C
  `scan` reports a device at *every* address.
- With no voltage on VOUT/VREF, `P` warns and does nothing useful. Check with `v`.

## Measurement features

- **Voltage** — `v` (once) / `V` (continuous) reports VOUT and all eight IO pins;
  `v.<pin>` reads one pin inside a transaction. The live VT100 status bar and the
  LCD show the same data continuously.
- **Frequency counter** — `f <pin>` once, `F <pin>` continuous (odd pins only).
  Reports frequency, period, and duty cycle.
- **Frequency generator (PWM)** — `G` (menu) or `G <pin>`; enter a period or
  frequency *with units* (`12.4khz`, `1ms`, `500ns`) and a duty cycle *with the
  percent sign* (`35%`). `g` / `g <pin>` disables. Shows as `PWM` on the status
  bar and LCD.
- **Logic analyzer** — 8 channels, 131 K samples, 62.5 MSPS, trigger on one pin
  high or low. Three front ends: `logic` in the terminal (ASCII graph, plus
  "follow along" capture that fires on every bus transaction), SUMP for
  sigrok/PulseView, and FALA (follow-along) for a patched PulseView. See
  `references/automation.md`.
- **Oscilloscope** — `d` → Scope puts a scope on the LCD. 0.5 MSPS, 12-bit, one
  channel, any IO pin: fine for audio and slow analog, useless above ~500 kHz.
  Commands: `sr <pin> <o|n|a>` run (once/normal/auto), `ss` stop, `x` timebase,
  `y` volts, `t` trigger. Those drop into a single-key interactive mode
  (`+ - ^ v < > B M E T r s o n a t x y`, enter to leave).

## Gotchas

- **It boots into HiZ.** No mode, no power, no pull-ups — commands "do nothing"
  until you `m`, then `W`, then `P`.
- **Pick modes and binmodes by name, not menu number.** The numbering differs
  between firmware builds (the docs themselves show several different menus).
- **8-bit I2C addresses** in bus syntax (`0xA0`/`0xA1`), 7-bit in datasheets.
- **A bus line must start with `[`, `{`, or `>`.** Otherwise it is a terminal
  command and you will get an error, or worse, something unrelated.
- **Pull-ups need a voltage on VOUT/VREF**, from `W` or from the target.
- **`a`/`A`/`@` refuse pins already owned** by the active mode or by a PWM.
- **Frequency measurement is odd-pins-only**; paired PWM pins share a frequency.
- **The onboard USB disk is read-only while a terminal is connected**, and it
  detaches/reattaches whenever the Bus Pirate writes to it (that is deliberate,
  to stop corruption). Close the terminal to copy files onto it.
- **Scripts cannot answer menus** — only lines typed at the command prompt.
  `W 3.3 50` works; `W` followed by `3.3` on the next line does not.
- **Button script assignments do not survive a reboot.**
- **SUMP and follow-along logic analyzer share one capture buffer** and cannot
  run simultaneously (you get a memory error).
- **Before Bus Pirate 6, logic capture is taken behind the IO buffer** — you see
  what the Bus Pirate intended to drive, not what is actually on the wire. Fine
  when all pins are inputs (HiZ), misleading when driving.
- **Self-test (`~`) requires HiZ and nothing connected**; attached devices can be
  damaged and will fail the test.
- **Wrong `.uf2` → menacing red blink.** Hold the underside button while
  plugging in to force the bootloader, then load the other file. Bootloader disk
  names: `RPI-RP2` (v5), `RP2350` or `BP__BOOT` (v6).
- **The terminal is a full-screen ANSI UI.** The live status bar constantly
  rewrites the bottom of the screen, so naive `readline()` scripting sees escape
  sequences and cursor moves interleaved with your data. Fixes, in order of
  preference: use the BPIO2 binary port instead; answer `n` to the VT100 prompt;
  or set `"terminal_ansi_color": 0` and `"terminal_ansi_statusbar": 0` in
  `bpconfig.bp`. Details in `references/automation.md`.
- **255 character limit** on a single terminal line.

## Sources

- Command reference (the single biggest page, and the most current):
  <https://docs.buspirate.com/docs/command-reference/>
- Quick setup / port identification: <https://docs.buspirate.com/docs/tutorial-basics/quick-setup/>
- IO pin descriptions and the RP2040 pin map: <https://docs.buspirate.com/docs/overview/io-pins/>
- Logic analyzer: <https://docs.buspirate.com/docs/logic-analyzer/logicanalyzer/>
- Oscilloscope: <https://docs.buspirate.com/docs/scope/>
- BPIO2 scripting interface: <https://docs.buspirate.com/docs/binmode-reference/protocol-bpio2/>
- Firmware downloads/upgrade: <https://docs.buspirate.com/docs/downloads/>

The device's own `?`, `help mode`, and `<command> -h` output is generated from
the running firmware and is more current than any of the above — including this
skill. Check it before concluding a documented flag does not exist.
