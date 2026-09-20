# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic judgments exercise the tool, never an ENC28J60 candidate benchmark."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import score


class ScoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import yaml  # noqa: F401 - dependency is mandatory, not a skipped scoring suite
        except ImportError as exc:
            raise RuntimeError('Scorer tests require PyYAML; run with uv run --with pyyaml') from exc
        cls.rows, cls.counts, cls.facts, cls.sources, cls.blobs = score.load_benchmark()
        cls.candidate = b'Synthetic assertion; not a hardware specification.\n'
        cls.inputs = score.identity(cls.blobs, cls.candidate)
        cls.base = score.template(cls.rows, cls.counts, cls.facts, cls.inputs)
        cls.base['reviewers'] = ['reviewer-a', 'reviewer-b']
        cls.base['audit'] = {'reviewer': 'reviewer-a', 'complete': True,
                             'notes': 'Synthetic fixture: inventory declared complete.'}
        cls.base['cleanroom'] = {'reviewer': 'reviewer-b', 'verdict': 'PASS',
                                 'notes': 'Synthetic fixture: boundary declared checked.'}
        for row in cls.base['coverage']:
            for fact in row['facts']:
                cid = f"{row['id']}-{fact['number']}"
                fact.update(state='correct', claims=[cid], notes='Synthetic judgment.')
                cls.base['claims'].append({
                    'id': cid, 'proposition': f'Synthetic proposition {cid}',
                    'weight': 'minor', 'verdict': 'PASS', 'error': 'none',
                    'requirements': [row['id']],
                    'evidence': [{'start': 1, 'end': 1,
                                  'quote': cls.candidate.decode().strip()}],
                    'reviews': [{'reviewer': who, 'verdict': 'PASS',
                                 'sources': [{'source': 'DS39662E', 'locator': 'synthetic locator'}],
                                 'rationale': 'Synthetic agreement.'}
                                for who in cls.base['reviewers']],
                })

    def setUp(self):
        self.review = copy.deepcopy(self.base)

    def result(self):
        return score.score(self.rows, self.counts, self.facts, self.sources, self.inputs,
                           self.candidate, self.review)

    def entry(self, rid):
        return next(e for e in self.review['coverage'] if e['id'] == 'ENC28J60-' + rid)

    def claim(self, fact):
        return next(c for c in self.review['claims'] if c['id'] == fact['claims'][0])

    def set_verdict(self, claim, verdict, error='none'):
        claim.update(verdict=verdict, error=error)
        for rev in claim['reviews']:
            rev['verdict'] = verdict

    def assert_blocked(self, result):
        self.assertEqual(result['acceptance']['spec_ready']['status'], 'blocked')

    def test_full_synthetic_review_uses_frozen_denominator(self):
        result = self.result()
        self.assertEqual(result['recall']['overall']['eligible_rows'], 162)
        self.assertEqual(result['recall']['overall']['recall'], 1)
        self.assertEqual(result['acceptance']['spec_ready']['status'], 'accepted')
        self.assertEqual(result['acceptance']['hardware_validated']['status'], 'blocked')

    def test_zero_failures_one_missing_critical_is_blocked(self):
        for fact in self.entry('REG-001')['facts']:
            fact.update(state='absent', claims=[])
        result = self.result()
        self.assertEqual(result['precision']['errors'], 0)
        self.assert_blocked(result)
        self.assertEqual(result['recall']['critical']['verdicts']['missing'], 1)

    def test_missing_section_does_not_shrink_denominator(self):
        for entry in self.review['coverage']:
            if entry['id'].startswith('ENC28J60-RX-'):
                for fact in entry['facts']:
                    fact.update(state='absent', claims=[])
        result = self.result()
        self.assertEqual(result['recall']['overall']['eligible_rows'], 162)
        self.assertLess(result['recall']['overall']['recall'], 1)
        self.assert_blocked(result)

    def test_wrong_constant_lowers_precision_and_zeroes_composite(self):
        fact = self.entry('REG-001')['facts'][0]
        fact['state'] = 'contradicted'
        self.set_verdict(self.claim(fact), 'FAIL', 'contradicted')
        result = self.result()
        self.assertEqual(result['precision']['errors'], 1)
        self.assertLess(result['precision']['precision'], 1)
        row = next(r for r in result['coverage'] if r['id'].endswith('REG-001'))
        self.assertEqual((row['verdict'], row['credit']), ('misstated', '0'))
        self.assert_blocked(result)

    def test_proportional_credit_and_named_missed_critical_fact(self):
        fact = self.entry('PHY-018')['facts'][0]
        fact.update(state='absent', claims=[])
        result = self.result()
        row = next(r for r in result['coverage'] if r['id'].endswith('PHY-018'))
        self.assertEqual(row['credit'], '4/5')
        self.assertEqual(row['missed_critical_facts'], [1])
        self.assert_blocked(result)

    def test_atomic_partial_and_zero_credit_composite_partial(self):
        atomic = next(e for e in self.review['coverage'] if e['id'] not in self.counts)
        atomic['facts'][0]['state'] = 'underspecified'
        for fact in self.entry('REG-001')['facts']:
            fact['state'] = 'underspecified'
        result = self.result()
        by_id = {r['id']: r for r in result['coverage']}
        self.assertEqual(by_id[atomic['id']]['credit'], '1/2')
        self.assertEqual(by_id['ENC28J60-REG-001']['credit'], '0')
        self.assertEqual(by_id['ENC28J60-REG-001']['verdict'], 'partial')

    def test_stale_candidate_or_tool_or_lock_blocks(self):
        for name in ('candidate_sha256', 'sha256'):
            with self.subTest(name=name):
                self.review = copy.deepcopy(self.base)
                if name == 'sha256':
                    self.review['inputs'][name]['ledger.lock'] = '0' * 64
                else:
                    self.review['inputs'][name] = '0' * 64
                decision = self.result()['acceptance']['spec_ready']
                self.assertEqual(decision['status'], 'stale')
                expected = 'input digest changed: ledger.lock' if name == 'sha256' else \
                    'input changed: candidate_sha256'
                self.assertIn(expected, decision['reasons'])

    def test_policy_mismatch_refused(self):
        self.review['inputs']['acceptance_policy'] = 'future-policy'
        with self.assertRaisesRegex(ValueError, 'version mismatch'):
            self.result()

    def test_critical_unverifiable_adjudicate_and_missing_independent_review(self):
        for verdict in ('UNVERIFIABLE', 'ADJUDICATE'):
            with self.subTest(verdict=verdict):
                self.review = copy.deepcopy(self.base)
                fact = self.entry('REG-001')['facts'][0]
                fact['state'] = 'underspecified'
                self.set_verdict(self.claim(fact), verdict)
                self.assert_blocked(self.result())
        self.review = copy.deepcopy(self.base)
        self.claim(self.entry('REG-001')['facts'][0])['reviews'].pop()
        self.assert_blocked(self.result())

    def test_extra_out_of_scope_claim_error_still_counts(self):
        extra = copy.deepcopy(self.review['claims'][0])
        extra.update(id='extra', proposition='An extra assertion.', requirements=['ENC28J60-IRQ-016'])
        self.set_verdict(extra, 'FAIL', 'contradicted')
        self.review['claims'].append(extra)
        self.assertEqual(self.result()['precision']['errors'], 1)
        self.assert_blocked(self.result())

    def test_inference_attribution_error_keeps_recall(self):
        claim = self.claim(self.entry('RX-006')['facts'][0])
        self.set_verdict(claim, 'FAIL', 'attribution_error')
        result = self.result()
        self.assertEqual(result['recall']['overall']['recall'], 1)
        self.assertEqual(result['precision']['errors'], 1)

    def test_unsupported_partial_and_adjudicate_precision_accounting(self):
        for claim, verdict in zip(self.review['claims'][:3], ('UNVERIFIABLE', 'GAP', 'ADJUDICATE')):
            self.set_verdict(claim, verdict)
        for fact in self.review['coverage'][0]['facts'][:3]:
            fact['state'] = 'underspecified'
        precision = self.result()['precision']
        self.assertEqual(precision['precision'], 1)
        self.assertEqual(precision['denominator'], precision['claims'])
        self.assertEqual(precision['settled_denominator'], precision['claims'] - 1)
        self.assertEqual((precision['unsupported'], precision['partial'], precision['adjudicate']),
                         (1, 1, 1))

    def test_missing_row_fact_and_dangling_claim_refused(self):
        mutations = [lambda r: r['coverage'].pop(),
                     lambda r: r['coverage'][0]['facts'].pop(),
                     lambda r: r['coverage'][0]['facts'][0].update(claims=['unknown'])]
        for mutate in mutations:
            self.review = copy.deepcopy(self.base)
            mutate(self.review)
            with self.assertRaises(ValueError):
                self.result()

    def test_duplicate_semantic_claims_require_audit_and_literal_duplicates_fail(self):
        self.review['claims'][1]['proposition'] = self.review['claims'][0]['proposition']
        with self.assertRaisesRegex(ValueError, 'duplicate proposition'):
            self.result()

    def test_nonpublic_source_and_profile_refused(self):
        self.review['claims'][0]['reviews'][0]['sources'][0]['source'] = '<private-source>'
        with self.assertRaisesRegex(ValueError, 'outside frozen public corpus'):
            self.result()
        self.review = copy.deepcopy(self.base)
        self.review['run']['access_profile'] = 'vendor-confidential'
        with self.assertRaisesRegex(ValueError, 'public-only'):
            self.result()

    def test_pending_template_never_accepts(self):
        self.review = score.template(self.rows, self.counts, self.facts, self.inputs)
        result = self.result()
        self.assert_blocked(result)
        self.assertIsNone(result['precision']['precision'])
        self.assertEqual(result['measurement_status'], 'provisional')

    def test_pending_fact_is_not_hidden_by_another_contradiction(self):
        facts = self.entry('REG-001')['facts']
        facts[0]['state'] = 'contradicted'
        self.set_verdict(self.claim(facts[0]), 'FAIL', 'contradicted')
        facts[1].update(state='pending', claims=[])
        self.assertEqual(self.result()['measurement_status'], 'provisional')

    def test_incomplete_audit_cleanroom_and_self_review_block(self):
        self.review['audit']['complete'] = False
        self.assert_blocked(self.result())
        self.review = copy.deepcopy(self.base)
        self.review['cleanroom']['verdict'] = 'FAIL'
        self.assert_blocked(self.result())
        self.review = copy.deepcopy(self.base)
        self.review['run']['author'] = 'reviewer-a'
        with self.assertRaisesRegex(ValueError, 'author cannot'):
            self.result()

    def test_changed_frozen_benchmark_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            for name in score.FILES:
                (tmp / name).write_bytes(self.blobs[name])
            (tmp / 'SCORING-FACTS.md').write_bytes(self.blobs['SCORING-FACTS.md'] + b'\n')
            with self.assertRaisesRegex(ValueError, 'invalid frozen benchmark'):
                score.load_benchmark(tmp)

    def test_correct_noncritical_fact_needs_supported_claim(self):
        by_id = {r['id']: r for r in self.rows}
        for verdict in ('GAP', 'UNVERIFIABLE', 'ADJUDICATE', 'PENDING'):
            self.review = copy.deepcopy(self.base)
            entry = next(e for e in self.review['coverage']
                         if by_id[e['id']]['weight'] != 'critical')
            self.set_verdict(self.claim(entry['facts'][0]), verdict)
            # PENDING claim reviews have no settled verdict yet.
            if verdict == 'PENDING':
                self.claim(entry['facts'][0])['reviews'] = []
            with self.assertRaisesRegex(ValueError, 'correct fact needs supported content'):
                self.result()

    def test_precision_policy_and_settled_ratios_are_distinct(self):
        facts = self.entry('REG-001')['facts']
        facts[0]['state'] = 'contradicted'
        self.set_verdict(self.claim(facts[0]), 'FAIL', 'contradicted')
        facts[1]['state'] = 'underspecified'
        self.set_verdict(self.claim(facts[1]), 'ADJUDICATE')
        precision = self.result()['precision']
        self.assertGreater(precision['precision'], precision['settled_precision'])

    def test_complete_review_still_has_provisional_measurement(self):
        result = self.result()
        self.assertEqual(result['review_status'], 'complete')
        self.assertEqual(result['measurement_status'], 'provisional')

    def test_duplicate_json_keys_refused(self):
        with self.assertRaisesRegex(ValueError, 'duplicate JSON key'):
            score.read_json(b'{"claims": [], "claims": []}')

    def test_mixed_contradictory_evidence_cannot_inflate_recall(self):
        for state in ('correct', 'underspecified'):
            self.review = copy.deepcopy(self.base)
            fact = self.entry('REG-001')['facts'][0]
            extra = copy.deepcopy(self.claim(fact))
            extra.update(id='contradictory-extra', proposition='A contradictory extra assertion.')
            self.set_verdict(extra, 'FAIL', 'contradicted')
            self.review['claims'].append(extra)
            fact['claims'].append(extra['id'])
            fact['state'] = state
            with self.assertRaisesRegex(ValueError, 'non-contradicted fact'):
                self.result()

    def test_crlf_and_unicode_separator_use_editor_line_numbers(self):
        self.candidate = 'One line with a unicode separator: \u2028 still line one.\r\n'.encode()
        self.inputs = score.identity(self.blobs, self.candidate)
        self.review['inputs'] = self.inputs
        for claim in self.review['claims']:
            claim['evidence'][0]['quote'] = self.candidate.decode().removesuffix('\r\n')
        self.assertEqual(self.result()['acceptance']['spec_ready']['status'], 'accepted')

    def test_template_cli_refuses_overwrite_and_archives_blocked_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            candidate, review = tmp / 'candidate.md', tmp / 'review.json'
            candidate.write_bytes(self.candidate)
            command = [sys.executable, str(ROOT / 'score.py'), 'template',
                       '--candidate', str(candidate), '--output', str(review)]
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
            original = review.read_bytes()
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 3)
            self.assertEqual(original, review.read_bytes())
            attempt = tmp / 'attempt'
            blocked = subprocess.run([sys.executable, str(ROOT / 'score.py'), 'score',
                                      '--candidate', str(candidate), '--review', str(review),
                                      '--output', str(attempt)], capture_output=True, text=True)
            self.assertEqual(blocked.returncode, 1, blocked.stderr)
            self.assertEqual((attempt / 'review.json').read_bytes(), original)
            result = json.loads((attempt / 'result.json').read_bytes())
            self.assertEqual(result['acceptance']['spec_ready']['status'], 'blocked')

    def test_edited_fact_text_is_refused(self):
        fact = self.entry('REG-001')['facts'][0]
        fact['text'] = fact['text'].replace('0x00', '0x20')
        with self.assertRaises(ValueError):
            self.result()

    def test_template_carries_the_frozen_fact_wording(self):
        composite = self.entry('REG-001')['facts']
        frozen = self.facts['ENC28J60-REG-001']
        self.assertEqual([f['text'] for f in composite], frozen)
        atomic = self.entry('REG-012')['facts']
        row = next(r for r in self.rows if r['id'] == 'ENC28J60-REG-012')
        self.assertEqual(len(atomic), 1)
        self.assertEqual(atomic[0]['text'], row['statement'])

    def test_empty_bucket_is_null(self):
        self.assertIsNone(score.bucket([])['recall'])

    def test_claim_quotes_must_match_candidate(self):
        self.review['claims'][0]['evidence'][0]['quote'] = 'invented'
        with self.assertRaisesRegex(ValueError, 'quote differs'):
            self.result()

    def test_immutable_archive_and_offline_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            candidate, review, attempt = tmp / 'candidate.md', tmp / 'review.json', tmp / 'attempt'
            candidate.write_bytes(self.candidate)
            review.write_bytes(score.canonical(self.review))
            command = [sys.executable, str(ROOT / 'score.py'), 'score', '--candidate',
                       str(candidate), '--review', str(review), '--output', str(attempt)]
            first = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            archived = (attempt / 'result.json').read_bytes()
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 3)
            self.assertEqual((attempt / 'result.json').read_bytes(), archived)
            report = json.loads(archived)
            for name, expected in report['artifacts'].items():
                self.assertEqual(score.digest((attempt / name).read_bytes()), expected)
            replay = subprocess.run([sys.executable, str(attempt / 'score.py'), 'score',
                                     '--candidate', str(attempt / 'candidate.md'), '--review',
                                     str(attempt / 'review.json'), '--output', str(tmp / 'replay')],
                                    capture_output=True, text=True)
            self.assertEqual(replay.returncode, 0, replay.stderr)
            replayed = json.loads((tmp / 'replay' / 'result.json').read_bytes())
            for result in (report, replayed):
                result.pop('created_at')
                result.pop('runtime')
            self.assertEqual(report, replayed)


if __name__ == '__main__':
    unittest.main()
