# Copyright 2026 Curtis Galloway
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Drives CDC bulk endpoints for the KB2040 traffic generator.

Run alongside code.py on the KB2040. Three behaviors run concurrently:

  Echo thread    — reads the binary echo stream from the device's data port
                   and writes it straight back. Satisfies code.py's CDC echo
                   patterns and produces correlated IN+OUT bulk pairs in the
                   capture.

  Console thread — reads pattern markers from the device's console port and
                   feeds them to ProbeGate. The gate closes during patterns
                   that verify their own echo (cdc-large / -small / -patterns
                   / mixed-all) and opens during cdc-receive and HID-only
                   patterns. Without the gate, probes interleaved into an
                   echo round-trip corrupt the device's read-back check.

  Probe thread   — sends a 16-byte burst every 500 ms when the gate is open.
                   Bursts fire during cdc-receive (consumed by the device)
                   and during HID-only patterns (pile up in the device's
                   input buffer for later draining). Produces pure host-
                   initiated bulk OUT.

Usage:
  uv run host_exerciser.py \\
      [--port DATA] [--console-port CONSOLE] [--start] [--list]

--start  Sends 'start\\n' to the device after opening the port, so you can
         kick off a full capture session without touching the board.
"""

# /// script
# dependencies = ["pyserial"]
# ///

import argparse
import sys
import threading
import time

import serial
import serial.tools.list_ports

BAUD = 115200
ADAFRUIT_VID = 0x239A
PROBE_INTERVAL = 0.5  # seconds between probe bursts
PROBE_PAYLOAD = bytes([0xCA, 0xFE, 0xBA, 0xBE] * 4)  # 16-byte recognisable marker


class ProbeGate:
    """Suppresses probe bursts while the device runs a pattern that verifies its
    own echo. The echo thread feeds inbound bytes through update(); when a known
    pattern marker is seen, the gate opens or closes accordingly. Probes
    interleaved with cdc-large/small/patterns/mixed-all would otherwise corrupt
    the device's echo comparison.
    """

    # Patterns where the device writes a payload and then reads it back —
    # probes injected into that window corrupt the echo check.
    _CLOSE = (b"[cdc-large]", b"[cdc-small]", b"[cdc-patterns]", b"[mixed-all]")
    # Everything else: device either wants probes (cdc-receive) or isn't
    # touching CDC at all (HID patterns, idle, cycle boundaries).
    _OPEN = (
        b"[cdc-receive]",
        b"[kbd-",
        b"[mouse-",
        b"[consumer-",
        b"[mixed-hid]",
        b"[reconnect]",
        b"--- start ---",
        b"--- stopped ---",
        b"--- all patterns complete ---",
    )

    def __init__(self) -> None:
        self.event = threading.Event()
        self.event.set()  # default open: idle state allows probes
        self._buf = b""

    def update(self, chunk: bytes) -> None:
        # Rolling buffer keeps markers detectable across read boundaries.
        self._buf = (self._buf + chunk)[-128:]
        while True:
            best_idx = -1
            best_marker = b""
            best_open = False
            for markers, open_state in (
                (self._CLOSE, False),
                (self._OPEN, True),
            ):
                for m in markers:
                    idx = self._buf.find(m)
                    if idx != -1 and (best_idx == -1 or idx < best_idx):
                        best_idx, best_marker, best_open = idx, m, open_state
            if best_idx == -1:
                return
            label = best_marker.decode(errors="replace")
            if best_open and not self.event.is_set():
                self.event.set()
                print(f"{ts()}  gate OPEN   {label!r}")
            elif not best_open and self.event.is_set():
                self.event.clear()
                print(f"{ts()}  gate CLOSE  {label!r}")
            self._buf = self._buf[best_idx + len(best_marker) :]

    def force_open(self) -> None:
        """Release any waiters — used during shutdown."""
        self.event.set()


def find_kb2040_ports():
    """Return (console_port, data_port) paths for the KB2040, or (None, None)."""
    ports = sorted(
        [p for p in serial.tools.list_ports.comports() if p.vid == ADAFRUIT_VID],
        key=lambda p: p.device,
    )
    if len(ports) < 2:
        return None, None
    return ports[0].device, ports[1].device  # index 0 = console/REPL, 1 = data


def ts():
    return f"{time.monotonic():10.3f}"


def echo_thread(ser: serial.Serial, stop: threading.Event) -> None:
    """Read echo-protocol data from device; echo back immediately; log to stdout.
    Pattern markers no longer travel on this port — they come in via console_thread.
    """
    while not stop.is_set():
        try:
            waiting = ser.in_waiting
            if waiting:
                data = ser.read(waiting)
                ser.write(data)
                _log_transfer("dev→host", data)
            else:
                time.sleep(0.002)
        except (serial.SerialException, OSError):
            break  # port closed or device disappeared (e.g. [reconnect] reset)


def console_thread(ser: serial.Serial, stop: threading.Event, gate: ProbeGate) -> None:
    """Read pattern markers from the device's console (REPL) port and feed the gate."""
    while not stop.is_set():
        try:
            waiting = ser.in_waiting
            if waiting:
                data = ser.read(waiting)
                gate.update(data)
                _log_transfer("console ", data)
            else:
                time.sleep(0.01)
        except (serial.SerialException, OSError):
            break  # port closed or device disappeared (e.g. [reconnect] reset)


