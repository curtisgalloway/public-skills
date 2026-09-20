#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Score reviewed ENC28J60 claims and coverage; preserve an exclusive attempt directory.

Requires PyYAML. See SCORING-RUN.md for the review contract and trust boundaries.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

import ledger_check

HERE = Path(__file__).resolve().parent
ACCEPT_PATH = HERE / 'strict_accept.py'
if not ACCEPT_PATH.exists():
    ACCEPT_PATH = HERE / '../../skills/board-expert/scripts/strict_accept.py'
spec = importlib.util.spec_from_file_location('strict_accept', ACCEPT_PATH)
strict_accept = importlib.util.module_from_spec(spec)
spec.loader.exec_module(strict_accept)
SCHEMA = 'enc28j60-review-3'
PACKET_SCHEMA = 'enc28j60-packet-1'
# The pin manifest is citable for a proposition about its own contents, and for nothing
# else: a manifest-only claim earns no coverage credit (see `score`).
MANIFEST = 'corpus.yaml'
PACKET_RECORD = ('id', 'proposition', 'weight', 'requirements', 'evidence')
POLICY = 'enc28j60-1.4'
FILES = ('ledger.yaml', 'ledger.lock', 'corpus.yaml', 'SCORING-POLICY.md',
         'SCORING-FACTS.md', 'LEDGER-FORMAT.md')
RECALL_CLASSES = {'documented-hardware-requirement', 'inference', 'unresolved-conflict'}
FACT_STATES = {'correct', 'underspecified', 'contradicted', 'absent', 'pending'}
CLAIM_VERDICTS = {'PASS', 'FAIL', 'GAP', 'UNVERIFIABLE', 'ADJUDICATE', 'PENDING'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + '\n').encode()


def read_json(data):
    def unique(pairs):
        obj = {}
        for key, value in pairs:
            require(key not in obj, f'duplicate JSON key: {key}')
            obj[key] = value
        return obj
    return json.loads(data, object_pairs_hook=unique)


def text(value, where):
    require(isinstance(value, str) and bool(value.strip()), f'{where}: expected nonempty text')


def keys(value, expected, where):
    require(isinstance(value, dict) and set(value) == set(expected),
            f'{where}: expected fields {sorted(expected)}')


def unique_list(value, where):
    require(isinstance(value, list) and all(isinstance(v, str) and v.strip() for v in value),
            f'{where}: expected list of nonempty strings')
    require(len(value) == len(set(value)), f'{where}: duplicate entries')


def load_benchmark(root=HERE):
    blobs = {name: (root / name).read_bytes() for name in FILES}
    ledger = ledger_check.load_yaml(root / 'ledger.yaml')
    corpus = ledger_check.load_yaml(root / 'corpus.yaml')
    lock = ledger_check.load_yaml(root / 'ledger.lock')
    errors, _, _ = ledger_check.check(
        ledger, corpus, blobs['ledger.yaml'], blobs['corpus.yaml'], lock=lock, freeze=True,
        policy_bytes=blobs['SCORING-POLICY.md'], format_bytes=blobs['LEDGER-FORMAT.md'],
        facts_bytes=blobs['SCORING-FACTS.md'])
    require(not errors, 'invalid frozen benchmark: ' + '; '.join(errors))
    require(lock['policy_version'] == POLICY, 'unsupported scoring policy version')
    blobs['score.py'] = Path(__file__).read_bytes()
    blobs['ledger_check.py'] = Path(ledger_check.__file__).read_bytes()
    blobs['strict_accept.py'] = ACCEPT_PATH.read_bytes()
    blobs['prepare.py'] = (root / 'prepare.py').read_bytes()
    counts = ledger_check.policy_fact_counts(blobs['SCORING-POLICY.md'])
    facts = ledger_check.facts_text(blobs['SCORING-FACTS.md'])
    # The template copies fact text; the copy is only safe while it is re-derivable from the
    # frozen file, so a list whose length disagrees with the frozen count stops the run here.
    for rid, n in counts.items():
        require(len(facts.get(rid, ((), ''))[0]) == n,
                f'{rid}: frozen fact list does not match its count')
    return ledger['rows'], counts, facts, \
        ledger_check.corpus_sources(corpus)[0] | {MANIFEST}, blobs


def identity(blobs, candidate):
    return {
        'sha256': {name: digest(data) for name, data in blobs.items()},
        'candidate_sha256': digest(candidate),
        'scoring_policy': POLICY, 'acceptance_policy': strict_accept.VERSION,
    }


