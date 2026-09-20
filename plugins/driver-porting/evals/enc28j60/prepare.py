#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Prepare an ENC28J60 accuracy review: audit the claim inventory, then emit neutral packets.

The first practice run failed its independence check in preparation, not in scoring: a revision
file assembled by hand carried one reader's verdict summaries into a second reader's packet, and
the inventory was still being segmented while review was running. This tool exists so neither is
a matter of care. See SCORING-RUN.md for the review contract it feeds.

Requires PyYAML (it reads the frozen ledger and corpus). From this directory:

    uv run --with pyyaml python3 prepare.py sources
    uv run --with pyyaml python3 prepare.py inventory --candidate c.md --inventory inv.json
    uv run --with pyyaml python3 prepare.py packet --candidate c.md --inventory inv.json \
        --output packet.json

Exit codes: 0 clean, 1 findings (an inventory not ready, or a packet refused), 3 unreadable or
invalid inputs and output collisions; argparse usage errors use 2.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

import ledger_check
import score

HERE = Path(__file__).resolve().parent
SCHEMA = 'enc28j60-inventory-2'
PACKET_SCHEMA = score.PACKET_SCHEMA

# The only fields a reviewer packet may carry. A packet is built by copying these out of the
# inventory, never by deleting fields from it: a field added to the inventory later is absent
# from the packet until someone adds it here on purpose.
PACKET_FIELDS = ('id', 'proposition', 'weight', 'requirements', 'evidence')
RECORD_FIELDS = PACKET_FIELDS + ('status', 'supersedes', 'segmentation', 'notes')
STATUSES = ('active', 'retired')
ALLOWANCE_FIELDS = ('record', 'field', 'token', 'reason', 'content_sha256')

# Judgment vocabulary. This is a lint, not a proof of neutrality: it catches the shape the
# practice run's leak actually had, and an operator who paraphrases defeats it. A packet
# carrying any of it is refused.
VERDICT_TOKENS = ('PASS', 'FAIL', 'GAP', 'UNVERIFIABLE', 'ADJUDICATE', 'PENDING')
LEAK_PHRASES = ('verdict', 'reviewer', 'first reader', 'second reader', 'first-pass',
                'confirms', 'concurs', 'agreed with', 'disagreed with')

# What a citation the scorer cannot represent should have cited instead. The manifest indexes
# pins; a fact it indexes was read in a document, and that document is what a hardware claim
# cites. Keys are matched case-insensitively against the whole string.
SOURCE_HINTS = {
    'corpus': 'the pinned edition or file the manifest entry indexes, e.g. DS80349C',
    'manifest': 'the pinned edition or file the manifest entry indexes, e.g. DS80349C',
    'errata_map': 'the errata edition whose table the map transcribes, DS80349B or DS80349C',
    'errata': 'the errata edition read, DS80349B or DS80349C',
    'datasheet': 'the data sheet edition read, e.g. DS39662E',
    'data sheet': 'the data sheet edition read, e.g. DS39662E',
    'linux': "the pinned driver path, e.g. drivers/net/ethernet/microchip/enc28j60.c",
    'driver': 'the pinned driver path or the driver commit the manifest names',
}

COMPOUND_RE = re.compile(r';|\band\b(?=.*\b(?:at|is|are|to|of)\b)|(?<=[a-z0-9])\.\s+[A-Z]')


def fail(message):
    print(f'prepare: {message}', file=sys.stderr)
    return 3


def load_inventory(path):
    data = score.read_json(Path(path).read_bytes())
    score.require(isinstance(data, dict), 'inventory: expected an object')
    score.keys(data, ('schema', 'candidate_sha256', 'allowances', 'records'), 'inventory')
    score.require(data['schema'] == SCHEMA, f'inventory: schema must be {SCHEMA}')
    score.require(isinstance(data['records'], list) and data['records'],
                  'inventory: records must be a nonempty list')
    return data


