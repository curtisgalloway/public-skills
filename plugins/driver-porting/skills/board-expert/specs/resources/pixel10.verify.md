---
spec: pixel10
spec_file: pixel10.spec.md
spec_sha256: 6797b8a3297adef613a2d93dea03cb118c57c5f3a5786754ca54b1daf72a6339
verified: 2026-09-18
verifier: >-
  Claude Opus 5 (1M context) under Claude Code, orchestrating spec-verifier. Second pass, after the
  corrections the first pass proposed were applied. Two independent subagents with fresh contexts: a
  full-spec verifier over all 18 claims, and a second verifier over the bring-up-critical facts
  (debug console, unlock and flash path, kernel provenance) per the two-verifier rule. Neither saw
  the author's report, the previous record, this conversation, or the other's work; both were told a
  correction that overshot is as much a FAIL as the original defect.
sources:
  - name: laguna-kernel-prebuilts
    url: https://github.com/GrapheneOS/device_google_laguna-kernels_6.6
    commit: 80c104d7e5591ebc3cd413f54b076d972484ff0b
    fetch: ok
  - name: laguna-kernel-source
    url: https://gitlab.com/grapheneos/kernel_pixel_6.6
    fetch: ok
    fetch_via: "project metadata and root tree at ref 17; no file contents read"
  - name: pixelscripts
    url: https://gitlab.com/LinaroLtd/googlelt/pixelscripts
    commit: 156bd361b39c55303cb4de33cd66ace9b1f610f2
    fetch: ok
  - name: "Add Laguna/Tensor G5 SoC and Frankel, Blazer & Mustang boards (v4)"
    url: https://lore.kernel.org/all/20260918-contrib-pg-pixel10-initial-dts-v4-0-745eaca28b1a@linaro.org/
    fetch: ok
    fetch_via: "t.mbox.gz with a Wget user agent; base-commit 3f2425f5b5bbbdd991ca9cdfd5502e68d8895998"
  - name: "arm64: google: Introduce frankel, blazer, and mustang boards (v1)"
    url: https://lore.kernel.org/linux-arm-kernel/20251111192422.4180216-1-dianders@chromium.org/
    fetch: ok
  - name: Google Store, Pixel 10 tech specs
    url: https://store.google.com/us/product/pixel_10_specs?hl=en-US
    fetch: ok
  - name: Factory images for Nexus and Pixel devices
    url: https://developers.google.com/android/images
    fetch: partial
    fetch_via: "per-device image tables are script-rendered; the prose warnings are readable"
  - name: Android bootloader locking and unlocking
    url: https://source.android.com/docs/core/architecture/bootloader/locking_unlocking
    fetch: ok
  - name: Android boot image header
    url: https://source.android.com/docs/core/architecture/bootloader/boot-image-header
    fetch: ok
  - name: Android DTB and DTBO partitions
    url: https://source.android.com/docs/core/architecture/dto/partitions
    fetch: ok
  - name: GrapheneOS source page
    url: https://grapheneos.org/source
    fetch: ok
  - name: "9to5Google, Pixel 10 Exynos modem report (located by search; NOT an entry in the spec)"
    url: https://9to5google.com/2025/06/03/google-pixel-10-tensor-g5-exynos-modem-leak/
    fetch: ok
summary: {pass: 15, fail: 2, unverifiable: 0, gap: 0, adjudicate: 1}
---

# Verification of `pixel10`

Second verification pass. The first pass found five defects; every proposed correction was applied,
and this pass re-derived all 18 claims from the sources without reference to either. The board
declares no `instances:` key, which `SPEC-FORMAT.md`'s key table marks as correct for `kind: board`,
so there are no `instances/<name>` claims.

- Quick-facts/1 "What is on the board": FAIL — citation locatability, not substance. The `[doc]` and
  `[DT]` halves hold: the Google Store page gives Tensor G5, the Titan M2 security coprocessor,
  "128 GB / 12 GB RAM" and "256 GB / 12 GB RAM", USB Type-C 3.2, Wi-Fi 6E 802.11ax 2x2 MIMO and
  "5G mmWave + Sub 6GHz Model GLBW0"; dtbo entry 12 carries a `samsung,exynos-cp` node whose link
  name is PCIe and a `google,cp-pmic-spmi` node. The `[press]` clause names "a 9to5Google report of
  a prototype's baseband string", which is an entry in neither this spec's `resources.docs` nor
  `tensor-g5`'s, and gives no URL, title or date — it cannot be located from the spec. The verifier
  found the article independently and confirms it says what the spec says it says. Proposed
  correction: add a `resources.docs` entry (title "9to5Google, Pixel 10 will still use an Exynos
  modem rather than MediaTek in Tensor G5, leak shows", the URL above, `access: public`,
  `cite: false`, a `verified:` date) and name it in the parenthetical. Better option, noted by the
  verifier: entry 12's modem node carries its own vendor name string, which would let the part
  number rest on `[DT]` rather than on press at all.
