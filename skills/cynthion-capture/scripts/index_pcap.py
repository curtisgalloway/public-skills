#!/usr/bin/env python3
# Copyright 2026 contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""USB pcap indexer for Cynthion captures.

Reads one or more LINKTYPE_USB_2_0 pcap files and writes a JSON index
alongside each, recording per-device packet statistics and USB descriptor
information extracted from enumeration traffic (VID, PID, device class).

Usage:
    python3 index_pcap.py capture.pcap
    python3 index_pcap.py captures/*.pcap
    python3 index_pcap.py capture.pcap --manifest captures/
    python3 index_pcap.py capture.pcap --stdout     # print index, don't write file
"""

import argparse
import gzip
import json
import os
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _sibling import import_decode  # noqa: E402

PCAP_MAGIC_LE = 0xa1b2c3d4
PCAP_MAGIC_NS = 0xa1b23c4d


def _open_pcap(path: str):
    if path.endswith(".gz"):
        return gzip.open(path, "rb")
    return open(path, "rb")


def _json_path(pcap_path: str) -> Path:
    p = Path(pcap_path)
    if p.suffix == ".gz":
        p = p.with_suffix("")
    return p.with_suffix(".json")


def _pcap_meta(path: str):
    """Return (first_ts, last_ts, total_packets, total_bytes) from pcap record headers."""
    first_ts = last_ts = None
    total_packets = total_bytes = 0

    with _open_pcap(path) as f:
        raw_magic = f.read(4)
        if len(raw_magic) < 4:
            return None, None, 0, 0
        magic = struct.unpack("<I", raw_magic)[0]
        if magic in (PCAP_MAGIC_LE, PCAP_MAGIC_NS):
            endian = "<"
            divisor = 1e9 if magic == PCAP_MAGIC_NS else 1e6
        elif magic in (0xd4c3b2a1, 0x4d3cb2a1):
            endian = ">"
            divisor = 1e6 if magic == 0xd4c3b2a1 else 1e9
        else:
            return None, None, 0, 0

        f.read(20)  # rest of global header (version, zone, sigfigs, snaplen, linktype)

        while True:
            hdr = f.read(16)
            if len(hdr) < 16:
                break
            ts_sec, ts_frac, incl_len, _ = struct.unpack(endian + "IIII", hdr)
            ts = ts_sec + ts_frac / divisor
            if first_ts is None:
                first_ts = ts
            last_ts = ts
            total_packets += 1
            total_bytes += incl_len
            f.seek(incl_len, 1)

    return first_ts, last_ts, total_packets, total_bytes


def build_index(pcap_path: str, decode) -> dict:
    """Return an index dict for the given pcap file using decode.py's pipeline."""
    first_ts, last_ts, total_packets, total_bytes = _pcap_meta(pcap_path)

    devices: dict[int, dict] = {}

    def touch(addr: int, rel_time: float):
        if addr not in devices:
            devices[addr] = {
                "first_seen": None,
                "last_seen": None,
                "transfers": 0,
            }
        d = devices[addr]
        abs_ts = (first_ts or 0) + rel_time
        if d["first_seen"] is None or abs_ts < d["first_seen"]:
            d["first_seen"] = abs_ts
        if d["last_seen"] is None or abs_ts > d["last_seen"]:
            d["last_seen"] = abs_ts
        d["transfers"] += 1
        return d

    try:
        pkts = decode.stream_packets(pcap_path, force_native=True)
        txns = decode.stream_transactions(pkts)
        for xfer in decode.stream_transfers(txns):
            d = touch(xfer.addr, xfer.time_s)

            # Capture VID/PID from a successful GET_DESCRIPTOR(DEVICE) response.
            if (xfer.type == "control" and xfer.endp == 0 and xfer.decoded
                    and xfer.decoded.get("descriptor_type") == 1
                    and "idVendor" in xfer.decoded):
                for key in ("idVendor", "idProduct", "bDeviceClass",
                            "bDeviceSubClass", "bDeviceProtocol", "bcdUSB",
                            "bMaxPacketSize0", "bNumConfigurations"):
                    if key in xfer.decoded:
                        d[key] = xfer.decoded[key]
    except Exception as exc:
        print(f"  warning: decode error in {os.path.basename(pcap_path)}: {exc}",
              file=sys.stderr)

    # Serialize: use string keys for JSON, round float timestamps.
    devices_out = {}
    for addr, info in sorted(devices.items()):
        entry = dict(info)
        if entry.get("first_seen") is not None:
            entry["first_seen"] = round(entry["first_seen"], 6)
        if entry.get("last_seen") is not None:
            entry["last_seen"] = round(entry["last_seen"], 6)
        devices_out[str(addr)] = entry

    return {
        "file": os.path.basename(pcap_path),
        "indexed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "start_time": round(first_ts, 6) if first_ts else None,
        "end_time": round(last_ts, 6) if last_ts else None,
        "duration_s": round(last_ts - first_ts, 3) if (first_ts and last_ts) else 0,
        "packets": total_packets,
        "bytes": total_bytes,
        "devices": devices_out,
    }


def write_index(pcap_path: str, index: dict) -> str:
    """Write index as JSON alongside the pcap file. Returns the index path."""
    out = _json_path(pcap_path)
    with open(out, "w") as f:
        json.dump(index, f, indent=2)
        f.write("\n")
    return str(out)


def _manifest_entry(pcap_path: str, index: dict) -> dict:
    """Build the compact entry for this segment in manifest.json."""
    devices_brief = []
    for addr_s, info in index.get("devices", {}).items():
        entry: dict = {"addr": int(addr_s)}
        if "idVendor" in info:
            entry["vid"] = info["idVendor"]
            entry["pid"] = info["idProduct"]
        devices_brief.append(entry)

    index_path = str(_json_path(pcap_path))
    return {
        "file": os.path.basename(pcap_path),
        "index": os.path.basename(index_path),
        "start_time": index["start_time"],
        "end_time": index["end_time"],
        "duration_s": index["duration_s"],
        "packets": index["packets"],
        "bytes": index["bytes"],
        "devices": devices_brief,
    }


def update_manifest(manifest_path: str, pcap_path: str, index: dict):
    """Add or update a segment entry in manifest.json."""
    try:
        with open(manifest_path) as f:
            manifest = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        manifest = {"segments": []}

    fname = os.path.basename(pcap_path)
    manifest["segments"] = [s for s in manifest.get("segments", [])
                             if s.get("file") != fname]
    manifest["segments"].append(_manifest_entry(pcap_path, index))
    manifest["segments"].sort(key=lambda s: s.get("start_time") or 0)

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")


def _print_summary(pcap_path: str, index: dict):
    devices = index.get("devices", {})
    dt = datetime.fromtimestamp(index["start_time"] or 0, tz=timezone.utc)
    print(f"{os.path.basename(pcap_path)}  "
          f"[{dt.strftime('%Y-%m-%d %H:%M:%S')} UTC]  "
          f"{index['duration_s']:.1f}s  "
          f"{index['packets']} pkts  "
          f"{len(devices)} device(s)")
    for addr_s, info in devices.items():
        vid_pid = ""
        if "idVendor" in info:
            vid_pid = f"  {info['idVendor']}:{info['idProduct']}"
            cls = info.get("bDeviceClass", "")
            if cls:
                vid_pid += f"  class={cls}"
        print(f"  addr {addr_s:>3}  {info['transfers']:>6} transfers"
              f"  {info.get('first_seen', 0):.3f}–{info.get('last_seen', 0):.3f}s"
              f"{vid_pid}")


def main():
    p = argparse.ArgumentParser(
        description="Index Cynthion USB pcap files — writes a .json beside each .pcap.")
    p.add_argument("pcap", nargs="+", help="One or more .pcap files to index")
    p.add_argument("--manifest", metavar="DIR",
                   help="Also update (or create) manifest.json in DIR")
    p.add_argument("--stdout", action="store_true",
                   help="Print the index JSON to stdout instead of writing a file")
    args = p.parse_args()

    try:
        decode = import_decode()
    except ImportError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    for pcap_path in args.pcap:
        if not os.path.isfile(pcap_path):
            print(f"SKIP: {pcap_path} — not found", file=sys.stderr)
            continue

        print(f"Indexing {pcap_path} ...", end=" ", flush=True)
        index = build_index(pcap_path, decode)

        if args.stdout:
            print()
            print(json.dumps(index, indent=2))
        else:
            out = write_index(pcap_path, index)
            print(f"→ {out}")

        _print_summary(pcap_path, index)

        if args.manifest:
            manifest_path = os.path.join(args.manifest, "manifest.json")
            update_manifest(manifest_path, pcap_path, index)
            print(f"  manifest updated: {manifest_path}")


if __name__ == "__main__":
    main()
