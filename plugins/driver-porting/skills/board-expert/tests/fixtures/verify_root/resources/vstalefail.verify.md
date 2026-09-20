---
spec: vstalefail
spec_file: vstalefail.spec.md
spec_sha256: 0000000000000000000000000000000000000000000000000000000000000000
verified: 2026-09-18
verifier: synthetic fixture
sources:
  - name: linux
    commit: 0123456789abcdef0123456789abcdef01234567
    fetch: ok
summary: {pass: 0, fail: 1, unverifiable: 0, gap: 0}
---
<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Verification of `vstalefail`

- Quick-facts/1 "Timer": FAIL — the device tree says 19.2 MHz; the spec said
  24 MHz before it changed after this record was written.
