#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Check an ENC28J60 gold ledger against LEDGER-FORMAT.md, and gate its freeze.

Usage:
    python3 ledger_check.py ledger.yaml [--corpus corpus.yaml] [--policy SCORING-POLICY.md]
                           [--format LEDGER-FORMAT.md] [--facts SCORING-FACTS.md]
                           [--lock ledger.lock] [--freeze] [--json]

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
    (the ledger was edited after freezing), a lock whose corpus sha256 differs from the manifest
    the check ran against, or a lock whose policy version or policy sha256 differs from the
    scoring policy on disk, or a lock missing or disagreeing with the digests of
    LEDGER-FORMAT.md and SCORING-FACTS.md, or missing a repository revision. A version label on a
    file anyone can edit binds nothing, so the lock pins the bytes of every file a score depends
    on, and the revision is how someone gets those bytes back.
  * a composite scoring unit the policy names with no fact count, a count below two, a unit with
    no list in SCORING-FACTS.md, a list whose length disagrees with its own printed count or with
    the policy's table, or a list for a row the policy does not call composite. Those counts are
    the denominators of proportional partial credit, so a wrong one is a wrong score.
  * with --freeze: the scoring policy is missing or declares no `Version:` line. Which classes
    are in the recall denominator has to be settled and named before a candidate exists, so a
    freeze without a policy is refused.
  * with --freeze: any row still carrying a provisional merge marker (weight_disputed,
    class_disputed, in_scope_disputed) or an active row carrying an `overlaps:` list without a
    `replaced_by:` disposition; a critical active row with fewer than two distinct readers and no
    structured `independent_review` (a mapping with `reviewer` not among the row's readers, a
    non-empty `locators` list, and a `disposition`; a bare note does not count). This is the
    mechanical half of what LEDGER-FORMAT.md rule 5 means by "frozen": nothing provisional,
    nothing double-counted, every critical row read twice. It cannot establish blind authorship,
    semantic deduplication, or the adequacy of a review; those are the adjudicator's attestation
    in the lock, which the checker only records.

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
POLICY_VERSION_RE = re.compile(r"^Version:\s*(\S+)\s*$", re.MULTILINE)


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


def policy_identity(policy_bytes: bytes | None) -> tuple[str | None, str | None]:
    """The scoring policy's declared version and the hash of its bytes."""
    if policy_bytes is None:
        return None, None
    m = POLICY_VERSION_RE.search(policy_bytes.decode("utf-8", "replace"))
    return (m.group(1) if m else None), hashlib.sha256(policy_bytes).hexdigest()


