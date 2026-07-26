<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Driving a Bus Pirate from a host script

Companion to `SKILL.md`. Three ways to automate, in descending order of
robustness:

1. **BPIO2** on the second USB serial port — a real binary protocol with typed
   requests and responses. Use this whenever you are writing code.
2. **On-device `script` / `macro` files** on the internal flash — good for
   canned sequences and button-triggered actions, no host code at all.
3. **Screen-scraping the interactive terminal** — always possible, never
   pleasant. Use it when BPIO2 does not cover a command you need (most of the
   `flash`/`eeprom`/`ddr5`/`bluetag` tooling only exists in the terminal).

## The second serial port and `binmode`

A Bus Pirate 5/6 enumerates two CDC serial ports. The first is the user
terminal; the second speaks whatever binary protocol `binmode` selected:

| binmode | For |
|---|---|
| SUMP logic analyzer | sigrok/PulseView via the `ols` driver |
| **BPIO2 flatbuffer interface** | general scripting (this is the one you want) |
| Arduino CH32V003 SWIO | programming CH32V003 parts |
| Follow along logic analyzer (FALA) | patched PulseView, live capture per transaction |
| Legacy Binary Mode (experimental) | flashrom and AVRDUDE |
| IRMAN IR decoder | LIRC and friends |
| AIR capture | AnalysIR |

```
HiZ> binmode          # menu; select by NAME — the numbering has changed between builds
```

Older firmware listed slot 2 as "Binmode test framework"; current firmware lists
it as "BPIO2 flatbuffer interface". Save it as the default when prompted so the
choice survives a reboot. If a host tool sees nothing, the two usual causes are
the wrong binmode and the wrong serial port.

## BPIO2

BPIO2 is FlatBuffers messages, COBS-framed (a `0x00` byte terminates a packet),
over the second CDC port. It replaces the v3-era BBIO1 bit-bang protocol
entirely — nothing carries over.

Official clients: a **Python library** (`pybpio`) plus examples and precompiled
FlatBuffers tooling, and a **Rust crate**. Precompiled tooling is available for
the usual language set; to regenerate it yourself use `flatc --python bpio.fbs`
(or `flatcc -a bpio.fbs` for C). Python needs `pyserial` and a `cobs` package.

Message model — three request/response pairs wrapped in a packet:

- `StatusRequest`/`StatusResponse` — versions, current mode, pin labels, PSU
  state and measurements, per-pin ADC millivolts, IO direction/value bitmaps,
  pull-up state, disk usage, LED count.
- `ConfigurationRequest`/`ConfigurationResponse` — change mode and mode
  settings, and simultaneously set PSU/pull-ups/IO/LEDs.
- `DataRequest`/`DataResponse` — the actual bus traffic: start/stop conditions,
  a write vector, and a byte count to read.

`RequestPacket` carries `version_major` (2 for current tooling) and
`minimum_version_minor`; `ResponsePacket` carries an `error` string that is
empty on success. Same-major FlatBuffers are backwards compatible, so old hosts
keep working against new firmware.

### Python quick reference

```python
from pybpio.bpio_client import BPIOClient
from pybpio.bpio_i2c import BPIOI2C

client = BPIOClient("/dev/cu.usbmodem…123")   # the SECOND port
client.show_status()                          # human-readable dump
status = client.status_request()              # same data as a dict; status['error'] is None on success

i2c = BPIOI2C(client)
i2c.configure(speed=400_000, clock_stretch=False,
              pullup_enable=True, psu_enable=True,
              psu_set_mv=3300, psu_set_ma=0)   # mode + hardware in one call

print([hex(a) for a in i2c.scan()])            # 0x00–0x7F sweep
res = i2c.transfer(write_data=[0xA0, 0x00], read_bytes=2)   # START, write, restart, read, STOP
```

Mode classes: `BPIOI2C`, `BPIOSPI`, `BPIO1Wire`, `BPIOUART`, `BPIOLED`. Each has
`configure(**kwargs)`, the mode's primitives, and the whole shared getter/setter
surface.

