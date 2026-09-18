#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""
Tests for scripts/spec_check.py, run against wholly synthetic fixture roots.

Run:  python3 -m unittest discover -s plugins/driver-porting/skills/board-expert/tests -v
  or: python3 plugins/driver-porting/skills/board-expert/tests/test_spec_check.py

Every case runs twice, once per parser: with PyYAML if it is importable, and
with --no-pyyaml so the stdlib subset parser is exercised on the same inputs.
CI has no PyYAML, so the fallback is the parser that actually gates a push.
"""

import json
import pathlib
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
CHECKER = HERE.parent / "scripts" / "spec_check.py"
FIX = HERE / "fixtures"
GOOD = FIX / "good_root"
BAD = FIX / "bad_root"
VENDOR = FIX / "vendor_root"

sys.path.insert(0, str(CHECKER.parent))
import spec_check  # noqa: E402

PARSER_FLAGS = [["--no-pyyaml"]]
try:
    import yaml  # noqa: F401

    PARSER_FLAGS.append([])
except ImportError:
    pass


def run(*args, flags):
    proc = subprocess.run(
        [sys.executable, str(CHECKER), *flags, "--json", *[str(a) for a in args]],
        capture_output=True,
        text=True,
        check=False,
    )
    data = json.loads(proc.stdout) if proc.stdout.strip() else {"findings": []}
    return proc.returncode, data, proc.stderr


def messages(data):
    return [f["message"] for f in data["findings"]]


class SubsetParser(unittest.TestCase):
    def test_parses_the_shapes_the_format_uses(self):
        text = (
            "kind: soc\n"
            "id: x\n"
            "triggers: [a, b c, 'd,e']\n"
            "empty: []\n"
            "hex: 0xfe201000\n"
            "nothing: null\n"
            "flag: true\n"
            "note: >-\n"
            "  folded line one\n"
            "  folded line two\n"
            "instances:\n"
            "  - name: uart0   # trailing comment\n"
            "    ip: pl011\n"
            "    clocks: [clk]\n"
            "  - name: uart1\n"
            "resources:\n"
            "  repos:\n"
            "    - name: linux\n"
            "      files:\n"
            "        - a/b.c\n"
            "        - d/e.c\n"
            "  docs: []\n"
        )
        data = spec_check.parse_yaml_subset(text)
        self.assertEqual(data["triggers"], ["a", "b c", "d,e"])
        self.assertEqual(data["empty"], [])
        self.assertEqual(data["hex"], 0xFE201000)
        self.assertIsNone(data["nothing"])
        self.assertTrue(data["flag"])
        self.assertEqual(data["note"], "folded line one folded line two")
        self.assertEqual(data["instances"][0], {"name": "uart0", "ip": "pl011", "clocks": ["clk"]})
        self.assertEqual(data["instances"][1], {"name": "uart1"})
        self.assertEqual(data["resources"]["repos"][0]["files"], ["a/b.c", "d/e.c"])
        self.assertEqual(data["resources"]["docs"], [])

    def test_agrees_with_pyyaml_on_the_shipped_specs(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML not installed")
        shipped = HERE.parent / "specs"
        for path in sorted(shipped.rglob("*.spec.md")):
            m = spec_check.FRONTMATTER_RE.match(path.read_text())
            self.assertIsNotNone(m, path)
            self.assertEqual(
                spec_check.parse_yaml_subset(m.group(1)), yaml.safe_load(m.group(1)), path
            )


class GoodRoot(unittest.TestCase):
    def test_clean_root_passes_with_both_parsers(self):
        for flags in PARSER_FLAGS:
            with self.subTest(flags=flags):
                code, data, err = run(GOOD, "--stub", FIX / "stub_good.md", flags=flags)
                self.assertEqual(code, 0, err)
                self.assertEqual(messages(data), [])
                self.assertEqual(data["specs"], 3)

    def test_shipped_public_root_passes(self):
        for flags in PARSER_FLAGS:
            with self.subTest(flags=flags):
                code, data, err = run(HERE.parent / "specs", flags=flags)
                self.assertEqual(code, 0, err + json.dumps(data))

    def test_missing_root_marker_is_a_precondition(self):
        code, _, err = run(FIX, flags=["--no-pyyaml"])
        self.assertEqual(code, 3)
        self.assertIn("no board-specs.yaml", err)


class BadRoot(unittest.TestCase):
    def findings(self, flags):
        code, data, _ = run(BAD, "--stub", FIX / "stub_bad.md", flags=flags)
        self.assertEqual(code, 1)
        return messages(data)

    def test_every_failure_class_is_reported(self):
        for flags in PARSER_FLAGS:
            with self.subTest(flags=flags):
                msgs = "\n".join(self.findings(flags))
                self.assertIn("parts entry 'missingsoc' resolves to nothing", msgs)
                self.assertIn("access: internal under a public root", msgs)
                self.assertIn("via 'skill:acme-board-tools' is not a public skill", msgs)
                self.assertIn("fact bullet has no provenance tag", msgs)
                self.assertIn("[source-observed] fact without", msgs)
                self.assertIn("ip 'nosuchip' resolves to nothing", msgs)
                self.assertIn("'badboard' is not an ip spec", msgs)
                self.assertIn("duplicate id 'badsoc'", msgs)
                self.assertIn("ip spec has no docs entry with cite: true", msgs)
                self.assertIn("frontmatter does not parse", msgs)
                self.assertIn("unknown kind 'widget'", msgs)
                self.assertIn("missing required key 'cache'", msgs)
                self.assertIn("stub spec id 'nosuchboard' resolves to nothing", msgs)

    def test_public_skill_allowlist_silences_via(self):
        code, data, _ = run(BAD, "--public-skill", "acme-board-tools", flags=["--no-pyyaml"])
        self.assertEqual(code, 1)
        self.assertNotIn("is not a public skill", "\n".join(messages(data)))


class VendorRoot(unittest.TestCase):
    def test_overlays_resolve_across_roots_and_internal_is_allowed(self):
        for flags in PARSER_FLAGS:
            with self.subTest(flags=flags):
                code, data, _ = run(GOOD, VENDOR, flags=flags)
                msgs = messages(data)
                self.assertEqual(code, 1, msgs)
                self.assertIn("overlays 'nosuchboard' resolves to nothing", "\n".join(msgs))
                self.assertNotIn("access: internal", "\n".join(msgs))
                warnings = [f for f in data["findings"] if f["level"] == "warning"]
                self.assertEqual(len(warnings), 2)
                self.assertIn("2 overlays for 'widgetboard' in layer 'product'", warnings[0]["message"])

    def test_vendor_root_alone_cannot_resolve_its_targets(self):
        code, data, _ = run(VENDOR, flags=["--no-pyyaml"])
        self.assertEqual(code, 1)
        self.assertIn("overlays 'widgetboard' resolves to nothing", "\n".join(messages(data)))


if __name__ == "__main__":
    unittest.main()
