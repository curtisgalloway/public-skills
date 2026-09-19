# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for the ENC28J60 corpus pin checker.

These cover the parser only. The fetching half needs the network and the vendor's servers, so it
is exercised by running the script, not by a unit test.

The parser is the part that has already been wrong once: an earlier version matched entries with a
single space after a comma, so the two editions whose fields were column-aligned with two spaces
were silently dropped and never checked. A checker that skips a pin without saying so is worse
than no checker, hence the count assertions below.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import corpus_check  # noqa: E402

MANIFEST = Path(__file__).resolve().parents[1] / "corpus.yaml"


class LoadManifestTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = corpus_check.load_manifest(MANIFEST)

    def test_driver_commit_is_pinned(self):
        self.assertRegex(self.manifest["commit"], r"^[0-9a-f]{40}$")

    def test_both_driver_files_are_pinned(self):
        paths = [f["path"] for f in self.manifest["files"]]
        self.assertEqual(
            paths,
            [
                "drivers/net/ethernet/microchip/enc28j60.c",
                "drivers/net/ethernet/microchip/enc28j60_hw.h",
            ],
        )
        for f in self.manifest["files"]:
            self.assertRegex(f["sha256"], r"^[0-9a-f]{64}$")
            self.assertGreater(f["bytes"], 0)

    def test_every_document_edition_is_picked_up(self):
        """Alignment spacing inside an entry must not change what gets checked."""
        kinds = [d["kind"] for d in self.manifest["documents"]]
        self.assertEqual(kinds.count("datasheet"), 5, "datasheet revs A-E")
        self.assertEqual(kinds.count("errata"), 2, "errata revs B and C")

    def test_urls_resolve_against_the_right_pattern(self):
        by_kind = {}
        for d in self.manifest["documents"]:
            by_kind.setdefault(d["kind"], []).append(d)
        for d in by_kind["datasheet"]:
            self.assertIn("39662", d["url"])
            self.assertIn(d["rev"].lower() + ".pdf", d["url"])
        for d in by_kind["errata"]:
            self.assertIn("80349", d["url"])
            self.assertIn(d["rev"].lower() + ".pdf", d["url"])

    def test_an_edition_outside_a_section_is_refused(self):
        """A stray edition must raise, not attach itself to whatever came last."""
        broken = (
            "  commit: " + "0" * 40 + "\n"
            "    - path: a/b.c\n      bytes: 1\n      sha256: " + "a" * 64 + "\n"
            "      - {rev: A, year: 2004, pages: 1, bytes: 2, sha256: " + "b" * 64 + "}\n"
        )
        tmp = Path(self.id().split(".")[-1] + ".yaml")
        tmp.write_text(broken)
        try:
            with self.assertRaises(ValueError):
                corpus_check.load_manifest(tmp)
        finally:
            tmp.unlink()

    def test_a_manifest_without_a_commit_is_refused(self):
        tmp = Path(self.id().split(".")[-1] + ".yaml")
        tmp.write_text("pilot: enc28j60\n")
        try:
            with self.assertRaises(ValueError):
                corpus_check.load_manifest(tmp)
        finally:
            tmp.unlink()


if __name__ == "__main__":
    unittest.main()
