---
spec: pixel10
spec_file: pixel10.spec.md
spec_sha256: 3db7de3fc095182ccb26d3eb867044f88f0f92636532ee4f0152729855a7304e
verified: 2026-09-18
verifier: >-
  Claude Opus 5 (1M context) under Claude Code, orchestrating spec-verifier. Two independent
  subagents with fresh contexts: a full-spec verifier over all 18 claims, and a second verifier
  over the bring-up-critical facts (debug console, unlock and flash path) per the two-verifier
  rule. Neither saw the author's report, this conversation, or the other's work.
sources:
  - name: laguna-kernel-prebuilts
    url: https://github.com/GrapheneOS/device_google_laguna-kernels_6.6
    commit: 80c104d7e5591ebc3cd413f54b076d972484ff0b
    fetch: ok
  - name: "Laguna/Tensor G5 series v4 (lore.kernel.org thread mbox, 9 messages)"
    url: https://lore.kernel.org/all/20260918-contrib-pg-pixel10-initial-dts-v4-0-745eaca28b1a@linaro.org/
    fetch: partial
    fetch_via: "canonical HTML bot-challenged; t.mbox.gz with a Wget user agent works"
  - name: "Laguna/Tensor G5 series v1 (lore.kernel.org thread mbox, 36 messages)"
    url: https://lore.kernel.org/linux-arm-kernel/20251111192422.4180216-1-dianders@chromium.org/
    fetch: partial
    fetch_via: "as above"
  - name: pixelscripts
    url: https://gitlab.com/LinaroLtd/googlelt/pixelscripts
    commit: 156bd361b39c55303cb4de33cd66ace9b1f610f2
    fetch: ok
  - name: Google Store, Pixel 10 tech specs
    url: https://store.google.com/us/product/pixel_10_specs?hl=en-US
    fetch: ok
  - name: Factory images for Nexus and Pixel devices
    url: https://developers.google.com/android/images
    fetch: partial
    fetch_via: "per-device tables script-rendered, unreadable to a fetcher"
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
  - name: "GrapheneOS kernel_pixel_6.6 (project metadata and root listing only)"
    url: https://gitlab.com/grapheneos/kernel_pixel_6.6
    fetch: ok
  - name: "9to5Google, Pixel 10 Exynos modem report"
    url: https://9to5google.com/2025/06/03/google-pixel-10-tensor-g5-exynos-modem-leak/
    fetch: ok
summary: {pass: 13, fail: 5, unverifiable: 0, gap: 0}
---

# Verification of `pixel10`

First end-to-end run of `spec-verifier` against this spec. The board declares no `instances:` key,
which the format requires of a `board` kind, so there are no `instances/<name>` claims; the console
instance the spec cross-references (`lsion_cli16_uart`) resolves in the composed `tensor-g5` spec.

- Quick-facts/1 "What is on the board": PASS — SoC, security chip, 12 GB RAM at both 128 GB and
  256 GB, 5G mmWave plus Sub-6 on model GLBW0, Wi-Fi 6E 2x2 MIMO and USB Type-C 3.2 read off the
  Google Store Pixel 10 spec page; the modem description checked against the frankel MP overlay
  (dtbo entry 12), which carries the Samsung cellular-processor node with a PCIe link name, the
  modem-PMIC-over-SPMI node and the ap-to-cp PCIe reset pins. The `[press]` part (Exynos 5400) was
  re-derived against a June 2025 9to5Google report of a baseband string read from a leaked Pro DVT
  unit; the bullet carries its required hardware TODO. Note, not a failure: that report is not an
  entry in `resources.docs`, so the `[press]` citation is not locatable from the spec alone.
- Quick-facts/2 "Partitions and boot images": PASS — boot-image v4 layout and the DTB living in
  `vendor_boot` on the Android boot image header page; the dt-table container, its `id`/`rev` fields
  and bootloader matching on the DTB/DTBO partitions page; the build and flash flow (header version
  4, the whole board DTB, a vendor bootconfig, the erase set, the flash pair, the stage-and-boot
  alternative, `make RUNTARGET=frankel flash`) against the pixelscripts Makefile at the pinned
  commit; the A/B slot note against the factory-images page. Both verifiers agree.
