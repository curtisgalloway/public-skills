#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
# /// script
# requires-python = ">=3.9"
# dependencies = ["pyserial"]
# ///
"""Read and control a FNIRSI DPS-150 bench supply over its USB serial port.

Exit status:
  0   success
  2   usage error, or more than one candidate port
  3   precondition missing: pyserial, wrong device, a live output request
      above the supply's present upper limit, or a limit or setpoint that
      cannot be checked because it is not a finite number
  4   supply unreachable: no port, port busy, or no handshake
  21  a write landed but read back differently; check the state
  22  a write went out and no status came back; check the state first
"""

import argparse
import json
import math
import pathlib
import struct
import sys
import time

VERSION = "1.0.0"

USB_VID = 0x2E3C
USB_PID = 0x5740
BAUD = 9600

RX = 0xF0
TX = 0xF1
START_GET = 0xA1
START_SET = 0xB1

CMD_SET_VOLTS = 0xC1
CMD_SET_AMPS = 0xC2
CMD_OUTPUT = 0xDB
CMD_MODEL = 0xDE
CMD_VERSION_DF = 0xDF
CMD_VERSION_E0 = 0xE0
CMD_READY = 0xE1
CMD_STATUS = 0xFF

SESSION_OPEN = bytes.fromhex("f1c100010102")
SESSION_CLOSE = bytes.fromhex("f1c100010001")
SESSION_MAGIC = bytes.fromhex("f1b000010101")

MAX_VOLTS = 30.0
MAX_AMPS = 5.1
READBACK_TOLERANCE = 0.01
STATUS_LENGTH = 139
MAX_TEXT_LENGTH = 64

PROTECTION = ("none", "OVP", "OCP", "OPP", "OTP", "LVP", "REP")


class ToolError(Exception):
    """A failure that maps to a documented exit status."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def frame(start, cmd, payload):
    """Builds a host-to-device frame."""
    body = bytes([cmd, len(payload)]) + payload
    return bytes([TX, start]) + body + bytes([sum(body) & 0xFF])


def query(cmd):
    """Builds a read request for one command ID."""
    return frame(START_GET, cmd, b"\x00")


def parse_frames(buf):
    """Splits a byte stream into checked frames.

    Returns:
      A list of (cmd, payload) tuples and the unconsumed tail of buf.
    """
    frames = []
    i = 0
    while i < len(buf):
        if buf[i] != RX:
            i += 1
            continue
        if i + 4 > len(buf):
            break
        cmd, length = buf[i + 2], buf[i + 3]
        end = i + 4 + length
        if end >= len(buf):
            break
        payload = bytes(buf[i + 4 : end])
        if (cmd + length + sum(payload)) & 0xFF == buf[end]:
            frames.append((cmd, payload))
            i = end + 1
        else:
            i += 1
    return frames, bytes(buf[i:])


def printable_text(payload):
    """Decodes a device string for display: printable ASCII, bounded length.

    The bytes come from the device, and doctor prints them, so a control byte
    must not reach the terminal. Every other byte becomes "?".
    """
    text = payload[:MAX_TEXT_LENGTH].decode("ascii", "replace")
    return "".join(ch if " " <= ch <= "~" else "?" for ch in text)


def decode_status(data):
    """Decodes a full-status payload into named fields."""
    if len(data) != STATUS_LENGTH:
        raise ToolError(22, f"status payload is {len(data)} bytes")

    def f32(offset):
        value = struct.unpack_from("<f", data, offset)[0]
        return round(value, 3)

    protection = data[108]
    return {
        "input_v": f32(0),
        "set_v": f32(4),
        "set_a": f32(8),
        "output_v": f32(12),
        "output_a": f32(16),
        "output_w": f32(20),
        "temperature_c": f32(24),
        "ovp_v": f32(76),
        "ocp_a": f32(80),
        "opp_w": f32(84),
        "otp_c": f32(88),
        "lvp_v": f32(92),
        "capacity_ah": f32(99),
        "energy_wh": f32(103),
        "output_on": data[107] == 1,
        "protection": (
            PROTECTION[protection]
            if protection < len(PROTECTION)
            else f"unknown({protection})"
        ),
        "mode": "CV" if data[109] == 1 else "CC",
        "upper_limit_v": f32(111),
        "upper_limit_a": f32(115),
    }


class Session:
    """One handshaken conversation with the supply; ends it on exit."""

    def __init__(self, port):
        self.port = port
        self.buffer = b""

    def __enter__(self):
        self.port.write(SESSION_OPEN)
        time.sleep(0.2)
        for _ in range(10):
            self.port.write(query(CMD_READY))
            ready = self.wait_for(CMD_READY, 0.1)
            if ready is not None and ready[:1] == b"\x01":
                self.port.write(SESSION_MAGIC)
                time.sleep(0.2)
                return self
        self.close()
        raise ToolError(4, "no handshake reply; is this a DPS-150?")

    def __exit__(self, *_):
        self.close()

    def close(self):
        """Ends the session and releases the port."""
        self.port.write(SESSION_CLOSE)
        time.sleep(0.2)
        self.port.close()

    def wait_for(self, cmd, timeout):
        """Returns the payload of the next cmd frame, or None on timeout."""
        deadline = time.monotonic() + timeout
        while True:
            frames, self.buffer = parse_frames(self.buffer)
            for got, payload in frames:
                if got == cmd:
                    return payload
            if time.monotonic() >= deadline:
                return None
            self.buffer += self.port.read(max(1, self.port.in_waiting))

    def ask(self, cmd, timeout=1.0):
        """Sends a read and returns its payload, or None on timeout."""
        self.buffer = b""
        self.port.reset_input_buffer()
        self.port.write(query(cmd))
        return self.wait_for(cmd, timeout)

    def text(self, cmd):
        """Reads an ASCII field made safe to print, or None on timeout."""
        payload = self.ask(cmd)
        return None if payload is None else printable_text(payload)

    def status(self):
        """Reads and decodes the full status."""
        payload = self.ask(CMD_STATUS)
        if payload is None:
            raise ToolError(22, "no status reply")
        return decode_status(payload)

    def require_model(self):
        """Returns the model name, refusing anything but a DPS-150."""
        model = self.text(CMD_MODEL)
        if model is None or not model.startswith("DPS-150"):
            raise ToolError(3, f"device reports model {model!r}, not DPS-150")
        return model

    def write(self, cmd, payload):
        """Sends a write and allows the supply time to apply it."""
        self.port.write(frame(START_SET, cmd, payload))
        time.sleep(0.4)


def find_port():
    """Returns the single USB port with the supply's IDs."""
    list_ports = load_serial().tools.list_ports
    ports = sorted(
        p.device for p in list_ports.comports() if p.vid == USB_VID and p.pid == USB_PID
    )
    if not ports:
        raise ToolError(4, "no port with USB ID 2e3c:5740; is the supply on?")
    if len(ports) > 1:
        raise ToolError(2, f"several candidates, choose with --port: {ports}")
    return ports[0]


