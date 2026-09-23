# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Adversarial archive and transfer checks using small synthetic pinned trees."""

import io
import json
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import export_kernel as exporter  # pylint: disable=wrong-import-position


class ExportTests(unittest.TestCase):
    """Exercise failure gates without downloading or modifying the real kernel."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.archive = self.root / "input.tar.gz"
        self.output = self.root / "output"
        self.files = {
            "Foo.h": ("100644", b"upper\n"),
            "foo.h": ("100644", b"lower\n"),
            "scripts/run": ("100755", b"exit 0\n"),
            "link": ("120000", b"Foo.h"),
            "vendor.txt": ("100644", b"unrelated Microchip part\n"),
            "drivers/net/ethernet/microchip/Kconfig": (
                "100644",
                b"before\nconfig ENC28J60\nsecret\nconfig ENCX24J600\nafter\n",
            ),
            "drivers/net/ethernet/microchip/Makefile": (
                "100644",
                b"obj-$(CONFIG_ENC28J60) += enc28j60.o\nkeep\n",
            ),
            "arch/arm/configs/mxs_defconfig": ("100644", b"CONFIG_ENC28J60=y\nkeep\n"),
        }
        self.files.update(
            {path: ("100644", b"forbidden enc28j60\n") for path in exporter.REMOVED}
        )

    def prepare(self, extra=None):
        """Build a fixture and pin it exactly as a caller must pin the real input."""
        with tarfile.open(self.archive, "w:gz") as archive:
            for path, (mode, data) in self.files.items():
                member = tarfile.TarInfo(exporter.PREFIX + "/" + path)
                if mode == "120000":
                    member.type = tarfile.SYMTYPE
                    member.linkname = data.decode()
                    archive.addfile(member)
                else:
                    member.mode = 0o755 if mode == "100755" else 0o644
                    member.size = len(data)
                    archive.addfile(member, io.BytesIO(data))
            if extra:
                archive.addfile(extra)
        tree = exporter.git_tree(
            {
                path: (mode, exporter.git_object(b"blob", data))
                for path, (mode, data) in self.files.items()
            }
        )
        self.addCleanup(mock.patch.stopall)
        mock.patch.object(exporter, "TREE", tree).start()
        mock.patch.object(
            exporter, "ARCHIVE_SHA256", exporter.sha256_file(self.archive)
        ).start()

    def export(self):
        return exporter.export_archive(self.archive, self.output)

    def extract_fixture(self):
        """Write a controlled fixture, independent of tar extraction semantics."""
        root = self.root / "extracted"
        root.mkdir()
        for path, (mode, data) in self.files.items():
            if path in exporter.REMOVED:
                continue
            if path in exporter.EDITED:
                data = exporter.transform(path, data)
            item = root / path
            item.parent.mkdir(parents=True, exist_ok=True)
            if mode == "120000":
                item.symlink_to(data.decode())
            else:
                item.write_bytes(data)
                item.chmod(0o755 if mode == "100755" else 0o644)
        return root

    def test_export_preserves_case_modes_and_links_and_removes_only_declared_content(
        self,
    ):
        self.prepare()
        manifest = self.export()
        paths = {entry["path"] for entry in manifest["entries"]}
        self.assertEqual(paths, set(self.files) - exporter.REMOVED)
        self.assertEqual(len(manifest["changes"]), 8)
        self.assertIn("vendor.txt", manifest["vendor_hit_paths_pending_review"])
        with tarfile.open(self.output / "source.tar") as archive:
            self.assertEqual(archive.extractfile("source/Foo.h").read(), b"upper\n")
            self.assertEqual(archive.extractfile("source/foo.h").read(), b"lower\n")
            self.assertEqual(archive.getmember("source/link").linkname, "Foo.h")
            self.assertEqual(archive.getmember("source/scripts/run").mode, 0o755)
        self.assertEqual(
            json.loads((self.output / "manifest.json").read_text()), manifest
        )
        root = self.extract_fixture()
        if (root / "Foo.h").read_bytes() == (root / "foo.h").read_bytes():
            with self.assertRaisesRegex(ValueError, "inventory mismatch"):
                exporter.verify_directory(root, manifest)
        else:
            self.assertTrue(exporter.verify_directory(root, manifest)["match"])

    def test_git_tree_matches_independently_known_empty_tree(self):
        self.assertEqual(
            exporter.git_tree({}), "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
        )

    def test_bad_archive_hash_creates_no_output(self):
        self.prepare()
        self.archive.write_bytes(b"wrong bytes")
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            self.export()
        self.assertFalse(self.output.exists())

    def test_wrong_whole_tree_never_writes_manifest(self):
        self.prepare()
        with mock.patch.object(exporter, "TREE", "0" * 40):
            with self.assertRaisesRegex(ValueError, "whole-tree"):
                self.export()
        self.assertFalse((self.output / "manifest.json").exists())

    def test_existing_destination_is_preserved(self):
        self.prepare()
        self.output.mkdir()
        marker = self.output / "source.tar"
        marker.write_bytes(b"prior attempt")
        with self.assertRaises(FileExistsError):
            self.export()
        self.assertEqual(marker.read_bytes(), b"prior attempt")

    def test_duplicate_member_is_rejected(self):
        self.prepare(tarfile.TarInfo(exporter.PREFIX + "/Foo.h"))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.export()

    def test_traversal_is_rejected(self):
        self.prepare(tarfile.TarInfo(exporter.PREFIX + "/../outside"))
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            self.export()

    def test_hardlink_is_rejected(self):
        member = tarfile.TarInfo(exporter.PREFIX + "/hardlink")
        member.type, member.linkname = tarfile.LNKTYPE, exporter.PREFIX + "/Foo.h"
        self.prepare(member)
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            self.export()

    def test_escaping_and_chained_links_are_rejected(self):
        for target in ("../outside", "/outside", "link", "link/../Foo.h"):
            with self.subTest(target=target):
                with self.assertRaises(ValueError):
                    exporter.validate_links(
                        {"link": None, "other": None, "Foo.h": None},
                        {"link": "Foo.h", "other": target},
                    )

    def test_link_to_removed_source_is_rejected(self):
        self.files["link"] = ("120000", b"drivers/net/ethernet/microchip/enc28j60.c")
        self.prepare()
        with self.assertRaisesRegex(ValueError, "device-name"):
            self.export()

    def test_directory_links_are_checked_without_following_them(self):
        exporter.validate_links({"link": None, "dir/file": None}, {"link": "dir"})
        with self.assertRaisesRegex(ValueError, "ancestor"):
            exporter.validate_links({"link": None, "link/file": None}, {"link": "dir"})

    def test_unexpected_device_reference_fails_closed(self):
        self.files["surprise.txt"] = ("100644", b"EN28J60")
        self.prepare()
        with self.assertRaisesRegex(ValueError, "device-name"):
            self.export()
        self.assertFalse((self.output / "manifest.json").exists())

    def test_missing_expected_removal_fails(self):
        del self.files["MAINTAINERS"]
        self.prepare()
        with self.assertRaisesRegex(ValueError, "removal/edit missing"):
            self.export()

    def test_changed_registration_fails(self):
        self.files["arch/arm/configs/mxs_defconfig"] = (
            "100644",
            b"CONFIG_ENC28J60=m\n",
        )
        self.prepare()
        with self.assertRaisesRegex(ValueError, "Registration line changed"):
            self.export()

    def test_transfer_detects_case_loss_extra_file_mode_and_content_changes(self):
        self.prepare()
        manifest = self.export()
        root = self.extract_fixture()
        if (root / "Foo.h").read_bytes() == (root / "foo.h").read_bytes():
            self.skipTest("Case-sensitive transfer controls run in the Linux guest")
        mutations = [
            (
                (root / "foo.h").unlink,
                lambda: (root / "foo.h").write_bytes(b"lower\n"),
            ),
            (
                lambda: (root / "unexpected").write_bytes(b"extra"),
                (root / "unexpected").unlink,
            ),
            (
                lambda: (root / "scripts/run").chmod(0o644),
                lambda: (root / "scripts/run").chmod(0o755),
            ),
            (
                lambda: (root / "foo.h").write_bytes(b"corrupt"),
                lambda: (root / "foo.h").write_bytes(b"lower\n"),
            ),
        ]
        for mutate, restore in mutations:
            mutate()
            with self.assertRaisesRegex(ValueError, "inventory mismatch"):
                exporter.verify_directory(root, manifest)
            restore()
            self.assertTrue(exporter.verify_directory(root, manifest)["match"])

    def test_enumeration_failure_is_not_a_successful_inventory(self):
        del self.files["foo.h"]
        self.prepare()
        manifest = self.export()
        root = self.extract_fixture()
        self.assertTrue(exporter.verify_directory(root, manifest)["match"])
        hidden = root / "unreadable"
        hidden.mkdir()
        (hidden / "unexpected").write_bytes(b"extra")
        scandir = os.scandir

        def unreadable(path):
            if Path(path) == hidden:
                raise PermissionError("injected unreadable directory")
            return scandir(path)

        with mock.patch.object(exporter.os, "scandir", side_effect=unreadable):
            with self.assertRaisesRegex(PermissionError, "injected unreadable"):
                exporter.verify_directory(root, manifest)

    @unittest.skipIf(
        os.geteuid() == 0, "Real permission denial requires a non-root user"
    )
    def test_real_unreadable_extra_directory_is_rejected(self):
        del self.files["foo.h"]
        self.prepare()
        manifest = self.export()
        root = self.extract_fixture()
        self.assertTrue(exporter.verify_directory(root, manifest)["match"])
        hidden = root / "unreadable"
        hidden.mkdir()
        (hidden / "unexpected").write_bytes(b"extra")
        hidden.chmod(0)
        try:
            with self.assertRaises(PermissionError):
                exporter.verify_directory(root, manifest)
        finally:
            hidden.chmod(0o700)


if __name__ == "__main__":
    unittest.main()
