#!/usr/bin/env python3
# Copyright 2026 contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""
gen_protocol_doc.py — generate a Markdown protocol-reverse-engineering report.

Takes the protocol hypothesis JSON (from infer_commands.py) and one or more
labelled capture JSONs, and emits a structured Markdown document suitable for
saving as a protocol reference.

Usage:
    python3 gen_protocol_doc.py hypothesis.json \\
        --capture idle.json idle \\
        --capture button.json button_press \\
        -o protocol.md
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load(path: str) -> object:
    with open(path) as f:
        return json.load(f)


def _hex_to_int(h: str, default: int = 0) -> int:
    try:
        return int(str(h).replace("0x", ""), 16)
    except (ValueError, AttributeError):
        return default


def _transfer_count(transfers: List[dict]) -> Tuple[int, int]:
    ctrl  = sum(1 for x in transfers if x.get("type") == "control")
    other = sum(1 for x in transfers if x.get("type") != "control")
    return ctrl, other


def _control_summary(transfers: List[dict]) -> List[str]:
    rows = []
    seen_req = set()
    for xfer in transfers:
        if xfer.get("type") != "control":
            continue
        setup = xfer.get("setup") or {}
        req   = setup.get("bRequest", "?")
        dec   = xfer.get("decoded") or {}
        name  = dec.get("descriptor_name") or dec.get("request") or f"req={req:#04x}"
        key   = (req, name)
        if key not in seen_req:
            seen_req.add(key)
            rows.append(f"| `{setup.get('bmRequestType', '?')}` | `{req:#04x}` | {setup.get('direction', '?')} | {name} |")
    return rows


# ---------------------------------------------------------------------------
# Document generation
# ---------------------------------------------------------------------------

def generate_doc(
    hypothesis: dict,
    captures: List[Tuple[str, List[dict]]],  # (label, transfers)
    capture_paths: List[Tuple[str, str]],    # (label, path)
) -> str:
    dev = hypothesis.get("device", {})
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    vid = dev.get("idVendor", "unknown")
    pid = dev.get("idProduct", "unknown")

    lines = [
        f"# USB Protocol Notes: {vid} / {pid}",
        "",
        f"_Generated {now} by cynthion-reverse-engineer_",
        "",
        "## Device Identity",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| Vendor ID | `{vid}` |",
        f"| Product ID | `{pid}` |",
        f"| USB Spec | `{dev.get('bcdUSB', '?')}` |",
        "",
    ]

    # Captures summary
    lines += ["## Captures", "", "| Label | File | Control xfers | Data xfers |",
              "|-------|------|---------------|------------|"]
    for (label, xfers), (_, path) in zip(captures, capture_paths):
        ctrl, other = _transfer_count(xfers)
        lines.append(f"| {label} | `{Path(path).name}` | {ctrl} | {other} |")
    lines += ["", ""]

    # Control transfer map (from first capture)
    if captures:
        _, first_xfers = captures[0]
        ctrl_rows = _control_summary(first_xfers)
        if ctrl_rows:
            lines += [
                "## Control Transfer Map (EP0)",
                "",
                "| bmRequestType | bRequest | Direction | Name |",
                "|---------------|----------|-----------|------|",
            ]
            lines += ctrl_rows
            lines += ["", ""]

    # Endpoint map
    eps = hypothesis.get("endpoints", [])
    if eps:
        lines += [
            "## Endpoint Map",
            "",
            "| addr | EP | Direction | Frame size | Role |",
            "|------|----|-----------|------------|------|",
        ]
        for ep in eps:
            opcode_offsets = ep.get("opcode_offsets", [])
            role = "command" if opcode_offsets and ep.get("direction") == "OUT" else \
                   "response" if ep.get("direction") == "IN" else "data"
            lines.append(
                f"| {ep.get('addr')} | EP{ep.get('endp')} | {ep.get('direction')} | "
                f"{ep.get('frame_size', '?')} bytes | {role} |"
            )
        lines += ["", ""]

    # Endpoint pairs (command+response)
    pairs = hypothesis.get("endpoint_pairs", [])
    if pairs:
        lines += ["## Endpoint Pairs", ""]
        for pair in pairs:
            lines.append(f"- addr={pair['addr']} EP{pair['endp']}: {pair['note']}")
        lines += ["", ""]

    # Command table per endpoint
    for ep in eps:
        cmds = ep.get("commands", [])
        if not cmds:
            continue
        lines += [
            f"## Commands: addr={ep.get('addr')} EP{ep.get('endp')} {ep.get('direction')}",
            "",
            f"Frame size: {ep.get('frame_size', '?')} bytes · "
            f"Opcode at byte(s): {ep.get('opcode_offsets', [])}",
            "",
            "| Opcode | Seen In | Count | Example payload | Notes |",
            "|--------|---------|-------|-----------------|-------|",
        ]
        for cmd in cmds:
            lines.append(
                f"| `{cmd['opcode']}` | {', '.join(cmd['observed_in_labels'])} | "
                f"{cmd['count']} | `{cmd['example_payload']}` | _TODO_ |"
            )
        lines += ["", ""]

    # Byte role table per endpoint
    for ep in eps:
        roles = ep.get("byte_roles", [])
        if not roles:
            continue
        lines += [
            f"## Byte Roles: EP{ep.get('endp')} {ep.get('direction')}",
            "",
            "| Offset | Role | Notes |",
            "|--------|------|-------|",
        ]
        for b in roles:
            vals = "; ".join(
                f"{lbl}: {' '.join(vs)}"
                for lbl, vs in b.get("values_by_label", {}).items()
            )
            lines.append(f"| {b['offset']} | **{b['role']}** | {vals} |")
        lines += ["", ""]

    # Open questions
    open_qs = hypothesis.get("open_questions", [])
    lines += ["## Open Questions", ""]
    if open_qs:
        for q in open_qs:
            lines.append(f"- [ ] {q}")
    else:
        lines.append("- [ ] _None identified — verify by replaying captures against the device_")
    lines += [
        "- [ ] Confirm endpoint types (bulk vs interrupt) by reading endpoint descriptors",
        "- [ ] Identify CRC/checksum algorithm for varying bytes",
        "- [ ] Test replay script against real hardware",
        "- [ ] Document any class-specific requests",
        "",
    ]

    # Evidence
    lines += [
        "## Evidence",
        "",
        "Captures used in this analysis:",
        "",
    ]
    for (label, _), (_, path) in zip(captures, capture_paths):
        lines.append(f"- **{label}**: `{path}`")
    lines += ["", "_End of auto-generated protocol notes — edit freely._", ""]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(
        description="Generate a Markdown protocol document from hypothesis + captures."
    )
    p.add_argument("hypothesis", help="JSON from infer_commands.py")
    p.add_argument("--capture", nargs=2, metavar=("FILE", "LABEL"), action="append",
                   help="Add a capture: --capture idle.json idle (repeat for each capture)")
    p.add_argument("-o", "--output", help="Output .md file (default: stdout)")
    args = p.parse_args()

    hypothesis = _load(args.hypothesis)
    captures_raw = args.capture or []

    captures: List[Tuple[str, List[dict]]] = []
    capture_paths: List[Tuple[str, str]]  = []
    for path, label in captures_raw:
        with open(path) as f:
            xfers = json.load(f)
        captures.append((label, xfers))
        capture_paths.append((label, path))

    doc = generate_doc(hypothesis, captures, capture_paths)

    if args.output:
        Path(args.output).write_text(doc)
        print(f"Written to {args.output}")
    else:
        print(doc)


if __name__ == "__main__":
    main()
