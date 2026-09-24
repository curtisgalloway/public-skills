<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Tests for `scripts/spec_check.py`

```bash
python3 -m unittest discover -s plugins/driver-porting/skills/board-expert/tests -v
```

## Two parsers

Every case runs with `--no-pyyaml`, so CI exercises the stdlib subset parser, and runs again
with PyYAML when it is installed. One test asserts the two parsers agree on every shipped spec
and fixture.

Without PyYAML, both runs use the same parser (the checker's last line says `parser: subset`).
To exercise the real second path, run the suite once under a Python that has it:

```bash
uv run --with pyyaml python -m unittest discover -s plugins/driver-porting/skills/board-expert/tests -v
```

## Fixtures

All synthetic, under `fixtures/`:

- **`good_root/`**: all clean.
  - A board with `not_triggers`, two variants including a `source-observed`-grade one, a
    series, `fetch: partial` with `fetch_via`, a bullet whose prose names a tag, and angle
    brackets inside a code span.
  - An SoC with one structured instance.
  - An IP spec.
- **`bad_root/`**: one file per failure class the checker reports: references, shapes, tags,
  series, fetch and status values, a non-normalized id and alias, a bad variant `tag`, and an
  unsubstituted `<placeholder>`.
- **`vendor_root/`**: a `product` layer with an internal overlay, a duplicate overlay, and a
  dangling one.
- **`verify_root/`**: six SoC specs whose verification records under `resources/` cover every
  state: verified, stale, failing, stale and failing at once, missing, malformed.
- **Two stubs** (`stub_good.md`, `stub_bad.md`).
- **`stubs/`**: a skills directory for `--stubs-from`, with a real stub, a broken one, one with
  a leftover placeholder, and a non-stub that must be ignored.

The `vok` and `vfail` records carry the SHA-256 of their spec files as committed, and a test
recomputes it. If you edit either fixture spec, recompute its hash with `shasum -a 256` and
update the record.
