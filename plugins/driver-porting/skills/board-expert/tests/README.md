<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Tests for `scripts/spec_check.py`

```bash
python3 -m unittest discover -s plugins/driver-porting/skills/board-expert/tests -v
```

Fixtures are synthetic: `good_root/` (a board, an SoC with one instance, an IP spec, all clean),
`bad_root/` (one file per failure class the checker reports), `vendor_root/` (a `product` layer
with an internal overlay, a duplicate overlay, and a dangling one), and two stubs. Every case runs
with `--no-pyyaml` so the stdlib subset parser is what CI exercises, and again with PyYAML when it
is installed; one test asserts the two parsers agree on every shipped spec.
