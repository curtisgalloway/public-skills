# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic inventories exercise the preparation gates, never an ENC28J60 candidate benchmark."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import prepare
import score

CANDIDATE = (b'ECON1 lives at 0x1F in every bank.\n'
             b'The receive buffer starts at 0x05FA after reset.\n')


def record(rid, proposition, **over):
    base = {
        'id': rid, 'proposition': proposition, 'weight': 'minor',
        'requirements': ['ENC28J60-REG-001'],
        'evidence': [{'start': 1, 'end': 1, 'quote': CANDIDATE.decode().split('\n')[0]}],
        'status': 'active', 'supersedes': [], 'notes': '',
    }
    base.update(over)
    return base


class PrepareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import yaml  # noqa: F401 - dependency is mandatory, not a skipped suite
        except ImportError as exc:
            raise RuntimeError('Preparation tests require PyYAML; run with uv run --with pyyaml') from exc
        cls.rows, _, _, cls.sources, _ = score.load_benchmark(ROOT)

    def setUp(self):
        self.inventory = {
            'schema': prepare.SCHEMA,
            'candidate_sha256': score.digest(CANDIDATE),
            'records': [
                record('C0001', 'ECON1 is readable from every bank.'),
                record('C0002', 'The receive buffer start defaults to 0x05FA.'),
            ],
        }

    def audit(self):
        return prepare.audit(self.inventory, CANDIDATE, self.rows)

    def packet(self, allowed=()):
        return prepare.packet(self.inventory, CANDIDATE, self.sources, set(allowed))

    def test_clean_inventory_is_ready(self):
        self.assertEqual(self.audit(), ([], []))

    def test_wrong_candidate_digest_is_an_error(self):
        self.inventory['candidate_sha256'] = score.digest(b'other')
        errors, _ = self.audit()
        self.assertTrue(any('candidate_sha256' in e for e in errors))

    def test_quote_must_match_the_candidate_lines(self):
        self.inventory['records'][0]['evidence'][0]['quote'] = 'ECON1 lives at 0x20 in every bank.'
        errors, _ = self.audit()
        self.assertTrue(any('quote differs' in e for e in errors))

    def test_duplicate_propositions_block_review(self):
        self.inventory['records'].append(record('C0003', 'econ1   IS readable from every bank.'))
        errors, _ = self.audit()
        self.assertTrue(any('duplicate proposition' in e for e in errors))

    def test_retired_parent_and_its_children_must_agree(self):
        self.inventory['records'][0]['status'] = 'retired'
        self.inventory['records'].append(
            record('C0001a', 'ECON1 is at 0x1F.', supersedes=['C0001']))
        self.assertEqual(self.audit(), ([], []))
        self.inventory['records'][0]['status'] = 'active'
        errors, _ = self.audit()
        self.assertTrue(any('still active' in e for e in errors))

    def test_retired_record_with_no_replacement_warns(self):
        self.inventory['records'][0]['status'] = 'retired'
        errors, warnings = self.audit()
        self.assertEqual(errors, [])
        self.assertTrue(any('without a replacement' in w for w in warnings))

    def test_compound_proposition_is_flagged_for_segmentation(self):
        self.inventory['records'].append(
            record('C0004', 'ERDPT is at 0x00 and ERXND is at 0x0B.'))
        _, warnings = self.audit()
        self.assertTrue(any('C0004' in w for w in warnings))

    def test_unknown_requirement_and_weight_are_errors(self):
        self.inventory['records'][0]['requirements'] = ['ENC28J60-REG-999']
        self.inventory['records'][1]['weight'] = 'urgent'
        errors, _ = self.audit()
        self.assertTrue(any('unknown requirement' in e for e in errors))
        self.assertTrue(any('invalid weight' in e for e in errors))

    def test_packet_carries_only_allowlisted_fields(self):
        self.inventory['records'][0]['notes'] = 'reader-a says this one is obvious'
        built, found = self.packet()
        self.assertEqual(found, [])
        self.assertEqual(set(built['records'][0]), set(prepare.PACKET_FIELDS))
        self.assertNotIn('notes', json.dumps(built))
        self.assertNotIn('obvious', json.dumps(built))

    def test_packet_excludes_retired_records_and_sorts_by_id(self):
        self.inventory['records'][0]['status'] = 'retired'
        self.inventory['records'].append(
            record('C0000', 'ECON1 sits at 0x1F.', supersedes=['C0001']))
        built, _ = self.packet()
        self.assertEqual([r['id'] for r in built['records']], ['C0000', 'C0002'])

    def test_packet_refuses_a_leaked_verdict(self):
        self.inventory['records'][0]['proposition'] = 'ECON1 is readable from every bank (PASS).'
        _, found = self.packet()
        self.assertTrue(any('PASS' in f for f in found))

    def test_packet_refuses_a_leaked_review_phrase(self):
        self.inventory['records'][0]['proposition'] = \
            'ECON1 is readable from every bank, as the first reader noted.'
        _, found = self.packet()
        self.assertTrue(found)

    def test_allow_releases_a_word_the_candidate_genuinely_uses(self):
        self.inventory['records'][0]['proposition'] = 'A GAP timer governs the interframe gap.'
        self.assertTrue(self.packet()[1])
        self.assertEqual(self.packet(allowed=['GAP'])[1], [])

    def test_packet_binds_the_inventory_and_offers_the_source_vocabulary(self):
        built, _ = self.packet()
        self.assertEqual(built['inventory_sha256'],
                         score.digest(score.canonical(self.inventory)))
        self.assertEqual(built['candidate_sha256'], score.digest(CANDIDATE))
        self.assertIn('DS39662E', built['sources'])
        self.assertNotIn('corpus.yaml', built['sources'])

    def test_manifest_and_alias_citations_resolve_to_pins(self):
        self.assertEqual(prepare.resolve('DS80349C', self.sources), (True, ''))
        for name in ('corpus.yaml', 'the corpus manifest', 'linux', 'errata_map'):
            citable, instead = prepare.resolve(name, self.sources)
            self.assertFalse(citable)
            self.assertTrue(instead)
        self.assertIn('no pin', prepare.resolve('DS00000Z', self.sources)[1])

    def cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / 'prepare.py'), *args],
                              capture_output=True, text=True)

    def test_cli_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / 'candidate.md').write_bytes(CANDIDATE)
            inv = tmp / 'inventory.json'
            inv.write_bytes(score.canonical(self.inventory))
            names = tmp / 'names.json'
            names.write_text(json.dumps(['DS39662E']))
            args = ['--candidate', str(tmp / 'candidate.md'), '--inventory', str(inv)]
            self.assertEqual(self.cli('sources', '--check', str(names), '--json').returncode, 0)
            names.write_text(json.dumps(['corpus.yaml']))
            refused = self.cli('sources', '--check', str(names), '--json')
            self.assertEqual(refused.returncode, 1)
            self.assertIn('DS80349C', refused.stdout)
            self.assertEqual(self.cli('inventory', *args, '--json').returncode, 0)
            out = tmp / 'packet.json'
            self.assertEqual(self.cli('packet', *args, '--output', str(out)).returncode, 0)
            self.assertEqual(self.cli('packet', *args, '--output', str(out)).returncode, 3)
            written = json.loads(out.read_text())
            self.assertEqual(written['schema'], prepare.PACKET_SCHEMA)

            dirty = copy.deepcopy(self.inventory)
            dirty['records'].append(record('C0009', 'ERDPT is at 0x00 and ERXND is at 0x0B.'))
            inv.write_bytes(score.canonical(dirty))
            self.assertEqual(self.cli('inventory', *args, '--json').returncode, 1)
            # A warning is an unanswered segmentation question, so no packet is built from it.
            self.assertEqual(self.cli('packet', *args, '--output', str(tmp / 'p2.json')).returncode, 1)
            self.assertFalse((tmp / 'p2.json').exists())

            inv.write_text('{"schema": "wrong"}')
            self.assertEqual(self.cli('inventory', *args).returncode, 3)


if __name__ == '__main__':
    unittest.main()