def probe_thread(ser: serial.Serial, stop: threading.Event, gate: ProbeGate) -> None:
    """Send periodic probe bursts — host-initiated bulk OUT independent of device.
    Holds while the gate is closed (device running an echo-verifying pattern).
    """
    seq = 0
    while not stop.is_set():
        gate.event.wait()  # block when gate is closed
        if stop.is_set():
            break
        try:
            payload = bytes([seq & 0xFF]) + PROBE_PAYLOAD[1:]
            ser.write(payload)
            print(f"{ts()}  host→dev  {len(payload):4d}B  probe seq={seq & 0xFF:#04x}")
        except (serial.SerialException, OSError):
            break  # port closed or device disappeared (e.g. [reconnect] reset)
        seq += 1
        if stop.wait(PROBE_INTERVAL):  # interruptible sleep
            break


def _log_transfer(direction: str, data: bytes) -> None:
    is_printable = all(0x20 <= b < 0x7F or b in (0x09, 0x0A, 0x0D) for b in data)
    if is_printable:
        text = data.decode("utf-8", errors="replace").rstrip("\r\n")
        print(f"{ts()}  {direction}  {len(data):4d}B  {text!r}")
    else:
        tail = "..." if len(data) > 16 else ""
        print(f"{ts()}  {direction}  {len(data):4d}B  {data[:16].hex()}{tail}")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="KB2040 CDC bulk exerciser — echo + periodic probe"
    )
    ap.add_argument("--port", help="Data-port path (auto-detected if omitted)")
    ap.add_argument(
        "--console-port", help="Console-port path (auto-detected if omitted)"
    )
    ap.add_argument(
        "--start",
        action="store_true",
        help="Send 'start' command to trigger device pattern cycle",
    )
    ap.add_argument(
        "--list",
        action="store_true",
        help="List candidate serial ports and exit",
    )
    args = ap.parse_args()

    if args.list:
        print("Available serial ports:")
        for p in serial.tools.list_ports.comports():
            vid = f"{p.vid:#06x}" if p.vid is not None else "  n/a "
            print(f"  {p.device:<30}  VID={vid}  {p.description}")
        return

    auto_console, auto_data = find_kb2040_ports()
    data_port = args.port or auto_data
    console_port = args.console_port or auto_console
    if not data_port:
        print("KB2040 data port not found.")
        print("Check USB connection, or use --port to specify manually.")
        print("Use --list to see all available ports.")
        sys.exit(1)

    def _open(path: str, label: str) -> serial.Serial:
        print(f"Opening {label} {path} at {BAUD} baud")
        try:
            return serial.Serial(path, BAUD, timeout=0.05)
        except serial.SerialException as e:
            print(f"Could not open {path}: {e}", file=sys.stderr)
            if "Permission denied" in str(e):
                print(
                    "Hint: on Linux, /dev/ttyACM* is owned by group "
                    "'dialout'. Add yourself with:  "
                    "sudo usermod -aG dialout $USER  (then log out/in).",
                    file=sys.stderr,
                )
            sys.exit(1)

    ser = _open(data_port, "data   ")
    ser_log = _open(console_port, "console") if console_port else None
    if ser_log is None:
        print(
            "Console port not found — probe gating disabled, "
            "probes will fire continuously.",
            file=sys.stderr,
        )
    time.sleep(0.3)  # give device time to see DTR assert

    stop = threading.Event()
    gate = ProbeGate()
    threads = [
        threading.Thread(target=echo_thread, args=(ser, stop), daemon=True),
        threading.Thread(target=probe_thread, args=(ser, stop, gate), daemon=True),
    ]
    if ser_log is not None:
        threads.append(
            threading.Thread(
                target=console_thread, args=(ser_log, stop, gate), daemon=True
            )
        )
    for t in threads:
        t.start()

    if args.start:
        time.sleep(0.1)
        ser.write(b"start\n")
        print(f"{ts()}  host→dev     7B  'start\\n'  (triggering device cycle)")

    print("Running. Ctrl+C to stop.\n")
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print(f"\n{ts()}  stopping")
        stop.set()
        gate.force_open()  # release probe_thread if it's blocked on the gate
        for t in threads:
            t.join(timeout=2)
        ser.close()
        if ser_log is not None:
            ser_log.close()


if __name__ == "__main__":
    main()
