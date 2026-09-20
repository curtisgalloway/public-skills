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


POLICY = (
    "# Test policy\n\nVersion: test-1.0\nAdopted: 2026-09-20\n\n"
    "## Composite scoring units\n\n"
    "| Scoring unit | The facts it enumerates | Facts |\n|---|---|---|\n"
    "| RX-001 | the address and the consequence | 2 |\n"
    "| **Total** | | **1** |\n\n"
    "## Something else\n\nnot part of the list: INIT-001\n"
)

FACTS = (
    "# Test facts\n\n### ENC28J60-RX-001 - receive buffer start\n\n"
    "1. The buffer begins at 0x0000. DS80349C issue 5.\n"
    "2. Placing it elsewhere corrupts receive data. DS80349C issue 5.\n\n"
    "**Count: 2**\n"
)


def run(text: str, *extra: str, corpus: Path = CORPUS, policy: str | None = POLICY,
        facts: str | None = FACTS):
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "ledger.yaml"
        p.write_text(text, encoding="utf-8")
        args = [str(p), "--corpus", str(corpus), "--json"]
        if policy is not None:
            pol = Path(tmp) / "SCORING-POLICY.md"
            pol.write_text(policy, encoding="utf-8")
            args += ["--policy", str(pol)]
        if facts is not None:
            fct = Path(tmp) / "SCORING-FACTS.md"
            fct.write_text(facts, encoding="utf-8")
            args += ["--facts", str(fct)]
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = ledger_check.main([*args, *extra])
        return code, json.loads(out.getvalue())


