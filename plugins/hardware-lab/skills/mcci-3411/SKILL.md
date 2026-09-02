---
name: mcci-3411
description: >-
  Operate an MCCI Model 3411 "Merganser" USB 3.2 Gen2 test device: find and drive its FTDI control
  port and on-device RTEMS shell, switch between loopback, USB-IF compliance, and multi-bulk
  personalities, and run host-side throughput and data-integrity tests with usbiotest. Use when an
  MCCI 3411, Merganser, or SuperMUTT-compatible loopback/compliance device comes up, or to
  benchmark USB 3.2 Gen2 host throughput. Covers the VID/PID confusion between the control and
  data ports.
---

<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# MCCI Model 3411 USB 3.2 Gen2 test device

The Model 3411 "Merganser" is a single-board USB 3.2 Gen2 (10 Gbps) **device**
— it is the thing you plug into a host you want to test, not an analyzer. A
Movidius MA2085 running MCCI's TrueTask USB stack sinks and sources data at
close to line rate (MCCI claims sustained 8 Gbps in each direction
concurrently), so it is used for host-controller and class-driver throughput
benchmarking, hub testing, USB-over-Thunderbolt/USB4 performance work,
manufacturing test, and USB-IF compliance runs.

It has **two USB ports, and they are completely different devices**:

| Port | Role | What the host sees |
|---|---|---|
| **USB-C** | Data port. Connects to the system under test (SUT). Upstream-facing. | `040e:f64x` — depends on the selected mode (see below) |
| **micro-B** | Control port. Connects to *your* control computer. Also powers the board, taking precedence over USB-C. | `0403:6010` — an FTDI FT2232H |

Both ports can be attached to the same machine, but in normal use the USB-C
port goes to the SUT and the micro-B port goes to whatever machine is running
the test automation.

## Read this first: the VID/PID does not match the documentation

MCCI's product documentation lists the Model 3411 as **VID `040E`** with
PID `F644` (compliance) or `F645` (loopback). Those identifiers belong to the
**USB-C data port only**, and they only appear while the USB-C port is plugged
into a host.

The device you actually script against — the micro-B **control** port — is an
FTDI FT2232H and enumerates as:

```
idVendor  0x0403   (Future Technology Devices International, not MCCI)
idProduct 0x6010   (FT2232C/D/H dual UART/FIFO)
bcdDevice 0x0700   (FT2232H)
Manufacturer  "MCCI"
Product       "MCCI Model 3411 Control"
```

So `lsusb`/`ioreg` showing `0403:6010` instead of `040e:f645` is **not** a
fault and **not** a wrong device. If you search for `040e` and find nothing,
the USB-C cable is simply not connected to the machine you are searching on.
Identify the control port by its **string descriptors** (`MCCI Model 3411
Control`) or its serial number, never by VID/PID alone — a bare `0403:6010`
is indistinguishable from any other FT2232H board.

## Finding the control port

The FT2232H exposes two channels, and only one of them is the shell:

- **Channel A** (first port node) — JTAG/MPSSE for Movidius MDK tooling and
  firmware update. Opening it as a serial port succeeds but it never answers.
- **Channel B** (second port node) — the RTEMS console. **This is the one you
  want.**

```bash
# macOS — two nodes appear, the console is the one ending in 1
ls /dev/cu.usbserial-*
#   /dev/cu.usbserial-<SERIAL>0    channel A (JTAG, silent)
#   /dev/cu.usbserial-<SERIAL>1    channel B (shell)  ← use this

# Linux
ls /dev/ttyUSB*
#   /dev/ttyUSB0  channel A        /dev/ttyUSB1  channel B  ← use this
```

`<SERIAL>` is the board's serial number (a 12-character string like
`0002CC00XXXX`), which the shell also reports via `getserialnum` — that is how
you match a control port to a physical board when several are attached.

No driver install is needed on Linux or macOS; the in-box FTDI VCP driver
handles it. On Windows, install the FTDI VCP driver if the port does not
appear.

The bundled helper does the channel-B selection for you:

```bash
uv run --with pyserial python3 scripts/mcci3411.py ports
```