- Quick-facts/2 "Partitions and boot images": PASS — both verifiers. Header v4 keeps kernel and
  ramdisk in `boot` and the DTB in the vendor boot partition, which supports multiple vendor ramdisk
  fragments (AOSP boot-image-header page); the dt table and its per-entry `id`/`rev` matching (AOSP
  DTB/DTBO page); `mkbootimg --header_version 4` with a dtb image, a vendor bootconfig and two
  ramdisk fragments, the erase set (`boot`, `dtbo`, `vendor_boot`, plus `vendor_kernel_boot` and
  `init_boot` behind a partition-exists probe), the flash order (vendor_boot then boot) and the
  stage-and-boot alternative (pixelscripts Makefile); `make RUNTARGET=frankel flash` appears in the
  v4 cover letter; the A/B slot note is on the factory-images page. The second verifier
  independently re-derived the `dtbo.img` header and matched its recorded sha256.
- Quick-facts/3 "Unlock and boot policy": PASS — **both verifiers confirmed the correction applied
  after the first pass.** `prepare-device` runs `oem disable-verity`, `disable-verification`,
  `uart enable` and `ramdump disable` unconditionally, and `oem watchdog disable` only when the
  target is blazer or frankel — exactly the scoping the bullet now claims. Retail devices ship
  locked, unlock is denied unless the OEM-unlocking developer setting is on, unlock performs a
  factory data reset, critical sections carry their own lock state, and `flashing lock` reverses it
  (AOSP locking page); the May 2026 anti-rollback bump names all four Pixel 10 models
  (factory-images page); the fatal missing-`ufs0`-alias is in the v4 cover letter.
  Recorded by the second verifier, not failed: the AOSP page describes critical *sections* and the
  `lock_critical`/`unlock_critical` *states*, not a `fastboot flashing unlock_critical` command, so
  "critical partitions need a separate `unlock_critical`" is close to but not what the page says.
