#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Check an ENC28J60 gold ledger against LEDGER-FORMAT.md, and optionally against its freeze lock.

Usage:
    python3 ledger_check.py ledger.yaml [--lock ledger.lock] [--corpus corpus.yaml] [--json]

What fails (exit 1):
  * a row without one of the required fields, or with an id that does not match
    ENC28J60-<FACET>-<NNN> for a facet LEDGER-FORMAT.md defines
  * a duplicate id
  * a class, weight, or status outside the vocabulary
  * an inference row without premises, confidence, and settled_by
  * a derivation entry whose source is not a pin the corpus manifest names, or whose locator is a
    bare page number (a page is an edition's property; the locator has to survive the edition)
  * an applicability block that does not have exactly the three columns, or a vendor_confirmed
    revision the corpus does not know
  * a withdrawn row without notes saying why
  * with --lock, a ledger whose sha256 differs from the lock: the ledger was edited after freezing

What warns (reported, exit stays 0):
  * a gap in a facet's numbering with no withdrawn row to account for it
  * an unresolved-conflict row whose statement does not present both readings

Exit 3: the file could not be parsed, or PyYAML is not importable. The ledger uses block
scalars and nested mappings, so this checker needs a real YAML parser:
    uv run --with pyyaml python3 ledger_check.py ledger.yaml
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

FACETS = ("REG", "INIT", "TX", "RX", "IRQ", "PHY", "SPI", "ELEC", "ERR")
ID_RE = re.compile(r"^ENC28J60-(" + "|".join(FACETS) + r")-(\d{3})$")
CLASSES = (
    "documented-hardware-requirement",
    "observed-software-behavior",
    "inference",
    "implementation-choice",
    "unresolved-conflict",
)
WEIGHTS = ("critical", "important", "minor")
STATUSES = ("active", "withdrawn")
REQUIRED = ("id", "statement", "class", "derivation", "applicability", "weight", "in_scope", "recoverable", "status")
APPLICABILITY = ("vendor_confirmed", "implementation_observed", "unresolved")
PAGE_ONLY_RE = re.compile(r"^\s*(p\.?|page)\s*\d+\s*$", re.IGNORECASE)
HEADER = ("pilot", "corpus_frozen", "authored", "author", "authoring_rule")


def load_yaml(path: Path):
    try:
        import yaml  # type: ignore
    except ImportError:
        print("ledger_check: PyYAML is not importable; run with `uv run --with pyyaml python3 ...`", file=sys.stderr)
        sys.exit(3)
    try:
        with path.open(encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as exc:  # noqa: BLE001 - report any parse failure the same way
        print(f"ledger_check: {path}: does not parse: {exc}", file=sys.stderr)
        sys.exit(3)


def corpus_sources(corpus: dict | None) -> tuple[set[str], set[str]]:
    """The derivation sources a row may cite, and the silicon revisions it may name."""
    if not corpus:
        return set(), set()
    sources: set[str] = set()
    docs = corpus.get("documents", {})
    for key in ("datasheet", "errata"):
        doc = docs.get(key, {})
        for ed in doc.get("editions", []):
            sources.add(f"{doc.get('id')}{ed.get('rev')}")
    for f in corpus.get("driver", {}).get("files", []):
        sources.add(f.get("path"))
    revisions = set(corpus.get("silicon_revisions", {}).get("values", {}).keys())
    return sources, revisions


def check(ledger: dict, corpus: dict | None, lock: dict | None, ledger_bytes: bytes) -> tuple[list[str], list[str], dict]:
    errors: list[str] = []
    warnings: list[str] = []
    sources, revisions = corpus_sources(corpus)

    if not isinstance(ledger, dict):
        return ["ledger is not a mapping"], [], {}
    for key in HEADER:
        if key not in ledger:
            errors.append(f"header: missing {key!r}")
    rows = ledger.get("rows")
    if not isinstance(rows, list):
        return errors + ["rows: missing or not a list"], warnings, {}

    seen: dict[str, int] = {}
    per_facet: dict[str, list[int]] = {f: [] for f in FACETS}
    withdrawn_per_facet: dict[str, set[int]] = {f: set() for f in FACETS}
    counts = {"rows": 0, "class": {}, "weight": {}, "facet": {}, "in_scope": 0, "recoverable": 0, "readers_both": 0}

    for i, row in enumerate(rows):
        where = f"rows[{i}]"
        if not isinstance(row, dict):
            errors.append(f"{where}: not a mapping")
            continue
        rid = str(row.get("id", ""))
        where = rid or where
        for key in REQUIRED:
            if key not in row:
                errors.append(f"{where}: missing {key!r}")
        m = ID_RE.match(rid)
        if not m:
            errors.append(f"{where}: id does not match ENC28J60-<FACET>-<NNN>")
        else:
            facet, num = m.group(1), int(m.group(2))
            per_facet[facet].append(num)
            counts["facet"][facet] = counts["facet"].get(facet, 0) + 1
            if row.get("status") == "withdrawn":
                withdrawn_per_facet[facet].add(num)
        if rid in seen:
            errors.append(f"{where}: duplicate id (also rows[{seen[rid]}])")
        seen[rid] = i

        cls = row.get("class")
        if cls not in CLASSES:
            errors.append(f"{where}: class {cls!r} not in {CLASSES}")
        if row.get("weight") not in WEIGHTS:
            errors.append(f"{where}: weight {row.get('weight')!r} not in {WEIGHTS}")
        if row.get("status") not in STATUSES:
            errors.append(f"{where}: status {row.get('status')!r} not in {STATUSES}")
        if row.get("status") == "withdrawn" and not str(row.get("notes", "")).strip():
            errors.append(f"{where}: withdrawn without notes saying why")
        for key in ("in_scope", "recoverable"):
            if key in row and not isinstance(row[key], bool):
                errors.append(f"{where}: {key} must be a boolean")
        if not str(row.get("statement", "")).strip():
            errors.append(f"{where}: empty statement")
        if cls == "inference":
            for key in ("premises", "confidence", "settled_by"):
                if not row.get(key):
                    errors.append(f"{where}: inference row without {key!r}")
        if cls == "unresolved-conflict":
            s = str(row.get("statement", ""))
            if not re.search(r"reader\s+[AB]", s, re.IGNORECASE) and " vs " not in s and "disagree" not in s.lower():
                warnings.append(f"{where}: unresolved-conflict statement does not present both readings")

        der = row.get("derivation")
        if not isinstance(der, list) or not der:
            errors.append(f"{where}: derivation must be a non-empty list")
        else:
            for j, d in enumerate(der):
                if not isinstance(d, dict) or "source" not in d or "locator" not in d:
                    errors.append(f"{where}: derivation[{j}] needs source and locator")
                    continue
                if sources and d["source"] not in sources:
                    errors.append(f"{where}: derivation[{j}] source {d['source']!r} is not a corpus pin")
                if PAGE_ONLY_RE.match(str(d["locator"])):
                    errors.append(f"{where}: derivation[{j}] locator is a bare page number")

        app = row.get("applicability")
        if not isinstance(app, dict) or tuple(sorted(app)) != tuple(sorted(APPLICABILITY)):
            errors.append(f"{where}: applicability must have exactly {APPLICABILITY}")
        else:
            vc = app.get("vendor_confirmed")
            if not isinstance(vc, list):
                errors.append(f"{where}: applicability.vendor_confirmed must be a list")
            elif revisions:
                for rev in vc:
                    if rev not in revisions:
                        errors.append(f"{where}: applicability.vendor_confirmed names unknown revision {rev!r}")
            for key in ("implementation_observed", "unresolved"):
                if not isinstance(app.get(key), bool):
                    errors.append(f"{where}: applicability.{key} must be a boolean")

        counts["rows"] += 1
        counts["class"][cls] = counts["class"].get(cls, 0) + 1
        counts["weight"][row.get("weight")] = counts["weight"].get(row.get("weight"), 0) + 1
        if row.get("in_scope") is True:
            counts["in_scope"] += 1
        if row.get("recoverable") is True:
            counts["recoverable"] += 1
        if isinstance(row.get("readers"), list) and len(row["readers"]) >= 2:
            counts["readers_both"] += 1

    for facet, nums in per_facet.items():
        if not nums:
            continue
        expected = set(range(1, max(nums) + 1))
        gaps = expected - set(nums) - withdrawn_per_facet[facet]
        if gaps:
            warnings.append(f"{facet}: numbering gap at {sorted(gaps)} with no withdrawn row to account for it")

    digest = hashlib.sha256(ledger_bytes).hexdigest()
    counts["sha256"] = digest
    if lock is not None:
        if lock.get("sha256") != digest:
            errors.append(f"lock: ledger sha256 {digest[:12]}... differs from lock {str(lock.get('sha256'))[:12]}...; the ledger was edited after freezing")
        counts["frozen"] = lock.get("frozen")
    return errors, warnings, counts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("ledger", type=Path)
    ap.add_argument("--lock", type=Path, help="freeze record with sha256 and frozen date")
    ap.add_argument("--corpus", type=Path, help="corpus.yaml; defaults to the one beside the ledger if present")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    ledger_bytes = args.ledger.read_bytes()
    ledger = load_yaml(args.ledger)
    corpus_path = args.corpus or args.ledger.parent / "corpus.yaml"
    corpus = load_yaml(corpus_path) if corpus_path.exists() else None
    lock = load_yaml(args.lock) if args.lock else None

    errors, warnings, counts = check(ledger, corpus, lock, ledger_bytes)
    if args.json:
        json.dump({"errors": errors, "warnings": warnings, "counts": counts}, sys.stdout, indent=1)
        print()
    else:
        for w in warnings:
            print(f"warning: {w}")
        for e in errors:
            print(f"error: {e}")
        status = "FAIL" if errors else "OK"
        print(f"{status}: {counts.get('rows', 0)} rows, {len(errors)} error(s), {len(warnings)} warning(s); sha256 {counts.get('sha256', '')[:12]}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
