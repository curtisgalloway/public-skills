# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""The author's manifest must pin the sources without carrying the reading of them."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import author_manifest
import ledger_check

# Corpus sections that exist because someone read the sources. Each is either scored directly or
# pre-digests a trap a candidate is scored on reaching by itself.
WITHHELD = ('silicon_revisions', 'errata_map', 'renumbering', 'applicability_columns')


def strings(value):
    """Every string anywhere in a nested structure."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


class AuthorManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import yaml  # noqa: F401 - dependency is mandatory, not a skipped suite
        except ImportError as exc:
            raise RuntimeError('These tests require PyYAML; run with uv run --with pyyaml') from exc
        cls.corpus = ledger_check.load_yaml(ROOT / 'corpus.yaml')
        cls.manifest = author_manifest.project(cls.corpus)
        cls.rendered = author_manifest.render(cls.manifest).decode()

    def test_only_allowlisted_keys_reach_the_author(self):
        self.assertEqual(set(self.manifest),
                         set(author_manifest.CORPUS_KEYS) | {'schema', 'notice'})
        for name, doc in self.manifest['documents'].items():
            self.assertLessEqual(set(doc), set(author_manifest.DOCUMENT_KEYS), name)
            for edition in doc['editions']:
                self.assertLessEqual(set(edition), set(author_manifest.EDITION_KEYS), name)
        self.assertLessEqual(set(self.manifest['driver']), set(author_manifest.DRIVER_KEYS))

    def test_the_pins_an_author_needs_survive(self):
        datasheet = self.manifest['documents']['datasheet']
        self.assertEqual(datasheet['current'], 'E')
        self.assertEqual(len(datasheet['editions']), 5)
        for edition in datasheet['editions']:
            self.assertEqual(len(edition['sha256']), 64)
        driver = self.manifest['driver']
        self.assertEqual(driver['commit'], 'adc218676eef25575469234709c2d87185ca223a')
        self.assertEqual([f['path'] for f in driver['files']],
                         [f['path'] for f in self.corpus['driver']['files']])

    def test_no_withheld_section_leaks_a_distinctive_phrase(self):
        """A key added to a withheld corpus section must not appear in the author's copy."""
        for section in WITHHELD:
            self.assertIn(section, self.corpus, f'{section}: test is out of date with the corpus')
            self.assertNotIn(section, self.manifest)
            for text in strings(self.corpus[section]):
                # Long enough to be this benchmark's prose rather than the device's vocabulary:
                # an errata summary and the data sheet's own title share "SPI Interface", and
                # flagging that would be flagging the title the author is supposed to have.
                if len(text) >= 20:
                    self.assertNotIn(text, self.rendered, f'{section} leaked: {text!r}')

    def test_the_scored_revision_codes_and_errata_index_are_absent(self):
        # ENC28J60-REG-015 scores the EREVID codes; the errata map pre-digests the renumbering.
        for leaked in ('EREVID', '0b00000110', 'current_at_errata_c',
                       'silicon_issues', 'clarifications', 'vendor_confirmed'):
            self.assertNotIn(leaked, self.rendered)

    def test_no_corpus_comment_survives(self):
        # Comments carry the reasoning; re-emitting rather than copying is what drops them.
        source = (ROOT / 'corpus.yaml').read_text()
        comments = [line.strip().lstrip('# ') for line in source.splitlines()
                    if line.strip().startswith('#')]
        for comment in comments:
            # The SPDX header is the one comment the generator reproduces on purpose.
            if len(comment) >= 20 and not comment.startswith('SPDX-'):
                self.assertNotIn(comment, self.rendered, f'comment survived: {comment!r}')

    def test_the_errata_pairing_reading_is_withheld_but_its_cover_fact_is_not(self):
        errata = self.manifest['documents']['errata']
        self.assertNotIn('gap', errata)
        self.assertEqual([e.get('accompanies') for e in errata['editions']],
                         ['DS39662C', 'DS39662C'])

    def test_render_is_deterministic_and_check_detects_drift(self):
        self.assertEqual(author_manifest.render(self.manifest),
                         author_manifest.render(author_manifest.project(self.corpus)))
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'author-manifest.yaml'
            command = [sys.executable, str(ROOT / 'author_manifest.py')]
            self.assertEqual(
                subprocess.run(command + ['--output', str(out)], capture_output=True).returncode, 0)
            self.assertEqual(
                subprocess.run(command + ['--output', str(out)], capture_output=True).returncode, 3)
            self.assertEqual(
                subprocess.run(command + ['--check', str(out)], capture_output=True).returncode, 0)
            out.write_bytes(self.rendered.encode().replace(b'enc28j60', b'other', 1))
            self.assertEqual(
                subprocess.run(command + ['--check', str(out)], capture_output=True).returncode, 1)


if __name__ == '__main__':
    unittest.main()
