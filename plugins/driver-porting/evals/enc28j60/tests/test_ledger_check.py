# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for the ledger checker.

They need PyYAML, because the ledger format uses block scalars and nested mappings and the checker
does not carry its own parser. Without PyYAML the tests skip and say so; CI without it is not a
green result for this file.

The freeze-gate tests exist because a reviewer exercised the first version of check() with an
invented source, a numeric page locator, an unexplained scope exclusion, a duplicated reader name
and a dateless lock, and got zero errors. Each of those is now a named failure below.
"""

import contextlib
import hashlib
import io
import json
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


def run(text: str, *extra: str, corpus: Path = CORPUS):
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "ledger.yaml"
        p.write_text(text, encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = ledger_check.main([str(p), "--corpus", str(corpus), "--json", *extra])
        return code, json.loads(out.getvalue())


def errors_of(text: str, *extra: str) -> str:
    code, data = run(text, *extra)
    return "\n".join(data["errors"])


@unittest.skipIf(yaml is None, "PyYAML not importable; run under `uv run --with pyyaml`")
class LedgerCheckTest(unittest.TestCase):
    def test_good_ledger_is_clean(self):
        code, data = run(GOOD)
        self.assertEqual(code, 0, data)
        self.assertEqual(data["errors"], [])
        self.assertEqual(data["warnings"], [])
        self.assertEqual(data["counts"]["rows"], 3)
        self.assertEqual(data["counts"]["active"], 2)
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
            "bare page reference",
            "is not a corpus pin",
            "weight 'urgent'",
            "unknown revision 'B9'",
            "inference row needs a non-empty premises list",
            "withdrawn without notes",
        ):
            self.assertIn(needle, msgs)

    def test_reviewer_probes_now_fail(self):
        # Each of these passed the first version of the checker.
        self.assertIn("bare page reference", errors_of(GOOD.replace("locator: section 6.1", "locator: 42")))
        self.assertIn("bare page reference", errors_of(GOOD.replace("locator: section 6.1", "locator: pp. 42-43")))
        self.assertIn("locator must be a non-empty string", errors_of(GOOD.replace("locator: section 6.1", 'locator: ""')))
        self.assertIn("locator must be a non-empty string", errors_of(GOOD.replace("locator: section 6.1", "locator: null")))
        self.assertIn("statement must be a non-empty string", errors_of(GOOD.replace("statement: Something concluded.", "statement: null")))
        self.assertIn("in_scope false without notes", errors_of(GOOD.replace("    weight: important\n    in_scope: true", "    weight: important\n    in_scope: false")))
        self.assertIn("recoverable false without notes", errors_of(GOOD.replace("    in_scope: true\n    recoverable: true\n    status: active\n", "    in_scope: true\n    recoverable: false\n    status: active\n", 1)))
        self.assertIn("lists the same reader twice", errors_of(GOOD.replace("readers: [A, B]", "readers: [A, A]")))

    def test_missing_corpus_is_an_error_not_a_skip(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "ledger.yaml"
            p.write_text(GOOD, encoding="utf-8")
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                code = ledger_check.main([str(p), "--corpus", str(Path(tmp) / "nope.yaml")])
            self.assertEqual(code, 1)
            self.assertIn("corpus manifest not found", err.getvalue())

    def test_driver_commit_is_an_accepted_source(self):
        code, data = run(GOOD.replace("source: DS39662E", "source: adc218676eef25575469234709c2d87185ca223a"))
        self.assertEqual(code, 0, data["errors"])

    def test_numbering_gap_warns_unless_withdrawn(self):
        gapped = GOOD.replace("ENC28J60-INIT-001", "ENC28J60-INIT-003")
        code, data = run(gapped)
        self.assertEqual(code, 0)
        self.assertTrue(any("INIT: numbering gap at [1, 2]" in w for w in data["warnings"]), data["warnings"])

    def test_unexpected_key_warns(self):
        code, data = run(GOOD.replace("    readers: [A, B]\n", "    readers: [A, B]\n    wieght_disputed: {A: minor}\n"))
        self.assertEqual(code, 0)
        self.assertTrue(any("unexpected keys ['wieght_disputed']" in w for w in data["warnings"]), data["warnings"])

    def test_freeze_gate(self):
        # Clean ledger passes the gate: the only critical row has two readers.
        code, data = run(GOOD, "--freeze")
        self.assertEqual(code, 0, data["errors"])
        # A provisional marker blocks it.
        msgs = errors_of(GOOD.replace("    readers: [A, B]\n", "    readers: [A, B]\n    weight_disputed: {A: critical, B: important}\n"), "--freeze")
        self.assertIn("provisional markers still present ['weight_disputed']", msgs)
        # A critical row with one reader and no independent review blocks it.
        msgs = errors_of(GOOD.replace("readers: [A, B]", "readers: [A]"), "--freeze")
        self.assertIn("critical row with fewer than two readers", msgs)
        # ...and a bare note does not satisfy it: the review must say who, against what, and what they decided.
        msgs = errors_of(GOOD.replace("    readers: [A, B]\n", "    readers: [A]\n    independent_review: checked by C\n"), "--freeze")
        self.assertIn("needs a structured independent_review", msgs)
        structured = (
            "    readers: [A]\n"
            "    independent_review:\n"
            "      reviewer: C\n"
            "      locators: [\"DS80349C silicon issue 5\"]\n"
            "      disposition: supported as stated\n"
        )
        code, data = run(GOOD.replace("    readers: [A, B]\n", structured), "--freeze")
        self.assertEqual(code, 0, data["errors"])
        # The reviewer must not be one of the row's own readers.
        msgs = errors_of(GOOD.replace("    readers: [A, B]\n", structured.replace("reviewer: C", "reviewer: A")), "--freeze")
        self.assertIn("needs a structured independent_review", msgs)
        # An overlap with no disposition blocks it.
        msgs = errors_of(GOOD.replace("    readers: [A, B]\n", "    readers: [A, B]\n    overlaps: [ENC28J60-RX-002]\n"), "--freeze")
        self.assertIn("overlaps ['ENC28J60-RX-002'] with no disposition", msgs)
        # Without --freeze none of these are errors.
        code, data = run(GOOD.replace("readers: [A, B]", "readers: [A]"))
        self.assertEqual(code, 0, data["errors"])

    def test_lock_detects_edits_and_needs_a_date_and_corpus_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.yaml"
            ledger.write_text(GOOD, encoding="utf-8")
            lock = Path(tmp) / "ledger.lock"
            good_lock = (
                f"frozen: 2026-09-19\n"
                f"sha256: {hashlib.sha256(GOOD.encode()).hexdigest()}\n"
                f"corpus_sha256: {hashlib.sha256(CORPUS.read_bytes()).hexdigest()}\n"
            )
            lock.write_text(good_lock)
            self.assertEqual(ledger_check.main([str(ledger), "--corpus", str(CORPUS), "--lock", str(lock)]), 0)

            lock.write_text(good_lock.replace("frozen: 2026-09-19\n", ""))
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(ledger_check.main([str(ledger), "--corpus", str(CORPUS), "--lock", str(lock)]), 1)
            self.assertIn("missing frozen date", out.getvalue())

            lock.write_text(good_lock.replace("corpus_sha256: ", "corpus_sha256: 0"))
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(ledger_check.main([str(ledger), "--corpus", str(CORPUS), "--lock", str(lock)]), 1)
            self.assertIn("manifest is not the one frozen", out.getvalue())

            lock.write_text(good_lock)
            ledger.write_text(GOOD + "# edited\n", encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(ledger_check.main([str(ledger), "--corpus", str(CORPUS), "--lock", str(lock)]), 1)
            self.assertIn("edited after freezing", out.getvalue())


if __name__ == "__main__":
    unittest.main()