def load_serial():
    """Imports pyserial on first use, so tests run without it."""
    try:
        import serial  # pylint: disable=import-outside-toplevel
        import serial.tools.list_ports  # pylint: disable=import-outside-toplevel
    except ImportError as err:
        raise ToolError(3, "pyserial missing; run with `uv run`") from err
    return serial


def open_port(path):
    """Opens the port with DTR off and RTS on, as the supply expects."""
    serial = load_serial()
    port = serial.Serial()
    port.port = path or find_port()
    port.baudrate = BAUD
    port.timeout = 0.1
    port.dtr = False
    port.rts = True
    try:
        port.open()
    except serial.SerialException as err:
        raise ToolError(4, f"cannot open {port.port}: {err}") from err
    return port


def close_enough(actual, wanted):
    """Compares a readback with the value written."""
    return abs(actual - wanted) <= READBACK_TOLERANCE


def check_limits(status, volts, amps):
    """Refuses requests above what the present input can deliver.

    Fails closed. NaN compares False with everything, so a value that is not
    a finite number is refused here rather than passing the comparisons below.
    """
    for name in ("upper_limit_v", "upper_limit_a"):
        if not math.isfinite(status[name]) or status[name] < 0:
            raise ToolError(
                3, f"cannot check the request: device reports {name} {status[name]}"
            )
    for value, unit in ((volts, "V"), (amps, "A")):
        if value is not None and not math.isfinite(value):
            raise ToolError(3, f"cannot check the request: setpoint is {value} {unit}")
    if volts is not None and volts > status["upper_limit_v"]:
        raise ToolError(
            3,
            f"{volts} V is above the upper limit {status['upper_limit_v']} V; "
            f"the input is {status['input_v']} V, so check the USB-C source",
        )
    if amps is not None and amps > status["upper_limit_a"]:
        raise ToolError(
            3, f"{amps} A is above the upper limit {status['upper_limit_a']} A"
        )


def do_set(session, volts, amps):
    """Writes setpoints, checks them, and returns the status read back."""
    before = session.status()
    if before["output_on"]:
        check_limits(before, volts, amps)
        print("warning: output is on; this changes it live", file=sys.stderr)
    if amps is not None:
        session.write(CMD_SET_AMPS, struct.pack("<f", amps))
    if volts is not None:
        session.write(CMD_SET_VOLTS, struct.pack("<f", volts))
    after = session.status()
    if volts is not None and not close_enough(after["set_v"], volts):
        raise ToolError(21, f"voltage reads back as {after['set_v']}")
    if amps is not None and not close_enough(after["set_a"], amps):
        raise ToolError(21, f"current reads back as {after['set_a']}")
    return after