def composite_ids(policy_bytes: bytes | None) -> tuple[set[str], int | None]:
    """The ids the policy names as composite scoring units, and the total it claims.

    The policy writes them without the device prefix (``REG-008``), in one section. Parsing them
    is what lets the checker refuse a list that has drifted from the ledger: the policy asserts
    the inventory is exhaustive as of a date, and an id that no longer exists, or that names a
    withdrawn row, is the first sign that assertion has gone stale.
    """
    if policy_bytes is None:
        return set(), None
    text = policy_bytes.decode("utf-8", "replace")
    m = re.search(r"^##\s+Composite scoring units\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    if not m:
        return set(), None
    section = m.group(1)
    # Only the table rows are the list. The section's prose names withdrawn rows when it explains
    # why something was not split, and those are commentary, not entries.
    ids: set[str] = set()
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|") or "Total" in line or line.startswith("|---"):
            continue
        ids |= {f"ENC28J60-{t}" for t in re.findall(r"\b(?:" + "|".join(FACETS) + r")-\d{3}\b", line)}
    total = re.search(r"\*\*Total\*\*\s*\|[^|]*\|\s*\*\*(\d+)\*\*", section)
    return ids, (int(total.group(1)) if total else None)


def policy_fact_counts(policy_bytes: bytes | None) -> dict[str, int]:
    """Each composite unit's frozen fact count, from the policy's table."""
    if policy_bytes is None:
        return {}
    text = policy_bytes.decode("utf-8", "replace")
    m = re.search(r"^##\s+Composite scoring units\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    if not m:
        return {}
    out: dict[str, int] = {}
    for line in m.group(1).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        rid = re.fullmatch(r"(?:ENC28J60-)?((?:" + "|".join(FACETS) + r")-\d{3})", cells[0])
        n = re.fullmatch(r"\*{0,2}(\d+)\*{0,2}", cells[-1])
        if rid and n:
            out[f"ENC28J60-{rid.group(1)}"] = int(n.group(1))
    return out


def facts_lists(facts_bytes: bytes | None) -> tuple[dict[str, tuple[int, int | None]], list[str], list[str]]:
    """Per unit, the number of listed facts and the count the file declares beside them.

    The file is a scoring checklist: one `### <id>` section per composite unit, an ordered list,
    and a `Count: N` the list length must equal. Parsing it is what stops the three numbers, the
    list, its printed count and the policy's table, from drifting apart once they are frozen.
    """
    if facts_bytes is None:
        return {}, [], []
    text = facts_bytes.decode("utf-8", "replace")
    out: dict[str, tuple[int, int | None]] = {}
    dups: list[str] = []
    misnumbered: list[str] = []
    parts = re.split(r"^###\s+(?:ENC28J60-)?((?:" + "|".join(FACETS) + r")-\d{3})\b", text, flags=re.M)
    for i in range(1, len(parts) - 1, 2):
        rid, body = f"ENC28J60-{parts[i]}", parts[i + 1]
        numbers = [int(n) for n in re.findall(r"^\s*(\d+)\.\s+\S", body, re.M)]
        if numbers != list(range(1, len(numbers) + 1)):
            misnumbered.append(rid)
        declared = re.search(r"Count:\s*(\d+)", body)
        if rid in out:
            dups.append(rid)
        out[rid] = (len(numbers), int(declared.group(1)) if declared else None)
    return out, dups, misnumbered


def facts_text(facts_bytes: bytes | None) -> dict[str, tuple[list[str], str]]:
    """Each composite unit's ordered fact entries and its unit-level prose, as frozen.

    A review template copies both beside the numbered dispositions so a reader judges a fact it
    can see. The copy is never a second authority: this map is re-derived from the frozen bytes
    and a review whose text differs is refused rather than scored.

    The prose is carried because SCORING-FACTS.md ("How a list works") assigns requirements in
    unit-level sentences as well as in entries: INIT-015's two MABBIPG values carry the IEEE
    minimum gap that only the sentence below them names. An entry list alone is a weaker
    obligation than the frozen one, so copying only the entries would hand a reviewer a second,
    looser reading of the answer key.
    """
    if facts_bytes is None:
        return {}
    text = facts_bytes.decode("utf-8", "replace")
    out: dict[str, tuple[list[str], str]] = {}
    parts = re.split(r"^###\s+(?:ENC28J60-)?((?:" + "|".join(FACETS) + r")-\d{3})\b", text, flags=re.M)
    for i in range(1, len(parts) - 1, 2):
        rid, body = f"ENC28J60-{parts[i]}", parts[i + 1]
        entries, prose = [], []
        for line in body.splitlines():
            m = re.match(r"^\s*\d+\.\s+(\S.*)$", line)
            if m:
                entries.append(m.group(1).strip())
            elif line.strip() and not line.startswith("#"):
                prose.append(line.strip())
        # The heading line's trailing title is not prose; the split consumed the id, so drop the
        # remainder of that first line and keep everything the unit says under its list.
        if prose and prose[0].startswith("—"):
            prose.pop(0)
        out[rid] = (entries, "\n".join(prose))
    return out


def check(
    ledger: dict,
    corpus: dict,
    ledger_bytes: bytes,
    corpus_bytes: bytes,
    lock: dict | None = None,
    freeze: bool = False,
    policy_bytes: bytes | None = None,
    format_bytes: bytes | None = None,
    facts_bytes: bytes | None = None,
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
            if row.get("weight") == "critical" and n_readers < 2:
                ir = row.get("independent_review")
                ok = (
                    isinstance(ir, dict)
                    and _nonempty_str(ir.get("reviewer"))
                    and ir.get("reviewer") not in (readers or [])
                    and isinstance(ir.get("locators"), list)
                    and ir["locators"]
                    and all(_nonempty_str(x) for x in ir["locators"])
                    and _nonempty_str(ir.get("disposition"))
                )
                if not ok:
                    errors.append(
                        f"{where}: freeze: critical row with fewer than two readers needs a structured "
                        "independent_review (reviewer not among readers, locators list, disposition)"
                    )

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
    policy_version, policy_digest = policy_identity(policy_bytes)
    format_digest = hashlib.sha256(format_bytes).hexdigest() if format_bytes is not None else None
    facts_digest = hashlib.sha256(facts_bytes).hexdigest() if facts_bytes is not None else None
    counts["sha256"] = digest
    counts["corpus_sha256"] = corpus_digest
    counts["policy_version"] = policy_version
    counts["policy_sha256"] = policy_digest
    counts["format_sha256"] = format_digest
    counts["facts_sha256"] = facts_digest
    comp_ids, comp_total = composite_ids(policy_bytes)
    counts["composite_units"] = len(comp_ids)
    if comp_ids:
        active_ids = {r["id"] for r in rows if isinstance(r, dict) and r.get("status") == "active"}
        all_ids = {r["id"] for r in rows if isinstance(r, dict)}
        for cid in sorted(comp_ids - all_ids):
            errors.append(f"policy: composite list names {cid}, which is not a row in this ledger")
        for cid in sorted((comp_ids & all_ids) - active_ids):
            errors.append(f"policy: composite list names {cid}, which is withdrawn")
        if comp_total is not None and comp_total != len(comp_ids):
            errors.append(f"policy: composite list prints a total of {comp_total} but names {len(comp_ids)} distinct ids")
        # The fact counts are the denominators of proportional partial credit, so they are
        # checked the way the id list is: a count that is absent, below two, or disagrees with
        # the list that justifies it is a wrong score waiting to happen.
        pol_counts = policy_fact_counts(policy_bytes)
        lists, dup_lists, misnumbered = facts_lists(facts_bytes)
        for rid in sorted(set(dup_lists)):
            errors.append(f"facts: {rid} has more than one fact list; a unit has exactly one")
        for rid in sorted(set(misnumbered)):
            errors.append(f"facts: {rid}'s entries are not numbered 1..n; reports name a missed fact by its number")
        for cid in sorted(comp_ids):
            n = pol_counts.get(cid)
            if n is None:
                errors.append(f"policy: composite unit {cid} has no fact count")
            elif n < 2:
                errors.append(f"policy: composite unit {cid} declares {n} fact(s); a composite has at least two")
            if facts_bytes is None:
                continue
            if cid not in lists:
                errors.append(f"facts: composite unit {cid} has no fact list")
                continue
            items, declared = lists[cid]
            if declared is None:
                errors.append(f"facts: {cid} prints no count beside its list")
            elif declared != items:
                errors.append(f"facts: {cid} lists {items} fact(s) but prints a count of {declared}")
            if n is not None and items != n:
                errors.append(f"facts: {cid} lists {items} fact(s) but the policy's table says {n}")
        for extra in sorted(set(lists) - comp_ids):
            errors.append(f"facts: {extra} has a fact list but is not a composite unit in the policy")
        counts["listed_facts"] = sum(i for i, _ in lists.values())
    if facts_bytes is not None and not comp_ids:
        errors.append("facts: a fact list exists but the policy names no composite units to match it against")
    if freeze:
        if policy_bytes is None:
            errors.append("freeze: no scoring policy; which classes are in the recall denominator must be named before a candidate exists")
        elif not policy_version:
            errors.append("freeze: the scoring policy declares no 'Version:' line, so a lock cannot name a version")
        elif not comp_ids:
            errors.append("freeze: the scoring policy names no composite scoring units; a policy whose bounded exception is empty cannot be checked against the ledger")
        elif facts_bytes is None:
            errors.append("freeze: the policy names composite scoring units but there is no SCORING-FACTS.md; a frozen count without its fact list fixes a denominator and leaves the numerator to the scorer")
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
            if policy_bytes is None:
                errors.append("lock: no scoring policy on disk to check the lock's policy fields against")
            else:
                # Both sides must be present. Comparing two absent versions succeeds by accident,
                # which is how an unversioned policy could once pass a lock check.
                if not policy_version:
                    errors.append("lock: the scoring policy on disk declares no 'Version:' line")
                if not _nonempty_str(lock.get("policy_version")):
                    errors.append("lock: missing policy_version")
                elif lock.get("policy_version") != policy_version:
                    errors.append(f"lock: policy version {policy_version!r} on disk differs from lock {lock.get('policy_version')!r}")
                if not _nonempty_str(lock.get("policy_sha256")):
                    errors.append("lock: missing policy_sha256")
                elif lock.get("policy_sha256") != policy_digest:
                    errors.append(f"lock: policy sha256 {str(policy_digest)[:12]}... differs from lock {str(lock.get('policy_sha256'))[:12]}...; the policy was edited after freezing")
            if not _nonempty_str(lock.get("format_sha256")):
                errors.append("lock: missing format_sha256; LEDGER-FORMAT.md supplies the verdict definitions the policy refers to, so its bytes are pinned too")
            elif format_bytes is None:
                errors.append("lock: no LEDGER-FORMAT.md on disk to check the lock's format_sha256 against")
            elif lock.get("format_sha256") != format_digest:
                errors.append(f"lock: format sha256 {str(format_digest)[:12]}... differs from lock {str(lock.get('format_sha256'))[:12]}...; LEDGER-FORMAT.md was edited after freezing")
            if not _nonempty_str(lock.get("facts_sha256")):
                errors.append("lock: missing facts_sha256; SCORING-FACTS.md holds the denominators of proportional partial credit, so its bytes are pinned too")
            elif facts_bytes is None:
                errors.append("lock: no SCORING-FACTS.md on disk to check the lock's facts_sha256 against")
            elif lock.get("facts_sha256") != facts_digest:
                errors.append(f"lock: facts sha256 {str(facts_digest)[:12]}... differs from lock {str(lock.get('facts_sha256'))[:12]}...; SCORING-FACTS.md was edited after freezing")
            if not _nonempty_str(lock.get("revision")):
                errors.append("lock: missing revision; a digest identifies bytes, a repository revision makes them recoverable")
            counts["frozen"] = lock.get("frozen")
    return errors, warnings, counts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("ledger", type=Path)
    ap.add_argument("--corpus", type=Path, help="corpus.yaml; defaults to the one beside the ledger")
    ap.add_argument("--policy", type=Path, help="the scoring policy; defaults to SCORING-POLICY.md beside the ledger")
    ap.add_argument("--format", type=Path, help="the ledger format; defaults to LEDGER-FORMAT.md beside the ledger")
    ap.add_argument("--facts", type=Path, help="the credit-bearing fact lists; defaults to SCORING-FACTS.md beside the ledger")
    ap.add_argument("--lock", type=Path, help="freeze record with frozen, sha256, corpus_sha256, policy_version, policy_sha256")
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
    policy_path = args.policy or args.ledger.parent / "SCORING-POLICY.md"
    if args.policy and not policy_path.exists():
        print(f"ledger_check: scoring policy not found at {policy_path}", file=sys.stderr)
        return 1
    policy_bytes = policy_path.read_bytes() if policy_path.exists() else None
    format_path = args.format or args.ledger.parent / "LEDGER-FORMAT.md"
    format_bytes = format_path.read_bytes() if format_path.exists() else None
    facts_path = args.facts or args.ledger.parent / "SCORING-FACTS.md"
    facts_bytes = facts_path.read_bytes() if facts_path.exists() else None

    errors, warnings, counts = check(
        ledger, corpus, ledger_bytes, corpus_bytes, lock=lock, freeze=args.freeze,
        policy_bytes=policy_bytes, format_bytes=format_bytes, facts_bytes=facts_bytes,
    )
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
