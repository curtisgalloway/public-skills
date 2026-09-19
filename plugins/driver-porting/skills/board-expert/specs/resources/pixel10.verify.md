---
spec: pixel10
spec_file: pixel10.spec.md
spec_sha256: f6c36414b2206936e82fe4446b015a4e57ecc12d4b777e3054d58437bf934c3f
verified: 2026-09-18
verifier: >-
  Claude Opus 5 (1M context) under Claude Code, orchestrating spec-verifier. Third and final pass,
  frozen: verdicts here are recorded as returned, and the corrections they propose were deliberately
  NOT applied, to end a correct-then-reverify cycle in which three successive corrections each
  introduced a new phrasing defect. Verdict lines say which pass and which spec hash established
  them; a line marked "carried forward" was established against an earlier hash on bullet text that
  has not changed since. Verifiers were fresh contexts, told that a correction which overshot is as
  much a FAIL as the original defect, and that nothing they found would be fixed before the record
  was written.
sources:
  - name: laguna-kernel-prebuilts
    url: https://github.com/GrapheneOS/device_google_laguna-kernels_6.6
    commit: 80c104d7e5591ebc3cd413f54b076d972484ff0b
    fetch: ok
  - name: laguna-kernel-source
    url: https://gitlab.com/grapheneos/kernel_pixel_6.6
    fetch: ok
    fetch_via: "ref 17: root tree, muzel and rango device definitions and constants, device-tree directory history"
  - name: GrapheneOS source page
    url: https://grapheneos.org/source
    fetch: ok
  - name: pixelscripts
    url: https://gitlab.com/LinaroLtd/googlelt/pixelscripts
    commit: 156bd361b39c55303cb4de33cd66ace9b1f610f2
    fetch: ok
  - name: "Add Laguna/Tensor G5 SoC and Frankel, Blazer & Mustang boards (v4)"
    url: https://lore.kernel.org/all/20260918-contrib-pg-pixel10-initial-dts-v4-0-745eaca28b1a@linaro.org/
    fetch: ok
  - name: "arm64: google: Introduce frankel, blazer, and mustang boards (v1)"
    url: https://lore.kernel.org/linux-arm-kernel/20251111192422.4180216-1-dianders@chromium.org/
    fetch: ok
  - name: Google Store, Pixel 10 tech specs
    url: https://store.google.com/us/product/pixel_10_specs?hl=en-US
    fetch: ok
  - name: Factory images for Nexus and Pixel devices
    url: https://developers.google.com/android/images
    fetch: partial
    fetch_via: "per-device tables script-rendered; the May 2026 bootloader note is in the static text"
  - name: Android bootloader locking and unlocking
    url: https://source.android.com/docs/core/architecture/bootloader/locking_unlocking
    fetch: ok
  - name: Android boot image header
    url: https://source.android.com/docs/core/architecture/bootloader/boot-image-header
    fetch: ok
  - name: Android DTB and DTBO partitions
    url: https://source.android.com/docs/core/architecture/dto/partitions
    fetch: ok
  - name: android.googlesource.com project list
    url: https://android.googlesource.com/
    fetch: ok
  - name: "9to5Google, Pixel 10 Exynos modem report"
    url: https://9to5google.com/2025/06/03/google-pixel-10-tensor-g5-exynos-modem-leak/
    fetch: ok
summary: {pass: 17, fail: 1, unverifiable: 0, gap: 0, adjudicate: 0}
---

# Verification of `pixel10`

Three passes. The first found five defects; the second, after corrections, found two failures and one
adjudication item; this third pass re-verified the corrected bullets and closed the adjudication. One
failure stands, recorded rather than fixed. The board declares no `instances:` key, correct for
`kind: board`.

- Quick-facts/1 "What is on the board": PASS — pass 3 at `e8e96f14`, bullet unchanged since. The
  `[press]` citation is now locatable: `resources.docs` holds one 9to5Google entry titled with the
  article's headline verbatim, `cite: false`, and the tag clause names it. The article says what the
  bullet says: hands-on images of a pre-release Pixel 10 Pro, a device-info app reading a baseband
  identifier beginning `g5400`, concluding the same Exynos 5400 modem as the Pixel 9 series. The
  Store page gives Tensor G5, Titan M2, 12 GB RAM, 128/256 GB, Wi-Fi 6E 802.11ax 2x2 MIMO, USB-C
  3.2 and the mmWave line carrying model GLBW0; dtbo entry 12 carries `samsung,exynos-cp` with link
  name PCIe and a `google,cp-pmic-spmi` child.
  Recorded, not failed, and worth acting on: entry 12's modem node carries a vendor-name property
  whose value names the part directly. The part could then rest at `[DT]` strength with the press
  report as corroboration, and the TODO could narrow to confirming on a shipped unit. Deliberately
  not applied in this pass.
  Also recorded: the article calls its subject a hands-on pre-release unit; "prototype" is the
  spec's word.
