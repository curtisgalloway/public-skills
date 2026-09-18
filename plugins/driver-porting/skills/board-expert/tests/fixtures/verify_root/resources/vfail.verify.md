---
spec: vfail
spec_file: vfail.spec.md
spec_sha256: a665a727448a96736a913daa5687e648ac0cef3ee3212f5d085df11d5c20550b
verified: 2026-09-18
verifier: synthetic fixture (hash recomputed by test_record_hashes_match_the_fixture_specs)
sources:
  - name: linux
    commit: 0123456789abcdef0123456789abcdef01234567
    fetch: ok
summary: {pass: 1, fail: 1, unverifiable: 0, gap: 0}
---

# Verification of `vfail`

- Quick-facts/1 "Addressing": PASS — flat map matches vfail.dtsi at the commit.
- Quick-facts/2 "Timer": FAIL — the spec says 24 MHz; the device tree's clock node at the commit
  says 19.2 MHz. Proposed correction: change the frequency and cite the clock node.