- Quick-facts/4 "Physical console access" (the board's debug console bullet, two verifiers): PASS —
  the series node, the `serial0` alias and `stdout-path`, the production `chosen` giving
  `console=ttyS0,115200n8`, the USB-Cereal dongle with its 1.8 V selection and absent orientation
  detection, power-plus-volume-down for fastboot, the ~60 s press to recover a crashed kernel, and
  SysRq over the line. The README's cable photo is Pixel 6 material, which the spec says.
  Recorded by both verifiers, not failed: `fastboot oem uart config 3000000` sits inside a shell
  test that the `fastboot oem uart mux` output does not report a virtual mux, while the bullet
  states it unconditionally. The spec tracks conditionals elsewhere (the watchdog line), so a reader
  could reasonably expect the guard here.
- Quick-facts/5 "Per-revision device trees": PASS — the three board files exist in v4, each
  including `lga-pixel-common.dtsi`, `lga-frankel.dts` carrying `model = "Frankel"` and the
  compatible pair; patch 3/4 states only B0 is officially supported and that the trees boot EVT
  devices with A0 silicon, which the cover letter repeats for one EVT 1.1 board; the production
  blob's root has no `model` and `compatible = "google,lga"` only, with entry 12 supplying
  `model = "FRANKEL MP based on LGA"`; the muzel directory holds the two blobs and one `dtbo.img`.
- Quick-facts/6 "Device-tree selection by the bootloader": PASS — **the correction applied after the
  first pass verified.** The header reads magic `0xd7b7ab1e`, 32-byte header and entries, 34
  entries, page size 4096, every `custom` word 0. Ids and models: frankel Proto/EVT/DVT/PVT at
  `0x070302`–`0x070305`, MP at `0x070306` rev `0x010000` (entry 12); blazer `0x070402`–`0x070406`
  (MP entry 20); mustang `0x070502`–`0x070506` (MP entry 30); two Deepspace development-board
  entries at `0x070101`; two at `0x078000` reading "EMULATOR board based on LGA" and "SoC Hybrid
  emulator board based on LGA"; entries 31–33 with id 0 setting the `eng`/`user`/`userdebug`
  variants and their security and ramdump policy. The emulator pair disables the trace funnels, the
  ETMs and 62 interrupt-aggregator targets, carries ten `gpio-line-names` tables, and marks the GPU
  node pre-silicon and virtual-platform; **only the hybrid entry adds virtio MMIO devices**, which
  the corrected bullet says. Entries 11 and 12 differ in exactly two properties. The v1 patch 1/4
  message gives the field widths, the worked example and the never-another-product matching rule.
- Quick-facts/7 "Kernel family and branch": ADJUDICATE — **the two verifiers disagree; both readings
  are recorded and the claim is excluded from the pass/fail counts until a person settles it.**
  Not in dispute: the v4 series is dated 2026-09-18, rebased on next-20260918 with base-commit
  `3f2425f5b5bbbdd991ca9cdfd5502e68d8895998`, adds `lga-frankel.dts` and boots to an initramfs
  busybox shell; the prebuilt image's banner is `6.6.143-android15-8-gcf06d8aff8ae-4k` built
  2026-09-14; the per-board module lists are as described; `kernel_pixel_6.6` is public with default
  branch `17` and per-device build scripts at its root.
  *Full verifier (PASS):* the GrapheneOS source page lists the laguna prebuilt repository for the
  Pixel 10 family and, in the next section, `kernel_pixel_6.6` as the monolithic repository for
  10th-generation Pixel kernels — which is what the corrected bullet says.
  *Second verifier (FAIL):* the same page's heading reads in full "GrapheneOS forks of AOSP kernel
  prebuilt repositories **with the builds replaced with the GrapheneOS kernels built from the source
  repositories listed in the next section**", and the next section is headed "GrapheneOS forks of
  AOSP kernel repositories". On that reading both repositories the spec names are third-party forks,
  and the prebuilt binaries are not the vendor's but that project's own builds — so "the shipped
  binaries come from the laguna prebuilts repository" is backwards, and the version string and build
  date describe a third-party rebuild rather than a retail binary. Two checks it offers in support:
  the prebuilts commit was authored by a GrapheneOS maintainer on 2026-09-14T23:56Z with the message
  "rebuild with latest changes", and the cached kernel image's build timestamp is the same day.
  Its proposed correction, if that reading wins: say the source is published upstream by the vendor
  as a monolithic per-generation repository, that the copy read here is a third-party fork of it,
  and that the prebuilt directory read here is a third-party fork whose kernel builds that project
  states it has replaced with its own — citing the vendor repository if the "shipped binaries" claim
  is kept. It also suggests carrying the same caveat wherever `[DT]` facts come from `lga-b0.dtb` or
  `dtbo.img`, while noting it found nothing suggesting those blobs' values are altered.
  Note for the adjudicator: this bullet was rewritten between passes. The first pass failed it for
  saying the kernel was "published only as prebuilts"; the correction introduced the "shipped
  binaries" clause now in dispute.
- Quick-facts/8 "Companion parts": PASS — every part named appears in dtbo entry 12: the MAX77779
  PMIC, charger, fuel gauge and voltage monitor over SPMI; the MAX77759 Type-C port controller;
  `nxp,pca9468`; `cps,cps4041`; `richtek,rt6160`; `ti,tps628600`; `dlg,slg51002`;
  `samsung,exynos-cp` and `samsung,exynos-gnss`; Broadcom WLAN and Bluetooth; `st,st21nfc` with
  `st,st54spi`; `focaltech,ts`; `cirrus,cs35l43` and `cirrus,cs40l27b`; `qcom,qbt-handler`; and all
  six `google,gs-*` panel entries.
- Quick-facts/9 "Power": FAIL — the mailbox claim and the battery-side claim hold (the main PMIC
  regulator node carries a mailbox handle and a destination channel; entry 12 carries the MAX77779
  SPMI family). The spec says the PMIC's rails are "monitor-only for the OS" without qualification,
  and the device tree does not say that: under `da9188mfd` in `lga-b0.dtb` the `da9188` set has 41
  rails of which 34 carry the monitor-only marker and 7 do not, all LDOs; a second set `da9189` sits
  beside it with 42 rails of which 30 are marked and 12 are not (11 LDOs and one buck). 64 of 83
  overall. Proposed correction: "most of its rails are marked monitor-only for the OS (34 of 41 in
  the `da9188` set in `lga-b0.dtb`; a companion `da9189` set of 42 beside it has 30 marked)", and
  either name the companion set or delegate the pair to `tensor-g5`. The existing
  `TODO (verify on hardware)` already asks which rails the OS may touch, so this is wording rather
  than a new open question.
