<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Tests for `scripts/spec_check.py`

```bash
python3 -m unittest discover -s plugins/driver-porting/skills/board-expert/tests -v
```

Fixtures are synthetic: `good_root/` (a board with a variant and a series, an SoC with one
structured instance, an IP spec, all clean), `bad_root/` (one file per failure class the checker
reports: references, shapes, tags, series, fetch and status values), `vendor_root/` (a `product`
layer with an internal overlay, a duplicate overlay, and a dangling one), `verify_root/` (five
SoC specs whose verification records under `resources/` are in every state: verified, stale,
failing, missing, malformed), two stubs, and a `stubs/` skills directory for `--stubs-from` with a
real stub, a broken one, and a non-stub that must be ignored. The `vok` and `vfail` records carry
the SHA-256 of their spec files as committed; a test recomputes it, so editing either fixture spec
means recomputing its hash with `shasum -a 256` and updating the record. Every case runs with `--no-pyyaml` so the stdlib subset parser is what CI exercises, and
again with PyYAML when it is installed; one test asserts the two parsers agree on every shipped
spec and fixture. On a machine without PyYAML the two runs are the same parser (the checker's last
line says `parser: subset`), so run the suite once under a Python that has it for the real second
path: `uv run --with pyyaml python -m unittest discover -s plugins/driver-porting/skills/board-expert/tests -v`.
