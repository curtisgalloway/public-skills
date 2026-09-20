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
import prepare
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
        cls.records = []
        for row in cls.rows:
            if not score.roster(row):
                continue
            for i in range(1, cls.counts.get(row['id'], 1) + 1):
                cid = f"{row['id']}-{i}"
                cls.records.append({
                    'id': cid, 'proposition': f'Synthetic proposition {cid}',
                    'weight': 'minor', 'requirements': [row['id']],
                    'evidence': [{'start': 1, 'end': 1,
                                  'quote': cls.candidate.decode().strip()}]})
        cls.inventory = {
            'schema': 'enc28j60-inventory-2', 'candidate_sha256': score.digest(cls.candidate),
            'allowances': [],
            'records': [dict(r, status='active', supersedes=[], segmentation='', notes='')
                        for r in cls.records],
        }
        cls.inventory_bytes = score.canonical(cls.inventory)
        # The packet is what the preparation tool actually emits for this inventory: the scorer
        # rebuilds it and compares, so a hand-written fixture would only test the fixture.
        cls.packet, lint = prepare.packet(cls.inventory, cls.candidate, cls.sources)
        assert not lint, lint
        cls.packet_bytes = score.canonical(cls.packet)
        cls.base = score.template(cls.rows, cls.counts, cls.facts, cls.inputs,
                                  cls.packet, cls.packet_bytes)
        cls.base['reviewers'] = ['reviewer-a', 'reviewer-b']
        cls.base['preparation']['responses'] = [
            {'reviewer': who, 'packet_sha256': score.digest(cls.packet_bytes)}
            for who in cls.base['reviewers']]
        cls.base['audit'] = {'reviewer': 'reviewer-a', 'complete': True,
                             'notes': 'Synthetic fixture: inventory declared complete.'}
        cls.base['cleanroom'] = {'reviewer': 'reviewer-b', 'verdict': 'PASS',
                                 'notes': 'Synthetic fixture: boundary declared checked.'}
        by_id = {claim['id']: claim for claim in cls.base['claims']}
        for row in cls.base['coverage']:
            for fact in row['facts']:
                cid = f"{row['id']}-{fact['number']}"
                fact.update(state='correct', claims=[cid], notes='Synthetic judgment.')
                by_id[cid].update(verdict='PASS', reviews=[
                    {'reviewer': who, 'verdict': 'PASS',
                     'sources': [{'source': 'DS39662E', 'locator': 'synthetic locator'}],
                     'rationale': 'Synthetic agreement.'} for who in cls.base['reviewers']])

    def setUp(self):
        self.review = copy.deepcopy(self.base)
        self.packet = copy.deepcopy(type(self).packet)
        self.packet_bytes = score.canonical(self.packet)

    def reseal(self):
        """Re-issue the packet after a test changes what the reviewers were given."""
        self.packet_bytes = score.canonical(self.packet)
        self.review['preparation']['packet_sha256'] = score.digest(self.packet_bytes)
        for response in self.review['preparation']['responses']:
            response['packet_sha256'] = score.digest(self.packet_bytes)

    def give(self, claim):
        """Add a claim to the review and to the packet it must answer."""
        self.review['claims'].append(claim)
        self.packet['records'].append(
            {field: claim[field] for field in
             ('id', 'proposition', 'weight', 'requirements', 'evidence')})
        self.reseal()

    def result(self):
        return score.score(self.rows, self.counts, self.facts, self.sources, self.inputs,
                           self.candidate, self.review, self.packet, self.packet_bytes)

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
        self.give(extra)
        self.assertEqual(self.result()['precision']['errors'], 1)
        self.assert_blocked(self.result())

    def test_inference_attribution_error_keeps_recall(self):
        claim = self.claim(self.entry('RX-006')['facts'][0])
        self.set_verdict(claim, 'FAIL', 'attribution_error')
        result = self.result()
        self.assertEqual(result['recall']['overall']['recall'], 1)
        self.assertEqual(result['precision']['errors'], 1)

    def test_unsupported_partial_and_adjudicate_precision_accounting(self):
        # The packet sorts records by id, so reach the claims through the facts they evidence.
        for fact, verdict in zip(self.review['coverage'][0]['facts'][:3],
                                 ('UNVERIFIABLE', 'GAP', 'ADJUDICATE')):
            self.set_verdict(self.claim(fact), verdict)
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
        shared = self.review['claims'][0]['proposition']
        self.review['claims'][1]['proposition'] = shared
        self.packet['records'][1]['proposition'] = shared
        self.reseal()
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
        self.review = score.template(self.rows, self.counts, self.facts, self.inputs,
                                     self.packet, self.packet_bytes)
        self.review['reviewers'] = ['reviewer-a']
        self.review['preparation']['responses'] = [
            {'reviewer': 'reviewer-a', 'packet_sha256': score.digest(self.packet_bytes)}]
        result = self.result()
        self.assert_blocked(result)
        self.assertEqual(result['review_status'], 'incomplete')
        self.assertEqual(result['measurement_status'], 'provisional')
        # The frozen policy's precision is an upper bound over every claim, so an all-pending
        # template computes one. Nothing has been judged: the settled figure is the honest n/a,
        # and every claim is counted as pending beside it.
        precision = result['precision']
        self.assertEqual(precision['precision'], 1.0)
        self.assertIsNone(precision['settled_precision'])
        self.assertEqual(precision['pending'], precision['claims'])

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
            self.packet = copy.deepcopy(type(self).packet)
            self.give(extra)
            fact['claims'].append(extra['id'])
            fact['state'] = state
            with self.assertRaisesRegex(ValueError, 'non-contradicted fact'):
                self.result()

    def test_crlf_and_unicode_separator_use_editor_line_numbers(self):
        self.candidate = 'One line with a unicode separator: \u2028 still line one.\r\n'.encode()
        self.inputs = score.identity(self.blobs, self.candidate)
        self.review['inputs'] = self.inputs
        quote = self.candidate.decode().removesuffix('\r\n')
        for claim in self.review['claims']:
            claim['evidence'][0]['quote'] = quote
        for given in self.packet['records']:
            given['evidence'][0]['quote'] = quote
        self.packet['candidate_sha256'] = score.digest(self.candidate)
        self.reseal()
        self.assertEqual(self.result()['acceptance']['spec_ready']['status'], 'accepted')

    def test_template_cli_refuses_overwrite_and_archives_blocked_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            candidate, review = tmp / 'candidate.md', tmp / 'review.json'
            candidate.write_bytes(self.candidate)
            packet = tmp / 'packet.json'
            packet.write_bytes(self.packet_bytes)
            command = [sys.executable, str(ROOT / 'score.py'), 'template', '--candidate',
                       str(candidate), '--packet', str(packet), '--output', str(review)]
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
            original = review.read_bytes()
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 3)
            self.assertEqual(original, review.read_bytes())
            attempt = tmp / 'attempt'
            inventory = tmp / 'inventory.json'
            inventory.write_bytes(self.inventory_bytes)
            blocked = subprocess.run([sys.executable, str(ROOT / 'score.py'), 'score',
                                      '--candidate', str(candidate), '--review', str(review),
                                      '--packet', str(packet), '--inventory', str(inventory),
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
        entries, context = self.facts['ENC28J60-REG-001']
        self.assertEqual([f['text'] for f in composite], entries)
        self.assertEqual(self.entry('REG-001')['context'], context)
        self.assertIn('Bank membership', context)
        atomic = self.entry('REG-012')['facts']
        row = next(r for r in self.rows if r['id'] == 'ENC28J60-REG-012')
        self.assertEqual(len(atomic), 1)
        self.assertEqual(atomic[0]['text'], row['statement'])

    def test_every_reviewer_names_the_packet_it_answered(self):
        self.review['preparation']['responses'][1]['packet_sha256'] = score.digest(b'other')
        with self.assertRaisesRegex(ValueError, 'answered a different packet'):
            self.result()
        self.review['preparation']['responses'].pop()
        with self.assertRaisesRegex(ValueError, 'every reviewer names the packet'):
            self.result()

    def test_manifest_only_claim_is_judged_but_earns_no_coverage_credit(self):
        fact = self.entry('REG-001')['facts'][0]
        claim = self.claim(fact)
        for rev in claim['reviews']:
            rev['sources'] = [{'source': score.MANIFEST, 'locator': 'documents.datasheet'}]
        with self.assertRaisesRegex(ValueError, 'cites only the manifest'):
            self.result()
        # Unlinked from coverage it is still a claim, and still counted for precision.
        fact.update(state='absent', claims=[], notes='')
        result = self.result()
        self.assertEqual(result['precision']['claims'], len(self.review['claims']))
        self.assert_blocked(result)

    def test_a_claim_citing_both_manifest_and_pin_keeps_its_credit(self):
        claim = self.claim(self.entry('REG-001')['facts'][0])
        for rev in claim['reviews']:
            rev['sources'] = [{'source': score.MANIFEST, 'locator': 'documents.datasheet'},
                              {'source': 'DS39662E', 'locator': 'T3-1 bank 0'}]
        self.assertEqual(self.result()['acceptance']['spec_ready']['status'], 'accepted')

    def test_score_cli_refuses_an_inventory_the_packet_does_not_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            for name, data in (('candidate.md', self.candidate),
                               ('review.json', score.canonical(self.review)),
                               ('packet.json', self.packet_bytes)):
                (tmp / name).write_bytes(data)
            other = copy.deepcopy(self.inventory)
            other['records'][0]['notes'] = 'edited after the packet was built'
            (tmp / 'inventory.json').write_bytes(score.canonical(other))
            run = subprocess.run(
                [sys.executable, str(ROOT / 'score.py'), 'score',
                 '--candidate', str(tmp / 'candidate.md'), '--review', str(tmp / 'review.json'),
                 '--packet', str(tmp / 'packet.json'), '--inventory', str(tmp / 'inventory.json'),
                 '--output', str(tmp / 'attempt')], capture_output=True, text=True)
            self.assertEqual(run.returncode, 3)
            self.assertIn('not the one this packet was built from', run.stderr)
            self.assertFalse((tmp / 'attempt').exists())

    def test_a_packet_the_inventory_does_not_produce_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            forged = copy.deepcopy(self.packet)
            forged['reader_a_verdicts'] = {'C0001': 'PASS'}
            for name, data in (('candidate.md', self.candidate),
                               ('review.json', score.canonical(self.review)),
                               ('packet.json', score.canonical(forged)),
                               ('inventory.json', self.inventory_bytes)):
                (tmp / name).write_bytes(data)
            run = subprocess.run(
                [sys.executable, str(ROOT / 'score.py'), 'score',
                 '--candidate', str(tmp / 'candidate.md'), '--review', str(tmp / 'review.json'),
                 '--packet', str(tmp / 'packet.json'), '--inventory', str(tmp / 'inventory.json'),
                 '--output', str(tmp / 'attempt')], capture_output=True, text=True)
            self.assertEqual(run.returncode, 3)
            self.assertIn('packet', run.stderr)
            self.assertFalse((tmp / 'attempt').exists())

    def test_edited_packet_records_pass_structure_and_fail_the_rebuild(self):
        forged = copy.deepcopy(self.packet)
        forged['records'][0]['weight'] = 'critical'
        # Structurally it is a packet, and its digest still names a clean inventory. Only
        # rebuilding the packet from that inventory catches the edit.
        self.assertEqual(score.load_packet(score.canonical(forged), self.candidate), forged)
        rebuilt, lint = prepare.packet(self.inventory, self.candidate, self.sources)
        self.assertEqual(lint, [])
        self.assertNotEqual(forged, rebuilt)
        self.assertEqual(forged['inventory_sha256'], rebuilt['inventory_sha256'])
        # Bind the review to the forged packet, so nothing but the rebuild can refuse the run.
        forged_bytes = score.canonical(forged)
        self.review['preparation']['packet_sha256'] = score.digest(forged_bytes)
        for response in self.review['preparation']['responses']:
            response['packet_sha256'] = score.digest(forged_bytes)
        self.claim(self.entry('REG-001')['facts'][0])['weight'] = 'critical'
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            for name, data in (('candidate.md', self.candidate),
                               ('review.json', score.canonical(self.review)),
                               ('packet.json', forged_bytes),
                               ('inventory.json', self.inventory_bytes)):
                (tmp / name).write_bytes(data)
            run = subprocess.run(
                [sys.executable, str(ROOT / 'score.py'), 'score',
                 '--candidate', str(tmp / 'candidate.md'), '--review', str(tmp / 'review.json'),
                 '--packet', str(tmp / 'packet.json'), '--inventory', str(tmp / 'inventory.json'),
                 '--output', str(tmp / 'attempt')], capture_output=True, text=True)
            self.assertEqual(run.returncode, 3)
            self.assertIn('not the packet this inventory produces', run.stderr)
            self.assertFalse((tmp / 'attempt').exists())

    def test_a_manifest_only_response_is_not_an_independent_technical_review(self):
        claim = self.claim(self.entry('REG-001')['facts'][0])
        claim['weight'] = 'critical'
        self.packet['records'] = [dict(r, weight='critical') if r['id'] == claim['id'] else r
                                  for r in self.packet['records']]
        self.reseal()
        claim['reviews'][1]['sources'] = [{'source': score.MANIFEST, 'locator': 'documents'}]
        result = self.result()
        # Both readers still count as reviews; only one of them read a pinned document.
        scored = next(c for c in self.review['claims'] if c['id'] == claim['id'])
        self.assertEqual(len(scored['reviews']), 2)
        reasons = result['acceptance']['spec_ready']['reasons']
        self.assertTrue(any('lacks two independent reviews' in r for r in reasons))

    def test_empty_bucket_is_null(self):
        self.assertIsNone(score.bucket([])['recall'])

    def test_claim_quotes_must_match_candidate(self):
        self.review['claims'][0]['evidence'][0]['quote'] = 'invented'
        with self.assertRaisesRegex(ValueError, 'evidence differs from the packet'):
            self.result()
        self.packet['records'][0]['evidence'][0]['quote'] = 'invented'
        self.reseal()
        with self.assertRaisesRegex(ValueError, 'quote differs'):
            self.result()

    def test_immutable_archive_and_offline_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            candidate, review, attempt = tmp / 'candidate.md', tmp / 'review.json', tmp / 'attempt'
            candidate.write_bytes(self.candidate)
            review.write_bytes(score.canonical(self.review))
            packet = tmp / 'packet.json'
            packet.write_bytes(self.packet_bytes)
            inventory = tmp / 'inventory.json'
            inventory.write_bytes(self.inventory_bytes)
            command = [sys.executable, str(ROOT / 'score.py'), 'score', '--candidate',
                       str(candidate), '--review', str(review), '--packet', str(packet),
                       '--inventory', str(inventory), '--output', str(attempt)]
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
                                     str(attempt / 'review.json'), '--packet',
                                     str(attempt / 'packet.json'), '--inventory',
                                     str(attempt / 'inventory.json'), '--output',
                                     str(tmp / 'replay')],
                                    capture_output=True, text=True)
            self.assertEqual(replay.returncode, 0, replay.stderr)
            replayed = json.loads((tmp / 'replay' / 'result.json').read_bytes())
            for result in (report, replayed):
                result.pop('created_at')
                result.pop('runtime')
            self.assertEqual(report, replayed)


if __name__ == '__main__':
    unittest.main()
