---
spec: tensor-g5
spec_file: tensor-g5.spec.md
spec_sha256: 9fc40fa90db18fba35897fa82886225243e74b96fac6081aa0114443ebfd3d38
verified: 2026-09-20
verifier: >-
  Codex orchestrator reconciled 4 scoped claims: readers A and B, with fresh readers
  C and D rechecking the revised Tensor G5 boot bullet after human adjudication.
  Other results are explicitly retained historical findings, not a new full audit.
scope: scoped correction review with historical carry-forward
historical_commit: e6499c3dff8de50e94f7325f77b1c0299ce16a4f
historical_spec_sha256: e58871df4e9c4a127e9bec5eca4545dccd78f4bf02dc1487784691ed4a10819f
historical_record_sha256: 253dbc253d1d6bf11a22720ba94ebcbd5e0b658275c38b4f0d1d1166f35cee22
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
summary: {pass: 44, fail: 0, unverifiable: 3, gap: 0, adjudicate: 0}
---

<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Verification of `tensor-g5` — scoped correction review

**Terms:** A claim is one fact bullet or instance row. Carry-forward retains an earlier
finding for unchanged text; it does not repeat the source review. A hash identifies exact
bytes. See the [glossary](../../../../../../GLOSSARY.md).

## Scope and retained evidence

This record reconciles 4 scoped claims with the earlier record. Its summary mixes
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

- Quick-facts/1: PASS — Independent readers A and B reproduced the complete address classification and accepted the corrected decoding limits; 2,774 nodes and all ten counts totaling 645 register-bearing nodes agree.

- Quick-facts/2: PASS — After human adjudication narrowed the inference, fresh readers C and D independently checked the entire revised bullet. Intended hypervisor configuration establishes neither kernel build configuration nor actual firmware hand-off. The explicit hardware unknowns remain.

- Quick-facts/3: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- Quick-facts/4: UNVERIFIABLE — The retained report could not fetch the Arm architecture manual supporting the affinity interpretation. Retained device-tree observations do not verify the whole architectural claim. Scope qualification of the retained record, not a fresh source reading.

- Quick-facts/5: UNVERIFIABLE — The retained report could not fetch the Arm GIC architecture authority for the CPU-interface, redistributor and routing explanations. Its device-tree values and arithmetic remain historical observations. Scope qualification of the retained record, not a fresh source reading.

- Quick-facts/6: PASS — Readers A and B checked placement, register spacing, interrupt and clock data, personality layout, and the conditional baud request. Live baud remains unmeasured; the composed generic UART document is not certified.

- Quick-facts/7: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- Quick-facts/8: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- Quick-facts/9: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- Quick-facts/10: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- Quick-facts/11: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- Quick-facts/12: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- Quick-facts/13: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- Quick-facts/14: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- Quick-facts/15: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- Quick-facts/16: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- Gotchas/1: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- Gotchas/2: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- Gotchas/3: UNVERIFIABLE — The retained report could not fetch the Arm authority for the GICv2-versus-v3 architectural consequence. The device-tree observations alone do not establish it. Scope qualification of the retained record, not a fresh source reading.

- Gotchas/4: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- Gotchas/5: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- Gotchas/6: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- Gotchas/7: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- Gotchas/8: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- Gotchas/9: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- instances/lsion_cli16_uart: PASS — Readers A and B checked the complete row, including its series-versus-production clock distinction and conditional baud request; the numeric fields are unchanged.

- instances/lsios_cli0_uart: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- instances/lsios_cli1_uart: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- instances/lsios_cli2_uart: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- instances/lsios_cli3_uart: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- instances/lsios_cli4_uart: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- instances/lsios_cli5_uart: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- instances/lsios_cli6_uart: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- instances/lsioe_cli7_uart: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- instances/lsioe_cli8_uart: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- instances/lsioe_cli9_uart: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- instances/lsioe_cli10_uart: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- instances/lsioe_cli11_uart: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- instances/lsioe_cli12_uart: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- instances/lsioe_cli13_uart: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- instances/lsioe_cli14_uart: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- instances/lsion_cli15_uart: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- instances/lsion_cli_int0_uart: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- instances/lsion_cli_int1_uart: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- instances/lsion_cli_int2_uart: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- instances/lsion_cli_int3_uart: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.

- instances/lsion_cli_int4_uart: PASS — Historical verdict retained from the baseline record for unchanged text; its original scope and qualifications apply. Not re-read in this pass.
