#!/usr/bin/env python3
# Copyright 2026 contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""
infer_commands.py — heuristic command-structure inference from USB captures.

Takes two or more decoded captures (each with an action label) and emits a
JSON protocol-hypothesis document describing probable command opcodes,
argument positions, and response shapes.

Usage:
    python3 infer_commands.py idle.json button.json --label idle button
    python3 infer_commands.py *.json --label $(ls *.json | sed 's/.json//')
    python3 infer_commands.py a.pcap b.pcap --label before after --format markdown
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent))
from _sibling import import_decode

# ---------------------------------------------------------------------------
# Load helpers (same pattern as diff_transactions)
# ---------------------------------------------------------------------------

def load_transfers(path: str) -> List[dict]:
    if path.endswith(".json"):
        with open(path) as f:
            return json.load(f)
    decode = import_decode()
    pkts  = decode.stream_packets(path)
    txns  = decode.stream_transactions(pkts)
    xfers = decode.stream_transfers(txns)
    return [x.to_dict() for x in xfers]


# ---------------------------------------------------------------------------
# Hypothesis building
# ---------------------------------------------------------------------------

MAX_OPCODE_VALUES = 16   # a byte with > this many distinct values is not an opcode
MIN_SAMPLES = 2           # need at least this many transactions to characterise


def _extract_non_ep0(transfers: List[dict]) -> List[dict]:
    return [x for x in transfers if x.get("endp", 0) != 0 and x.get("payload_hex")]


def _bytes_from_xfer(xfer: dict) -> bytes:
    return bytes.fromhex(xfer["payload_hex"])


def _device_identity(all_transfers_by_label: List[Tuple[str, List[dict]]]) -> dict:
    """Extract device VID/PID from any control transfer that decoded a Device Descriptor."""
    for _label, xfers in all_transfers_by_label:
        for xfer in xfers:
            dec = xfer.get("decoded") or {}
            if dec.get("descriptor_type") == 1:  # Device Descriptor
                return {
                    "idVendor":  dec.get("idVendor", "unknown"),
                    "idProduct": dec.get("idProduct", "unknown"),
                    "bcdUSB":    dec.get("bcdUSB", "unknown"),
                    "manufacturer": dec.get("iManufacturer"),
                    "product":      dec.get("iProduct"),
                }
    return {}


def _classify_byte_role(values_by_label: Dict[str, List[int]]) -> str:
    """
    Given a dict mapping label → list of observed values for one byte offset,
    classify the byte's likely role.
    """
    all_vals = [v for vs in values_by_label.values() for v in vs]
    distinct = set(all_vals)

    # Constant: same value in every sample across every label
    if len(distinct) == 1:
        return "constant"

    # Monotonic (sequence counter): values strictly increment by 1 across samples
    sorted_vals = sorted(all_vals)
    if all(b - a == 1 for a, b in zip(sorted_vals, sorted_vals[1:])):
        return "counter"

    # Label-correlated: each label has consistent values, but labels differ
    per_label_distinct = {lbl: set(vs) for lbl, vs in values_by_label.items()}
    if all(len(s) <= 2 for s in per_label_distinct.values()):
        # Check that the value sets differ across labels
        all_sets = list(per_label_distinct.values())
        if any(all_sets[0] != s for s in all_sets[1:]):
            if len(distinct) <= MAX_OPCODE_VALUES:
                return "opcode"

    if len(distinct) <= MAX_OPCODE_VALUES:
        return "candidate_opcode"

    return "varying"


