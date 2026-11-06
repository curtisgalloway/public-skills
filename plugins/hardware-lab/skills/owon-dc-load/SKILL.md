---
name: owon-dc-load
description: Query an OWON OEL-series electronic DC load (tested on an OEL1520) over its USB-serial port - connection settings, the queries seen to work, and the non-standard replies that trip up generic SCPI clients. Use when the user wants to talk to, read, or script an OWON electronic load. Writes to the load are untested.
---

<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# owon-dc-load

Serial control notes for OWON OEL-series electronic DC loads. Everything
here was observed on one OEL1520, firmware FV1.5.0, with its input off
and reading 0 V. Other models and firmware are untested; start
with `*IDN?`.

**Only queries have been tested, apart from `SYST:REM`.** No setpoint,
mode or input command has been sent. Before scripting writes, check the
syntax against OWON's documentation and try it with no device attached.

## Connecting

- The tested load appeared on macOS as `/dev/cu.usbserial-*`, with a
  `1a86:7523` (CH340) USB-serial adapter on the bus. Linux is untested;
  expect `/dev/ttyUSB*`.
- It answered at **115200 baud**. pyserial's defaults (8N1, no flow
  control) worked.
- Queries ended with `\n`, `\r` or `\r\n` were all answered.
- Replies end with `\n`.

```python
import serial, time
s = serial.Serial('<port>', 115200, timeout=1.0)
time.sleep(0.2)
s.write(b'*IDN?\n')
time.sleep(0.3)
print(s.read(200))   # b'OWON,OEL1520,<serial>,FV:V1.5.0\n'
```

## Send `SYST:REM` first

In the first session after connecting, `*IDN?` answered but `:INPut?`,
`:FUNCtion?` and the `:MEASure:...?` queries returned nothing. After
`SYST:REM` was sent, all of them answered, including in later
connections. The likely reading is that other queries need remote mode
and that it persists, but this was not isolated. `SYST:REM` sends no
reply. Its effect on the front panel, and how to leave remote mode, were
not tested.

## Queries seen to work

After `SYST:REM`, short and long keywords both worked, with or without
a leading colon. Replies are bare values with no units. The readings
below were taken with the input off, so measured values were all
zero.

| Query | Reply seen | Notes |
| --- | --- | --- |
| `*IDN?` | `OWON,<model>,<serial>,FV:V<version>` | identity |
| `FUNC?` | `current` | other modes not seen |
| `INP?` | `OFF` | `ON` not seen |
| `INP:SHORt?` | `OFF` | `ON` not seen |
| `MEAS:VOLT?`, `MEAS:CURR?`, `MEAS:POW?` | `0.000` | presumably V, A, W |
| `VOLT?`, `CURR?`, `POW?` | `0.000` | presumably setpoints |
| `RES?` | `1000.00` | presumably a setpoint |
| `CURR:RANGe?`, `VOLT:RANGe?` | `1` | meaning of the value unknown |
| `MODE?` | `0` | meaning unknown; prefer `FUNC?` |

## Non-standard replies

- **`*OPC?` returned `V2.12.2B.1C.D`**, not `1`. Do not use it as a
  completion check.
- **`SYST:ERR?` returned `0x0000`**, not the usual
  `<code>,"<message>"` pair. Other codes were not seen.
- **Unrecognized queries replied `ERR`.** Seen with `BOGUS?` and
  `TRIG:SOURce?`. Whether they also set `SYST:ERR?` was not checked.
- **`*RST?` returned nothing.** Whether it resets anything is unknown,
  so do not send it to a load with settings you want to keep.