- Gotchas/1: PASS — both verifiers. The series gives the console node a DesignWare-class compatible
  pair with a 16550-at-32-bit-stride layout and leaves it disabled; patch 3/4 says the bootloader
  enables the UART when the console is turned on and that the baud is never hardcoded in the DT; the
  enable command lives in the Makefile. "PL011 assumptions do not apply" follows from the compatible
  and the register-stride properties.
- Gotchas/2: PASS — both verifiers. The v4 cover letter states the fatal missing-`ufs0`-alias and
  that the flashing scripts apply a placeholder; the Makefile applies the overlay to every `lga-`
  board DTB and `prepare-device` erases `dtbo`; the overlay's own header says the bootloader writes
  calibration data into that node.
  Recorded by the full verifier, not failed: no cited document states that a production overlay
  table applied over an upstream DTB "fails in the bootloader" — the README's stated reason for
  erasing the partition is that upstream does not support overlays the way Android does. The advice
  is sound and the `ufs0` half is documented verbatim; the `dtbo` half is a conclusion drawn from
  that rationale. With the `[inference]` class now available, this half would be better tagged as
  one than as `[doc]`.
- Gotchas/3: PASS — both verifiers. The factory-images May 2026 warning names the four Pixel 10
  models, the incremented anti-rollback version, and the unbootable-state mechanism.
- Gotchas/4: PASS — both verifiers. Unlock triggers a factory data reset and is denied unless the
  OEM-unlocking developer setting is enabled.
- Gotchas/5: PASS — both verifiers. `prepare-device` issues `oem watchdog disable` only for blazer
  and frankel, before the flash and boot steps; the blob carries two `google,wdt` nodes.
- Gotchas/6: PASS — the v4 cover letter places the Pixel 10a with the Tensor G1–G4 generation,
  described as Samsung Exynos offshoots, against Laguna as an in-house Google design.
- variants/Google Pixel 10 Pro: PASS — **the correction applied after the first pass verified.**
  `lga-blazer.dts` differs from `lga-frankel.dts` only in `model`, `compatible` and its header
  comment; ids run `0x070402`–`0x070406` with MP at entry 20; the blazer MP overlay differs from
  frankel MP in its panel node, its touch controller and its camera sensor nodes, supporting
  "display, cameras" now that the unsupported RAM claim is gone.
- variants/Google Pixel 10 Pro XL: PASS — same shape: `lga-mustang.dts` differs only in `model`,
  `compatible` and its header comment; ids `0x070502`–`0x070506` with MP at entry 30; its panel node
  differs from both siblings and its camera sensors differ from frankel's. Recorded, not failed:
  "display size" specifically is a product fact the device tree does not carry, though everything
  the `tag: DT` row rests on does.
- variants/Google Pixel 10 Pro Fold: PASS — the rango directory's `lga-b0.dtb` is byte-identical to
  muzel's (sha256 `f238c200…a030` on both) and its `dtbo.img` has exactly 11 entries, ids
  `0x070602`–`0x070606`, models naming RANGO stages, compatible `"google,lga-rango", "google,lga"`;
  the v4 series carries board files for frankel, blazer and mustang only, so "no public device-tree
  source" holds, and `shares: [soc]` is consistent with the identical blob.

## Process notes

Not verdicts.

1. **The board spec's series citations resolve only through composition.** `pixel10.spec.md`
   declares no `resources.series:` of its own; "series v4" and "series v1" resolve through
   `tensor-g5`'s `series:` entries, which the `linux-mainline` note points at explicitly. Locatable
   under the rules, but a reader of the board spec alone would not find them.
2. **Two corrections from the first pass are now confirmed by both verifiers** (the unlock-policy
   scoping and the `0x078000` emulator overlays), one is confirmed by the full verifier (the variant
   rows), and one is disputed (Quick-facts/7). A correction that overshoots is the failure mode this
   pass was designed to catch, and it caught one.
3. **Leak scan: findings, reviewed and cleared.** The full verifier's scan against the prebuilts,
   the dtbo entries, the pixelscripts tree and the v4 series returned 0 shared token runs, 0
   ALL-CAPS identifiers and 5 lowercase ones (`board_id`, `board_rev`, `link_name`,
   `lsion_cli16_uart`, `ttyS0`) — device-tree property names, a device-tree node label the spec
   already carries, and the standard Linux tty name. The second verifier's scan reduced to 0 shared
   runs after one rewrite pass with `ttyS0` remaining, cleared on the same grounds. All are `[DT]`
   or standard nomenclature, which the format admits. No driver or firmware source is reproduced.
