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
STUBS = FIX / "stubs"

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
            "    irq: {kind: SPI, number: 121, trigger: level-high, note: shared line}\n"
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
        self.assertEqual(
            data["instances"][0],
            {
                "name": "uart0",
                "ip": "pl011",
                "irq": {"kind": "SPI", "number": 121, "trigger": "level-high", "note": "shared line"},
                "clocks": ["clk"],
            },
        )
        self.assertEqual(data["instances"][1], {"name": "uart1"})
        self.assertEqual(data["resources"]["repos"][0]["files"], ["a/b.c", "d/e.c"])
        self.assertEqual(data["resources"]["docs"], [])

    def test_rejects_unterminated_flow_collections(self):
        with self.assertRaises(spec_check.YamlError):
            spec_check.parse_yaml_subset("name: [unterminated\n")
        with self.assertRaises(spec_check.YamlError):
            spec_check.parse_yaml_subset("irq: {kind: SPI\n")

    def test_rejects_colon_space_in_plain_scalars_like_pyyaml(self):
        with self.assertRaises(spec_check.YamlError) as ctx:
            spec_check.parse_yaml_subset("note: TODO (verify on hardware): the PMIC\n")
        self.assertIn("'note'", str(ctx.exception))
        with self.assertRaises(spec_check.YamlError):
            spec_check.parse_yaml_subset("irq: {kind: SPI, number: 3, note: shared: yes}\n")
        with self.assertRaises(spec_check.YamlError):
            spec_check.parse_yaml_subset("files:\n  - a: b: c\n")
        self.assertEqual(
            spec_check.parse_yaml_subset('note: "TODO (verify on hardware): quoted"\n'),
            {"note": "TODO (verify on hardware): quoted"},
        )
        self.assertEqual(spec_check.parse_yaml_subset("url: https://x/y\n"), {"url": "https://x/y"})

    def test_agrees_with_pyyaml_on_the_shipped_specs_and_fixtures(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML not installed")
        paths = list((HERE.parent / "specs").rglob("*.spec.md"))
        paths += [p for p in FIX.rglob("*.spec.md") if p.name not in ("broken.spec.md", "colon.spec.md")]
        for path in sorted(paths):
            m = spec_check.FRONTMATTER_RE.match(path.read_text())
            self.assertIsNotNone(m, path)
            self.assertEqual(
                spec_check.parse_yaml_subset(m.group(1)),
                spec_check.load_yaml(m.group(1), use_pyyaml=True),
                path,
            )


class TagRules(unittest.TestCase):
    def ok(self, bullet):
        return bool(spec_check.TAIL_RE.search(bullet))

    def test_tail_accepts_the_documented_shapes(self):
        self.assertTrue(self.ok("- Fact. `[DT]`"))
        self.assertTrue(self.ok("- Fact. `[DT]` (node), `[databook]` (DDI 0183)"))
        self.assertTrue(self.ok("- Fact. [DT] (node) [doc] (page)."))
        self.assertTrue(self.ok("- Fact. `[DT]` (a (nested) note). `TODO (verify on hardware)`: the IRQ."))
        self.assertTrue(self.ok("- Fact. `[source-observed]` TODO (verify on hardware)"))

    def test_tail_rejects_tags_in_the_middle(self):
        self.assertFalse(self.ok("- The `[DT]` value is 5, and then prose."))
        self.assertFalse(self.ok("- Fact. `[DT]` (node). See the other spec."))
        self.assertFalse(self.ok("- Fact. `[DT]` (node). TODO (verify on hardware): x. Also `[doc]` (p) more."))

    def test_gap_bullets(self):
        self.assertTrue(spec_check.GAP_RE.match("- **Power.** `TODO (verify on hardware)`: PMIC."))
        self.assertTrue(spec_check.GAP_RE.match("- TODO (verify on hardware): everything."))
        self.assertFalse(spec_check.GAP_RE.match("- **Power.** The PMIC is X. TODO (verify on hardware)"))

    def test_doc_needs_a_parenthetical(self):
        self.assertIsNone(spec_check.DOC_UNNAMED_RE.search("`[doc]` (page)"))
        self.assertIsNone(spec_check.DOC_UNNAMED_RE.search("[doc] (page)"))
        self.assertIsNotNone(spec_check.DOC_UNNAMED_RE.search("`[doc]`"))
        self.assertIsNotNone(spec_check.DOC_UNNAMED_RE.search("`[doc]`, `[DT]` (node)"))

    def test_dt_needs_a_parenthetical(self):
        dt = spec_check.UNNAMED_RES["DT"]
        self.assertIsNone(dt.search("`[DT]` (`bcm2712.dtsi`)"))
        self.assertIsNone(dt.search("[DT] (lga-b0.dtb from a prebuilt tree)"))
        self.assertIsNotNone(dt.search("`[DT]`"))
        self.assertIsNotNone(dt.search("`[DT]`, `[databook]` (DDI 0183)"))


class GoodRoot(unittest.TestCase):
    def test_clean_root_passes_with_both_parsers(self):
        for flags in PARSER_FLAGS:
            with self.subTest(flags=flags):
                code, data, err = run(GOOD, "--stub", FIX / "stub_good.md", flags=flags)
                self.assertEqual(code, 0, err + json.dumps(data))
                self.assertEqual(messages(data), [])
                self.assertEqual(data["specs"], 3)
                expected = "subset" if flags or not spec_check.pyyaml_available() else "pyyaml"
                self.assertEqual(data["parser"], expected)

    def test_human_output_names_the_parser(self):
        proc = subprocess.run(
            [sys.executable, str(CHECKER), "--no-pyyaml", str(GOOD)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("(parser: subset)", proc.stdout)

    def test_shipped_public_root_passes(self):
        for flags in PARSER_FLAGS:
            with self.subTest(flags=flags):
                code, data, err = run(
                    HERE.parent / "specs", "--stubs-from", HERE.parent.parent, flags=flags
                )
                self.assertEqual(code, 0, err + json.dumps(data))
                self.assertGreaterEqual(data["stubs"], 3)

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
                for expected in (
                    "parts entry 'missingsoc' resolves to nothing",
                    "access: internal under a public root",
                    "via 'skill:acme-board-tools' is not a public skill",
                    "fact bullet has no provenance tag",
                    "[source-observed] fact without",
                    "[press] fact without",
                    "[doc] must be followed by a parenthetical",
                    "[DT] must be followed by a parenthetical",
                    "irq.kind extended requires irq.parent",
                    "irq.parent is only valid for kind extended",
                    "irq.intid is not valid for kind extended",
                    "file 'c/d.dtsi': status must be one of",
                    "files entry must be a path or a mapping with path",
                    "does not end with its tag clause",
                    "ip 'nosuchip' resolves to nothing",
                    "'badboard' is not an ip spec",
                    "reg must be an integer or null",
                    "irq must be null or a mapping",
                    "irq.kind must be one of",
                    "irq.number must be an integer",
                    "duplicate id 'badsoc'",
                    "ip spec has no docs entry with cite: true",
                    "frontmatter does not parse",
                    "unknown kind 'widget'",
                    "missing required key 'cache'",
                    "variant_of 'nosuchbase' resolves to nothing",
                    "variants: entry without a name",
                    "a series is a map, never cite: true",
                    "fetch must be one of",
                    "status must be one of",
                    "stub spec id 'nosuchboard' resolves to nothing",
                ):
                    self.assertIn(expected, msgs)
                # colon.spec.md fails under both parsers, each in its own words
                if spec_check.parser_name(not flags) == "subset":
                    self.assertIn("contains ': '", msgs)
                else:
                    self.assertIn("mapping values are not allowed here", msgs)

    def test_public_skill_allowlist_silences_via(self):
        code, data, _ = run(BAD, "--public-skill", "acme-board-tools", flags=["--no-pyyaml"])
        self.assertEqual(code, 1)
        self.assertNotIn("is not a public skill", "\n".join(messages(data)))


class Stubs(unittest.TestCase):
    def test_stubs_from_finds_stubs_by_their_sentence(self):
        code, data, _ = run(GOOD, "--stubs-from", STUBS, flags=["--no-pyyaml"])
        self.assertEqual(code, 1)
        self.assertEqual(data["stubs"], 2)  # widget-expert and broken-expert; not-a-stub ignored
        msgs = "\n".join(messages(data))
        self.assertIn("stub spec id 'nosuchboard' resolves to nothing", msgs)
        self.assertNotIn("not-a-stub", msgs)

    def test_stubs_from_needs_a_directory(self):
        code, _, err = run(GOOD, "--stubs-from", FIX / "nowhere", flags=["--no-pyyaml"])
        self.assertEqual(code, 3)
        self.assertIn("is not a directory", err)


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


class CacheWarning(unittest.TestCase):
    def test_part_cache_mismatch_warns(self):
        import tempfile, shutil

        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / "root"
            shutil.copytree(GOOD, root)
            soc = root / "widgetsoc.spec.md"
            soc.write_text(soc.read_text().replace("cache: widget-resources", "cache: other-resources"))
            code, data, _ = run(root, flags=["--no-pyyaml"])
            self.assertEqual(code, 0)
            warnings = [f for f in data["findings"] if f["level"] == "warning"]
            self.assertEqual(len(warnings), 1)
            self.assertIn("names cache 'other-resources'", warnings[0]["message"])


if __name__ == "__main__":
    unittest.main()