def _analyse_endpoint(
    endp_key: Tuple[int, int, str],
    samples_by_label: Dict[str, List[bytes]],
) -> dict:
    """Produce a hypothesis for one endpoint given multi-label sample sets."""
    addr, endp, direction = endp_key

    # Find the most common payload length (frame size)
    all_payloads = [p for ps in samples_by_label.values() for p in ps]
    length_counter = Counter(len(p) for p in all_payloads)
    frame_size, _ = length_counter.most_common(1)[0]

    # Limit analysis to payloads of the dominant frame size
    filtered = {lbl: [p for p in ps if len(p) == frame_size]
                for lbl, ps in samples_by_label.items()}

    if all(len(ps) < MIN_SAMPLES for ps in filtered.values()):
        return {"addr": addr, "endp": endp, "direction": direction,
                "note": "insufficient samples"}

    # Per-offset classification
    byte_roles = []
    for i in range(frame_size):
        vals_by_label = {lbl: [p[i] for p in ps if len(p) > i]
                         for lbl, ps in filtered.items()}
        role = _classify_byte_role(vals_by_label)
        example_vals = {lbl: list(set(vals_by_label[lbl]))[:4]
                        for lbl in vals_by_label if vals_by_label[lbl]}
        byte_roles.append({
            "offset": i,
            "role": role,
            "values_by_label": {k: [f"{v:#04x}" for v in vs] for k, vs in example_vals.items()},
        })

    # Identify opcode candidates
    opcode_offsets = [b["offset"] for b in byte_roles if b["role"] in ("opcode", "candidate_opcode")]

    # Build command table: group by value at opcode offset
    commands = []
    if opcode_offsets:
        primary_op_offset = opcode_offsets[0]
        op_groups: Dict[int, Dict[str, List[bytes]]] = defaultdict(lambda: defaultdict(list))
        for lbl, ps in filtered.items():
            for p in ps:
                if len(p) > primary_op_offset:
                    op_val = p[primary_op_offset]
                    op_groups[op_val][lbl].append(p)

        for op_val in sorted(op_groups):
            by_label = op_groups[op_val]
            example = next((p for ps in by_label.values() for p in ps), b"")
            commands.append({
                "opcode": f"{op_val:#04x}",
                "observed_in_labels": sorted(by_label.keys()),
                "count": sum(len(ps) for ps in by_label.values()),
                "example_payload": example.hex(),
            })

    return {
        "addr": addr,
        "endp": endp,
        "direction": direction,
        "frame_size": frame_size,
        "byte_roles": byte_roles,
        "opcode_offsets": opcode_offsets,
        "commands": commands,
    }


def infer_hypothesis(
    captures: List[Tuple[str, List[dict]]],
    endp_filter: Optional[int] = None,
    addr_filter: Optional[int] = None,
) -> dict:
    """Build and return the full protocol hypothesis document."""
    device = _device_identity(captures)

    # Group non-EP0 transfers by endpoint key and label
    by_endp: Dict[Tuple, Dict[str, List[bytes]]] = defaultdict(lambda: defaultdict(list))
    for label, xfers in captures:
        for xfer in _extract_non_ep0(xfers):
            addr, endp, direction = xfer["addr"], xfer["endp"], xfer["direction"]
            if addr_filter is not None and addr != addr_filter:
                continue
            if endp_filter is not None and endp != endp_filter:
                continue
            by_endp[(addr, endp, direction)][label].append(_bytes_from_xfer(xfer))

    endpoints = []
    for key in sorted(by_endp):
        ep_hyp = _analyse_endpoint(key, by_endp[key])
        endpoints.append(ep_hyp)

    # Identify OUT endpoints that pair with IN endpoints (likely command/response pairs)
    endp_nums = {(k[0], k[1]) for k in by_endp}
    pairs = []
    for addr, endp in endp_nums:
        has_out = (addr, endp, "OUT") in by_endp
        has_in  = (addr, endp, "IN")  in by_endp
        if has_out and has_in:
            pairs.append({"addr": addr, "endp": endp, "note": "bidirectional — likely command+response"})

    open_questions = []
    for ep in endpoints:
        if ep.get("opcode_offsets") and not ep.get("commands"):
            open_questions.append(
                f"EP{ep['endp']} {ep['direction']}: opcode candidates at byte(s) "
                f"{ep['opcode_offsets']} but commands not resolved — need more captures"
            )
        if any(b["role"] == "varying" for b in ep.get("byte_roles", [])):
            varying = [b["offset"] for b in ep.get("byte_roles", []) if b["role"] == "varying"]
            open_questions.append(
                f"EP{ep['endp']} {ep['direction']}: bytes {varying} are fully varying "
                f"— possible CRC, timestamp, or random nonce"
            )

    return {
        "device": device,
        "labels": [lbl for lbl, _ in captures],
        "endpoint_pairs": pairs,
        "endpoints": endpoints,
        "open_questions": open_questions,
    }


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

