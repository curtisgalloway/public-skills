#!/usr/bin/env python3
# Copyright 2026 contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""
diff_transactions.py — byte-level comparison of two USB captures.

For each (addr, endpoint, direction) group, aligns transactions by sequence
position and classifies each byte offset as:

  constant   — same value in both captures
  monotonic  — value increments by exactly 1 between the two samples
               (likely a sequence counter or frame counter)
  varying    — different value with no simple relationship
               (opcode, argument, payload, CRC, or random nonce)

Usage:
    python3 diff_transactions.py A.json B.json
    python3 diff_transactions.py A.pcap B.pcap --label "idle" "button_pressed"
    python3 diff_transactions.py A.json B.json --endpoint 1 --format text
    python3 diff_transactions.py A.json B.json --format markdown > diff.md
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent))
from _sibling import import_decode


# ---------------------------------------------------------------------------
# Load transfers from JSON or pcap
# ---------------------------------------------------------------------------

def _load_json(path: str) -> List[dict]:
    with open(path) as f:
        return json.load(f)


def _load_pcap(path: str, decode) -> List[dict]:
    pkts  = decode.stream_packets(path)
    txns  = decode.stream_transactions(pkts)
    xfers = decode.stream_transfers(txns)
    return [x.to_dict() for x in xfers]


def load_transfers(path: str) -> List[dict]:
    if path.endswith(".json"):
        return _load_json(path)
    decode = import_decode()
    return _load_pcap(path, decode)


# ---------------------------------------------------------------------------
# Byte-level diff and classification
# ---------------------------------------------------------------------------

EndpKey = Tuple[int, int, str]  # (addr, endp, direction)


def _group_by_endp(transfers: List[dict]) -> Dict[EndpKey, List[bytes]]:
    groups: Dict[EndpKey, List[bytes]] = defaultdict(list)
    for xfer in transfers:
        payload_hex = xfer.get("payload_hex")
        if not payload_hex:
            continue
        key = (xfer["addr"], xfer["endp"], xfer["direction"])
        groups[key].append(bytes.fromhex(payload_hex))
    return groups


def _classify(val_a: Optional[int], val_b: Optional[int]) -> str:
    if val_a is None or val_b is None:
        return "missing"
    if val_a == val_b:
        return "constant"
    if (val_b - val_a) == 1:
        return "monotonic"
    return "varying"


def diff_endpoint(
    a_payloads: List[bytes],
    b_payloads: List[bytes],
) -> List[dict]:
    """Return per-transaction diff records for one endpoint."""
    results = []
    for seq, (pa, pb) in enumerate(zip(a_payloads, b_payloads)):
        width = max(len(pa), len(pb))
        byte_diffs = []
        for i in range(width):
            va = pa[i] if i < len(pa) else None
            vb = pb[i] if i < len(pb) else None
            cls = _classify(va, vb)
            byte_diffs.append({
                "offset": i,
                "a": f"{va:#04x}" if va is not None else "missing",
                "b": f"{vb:#04x}" if vb is not None else "missing",
                "class": cls,
            })
        results.append({
            "seq": seq,
            "a_len": len(pa),
            "b_len": len(pb),
            "bytes": byte_diffs,
            "varying_offsets": [d["offset"] for d in byte_diffs if d["class"] == "varying"],
            "monotonic_offsets": [d["offset"] for d in byte_diffs if d["class"] == "monotonic"],
        })
    return results


