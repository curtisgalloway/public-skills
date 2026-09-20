#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Check an ENC28J60 gold ledger against LEDGER-FORMAT.md, and gate its freeze.

Usage:
    python3 ledger_check.py ledger.yaml [--corpus corpus.yaml] [--lock ledger.lock] [--freeze] [--json]

What fails (exit 1):
  * the corpus manifest cannot be found (default: corpus.yaml beside the ledger): without it the
    source and revision checks would silently not run, so its absence is an error, never a skip
  * a row without one of the required fields, or with an id that does not match
    ENC28J60-<FACET>-<NNN> for a facet LEDGER-FORMAT.md defines; a duplicate id
  * a class, weight, or status outside the vocabulary; a statement that is not a non-empty string
  * an inference row without a non-empty premises list, a confidence, and a settled_by
  * a derivation entry whose source is not a pin the corpus manifest names (an edition id such as
    DS80349C, a driver path, or the driver commit), or whose locator is empty, not a string, or a
    bare page reference (a page is an edition's property; the locator has to survive the edition)
  * an applicability block missing one of its three columns, a vendor_confirmed revision the corpus
    does not know, or a non-boolean implementation_observed or unresolved
  * a withdrawn row, an out-of-scope row, or an unrecoverable row without notes saying why
  * a readers list that is not a list of distinct names
  * with --lock: a lock without a frozen date, a lock whose ledger sha256 differs from the file
    (the ledger was edited after freezing), or a lock whose corpus sha256 differs from the
    manifest the check ran against
  * with --freeze: any row still carrying a provisional merge marker (weight_disputed,
    class_disputed, in_scope_disputed) or an active row whose notes say it overlaps another
    active row without a disposition; a critical active row with fewer than two distinct readers
    and no `independent_review` note. The freeze gate is what LEDGER-FORMAT.md rule 5 means by
    "frozen": nothing provisional, nothing double-counted, every critical row read twice.

What warns (reported, exit stays 0):
  * a gap in a facet's numbering with no withdrawn row to account for it
  * an unresolved-conflict row whose statement does not present both readings
  * extra keys on a row beyond the schema and the merge conventions (typos hide here)

Beyond LEDGER-FORMAT.md's explicit schema this checker also requires the header keys the authoring
brief asked for (pilot, corpus_frozen, authored, author, authoring_rule); they are what a score
report cites.

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
OPTIONAL = (
    "notes", "premises", "confidence", "settled_by", "readers", "weight_disputed", "class_disputed",
    "in_scope_disputed", "replaced_by", "supersedes", "independent_review", "overlaps",
)
APPLICABILITY = ("vendor_confirmed", "implementation_observed", "unresolved")
PROVISIONAL = ("weight_disputed", "class_disputed", "in_scope_disputed")
PAGE_ONLY_RE = re.compile(r"^\s*(?:p{1,2}\.?|pages?)?\s*\d+(?:\s*[-–]\s*\d+)?\s*$", re.IGNORECASE)
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


def corpus_sources(corpus: dict) -> tuple[set[str], set[str]]:
    """The derivation sources a row may cite, and the silicon revisions it may name."""
    sources: set[str] = set()
    docs = corpus.get("documents", {}) or {}
    for key in ("datasheet", "errata"):
        doc = docs.get(key, {}) or {}
        for ed in doc.get("editions", []) or []:
            sources.add(f"{doc.get('id')}{ed.get('rev')}")
    driver = corpus.get("driver", {}) or {}
    for f in driver.get("files", []) or []:
        sources.add(str(f.get("path")))
    if driver.get("commit"):
        sources.add(str(driver["commit"]))
    revisions = set((corpus.get("silicon_revisions", {}) or {}).get("values", {}) or {})
    return sources, revisions


def _nonempty_str(v) -> bool:
    return isinstance(v, str) and bool(v.strip())


def check(
    ledger: dict,
    corpus: dict,
    ledger_bytes: bytes,
    corpus_bytes: bytes,
    lock: dict | None = None,
    freeze: bool = False,
) -> tuple[list[str], list[str], dict]:
    errors: list[str] = []
    warnings: list[str] = []
    sources, revisions = corpus_sources(corpus)
    if not sources:
        errors.append("corpus: manifest names no sources; nothing to validate derivations against")

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
    counts: dict = {"rows": 0, "active": 0, "class": {}, "weight": {}, "facet": {}, "in_scope": 0, "recoverable": 0, "readers_both": 0, "provisional": 0}

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
        extra = sorted(k for k in row if k not in REQUIRED and k not in OPTIONAL)
        if extra:
            warnings.append(f"{where}: unexpected keys {extra}")
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
        status = row.get("status")
        notes_ok = _nonempty_str(row.get("notes"))
        if cls not in CLASSES:
            errors.append(f"{where}: class {cls!r} not in {CLASSES}")
        if row.get("weight") not in WEIGHTS:
            errors.append(f"{where}: weight {row.get('weight')!r} not in {WEIGHTS}")
        if status not in STATUSES:
            errors.append(f"{where}: status {status!r} not in {STATUSES}")
        if status == "withdrawn" and not notes_ok:
            errors.append(f"{where}: withdrawn without notes saying why")
        for key in ("in_scope", "recoverable"):
            if key in row and not isinstance(row[key], bool):
                errors.append(f"{where}: {key} must be a boolean")
        if row.get("in_scope") is False and not notes_ok:
            errors.append(f"{where}: in_scope false without notes saying why")
        if row.get("recoverable") is False and not notes_ok:
            errors.append(f"{where}: recoverable false without notes saying why")
        if not _nonempty_str(row.get("statement")):
            errors.append(f"{where}: statement must be a non-empty string")
        if cls == "inference":
            prem = row.get("premises")
            if not isinstance(prem, list) or not prem or not all(_nonempty_str(p) for p in prem):
                errors.append(f"{where}: inference row needs a non-empty premises list of strings")
            for key in ("confidence", "settled_by"):
                if not _nonempty_str(row.get(key)):
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
                if str(d["source"]) not in sources:
                    errors.append(f"{where}: derivation[{j}] source {d['source']!r} is not a corpus pin")
                loc = d["locator"]
                if isinstance(loc, (int, float)) and not isinstance(loc, bool):
                    errors.append(f"{where}: derivation[{j}] locator is a bare page reference")
                elif not _nonempty_str(loc):
                    errors.append(f"{where}: derivation[{j}] locator must be a non-empty string")
                elif PAGE_ONLY_RE.match(loc):
                    errors.append(f"{where}: derivation[{j}] locator is a bare page reference")

        app = row.get("applicability")
        if not isinstance(app, dict):
            errors.append(f"{where}: applicability must be a mapping with {APPLICABILITY}")
        else:
            for key in APPLICABILITY:
                if key not in app:
                    errors.append(f"{where}: applicability missing {key!r}")
            extra_app = sorted(k for k in app if k not in APPLICABILITY)
            if extra_app:
                warnings.append(f"{where}: applicability has extra keys {extra_app}")
            vc = app.get("vendor_confirmed")
            if not isinstance(vc, list):
                errors.append(f"{where}: applicability.vendor_confirmed must be a list")
            else:
                for rev in vc:
                    if rev not in revisions:
                        errors.append(f"{where}: applicability.vendor_confirmed names unknown revision {rev!r}")
            for key in ("implementation_observed", "unresolved"):
                if key in app and not isinstance(app.get(key), bool):
                    errors.append(f"{where}: applicability.{key} must be a boolean")

        readers = row.get("readers")
        if readers is not None:
            if not isinstance(readers, list) or not all(_nonempty_str(r) for r in readers):
                errors.append(f"{where}: readers must be a list of names")
            elif len(set(readers)) != len(readers):
                errors.append(f"{where}: readers lists the same reader twice")
        n_readers = len(set(readers)) if isinstance(readers, list) else 0

        provisional = [k for k in PROVISIONAL if k in row]
        if provisional:
            counts["provisional"] += 1
        if freeze and status == "active":
            if provisional:
                errors.append(f"{where}: freeze: provisional markers still present {provisional}")
            if row.get("overlaps") and not row.get("replaced_by"):
                errors.append(f"{where}: freeze: overlaps {row.get('overlaps')} with no disposition")
            if row.get("weight") == "critical" and n_readers < 2 and not _nonempty_str(row.get("independent_review")):
                errors.append(f"{where}: freeze: critical row with fewer than two readers and no independent_review")

        counts["rows"] += 1
        if status == "active":
            counts["active"] += 1
        counts["class"][cls] = counts["class"].get(cls, 0) + 1
        counts["weight"][row.get("weight")] = counts["weight"].get(row.get("weight"), 0) + 1
        if row.get("in_scope") is True:
            counts["in_scope"] += 1
        if row.get("recoverable") is True:
            counts["recoverable"] += 1
        if n_readers >= 2:
            counts["readers_both"] += 1

    for facet, nums in per_facet.items():
        if not nums:
            continue
        expected = set(range(1, max(nums) + 1))
        gaps = expected - set(nums) - withdrawn_per_facet[facet]
        if gaps:
            warnings.append(f"{facet}: numbering gap at {sorted(gaps)} with no withdrawn row to account for it")

    digest = hashlib.sha256(ledger_bytes).hexdigest()
    corpus_digest = hashlib.sha256(corpus_bytes).hexdigest()
    counts["sha256"] = digest
    counts["corpus_sha256"] = corpus_digest
    if lock is not None:
        if not isinstance(lock, dict):
            errors.append("lock: not a mapping")
        else:
            if not lock.get("frozen"):
                errors.append("lock: missing frozen date")
            if lock.get("sha256") != digest:
                errors.append(f"lock: ledger sha256 {digest[:12]}... differs from lock {str(lock.get('sha256'))[:12]}...; the ledger was edited after freezing")
            if lock.get("corpus_sha256") != corpus_digest:
                errors.append(f"lock: corpus sha256 {corpus_digest[:12]}... differs from lock {str(lock.get('corpus_sha256'))[:12]}...; the manifest is not the one frozen with the ledger")
            counts["frozen"] = lock.get("frozen")
    return errors, warnings, counts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("ledger", type=Path)
    ap.add_argument("--corpus", type=Path, help="corpus.yaml; defaults to the one beside the ledger")
    ap.add_argument("--lock", type=Path, help="freeze record with frozen, sha256, and corpus_sha256")
    ap.add_argument("--freeze", action="store_true", help="also apply the freeze gate: no provisional rows, no undisposed overlaps, every critical row read twice")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    ledger_bytes = args.ledger.read_bytes()
    ledger = load_yaml(args.ledger)
    corpus_path = args.corpus or args.ledger.parent / "corpus.yaml"
    if not corpus_path.exists():
        print(f"ledger_check: corpus manifest not found at {corpus_path}; pass --corpus", file=sys.stderr)
        return 1
    corpus_bytes = corpus_path.read_bytes()
    corpus = load_yaml(corpus_path)
    lock = load_yaml(args.lock) if args.lock else None

    errors, warnings, counts = check(ledger, corpus, ledger_bytes, corpus_bytes, lock=lock, freeze=args.freeze)
    if args.json:
        json.dump({"errors": errors, "warnings": warnings, "counts": counts}, sys.stdout, indent=1)
        print()
    else:
        for w in warnings:
            print(f"warning: {w}")
        for e in errors:
            print(f"error: {e}")
        status = "FAIL" if errors else "OK"
        print(f"{status}: {counts.get('rows', 0)} rows ({counts.get('active', 0)} active, {counts.get('provisional', 0)} provisional), {len(errors)} error(s), {len(warnings)} warning(s); sha256 {counts.get('sha256', '')[:12]}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
