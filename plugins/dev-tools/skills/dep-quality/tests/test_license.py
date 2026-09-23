#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for the license gate in scripts/depscore.py.

Run:  python3 -m unittest discover -s plugins/dev-tools/skills/dep-quality/tests -v

The expressions are the ones registries actually return. Two of them
(fs2's "MIT/Apache-2.0" and jpeg-encoder's "(MIT OR Apache-2.0) AND IJG")
were wrongly rejected when the gate compared whole strings.
"""

import importlib.util
import pathlib
import unittest

HERE = pathlib.Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "depscore", HERE.parent / "scripts" / "depscore.py")
depscore = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(depscore)

ALLOW = depscore.DEFAULT_LICENSES


def allowed(expr):
    return depscore.license_allowed(expr, ALLOW)


class LicenseGateTest(unittest.TestCase):

    def test_single_ids(self):
        self.assertTrue(allowed("MIT"))
        self.assertTrue(allowed("MPL-2.0"))
        self.assertFalse(allowed("GPL-3.0"))

    def test_or_needs_one_allowed_side(self):
        self.assertTrue(allowed("MIT OR Apache-2.0"))
        self.assertTrue(allowed("Apache-2.0 OR MIT"))
        self.assertTrue(allowed("GPL-3.0 OR MIT"))
        self.assertFalse(allowed("GPL-3.0 OR AGPL-3.0"))

    def test_legacy_slash_is_or(self):
        self.assertTrue(allowed("MIT/Apache-2.0"))
        self.assertTrue(allowed("GPL-3.0/MIT"))

    def test_and_needs_every_side(self):
        self.assertTrue(allowed("(MIT OR Apache-2.0) AND IJG"))
        self.assertFalse(allowed("(MIT OR Apache-2.0) AND Unicode-3.0"))
        self.assertFalse(allowed("MIT AND GPL-3.0"))

    def test_precedence_and_binds_tighter(self):
        self.assertTrue(allowed("GPL-3.0 AND AGPL-3.0 OR MIT"))
        self.assertFalse(allowed("GPL-3.0 AND (AGPL-3.0 OR MIT)"))

    def test_with_exception_judged_by_base(self):
        self.assertTrue(allowed("Apache-2.0 WITH LLVM-exception"))
        self.assertFalse(allowed("GPL-2.0 WITH Classpath-exception-2.0"))

    def test_malformed_is_rejected(self):
        self.assertFalse(allowed("MIT OR"))
        self.assertFalse(allowed("(MIT"))
        self.assertFalse(allowed("MIT Apache-2.0"))

    def test_override_allowlist(self):
        self.assertTrue(depscore.license_allowed("GPL-3.0", {"GPL-3.0"}))
        self.assertFalse(depscore.license_allowed("MIT", {"GPL-3.0"}))


if __name__ == "__main__":
    unittest.main()