def audit(inventory, candidate, rows):
    """Everything that must be settled before a reviewer sees the inventory.

    Returns (errors, warnings). Errors are structural: the inventory does not describe this
    candidate, or its records cannot be reviewed as written. Warnings are the segmentation
    questions a human answers before the freeze; they are reported, never silently resolved.
    """
    errors, warnings = [], []
    if inventory['candidate_sha256'] != score.digest(candidate):
        errors.append('inventory: candidate_sha256 does not match the candidate')
    lines = candidate.decode('utf-8').replace('\r\n', '\n').split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    row_ids = {row['id'] for row in rows}
    ids, propositions, superseded = {}, {}, {}
    for record in inventory['records']:
        where = record.get('id') if isinstance(record, dict) else '?'
        try:
            score.keys(record, RECORD_FIELDS, f'record {where}')
            score.text(record['id'], 'record.id')
            score.require(record['id'] not in ids, f'duplicate record id: {record["id"]}')
            ids[record['id']] = record
            score.text(record['proposition'], record['id'])
            score.require(record['weight'] in ledger_check.WEIGHTS, f'{record["id"]}: invalid weight')
            score.require(record['status'] in STATUSES, f'{record["id"]}: invalid status')
            score.unique_list(record['requirements'], record['id'])
            score.require(set(record['requirements']) <= row_ids, f'{record["id"]}: unknown requirement')
            score.unique_list(record['supersedes'], f'{record["id"]}.supersedes')
            score.require(isinstance(record['notes'], str), f'{record["id"]}: notes must be text')
            if record['segmentation'] != '':
                score.keys(record['segmentation'], ('reason', 'proposition_sha256'),
                           f'{record["id"]}.segmentation')
                score.text(record['segmentation']['reason'], f'{record["id"]}.segmentation')
                # A reason written against one wording does not attest to another. Rewording the
                # proposition retires its disposition instead of carrying it forward silently.
                score.require(
                    record['segmentation']['proposition_sha256']
                    == score.digest(record['proposition'].encode()),
                    f'{record["id"]}: segmentation attests to a different proposition; '
                    'write the disposition against the current wording')
            score.evidence(record['evidence'], lines, record['id'])
        except ValueError as exc:
            errors.append(str(exc))
            continue
        for parent in record['supersedes']:
            superseded.setdefault(parent, []).append(record['id'])
        if record['status'] != 'active':
            continue
        normalized = ' '.join(record['proposition'].split()).casefold()
        if normalized in propositions:
            errors.append(f'{record["id"]}: duplicate proposition of {propositions[normalized]}; '
                          'merge them at their strongest statement before review')
        else:
            propositions[normalized] = record['id']
        # A heuristic cannot decide this, so it asks. The disposition is a written reason that
        # stays in the inventory: it is not an allowlisted packet field and never reaches a
        # reviewer. Tightening the pattern would buy cosmetic rewording, not segmentation.
        if COMPOUND_RE.search(record['proposition']) and not record['segmentation']:
            warnings.append(f'{record["id"]}: reads as more than one assertion; segment it, or '
                            'record in `segmentation` why it is one proposition')
    for parent, children in superseded.items():
        if parent not in ids:
            errors.append(f'unknown superseded record: {parent} (claimed by {", ".join(children)})')
            continue
        if ids[parent]['status'] != 'retired':
            errors.append(f'{parent}: superseded by {", ".join(children)} but still active')
        # Only a live record can carry a retired one's assertions forward. Requiring the
        # replacement to be active rejects a self-link and every cycle with it, since a cycle
        # needs a retired record to do the superseding.
        for child in children:
            if child == parent:
                errors.append(f'{parent}: supersedes itself')
            elif ids[child]['status'] != 'active':
                errors.append(f'{parent}: superseded by {child}, which is itself retired; '
                              'name the active record that carries its assertions')
    for record in ids.values():
        if record['status'] != 'retired':
            continue
        live = [c for c in superseded.get(record['id'], []) if c != record['id']
                and ids.get(c, {}).get('status') == 'active']
        if not live:
            warnings.append(f'{record["id"]}: retired with no active replacement; its assertions '
                            'leave the inventory')
    errors += allowance_errors(inventory['allowances'], ids)
    active = [r for r in ids.values() if r['status'] == 'active']
    if not active:
        errors.append('inventory: no active records to review')
    return errors, warnings