def diff_all(
    a_transfers: List[dict],
    b_transfers: List[dict],
    endp_filter: Optional[int] = None,
    addr_filter: Optional[int] = None,
    skip_control: bool = True,
) -> dict:
    """Diff two capture transfer lists; return structured results."""
    a_groups = _group_by_endp(a_transfers)
    b_groups = _group_by_endp(b_transfers)
    all_keys = sorted(set(a_groups) | set(b_groups))

    result: dict = {"endpoints": []}

    for key in all_keys:
        addr, endp, direction = key
        if addr_filter is not None and addr != addr_filter:
            continue
        if endp_filter is not None and endp != endp_filter:
            continue
        if skip_control and endp == 0:
            continue

        a_seqs = a_groups.get(key, [])
        b_seqs = b_groups.get(key, [])
        if not a_seqs or not b_seqs:
            continue

        txn_diffs = diff_endpoint(a_seqs, b_seqs)

        # Summarise classification across all transactions for this endpoint
        offset_classes: Dict[int, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for td in txn_diffs:
            for bd in td["bytes"]:
                offset_classes[bd["offset"]][bd["class"]] += 1

        byte_summary = []
        for offset in sorted(offset_classes):
            counts = offset_classes[offset]
            dominant = max(counts, key=counts.get)
            byte_summary.append({"offset": offset, "dominant_class": dominant, "counts": dict(counts)})

        result["endpoints"].append({
            "addr": addr, "endp": endp, "direction": direction,
            "a_count": len(a_seqs), "b_count": len(b_seqs),
            "compared": len(txn_diffs),
            "byte_summary": byte_summary,
            "transactions": txn_diffs,
        })

    return result


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

def format_json(result: dict, label_a: str, label_b: str) -> str:
    result["label_a"] = label_a
    result["label_b"] = label_b
    return json.dumps(result, indent=2)


def format_text(result: dict, label_a: str, label_b: str) -> str:
    lines = [f"Diff: '{label_a}' vs '{label_b}'\n"]
    for ep in result["endpoints"]:
        lines.append(
            f"addr={ep['addr']} ep={ep['endp']} {ep['direction']}  "
            f"({ep['compared']} transactions compared)"
        )
        for b in ep["byte_summary"]:
            cls = b["dominant_class"]
            marker = {"constant": ".", "monotonic": "^", "varying": "!", "missing": "?"}.get(cls, "?")
            lines.append(
                f"  byte[{b['offset']:2d}] {marker} {cls:<10}  {b['counts']}"
            )
        lines.append("")
    lines.append("Legend: . constant  ^ monotonic (counter)  ! varying (likely opcode/data)  ? missing")
    return "\n".join(lines)


def format_markdown(result: dict, label_a: str, label_b: str) -> str:
    lines = [
        f"# USB Transaction Diff: `{label_a}` vs `{label_b}`", "",
        "Legend: `.` constant · `^` monotonic (counter) · `!` varying · `?` missing", "",
    ]
    for ep in result["endpoints"]:
        lines.append(
            f"## addr={ep['addr']} EP{ep['endp']} {ep['direction']}  "
            f"({ep['compared']} transactions)"
        )
        lines.append("")
        lines.append("| byte | class | A values | B values |")
        lines.append("|------|-------|----------|----------|")
        # Collect sample values per offset across first 5 transactions
        offset_vals: Dict[int, Tuple[List, List]] = defaultdict(lambda: ([], []))
        for td in ep["transactions"][:5]:
            for bd in td["bytes"]:
                offset_vals[bd["offset"]][0].append(bd["a"])
                offset_vals[bd["offset"]][1].append(bd["b"])
        for b in ep["byte_summary"]:
            o = b["offset"]
            cls = b["dominant_class"]
            marker = {"constant": ".", "monotonic": "^", "varying": "!", "missing": "?"}.get(cls, "?")
            a_vals = " ".join(offset_vals[o][0])
            b_vals = " ".join(offset_vals[o][1])
            lines.append(f"| {o} | `{marker}` {cls} | `{a_vals}` | `{b_vals}` |")
        lines.append("")
    return "\n".join(lines)


FORMATTERS = {"json": format_json, "text": format_text, "markdown": format_markdown}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(
        description="Byte-classify differences between two USB capture files."
    )
    p.add_argument("a", help="First capture (.pcap or .json from decode.py)")
    p.add_argument("b", help="Second capture (.pcap or .json from decode.py)")
    p.add_argument("--label", nargs=2, metavar=("A", "B"), default=["A", "B"],
                   help="Human labels for the two captures (default: A B)")
    p.add_argument("--address", type=int, metavar="N")
    p.add_argument("--endpoint", type=int, metavar="N")
    p.add_argument("--include-control", action="store_true",
                   help="Include EP0 control transfers (excluded by default)")
    p.add_argument("--format", choices=list(FORMATTERS), default="text")
    args = p.parse_args()

    a_xfers = load_transfers(args.a)
    b_xfers = load_transfers(args.b)

    result = diff_all(
        a_xfers, b_xfers,
        endp_filter=args.endpoint,
        addr_filter=args.address,
        skip_control=not args.include_control,
    )
    print(FORMATTERS[args.format](result, args.label[0], args.label[1]))


if __name__ == "__main__":
    main()
