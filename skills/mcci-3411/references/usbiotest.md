<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# usbiotest — host-side testing against a Model 3411

`usbiotest` is MCCI's command-line test driver. It runs on the **system under
test** and talks to the 3411 over the **USB-C data port**, not the control
port. It uses the OS USB stack directly, so no MCCI driver is needed on Linux
or Windows. Windows users who want a GUI can use `USBIOEx` instead, which does
require MCCI's Model 3411 driver.

Distributed as `mcci_usbiotest-v2.0.0.zip` (Linux x86_64 and AARCH64, Windows
i386 and x64) from the
[MCCI knowledge base](https://portal.mcci.com/portal/en/kb/articles/mcci-model-3411-loopback-applications).

On Linux you generally need `sudo`, or a udev rule granting access to
`040e:*`.

## Synopsis

```
usbiotest [options] <deviceId>

usbiotest -i <IN_PIPE> -o <OUT_PIPE> -N <COUNT> -T <TESTTYPE> \
  -m <MODE> -b <BUFFERSIZE> -v -F <FREQ> -t <TIMEOUT> <VID>:<PID>
```

## Options

| Option | Meaning |
|---|---|
| `-i <pipe>` | IN endpoint, in C/I/A/P notation. `-i -` clears it. |
| `-o <pipe>` | OUT endpoint. `-o -` clears it. |
| `-N <n>` | Iteration count. `0` runs indefinitely. |
| `-T <type>` | `benchmark`, `integrity`, or `view`. |
| `-m <mode>` | Data pattern: `normal`, `random`, or `sweep`. |
| `-b <bytes>` | Transfer buffer size. Must match the device buffer. |
| `-F <freq>` | Report every N iterations. `0` suppresses the display. |
| `-t <ms>` | Per-transfer timeout in milliseconds. |
| `-I <n>` | Max isochronous packets per transfer. `-I 0` uses the default. |
| `-z` | Send a zero-length packet at the end of a transfer. |
| `-v` | Verbose. With no test options, lists every pipe on the device. |
| `-D <mask>` | Debug mask. `0x10` dumps a trace at exit; `0xffffffff` is everything. |
| `-h` | Full help. |

### Test types

- **`benchmark`** — raw throughput, no validation. Fastest; this is what you
  use for performance numbers.
- **`integrity`** — validates every received byte against what was sent. Much
  slower, and the right choice for signal-integrity or cable/hub debugging.
- **`view`** — hex-dumps received data. Slowest; for eyeballing small
  transfers only.

## Pipe notation

Pipes are `Configuration/Interface/AlternateSetting/PipeIndex`. Always confirm
against the device you have, since the map depends on mode and firmware:

```bash
./usbiotest -v 040e:f645
```

Loopback mode (firmware v2.0.0) exposes:

| Purpose | IN | OUT | Type | MaxPacketSize |
|---|---|---|---|---|
| Bulk throughput (primary) | `0/0/1/0` | `0/0/1/1` | Bulk | 1024 |
| Interrupt, small | `0/0/2/0` | `0/0/2/1` | Interrupt | 64 |
| Interrupt, large | `0/0/3/0` | `0/0/3/1` | Interrupt | 16384 |
| Isochronous, low bandwidth | `0/0/4/0` | `0/0/4/1` | Isoch | 512 |
| Isochronous 48K | `0/0/5/0` | `0/0/5/1` | Isoch | 49152 |
| Isochronous 96K (max) | `0/0/6/0` | `0/0/6/1` | Isoch | 98304 |
| Bulk sink (write only) | — | `0/0/7/0` | Bulk OUT | 1024 |
| Bulk source (read only) | `0/0/8/0` | — | Bulk IN | 1024 |

96K high-bandwidth isochronous requires Gen2; at Gen1 the ceiling is 48K.

## Buffer sizing

`-b` must agree with the device-side buffer. Check it from the control port
with `getbuffersize` (which prints **hex**) and convert:

| Endpoint type | Typical device value | `-b` decimal |
|---|---|---|
| Bulk | `0x100000` | `1048576` |
| Interrupt | `0x4000` | `16384` |
| Isochronous | `0x180000` | `1572864` |

MCCI's documented sizing rules, if you are choosing a new value and setting it
with `setbuffersize`:

- Bulk: `MaxPacketSize × MaxPacketSize` — e.g. `1024 × 1024 = 1048576`
- Isochronous: `MaxPacketSize × (8 ÷ Interval) × 20` — e.g.
  `49152 × 8 × 20 = 7864320`

A mismatch between `-b` and the device buffer shows up as failed transfers or
implausible throughput, not a clear error, so verify it before believing any
number.

## Device selection

| Syntax | Selects |
|---|---|
| `040e:f645` | First matching device |
| `040e:f645/1` | Second matching device (0-indexed) |
| `040e:f645::0002CC00XXXX` | By serial number — use this in fixtures |
| `040e:f645:2000` | VID + PID + revision |
| `040e:f645:2000:0002CC00XXXX` | Fully specified |

The serial number here is the same value `getserialnum` reports on the control
port, which is how you tie a control port and a data port back to one physical
board when a fixture holds several.

## Worked invocations

```bash
# Bulk throughput benchmark, 100 iterations, report every 100
sudo ./usbiotest -i 0/0/1/0 -o 0/0/1/1 -N 100 -T benchmark \
  -b 1048576 -F 100 040e:f645

# Data integrity soak, 1000 iterations
sudo ./usbiotest -i 0/0/1/0 -o 0/0/1/1 -N 1000 -T integrity \
  -b 1048576 -F 100 040e:f645

# Isochronous 48K benchmark
sudo ./usbiotest -i 0/0/5/0 -o 0/0/5/1 -N 100 -T benchmark \
  -b 7864320 -F 100 040e:f645

# OUT-only (host writes into the sink) — isolates one direction
./usbiotest -o 0/0/7/0 -N 100 -T benchmark -b 1048576 -F 100 040e:f645

# Multi-bulk mode (device must be in setdevicemode 2)
sudo ./usbiotest -i 0/0/1/0 -o 0/0/1/1 -N 1000 -T benchmark \
  -b 1048576 -F 1000 040e:020c

# Enumerate pipes without running a test
./usbiotest -v 040e:f645
```

## Interpreting results

- Bidirectional bulk on a healthy Gen2 host should approach MCCI's headline
  ~8 Gbps in each direction. Substantially less usually means the host
  negotiated Gen1 (check the OLED, or `getdevicespeed` on the control port), an
  intervening hub or cable is Gen1-only, or the host controller cannot sustain
  1 MB transfers.
- Run one direction at a time (`0/0/7/0` sink, `0/0/8/0` source) to work out
  which direction is the bottleneck before blaming the link.
- If throughput is fine but `integrity` fails, suspect the cable, the connector,
  or SSC interaction — `controlssc 0` on the control port is a quick A/B test.