- Quick-facts/2 "Partitions and boot images": PASS — carried forward from pass 2 at `6797b8a3`,
  bullet unchanged. Both verifiers of that pass agreed.
- Quick-facts/3 "Unlock and boot policy": PASS — carried forward from pass 2 at `6797b8a3`, bullet
  unchanged. Both verifiers confirmed the scoping correction: `oem disable-verity`,
  `disable-verification`, `uart enable` and `ramdump disable` run unconditionally, `oem watchdog
  disable` only for blazer and frankel.
  Recorded: the AOSP page describes critical *sections* and `lock_critical`/`unlock_critical`
  *states*, not a `fastboot flashing unlock_critical` command.
- Quick-facts/4 "Physical console access": PASS — carried forward from pass 2 at `6797b8a3`, bullet
  unchanged; two verifiers agreed.
  Recorded by both: `fastboot oem uart config 3000000` sits behind a shell test that the UART mux is
  not virtual, while the bullet states it unconditionally.
- Quick-facts/5 "Per-revision device trees": PASS — carried forward from pass 2 at `6797b8a3`.
- Quick-facts/6 "Device-tree selection by the bootloader": PASS — carried forward from pass 2 at
  `6797b8a3`. The emulator-overlay correction verified there: both `0x078000` entries are
  pre-silicon emulator board overlays, and only the hybrid entry adds virtio devices.
- Quick-facts/7 "Kernel family and branch": FAIL — pass 3 micro-check at `f6c36414`, the current
  hash. **Third consecutive pass to fail this bullet, on a third distinct ground.**
  What holds. The positive claim is right and at the right strength, neither too strong nor too
  weak: the GrapheneOS source page carries a heading for forks of AOSP kernel prebuilt repositories
  with the builds replaced by GrapheneOS kernels built from the source repositories of the following
  section; this repository is listed under it, and `kernel_pixel_6.6` in that next section. The
  `[inference]` that the DTB and DTBO images are outputs of that same build **holds on every
  premise, and one premise is stronger than the bullet claims**: the shipped DTBO entry order
  matches the declared order group for group (four development-board overlays, then 9 frankel, 8
  blazer, 10 mustang, 3 diagnostic; 11 rango), and the board ids cited elsewhere in the spec land on
  the declared positions — blazer MP at entry 20, mustang MP at entry 30, rango MP at entry 10. The
  timing premise is 1:1 within the window: the kernel image is touched in all 17 commits, the muzel
  DTBO in 2 (initial import plus 2026-08-19), and the muzel device-tree directory has exactly one
  commit in that window, 3 days 22 hours earlier, touching only two overlay includes — which also
  explains why the base DTB was never touched again.
  Three defects.
  (a) **Too strong.** "Byte-identity with a stock vendor artifact cannot be checked at all: AOSP
  publishes no laguna kernel-prebuilt repository." The premise is true — the fresh AOSP index has no
  laguna, muzel or rango entry — but it closes only one route. Google publishes factory and full-OTA
  images for these devices, carrying a stock DTBO partition image and the DTB; a byte comparison is
  possible in principle and would settle the inference outright, more decisively than the hardware
  check the bullet points at. Proposed correction: say what was not done rather than what cannot be
  — "was not checked here: AOSP publishes no laguna kernel-prebuilt repository, so the only stock
  artifact to compare against is the DTBO image inside Google's published Pixel 10 factory or
  full-OTA image, which this spec did not unpack".
  (b) **The `[inference]` premises carry no provenance class of their own**, which the format
  requires. All three are tree-and-build-definition observations, i.e. `[source-observed]`, and the
  bullet's own `[source-observed]` clause lists different items and covers neither the build
  definitions nor the commit histories. Proposed correction: tag each premise and extend that
  clause.
  (c) **The TODO does not name what would settle the inference.** `TODO (verify on hardware)` is
  scoped to a shipped build's version string, which settles whether the *kernel image* is a
  GrapheneOS build, not whether the DTB and DTBO are outputs of that build. Proposed correction:
  name the byte comparison against the published stock image as the inference's verification method.
  Recorded: the page names a *set* of source repositories collectively and the spec narrows that to
  `kernel_pixel_6.6`. The narrowing is corroborated by the muzel and rango device definitions living
  in that repository, but it is a reading of the page rather than a sentence on it.
  Note on (b) and (c): this is the first use of the `[inference]` class in any spec here, and it
  does not satisfy the class's own formation rules. That is evidence about the tag's design as much
  as about this bullet — a class whose first real use gets its own requirements wrong is a class
  whose requirements are not discoverable from the bullet being written.