def errors_of(text: str, *extra: str, **kw) -> str:
    code, data = run(text, *extra, **kw)
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

    def test_composite_list_is_checked_against_the_ledger(self):
        # The good policy names RX-001, which is active, and only counts ids inside its own section.
        code, data = run(GOOD)
        self.assertEqual(code, 0, data["errors"])
        self.assertEqual(data["counts"]["composite_units"], 1)
        # An id no row carries.
        msgs = errors_of(GOOD, policy=POLICY.replace("RX-001", "RX-099"))
        self.assertIn("composite list names ENC28J60-RX-099, which is not a row", msgs)
        # An id whose row is withdrawn.
        msgs = errors_of(GOOD, policy=POLICY.replace("| RX-001 |", "| RX-002 |"),
                         facts=FACTS.replace("RX-001", "RX-002"))
        self.assertIn("composite list names ENC28J60-RX-002, which is withdrawn", msgs)
        # A printed total that does not match the ids.
        msgs = errors_of(GOOD, policy=POLICY.replace("**Total** | | **1**", "**Total** | | **7**"))
        self.assertIn("prints a total of 7 but names 1 distinct ids", msgs)
        # A policy with no composite section blocks a freeze.
        msgs = errors_of(GOOD, "--freeze", policy="# Test policy\n\nVersion: test-1.0\n", facts=None)
        self.assertIn("names no composite scoring units", msgs)

    def test_fact_lists_are_checked_against_the_policy(self):
        # These are the denominators of proportional partial credit. A reviewer changed one count
        # to zero in an earlier version and the freeze gate stayed silent.
        code, data = run(GOOD)
        self.assertEqual(code, 0, data["errors"])
        self.assertEqual(data["counts"]["listed_facts"], 2)
        # The policy's count disagrees with the list that justifies it.
        msgs = errors_of(GOOD, policy=POLICY.replace("| 2 |", "| 3 |"))
        self.assertIn("lists 2 fact(s) but the policy's table says 3", msgs)
        # A composite unit with no count at all.
        msgs = errors_of(GOOD, policy=POLICY.replace("| RX-001 | the address and the consequence | 2 |",
                                                     "| RX-001 | the address and the consequence | |"))
        self.assertIn("has no fact count", msgs)
        # A count below two is not a composite.
        msgs = errors_of(GOOD, policy=POLICY.replace("| 2 |", "| 1 |"))
        self.assertIn("declares 1 fact(s); a composite has at least two", msgs)
        # The list's own printed count disagrees with its length.
        msgs = errors_of(GOOD, facts=FACTS.replace("**Count: 2**", "**Count: 5**"))
        self.assertIn("lists 2 fact(s) but prints a count of 5", msgs)
        # A unit the policy names with no list at all.
        msgs = errors_of(GOOD, facts="# Test facts\n\nnothing here\n")
        self.assertIn("has no fact list", msgs)
        # A list for something the policy does not call composite.
        msgs = errors_of(GOOD, facts=FACTS + "\n### ENC28J60-INIT-001 - stray\n\n1. one.\n2. two.\n\n**Count: 2**\n")
        self.assertIn("ENC28J60-INIT-001 has a fact list but is not a composite unit", msgs)

    def test_freeze_needs_a_versioned_scoring_policy(self):
        # No policy file at all.
        code, data = run(GOOD, "--freeze", policy=None, facts=None)
        self.assertEqual(code, 1)
        self.assertTrue(any("no scoring policy" in e for e in data["errors"]), data["errors"])
        # A policy with no Version line binds nothing.
        code, data = run(GOOD, "--freeze", policy="# Test policy\n\nno version here\n")
        self.assertEqual(code, 1)
        self.assertTrue(any("declares no 'Version:'" in e for e in data["errors"]), data["errors"])
        # Without --freeze a missing policy is not an error.
        code, data = run(GOOD, policy=None, facts=None)
        self.assertEqual(code, 0, data["errors"])

    def test_lock_pins_the_policy_version_and_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.yaml"
            ledger.write_text(GOOD, encoding="utf-8")
            policy = Path(tmp) / "SCORING-POLICY.md"
            policy.write_text(POLICY, encoding="utf-8")
            lock = Path(tmp) / "ledger.lock"
            base = [str(ledger), "--corpus", str(CORPUS), "--policy", str(policy), "--lock", str(lock)]

            fmt = Path(tmp) / "LEDGER-FORMAT.md"
            fmt.write_text("# format\n", encoding="utf-8")
            fct = Path(tmp) / "SCORING-FACTS.md"
            fct.write_text(FACTS, encoding="utf-8")
            base = base + ["--format", str(fmt), "--facts", str(fct)]

            def write_lock(drop=(), **over):
                fields = {
                    "frozen": "2026-09-20",
                    "revision": "0123456789abcdef0123456789abcdef01234567",
                    "sha256": hashlib.sha256(GOOD.encode()).hexdigest(),
                    "corpus_sha256": hashlib.sha256(CORPUS.read_bytes()).hexdigest(),
                    "policy_version": "test-1.0",
                    "policy_sha256": hashlib.sha256(POLICY.encode()).hexdigest(),
                    "format_sha256": hashlib.sha256(fmt.read_bytes()).hexdigest(),
                    "facts_sha256": hashlib.sha256(fct.read_bytes()).hexdigest(),
                }
                fields.update(over)
                for k in drop:
                    fields.pop(k, None)
                lock.write_text("".join(f"{k}: {v}\n" for k, v in fields.items()))

            write_lock()
            self.assertEqual(ledger_check.main(base), 0)

            # An unversioned policy and a lock that also omits the version must not agree by accident.
            policy.write_text("# Test policy\n\nno version here\n", encoding="utf-8")
            write_lock(drop=("policy_version",))
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(ledger_check.main(base), 1)
            self.assertIn("declares no 'Version:' line", out.getvalue())
            self.assertIn("missing policy_version", out.getvalue())
            policy.write_text(POLICY, encoding="utf-8")

            for field, needle in (("format_sha256", "missing format_sha256"), ("revision", "missing revision")):
                write_lock(drop=(field,))
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    self.assertEqual(ledger_check.main(base), 1)
                self.assertIn(needle, out.getvalue())

            write_lock()
            fmt.write_text("# format, quietly amended\n", encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(ledger_check.main(base), 1)
            self.assertIn("LEDGER-FORMAT.md was edited after freezing", out.getvalue())
            fmt.write_text("# format\n", encoding="utf-8")
            write_lock()

            write_lock(policy_version="test-0.9")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(ledger_check.main(base), 1)
            self.assertIn("policy version", out.getvalue())

            # Editing the policy after freezing, even trivially, breaks the lock.
            write_lock()
            policy.write_text(POLICY + "\na clarifying sentence nobody approved\n", encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(ledger_check.main(base), 1)
            self.assertIn("policy was edited after freezing", out.getvalue())

    def test_lock_detects_edits_and_needs_a_date_and_corpus_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.yaml"
            ledger.write_text(GOOD, encoding="utf-8")
            policy = Path(tmp) / "SCORING-POLICY.md"
            policy.write_text(POLICY, encoding="utf-8")
            fmt = Path(tmp) / "LEDGER-FORMAT.md"
            fmt.write_text("# format\n", encoding="utf-8")
            fct = Path(tmp) / "SCORING-FACTS.md"
            fct.write_text(FACTS, encoding="utf-8")
            lock = Path(tmp) / "ledger.lock"
            argv = [str(ledger), "--corpus", str(CORPUS), "--policy", str(policy),
                    "--format", str(fmt), "--facts", str(fct), "--lock", str(lock)]
            good_lock = (
                f"frozen: 2026-09-19\n"
                f"revision: 0123456789abcdef0123456789abcdef01234567\n"
                f"sha256: {hashlib.sha256(GOOD.encode()).hexdigest()}\n"
                f"corpus_sha256: {hashlib.sha256(CORPUS.read_bytes()).hexdigest()}\n"
                f"policy_version: test-1.0\n"
                f"policy_sha256: {hashlib.sha256(POLICY.encode()).hexdigest()}\n"
                f"format_sha256: {hashlib.sha256(fmt.read_bytes()).hexdigest()}\n"
                f"facts_sha256: {hashlib.sha256(fct.read_bytes()).hexdigest()}\n"
            )
            lock.write_text(good_lock)
            self.assertEqual(ledger_check.main(argv), 0)

            lock.write_text(good_lock.replace("frozen: 2026-09-19\n", ""))
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(ledger_check.main(argv), 1)
            self.assertIn("missing frozen date", out.getvalue())

            lock.write_text(good_lock.replace("corpus_sha256: ", "corpus_sha256: 0"))
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(ledger_check.main(argv), 1)
            self.assertIn("manifest is not the one frozen", out.getvalue())

            lock.write_text(good_lock)
            ledger.write_text(GOOD + "# edited\n", encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(ledger_check.main(argv), 1)
            self.assertIn("ledger was edited after freezing", out.getvalue())


if __name__ == "__main__":
    unittest.main()
