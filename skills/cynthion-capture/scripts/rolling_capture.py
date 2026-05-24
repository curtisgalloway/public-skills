#!/usr/bin/env python3
# Copyright 2026 contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Rolling Cynthion USB capture — writes rotating pcap segments with JSON indexes.

Captures USB traffic continuously, rotating to a new pcap file every N seconds
(or after N MB of pcap data). After each rotation, a JSON index is written
alongside the closed segment in a background thread so the capture loop never
stalls. A manifest.json in the output directory accumulates one entry per
segment for quick cross-segment device lookups.

Usage:
    python3 rolling_capture.py <output-dir>
    python3 rolling_capture.py <output-dir> --interval 600 --prefix usb
    python3 rolling_capture.py <output-dir> --interval 300 --max-size 100
    python3 rolling_capture.py <output-dir> --duration 3600 --speed fs

Options:
    output_dir              Directory for capture segments (created if absent)
    --interval N            Rotate after N seconds (default: 300)
    --max-size M            Also rotate after M MB of pcap data (optional)
    --prefix NAME           Filename prefix for segments (default: capture)
    --speed auto|hs|fs|ls   USB speed filter (default: auto)
    --duration N            Stop the whole session after N seconds (optional)
    --no-index              Skip JSON indexing (index later with index_pcap.py)

Output per segment:
    <prefix>_YYYYMMDD_HHMMSS.pcap   raw libpcap (LINKTYPE_USB_2_0)
    <prefix>_YYYYMMDD_HHMMSS.json   per-device index (async, written after rotation)

Session output:
    manifest.json                   index of all segments with device VID/PID
