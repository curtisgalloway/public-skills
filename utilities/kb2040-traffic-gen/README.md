# kb2040-traffic-gen

A two-piece USB traffic generator for Cynthion capture sessions. A KB2040
running CircuitPython emits a known sequence of HID + CDC patterns, and a
host Python script drives the other end of the CDC bulk endpoints so the
capture sees correlated dev↔host traffic.

The point is to produce a recognisable, repeatable mix in `.pcap` captures:
keyboard reports, mouse moves, large/small bulk transfers, host-driven
probes, and a hardware-reset re-enumeration. Useful for testing
[`cynthion-capture`](../../skills/cynthion-capture/), validating decoders, or
exercising downstream pcap tooling.

## Hardware

- **Adafruit KB2040** (RP2040 board with a NeoPixel and a BOOT button) —
  any RP2040 with a NeoPixel on `board.NEOPIXEL` and `board.BUTTON` will
  work, but pin names assume a stock KB2040.
- USB-C cable from the KB2040 to the host (or to Cynthion's TARGET port if
  you're capturing).
- *Optional but useful:* a [Great Scott Gadgets
  Cynthion](https://greatscottgadgets.com/cynthion/) wired between the
  KB2040 and the host to capture the resulting traffic.

## Files

| File                | Runs on    | Purpose                                                                  |
| ------------------- | ---------- | ------------------------------------------------------------------------ |
| `boot.py`           | KB2040     | Enables 2× CDC (console + data) and HID (keyboard / mouse / consumer).   |
| `code.py`           | KB2040     | Pattern generator. Waits for trigger, runs through `PATTERNS`, repeats.  |
| `host_exerciser.py` | host PC    | Drives the CDC data port (echo + probes) and triggers pattern cycles.    |

## Device setup

1. Install CircuitPython 9.x on the KB2040 (Adafruit's
   [installer](https://learn.adafruit.com/welcome-to-circuitpython/installing-circuitpython)
   covers the BOOTSEL → UF2 flow).
2. Drop the Adafruit HID library bundle into `CIRCUITPY/lib/` — needs
   `adafruit_hid/` (keyboard, mouse, consumer control).
3. Copy `boot.py` and `code.py` to the root of the `CIRCUITPY` drive.
4. Eject and reset. After re-enumeration the KB2040 should expose:
   - Two CDC serial devices (REPL/console + data)
   - A composite HID device (keyboard + mouse + consumer control)
   - The NeoPixel will breathe blue at idle.

By default `PATTERNS` in `code.py` has the HID patterns **commented out** —
they're disabled when running locally so the KB2040 doesn't type into your
workstation. Re-enable them once you have a Cynthion or HID-isolating
fixture between the KB2040 and the host.

## Host setup

Requires Python 3.10+ and [`uv`](https://docs.astral.sh/uv/). The script
declares its own dependencies inline (PEP 723), so `uv run` handles the
rest:

```bash
uv run host_exerciser.py --list
```

### Linux: serial port permissions

`/dev/ttyACM*` is owned by `root:dialout`. Add yourself to the group once:

```bash
sudo usermod -aG dialout $USER
```

Then log out and back in (or reboot) so existing processes pick up the new
group. If you're stuck in a long-running shell that predates the group
change, prefix with `sg dialout -c '...'` to spawn one with the new
membership:

```bash
sg dialout -c 'uv run host_exerciser.py'
```

## Running

### Default: forever-loop

```bash
uv run host_exerciser.py
```

The supervisor waits for the KB2040 to appear, opens both CDC ports, sends
`start\n`, runs threads to echo/drive/observe, and waits for the device's
end-of-cycle `[reconnect]` pattern to hard-reset the board. When the read
threads exit (USB gone), it tears down, waits ~2 s, re-detects the device
on its (possibly new) port names, and starts the next cycle. Stop with
Ctrl+C.

### Single cycle

```bash
uv run host_exerciser.py --once
```

Runs one cycle and exits. Useful for one-shot captures.

### Manual port selection

```bash
uv run host_exerciser.py --port /dev/ttyACM3 --console-port /dev/ttyACM2
```

By default the script picks the two lowest-numbered ports with Adafruit's
VID (`0x239A`). Override if your machine has other Adafruit devices.

### List candidate ports

```bash
uv run host_exerciser.py --list
```

## How the two CDC ports work

The KB2040 exposes both CDC interfaces; their roles are deliberately split
so pattern markers can't corrupt echo verification:

| Port              | CircuitPython side  | Host side       | Carries                                  |
| ----------------- | ------------------- | --------------- | ---------------------------------------- |
| Console (CDC #1)  | `usb_cdc.console`   | `--console-port`| Pattern markers (`[cdc-large]`, …), REPL |
| Data (CDC #2)     | `usb_cdc.data`      | `--port`        | Binary echo stream and host probe bursts |

On Linux, the console enumerates first as the lower-numbered device
(e.g. `/dev/ttyACM2`), and the data port is the next one
(e.g. `/dev/ttyACM3`).

## Patterns

Defined in `code.py`'s `PATTERNS` list, executed in registry order each
cycle. Markers in brackets are what the host logs on the console port.

### HID (commented out by default — local-safety)

| Marker            | What it does                                              |
| ----------------- | --------------------------------------------------------- |
| `[kbd-burst]`     | Rapid keystrokes                                          |
| `[kbd-typing]`    | Simulated typing                                          |
| `[kbd-modifiers]` | Ctrl/Alt/Shift/GUI combos                                 |
| `[kbd-fkeys]`     | Function keys F1–F12                                      |
| `[mouse-circles]` | Circular pointer movement                                 |
| `[mouse-clicks]`  | Buttons + scroll wheel                                    |
| `[mouse-drag]`    | Click-hold-move sequences                                 |
| `[consumer-ctrl]` | Media keys (play, vol, etc.)                              |
| `[mixed-hid]`     | Concurrent kbd + mouse traffic                            |
| `[mixed-all]`     | HID + CDC echo together                                   |

### CDC (always enabled)

| Marker            | What it does                                                                                 |
| ----------------- | -------------------------------------------------------------------------------------------- |
| `[cdc-large]`     | Device writes ~16 KiB in 64-byte chunks, then reads the echo back and verifies.              |
| `[cdc-small]`     | Varied small packets (1–65 bytes) with echo verification.                                    |
| `[cdc-patterns]`  | Named data patterns (zeros, 0xFF, ramps, etc.) with echo.                                    |
| `[cdc-receive]`   | Host writes probe bursts, device reads and counts them. Probe-gate opens here.               |
| `[reconnect]`     | Hardware reset via `microcontroller.reset()` — always last, causes a full USB re-enumeration.|

## The probe gate

The host probe thread sends a 16-byte burst every 500 ms. Without
coordination, those probes would interleave into the device's echo
verification windows and break the comparison. So the host watches the
console port for pattern markers and gates the probe thread:

- **Gate closed** during `[cdc-large]`, `[cdc-small]`, `[cdc-patterns]`,
  `[mixed-all]` — these patterns verify their own echo.
- **Gate open** during `[cdc-receive]` (device wants to read probes) and
  during HID-only patterns (CDC is idle, probes just pile up in the
  device's input buffer for later draining).

Watch the host log for `gate OPEN` / `gate CLOSE` transitions.

## Reading the host log

Each line is one I/O event with a host-monotonic timestamp:

```
  7250.675  host→dev    16B  probe seq=0x00
  7250.681  console     15B  '--- start ---'
  7250.692  gate CLOSE  '[cdc-large]'
  7250.736  dev→host    64B  01010101010101010101010101010101...
```

- `host→dev` — bytes the host wrote to the data port (echo replies + probes)
- `dev→host` — bytes the device wrote to the data port (echo source data)
- `console`  — bytes from the console port (pattern markers, REPL)
- `gate …`   — probe-gate state transitions

After each `[reconnect]`, expect a `--- session ended; device should be
re-enumerating ---` line, then `Opening data …` again for the next cycle.

## Troubleshooting

**`Permission denied: '/dev/ttyACM*'`** — you're not in the `dialout`
group. See [Linux serial port permissions](#linux-serial-port-permissions).

**`KB2040 data port not found`** — `--list` to confirm the ports are
present. If they aren't, check the cable / press the device reset. If only
one Adafruit-VID port shows up, `boot.py` didn't enable both CDC
interfaces — re-copy it.

**Device stops generating output mid-cycle** — usually means the host
echo thread died and the device is blocked waiting for an echo it'll
never get. With the supervisor loop, this is recovered automatically at
the next `[reconnect]`.

**Host shows `gate CLOSE` but never `gate OPEN` again** — the next
pattern marker probably arrived after a USB disconnect that killed the
console thread. The supervisor will restart on the next cycle.

**NeoPixel breathing blue forever** — device is idle, waiting for
`start\n` or a BOOT-button press. Means the supervisor isn't running
(or got Ctrl+C'd). Restart the host script.

## License

Apache 2.0 — see the repo-level [LICENSE](../../LICENSE).
