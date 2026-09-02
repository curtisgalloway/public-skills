# leak_scan tests

<!--
SPDX-FileCopyrightText: 2026 Curtis Galloway
SPDX-License-Identifier: Apache-2.0
-->

Python 3 stdlib only, no dependencies. From the repo root:

```bash
python3 -m unittest discover -s plugins/driver-porting/skills/os-investigator/tests -v
```

## Fixtures are synthetic, and must stay that way

`fixtures/fake_source/widgetron.c` is a wholly fictional peripheral written
from scratch as scanner bait. **Never replace it with real kernel, U-Boot,
TF-A, or vendor source** — a test suite carrying encumbered code is the leak
the scanner exists to detect, and it would ship in every clone of this repo.

The two candidate fixtures are the same hardware facts written both ways:
`leaky_spec.md` transcribes the source statement-by-statement and must be
flagged; `clean_spec.md` re-expresses those facts as databook-grouped tables
with provenance tags and must scan clean.

## The load-bearing test

`test_report_never_reproduces_source_text` guards the invariant that makes the
scanner's output filable as evidence: reports cite line ranges and digests,
never matched text. Bare identifier names are the one sanctioned exception —
you need the name to act on the finding — so that test asserts on multi-token
sequences and on an all-caps token the identifier lint does not print.

## Why fixtures carry no SPDX headers

Every other file in this repo carries one; the files under `fixtures/` do not,
deliberately. An identical SPDX header in both a source fixture and a
candidate fixture is an ~11-token shared run, which trips the scanner's own
`--min-run` threshold and would make `clean_spec.md` fail as a false positive.
The headers are omitted so the fixtures test the scanner rather than the
boilerplate. Fixture provenance is stated in-band instead.