| Mode class | Primitives |
|---|---|
| I2C | `start()` `stop()` `write(data)` `read(n)` `transfer(write_data, read_bytes)` `scan(start,end)` |
| SPI | `select()` `deselect()` `write()` `read(n)` `transfer(write_data, read_bytes)` `transfer_duplex(write_data)` |
| 1-Wire | `reset()` `write()` `read(n)` `transfer(write_data, read_bytes)` |
| UART | `write()` `transfer(write_data, read_bytes)` (1 s read timeout) `read_async(clear_buffer)`, or an `async_callback=` for push delivery |
| LED | colour/raw writes for onboard, WS2812 and APA102 strips |

For I2C `transfer()`, the **first byte of `write_data` is the 8-bit device
address** and it is reused for the read half of the transaction.

Shared configuration keyword arguments (they map 1:1 onto FlatBuffers fields):

| Mode config | `speed` `data_bits` `parity` `stop_bits` `flow_control` `signal_inversion` `clock_stretch` `clock_polarity` `clock_phase` `chip_select_idle` `submode` `tx_modulation` `rx_sensor` |
|---|---|
| Hardware | `mode_bitorder_msb/lsb` `psu_enable/disable` `psu_set_mv` `psu_set_ma` (0 = unlimited, default 300) `pullup_enable/disable` `io_direction_mask` `io_direction` `io_value_mask` `io_value` `led_resume` `led_color` `print_string` |

Setters return `True`/`False`/`None`; getters return `None` on error. Each
getter is a round trip — call `get_status()` once and index the dict instead of
calling ten getters.

Useful odds and ends: `set_print_string("…")` writes into the Bus Pirate's own
terminal (great for correlating a host script with a human watching the screen);
`set_hardware_bootloader()`, `set_hardware_reset()`, `set_hardware_selftest()`;
`set_io_direction(mask, dir)` / `set_io_value(mask, val)` for bitmask pin control.

### Debugging BPIO2

Set `"bpio_debug_enable": 1` in `BPCONFIG.BP` on the internal disk and reboot.
Every request is then decoded in the terminal:

```
[BPIO] Packet Type: 3
[Data Request] Start main condition: true
[Data Request] Data write: 0xA0 0x00
[Data Request] Bytes to read: 16
[I2C] Performing transaction
```

No `BPCONFIG.BP` yet? Run `c` then `x` in the terminal to create it.

## On-device scripting

Files live on the Bus Pirate's own FAT16 flash. Remember the disk is **read-only
to the host while a terminal is connected** — close the terminal to copy files
in, or write them with `dump`.

**Macros** (`.mcr`) — numbered one-liners:

```
# This is my example macro file
#! Enable power supply 3.3V, 100mA limit
1:W 3.3 100
#! Read 5 bytes from an I2C EEPROM
2:[0xa0 0][0xa1 r:5]
```

`macro -f macros.mcr` selects the file, `macro -l` lists it, `macro 1` runs an
entry. `#` is a comment, `#!` is a description shown by `-l`.

**Scripts** (`.scr`) — one command per line, `#` comments:

```
HiZ> script example.scr        # -p pause each line, -d hide comments, -x exit on error
```

The one hard limit: **scripts inject lines at the command prompt only.** They
cannot answer a menu. `W 3.3 50` works; `W` followed by `3.3` and `50` on
subsequent lines does not. Type `x` to abort a running script.

**Button** — `button short -f foo.scr` / `button long -f bar.scr`; defaults are
`button.scr` and `buttlong.scr` in the root. **These assignments do not survive
a reboot.**

**pause** — `pause` (any key), `pause -b` (button), `pause -b -k` (either),
`pause -x` (allow `x` to escape a script). The obvious way to say "now move the
probe" in the middle of an automated sequence.

## Screen-scraping the terminal

The terminal is a full-screen VT100 UI: colour, a live status bar redrawn at the
bottom, and cursor positioning interleaved with command output. Naive
`readline()` gets escape sequences and partial redraws. Tame it before you parse
it — in this order:

1. **Prefer BPIO2.** Really.
2. **Answer `n`** to `VT100 compatible color mode? (Y/n)>` after a reset/reboot.
   That selects the legacy monochrome ASCII mode and no status bar.
