# kb2040-traffic-gen

A USB traffic generator for Cynthion capture sessions, in two pieces: a KB2040 running
CircuitPython emits a known sequence of HID and CDC patterns, and a host Python script drives
the other end of the CDC bulk endpoints, so the capture sees correlated traffic in both
directions.

The result is a recognizable, repeatable mix in `.pcap` captures: keyboard reports, mouse
moves, large and small bulk transfers, host-driven probes, and a hardware-reset
re-enumeration. Use it to test
[`cynthion-capture`](../../plugins/hardware-lab/skills/cynthion-capture/), validate decoders,
or exercise downstream pcap tooling.

## Hardware

- **Adafruit KB2040** (RP2040 board with a NeoPixel and a BOOT button). Any RP2040 with a
  NeoPixel on `board.NEOPIXEL` and `board.BUTTON` works, but pin names assume a stock KB2040.
- A USB-C cable from the KB2040 to the host, or to Cynthion's TARGET port when capturing.
- *Optional:* a [Great Scott Gadgets Cynthion](https://greatscottgadgets.com/cynthion/) wired
  between the KB2040 and the host to capture the traffic.

## Files

| File                | Runs on    | Purpose                                                                  |
| ------------------- | ---------- | ------------------------------------------------------------------------ |
| `boot.py`           | KB2040     | Enables 2× CDC (console + data) and HID (keyboard / mouse / consumer).   |
| `code.py`           | KB2040     | Pattern generator. Waits for trigger, runs through `PATTERNS`, repeats.  |
| `host_exerciser.py` | host PC    | Drives the CDC data port (echo + probes) and triggers pattern cycles.    |

## Device setup

1. Install CircuitPython 9.x on the KB2040. Adafruit's
   [installer](https://learn.adafruit.com/welcome-to-circuitpython/installing-circuitpython)
   covers the BOOTSEL → UF2 flow.
2. Put `adafruit_hid/` (keyboard, mouse, consumer control) from the Adafruit library bundle
   in `CIRCUITPY/lib/`.
3. Copy `boot.py` and `code.py` to the root of the `CIRCUITPY` drive.
4. Eject and reset. After re-enumeration the KB2040 exposes:
   - two CDC serial devices (REPL/console + data)
   - a composite HID device (keyboard + mouse + consumer control)

   At idle the NeoPixel breathes blue.

The HID patterns in `code.py`'s `PATTERNS` are **commented out** by default, so the KB2040
does not type into your workstation. Re-enable them once a Cynthion or another HID-isolating
fixture sits between the KB2040 and the host.

## Host setup

Requires Python 3.10+ and [`uv`](https://docs.astral.sh/uv/). The script declares its
dependencies inline (PEP 723), so `uv run` installs them. Check that the device is visible:

```bash
uv run host_exerciser.py --list
```

### Linux: serial port permissions

`/dev/ttyACM*` is owned by `root:dialout`. Add yourself to the group once:

```bash
sudo usermod -aG dialout $USER
```

Then log out and back in (or reboot) so running processes pick up the group. From a shell
that predates the change, use `sg dialout -c '...'` to start a command with the new
membership:

```bash
sg dialout -c 'uv run host_exerciser.py'
```

## Running

```bash
uv run host_exerciser.py
```

By default the script loops forever. Each cycle it:

1. waits for the KB2040 to appear and opens both CDC ports
2. sends `start\n` and runs threads that echo, drive, and observe
3. waits for the device's end-of-cycle `[reconnect]` pattern, which hard-resets the board
4. when the read threads exit (USB gone), tears down, waits ~2 s, and re-detects the device
   on its (possibly new) port names

Stop with Ctrl+C. Other modes:

| Command | Does |
| --- | --- |
| `uv run host_exerciser.py --once` | Runs one cycle and exits. For one-shot captures. |
| `uv run host_exerciser.py --port /dev/ttyACM3 --console-port /dev/ttyACM2` | Picks the ports by hand. |
| `uv run host_exerciser.py --list` | Lists candidate ports. |

By default the script picks the two lowest-numbered ports with Adafruit's VID (`0x239A`).
Pass the ports by hand if your machine has other Adafruit devices.

## The two CDC ports

The two CDC interfaces have separate roles, so pattern markers cannot corrupt echo
verification:

| Port              | CircuitPython side  | Host side       | Carries                                  |
| ----------------- | ------------------- | --------------- | ---------------------------------------- |
| Console (CDC #1)  | `usb_cdc.console`   | `--console-port`| Pattern markers (`[cdc-large]`, …), REPL |
| Data (CDC #2)     | `usb_cdc.data`      | `--port`        | Binary echo stream and host probe bursts |

On Linux the console enumerates first as the lower-numbered device (e.g. `/dev/ttyACM2`) and
the data port follows (e.g. `/dev/ttyACM3`).

## Patterns

`code.py`'s `PATTERNS` list runs in order each cycle. The bracketed markers are what the host
logs from the console port.

### HID (commented out by default, for local safety)

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

The host's probe thread sends a 16-byte burst every 500 ms. Unchecked, those probes would land
inside the device's echo verification windows and break the comparison, so the host watches
the console port for pattern markers and gates the probe thread:

- **Closed** during `[cdc-large]`, `[cdc-small]`, `[cdc-patterns]` and `[mixed-all]`, which
  verify their own echo.
- **Open** during `[cdc-receive]` (the device wants probes) and during HID-only patterns (CDC
  is idle; probes queue in the device's input buffer and are drained later).

The host log shows each `gate OPEN` / `gate CLOSE` transition.

## Reading the host log

Each line is one I/O event with a host-monotonic timestamp:

```
  7250.675  host→dev    16B  probe seq=0x00
  7250.681  console     15B  '--- start ---'
  7250.692  gate CLOSE  '[cdc-large]'
  7250.736  dev→host    64B  01010101010101010101010101010101...
```

- `host→dev`: bytes the host wrote to the data port (echo replies + probes)
- `dev→host`: bytes the device wrote to the data port (echo source data)
- `console`: bytes from the console port (pattern markers, REPL)
- `gate …`: probe-gate transitions

After each `[reconnect]`, expect a `--- session ended; device should be re-enumerating ---`
line, then `Opening data …` for the next cycle.

## Troubleshooting

**`Permission denied: '/dev/ttyACM*'`**: you're not in the `dialout` group. See
[Linux serial port permissions](#linux-serial-port-permissions).

**`KB2040 data port not found`**: run `--list` to confirm the ports exist. If they don't,
check the cable or press the device's reset. If only one Adafruit-VID port shows up, `boot.py`
didn't enable both CDC interfaces; copy it again.

**Device stops producing output mid-cycle**: usually the host echo thread died and the device
is blocked waiting for an echo that will never come. The supervisor loop recovers at the next
`[reconnect]`.

**Host shows `gate CLOSE` but never `gate OPEN` again**: the next pattern marker probably
arrived after a USB disconnect killed the console thread. The supervisor restarts on the next
cycle.

**NeoPixel breathes blue forever**: the device is idle, waiting for `start\n` or a BOOT-button
press, which means the host script isn't running (or was stopped with Ctrl+C). Start it again.

## License

Apache 2.0. See the repo-level [LICENSE](../../LICENSE).
