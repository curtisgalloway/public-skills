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

# host_exerciser.py — drives CDC bulk endpoints for KB2040 traffic generator
#
# Run alongside code.py on the KB2040.  Two behaviors run concurrently:
#
#   Echo thread   — reads everything the device sends, writes it straight back.
#                   This satisfies the echo reads in code.py's CDC patterns and
#                   produces correlated IN+OUT bulk pairs in the capture.
#
#   Probe thread  — independently sends a 16-byte burst every 500 ms.
#                   These arrive while HID patterns are running (device not
#                   actively reading), so they pile up and get consumed when
#                   pat_cdc_receive runs.  Produces pure host-initiated bulk OUT.
#
# Usage:
#   uv run host_exerciser.py [--port /dev/tty.usbmodem...] [--start] [--list]
#
# --start  Sends 'start\n' to the device after opening the port, so you can
#          kick off a full capture session without touching the board.

# /// script
# dependencies = ["pyserial"]
# ///

import argparse
import sys
import threading
import time

import serial
import serial.tools.list_ports

BAUD           = 115200
ADAFRUIT_VID   = 0x239A
PROBE_INTERVAL = 0.5                            # seconds between probe bursts
PROBE_PAYLOAD  = bytes([0xCA, 0xFE, 0xBA, 0xBE] * 4)   # 16-byte recognisable marker


def find_data_port():
    """Return the path of the KB2040 CDC data port (second port, sorted by name)."""
    ports = sorted(
        [p for p in serial.tools.list_ports.comports() if p.vid == ADAFRUIT_VID],
        key=lambda p: p.device,
    )
    if len(ports) < 2:
        return None
    return ports[1].device   # index 0 = console/REPL, index 1 = data port


def ts():
    return f"{time.monotonic():10.3f}"


def echo_thread(ser: serial.Serial, stop: threading.Event) -> None:
    """Read from device; echo back immediately; log to stdout."""
    while not stop.is_set():
        try:
            waiting = ser.in_waiting
            if waiting:
                data = ser.read(waiting)
                ser.write(data)   # echo
                _log_transfer("dev→host", data)
            else:
                time.sleep(0.002)
        except serial.SerialException:
            break


def probe_thread(ser: serial.Serial, stop: threading.Event) -> None:
    """Send periodic probe bursts — host-initiated bulk OUT independent of device."""
    seq = 0
    while not stop.is_set():
        try:
            payload = bytes([seq & 0xFF]) + PROBE_PAYLOAD[1:]
            ser.write(payload)
            print(f"{ts()}  host→dev  {len(payload):4d}B  probe seq={seq & 0xFF:#04x}")
        except serial.SerialException:
            break
        seq += 1
        time.sleep(PROBE_INTERVAL)


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
    ap.add_argument("--port",  help="Serial port path (auto-detected if omitted)")
    ap.add_argument("--start", action="store_true",
                    help="Send 'start' command to trigger device pattern cycle")
    ap.add_argument("--list",  action="store_true",
                    help="List candidate serial ports and exit")
    args = ap.parse_args()

    if args.list:
        print("Available serial ports:")
        for p in serial.tools.list_ports.comports():
            print(f"  {p.device:<30}  VID={p.vid:#06x}  {p.description}")
        return

    port = args.port or find_data_port()
    if not port:
        print("KB2040 data port not found.")
        print("Check USB connection, or use --port to specify manually.")
        print("Use --list to see all available ports.")
        sys.exit(1)

    print(f"Opening {port} at {BAUD} baud")
    ser = serial.Serial(port, BAUD, timeout=0.05)
    time.sleep(0.3)   # give device time to see DTR assert

    stop = threading.Event()
    threads = [
        threading.Thread(target=echo_thread,  args=(ser, stop), daemon=True),
        threading.Thread(target=probe_thread, args=(ser, stop), daemon=True),
    ]
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
        for t in threads:
            t.join(timeout=2)
        ser.close()


if __name__ == "__main__":
    main()