def do_output(session, turn_on):
    """Switches the output, checks the state, and returns the status."""
    before = session.status()
    if turn_on:
        check_limits(before, before["set_v"], before["set_a"])
    session.write(CMD_OUTPUT, b"\x01" if turn_on else b"\x00")
    after = session.status()
    if after["output_on"] != turn_on:
        raise ToolError(21, f"output_on reads back as {after['output_on']}")
    return after


def emit(args, status):
    """Prints a status as JSON or as key: value lines."""
    if args.json:
        print(json.dumps(status, sort_keys=True))
        return
    for key in sorted(status):
        print(f"{key}: {status[key]}")


def cmd_status(args):
    """Prints the full status."""
    with Session(open_port(args.port)) as session:
        session.require_model()
        emit(args, session.status())


def cmd_set(args):
    """Writes the requested setpoints."""
    if args.volts is None and args.amps is None:
        raise ToolError(2, "give --volts, --amps, or both")
    if args.volts is not None and not 0 <= args.volts <= MAX_VOLTS:
        raise ToolError(2, f"--volts must be 0 to {MAX_VOLTS}")
    if args.amps is not None and not 0 <= args.amps <= MAX_AMPS:
        raise ToolError(2, f"--amps must be 0 to {MAX_AMPS}")
    if args.dry_run:
        for name, value in (("current", args.amps), ("voltage", args.volts)):
            if value is not None:
                print(f"would set {name} to {value}")
        return
    with Session(open_port(args.port)) as session:
        session.require_model()
        emit(args, do_set(session, args.volts, args.amps))


def cmd_output(args):
    """Turns the output on or off."""
    turn_on = args.state == "on"
    if args.dry_run:
        print(f"would turn output {args.state}")
        return
    if turn_on and not args.yes:
        raise ToolError(2, "output on energizes the terminals; pass --yes")
    with Session(open_port(args.port)) as session:
        session.require_model()
        emit(args, do_output(session, turn_on))
    if turn_on:
        print("note: output stays on after this tool exits", file=sys.stderr)


def cmd_doctor(args):
    """Reports each precondition as it passes."""
    load_serial()
    print("pyserial: ok")
    with Session(open_port(args.port)) as session:
        print("handshake: ok")
        print(f"model: {session.require_model()}")
        print(f"version 0xDF: {session.text(CMD_VERSION_DF)}")
        print(f"version 0xE0: {session.text(CMD_VERSION_E0)}")
        status = session.status()
    print(f"input: {status['input_v']} V")
    print(f"upper limit: {status['upper_limit_v']} V")
    print(f"output: {'on' if status['output_on'] else 'off'}")


def build_parser():
    """Builds the command-line parser."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=VERSION)
    parser.add_argument("--skill", action="store_true", help="print SKILL.md")
    parser.add_argument("--port", help="serial port; found by USB ID if omitted")
    parser.add_argument("--json", action="store_true", help="print one JSON object")
    commands = parser.add_subparsers(dest="command")

    status = commands.add_parser("status", help="read everything; changes nothing")
    status.set_defaults(run=cmd_status)

    doctor = commands.add_parser("doctor", help="check the link and report versions")
    doctor.set_defaults(run=cmd_doctor)

    setter = commands.add_parser("set", help="write voltage and current setpoints")
    setter.add_argument("--volts", type=float)
    setter.add_argument("--amps", type=float)
    setter.add_argument("--dry-run", action="store_true")
    setter.set_defaults(run=cmd_set)

    output = commands.add_parser("output", help="turn the output on or off")
    output.add_argument("state", choices=("on", "off"))
    output.add_argument("--yes", action="store_true", help="confirm turning it on")
    output.add_argument("--dry-run", action="store_true")
    output.set_defaults(run=cmd_output)
    return parser


def main(argv=None):
    """Runs the tool and returns its exit status."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.skill:
        skill = pathlib.Path(__file__).resolve().parent.parent / "SKILL.md"
        print(skill.read_text(encoding="utf-8"), end="")
        print(f"\n<!-- dps150.py {VERSION} -->")
        return 0
    if args.command is None:
        parser.print_usage(sys.stderr)
        return 2
    try:
        args.run(args)
    except ToolError as err:
        print(f"error: {err}", file=sys.stderr)
        return err.code
    except OSError as err:
        print(f"error: serial link failed: {err}", file=sys.stderr)
        return 22 if args.command in ("set", "output") else 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
