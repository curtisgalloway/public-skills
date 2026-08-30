#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Curtis Galloway
# SPDX-License-Identifier: Apache-2.0
"""Compare a source-anchored spec against the driver's register headers.

Anchors prove that what the spec says is *somewhere* in the code; they cannot
show what the spec left out, or catch a value that was copied wrong next to a
correct anchor.  This script extracts the register inventory from the headers
at the pinned commit and reports:

  omissions   header names the spec never mentions (cover them, or list them as
              out of scope explicitly)
  mismatches  a spec line that names a header constant next to a single hex
              literal that differs from the header's value
  conflicts   a name the spec itself pairs with two different values

Inventory sources (all regex-based, C-oriented):
  #define NAME <expr containing a hex literal>
  bit-field members:  <type> name : <width>;
  enum members with hex initializers

Device-tree inventory (``--dt FILE --dt-node LABEL_OR_NAME``): the node's
``compatible`` strings, every ``*-names`` string (reg, clock, reset,
power-domain, interrupt, nvmem-cell, phy, pinctrl, …), GIC SPI numbers from
``interrupts``, and the base addresses in ``reg`` — each reported as omitted
when the spec never mentions it.  The unwired interrupt, the clock the spec
forgot, and the window it never names all surface here.

Usage:
  inventory_check.py SPEC --repo PATH[@REV] [--headers a.h b.h]
                          [--dt board.dtsi --dt-node usb_phy] [--all] [--strict]

REV defaults to the spec's ``Source pin:`` (or ``Impl pin:``) line.  Exit 0 clean, 1 mismatches or
conflicts (or omissions under --strict), 2 usage/git error.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

PIN_RE = re.compile(r"^(?:Source|Impl) pin:\s*(?P<name>\S+?)@(?P<rev>[0-9A-Za-z._/-]+)\s*$")
DEFINE_RE = re.compile(r"^\s*#\s*define\s+([A-Za-z_]\w*)\s+(.+?)\s*(?:/[*/].*)?$")
BITFIELD_RE = re.compile(r"^\s*(?:unsigned\s+)?(?:int|long|char|short|u(?:int)?\d+(?:_t)?)\s+([A-Za-z_]\w*)\s*:\s*\d+\s*;")
ENUM_HEX_RE = re.compile(r"^\s*([A-Z_][A-Z0-9_]*)\s*=\s*(0[xX][0-9A-Fa-f_]+)")
HEX_RE = re.compile(r"0[xX][0-9A-Fa-f_]+")
SKIP_NAMES_RE = re.compile(r"^(_+|.*_H_?$|.*_H__$|.*_INCLUDED$)")


def norm_hex(tok: str) -> str:
    return tok[2:].replace("_", "").lower().lstrip("0") or "0"


def git_show(repo: str, rev: str, path: str) -> str | None:
    proc = subprocess.run(["git", "-C", repo, "show", f"{rev}:{path}"],
                          capture_output=True, text=True, errors="replace")
    return proc.stdout if proc.returncode == 0 else None


def extract(text: str) -> tuple[dict[str, str | None], dict[str, str]]:
    """Return ({name: normalized hex or None}, {name: kind})."""
    values: dict[str, str | None] = {}
    kinds: dict[str, str] = {}
    for line in text.split("\n"):
        m = DEFINE_RE.match(line)
        if m and not SKIP_NAMES_RE.match(m.group(1)):
            hexes = HEX_RE.findall(m.group(2))
            values[m.group(1)] = norm_hex(hexes[0]) if len(hexes) == 1 else None
            kinds[m.group(1)] = "define"
            continue
        m = BITFIELD_RE.match(line)
        if m:
            values.setdefault(m.group(1), None)
            kinds.setdefault(m.group(1), "bitfield")
            continue
        m = ENUM_HEX_RE.match(line)
        if m:
            values[m.group(1)] = norm_hex(m.group(2))
            kinds[m.group(1)] = "enum"
    return values, kinds


NAMES_PROP_RE = re.compile(r'^\s*([a-zA-Z0-9_,-]*-names|compatible)\s*=\s*(.+?);', re.S | re.M)
STRING_RE = re.compile(r'"([^"]*)"')
INTERRUPTS_RE = re.compile(r'^\s*interrupts(?:-extended)?\s*=\s*(.+?);', re.S | re.M)
REG_RE = re.compile(r'^\s*reg\s*=\s*(.+?);', re.S | re.M)
GIC_SPI_RE = re.compile(r'GIC_SPI\s+(\d+)')
PHANDLE_RE = re.compile(r'&([A-Za-z_]\w*)')
DT_CONST_RE = re.compile(r'<[^>]*>')
CAPS_CONST_RE = re.compile(r'(?<![A-Za-z0-9_])([A-Z][A-Z0-9_]{3,})(?![A-Za-z0-9_])')
BOOL_PROP_RE = re.compile(r'^\s*([a-z][a-z0-9,-]*);', re.M)


def dt_node_text(dts: str, node: str) -> str | None:
    """Return the body of the first node whose label or name matches `node`."""
    pat = re.compile(r'(?:^|\n)\s*(?:' + re.escape(node) + r'\s*:\s*[\w@,-]+|' + re.escape(node)
                     + r'(?:@[0-9a-fA-F]+)?)\s*\{')
    m = pat.search(dts)
    if not m:
        return None
    depth, i = 0, m.end() - 1
    start = m.end()
    while i < len(dts):
        if dts[i] == "{":
            depth += 1
        elif dts[i] == "}":
            depth -= 1
            if depth == 0:
                return dts[start:i]
        i += 1
    return None


def dt_inventory(body: str) -> dict[str, str]:
    """{item: kind} for the node's names, compatibles, SPIs and reg bases (top level only)."""
    # Drop nested child nodes so their properties are not attributed to this node.
    flat, depth = [], 0
    for ch in body:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        elif depth == 0:
            flat.append(ch)
    text = "".join(flat)
    inv: dict[str, str] = {}
    for m in NAMES_PROP_RE.finditer(text):
        for s_ in STRING_RE.findall(m.group(2)):
            inv[s_] = m.group(1)
    for m in INTERRUPTS_RE.finditer(text):
        for n in GIC_SPI_RE.findall(m.group(1)):
            inv[f"SPI {n}"] = "interrupts"
    for m in REG_RE.finditer(text):
        cells = HEX_RE.findall(m.group(1))
        for h in cells:
            v = norm_hex(h)
            if len(v) >= 5:  # a base address, not a size or a zero high word
                inv["0x" + v] = "reg base"
    for ph in PHANDLE_RE.findall(text):
        inv.setdefault(ph, "phandle")
    for cells in DT_CONST_RE.findall(text):
        for c in CAPS_CONST_RE.findall(cells):
            if c != "GIC_SPI" and not c.startswith("IRQ_TYPE"):
                inv.setdefault(c, "cell constant")
    for prop in BOOL_PROP_RE.findall(text):
        inv.setdefault(prop, "boolean property")
    return inv


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("spec")
    ap.add_argument("--repo", required=True, metavar="PATH[@REV]")
    ap.add_argument("--headers", nargs="+", default=[], metavar="PATH",
                    help="repo-relative header/source files to inventory")
    ap.add_argument("--dt", metavar="PATH", help="repo-relative .dts/.dtsi holding the node")
    ap.add_argument("--dt-node", metavar="LABEL", help="node label (usb_phy) or name (usb_phy@c410000)")
    ap.add_argument("--all", action="store_true", help="list every omission, not the first 40")
    ap.add_argument("--strict", action="store_true", help="omissions are failures too")
    ap.add_argument("--min-name-len", type=int, default=4,
                    help="ignore inventory names shorter than this (default 4)")
    args = ap.parse_args(argv)

    try:
        spec = Path(args.spec).read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    repo, _, rev = args.repo.partition("@")
    if not rev:
        pins = [PIN_RE.match(l.strip()) for l in spec.split("\n")]
        pins = [m for m in pins if m]
        if not pins:
            print("error: --repo has no @rev and the spec has no 'Source pin:'/'Impl pin:' line", file=sys.stderr)
            return 2
        rev = pins[0]["rev"]

    inventory: dict[str, str | None] = {}
    kinds: dict[str, str] = {}
    origin: dict[str, str] = {}
    for h in args.headers:
        text = git_show(repo, rev, h)
        if text is None:
            print(f"error: cannot read {h} at {rev} in {repo}", file=sys.stderr)
            return 2
        v, k = extract(text)
        for name in v:
            if len(name) < args.min_name_len:
                continue
            inventory.setdefault(name, v[name])
            kinds.setdefault(name, k[name])
            origin.setdefault(name, h)

    if not args.headers and not args.dt:
        print("error: give --headers and/or --dt/--dt-node", file=sys.stderr)
        return 2
    if bool(args.dt) != bool(args.dt_node):
        print("error: --dt and --dt-node go together", file=sys.stderr)
        return 2

    dt_items: dict[str, str] = {}
    if args.dt:
        dts = git_show(repo, rev, args.dt)
        if dts is None:
            print(f"error: cannot read {args.dt} at {rev} in {repo}", file=sys.stderr)
            return 2
        body = dt_node_text(dts, args.dt_node)
        if body is None:
            print(f"error: node {args.dt_node!r} not found in {args.dt}", file=sys.stderr)
            return 2
        dt_items = dt_inventory(body)

    spec_lines = spec.split("\n")
    mentions: dict[str, list[int]] = defaultdict(list)
    names_sorted = sorted(inventory, key=len, reverse=True)

    def stems(name: str) -> list[str]:
        # A spec usually names the register, not the header's NAME_OFFSET / NAME_MASK macro.
        out = [name]
        m = re.match(r"^(.*?)_(OFFSET|OFS|ADDR|REG|MASK|MSK|SHIFT|SHFT|POS|BIT)$", name)
        if m and len(m.group(1)) >= args.min_name_len:
            out.append(m.group(1))
        return out

    word_re = {n: re.compile(r"(?<![A-Za-z0-9_])(?:" + "|".join(re.escape(x) for x in stems(n))
                             + r")(?![A-Za-z0-9_])") for n in names_sorted}
    for i, line in enumerate(spec_lines, 1):
        for n in names_sorted:
            if word_re[n].search(line):
                mentions[n].append(i)

    omissions = [n for n in inventory if n not in mentions]
    mismatches = []
    conflicts = []
    for n, lines in mentions.items():
        seen: dict[str, list[int]] = defaultdict(list)
        for i in lines:
            hexes = HEX_RE.findall(spec_lines[i - 1])
            if len(hexes) == 1:
                seen[norm_hex(hexes[0])].append(i)
        hv = inventory[n]
        # Only offset-like macros are compared by value; MASK/SHIFT lines rarely carry one literal.
        if not (kinds[n] == "define" and n.endswith(("_OFFSET", "_OFS", "_ADDR", "_REG"))):
            hv = None
        if hv is not None:
            for v, at in seen.items():
                if v != hv:
                    mismatches.append((n, hv, v, at))
        if len(seen) > 1:
            conflicts.append((n, {v: at for v, at in seen.items()}))

    spec_norm_hex = set()
    for line in spec_lines:
        spec_norm_hex |= {norm_hex(h) for h in HEX_RE.findall(line)}
    dt_omitted = []
    dt_partial = []

    def find_word(w: str) -> int | None:
        m = re.search(r"(?<![A-Za-z0-9_-])" + re.escape(w) + r"(?![A-Za-z0-9_-])", spec)
        return spec.count("\n", 0, m.start()) + 1 if m else None

    for item, kind in dt_items.items():
        if kind == "reg base":
            if item[2:] not in spec_norm_hex:
                dt_omitted.append((item, kind))
            continue
        if find_word(item) is not None:
            continue
        # Specs often drop a namespace prefix (hsio_n_usb2_phy_cfg_pll_fb_div -> pll_fb_div).
        parts = item.split("_")
        hit = None
        for k in range(1, len(parts) - 1):
            tail = "_".join(parts[k:])
            if len(tail) < 8:
                break
            at = find_word(tail)
            if at is not None:
                hit = (tail, at)
                break
        if hit:
            dt_partial.append((item, kind, hit[0], hit[1]))
        else:
            dt_omitted.append((item, kind))

    print(f"spec: {args.spec}")
    print(f"inventory: {len(inventory)} names from {len(args.headers)} file(s) at {rev}"
          + (f"; {len(dt_items)} DT items from node {args.dt_node!r}" if dt_items else ""))
    print(f"mentioned: {len(mentions)}  omitted: {len(omissions)}  "
          f"mismatches: {len(mismatches)}  conflicts: {len(conflicts)}"
          + (f"  DT omitted: {len(dt_omitted)}  DT partial: {len(dt_partial)}" if dt_items else ""))
    for n, hv, v, at in mismatches:
        print(f"MISMATCH {n}: header 0x{hv}, spec 0x{v} at L{','.join(map(str, at))} ({origin[n]})")
    for n, d in conflicts:
        parts = "; ".join(f"0x{v} at L{','.join(map(str, at))}" for v, at in d.items())
        print(f"CONFLICT {n}: {parts}")
    shown = omissions if args.all else omissions[:40]
    for n in shown:
        print(f"omitted  {n} ({kinds[n]}, {origin[n]})")
    if len(omissions) > len(shown):
        print(f"... {len(omissions) - len(shown)} more omissions (use --all)")
    for item, kind, tail, at in dt_partial:
        print(f"partial  DT {kind}: {item} ~ {tail} at L{at}")
    for item, kind in dt_omitted:
        print(f"omitted  DT {kind}: {item}")
    bad = bool(mismatches or conflicts) or (args.strict and bool(omissions or dt_omitted))
    print(f"result: {'FAIL' if bad else 'PASS'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
