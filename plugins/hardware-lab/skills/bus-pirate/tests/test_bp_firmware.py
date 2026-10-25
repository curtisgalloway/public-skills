# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline tests for bp_firmware.py: attachment parsing and directory hygiene."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import bp_firmware  # pylint: disable=wrong-import-position

# Trimmed from the real post #682 HTML (2026-10-12).
POST_HTML = (
    '<p><img src="/images/emoji/twitter/arrow_down.png" class="emoji"> '
    '<strong><a class="attachment" '
    'href="/uploads/short-url/sN5EOMB3hlr7ri8ygYyN9Bmk2jC.zip">'
    "ci-buspirate-main-322c452.zip</a></strong> (3.1 MB)</p>"
)


class FindAttachmentTest(unittest.TestCase):

    def test_parses_real_post(self):
        self.assertEqual(
            bp_firmware.find_attachment(POST_HTML),
            (
                "ci-buspirate-main-322c452.zip",
                "322c452",
                "/uploads/short-url/sN5EOMB3hlr7ri8ygYyN9Bmk2jC.zip",
            ),
        )

    def test_ignores_other_attachments(self):
        html = '<a class="attachment" href="/uploads/x.zip">pulseview-setup.zip</a>'
        self.assertIsNone(bp_firmware.find_attachment(html))

    def test_ignores_plain_text_mention(self):
        self.assertIsNone(bp_firmware.find_attachment("see ci-buspirate-main-abc1234.zip"))


class FetchTest(unittest.TestCase):

    def test_refuses_non_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            open(os.path.join(tmp, "existing"), "w").close()
            with self.assertRaises(SystemExit):
                bp_firmware.fetch("rev10", tmp)


class BoardFilesTest(unittest.TestCase):

    def test_every_board_is_a_uf2(self):
        for board, member in bp_firmware.BOARD_FILES.items():
            self.assertTrue(member.endswith(".uf2"), board)


if __name__ == "__main__":
    unittest.main()
