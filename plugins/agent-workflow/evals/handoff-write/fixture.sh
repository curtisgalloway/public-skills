#!/bin/bash
# SPDX-FileCopyrightText: 2026 Curtis Galloway
# SPDX-License-Identifier: Apache-2.0
set -e
git init -q -b main
git config user.email "eval@example.com"
git config user.name "Eval Fixture"
mkdir -p src
printf 'def parse(line):\n    return line.split(",")\n' > src/parser.py
printf '# widget\n' > README.md
git add -A
git commit -q -m "initial"
git checkout -q -b feature/csv-quoting
printf 'def parse(line):\n    # TODO handle quoted fields\n    return line.split(",")\n' > src/parser.py
mkdir -p tests
printf 'a,"b,c",d\n' > tests/fixture.csv
