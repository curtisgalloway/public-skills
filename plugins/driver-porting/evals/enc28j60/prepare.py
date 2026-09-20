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
SCHEMA = 'enc28j60-inventory-1'
PACKET_SCHEMA = 'enc28j60-packet-1'

# The only fields a reviewer packet may carry. A packet is built by copying these out of the
# inventory, never by deleting fields from it: a field added to the inventory later is absent
# from the packet until someone adds it here on purpose.
PACKET_FIELDS = ('id', 'proposition', 'weight', 'requirements', 'evidence')
RECORD_FIELDS = PACKET_FIELDS + ('status', 'supersedes', 'notes')
STATUSES = ('active', 'retired')

# Judgment vocabulary. A packet carrying any of it is refused: these are the words a leaked
# verdict summary is written in, and no ENC28J60 proposition needs them.
VERDICT_TOKENS = ('PASS', 'FAIL', 'GAP', 'UNVERIFIABLE', 'ADJUDICATE', 'PENDING')
LEAK_PHRASES = ('verdict', 'reviewer', 'first reader', 'second reader', 'first-pass',
                'confirms', 'concurs', 'agreed with', 'disagreed with')

# What a citation the scorer cannot represent should have cited instead. The manifest is a list
# of pins, not an authority: every fact it indexes was read somewhere, and that is the pin name
# a review cites. Keys are matched case-insensitively against the whole string.
SOURCE_HINTS = {
    'corpus.yaml': 'the pinned edition or file the manifest entry indexes, e.g. DS80349C',
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
    data = score.read_json(path.read_bytes())
    score.require(isinstance(data, dict), 'inventory: expected an object')
    score.keys(data, ('schema', 'candidate_sha256', 'records'), 'inventory')
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
        if COMPOUND_RE.search(record['proposition']):
            warnings.append(f'{record["id"]}: reads as more than one assertion; segment it or '
                            'record why it is one proposition')
    for parent, children in superseded.items():
        if parent not in ids:
            errors.append(f'unknown superseded record: {parent} (claimed by {", ".join(children)})')
        elif ids[parent]['status'] != 'retired':
            errors.append(f'{parent}: superseded by {", ".join(children)} but still active')
    for record in ids.values():
        if record['status'] == 'retired' and record['id'] not in superseded:
            warnings.append(f'{record["id"]}: retired without a replacement; its assertions leave '
                            'the inventory')
    active = [r for r in ids.values() if r['status'] == 'active']
    if not active:
        errors.append('inventory: no active records to review')
    return errors, warnings


def leaks(value, where, allowed):
    """Judgment vocabulary found in text a reviewer would read."""
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


def packet(inventory, candidate, sources, allowed):
    """The neutral reviewer packet, and whatever leaked into it."""
    records, found = [], []
    for record in sorted((r for r in inventory['records'] if r['status'] == 'active'),
                         key=lambda r: r['id']):
        copied = {field: record[field] for field in PACKET_FIELDS}
        records.append(copied)
        for field, value in copied.items():
            if isinstance(value, str):
                found += leaks(value, f'{record["id"]}.{field}', allowed)
            elif field == 'evidence':
                for i, item in enumerate(value, 1):
                    found += leaks(item['quote'], f'{record["id"]}.evidence[{i}]', allowed)
    return {
        'schema': PACKET_SCHEMA,
        'candidate_sha256': score.digest(candidate),
        'inventory_sha256': score.digest(score.canonical(inventory)),
        'sources': sorted(sources),
        'records': records,
    }, found


def resolve(name, sources):
    """Whether a proposed source name is citable, and what to cite instead when it is not."""
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
    parser.add_argument('--allow', action='append', default=[], metavar='TOKEN',
                        help='packet: a judgment word this candidate genuinely uses, after review')
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
        built, found = packet(inventory, candidate, sources, set(args.allow))
        if found:
            for line in found:
                print(f'prepare: {line}', file=sys.stderr)
            print('prepare: packet refused; a reviewer must not read another reader\'s judgment. '
                  'If the candidate itself uses the word, pass --allow after checking it.',
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
