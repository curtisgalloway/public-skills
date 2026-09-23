---
spec: pixel10
spec_file: pixel10.spec.md
spec_sha256: de7d9bb2d518c12833345c56c0ee34a7d9715f83e6be96f0fa4a6fd242375c1e
verified: 2026-09-20
verifier: >-
  Codex orchestrator reconciled 1 scoped claims: readers A and B, with fresh readers
  C and D rechecking the revised Tensor G5 boot bullet after human adjudication.
  Other results are explicitly retained historical findings, not a new full audit.
scope: scoped correction review with historical carry-forward
historical_commit: e6499c3dff8de50e94f7325f77b1c0299ce16a4f
historical_spec_sha256: 5629084803e098f572ff262d67e40874a9a6557741d1d2dfbac9d53d90ed1e87
historical_record_sha256: b6e626685e74d7901f9050d27d92707b8811cccb7bb49af5ca9f2e0a35146130
sources:
  - name: linux-mainline
    commit: 17e7b8eacf4cac800a4fc89a28729df72a2dabda
    fetch: ok
  - name: laguna-kernel-prebuilts
    commit: 80c104d7e5591ebc3cd413f54b076d972484ff0b
    fetch: ok
  - name: pixelscripts
    commit: 156bd361b39c55303cb4de33cd66ace9b1f610f2
    fetch: ok
  - name: Devicetree Specification v0.4
    url: https://raw.githubusercontent.com/devicetree-org/devicetree-specification/v0.4/source/chapter2-devicetree-basics.rst
    fetch: ok
  - name: Laguna board series v4
    url: https://lore.kernel.org/all/20260918-contrib-pg-pixel10-initial-dts-v4-0-745eaca28b1a@linaro.org/
    fetch: ok
  - name: Laguna board series v1
    url: https://lore.kernel.org/linux-arm-kernel/20251111192422.4180216-1-dianders@chromium.org/
    fetch: ok
  - name: Android boot image header
    url: https://source.android.com/docs/core/architecture/bootloader/boot-image-header
    fetch: ok
  - name: Android DTB and DTBO partitions
    url: https://source.android.com/docs/core/architecture/dto/partitions
    fetch: ok
  - name: Android vendor boot partitions
    url: https://source.android.com/docs/core/architecture/partitions/vendor-boot-partitions
    fetch: ok
summary: {pass: 21, fail: 0, unverifiable: 0, gap: 0, adjudicate: 0}
---

<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Verification of `pixel10` — scoped correction review

**Terms:** A claim is one fact bullet or instance row. Carry-forward retains an earlier
finding for unchanged text; it does not repeat the source review. A hash identifies exact
bytes. See the [glossary](../../../../../../GLOSSARY.md).

## Scope and retained evidence

This record reconciles 1 scoped claims with the earlier record. Its summary mixes
fresh results and historical carry-forward; it must not be presented as a fresh full audit.
The baseline record and specification are preserved in Git at `e6499c3dff8de50e94f7325f77b1c0299ce16a4f` under the same
paths, with their hashes above. Their detailed rationales and source-access results remain
historical evidence. The new source list describes the scoped readings only.

The accompanying `pixel10-critical-20260920-identities.json` records exact old/new claim
identities. Four fact bullets and one matching UART instance note changed across the two
specifications; other fact bullets, variant rows, numerical table rows, and instance numeric
fields were compared mechanically. Equality permits attribution of a retained result;
it does not prove that result correct.

Independent reports are retained individually with the correction evidence. Reader A
accepted all five reviewed claims. Reader B accepted four and rejected the boot inference
about the kernel build. Their disagreement was recorded as ADJUDICATE, excluded from
pass/fail totals. The user chose narrower wording: boot options indicate intended
configuration but establish neither the build configuration nor actual firmware hand-off.
That resolves a defect in the assertion's definiteness, not a failure caused by disagreement.
Both original readings remain unchanged. Fresh readers C and D then passed the entire revised
boot bullet; no adjudication remains open. Report identities:

- Reader A (Codex task `verify_a`): `93c17b1cc393e6abe1d47dbbb39da3a0ec99db511cad415844a49af701ddfb6d`.
- Reader B (Codex task `verify_b`): `96a557db4de5e3ecac6c66f8cab9ed979f61788b7e3c63815f4c748dbb502409`.
- Reader C (Codex task `verify_boot_c`, revised boot bullet only): `0fe08e47bed410aa91b33cbe59f4b7ac1a5ec5885a27dabf0a38c8f133b678c6`.
- Reader D (Codex task `verify_boot_d`, revised boot bullet only): `f351f9bd985dc289bdba1491f6d75fb6e4988a231739e5c02d4fcdf97e214b7e`.

Both readers checked the same initial corrected specification hashes: Tensor G5
`f1626c586ddfcdfe279fd33405fb747f3c5810e3b39d6600ec48c594151bed9b` and Pixel 10
`de7d9bb2d518c12833345c56c0ee34a7d9715f83e6be96f0fa4a6fd242375c1e`.
The other four scoped claims are unchanged after that pair's review. Readers C and D
checked the final Tensor G5 hash in this record; the identity comparison records the single
changed bullet between those rounds. Fresh pinned publisher responses matched cached artifacts
during A/B's readings. C/D reused identified cached source bytes when pinned refreshes failed;
their reports retain that limit. Reader C also fetched reachable official Android documentation;
reader D used cached Android HTML.
Live Android documentation is identified by each reader's response digest and access date;
it is not an immutable historical edition. Neither source matching nor agreement proves
hardware behavior or identity with a stock factory image. Source and scanner maps, raw outcomes,
and reproduction scripts are retained with the individually fingerprinted reports.

Three retained Tensor G5 whole-claim grades are qualified as UNVERIFIABLE because their
earlier rationales explicitly lacked the architectural authority: Quick-facts/4,
Quick-facts/5, and Gotchas/3. This pass did not reopen those authorities. The older vendor
kernel-source reference uses branch `17` without an exact commit; its retained findings
remain historical and are not freshly authenticated here. The generic UART specification
remains unverified. No implementation or hardware test was performed.

## Verdicts

- Quick-facts/1: PASS — Historical PASS for the modem provenance tag clause only, retained for unchanged text. This is not a fresh whole-claim review; the baseline record supplies its scope and rationale.

- Quick-facts/2: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- Quick-facts/3: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- Quick-facts/4: PASS — Readers A and B checked the whole console bullet. The rate request is conditional on virtual-mux selection; persistence remains unestablished, and cable/recovery directions remain documentation rather than Pixel 10 measurements.

- Quick-facts/5: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- Quick-facts/6: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- Quick-facts/7: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- Quick-facts/8: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- Quick-facts/9: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- Gotchas/1: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- Gotchas/2: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- Gotchas/3: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- Gotchas/4: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- Gotchas/5: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- Gotchas/6: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- variants/Google Pixel 10 Pro: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- variants/Google Pixel 10 Pro XL: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- variants/Google Pixel 10 Pro Fold: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- `resources/laguna-kernel-prebuilts` note: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- resources/laguna-kernel-source `fetch_via`: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- `resources` factory-images `docs` note: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.
