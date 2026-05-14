#!/usr/bin/env python3
# Copyright 2026 contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""
diff.py — Diff two Packetry/Cynthion USB pcap captures.

Aligns transactions by endpoint and sequence order, then reports byte-level
differences in the data payloads. Useful for spotting regressions between
firmware versions or comparing two devices running the same protocol.

Usage:
    python3 diff.py a.pcap b.pcap
    python3 diff.py a.pcap b.pcap --endpoint 1
    python3 diff.py a.pcap b.pcap --address 2
    python3 diff.py a.pcap b.pcap --format markdown
    python3 diff.py a.pcap b.pcap --control-only
"""

import argparse
import json
import sys
from collections import defaultdict
from typing import Dict, Iterator, List, Optional, Tuple

# Import the shared pipeline from decode.py in the same directory
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from decode import (
    Filters, Transaction, Transfer,
    stream_packets, stream_transactions, stream_transfers,
)


# ---------------------------------------------------------------------------
# Load helpers
# ---------------------------------------------------------------------------

def _null_filters() -> Filters:
    """Return a Filters instance that passes everything."""

    class _Args:
        filter = []
        time_range = None
        phase = None

    return Filters(_Args())


def load_transactions(pcap_path: str, force_native: bool = False) -> List[Transaction]:
    """Return all transactions from a capture file."""
    pkts = stream_packets(pcap_path, force_native=force_native)
    return list(stream_transactions(pkts))


def load_transfers(pcap_path: str, force_native: bool = False) -> List[Transfer]:
    pkts  = stream_packets(pcap_path, force_native=force_native)
    txns  = stream_transactions(pkts)
    xfers = stream_transfers(txns)
    return list(xfers)


# ---------------------------------------------------------------------------
# Alignment
# ---------------------------------------------------------------------------

# Key: (addr, endp, direction)
EndpointKey = Tuple[int, int, str]


def _group_by_endpoint(
    transactions: List[Transaction],
) -> Dict[EndpointKey, List[Transaction]]:
    groups: Dict[EndpointKey, List[Transaction]] = defaultdict(list)
    for tx in transactions:
        if tx.successful and tx.payload:
            key = (tx.addr, tx.endp, tx.direction)
            groups[key].append(tx)
    return groups


def _align(
    a_txns: List[Transaction], b_txns: List[Transaction]
) -> Iterator[Tuple[Optional[Transaction], Optional[Transaction]]]:
    """Pair transactions by sequence position (simple zip with length padding)."""
    for i in range(max(len(a_txns), len(b_txns))):
        yield (
            a_txns[i] if i < len(a_txns) else None,
            b_txns[i] if i < len(b_txns) else None,
        )


# ---------------------------------------------------------------------------
# Byte-level diff
# ---------------------------------------------------------------------------

def _diff_bytes(a: bytes, b: bytes) -> List[dict]:
    """Return a list of differing byte positions with before/after values."""
    diffs = []
    for i in range(max(len(a), len(b))):
        ba = a[i] if i < len(a) else None
        bb = b[i] if i < len(b) else None
        if ba != bb:
            diffs.append({"offset": i, "a": f"{ba:#04x}" if ba is not None else "missing",
                          "b": f"{bb:#04x}" if bb is not None else "missing"})
    return diffs


def _hex_line(data: bytes, changed: set, width: int = 16) -> List[str]:
    """Render hex dump lines with changed offsets marked."""
    lines = []
    for row in range(0, len(data), width):
        chunk = data[row:row + width]
        parts = []
        for i, byte in enumerate(chunk):
            marker = "*" if (row + i) in changed else " "
            parts.append(f"{marker}{byte:02x}")
        lines.append(f"  {row:04x}  {'  '.join(parts)}")
    return lines


# ---------------------------------------------------------------------------
# Diff result
# ---------------------------------------------------------------------------

class TxnDiff:
    def __init__(self, key: EndpointKey, seq: int,
                 a: Optional[Transaction], b: Optional[Transaction]):
        self.key = key
        self.seq = seq
        self.a = a
        self.b = b
        self.byte_diffs: List[dict] = []
        self.length_changed = False
        self.only_in_a = (b is None)
        self.only_in_b = (a is None)

        if a and b:
            pa, pb = a.payload or b"", b.payload or b""
            self.length_changed = len(pa) != len(pb)
            self.byte_diffs = _diff_bytes(pa, pb)

    @property
    def has_diff(self) -> bool:
        return bool(self.byte_diffs) or self.only_in_a or self.only_in_b

    def to_dict(self) -> dict:
        addr, endp, direction = self.key
        d: dict = {
            "addr": addr, "endp": endp, "direction": direction, "seq": self.seq,
        }
        if self.only_in_a:
            d["status"] = "only_in_a"
            d["a_time_s"] = round(self.a.time_s, 6) if self.a else None
            d["a_payload"] = self.a.payload.hex() if (self.a and self.a.payload) else None
        elif self.only_in_b:
            d["status"] = "only_in_b"
            d["b_time_s"] = round(self.b.time_s, 6) if self.b else None
            d["b_payload"] = self.b.payload.hex() if (self.b and self.b.payload) else None
        else:
            pa = self.a.payload or b""
            pb = self.b.payload or b""
            d["status"] = "changed" if self.byte_diffs else "identical"
            d["a_len"] = len(pa)
            d["b_len"] = len(pb)
            d["byte_diffs"] = self.byte_diffs
        return d


# ---------------------------------------------------------------------------
# Core diff engine
# ---------------------------------------------------------------------------

def diff_captures(
    a_path: str, b_path: str,
    addr_filter: Optional[int] = None,
    endp_filter: Optional[int] = None,
    control_only: bool = False,
    force_native: bool = False,
) -> List[TxnDiff]:
    a_txns = load_transactions(a_path, force_native)
    b_txns = load_transactions(b_path, force_native)

    a_groups = _group_by_endpoint(a_txns)
    b_groups = _group_by_endpoint(b_txns)

    all_keys = sorted(set(a_groups) | set(b_groups))

    results: List[TxnDiff] = []

    for key in all_keys:
        addr, endp, direction = key
        if addr_filter is not None and addr != addr_filter:
            continue
        if endp_filter is not None and endp != endp_filter:
            continue
        if control_only and endp != 0:
            continue

        a_seq = a_groups.get(key, [])
        b_seq = b_groups.get(key, [])

        for seq, (ta, tb) in enumerate(_align(a_seq, b_seq)):
            d = TxnDiff(key, seq, ta, tb)
            if d.has_diff:
                results.append(d)

    return results


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

def format_json(diffs: List[TxnDiff]) -> str:
    return json.dumps([d.to_dict() for d in diffs], indent=2)


def format_text(diffs: List[TxnDiff]) -> str:
    if not diffs:
        return "No differences found."

    lines = [f"{len(diffs)} difference(s) found.\n"]
    for d in diffs:
        addr, endp, direction = d.key
        hdr = f"addr={addr} ep={endp} {direction} seq={d.seq}"

        if d.only_in_a:
            lines.append(f"  ONLY IN A  {hdr}")
            if d.a and d.a.payload:
                lines.append(f"    {len(d.a.payload)} bytes: {d.a.payload.hex()}")
        elif d.only_in_b:
            lines.append(f"  ONLY IN B  {hdr}")
            if d.b and d.b.payload:
                lines.append(f"    {len(d.b.payload)} bytes: {d.b.payload.hex()}")
        else:
            pa = d.a.payload or b""
            pb = d.b.payload or b""
            changed_offsets = {bd["offset"] for bd in d.byte_diffs}
            lines.append(f"  CHANGED    {hdr}  (a={len(pa)}B b={len(pb)}B  {len(d.byte_diffs)} byte(s) differ)")
            lines.append("    A:")
            lines.extend(_hex_line(pa, changed_offsets))
            lines.append("    B:")
            lines.extend(_hex_line(pb, changed_offsets))
            lines.append(f"    Offsets: {[bd['offset'] for bd in d.byte_diffs]}")
        lines.append("")

    return "\n".join(lines)


def format_markdown(diffs: List[TxnDiff]) -> str:
    lines = ["# USB Capture Diff", ""]
    if not diffs:
        lines.append("No differences found.")
        return "\n".join(lines)

    lines.append(f"**{len(diffs)} difference(s)** found.\n")
    lines += ["| addr | ep | dir | seq | status | details |",
              "|------|----|-----|-----|--------|---------|"]

    for d in diffs:
        addr, endp, direction = d.key
        if d.only_in_a:
            status, detail = "only in A", ""
        elif d.only_in_b:
            status, detail = "only in B", ""
        else:
            pa = d.a.payload or b""
            pb = d.b.payload or b""
            status = "changed" if d.byte_diffs else "identical"
            offsets = [str(bd["offset"]) for bd in d.byte_diffs[:5]]
            detail = f"{len(d.byte_diffs)} byte(s) at [{', '.join(offsets)}{'...' if len(d.byte_diffs)>5 else ''}]"
        lines.append(f"| {addr} | {endp} | {direction} | {d.seq} | {status} | {detail} |")

    return "\n".join(lines)


FORMATTERS = {"json": format_json, "text": format_text, "markdown": format_markdown}

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(
        description="Diff two Packetry/Cynthion USB pcap captures by transaction sequence."
    )
    p.add_argument("a", help="First capture file (reference)")
    p.add_argument("b", help="Second capture file (comparison)")
    p.add_argument("--address", type=int, metavar="N", help="Restrict to USB device address N")
    p.add_argument("--endpoint", type=int, metavar="N", help="Restrict to endpoint N")
    p.add_argument("--control-only", action="store_true", help="Only diff EP0 control transfers")
    p.add_argument("--format", choices=list(FORMATTERS), default="text",
                   help="Output format (default: text)")
    p.add_argument("--native", action="store_true", help="Force native decoder (skip tshark)")
    args = p.parse_args()

    diffs = diff_captures(
        args.a, args.b,
        addr_filter=args.address,
        endp_filter=args.endpoint,
        control_only=args.control_only,
        force_native=args.native,
    )
    print(FORMATTERS[args.format](diffs))


if __name__ == "__main__":
    main()
