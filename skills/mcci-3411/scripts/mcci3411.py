#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0

"""Drive an MCCI Model 3411 USB 3.2 Gen2 test device over its control port.

The 3411's micro-B control port is an FTDI FT2232H (0403:6010).  Channel A is
JTAG/MPSSE and stays silent; channel B is an RTEMS shell at 115200 8N1 whose
prompt is ``SHLL [/] # ``.  This module finds channel B, runs shell commands,
and copes with the shell's pager, which silently eats the first character of
whatever you send next.

Usage:
    python3 mcci3411.py ports              # list candidate control ports
    python3 mcci3411.py info               # firmware, serial, mode, speed, …
    python3 mcci3411.py mode               # getdevicemode
    python3 mcci3411.py mode loopback      # setdevicemode 1
    python3 mcci3411.py shell getbuffersize
    python3 mcci3411.py shell 'setdevicespeed 4 1000 1000'

Requires pyserial:
    uv run --with pyserial python3 mcci3411.py info
"""

import argparse
import sys
import time

import serial
from serial.tools import list_ports

FTDI_VID = 0x0403
FT2232H_PID = 0x6010

BAUD = 115200
PROMPT = "SHLL [/] #"
PAGER = "Press any key to continue..."

# setdevicemode arguments, as reported by `help model3411` on firmware v2.0.0.
MODES = {"compliance": 0, "loopback": 1, "multi-bulk": 2}

# setdevicespeed arguments.
SPEEDS = {"nochange": 0, "fs": 1, "hs": 2, "ss-g1": 3, "ss-g2": 4}

# Read-only commands run by `info`, in display order.
INFO_COMMANDS = (
    "appversion",
    "getserialnum",
    "getdevicemode",
    "getdevicespeed",
    "getbuffersize",
    "controlssc",
)


class Mcci3411Error(Exception):
    """Raised when the control port cannot be found or does not respond."""


def candidate_ports():
    """Return FT2232H channel-B device paths, one per attached FT2232H.

    Both channels of an FT2232H report the same USB serial number, so group by
    serial and take the second path in sorted order: ``…A1`` on macOS,
    ``/dev/ttyUSB1`` on Linux.  Channel A is the JTAG interface and never
    answers.
    """
    by_serial = {}
    for port in list_ports.comports():
        if port.vid == FTDI_VID and port.pid == FT2232H_PID:
            by_serial.setdefault(port.serial_number, []).append(port.device)

    channel_b = []
    for _, devices in sorted(by_serial.items(), key=lambda kv: str(kv[0])):
        devices.sort()
        if len(devices) >= 2:
            channel_b.append(devices[1])
        else:
            # Only one node exposed (e.g. channel A bound to a JTAG driver).
            channel_b.extend(devices)
    return channel_b


class Mcci3411:
    """A connection to the Model 3411 shell on the control port."""

    def __init__(self, port=None, timeout=5.0):
        if port is None:
            ports = candidate_ports()
            if not ports:
                raise Mcci3411Error(
                    "No FTDI FT2232H (0403:6010) control port found. Check the "
                    "micro-B cable; note the 3411's USB-C data port has a "
                    "different VID/PID and is not this port."
                )
            port = ports[0]
        self.port = port
        self._timeout = timeout
        self._ser = serial.Serial(port, BAUD, timeout=0.2)
        time.sleep(0.2)
        self._ser.reset_input_buffer()

    def close(self):
        self._ser.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()

    def command(self, cmd):
        """Run one shell command and return its output without the prompt."""
        self._ser.reset_input_buffer()
        self._ser.write(cmd.encode() + b"\r")

        buf = ""
        deadline = time.monotonic() + self._timeout
        while time.monotonic() < deadline:
            chunk = self._ser.read(4096)
            if chunk:
                buf += chunk.decode("utf-8", "replace")
            if PAGER in buf:
                # Advance the pager. It consumes exactly one character, so
                # send a space rather than letting it swallow real input.
                buf = buf.replace(PAGER, "")
                self._ser.write(b" ")
                deadline = time.monotonic() + self._timeout
                continue
            if buf.rstrip().endswith(PROMPT):
                break
        else:
            raise Mcci3411Error(
                f"No prompt from {self.port} within {self._timeout}s. "
                f"Is this FT2232H channel B? Got: {buf[-200:]!r}"
            )
        return _strip(buf, cmd)


def _strip(raw, cmd):
    """Remove the shell's command echo and trailing prompt from a response."""
    text = raw.rstrip()
    if text.endswith(PROMPT):
        text = text[: -len(PROMPT)].rstrip()
    lines = text.splitlines()
    if lines and lines[0].strip() == cmd.strip():
        lines = lines[1:]
    return "\n".join(lines).strip()


def _cmd_ports(_args):
    ports = candidate_ports()
    if not ports:
        print("No FT2232H control port found.", file=sys.stderr)
        return 1
    for port in ports:
        print(port)
    return 0


def _cmd_info(args):
    with Mcci3411(args.port) as dev:
        print(f"control port: {dev.port}")
        for cmd in INFO_COMMANDS:
            out = dev.command(cmd)
            print(f"\n$ {cmd}\n{out}")
    return 0


def _cmd_mode(args):
    with Mcci3411(args.port) as dev:
        if args.value is None:
            print(dev.command("getdevicemode"))
            return 0
        code = MODES.get(args.value, args.value)
        print(dev.command(f"setdevicemode {code}"))
        print(
            "\nUnplug and replug the USB-C data cable for the new mode to "
            "take effect.",
            file=sys.stderr,
        )
    return 0


def _cmd_speed(args):
    with Mcci3411(args.port) as dev:
        if args.value is None:
            print(dev.command("getdevicespeed"))
            return 0
        code = SPEEDS.get(args.value, args.value)
        cmd = f"setdevicespeed {code}"
        if args.disconnect_delay is not None:
            cmd += f" {args.disconnect_delay}"
            if args.connect_delay is not None:
                cmd += f" {args.connect_delay}"
        print(dev.command(cmd))
    return 0


def _cmd_shell(args):
    with Mcci3411(args.port) as dev:
        for cmd in args.command:
            print(dev.command(cmd))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("-p", "--port", help="serial port (default: autodetect)")
    sub = ap.add_subparsers(dest="subcommand", required=True)

    sub.add_parser("ports", help="list candidate control ports").set_defaults(
        func=_cmd_ports)
    sub.add_parser("info", help="dump firmware and configuration").set_defaults(
        func=_cmd_info)

    p_mode = sub.add_parser("mode", help="get or set the device mode")
    p_mode.add_argument("value", nargs="?",
                        help=f"one of {', '.join(MODES)} (or a raw number)")
    p_mode.set_defaults(func=_cmd_mode)

    p_speed = sub.add_parser("speed", help="get or set the device speed")
    p_speed.add_argument("value", nargs="?",
                         help=f"one of {', '.join(SPEEDS)} (or a raw number)")
    p_speed.add_argument("disconnect_delay", nargs="?", type=int)
    p_speed.add_argument("connect_delay", nargs="?", type=int)
    p_speed.set_defaults(func=_cmd_speed)

    p_shell = sub.add_parser("shell", help="run raw shell commands")
    p_shell.add_argument("command", nargs="+")
    p_shell.set_defaults(func=_cmd_shell)

    args = ap.parse_args()
    try:
        return args.func(args)
    except Mcci3411Error as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