def roster(row):
    return row['status'] == 'active' and row['in_scope'] and row['recoverable']


def eligible(row):
    return roster(row) and row['class'] in RECALL_CLASSES


def fact_text(row, counts, facts, number):
    """The frozen wording of one numbered fact: the listed entry, or an atomic row's statement."""
    if counts.get(row['id'], 1) > 1:
        return facts[row['id']][0][number - 1]
    return row['statement']


def unit_context(row, counts, facts):
    """The unit-level prose that assigns requirements to a composite row's entries.

    SCORING-FACTS.md binds attributes in sentences as well as in entries, so a disposition made
    against the entry alone can be made against a weaker obligation than the frozen one. An
    atomic row has no list and no unit prose.
    """
    if counts.get(row['id'], 1) > 1:
        return facts[row['id']][1]
    return ''


def load_packet(data, candidate):
    """A reviewer packet, checked to describe this candidate.

    The packet is what the readers were given. Binding it into the review is what lets a score
    say which propositions were judged; it does not establish that the readers saw nothing else.
    """
    packet = read_json(data)
    require(isinstance(packet, dict), 'packet: expected an object')
    keys(packet, ('schema', 'candidate_sha256', 'inventory_sha256', 'sources', 'exceptions',
                  'records'), 'packet')
    require(packet['schema'] == PACKET_SCHEMA, f'packet: schema must be {PACKET_SCHEMA}')
    require(packet['candidate_sha256'] == digest(candidate),
            'packet: built against a different candidate')
    require(isinstance(packet['records'], list) and packet['records'], 'packet: no records')
    return packet


def template(rows, counts, facts, inputs, packet, packet_bytes):
    return {
        'schema': SCHEMA, 'inputs': inputs,
        'run': {
            'id': 'replace-me', 'mode': 'practice', 'model': 'unknown',
            'ledger_author_model_relationship': 'unknown',
            'generation_prompt': 'unknown', 'skill_revision': 'unknown',
            'tools': 'unknown', 'budget': 'unknown', 'seed': 'unknown',
            'generated_at': 'unknown', 'author': 'author-1', 'access_profile': 'public-only',
        },
        'reviewers': [],
        'preparation': {'packet_sha256': digest(packet_bytes),
                        'inventory_sha256': packet['inventory_sha256'], 'responses': []},
        'audit': {'reviewer': '', 'complete': False, 'notes': ''},
        'cleanroom': {'reviewer': '', 'verdict': 'PENDING', 'notes': ''},
        'claims': [dict(record, verdict='PENDING', error='none', reviews=[])
                   for record in packet['records']],
        'coverage': [
            {'id': row['id'], 'context': unit_context(row, counts, facts), 'facts': [
                {'number': i, 'text': fact_text(row, counts, facts, i),
                 'state': 'pending', 'claims': [], 'notes': ''}
                for i in range(1, counts.get(row['id'], 1) + 1)]}
            for row in rows if roster(row)
        ],
    }


def evidence(value, lines, where):
    require(isinstance(value, list) and value, f'{where}: evidence is required')
    for item in value:
        keys(item, ('start', 'end', 'quote'), where)
        start, end = item['start'], item['end']
        require(type(start) is int and type(end) is int and 1 <= start <= end <= len(lines),
                f'{where}: invalid candidate line range')
        text(item['quote'], where)
        require(item['quote'] == '\n'.join(lines[start - 1:end]),
                f'{where}: quote differs from candidate lines')


def bucket(rows):
    counts = Counter(r['verdict'] for r in rows)
    partial = sum((Fraction(r['credit']) for r in rows if r['verdict'] == 'partial'), Fraction())
    numerator = counts['covered'] + partial
    return {
        'eligible_rows': len(rows), 'covered': counts['covered'],
        'partial_credit': str(partial), 'numerator': str(numerator),
        'recall': float(numerator / len(rows)) if rows else None,
        'verdicts': {v: counts[v] for v in ('covered', 'partial', 'missing', 'misstated', 'pending')},
        'atomic_verdicts': dict(Counter(r['verdict'] for r in rows if r['fact_count'] == 1)),
        'composite_verdicts': dict(Counter(r['verdict'] for r in rows if r['fact_count'] > 1)),
    }


