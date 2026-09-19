---
spec: vok
spec_file: vok.spec.md
spec_sha256: b5e45a0d50d471106253119dfd47a6235dba53d3425f6c77825773cbbe776258
verified: 2026-09-18
verifier: synthetic fixture (hash recomputed by test_record_hashes_match_the_fixture_specs)
sources:
  - name: linux
    commit: 0123456789abcdef0123456789abcdef01234567
    fetch: ok
  - name: platform page
    url: https://example.com/platform
    fetch: blocked
summary: {pass: 1, fail: 0, unverifiable: 1, gap: 1}
---

# Verification of `vok`

- Quick-facts/1 "Addressing": PASS — flat map matches vok.dtsi at the commit.
- Quick-facts/2 "Power": GAP — a TODO-only bullet; nothing to verify.
- Gotchas/1: UNVERIFIABLE — the platform page fetch was blocked this pass.
