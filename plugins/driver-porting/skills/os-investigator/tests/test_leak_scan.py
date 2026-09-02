#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Curtis Galloway
# SPDX-License-Identifier: Apache-2.0
"""
Tests for scripts/leak_scan.py, run against wholly synthetic fixtures.

Run:  python3 -m unittest discover -s plugins/driver-porting/skills/os-investigator/tests -v
  or: python3 plugins/driver-porting/skills/os-investigator/tests/test_leak_scan.py

The load-bearing case is test_report_never_reproduces_source_text: the
scanner's whole premise is that its report can be filed as evidence and
handed to a verifier without itself becoming a leak. Bare identifier names
are the one sanctioned exception.
"""

import pathlib
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
SCANNER = HERE.parent / "scripts" / "leak_scan.py"
FIX = HERE / "fixtures"
SOURCE = FIX / "fake_source"


def run_scan(*args):
    """Run leak_scan.py and return (returncode, stdout+stderr)."""
    proc = subprocess.run(
        [sys.executable, str(SCANNER)] + [str(a) for a in args],
        capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


class TestLeakScan(unittest.TestCase):

    def test_leaky_spec_is_flagged(self):
        """Transcribed source must trip both checks and exit 1."""
        rc, out = run_scan(FIX / "leaky_spec.md", "--against", SOURCE)
        self.assertEqual(rc, 1, out)
        self.assertIn("FINDINGS", out)
        self.assertNotIn("[runs] 0 shared run(s)", out)
        self.assertIn("purple_latch_timeout", out)
        self.assertIn("widgetron_bringup_sequence", out)

    def test_clean_spec_passes(self):
        """Same facts re-expressed as hardware facts must scan clean."""
        rc, out = run_scan(FIX / "clean_spec.md", "--against", SOURCE)
        self.assertEqual(rc, 0, out)
        self.assertIn("verdict: clean", out)

    def test_report_never_reproduces_source_text(self):
        """The report cites locations and digests, never matched text.

        Bare identifiers are deliberately exempt, so these assertions use
        multi-token sequences that can only appear if verbatim text was
        echoed, plus an all-caps token the identifier lint does not print.
        """
        rc, out = run_scan(FIX / "leaky_spec.md", "--against", SOURCE)
        self.assertEqual(rc, 1, out)
        for verbatim in ("widgetron_write(wp,", "& STATUS_RESET_BUSY",
                         "ETIMEDOUT", "unsigned int"):
            self.assertNotIn(verbatim, out,
                             f"scanner reproduced source text: {verbatim!r}")
        self.assertIn("candidate L", out)
        self.assertIn("sha1:", out)

    def test_whitelist_suppresses_databook_nomenclature(self):
        """Whitelisted all-caps names stop being reported."""
        _, before = run_scan(FIX / "leaky_spec.md", "--against", SOURCE)
        self.assertIn("WIDGETRON_CTRL", before)
        _, after = run_scan(FIX / "leaky_spec.md", "--against", SOURCE,
                            "--whitelist", FIX / "nomenclature-whitelist.txt")
        self.assertIn("[idents] 0 ALL-CAPS", after)
        self.assertNotIn("WIDGETRON_CTRL", after)
        self.assertIn("purple_latch_timeout", after,
                      "whitelisting databook names must not mask "
                      "source-invented ones")

    def test_numeric_overlap_alone_does_not_trigger(self):
        """Register tables legitimately share numbers with the source."""
        rc, out = run_scan(FIX / "clean_spec.md", "--against", SOURCE)
        self.assertEqual(rc, 0, out)
        self.assertIn("[runs] 0 shared run(s)", out)

    def test_bad_shingle_size_is_usage_error(self):
        rc, out = run_scan(FIX / "clean_spec.md", "--against", SOURCE,
                           "--k", "20", "--min-run", "10")
        self.assertEqual(rc, 2, out)
        self.assertIn("--k must be <= --min-run", out)

    def test_missing_source_path_is_error(self):
        rc, out = run_scan(FIX / "clean_spec.md", "--against",
                           HERE / "no-such-directory")
        self.assertEqual(rc, 2, out)


if __name__ == "__main__":
    unittest.main()