def score(rows, counts, facts, sources, inputs, candidate, review, packet, packet_bytes):
    keys(review, ('schema', 'inputs', 'run', 'reviewers', 'preparation', 'audit', 'cleanroom',
                  'claims', 'coverage'), 'review')
    require(review['schema'] == SCHEMA, 'unsupported review schema')
    # A policy change is not a freshness warning: cross-policy scoring is forbidden.
    require(isinstance(review['inputs'], dict), 'inputs: expected mapping')
    for key in ('scoring_policy', 'acceptance_policy'):
        require(review['inputs'].get(key) == inputs[key], f'{key}: version mismatch')
    stale = []
    for key in sorted(set(inputs) | set(review['inputs'])):
        if review['inputs'].get(key) != inputs.get(key):
            if key == 'sha256' and isinstance(review['inputs'].get(key), dict):
                previous = review['inputs'][key]
                for name in sorted(set(previous) | set(inputs[key])):
                    if previous.get(name) != inputs[key].get(name):
                        stale.append(f'input digest changed: {name}')
            else:
                stale.append(f'input changed: {key}')
    run = review['run']
    keys(run, ('id', 'mode', 'model', 'ledger_author_model_relationship', 'generation_prompt',
               'skill_revision', 'tools', 'budget', 'seed', 'generated_at', 'author',
               'access_profile'), 'run')
    for key, value in run.items():
        text(value, f'run.{key}')
    require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', run['id']), 'invalid run id')
    require(run['mode'] in ('practice', 'blind'), 'run mode must be practice or blind')
    require(run['access_profile'] == 'public-only', 'pilot only accepts public-only inputs')
    prep = review['preparation']
    keys(prep, ('packet_sha256', 'inventory_sha256', 'responses'), 'preparation')
    require(prep['packet_sha256'] == digest(packet_bytes),
            'preparation: this review names a different packet')
    require(prep['inventory_sha256'] == packet['inventory_sha256'],
            'preparation: the packet was built from a different inventory')
    unique_list(review['reviewers'], 'reviewers')
    reviewers = set(review['reviewers'])
    # Each reader names the packet its instructions carried. A digest recorded once for the whole
    # review cannot tell an answer to this round from an answer imported out of the last one.
    require(isinstance(prep['responses'], list), 'preparation: responses must be a list')
    answered = set()
    for response in prep['responses']:
        keys(response, ('reviewer', 'packet_sha256'), 'preparation.responses')
        require(response['reviewer'] in reviewers, 'preparation: unknown reviewer in responses')
        require(response['reviewer'] not in answered, 'preparation: duplicate response')
        answered.add(response['reviewer'])
        require(response['packet_sha256'] == digest(packet_bytes),
                f'preparation: {response["reviewer"]} answered a different packet')
    require(run['author'] not in reviewers, 'candidate author cannot independently review itself')
    require(answered == reviewers, 'preparation: every reviewer names the packet it answered')
    audit, cleanroom = review['audit'], review['cleanroom']
    keys(audit, ('reviewer', 'complete', 'notes'), 'audit')
    keys(cleanroom, ('reviewer', 'verdict', 'notes'), 'cleanroom')
    require(type(audit['complete']) is bool, 'audit.complete must be boolean')
    require(cleanroom['verdict'] in ('PASS', 'FAIL', 'PENDING'), 'invalid cleanroom verdict')
    for name, gate, finished in (
        ('audit', audit, audit['complete']), ('cleanroom', cleanroom, cleanroom['verdict'] != 'PENDING')
    ):
        if finished:
            require(gate['reviewer'] in reviewers, f'{name}: unknown reviewer')
            text(gate['notes'], name)
    row_by_id = {row['id']: row for row in rows}
    # Judgments answer the propositions the readers were given. A proposition found during
    # review belongs to a new inventory, a new packet and a retained new attempt, never to a
    # quiet edit of the list one reader already answered.
    given = {record['id']: record for record in packet['records']}
    require({c['id'] for c in review['claims'] if isinstance(c, dict)} == set(given),
            'claims: do not match the packet the reviewers were given')
    claims = {}
    propositions = set()
    require(isinstance(review['claims'], list), 'claims must be a list')
    lines = candidate.decode('utf-8').replace('\r\n', '\n').split('\n')
    if lines[-1] == '':
        lines.pop()
    for claim in review['claims']:
        keys(claim, ('id', 'proposition', 'weight', 'verdict', 'error', 'requirements',
                     'evidence', 'reviews'), 'claim')
        cid = claim['id']
        text(cid, 'claim.id')
        require(cid not in claims, f'duplicate claim id: {cid}')
        text(claim['proposition'], cid)
        for field in PACKET_RECORD:
            require(claim[field] == given[cid][field],
                    f'{cid}: {field} differs from the packet the reviewers were given')
        normalized = ' '.join(claim['proposition'].split()).casefold()
        require(normalized not in propositions, f'{cid}: duplicate proposition; merge strongest statement')
        propositions.add(normalized)
        require(claim['weight'] in ledger_check.WEIGHTS, f'{cid}: invalid weight')
        require(claim['verdict'] in CLAIM_VERDICTS, f'{cid}: invalid verdict')
        require(claim['error'] in ('none', 'contradicted', 'attribution_error'), f'{cid}: invalid error')
        require((claim['verdict'] == 'FAIL') == (claim['error'] != 'none'), f'{cid}: inconsistent error')
        unique_list(claim['requirements'], cid)
        require(set(claim['requirements']) <= row_by_id.keys(), f'{cid}: unknown requirement')
        evidence(claim['evidence'], lines, cid)
        require(isinstance(claim['reviews'], list), f'{cid}: reviews must be a list')
        seen = set()
        for rev in claim['reviews']:
            keys(rev, ('reviewer', 'verdict', 'sources', 'rationale'), cid)
            who = rev['reviewer']
            require(who in reviewers and who not in seen, f'{cid}: unknown/duplicate reviewer')
            seen.add(who)
            require(rev['verdict'] in CLAIM_VERDICTS - {'PENDING'}, f'{cid}: invalid review verdict')
            text(rev['rationale'], cid)
            require(isinstance(rev['sources'], list) and rev['sources'], f'{cid}: source locators required')
            for source in rev['sources']:
                keys(source, ('source', 'locator'), cid)
                require(source['source'] in sources, f'{cid}: source outside frozen public corpus')
                text(source['locator'], cid)
        if claim['verdict'] not in ('PENDING', 'ADJUDICATE'):
            require(seen, f'{cid}: settled verdict needs a reviewer')
            require(all(r['verdict'] == claim['verdict'] for r in claim['reviews']),
                    f'{cid}: conflicting reviews must remain ADJUDICATE')
        weight = min([claim['weight']] + [row_by_id[r]['weight'] for r in claim['requirements']],
                     key=ledger_check.WEIGHTS.index)
        # A claim resting only on the pin manifest is a claim about this benchmark, not about the
        # device. It is judged for precision like any other claim, and it cannot evidence a fact:
        # the manifest transcribes documents, so crediting it would let a transcription stand in
        # for the reading the ledger was authored from.
        # Read per response, not pooled. Pooling lets one reader's pinned citation mask another
        # reader's manifest-only one, so a technical reading and a transcription would together
        # satisfy a critical claim's two independent reviews.
        technical = sorted(rev['reviewer'] for rev in claim['reviews']
                           if {src['source'] for src in rev['sources']} - {MANIFEST})
        claims[cid] = dict(claim, weight=weight, reviewers=sorted(seen),
                           technical_reviewers=technical,
                           manifest_only=bool(claim['reviews']) and not technical)
    require(isinstance(review['coverage'], list), 'coverage must be a list')
    coverage = {}
    for entry in review['coverage']:
        keys(entry, ('id', 'context', 'facts'), 'coverage')
        rid = entry['id']
        require(isinstance(rid, str) and rid in row_by_id and roster(row_by_id[rid]),
                'coverage: unknown or excluded row')
        require(rid not in coverage, f'{rid}: duplicate coverage')
        require(entry['context'] == unit_context(row_by_id[rid], counts, facts),
                f'{rid}: unit context differs from the frozen list')
        n = counts.get(rid, 1)
        require(isinstance(entry['facts'], list) and len(entry['facts']) == n,
                f'{rid}: must judge exactly {n} frozen facts')
        for i, fact in enumerate(entry['facts'], 1):
            keys(fact, ('number', 'text', 'state', 'claims', 'notes'), rid)
            require(type(fact['number']) is int and fact['number'] == i, f'{rid}: fact order changed')
            # A judgment carries the fact it was made against; edited text is a different fact.
            require(fact['text'] == fact_text(row_by_id[rid], counts, facts, i),
                    f'{rid}: fact {i} text differs from the frozen list')
            require(fact['state'] in FACT_STATES, f'{rid}: invalid fact state')
            unique_list(fact['claims'], rid)
            require(set(fact['claims']) <= claims.keys(), f'{rid}: dangling claim link')
            for cid in fact['claims']:
                require(rid in claims[cid]['requirements'], f'{rid}: claim lacks reverse requirement link')
                require(not claims[cid]['manifest_only'],
                        f'{rid}: {cid} cites only the manifest and cannot evidence a fact')
            if fact['state'] in ('absent', 'pending'):
                require(not fact['claims'], f'{rid}: absent/pending facts cannot cite claims')
            else:
                require(fact['claims'], f'{rid}: stated fact needs candidate evidence through claims')
                text(fact['notes'], rid)
            if fact['state'] != 'contradicted':
                require(not any(claims[c]['error'] == 'contradicted' for c in fact['claims']),
                        f'{rid}: contradicted claim cannot evidence a non-contradicted fact')
            if fact['state'] == 'correct':
                require(any(claims[c]['verdict'] == 'PASS' or
                            claims[c]['error'] == 'attribution_error' for c in fact['claims']),
                        f'{rid}: correct fact needs supported content, not only unresolved, '
                        'underspecified or unsupported claims')
            if fact['state'] == 'contradicted':
                require(any(claims[c]['error'] == 'contradicted' for c in fact['claims']),
                        f'{rid}: contradiction must also be a precision error')
        coverage[rid] = entry
    require(set(coverage) == {r['id'] for r in rows if roster(r)},
            'coverage must contain every recall row and active in-scope recoverable probe')
    results = []
    for row in rows:
        if not roster(row):
            continue
        rid = row['id']
        facts = coverage[rid]['facts']
        states = [f['state'] for f in facts]
        n, k = len(facts), states.count('correct')
        if 'contradicted' in states:
            verdict, credit = 'misstated', Fraction()
        elif 'pending' in states:
            verdict, credit = 'pending', Fraction()
        elif k == n:
            verdict, credit = 'covered', Fraction(1)
        elif all(s == 'absent' for s in states):
            verdict, credit = 'missing', Fraction()
        else:
            verdict, credit = 'partial', Fraction(k, n) if n > 1 else Fraction(1, 2)
        results.append({
            'id': rid, 'weight': row['weight'], 'class': row['class'],
            'eligible': eligible(row), 'verdict': verdict, 'credit': str(credit),
            'fact_count': n, 'correct_facts': k,
            'missed_critical_facts': [f['number'] for f in facts if f['state'] != 'correct']
            if row['weight'] == 'critical' and verdict != 'covered' else [],
            'applicability': row['applicability'],
        })
    scored = [r for r in results if r['eligible']]
    precision_counts = Counter(c['verdict'] for c in claims.values())
    denominator = len(claims)
    settled = denominator - precision_counts['ADJUDICATE'] - precision_counts['PENDING']
    precision = {
        'claims': len(claims), 'denominator': denominator,
        'errors': precision_counts['FAIL'], 'unsupported': precision_counts['UNVERIFIABLE'],
        'partial': precision_counts['GAP'], 'adjudicate': precision_counts['ADJUDICATE'],
        'pending': precision_counts['PENDING'],
        'precision': (denominator - precision_counts['FAIL']) / denominator if denominator else None,
        'settled_denominator': settled,
        'settled_precision': (settled - precision_counts['FAIL']) / settled if settled else None,
    }
    gates = {
        'semantic_claim_inventory_audit': audit['complete'],
        'cleanroom': cleanroom['verdict'] == 'PASS',
        'nonempty_claim_inventory': bool(claims),
        'coverage_review_complete': all(f['state'] != 'pending'
                                        for e in coverage.values() for f in e['facts']),
    }
    # Acceptance counts technical reviews only. The policy's rule is unchanged — a critical claim
    # needs two agreeing independent reviews — but a response citing only the pin manifest is not
    # one of them, for the same reason a manifest-only claim earns no coverage credit.
    judged = [dict(claim, reviewers=claim['technical_reviewers']) for claim in claims.values()]
    acceptance = strict_accept.decide(results, judged, gates, stale)
    return {
        'schema': 'enc28j60-score-1', 'inputs': inputs, 'run': run,
        'measurement_status': 'stale' if stale else 'provisional',
        'review_status': 'complete' if audit['complete'] and not precision_counts['PENDING']
        and not precision_counts['ADJUDICATE'] and gates['coverage_review_complete']
        else 'incomplete',
        'limitations': ['Documentary judgments against a frozen, unvalidated answer key; '
                        'not a hardware measurement.'],
        'recall_unit': 'frozen scoring rows, not individual facts',
        'recall': {'overall': bucket(scored), **{
            weight: bucket([r for r in scored if r['weight'] == weight])
            for weight in ledger_check.WEIGHTS}},
        'precision': precision, 'coverage': results,
        'excluded': [{'id': r['id'], 'status': r['status'], 'in_scope': r['in_scope'],
                      'recoverable': r['recoverable']} for r in rows if not roster(r)],
        'observed_software_behavior': dict(Counter(r['verdict'] for r in results
                                                  if r['class'] == 'observed-software-behavior')),
        'implementation_choice_probes': dict(Counter(r['verdict'] for r in results
                                                    if r['class'] == 'implementation-choice')),
        'acceptance': acceptance,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('command', choices=('template', 'score'))
    parser.add_argument('--candidate', required=True, type=Path)
    parser.add_argument('--review', type=Path)
    parser.add_argument('--packet', required=True, type=Path,
                        help='the reviewer packet from prepare.py; both commands name it')
    parser.add_argument('--inventory', type=Path,
                        help='score: the inventory the packet was built from, archived with '
                             'the attempt')
    parser.add_argument('--output', required=True, type=Path,
                        help='new review file for template; new attempt directory for score')
    args = parser.parse_args(argv)
    try:
        rows, counts, facts, sources, blobs = load_benchmark()
        candidate = args.candidate.read_bytes()
        candidate.decode('utf-8')
        packet_bytes = args.packet.read_bytes()
        packet = load_packet(packet_bytes, candidate)
        inputs = identity(blobs, candidate)
        if args.command == 'template':
            with args.output.open('xb') as f:
                f.write(canonical(template(rows, counts, facts, inputs, packet, packet_bytes)))
            return 0
        require(args.review is not None, '--review is required for scoring')
        require(args.inventory is not None, '--inventory is required for scoring')
        # The packet names an inventory by digest; without the bytes, that digest identifies
        # nothing anyone can read, and the segmentation dispositions behind the packet are lost.
        # prepare imports this module, so it is imported here rather than at module scope.
        import prepare
        inventory = prepare.load_inventory(args.inventory)
        inventory_bytes = canonical(inventory)
        require(digest(inventory_bytes) == packet['inventory_sha256'],
                'inventory: not the one this packet was built from')
        errors, warnings = prepare.audit(inventory, candidate, rows)
        require(not errors and not warnings,
                'inventory: not ready for review: ' + '; '.join(errors + warnings))
        # A digest over the inventory says nothing about the packet's contents. Rebuilding the
        # packet from the audited inventory is what makes the two agree: any producer may build
        # one, but it has to be the packet that inventory produces, lint and all.
        expected, lint = prepare.packet(inventory, candidate, sources)
        require(not lint, 'packet: leakage lint findings: ' + '; '.join(lint))
        require(packet == expected,
                'packet: not the packet this inventory produces; rebuild it with prepare.py')
        review_bytes = args.review.read_bytes()
        review = read_json(review_bytes)
        report = score(rows, counts, facts, sources, inputs, candidate, review, packet,
                       packet_bytes)
        # Reserve once; never replace any prior attempt, even a failed partial write.
        args.output.mkdir(parents=True, exist_ok=False)
        blobs = dict(blobs, **{'candidate.md': candidate, 'review.json': review_bytes,
                               'packet.json': packet_bytes, 'inventory.json': inventory_bytes})
        for name, data in blobs.items():
            (args.output / name).write_bytes(data)
        import yaml
        report['runtime'] = {'python': sys.version, 'pyyaml': yaml.__version__}
        report['created_at'] = datetime.now(timezone.utc).isoformat()
        report['artifacts'] = {name: digest(data) for name, data in blobs.items()}
        (args.output / 'result.json').write_bytes(canonical(report))
        print(json.dumps({'result': str(args.output / 'result.json'),
                          'spec_ready': report['acceptance']['spec_ready']}, indent=2))
        return 0 if report['acceptance']['spec_ready']['status'] == 'accepted' else 1
    except (OSError, ValueError, TypeError, KeyError, UnicodeError) as exc:
        print(f'score: {exc}', file=sys.stderr)
        return 3


if __name__ == '__main__':
    sys.exit(main())