def format_json(hyp: dict) -> str:
    return json.dumps(hyp, indent=2)


def format_markdown(hyp: dict) -> str:
    dev = hyp.get("device", {})
    lines = [
        "# USB Protocol Hypothesis", "",
        "## Device",
        f"- **VID/PID:** {dev.get('idVendor', '?')} / {dev.get('idProduct', '?')}",
        f"- **USB spec:** {dev.get('bcdUSB', '?')}",
        "",
        f"**Captures analysed:** {', '.join(hyp.get('labels', []))}",
        "",
    ]

    if hyp.get("endpoint_pairs"):
        lines.append("## Endpoint Pairs (likely command+response)")
        for pair in hyp["endpoint_pairs"]:
            lines.append(f"- addr={pair['addr']} EP{pair['endp']}: {pair['note']}")
        lines.append("")

    for ep in hyp.get("endpoints", []):
        lines.append(f"## addr={ep.get('addr')} EP{ep.get('endp')} {ep.get('direction')}  "
                     f"(frame size: {ep.get('frame_size', '?')} bytes)")
        lines.append("")

        roles = ep.get("byte_roles", [])
        if roles:
            lines.append("| byte | role | values by label |")
            lines.append("|------|------|-----------------|")
            for b in roles:
                vals = "; ".join(f"{lbl}: {' '.join(vs)}" for lbl, vs in b["values_by_label"].items())
                lines.append(f"| {b['offset']} | **{b['role']}** | {vals} |")
            lines.append("")

        cmds = ep.get("commands", [])
        if cmds:
            lines.append("**Inferred commands:**")
            lines.append("")
            lines.append("| opcode | seen in | count | example |")
            lines.append("|--------|---------|-------|---------|")
            for cmd in cmds:
                lines.append(
                    f"| `{cmd['opcode']}` | {', '.join(cmd['observed_in_labels'])} | "
                    f"{cmd['count']} | `{cmd['example_payload']}` |"
                )
            lines.append("")

    if hyp.get("open_questions"):
        lines.append("## Open Questions")
        for q in hyp["open_questions"]:
            lines.append(f"- {q}")
        lines.append("")

    return "\n".join(lines)


FORMATTERS = {"json": format_json, "markdown": format_markdown}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(
        description="Infer USB command structure from multiple labelled captures."
    )
    p.add_argument("captures", nargs="+",
                   help="Capture files (.pcap or .json), one per action")
    p.add_argument("--label", nargs="+", metavar="LABEL",
                   help="Labels for each capture (default: A B C …)")
    p.add_argument("--address", type=int)
    p.add_argument("--endpoint", type=int)
    p.add_argument("--format", choices=list(FORMATTERS), default="json")
    args = p.parse_args()

    labels = args.label or [chr(65 + i) for i in range(len(args.captures))]
    if len(labels) != len(args.captures):
        p.error(f"--label count ({len(labels)}) must match capture count ({len(args.captures)})")

    captures = [(lbl, load_transfers(path)) for lbl, path in zip(labels, args.captures)]
    hyp = infer_hypothesis(captures, endp_filter=args.endpoint, addr_filter=args.address)
    print(FORMATTERS[args.format](hyp))


if __name__ == "__main__":
    main()