- Quick-facts/8 "Companion parts": PASS — carried forward from pass 2 at `6797b8a3`.
- Quick-facts/9 "Power": PASS — pass 3 at `e8e96f14`, bullet unchanged since. Counts reproduced
  independently from the decompiled blob against the boolean marker on each regulator child:
  `da9188` 41 children, 34 marked, 7 unmarked and all LDOs; `da9189` 42 children, 30 marked, 12
  unmarked of which 11 LDOs and 1 buck. Matches the bullet exactly, "almost all LDOs" included. The
  mailbox half holds: the regulator node's handle resolves to the CPM interface node.
- Gotchas/1: PASS — carried forward from pass 2 at `6797b8a3`; both verifiers agreed.
- Gotchas/2: PASS — carried forward from pass 2 at `6797b8a3`; both agreed.
  Recorded: no cited document states that a production overlay table applied over an upstream DTB
  "fails in the bootloader"; that half is a conclusion from the README's rationale, and with the
  `[inference]` class now available it would be better tagged as one than as `[doc]`.
- Gotchas/3: PASS — carried forward from pass 2 at `6797b8a3`; both agreed.
- Gotchas/4: PASS — carried forward from pass 2 at `6797b8a3`; both agreed.
- Gotchas/5: PASS — carried forward from pass 2 at `6797b8a3`; both agreed.
- Gotchas/6: PASS — carried forward from pass 2 at `6797b8a3`.
- variants/Google Pixel 10 Pro: PASS — carried forward from pass 2 at `6797b8a3`; the RAM-claim
  correction verified there.
- variants/Google Pixel 10 Pro XL: PASS — carried forward from pass 2 at `6797b8a3`.
  Recorded: "display size" is a product fact the device tree does not carry, though everything the
  `tag: DT` row rests on does.
- variants/Google Pixel 10 Pro Fold: PASS — carried forward from pass 2 at `6797b8a3`.

## Frontmatter

Not a fact bullet, so not a verdict line; recorded because every `[DT]` value in the spec inherits
it. The `laguna-kernel-prebuilts` `note:` **FAILS on two clauses**, both recorded and not fixed:

1. The same over-reach as Quick-facts/7 (a): "Byte-identity with a stock vendor artifact is
   uncheckable." Premise true, conclusion does not follow — the stock DTBO image ships inside the
   published factory and full-OTA images.
2. "Carries no README, licence or description of its own" — README and licence check out, the
   description does not. The repository carries a one-line host description naming the four devices
   whose prebuilts it holds. The note's *argument* survives, since that description says what the
   repository holds and nothing about where the blobs came from, but the stated fact is wrong. The
   distinction matters because the sibling `license:` field explicitly reasons about what the host
   reports.

Everything else in the entry verified: the pinned commit is HEAD of branch `17` (2026-09-14); the
muzel `dtbo.img` sha256 matches on a fresh download and its header reports 34 entries; the listed
files exist; no README and no licence file anywhere in the tree and the host reports no licence,
matching the `license:` field; the source page is indeed what states the builds are GrapheneOS
builds; and AOSP publishes no laguna kernel-prebuilt repository.

## Process notes

1. **Why this record is frozen.** Three successive corrections to this spec each introduced a new
   defect: "published only as prebuilts" → "identity unverified" (too weak, failed by two readers)
   → the current wording (too strong, plus two formation shortfalls). Each was caught by the next
   pass, and each pass cost a full verification cycle. The corrections proposed above are therefore
   recorded for a person to apply and re-verify deliberately, rather than applied now.
2. **The board spec's series citations resolve only through composition** with `tensor-g5`, which
   carries the `series:` entries. Locatable under the rules; invisible to someone reading the board
   spec alone.
3. **Leak scan: clean across this pass's verifiers.** The scoped-pass verifier returned 0 runs, 0
   high-signal and 0 ALL-CAPS identifiers against the decompiled blob, the entry-12 overlay, a build
   script and the module lists; the micro-check verifier returned clean against 40 files including
   the build definitions. Earlier passes' findings were all device-tree node names, property names
   and a tty name, reviewed and cleared as `[DT]` or standard nomenclature. No driver or firmware
   source is reproduced anywhere.
