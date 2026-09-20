# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for the ledger checker.

They need PyYAML, because the ledger format uses block scalars and nested mappings and the checker
does not carry its own parser. Without PyYAML the tests skip and say so; CI without it is not a
green result for this file.
"""

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    import yaml  # noqa: F401
except ImportError:  # pragma: no cover
    yaml = None

import ledger_check  # noqa: E402

CORPUS = Path(__file__).resolve().parents[1] / "corpus.yaml"

GOOD = """\
pilot: enc28j60
corpus_frozen: 2026-09-19
authored: 2026-09-19
author: test
authoring_rule: blind
rows:
  - id: ENC28J60-RX-001
    statement: >-
      The receive buffer must begin at address 0x0000.
    class: documented-hardware-requirement
    derivation:
      - source: DS80349C
        locator: "silicon issue 5 (Memory, Ethernet Buffer)"
    applicability:
      vendor_confirmed: [B1, B4, B5, B7]
      implementation_observed: true
      unresolved: false
    weight: critical
    in_scope: true
    recoverable: true
    status: active
    readers: [A, B]
  - id: ENC28J60-RX-002
    statement: Withdrawn on purpose.
    class: implementation-choice
    derivation:
      - source: drivers/net/ethernet/microchip/enc28j60.c
        locator: the receive handler
    applicability:
      vendor_confirmed: []
      implementation_observed: true
      unresolved: false
    weight: minor
    in_scope: true
    recoverable: true
    status: withdrawn
    notes: duplicate of RX-001 after merge
  - id: ENC28J60-INIT-001
    statement: Something concluded.
    class: inference
    premises: [a, b]
    confidence: medium
    settled_by: hardware
    derivation:
      - source: DS39662E
        locator: section 6.1
    applicability:
      vendor_confirmed: []
      implementation_observed: false
      unresolved: true
    weight: important
    in_scope: true
    recoverable: true
    status: active
"""


def run(text: str, *extra: str):
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "ledger.yaml"
        p.write_text(text, encoding="utf-8")
        import contextlib
        import io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = ledger_check.main([str(p), "--corpus", str(CORPUS), "--json", *extra])
        import json
        return code, json.loads(out.getvalue())


@unittest.skipIf(yaml is None, "PyYAML not importable; run under `uv run --with pyyaml`")
class LedgerCheckTest(unittest.TestCase):
    def test_good_ledger_is_clean(self):
        code, data = run(GOOD)
        self.assertEqual(code, 0, data)
        self.assertEqual(data["errors"], [])
        self.assertEqual(data["warnings"], [])
        self.assertEqual(data["counts"]["rows"], 3)
        self.assertEqual(data["counts"]["readers_both"], 1)
        self.assertEqual(data["counts"]["facet"], {"RX": 2, "INIT": 1})

    def test_every_error_class_is_reported(self):
        bad = (
            GOOD.replace("ENC28J60-RX-002", "ENC28J60-RX-001", 1)  # duplicate id
            .replace("locator: section 6.1", "locator: page 33")  # bare page
            .replace("source: DS39662E", "source: DS39662Z")  # unknown pin
            .replace("weight: important", "weight: urgent")  # bad weight
            .replace("vendor_confirmed: [B1, B4, B5, B7]", "vendor_confirmed: [B1, B9]")  # unknown rev
            .replace("    premises: [a, b]\n", "")  # inference without premises
            .replace("    notes: duplicate of RX-001 after merge\n", "")  # withdrawn without notes
        )
        code, data = run(bad)
        self.assertEqual(code, 1)
        msgs = "\n".join(data["errors"])
        for needle in (
            "duplicate id",
            "bare page number",
            "is not a corpus pin",
            "weight 'urgent'",
            "unknown revision 'B9'",
            "inference row without 'premises'",
            "withdrawn without notes",
        ):
            self.assertIn(needle, msgs)

    def test_numbering_gap_warns_unless_withdrawn(self):
        gapped = GOOD.replace("ENC28J60-INIT-001", "ENC28J60-INIT-003")
        code, data = run(gapped)
        self.assertEqual(code, 0)
        self.assertTrue(any("INIT: numbering gap at [1, 2]" in w for w in data["warnings"]), data["warnings"])

    def test_lock_detects_an_edit_after_freezing(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.yaml"
            ledger.write_text(GOOD, encoding="utf-8")
            lock = Path(tmp) / "ledger.lock"
            lock.write_text(f"frozen: 2026-09-19\nsha256: {hashlib.sha256(GOOD.encode()).hexdigest()}\n")
            self.assertEqual(ledger_check.main([str(ledger), "--corpus", str(CORPUS), "--lock", str(lock)]), 0)
            ledger.write_text(GOOD + "# edited\n", encoding="utf-8")
            self.assertEqual(ledger_check.main([str(ledger), "--corpus", str(CORPUS), "--lock", str(lock)]), 1)


if __name__ == "__main__":
    unittest.main()