def allowance_errors(allowances, ids):
    """Each exception to the leakage lint, scoped to one record, field and word.

    An allowance lives in the inventory rather than on the command line so that its reason is
    retained and bound with the attempt, and so that no justification text reaches a reviewer: a
    reason reading "allowed because the first reader marked this correct" would recreate the
    leak the lint exists to catch.
    """
    errors, seen = [], set()
    if not isinstance(allowances, list):
        return ['inventory: allowances must be a list']
    for item in allowances:
        try:
            score.keys(item, ALLOWANCE_FIELDS, 'allowance')
            for key in ALLOWANCE_FIELDS:
                score.text(item[key], f'allowance.{key}')
            key = (item['record'], item['field'], item['token'])
            score.require(key not in seen, f'duplicate allowance: {key}')
            seen.add(key)
            record = ids.get(item['record'])
            score.require(record is not None, f'allowance: unknown record {item["record"]}')
            score.require(item['field'] in PACKET_FIELDS or item['field'].startswith('evidence'),
                          f'allowance: {item["field"]} is not a packet field')
            content = allowance_text(record, item['field'])
            score.require(item['token'] in content,
                          f'allowance {item["record"]}.{item["field"]}: the record does not '
                          f'contain {item["token"]}')
            # An allowance releases a word across the whole field, and `evidence` can hold
            # several multiline quotes. Binding the field's content stops an old justification
            # from silently covering text added to it afterwards.
            score.require(item['content_sha256'] == score.digest(content.encode()),
                          f'allowance {item["record"]}.{item["field"]}: written against '
                          'different content; re-check it against the field as it now reads')
        except ValueError as exc:
            errors.append(str(exc))
    return errors


def allowance_text(record, field):
    """The text an allowance is scoped to: one packet field of one record."""
    if field == 'evidence':
        return '\n'.join(item['quote'] for item in record['evidence'])
    value = record.get(field)
    return value if isinstance(value, str) else '\n'.join(map(str, value or ()))


def leaks(value, where, allowed):
    """Judgment vocabulary found in text a reviewer would read.

    `allowed` holds the words released for this one record and field. An exception is never
    global: a candidate that legitimately says PASS somewhere does not license the word on an
    unrelated proposition, which is where a leaked outcome would actually sit.
    """
    found = []
    for token in VERDICT_TOKENS:
        if token in allowed:
            continue
        if re.search(r'\b' + token + r'\b', value):
            found.append(f'{where}: carries the verdict token {token}')
    lowered = value.casefold()
    for phrase in LEAK_PHRASES:
        if phrase in allowed:
            continue
        if phrase in lowered:
            found.append(f'{where}: carries the review phrase {phrase!r}')
    return found


def packet(inventory, candidate, sources):
    """The reviewer packet, and whatever the leakage lint found in it.

    The lint is a lint: it catches the shape the practice run's leak had, and an operator who
    paraphrases a verdict defeats it. Exceptions come from the inventory, scoped to one record
    and field; their reasons stay there, so no justification prose reaches a reviewer.
    """
    allowed = {}
    for item in inventory['allowances']:
        if isinstance(item, dict) and all(k in item for k in ALLOWANCE_FIELDS):
            allowed.setdefault((item['record'], item['field']), set()).add(item['token'])
    records, found = [], []
    for record in sorted((r for r in inventory['records'] if r['status'] == 'active'),
                         key=lambda r: r['id']):
        copied = {field: record[field] for field in PACKET_FIELDS}
        records.append(copied)
        for field, value in copied.items():
            here = allowed.get((record['id'], field), set())
            if isinstance(value, str):
                found += leaks(value, f'{record["id"]}.{field}', here)
            elif field == 'evidence':
                for i, item in enumerate(value, 1):
                    found += leaks(item['quote'], f'{record["id"]}.evidence[{i}]',
                                   here | allowed.get((record['id'], f'evidence[{i}]'), set()))
            else:
                for item in value:
                    found += leaks(str(item), f'{record["id"]}.{field}', here)
    return {
        'schema': PACKET_SCHEMA,
        'candidate_sha256': score.digest(candidate),
        'inventory_sha256': score.digest(score.canonical(inventory)),
        'sources': sorted(sources),
        'exceptions': sorted({f'{r}.{f}:{t}' for (r, f), ts in allowed.items() for t in ts}),
        'records': records,
    }, found


