#!/usr/bin/env python3
# Copyright 2026 contributors
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
"""Headless Cynthion USB Analyzer capture tool.

Writes a standard libpcap file (LINKTYPE_USB_2_0, link type 288).
Compatible with Wireshark and any pcap reader.

Protocol source: packetry src/backend/cynthion.rs
  VID/PID:         0x1d50 / 0x615b
  Analyzer iface:  class=0xFF sub=0x10 proto=0x01
  Bulk IN:         0x81, 16 KiB transfers
  Control req 1:   start/stop  (ControlOut, vendor|interface)
    value byte:    bits[2:1]=speed (0=auto,1=LS,2=FS,3=HS), bit[0]=enable
  Frame format:    [len_be:2][ts_be:2][data:len][pad_if_odd]
  Event frame:     first byte == 0xFF (4-byte header, no payload)
"""

import argparse
import signal
import struct
import sys
import time
import usb.core
import usb.util

VID            = 0x1d50
PID            = 0x615b
BULK_EP_IN     = 0x81
TRANSFER_SIZE  = 0x4000   # 16 KiB, matching Packetry

CTRL_OUT       = 0x41     # Vendor | Interface | Host-to-Device
REQ_CAPTURE    = 1

# Speed field occupies bits[2:1] of the start-request value byte.
# Enum order confirmed empirically: 0=HS-only, 1=FS-only, 2=LS-only, 3=Auto.
# Auto (3) is the correct default — it captures all speeds and works even when
# the device is already enumerated before capture starts.
SPEED_HS, SPEED_FS, SPEED_LS, SPEED_AUTO = 0, 1, 2, 3
SPEEDS = {'auto': SPEED_AUTO, 'hs': SPEED_HS, 'fs': SPEED_FS, 'ls': SPEED_LS}

PCAP_MAGIC     = 0xa1b2c3d4
LINKTYPE_USB20 = 288       # LINKTYPE_USB_2_0


def find_analyzer_interface(dev):
    for cfg in dev:
        for intf in cfg:
            if (intf.bInterfaceClass    == 0xFF
                    and intf.bInterfaceSubClass == 0x10
                    and intf.bInterfaceProtocol == 0x01):
                return intf
    return None


def pcap_global_header(snaplen=65535):
    return struct.pack('<IHHiIII', PCAP_MAGIC, 2, 4, 0, 0, snaplen, LINKTYPE_USB20)


def pcap_record(data, ts):
    ts_sec  = int(ts)
    ts_usec = int((ts - ts_sec) * 1_000_000)
    n = len(data)
    return struct.pack('<IIII', ts_sec, ts_usec, n, n) + data


def send_capture_request(dev, intf_num, value):
    dev.ctrl_transfer(CTRL_OUT, REQ_CAPTURE, value, intf_num, None, timeout=1000)


def parse_frames(buf, out, stats):
    while len(buf) >= 4:
        if buf[0] == 0xFF:
            buf = buf[4:]
            continue
        pkt_len = (buf[0] << 8) | buf[1]
        if pkt_len == 0:
            buf = buf[1:]
            continue
        frame_len = 4 + pkt_len + (pkt_len % 2)
        if len(buf) < frame_len:
            break
        payload = buf[4:4 + pkt_len]
        out.write(pcap_record(payload, time.time()))
        out.flush()
        stats['packets'] += 1
        stats['bytes']   += pkt_len
        buf = buf[frame_len:]
    return buf


def main():
    ap = argparse.ArgumentParser(
        description='Headless Cynthion USB 2.0 capture — writes a libpcap file.')
    ap.add_argument('output',
        help='Output .pcap path')
    ap.add_argument('-d', '--duration', type=float, default=None,
        metavar='SECONDS',
        help='Stop after this many seconds (default: run until Ctrl-C / SIGTERM)')
    ap.add_argument('-s', '--speed', choices=SPEEDS.keys(), default='auto',
        help='USB speed filter (default: auto)')
    args = ap.parse_args()

    dev = usb.core.find(idVendor=VID, idProduct=PID)
    if dev is None:
        print('ERROR: No Cynthion USB Analyzer found.\n'
              '  Check CONTROL port cable and run: cynthion run analyzer',
              file=sys.stderr)
        sys.exit(1)

    intf = find_analyzer_interface(dev)
    if intf is None:
        print('ERROR: Analyzer interface (class FF/10/01) not found on device.',
              file=sys.stderr)
        sys.exit(1)

    intf_num = intf.bInterfaceNumber

    try:
        if dev.is_kernel_driver_active(intf_num):
            dev.detach_kernel_driver(intf_num)
    except usb.core.USBError:
        pass

    usb.util.claim_interface(dev, intf_num)

    speed_code = SPEEDS[args.speed]
    ctrl_start = (speed_code << 1) | 1   # speed[2:1] | enable[0]

    running = True

    def _stop(sig, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT,  _stop)
    signal.signal(signal.SIGTERM, _stop)

    stats = {'packets': 0, 'bytes': 0}
    buf   = b''

    try:
        with open(args.output, 'wb') as f:
            f.write(pcap_global_header())
            send_capture_request(dev, intf_num, ctrl_start)
            deadline = (time.time() + args.duration) if args.duration else None
            print(f'Capturing ({args.speed} speed) → {args.output}'
                  + (f' for {args.duration}s' if args.duration else ' until Ctrl-C'),
                  flush=True)

            while running:
                if deadline and time.time() >= deadline:
                    break
                try:
                    chunk = bytes(dev.read(BULK_EP_IN, TRANSFER_SIZE, timeout=500))
                    buf  += chunk
                    buf   = parse_frames(buf, f, stats)
                except usb.core.USBTimeoutError:
                    pass

    finally:
        try:
            send_capture_request(dev, intf_num, 0)
        except Exception:
            pass
        usb.util.release_interface(dev, intf_num)

    print(f'Done: {stats["packets"]} packets, {stats["bytes"]} bytes → {args.output}')


if __name__ == '__main__':
    main()