"""

import argparse
import gzip
import json
import os
import signal
import struct
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import usb.core
import usb.util

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _sibling import import_decode  # noqa: E402
import index_pcap  # noqa: E402  (same scripts/ directory)

# ---------------------------------------------------------------------------
# Cynthion hardware constants
# ---------------------------------------------------------------------------

VID            = 0x1d50
PID_DEVICE     = 0x615b
BULK_EP_IN     = 0x81
TRANSFER_SIZE  = 0x4000

CTRL_OUT       = 0x41
REQ_CAPTURE    = 1

SPEED_HS, SPEED_FS, SPEED_LS, SPEED_AUTO = 0, 1, 2, 3
SPEEDS = {"auto": SPEED_AUTO, "hs": SPEED_HS, "fs": SPEED_FS, "ls": SPEED_LS}

PCAP_MAGIC     = 0xa1b2c3d4
LINKTYPE_USB20 = 288
USB_PID_SOF    = 0xA5

# ---------------------------------------------------------------------------
# pcap helpers
# ---------------------------------------------------------------------------

def _pcap_global_header(snaplen: int = 65535) -> bytes:
    return struct.pack("<IHHiIII", PCAP_MAGIC, 2, 4, 0, 0, snaplen, LINKTYPE_USB20)


def _pcap_record(data: bytes, ts: float) -> bytes:
    ts_sec  = int(ts)
    ts_usec = int((ts - ts_sec) * 1_000_000)
    n = len(data)
    return struct.pack("<IIII", ts_sec, ts_usec, n, n) + data


# ---------------------------------------------------------------------------
# Cynthion device helpers
# ---------------------------------------------------------------------------

def _find_analyzer_interface(dev):
    for cfg in dev:
        for intf in cfg:
            if (intf.bInterfaceClass    == 0xFF
                    and intf.bInterfaceSubClass == 0x10
                    and intf.bInterfaceProtocol == 0x01):
                return intf
    return None


def _send_capture_request(dev, intf_num: int, value: int):
    dev.ctrl_transfer(CTRL_OUT, REQ_CAPTURE, value, intf_num, None, timeout=1000)


# ---------------------------------------------------------------------------
# Frame parser
# ---------------------------------------------------------------------------

def _parse_frames(buf: bytes, out, stats: dict) -> bytes:
    """Parse Cynthion bulk-in frames, write pcap records, update stats in-place."""
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
        if payload and payload[0] == USB_PID_SOF:
            stats["sof_dropped"] += 1
            buf = buf[frame_len:]
            continue
        rec = _pcap_record(payload, time.time())
        out.write(rec)
        stats["packets"]    += 1
        stats["bytes"]      += pkt_len
        stats["pcap_bytes"] += len(rec)
        buf = buf[frame_len:]
    return buf


# ---------------------------------------------------------------------------
# Background indexer
# ---------------------------------------------------------------------------

class _IndexWorker:
    """Schedules background indexer threads and serialises manifest writes."""

    def __init__(self, decode, manifest_path: str):
        self._decode        = decode
        self._manifest_path = manifest_path
        self._lock          = threading.Lock()
        self._threads: list[threading.Thread] = []

    def schedule(self, pcap_path: str):
        t = threading.Thread(
            target=self._run, args=(pcap_path,), daemon=True, name="indexer",
        )
        self._threads.append(t)
        t.start()

    def _run(self, pcap_path: str):
        try:
            index = index_pcap.build_index(pcap_path, self._decode)
            index_pcap.write_index(pcap_path, index)
            with self._lock:
                index_pcap.update_manifest(self._manifest_path, pcap_path, index)
        except Exception as exc:
            print(f"\nIndexer warning ({os.path.basename(pcap_path)}): {exc}",
                  file=sys.stderr)

    def join_all(self, timeout: float = 60.0):
        deadline = time.time() + timeout
        for t in self._threads:
            t.join(timeout=max(0.0, deadline - time.time()))


# ---------------------------------------------------------------------------
# Segment manager
# ---------------------------------------------------------------------------

class _SegmentManager:
    """Opens, rotates, and closes pcap segment files."""

    def __init__(self, output_dir: str, prefix: str,
                 interval_s: float, max_size_bytes: int | None,
                 indexer: _IndexWorker | None):
        self._dir        = output_dir
        self._prefix     = prefix
        self._interval   = interval_s
        self._max_size   = max_size_bytes
        self._indexer    = indexer

        self._file       = None
        self._path       = None
        self._seg_start  = 0.0
        self._stats      = {}

        # Running totals across all segments.
        self.total_packets     = 0
        self.total_bytes       = 0
        self.total_sof_dropped = 0

    def _seg_path(self) -> str:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(self._dir, f"{self._prefix}_{stamp}.pcap.gz")

    def _open_new(self):
        path = self._seg_path()
        f = gzip.open(path, "wb", compresslevel=6)
        f.write(_pcap_global_header())
        self._file      = f
        self._path      = path
        self._seg_start = time.time()
        self._stats     = {"packets": 0, "bytes": 0, "pcap_bytes": 24, "sof_dropped": 0}
        print(f"  segment → {os.path.basename(path)}", flush=True)

    def open_first(self):
        self._open_new()

    def write(self, buf: bytes) -> bytes:
        """Parse bulk-in data, write pcap records, update running totals."""
        before_pkts  = self._stats["packets"]
        before_bytes = self._stats["bytes"]
        before_sof   = self._stats["sof_dropped"]
        buf = _parse_frames(buf, self._file, self._stats)
        self._file.flush()
        self.total_packets     += self._stats["packets"]     - before_pkts
        self.total_bytes       += self._stats["bytes"]       - before_bytes
        self.total_sof_dropped += self._stats["sof_dropped"] - before_sof
        return buf

    def should_rotate(self) -> bool:
        if time.time() - self._seg_start >= self._interval:
            return True
        if self._max_size and self._stats["pcap_bytes"] >= self._max_size:
            return True
        return False

    def rotate(self):
        self._close_current()
        self._open_new()

    def close_final(self):
        self._close_current()

    def _close_current(self):
        if self._file is None:
            return
        self._file.flush()
        self._file.close()
        path        = self._path
        self._file  = None
        self._path  = None
        if self._indexer:
            self._indexer.schedule(path)


# ---------------------------------------------------------------------------
# Clock synchronization
# ---------------------------------------------------------------------------

_SYNC_PROBES = 5


def _measure_clock_offset(target_host: str) -> dict | None:
    """SSH to target_host and measure its clock offset vs local.

    Runs _SYNC_PROBES round trips, keeps the one with the smallest RTT
    (minimum-RTT filter, same principle as NTP's clock filter).

    Returns a dict suitable for embedding in manifest.json, or None if
    all probes fail.
    """
    best = None
    for _ in range(_SYNC_PROBES):
        t1 = time.time()
        try:
            result = subprocess.run(
                ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5",
                 target_host, "date +%s%N"],
                capture_output=True, text=True, timeout=10,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue
        t2 = time.time()
        if result.returncode != 0:
            continue
        try:
            remote_ns = int(result.stdout.strip())
        except ValueError:
            continue
        rtt = t2 - t1
        remote_ts = remote_ns / 1e9
        offset = remote_ts - (t1 + rtt / 2)
        if best is None or rtt < best["rtt_s"]:
            best = {
                "target_host": target_host,
                "measured_at": round(t1, 3),
                "offset_s": round(offset, 6),
                "uncertainty_s": round(rtt / 2, 6),
                "rtt_s": round(rtt, 6),
                "method": "ssh-date",
            }
    return best


def _record_clock_sync(manifest_path: str, sync_info: dict):
    """Write clock_sync into manifest.json, preserving any existing content."""
    try:
        with open(manifest_path) as f:
            manifest = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        manifest = {"segments": []}
    manifest["clock_sync"] = sync_info
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Rolling Cynthion USB capture — rotates pcap segments with JSON indexes.")
    ap.add_argument("output_dir",
        help="Directory for capture segments (created if it does not exist)")
    ap.add_argument("--interval", type=float, default=300, metavar="SECONDS",
        help="Rotate to a new segment every N seconds (default: 300)")
    ap.add_argument("--max-size", type=float, default=None, metavar="MB",
        help="Also rotate after M MB of pcap data written (optional)")
    ap.add_argument("--prefix", default="capture", metavar="NAME",
        help="Filename prefix for segment files (default: capture)")
    ap.add_argument("--speed", choices=SPEEDS.keys(), default="auto",
        help="USB speed filter (default: auto)")
    ap.add_argument("--duration", type=float, default=None, metavar="SECONDS",
        help="Stop the whole session after N seconds (optional)")
    ap.add_argument("--no-index", action="store_true",
        help="Skip JSON indexing (run index_pcap.py later on the output directory)")
    ap.add_argument("--target-host", default=None, metavar="[USER@]HOST",
        help="SSH target to measure clock offset against at capture start "
             "(stored in manifest.json for post-processing correlation)")
    args = ap.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    max_size_bytes = int(args.max_size * 1024 * 1024) if args.max_size else None
    manifest_path  = os.path.join(args.output_dir, "manifest.json")

    if args.target_host:
        print(f"Measuring clock offset vs {args.target_host} ({_SYNC_PROBES} probes) ...",
              flush=True)
        sync = _measure_clock_offset(args.target_host)
        if sync:
            offset_ms = sync["offset_s"] * 1000
            uncert_ms = sync["uncertainty_s"] * 1000
            sign = "+" if offset_ms >= 0 else ""
            print(f"  clock sync: target is {sign}{offset_ms:.2f}ms ± {uncert_ms:.2f}ms  "
                  f"(rtt={sync['rtt_s'] * 1000:.1f}ms)", flush=True)
            _record_clock_sync(manifest_path, sync)
        else:
            print(f"  WARNING: clock sync failed — could not SSH to {args.target_host}",
                  file=sys.stderr)

    indexer = None
    if not args.no_index:
        try:
            decode  = import_decode()
            indexer = _IndexWorker(decode, manifest_path)
        except ImportError as exc:
            print(f"WARNING: {exc}\nRunning without indexing.",
                  file=sys.stderr)

    dev = usb.core.find(idVendor=VID, idProduct=PID_DEVICE)
    if dev is None:
        print("ERROR: No Cynthion USB Analyzer found.\n"
              "  Check CONTROL port cable and run: cynthion run analyzer",
              file=sys.stderr)
        sys.exit(1)

    intf = _find_analyzer_interface(dev)
    if intf is None:
        print("ERROR: Analyzer interface (class FF/10/01) not found.", file=sys.stderr)
        sys.exit(1)

    intf_num = intf.bInterfaceNumber
    try:
        if dev.is_kernel_driver_active(intf_num):
            dev.detach_kernel_driver(intf_num)
    except usb.core.USBError:
        pass
    usb.util.claim_interface(dev, intf_num)

    speed_code = SPEEDS[args.speed]
    ctrl_start = (speed_code << 1) | 1

    running = True

    def _stop(sig, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT,  _stop)
    signal.signal(signal.SIGTERM, _stop)

    session_start = time.time()
    deadline      = (session_start + args.duration) if args.duration else None

    seg = _SegmentManager(
        output_dir     = args.output_dir,
        prefix         = args.prefix,
        interval_s     = args.interval,
        max_size_bytes = max_size_bytes,
        indexer        = indexer,
    )
    seg.open_first()

    print(
        f"Rolling capture ({args.speed}) → {args.output_dir}/"
        f"  interval={args.interval:.0f}s"
        + (f"  max-size={args.max_size:.0f}MB" if args.max_size else "")
        + (f"  duration={args.duration:.0f}s" if args.duration else "  (Ctrl-C to stop)"),
        flush=True,
    )
    _send_capture_request(dev, intf_num, ctrl_start)

    buf         = b""
    last_status = time.time()

    try:
        while running:
            if deadline and time.time() >= deadline:
                break
            try:
                chunk = bytes(dev.read(BULK_EP_IN, TRANSFER_SIZE, timeout=500))
                buf  += chunk
                buf   = seg.write(buf)
            except usb.core.USBTimeoutError:
                pass

            if seg.should_rotate():
                seg.rotate()

            now = time.time()
            if now - last_status >= 60:
                elapsed = now - session_start
                print(f"  [{elapsed / 60:.0f}m]  "
                      f"{seg.total_packets} pkts  {seg.total_bytes / 1e6:.1f} MB  "
                      f"{seg.total_sof_dropped} SOF dropped",
                      flush=True)
                last_status = now

    finally:
        try:
            _send_capture_request(dev, intf_num, 0)
        except Exception:
            pass
        usb.util.release_interface(dev, intf_num)
        seg.close_final()

        if indexer:
            print("Waiting for background indexers ...", flush=True)
            indexer.join_all(timeout=60)

        elapsed = time.time() - session_start
        print(
            f"Done: {seg.total_packets} pkts  "
            f"{seg.total_bytes / 1e6:.2f} MB  "
            f"{elapsed:.1f}s  → {args.output_dir}/"
        )
        if not args.no_index:
            print(f"  manifest: {manifest_path}")


if __name__ == "__main__":
    main()