- Quick-facts/3 "Unlock and boot policy": FAIL — the spec says the flow runs `fastboot oem watchdog
  disable` and `ramdump disable` "on frankel and blazer". In the pixelscripts `prepare-device`
  target at commit 156bd361, only watchdog-disable is inside the conditional testing the run target
  against blazer and frankel; ramdump-disable sits after that conditional's `endif` and runs for
  every supported target, as do disable-verity, disable-verification and uart enable. **Both
  verifiers reached this independently.** Proposed correction: "The upstream flow also runs
  `fastboot oem disable-verity`, `disable-verification` and `ramdump disable` on every target, and
  `fastboot oem watchdog disable` only on frankel and blazer." Everything else in the bullet passes:
  locked at retail delivery, the OEM-unlocking setting gating `fastboot flashing unlock`, the
  factory-data-reset wipe, the separate `unlock_critical`, and `fastboot flashing lock` reversing it
  (Android locking/unlocking page); the May 2026 anti-rollback bump (factory-images page); the fatal
  missing-`ufs0`-alias (pixelscripts commit message and the v4 cover letter). Recorded but not
  failed: "lowers the verified-boot state" is a loose paraphrase — the cited page only associates
  the orange verified-boot state with an unlocked flash state, never the converse direction the
  sentence implies. Tighten the wording or add the AVB Verified Boot page as a citation.