## Talking to the shell

**115200 baud, 8 data bits, no parity, 1 stop bit, no flow control.** The
prompt is:

```
SHLL [/] #
```

It is an RTEMS shell, so alongside MCCI's own commands you get `date`, `sleep`,
`setenv`, `rtc`, `spi`, `i2cdetect`/`i2cget`/`i2cset`, filesystem and memory
commands, and `logoff`/`exit`. `help` lists the topics:

```
all, model3411, help, misc, files, mem, rtems, monitor
```

### Gotcha: the pager eats your next keystroke

Long output pauses with `Press any key to continue...`, and the key that
dismisses it is **consumed** — it does not reach the command line. Scripted
sessions that keep writing will lose the first character of the next command
and get a confusing error:

```
SHLL [/] # pversion
pversion: command not found          ← "appversion" lost its leading "a"
```

Send a single space to dismiss the pager before sending anything else.
`scripts/mcci3411.py` handles this automatically; a naive `screen`/`pyserial`
loop does not.

## The `model3411` command set

Verbatim from `help model3411` on application firmware v2.0.0 (the shell
truncates command names in the help listing to 12 characters; the full names
are in the usage text):

```
setdebugflag - setdebugflag object_name_pattern clear_debug_flag set_debug_flag
setvidpid    - setvidpid compliance_vendor_id compliance_product_id
setdevicemod - setdevicemode [0=compliance|1=loopback|2=multi-bulk]
getdevicemod - getdevicemode
setdevicespe - setdevicespeed [0=no speed change, 1=FS, 2=HS, 3=SS G1, 4=SS G2]
            [disconnect delay] [connect delay]
getdevicespe - getdevicespeed
setbuffersiz - setbuffersize [0=bulk|1=interrupt|2=iso] buffer_size_in_hex
getbuffersiz - getbuffersize
controlssc   - controlssc [0=disable|1=enable]
appversion   - appversion
getserialnum - getserialnum
```

Every getter also works as a bare read: `controlssc` with no argument reports
`UsbPhy SSC enabled` rather than changing anything.

### Device mode

| Mode | `setdevicemode` | Data-port VID:PID | Use |
|---|---|---|---|
| USB-IF compliance | `0` | `040e:f644` | USB4CV / XHCICV compliance runs; behaves like a Microsoft SuperMUTT |
| Loopback | `1` | `040e:f645` | Throughput benchmarks and data-integrity tests |
| Multi-bulk | `2` | `040e:020c` | Concurrent multi-stream stress |

```
SHLL [/] # setdevicemode 0
Setting compliance device mode
*Model3411AppI_SetDeviceModeCallback: setting device mode from 1 to 0
```

**A mode change does not take effect until the USB-C cable is disconnected and
reconnected.** If USB4CV or XHCICV refuses to recognize the device, check
`getdevicemode` first — compliance tools only accept mode 0.

MCCI's knowledge base also documents a UASP mode (`3`, `040e:020d`) for storage
benchmarking. Firmware v2.0.0's own help lists only modes 0–2, so treat UASP as
firmware-dependent and confirm with `help model3411` on the board in front of
you rather than assuming.

`setvidpid` overrides the VID/PID advertised in **compliance** mode, which is
what you use to impersonate a specific device for a compliance scenario.

### Device speed

`setdevicespeed <code> [disconnect_delay] [connect_delay]` forces the data port
to enumerate at a chosen speed — the way to test how a host behaves when the
same device appears at Gen2, Gen1, high speed, or full speed. The two optional
delays control the simulated unplug/replug that applies the change.

```
SHLL [/] # getdevicespeed
Current device speed is super G1
```

Codes: `0` no change, `1` full speed, `2` high speed, `3` SuperSpeed Gen1,
`4` SuperSpeed Gen2.

`controlssc 0|1` disables or enables spread-spectrum clocking on the USB PHY —
useful when chasing signal-integrity or EMC behaviour.

### Buffer sizes

`getbuffersize` reports the device-side endpoint buffers **in hex**:

```
Bulk endpoint buffer size 100000          (0x100000 = 1048576 bytes)
Interrupt endpoint buffer size 4000       (0x4000   = 16384 bytes)
Isochronous endpoint buffer size 180000   (0x180000 = 1572864 bytes)
```

`setbuffersize <0|1|2> <hex>` changes them. The host-side test tool's `-b`
argument **must match** the value reported here, or transfers will fail or
report nonsense throughput.

## Helper script

`scripts/mcci3411.py` wraps all of the above: channel-B autodetection, pager
handling, prompt-synchronised reads, and command echo stripping.

```bash
uv run --with pyserial python3 scripts/mcci3411.py ports
uv run --with pyserial python3 scripts/mcci3411.py info
uv run --with pyserial python3 scripts/mcci3411.py mode
uv run --with pyserial python3 scripts/mcci3411.py mode loopback
uv run --with pyserial python3 scripts/mcci3411.py speed ss-g2 1000 1000
uv run --with pyserial python3 scripts/mcci3411.py shell getbuffersize
uv run --with pyserial python3 scripts/mcci3411.py shell 'setvidpid 040e f644'
```

`info` prints firmware version, serial number, mode, speed, buffer sizes, and
SSC state in one pass — run it first in any session so the rest of the work is
grounded in what the board is actually configured to do.

Use `-p/--port` to pin a specific node when more than one FT2232H is attached.
Import it as a module for automation:

```python
from mcci3411 import Mcci3411
with Mcci3411() as dev:
    dev.command("setdevicemode 1")
```

## Running actual throughput tests

Mode switching is only the setup step; the measurement happens on the **system
under test**, over the USB-C port, with MCCI's `usbiotest` CLI (Linux and
Windows; no driver required) or the `USBIOEx` Windows GUI.

Read `references/usbiotest.md` for the pipe notation, the endpoint map, buffer
sizing, and worked invocations.

The short version, for a bulk throughput benchmark against a device in loopback
mode:

```bash
sudo ./usbiotest -i 0/0/1/0 -o 0/0/1/1 -N 100 -T benchmark \
  -b 1048576 -F 100 040e:f645
```

## Other on-board hardware

The board carries a 64x48 OLED (mode and enumeration-speed readout), an
accelerometer used to rotate that display, a thermal sensor, and a high-side
power monitor reporting Vbus voltage and device power draw. These sit on I2C
buses reachable from the shell via `i2cdetect`/`i2cget`. Enumerate before you
poke: the display and sensors share those buses with running firmware, so
prefer reads, and do not `i2cset` unless you know the target register.

## Troubleshooting

- **Serial port opens but nothing echoes.** You are on channel A (JTAG). Use
  the second node — `…1` on macOS, `/dev/ttyUSB1` on Linux.
- **`command not found` for a command you know exists.** The pager ate the
  first character. Send a space, then re-send the command.
- **Compliance tools do not see the device.** `getdevicemode` must report
  `compliance`; after `setdevicemode 0`, replug the USB-C cable.
- **No `040e:*` device anywhere.** The USB-C cable is not connected, or is a
  charge-only cable. The control port alone will never show `040e`.
- **Device enumerates at the wrong speed.** Check `getdevicespeed` — a previous
  session may have pinned it with `setdevicespeed`. `setdevicespeed 0` leaves
  the current speed alone; pick an explicit code to change it.
- **Only one serial node appears.** Something has claimed channel A (a JTAG or
  `ftdi_sio` binding). The shell is still on the remaining node.

## Sources

- [Model 3411 product page](https://mcci.com/usb/dev-tools/model-3411/)
- [Model 3411 Gen2 Loopback datasheet (PDF)](https://mcci.com/wp-content/uploads/2022/06/971001060c_Model-3411-Gen2-Loopback-Datasheet.pdf)
- [MCCI Mode Switch guide (PDF)](https://usb.org/sites/default/files/MCCI%203411%20-%20Mode%20Switch.pdf)
- [MCCI KB: Model 3411 loopback applications](https://portal.mcci.com/portal/en/kb/articles/mcci-model-3411-loopback-applications)

Command output quoted in this skill was captured from a Model 3411 running
application firmware v2.0.0.
