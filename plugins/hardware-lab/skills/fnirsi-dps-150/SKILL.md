---
name: fnirsi-dps-150
description: Read and control a FNIRSI DPS-150 USB-C bench power supply over its USB serial port with the bundled dps150.py: status, voltage and current setpoints, output on/off, plus the binary protocol, the handshake that makes a silent port answer, and which fields were verified on the wire. Use when the user wants to connect to, automate, or script a DPS-150, or has a silent "AT32 Virtual Com Port" (USB ID 2e3c:5740) that may be a bench supply.
---

<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# fnirsi-dps-150

Remote control for the FNIRSI DPS-150, a 30 V / 5.1 A / 150 W supply fed
from USB-C. Verified on a unit whose version replies were `V1.0` and `V1.2`.

**Terms.** *Setpoint*: the voltage or current limit the supply aims for.
*CV/CC*: constant voltage / constant current, which of the two setpoints
is in control. *Session*: the handshake that makes the supply answer.

## Before you touch the output

- **`output on` energizes the terminals.** Find out what is connected
  first, and confirm with the user. Start at a low voltage and a low
  current limit.
- **The output stays on after the session ends.** Verified: it held
  1.000 V through a disconnect and a reconnect. Nothing turns it off for
  you when the tool exits, so run `output off` yourself.
- **Check `set_v` before enabling.** Setpoints persist across sessions,
  so a leftover value from the front panel may be much higher than you
  expect.
- **Identify the port first when several instruments are attached.**
  `2e3c:5740` is Artery's generic ID, so other devices can share it. Do
  not send this handshake to a port another session is using.

## Using the tool

Needs `uv` (or Python 3.9+ with `pyserial`). Run from this skill's
directory. Global flags go before the subcommand.

```bash
uv run scripts/dps150.py doctor
uv run scripts/dps150.py --json status
uv run scripts/dps150.py set --volts 3.3 --amps 0.1
uv run scripts/dps150.py output on --yes
uv run scripts/dps150.py output off
```

The port is found by USB ID. Pass `--port <path>` if more than one
matches. `set` and `output` accept `--dry-run`, and every write is read
back. `status` and `doctor` still run the session handshake but write no
setpoint or output state.

`output_v` takes about a second to settle after a switch: the status
printed by `output on` or `output off` can show a value in transit, such
as 0.661 V on the way to 1.000 V. Trust `output_on` there, and run
`status` a second later for the voltage.

| Exit | Meaning | What to do |
| --- | --- | --- |
| 0 | success | |
| 2 | usage error, several ports, or `output on` without `--yes` | fix the command |
| 3 | `pyserial` missing, wrong model, or request above the upper limit | fix the cause; for the limit, see below |
| 4 | no port, port busy, or no handshake | check the cable, power, and other users of the port |
| 21 | a write read back differently | run `status` before retrying |
| 22 | no reply after a write | run `status` before retrying; the write may have landed |

## The input sets the ceiling

The maximum output follows the input. On a 5.13 V input,
`upper_limit_v` read 4.93 V, always 0.2 V below the input. A setpoint of
12 V was stored without complaint, but it cannot be reached from that
input. With the output off the tool stores such a setpoint, so you can
preset it. It refuses, with exit 3, `output on` while the setpoint is
above `upper_limit_v`, and `set` above it while the output is on. If
`input_v` is near 5 V, the USB-C source or cable is not providing a
higher voltage. What the supply does when enabled above the limit was
not tested.

## Protocol

USB CDC serial. Verified at 9600 8N1 with DTR off and RTS on. Another
implementation opens at 115200 with hardware flow control, so the baud
rate may not matter on this USB link.

**The port is silent until the handshake.** It sends nothing on its own,
and a valid model query before the handshake gets no reply. Do not read
that silence as a dead device or a wrong baud rate.

Frame: `[DIR][START][CMD][LEN][DATA...][CHK]`, with `CHK = (CMD + LEN +
sum(DATA)) mod 256`. DIR and START are not in the sum.

| Byte | Value |
| --- | --- |
| DIR | `F1` host to device, `F0` device to host |
| START | `A1` read or reply, `B1` write, `C1` session, `B0` the magic frame |

Session, as literal bytes:

1. Send `f1 c1 00 01 01 02`, wait 200 ms.
2. Poll `f1 a1 e1 01 00 e2` until the reply payload is `01`.
3. Send `f1 b0 00 01 01 01`.
4. To end, send `f1 c1 00 01 00 01` and close the port.

After the handshake the supply pushes telemetry about every 600 ms, so
skip unrelated frames while waiting for a reply.

| CMD | Direction | Payload | Meaning |
| --- | --- | --- | --- |
| `C0` | push | f32 | input voltage |
| `C1` / `C2` | write | f32 | voltage / current setpoint |
| `C3` | push | 3 × f32 | output V, A, W |
| `C4` | push | f32 | temperature (see below) |
| `DB` | write | u8 | output: `01` on, `00` off |
| `DE` | read | ASCII | model, `DPS-150` |
| `DF` / `E0` | read | ASCII | versions (see below) |
| `E2` / `E3` | push | f32 | upper limit voltage / current |
| `FF` | read | 139 bytes | full status |

All floats are little-endian. Worked examples: 12.0 V is
`f1 b1 c1 04 00 00 40 41 46`; a model read is `f1 a1 de 01 00 df`.

Full status offsets (note the tail is unaligned):

| Offset | Type | Field |
| --- | --- | --- |
| 0, 4, 8 | f32 | input V, set V, set A |
| 12, 16, 20 | f32 | output V, A, W |
| 24 | f32 | temperature |
| 28–75 | 12 × f32 | six preset V/A pairs |
| 76–92 | 5 × f32 | OVP, OCP, OPP, OTP, LVP protection limits |
| 96, 97, 98 | u8 | brightness, volume, metering |
| 99, 103 | f32 | capacity Ah, energy Wh |
| 107 | u8 | output state, 1 on |
| 108 | u8 | protection: 1 OVP, 2 OCP, 3 OPP, 4 OTP, 5 LVP |
| 109 | u8 | 0 CC, 1 CV |
| 111, 115 | f32 | upper limit V, A |

## What was and was not verified

Verified on the wire: the handshake, all reads, `C1`, `C2`, `DB`, setpoint
readback, and byte 107 following the output through on and off.

Not exercised: any real load, so current readings, CC mode, and current
limiting are unproven. Protection trips, presets, and the setters for
protection limits were not tried, and the tool does not expose them.

The two public references disagree, so treat these as open:

- **`DF` / `E0`:** one calls `DF` hardware and `E0` firmware, the other
  the reverse. The tool prints them by ID for that reason.
- **`C4` / `E2`:** one calls these a boost rail and an alternate input
  reading. The other calls them temperature and upper limit voltage.
  This skill uses the second: `C4` read about 27.4 at room temperature
  and `E2` tracked the input minus 0.2 V, but neither was tested
  against a thermometer or a changed input.

## References

- [cho45/fnirsi-dps-150](https://github.com/cho45/fnirsi-dps-150): WebSerial
  implementation, the source of the full status layout.
- [DPS-150 protocol write-up](https://philipp-iot.github.io/fnirsi_protocol/):
  the handshake sequence and serial settings.