- Quick-facts/4 "Physical console access" (the board's debug console bullet, two verifiers): PASS —
  `serial@db62000` and the `lsion_cli16_uart` label in the v4 `lga.dtsi`; `serial0` alias and
  `stdout-path` in `lga-pixel-common.dtsi`; the production `chosen` bootargs in the decompiled
  `lga-b0.dtb` give `console=ttyS0,115200n8`; the USB-Cereal dongle, its 1.8 V selection switch, its
  lack of orientation detection, power-plus-volume-down for fastboot, the ~60 s long press to
  recover from a crashed kernel, and SysRq over the line, all in the pixelscripts README (whose
  cable photo and example log are Pixel 6 material, as the spec says); `fastboot oem uart enable`
  and `uart config 3000000` and the ttyS0-with-bootloader-supplied-`console=` behavior in the
  Makefile. Recorded but not failed, by both verifiers: `fastboot oem uart config 3000000` is
  guarded by a shell test that the `fastboot oem uart mux` output does not contain a virtual entry,
  while the spec states it unconditionally.
- Quick-facts/5 "Per-revision device trees": PASS — the three board `.dts` files exist in the v4
  series; `lga-frankel.dts` carries `model = "Frankel"` and `compatible = "google,lga-frankel",
  "google,lga"`; diffing frankel against blazer and mustang shows only the model, the first
  compatible and the header comment change; all three include `lga-pixel-common.dtsi`. The A0/EVT
  claim is stated in both the v4 cover letter and patch 3/4. The production blob's root has
  `compatible = "google,lga"` and no `model`; overlay entry 12 supplies `model = "FRANKEL MP based
  on LGA"` with the same compatible pair. The muzel directory holds `lga-a0.dtb`, `lga-b0.dtb` and
  one `dtbo.img`.
- Quick-facts/6 "Device-tree selection by the bootloader": FAIL — the spec calls the two id-`0x078000`
  table entries "an `0x078000` pair that only disables coresight nodes". Entries 2 and 3 of the muzel
  dtbo at the pinned commit are full pre-silicon *emulator board* overlays: entry 2 sets the root
  model to `EMULATOR board based on LGA` (compatible `google,lga`, `google,lga-emulator`), entry 3 to
  `SoC Hybrid emulator board based on LGA` (`google,lga-soc-hybrid`, `google,lga-soc-hybrid-emulator`).
  Each carries 123–127 fragments, of which only about 110 are status-disable fragments, and those
  cover the CoreSight trace path *and* several memory-subsystem interrupt aggregators. The rest
  supply the eleven pinctrl/PMIC-GPIO gpio-line-name tables, a `chosen` fragment with bootargs and
  an rng seed, a `gpu` fragment marked pre-silicon plus virtual-platform (entry 2) or emulator
  (entry 3), a fixed 200 MHz clock that entry 2 wires to the console UART, a UFS phy-init skip, and
  in entry 3 virtio block devices, a virtual UART and in-emulation markers on the power controller
  and the cpm clock. Proposed correction: replace the clause with "a pair of pre-silicon emulator
  board overlays at `0x078000` (`EMULATOR board based on LGA` and `SoC Hybrid emulator board based
  on LGA`), which besides disabling the CoreSight trace path and several interrupt aggregators carry
  the full pinctrl line-name tables, a virtual/emulated GPU marker and, for the hybrid entry, virtio
  devices", and retire the closing `TODO` about the meaning of the `0x078000` overlay, which the
  model strings answer. Second, smaller discrepancy in the same bullet: "socketed" on the `0x070101`
  entry is supported by neither cited source — the dtbo gives models `Deepspace board based on LGA`
  and `Deepspace board + Tesseract based on LGA` with a `google,lga-deepspace` compatible, and the
  v1 patch 1/4 message describes the author's own socketed development board without naming it; a
  later reply in the same v1 thread does tie the `070101` id to a deepspace devboard, so
  "development board" stands. Proposed correction: drop "socketed".
  Scope note: the second verifier passed this bullet within its narrower brief — it examined the
  `board_id`/`board_rev` encoding, the closest-revision matching rule and the dtbo table values, all
  of which check out, and did not reach the `0x078000` pair. Not a disagreement.
  Everything else in the bullet passes exactly: the `board_id` and `board_rev` encodings and the
  stage codes (0x02 Proto, 0x03 EVT, 0x04 DVT, 0x05 PVT, 0x06 MP) from the v1 patch 1/4 message and
  its binding comments; the closest-revision-never-another-product matching rule from the same
  message; magic `0xd7b7ab1e`, 32-byte entries, page size 4096, 34 entries and all-zero `custom`
  fields read straight out of the image header (the second verifier independently recomputed the
  image's sha256 and matched the frontmatter note); frankel `0x070302`–`0x070305` and MP `0x070306`
  rev `0x010000` at entry 12; blazer MP entry 20 and mustang MP entry 30; the three id-0
  `eng`/`user`/`userdebug` build-variant overlays that set security and dump policy; frankel PVT vs
  MP differing only in id and model (a 12-line diff); and frankel vs blazer MP differing in panels,
  touch and display PMIC — though that diff is 3541 lines and also covers UWB, cameras and
  regulators, so "differ in panels, touch, and display PMIC" is true but not exhaustive.
  One presentational note from the second verifier: the v1 message describes `stage` as a 4-bit
  field, which the spec's `<< 16 | product << 8 | stage` shorthand does not convey, though every
  value it yields is correct.
- Quick-facts/7 "Kernel family and branch": FAIL — the spec says the production kernel is "published
  only as prebuilts" and cites the GrapheneOS source page. That page, fetched fresh, introduces the
  prebuilt repositories as forks of AOSP kernel prebuilt repositories with the builds replaced by
  GrapheneOS kernels "built from the source repositories listed in the next section", and that next
  section lists `kernel_pixel_6.6` — "Monolithic repository for 10th gen Pixel kernels" — linked to
  `https://gitlab.com/grapheneos/kernel_pixel_6.6`. That project resolves (public, default branch
  `17`, active the same day as the prebuilts commit) and its root listing carries per-device build
  scripts. The verifier read the listing only, no file contents. Proposed correction: change the
  clause to say the 10th-gen Pixel kernel *source* is published as a monolithic repository
  (`kernel_pixel_6.6`, GitLab) while the shipped binaries come from the laguna prebuilts repository;
  add that repository to `resources.repos`; and fix the frontmatter note on the GrapheneOS source
  page doc entry, which currently reads "lists the laguna kernel prebuilt repository and no laguna
  kernel source repository". The Orientation prose ("the vendor kernel source is not published") has
  the same problem and should be revisited, though Orientation carries no verdict.
  The rest of the bullet passes: v4 dated 2026-09-18 with "Rebase on next-20260918" in its
  changelog, adding `lga-frankel.dts` and booting to an initramfs busybox shell (cover letter); the
  prebuilt image's version string is exactly `6.6.143-android15-8-gcf06d8aff8ae-4k`, built Mon Sep
  14 2026; `init.insmod.frankel.cfg` loads a Broadcom wlan driver, the Cirrus haptics pair and a
  FocalTech touch driver after the common set, and the blazer and mustang configs substitute a
  Synaptics touch driver.
- Quick-facts/8 "Companion parts": PASS — every named part has a matching compatible in the frankel
  MP overlay: MAX77779 PMIC, charger, fuel gauge and voltage monitor all over SPMI; the MAX77759
  Type-C port controller; NXP PCA9468; CPS4041; Richtek RT6160 and TI TPS628600; Dialog SLG51002;
  the Samsung Exynos cellular processor and GNSS; Broadcom Wi-Fi and a Broadcom Bluetooth node;
  ST21NFC with an ST54 SPI secure element; a FocalTech touch controller; Cirrus CS35L43 and
  CS40L27B; a Qualcomm fingerprint handler; and the six `google,gs-*` panel entries exactly as
  listed.
- Quick-facts/9 "Power": PASS — the `da9188mfd` node with its regulator, RTC, GPIO and vGPIO
  children is in the decompiled `lga-b0.dtb`; the MAX77779 family SPMI clients are in overlay entry
  12; the delegation of the rails to the `tensor-g5` spec is consistent with where the node lives.
- Gotchas/1: PASS — `lga.dtsi` gives the console UART `compatible = "google,lga-uart",
  "snps,dw-apb-uart"` with `status = "disabled"`; v4 patch 3/4's notes say the bootloader enables the
  UART when the console is turned on and that the baud is never hardcoded in the DT; the Makefile's
  `fastboot oem uart enable` confirms the fastboot step. Both verifiers agree.
- Gotchas/2: PASS — the pixelscripts README states that because upstream does not support overlays
  the way Android does, the flow packages full DTBs with `vendor_boot.img` and erases the `dtbo`
  partition; the Makefile erases `dtbo` and applies `lga-ufs-placeholder.dtbo` with `fdtoverlay`;
  that overlay's own header states the Pixel bootloader treats a missing `ufs0` alias as a fatal
  error, and the v4 cover letter says the same. Recorded: the "fails in the bootloader" wording for
  the mixed-flow case is an inference from the README's rationale rather than an explicit statement
  there. Both verifiers agree.
- Gotchas/3: PASS — the factory-images page's May 2026 warning names Pixel 10, 10 Pro, 10 Pro XL and
  10 Pro Fold, says the update increments the bootloader anti-rollback version, and that older
  Android 16 builds can no longer be flashed and booted afterwards; the inactive slot retains the
  older bootloader and falling back to it leaves the device unbootable. Both verifiers agree.
- Gotchas/4: PASS — the locking/unlocking page requires `get_unlock_ability` to be 1, obtained by
  enabling OEM unlocking in developer options, and has the device perform a factory data reset
  before the persistent unlock flag is set. Both verifiers agree.
- Gotchas/5: PASS — two `google,wdt` nodes in the decompiled `lga-b0.dtb`, and the Makefile's
  `fastboot oem watchdog disable` on frankel and blazer before booting a development kernel. Both
  verifiers agree.
- Gotchas/6: PASS — the v4 cover letter states that Tensor G1–G4, found in Pixel 6 through Pixel 9
  and the Pixel 10a, were Samsung Exynos offshoots whereas Laguna is an entirely in-house Google
  design.
- variants/Google Pixel 10 Pro: FAIL — display, cameras, the `.dts` claim and the ids all check out
  (blazer MP overlay entry 20 with the `gs-bzea` panel, a Samsung display PMIC and thirteen LWIS i2c
  devices against frankel's twelve; `lga-blazer.dts` differing from `lga-frankel.dts` only in model,
  first compatible and header comment; dtbo ids `0x070402`–`0x070406` with MP at `0x070406`, entry
  20). "RAM", however, appears nowhere in the v4 series or in either overlay, and the only store
  page in `resources.docs` is the base Pixel 10 one, which does not mention the Pro at all — so the
  row's named `source` does not establish it. Proposed correction: drop "RAM" from the `differs`
  line, or add the Google Store Pixel 10 Pro spec page to `resources.docs` and re-tag the row `doc`
  (or split the row's provenance).
- variants/Google Pixel 10 Pro XL: FAIL — same discrepancy, same proposed correction. The verified
  part: mustang MP overlay entry 30 carries the `gs-mtea` panel, a Samsung display PMIC and thirteen
  LWIS i2c devices; `lga-mustang.dts` differs from `lga-frankel.dts` only in model, first compatible
  and header comment; dtbo ids `0x070502`–`0x070506` with MP at `0x070506`, entry 30.
- variants/Google Pixel 10 Pro Fold: PASS — `gos/rango/lga-b0.dtb` is byte-identical to the muzel
  one (sha256 `f238c200…a030`); `gos/rango/dtbo.img` is a separate image (sha256 `8b8084ec…2de9`)
  with exactly 11 entries, ids `0x070602`–`0x070606`, every entry's root compatible
  `"google,lga-rango", "google,lga"`; no rango device tree appears in the v4 or v1 series. Recorded:
  "foldable" rests on the product name rather than on the DT, which is a naming convention rather
  than a factual error.

## Process notes

Not verdicts; they concern the spec's frontmatter and this run's mechanics.

1. **A `resources.docs` fetch annotation looks wrong.** The pixelscripts README and Makefile were
   readable only through GitLab API copies. Two cached raw-URL fetches of the README are GitLab 404
   pages, so the entry for `.../-/raw/clo/main/README.md` carrying `fetch: ok` is questionable —
   the raw-URL form did not work for whoever populated the cache. Worth re-checking before the next
   run.
2. **Three citations are not locatable from the spec alone** — the 9to5Google modem report
   (Quick-facts/1), and in the composed SoC spec a similar pattern. Adding them to `resources.docs`
   would make the `[press]` and `[doc]` tags resolvable.
3. **Leak scan.** The verifiers scanned their own drafts: the full verifier against the decompiled
   `lga-b0.dts`, six dtbo entry `.dts` files, the pixelscripts Makefile and README, the v4 and v1
   `google/` dts directories and the frankel insmod config — 0 shared runs, 0 ALL-CAPS, one
   lowercase identifier (`LinaroLtd`, a path segment of the public pixelscripts URL the spec's own
   frontmatter already publishes); the second verifier's independent scan likewise, its three
   lowercase hits being a device-tree node label, a tty name and a hardware-identification field.
   The orchestrator then scanned **this record** against the cache's `linux/`, `lore/` and the
   verifier scratch trees: `FINDINGS - review required`, 1 shared run and 4 high-signal
   identifiers. Reviewed one by one and cleared, all of them device-tree content the format
   explicitly admits as `[DT]` hardware description:
   - the shared run (record L113) is the emulator overlay's `model` string and its `compatible`
     pair, quoted from a decompiled dtbo entry — the very evidence the Quick-facts/6 FAIL rests on
     and what its proposed correction asks the spec to name;
   - `board_id` and `board_rev` are device-tree property names;
   - `lsion_cli16_uart` is a device-tree node label, and the composed SoC record carries the other
     twenty-one as the `instances/<name>` keys this format mandates;
   - `ttyS0` is a tty name on the production command line.
   No driver or firmware source is reproduced. Nothing was rewritten to satisfy the scanner;
   the findings are recorded here as judged.