3. **Or turn it off persistently** in `BPCONFIG.BP`: `"terminal_ansi_color": 0`
   and `"terminal_ansi_statusbar": 0`. Same settings are reachable from the `c`
   menu (2 = ANSI color mode, 3 = ANSI toolbar mode) and are saved on exit.
4. **Strip whatever is left** host-side: `re.sub(rb'\x1b\[[0-9;?]*[a-zA-Z]', b'', buf)`.

Then the framing that actually works (host-side pattern, not a documented API —
verify against your firmware):

- The device echoes what you type. Send `b"...\r"` and expect the echo back.
- **Read until the prompt.** The prompt is the mode name plus `"> "` —
  `HiZ> `, `I2C> `, `SPI> `, `LED-(WS2812)> `, `INFRARED-(RAW)> `. A regex like
  `rb'\r?\n?[A-Za-z0-9\-()]+> $'` on the tail of the buffer is a reliable
  end-of-response marker; anything between your echoed command and that prompt
  is the response.
- **Send a bare `\r` first** and wait for a prompt to prove you have the terminal
  port and not the binary one.
- **`cls`** clears and re-initialises the terminal — useful right after
  attaching, since you may have joined mid-screen.
- **Keep lines under 255 characters.**
- **Watch for the halt condition.** A PSU over-current or undervoltage trip
  disables the supply, inverts the colours, rings the bell (`\a`), prints an
  error, and **stops executing queued commands**. If you are streaming a batch,
  detect the error and re-arm with `W` rather than plowing on.
- Long operations (`flash read`, `eeprom test`, `bluetag`) print progress and
  can page with "space to continue, x to exit" — pass `-c` to disable paging
  where the command supports it, and set generous read timeouts.
- `bridge` and the scope's interactive modes swallow the command line entirely:
  `bridge` only exits on a **physical button press**, so never enter it from a
  script you cannot babysit.

## Logic analyzer front ends

All three share one capture core: 8 channels, 131 K samples, 62.5 MSPS (more if
overclocked), trigger on a single pin high or low.

- **`logic` in the terminal** — `logic start|stop|show|hide|nav`, `logic -i`
  (info), `-f <Hz>` sample rate, `-o <N>` oversample multiplier, `-0`/`-1` graph
  characters, `-d` debug. It draws an ASCII graph in the toolbar and captures
  automatically on every bus transaction ("follow along"); `logic nav` pans with
  the arrow keys, `x` exits. Entering a mode auto-sets 8× oversampling of the
  bus speed.
- **SUMP → PulseView** — `binmode` → SUMP, then in PulseView pick
  *Openbench Logic Sniffer & SUMP compatibles (ols)*, interface *Serial Port*,
  and the **second** Bus Pirate port, then *Scan for devices*. A 3.3 V supply is
  switched on automatically when the SUMP port is opened (if the terminal is
  closed or is in HiZ) and off when it closes — the IO buffers need power or you
  see nothing. Windows needs the patched PulseView build.
- **FALA → patched PulseView** — `binmode` → Follow along logic analyzer, driver
  *BP5 + binmode-FALA*. Every transaction pushes its samples straight into
  PulseView. Windows-only for now (Linux users have built libsigrok with FALA
  support by hand), and only some modes are wired up — modes with internal
  buffers can end the capture early or return nothing.

**SUMP and follow-along cannot run at the same time** — they share the capture
buffer and you get a memory error. Before Bus Pirate 6 the capture is taken
behind the IO buffer, so it shows what the Bus Pirate drove, not what the bus
actually did; that only matters when pins are outputs.

## flashrom and AVRDUDE

`binmode` → *Legacy Binary Mode for Flashrom and AVRdude (EXPERIMENTAL)*, then
point the tool at the **second** serial port:

```
flashrom --progress -V -c "W25Q64JV-.Q" \
  -p buspirate_spi:dev=COM54,serialspeed=115200,spispeed=1M \
  -r flash_content.bin
```

On macOS/Linux substitute the `/dev/cu.usbmodem…` or `/dev/ttyACM…` node for
`COM54`. AVRDUDE (and the AVRDUDESS GUI) work the same way. For most NOR flash
work the built-in `flash` command in SPI mode is faster to reach for and does
not need a binmode switch.