def resolve(name, sources):
    """Whether a proposed source name is citable, and what to cite instead when it is not."""
    if name == score.MANIFEST:
        return True, ('only for a proposition about the manifest itself; a claim about the '
                      'device cites the pinned document, and a manifest-only claim earns no '
                      'coverage credit')
    if name in sources:
        return True, ''
    lowered = name.casefold()
    for key, hint in SOURCE_HINTS.items():
        if key in lowered:
            return False, hint
    return False, 'no pin in corpus.yaml carries this name; cite the edition, path or commit read'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('command', choices=('sources', 'inventory', 'packet'))
    parser.add_argument('--candidate', type=Path)
    parser.add_argument('--inventory', type=Path)
    parser.add_argument('--output', type=Path, help='new packet file; never overwritten')
    parser.add_argument('--check', type=Path, help='sources: a JSON list of proposed source names')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    try:
        rows, _, _, sources, _ = score.load_benchmark(HERE)
        if args.command == 'sources':
            proposed = score.read_json(args.check.read_bytes()) if args.check else []
            score.require(isinstance(proposed, list), '--check: expected a JSON list of names')
            checked = [dict(zip(('source', 'citable', 'instead'), (n,) + resolve(n, sources)))
                       for n in proposed]
            report = {'sources': sorted(sources), 'checked': checked}
            bad = [c for c in checked if not c['citable']]
            if args.json:
                print(json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False))
            else:
                print('Citable source names (exactly these strings):')
                for name in report['sources']:
                    print(f'  {name}')
                for entry in checked:
                    mark = 'ok  ' if entry['citable'] else 'NO  '
                    print(f'{mark}{entry["source"]}'
                          + (f' -> {entry["instead"]}' if entry['instead'] else ''))
            return 1 if bad else 0

        score.require(args.candidate is not None and args.inventory is not None,
                      'inventory and packet need --candidate and --inventory')
        candidate = args.candidate.read_bytes()
        candidate.decode('utf-8')
        inventory = load_inventory(args.inventory)
        errors, warnings = audit(inventory, candidate, rows)
        if args.command == 'inventory':
            report = {'errors': errors, 'warnings': warnings,
                      'active': sum(1 for r in inventory['records']
                                    if isinstance(r, dict) and r.get('status') == 'active'),
                      'ready': not errors and not warnings}
            if args.json:
                print(json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False))
            else:
                for line in errors:
                    print(f'error: {line}')
                for line in warnings:
                    print(f'warning: {line}')
                print(f'{report["active"]} active records; '
                      + ('ready for review' if report['ready'] else 'not ready for review'))
            return 0 if report['ready'] else 1

        score.require(args.output is not None, 'packet needs --output')
        # An inventory still under audit is not a reviewable inventory, and a warning is a
        # segmentation question nobody has answered yet. Neither becomes a packet.
        if errors or warnings:
            for line in errors + warnings:
                print(f'prepare: {line}', file=sys.stderr)
            print('prepare: run `inventory` and settle these before building a packet',
                  file=sys.stderr)
            return 1
        built, found = packet(inventory, candidate, sources)
        if found:
            for line in found:
                print(f'prepare: {line}', file=sys.stderr)
            print('prepare: packet refused; a reviewer must not read another reader\'s judgment. '
                  'If a record genuinely uses the word, add a scoped allowance to the inventory.',
                  file=sys.stderr)
            return 1
        with args.output.open('xb') as f:
            f.write(score.canonical(built))
        print(f'{len(built["records"])} records written to {args.output}')
        return 0
    except FileExistsError:
        return fail(f'{args.output}: exists; write each packet to a new path')
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return fail(str(exc))
    except ValueError as exc:
        return fail(str(exc))


if __name__ == '__main__':
    sys.exit(main())
