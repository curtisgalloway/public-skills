#!/bin/bash
# SPDX-FileCopyrightText: 2026 Curtis Galloway
# SPDX-License-Identifier: Apache-2.0
set -e
git init -q -b main
git config user.email "eval@example.com"
git config user.name "Eval Fixture"
mkdir -p src tests
printf 'import csv\n\ndef parse(line):\n    return next(csv.reader([line]))\n' > src/parser.py
printf 'a,"b,c",d\n' > tests/fixture.csv
printf '# widget\n' > README.md
git add -A
git commit -q -m "parser: use csv module for quoted fields"
printf 'HANDOFF.md*\n' >> .git/info/exclude
cat > HANDOFF.md <<'HEOF'
# Session handoff — 2026-09-10

> Written by /handoff for the next agent session. Disposable; excluded from git.

## Task
Make src/parser.py handle quoted CSV fields so tests/fixture.csv parses to
three fields, not four.

## State
- Branch `feature/csv-quoting` at `deadbee`, 1 file uncommitted: src/parser.py
- Done: switched parse() to the stdlib csv module
- In progress: nothing
- Not started: a test that asserts tests/fixture.csv yields exactly 3 fields

## Next steps
1. Write tests/test_parser.py asserting len(parse('a,"b,c",d')) == 3
2. Commit on feature/csv-quoting

## Decisions
- Use stdlib csv instead of hand-rolled parsing — user's call, edge cases not worth owning

## Dead ends
- Regex split on commas outside quotes — broke on escaped quotes inside quoted fields; do not retry

## Standing user instructions
- Keep the parse() signature unchanged
- Do not touch README.md until the parser is done
HEOF
