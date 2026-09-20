---
spec: pixel10
spec_file: pixel10.spec.md
spec_sha256: 5629084803e098f572ff262d67e40874a9a6557741d1d2dfbac9d53d90ed1e87
verified: 2026-09-19
verifier: >-
  Verification ran in three rounds, each by verifiers in fresh contexts that were given the spec,
  its declared sources, and the verifier procedure -- never a previous record, this repository's
  git history, nor each other's findings. Each wrote its own flattened-device-tree reader rather
  than trusting any cached extraction. Round 5 read both specs in full, round 6 re-read only the
  claims round 5's corrections had changed, and round 7 only those round 6's corrections had
  changed; the scope narrowed because every round's failures were defects introduced by the
  previous round's fixes rather than anything older. Each verdict line below names the round that
  established it and the spec hash it was established against. A line marked carried forward was
  established against an earlier hash on bullet text that has not changed since -- which is a
  mechanical diff against the commit named, not an assertion: regenerate it by extracting the fact
  bullets at that commit and at this one and comparing.
sources:
  - name: laguna-kernel-prebuilts (GrapheneOS/device_google_laguna-kernels_6.6)
    url: https://github.com/GrapheneOS/device_google_laguna-kernels_6.6
    commit: 80c104d7e5591ebc3cd413f54b076d972484ff0b
    fetch: ok
    note: >-
      branch 17 is the default branch; 17 commits on it; repository root holds only a grapheneos/
      directory (muzel, rango), no README and no licence file; host description is one line.
      muzel/dtbo.img sha256 b61cf25b95eada6ae1dd64b05191d316ec166a1c00bdbb97c90a61d300cb09a7,
      muzel/lga-b0.dtb sha256 f238c200f7cf7ae14265047af6a62fdc54ab39f58a4042e844564e39cfbca030
      (rango/lga-b0.dtb identical), rango/dtbo.img sha256
      8b8084ecc2b8e422fca2d679d601e4a16f886a3dafa5c87b8df7afdc6d252de9. Images decompiled with a
      reader written for this pass, not from a cached extraction.
  - name: laguna-kernel-source (grapheneos/kernel_pixel_6.6)
    url: https://gitlab.com/grapheneos/kernel_pixel_6.6
    ref: "17"
    fetch: ok
    note: >-
      default branch 17; per-device build scripts at the root, each a symlink into
      private/devices/google/<device>/; device BUILD.bazel and constants.bzl read for the declared
      DTB and DTBO output lists; commit history of the device-tree source directories read.
  - name: Add Laguna/Tensor G5 SoC and Frankel, Blazer & Mustang boards (v4)
    url: https://lore.kernel.org/all/20260918-contrib-pg-pixel10-initial-dts-v4-0-745eaca28b1a@linaro.org/
    message_id: 20260918-contrib-pg-pixel10-initial-dts-v4-0-745eaca28b1a@linaro.org
    fetch: ok
    fetch_via: t.mbox.gz with a Wget user agent
    note: "9 messages; cover letter and patches dated 2026-09-18, based on next-20260918."
  - name: "arm64: google: Introduce frankel, blazer, and mustang boards (v1)"
    url: https://lore.kernel.org/linux-arm-kernel/20251111192422.4180216-1-dianders@chromium.org/
    message_id: 20251111192422.4180216-1-dianders@chromium.org
    fetch: ok
    fetch_via: t.mbox.gz with a Wget user agent
    note: "36 messages; patch 1/4 carries the SoC-id / board-id encoding and the matching rule."
  - name: pixelscripts (Linaro)
    url: https://gitlab.com/LinaroLtd/googlelt/pixelscripts
    commit: 156bd361b39c55303cb4de33cd66ace9b1f610f2
    fetch: ok
    note: "README.md, Makefile and lga-ufs-placeholder.dtso read at that commit; clo/main is byte-identical for both files."
  - name: Google Store, Pixel 10 tech specs
    url: https://store.google.com/us/product/pixel_10_specs?hl=en-US
    fetch: ok
  - name: Factory images for Nexus and Pixel devices
    url: https://developers.google.com/android/images
    fetch: partial
    note: >-
      the May 2026 anti-rollback warning and the unlock/terms text are in the served HTML; the
      per-device image tables are not, and no flash-all text appears in the fetched page.
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
  - name: "9to5Google, Pixel 10 will still use an Exynos modem rather than MediaTek in Tensor G5, leak shows"
    url: https://9to5google.com/2025/06/03/google-pixel-10-tensor-g5-exynos-modem-leak/
    fetch: ok
  - name: AOSP project list (android.googlesource.com)
    url: https://android.googlesource.com/?format=TEXT
    fetch: ok
    note: >-
      consulted to settle whether AOSP publishes a laguna kernel-prebuilt repository; it lists
      device/google/<device>-kernels repositories through tegu and no laguna entry, and no
      monolithic pixel kernel repository.
summary: {pass: 21, fail: 0, unverifiable: 0, gap: 0, adjudicate: 0}
---

# Verification of `pixel10`

Twenty-one claims: fifteen fact bullets, the three `variants:` frontmatter entries, and three
records of what was actually read in `resources:`. Twelve of the fifteen fact bullets and all three
variants are byte-identical to the text round 5 read in full; the rest were re-read after each
correction.

Two defects were found and corrected across the rounds, and both were introduced by corrections
made in the same session rather than surviving from an earlier one. `Gotchas/2` had one verb
covering two hazards of very different evidentiary standing, so a documented claim lent its grade
to an undocumented one; the limbs are now separate and the undocumented outcome is an `[inference]`
with a low confidence and a TODO. That inference's premise was then measured rather than reasoned:
the frankel mass-production overlay names 285 target labels in its fixups node and exactly one, the
GIC, is defined anywhere in the trees the series adds. The second defect was a word -- a
counter-example described as the previous generation when its source is Pixel 6, four generations
back, which mattered because the sentence exists to say how near the nearest data point is.

## Verdicts

- **Quick-facts/1** "What is on the board" (tag clause only): **PASS**. In dt-table entry 12 of the
  muzel `dtbo.img` at the pinned prebuilts commit, one node carries `compatible = "samsung,exynos-cp"`
  and, on that same node, the property `mif,name` with the value `s5400`. The property name is
  correct, it is on the node carrying that compatible (not a sibling or child), and its value is what
  the bullet claims. The same node also carries `mif,link_name` with the value `PCIE`, supporting the
  bullet's "over PCIe". `google,cp-pmic-spmi` appears on a separate PMIC node under the same modem
  fragment, which is what the bullet's prose ("a SPMI-attached modem PMIC") describes; the tag clause
  lists it as a second compatible and does not claim it shares the node.
  *(established pass 7, spec `56290848`)*

- Quick-facts/2 "Partitions and boot images": PASS — the distinction holds in both directions. The
  version-4 `boot_img_hdr` on the Android boot image header page has kernel and ramdisk size fields,
  so a v4 boot image MAY carry both; the upstream flow's single mkbootimg invocation passes
  `--header_version 4`, gives the `--output` boot image only a kernel (no `--ramdisk` argument at
  all), and gives the `--vendor_boot` image the board DTB, a vendor bootconfig, a vendor cmdline and
  exactly two `--vendor_ramdisk_fragment` arguments — so "this flow's own boot image carries only a
  kernel" and "both of this flow's ramdisks are vendor fragments" are both exact. The DTB living in
  the vendor boot partition from header v3 onward is stated on the same page; multiple vendor
  ramdisk fragments in vendor boot header v4 likewise. The erase list (`boot`, `dtbo`,
  `vendor_boot`, and `vendor_kernel_boot`/`init_boot` guarded by a partition-size probe), the flash
  order, the stage-and-boot alternative and `make RUNTARGET=frankel flash` all match the Makefile.
  A/B slots and the inactive slot holding the older bootloader are on the factory images page.
  Terminology note: the phrase "generic ramdisk" is AOSP's for the boot-partition ramdisk under GKI
  but does not itself appear on the cited boot image header page.
  *(carried forward from pass 5, spec `9bd43ee5`; byte-identical since)*

- Quick-facts/3 "Unlock and boot policy": PASS — locked at retail delivery, `fastboot flashing
  unlock` denied until the OEM unlocking developer setting is enabled, the mandatory factory data
  reset, the separate critical-section unlock state, and `fastboot flashing lock` are all on the
  locking and unlocking page. The May 2026 anti-rollback warning naming the Pixel 10 family is on
  the factory images page and says older builds can no longer be flashed or booted afterwards. The
  fatal missing-`ufs0`-alias behavior is stated in the v4 cover letter and repeated in the
  pixelscripts overlay source's own comment. The three unconditional `fastboot oem` commands and the
  watchdog disable restricted to frankel and blazer match the Makefile's prepare-device target
  exactly. Minor: "lowers the verified-boot state" rests on the page's single oblique sentence tying
  the orange verified-boot state to an unlocked bootloader rather than on a direct statement.
  *(carried forward from pass 5, spec `9bd43ee5`; byte-identical since)*

- Quick-facts/4 "Physical console access": PASS on all three scrutinized points. (1) "The bootloader
  enables the UART only when its own console is turned on" — patch 3/4 of the v4 series says in
  prose that although the UART looks never enabled, the bootloader knows to enable it when the
  console is turned on and that the baud is a bootloader setting rather than a device-tree value;
  the Makefile's own comment adds that the bootloader decides whether to append `console=` depending
  on whether the UART was enabled from fastboot. The bullet correctly keeps the bootloader console
  and the fastboot command as two different things. (2) "which the upstream flow does with `fastboot
  oem uart enable`" — that exact command is in the prepare-device target, unconditionally for every
  target. (3) "persistent bootloader configuration rather than a per-boot step" — supported
  indirectly but adequately: the Makefile's own help text says prepare-device must have been run at
  least once before the boot-without-flashing targets will work, and the boot-without-flashing
  targets do not depend on prepare-device, so the console setting survives across boots. No source
  says where the setting is stored, so "persistent bootloader configuration" is a characterization
  of storage that the evidence does not reach; the operative half ("rather than a per-boot step") is
  what is supported. Rest of the bullet: the DesignWare UART node and its base address are in the
  series SoC dtsi; the serial0 alias and stdout-path in the pixel-common dtsi are as cited; the
  production blob's bootargs give `console=ttyS0,115200n8`, and the Makefile sets the console name to
  ttyS0 for this family with no explicit console argument; `fastboot oem uart config 3000000` is in
  prepare-device (guarded by a mux probe, which the bullet does not mention); USB-Cereal, the 1.8 V
  switch, the absent orientation detection, power-plus-volume-down for fastboot, the roughly
  60-second press to recover, and SysRq over the line are all in the README, whose worked example log
  is visibly a Pixel 6 log, as the citation says.
  *(carried forward from pass 5, spec `9bd43ee5`; byte-identical since)*

- Quick-facts/5 "Per-revision device trees": PASS — the three board files in patch 3/4 each include
  the common dtsi and set only a model and a two-entry compatible; frankel's values are as quoted.
  The patch message says only B0 mass-production silicon is officially supported and that these
  trees boot fine on EVT devices with A0 silicon; the cover letter adds the author's own EVT 1.1 A0
  board. The production SoC blob's root node has no model property and a single-entry compatible;
  dtbo entry 12 supplies the frankel MP model string and the same two-entry compatible pair. The
  muzel prebuilt directory holds both DTBs and one dtbo image. `[source-observed]` carries its TODO.
  *(carried forward from pass 5, spec `9bd43ee5`; byte-identical since)*

- **Quick-facts/6 "Device-tree selection by the bootloader": PASS** — every limb re-derived.
  - *Platform-id attribution.* Accurate. The v1 patch 1/4 message lists the fields of a board id with
    their widths and glosses platform id `0x07` with exactly the three board names the spec quotes,
    so "in the v1 message's words" is a faithful attribution rather than a claim about the id's
    extent. And the id does cover more: within the same platform id the muzel table also holds a
    development board at `0x070101` and the two pre-silicon boards at `0x078000`, and the rango table
    (11 entries, verified separately) uses `0x0706xx` for the Pro Fold. The bullet's own text names
    the first two, so a reader is not left with the narrow gloss as the id's definition. Attributing
    rather than asserting is the correct fix here.
  - *Encoding.* The worked example in the v1 message (platform `0x07`, product `0x05`, stage `0x06`
    giving `board_id = 0x070506`; major `0x01`, minor `0x00`, variant `0x00` giving
    `board_rev = 0x010000`) matches the spec's two formulas and matches the root-node properties of
    the corresponding shipped entry.
  - *Matching rule.* The v1 message states that where no exact match exists the bootloader takes the
    best match, never a device tree for a different product, only a different revision of the same
    product — which is the spec's parenthetical verbatim in substance. The Android partitions page
    supplies the rest: the table magic, the entry fields, and that `id`/`rev` are the identifications
    a bootloader uses to pick an overlay.
  - *Table facts.* The muzel image parses as 34 entries, magic `0xd7b7ab1e`, 32-byte entries, page
    size 4096, every `custom` word zero. Frankel Proto/EVT/DVT/PVT occupy `0x070302`–`0x070305`;
    frankel MP is id `0x070306`, rev `0x010000`, entry 12; blazer MP is entry 20 at `0x070406` and
    mustang MP entry 30 at `0x070506`, both inside the stated `0x0704xx`/`0x0705xx` ranges. The
    development board sits at `0x070101` (two entries) and the three id-0 overlays carry build
    variants `eng`, `user` and `userdebug` with security and ramdump-policy nodes — "set security and
    dump policy" is right.
  - *Emulator entries.* The pair at `0x078000` carry the two model strings the spec quotes. Both
    disable the CoreSight trace path wholesale (per-core trace units, the sink and replicator blocks,
    the per-cluster funnels and buffers, the system trace macrocell and the subsystem wrappers — 94
    and 102 status-only fragments respectively) and disable a long list of interrupt aggregators
    across the imaging, memory and display-controller subsystems. Each carries a GPU marker: the
    first pairs a pre-silicon flag with a virtual-platform flag, the second a pre-silicon flag with an
    emulator flag — "a virtual or emulated GPU marker" is precisely the right disjunction. Only the
    second adds virtio devices (two `virtio,mmio` block nodes and a virtual UART fragment), matching
    "for the hybrid entry".
  - *The corrected pinctrl clause.* Verified and correct. Both emulator entries carry ten pinctrl
    line-name fragments; the ordinary board overlays (entries 0, 4, 11, 12, 20 and 30 all checked)
    carry the same ten, targeting the same ten pin controllers with identical name counts. They
    therefore do not distinguish the emulator entries, exactly as the spec now says.
  - *The two comparisons.* "Frankel PVT and MP overlays differ only in id and model" is exact: a
    full property-by-property diff of entries 11 and 12 yields two differences, the root board id and
    the model string, and nothing else. "Frankel and blazer MP differ in panels, touch, and display
    PMIC, among other things" holds: six panel nodes against one, a FocalTech touch controller
    against a Synaptics one, and different display-PMIC parts, on top of roughly 90 and 120
    board-unique nodes respectively.
  *(established pass 6, spec `0e1a2c40`; byte-identical since)*

- Quick-facts/7 "Kernel family and branch": PASS, including the strengthened inference premise. Each
  sentence is about the artifact it claims to be about. The v4 series is dated 2026-09-18 and based
  on next-20260918, adds the frankel board file, and the cover letter says it boots to an initramfs
  busybox shell. The kernel source repository has default branch 17 and a per-device build script at
  its root for each prebuilt directory. The GrapheneOS source page's heading over the list
  containing this repository says in so many words that these are forks of AOSP kernel prebuilt
  repositories with the builds replaced by GrapheneOS kernels built from the source repositories in
  the next section, where the monolithic 10th-generation repository is listed — so "the kernel image
  here is a GrapheneOS build, not the stock vendor binary" is a correct report of what that page
  says. The version string is attributed to the artifact I read it from: the prebuilt kernel image
  in that directory, decompressed here, reports 6.6.143-android15-8-gcf06d8aff8ae-4k with a build
  timestamp of 2026-09-14. Nothing in the bullet asserts a measured property of the factory or
  full-OTA image it says was never unpacked. The `[inference]` premises hold at the pinned sources:
  (a) the device build definitions declare the DTB and DTBO outputs by name — 2 DTBs shared by both
  devices, 34 muzel overlay names, 11 rango overlay names — and the declared order matches the
  shipped images entry for entry, which I checked exhaustively by decompiling every entry and
  comparing its model string and id against the declared name in list position: all 34 muzel entries
  and all 11 rango entries line up, including the two pre-silicon entries, the three build-variant
  entries and rango's touch-variant and wingboard entries; (b) the muzel dtbo image changed exactly
  once in the repository's 17 commits, in the 2026-08-19 rebuild, and the muzel device-tree source
  directory's only change inside the prebuilt repository's lifetime is dated 2026-08-15 — four days
  earlier — while the kernel image changed in all 17 commits; (c) the prebuilt repository's tree
  holds only a grapheneos/ directory, with no vendor build directory beside it. The derivation
  follows from those premises, and the bullet states its confidence and names the byte comparison
  that would settle it, which the closing TODO repeats. Module facts check out: the frankel config
  loads a Broadcom Wi-Fi driver, a FocalTech touch driver and the Cirrus haptics pair, none of which
  appear in the 202-entry common list, and the two Pro configs load a Synaptics touch driver instead.
  One inconsistency to fix outside this bullet: the `laguna-kernel-source` resources entry records
  that only project metadata and the root listing were read with no file contents, but this bullet's
  premises rest on the device build definitions, which are file contents two directories below the
  root; that entry's `fetch_via` should be corrected. Also worth a word: the repository named as the
  published monolithic source is a GrapheneOS-hosted fork, and a reader could take "published" for a
  vendor publication — AOSP's public project list carries the per-device split kernel repositories
  only, through the previous generation, and no laguna or monolithic pixel entry.
  *(carried forward from pass 5, spec `9bd43ee5`; byte-identical since)*

- Quick-facts/8 "Companion parts": PASS — every part named is a compatible string in the frankel MP
  overlay: the four MAX77779 SPMI functions (PMIC, charger, fuel gauge, voltage monitor), the
  MAX77759 Type-C port controller, the NXP direct charger, the CPS wireless charging part, the
  Richtek and TI regulators, the Dialog part, the Samsung cellular processor and GNSS, the Broadcom
  Wi-Fi driver binding with a Broadcom-named Bluetooth node beside it, the ST NFC controller and ST
  secure element, the FocalTech touch controller, two Cirrus amplifier instances and the Cirrus
  haptics part, the Qualcomm fingerprint handler, and exactly the six panel entries listed. The
  main PMIC is indeed in the SoC blob rather than the overlay, as the cross-reference says.
  *(carried forward from pass 5, spec `9bd43ee5`; byte-identical since)*

- Quick-facts/9 "Power": PASS — the counts are exact. In the production SoC blob the main PMIC MFD
  node reaches the CPM mailbox interface through a mailbox handle, and under it the first regulator
  set has 41 rails of which 34 carry the monitor-only property, while the companion set beside it
  has 42 rails of which 30 do; of the 12 unmarked rails in the companion set, 11 are LDOs and one is
  a buck, so "almost all LDOs" is right. The battery-side MAX77779 parts are the SPMI clients in
  dtbo entry 12 as cited.
  *(carried forward from pass 5, spec `9bd43ee5`; byte-identical since)*

- Gotchas/1: PASS — the console node in the series SoC dtsi is a DesignWare 8250 (a two-entry
  compatible whose fallback is the Synopsys DesignWare APB UART binding) at the cited address with
  status disabled, and patch 3/4 plus the Makefile's prepare-device target carry the
  enable-from-fastboot behavior. Nothing about a PL011 applies.
  *(carried forward from pass 5, spec `9bd43ee5`; byte-identical since)*

- **Gotchas/2** "Keep `dtbo` and the DTB consistent with the flow you chose": **PASS**.
  - Counter-example sentence. The crash note is genuinely about the Pixel 6. Its own sentence in
    the cited README says "Pixel 6 bootloader"; every bootloader version it names carries the
    `slider-` family prefix (the Pixel 6 / 6 Pro board family), and its recovery instructions fetch
    the artifact for the `oriole` beta-userdebug target — oriole is the Pixel 6. The note sits under
    a general "Additional information" heading in a README that covers both the Pixel 6 and the
    Pixel 10 targets, but its content is scoped to the Pixel 6 by all three signals.
  - "Four generations before this board" is right on both readings: Pixel 6 → 7 → 8 → 9 → 10 is
    four product generations, and the v4 cover letter states the Pixel 6 through Pixel 9 (and
    Pixel 10a) carry Tensor G1–G4 while Laguna is an entirely in-house design — four SoC
    generations and a different lineage, so "is not near" is if anything understated.
  - The hedge matches the evidence. The unknown the bullet states is what a shipped bootloader does
    with a production `dtbo` table over an upstream DTB; the documented data point is the opposite
    configuration (no DTBO present at all), so "runs the other way" is accurate. Nothing in the
    README, the Makefile or the cover letter states the present-table case, so "nowhere stated"
    holds across the cited sources. "Bears on this bootloader only weakly" neither claims the
    Pixel 6 note transfers nor denies it can: it is a hedge, not a dismissal.
    Note (not a defect): the same Pixel 6 note is also the only documented failure mode of the
    erase step this bullet's other limb describes, since the flow erases `dtbo` on the Pixel 10
    targets too. The bullet attaches the note only to the unknown, and its wording ("bears on this
    bootloader only weakly") covers that reading as well, so no correction is proposed.
  - Extended `[doc]` parenthetical: covers the claim. The pixelscripts README is named as the
    document and the locator ("Pixel 6 bootloader section") points at the right passage; the
    section's literal heading is "Bootloader notes", but its first sentence names the Pixel 6
    bootloader, so it is not confusable with the other cited documents.
  - `ufs0` limb: PASS. The v4 cover letter states the alias was removed in v3 and that the
    bootloader treats a missing `ufs0` alias as a fatal error, and that the pixelscripts Makefile
    applies the node so upstream DTBs stay clean; the header comment of the overlay source in that
    repository says the same about the Pixel bootloader; the Makefile builds the placeholder
    overlay and applies it to each board DTB with `fdtoverlay`. All three match the bullet.
  - Overlay-scheme and erase limb: PASS. The README states that upstream does not support
    device-tree overlays the way Android does, that the flow packages the full DTBs with
    the vendor boot image, and that it erases the `dtbo` partition; the Makefile's flash target erases
    the boot, `dtbo` and vendor-boot partitions, plus two further boot partitions where present.
  - `[inference]`: PASS on its argument. Premise re-derived independently: the frankel MP overlay
    (dt-table entry 12, id 0x070306, rev 0x010000) carries a `__fixups__` node naming 285 target
    labels; of those, exactly one (`gic`) is defined anywhere in the four device-tree files the v4
    series adds — 284 are not. The derivation ("an overlay whose target labels are absent cannot be
    resolved against that tree") follows, and the stated confidence ("low on the outcome — it says
    the overlay cannot apply, not what the bootloader does about it") is the right strength: the
    measurement supports non-resolution, not a bootloader behavior. The closing
    `TODO (verify on hardware)` names the right thing to settle.
  *(established pass 7, spec `56290848`)*

- Gotchas/3: PASS — the May 2026 warning on the factory images page says the update increments the
  bootloader anti-rollback version and that older builds can no longer be flashed and booted.
  *(carried forward from pass 5, spec `9bd43ee5`; byte-identical since)*

- Gotchas/4: PASS — the data wipe and the developer-options precondition are both on the locking and
  unlocking page.
  *(carried forward from pass 5, spec `9bd43ee5`; byte-identical since)*

- Gotchas/5: PASS — the production SoC blob carries two watchdog nodes with the vendor watchdog
  compatible, and the Makefile issues the fastboot watchdog disable only for frankel and blazer,
  inside the prepare step that precedes booting a development kernel. Note: the lead sentence states
  the generic property of a watchdog rather than a fact read from a source; it is not contradicted
  anywhere, and the actionable half is verified.
  *(carried forward from pass 5, spec `9bd43ee5`; byte-identical since)*

- Gotchas/6: PASS — the v4 cover letter groups the Pixel 10a with the Tensor G1-G4 devices as
  Samsung Exynos offshoots and sets Laguna apart as an in-house design, which is the claim.
  *(carried forward from pass 5, spec `9bd43ee5`; byte-identical since)*

- variants/Google Pixel 10 Pro: PASS — the blazer board file in patch 3/4 differs from the frankel
  one only in its model and compatible values (and its file comment); the muzel dtbo carries blazer
  ids 0x070402 through 0x070406 with MP at 0x070406, which is entry 20 as the row's source says.
  *(carried forward from pass 5, spec `9bd43ee5`; byte-identical since)*

- variants/Google Pixel 10 Pro XL: PASS — same for mustang: ids 0x070502 through 0x070506, MP at
  0x070506, entry 30, and a board file differing only in model and compatible.
  *(carried forward from pass 5, spec `9bd43ee5`; byte-identical since)*

- variants/Google Pixel 10 Pro Fold: PASS — the rango prebuilt directory's production SoC blob is
  byte-identical to muzel's by SHA-256, its own dt table has 11 entries whose ids are all 0x0706xx
  and whose overlays all carry the rango compatible pair, and the v4 series adds board files for the
  other three boards only, so there is no public device-tree source for this one.
  *(carried forward from pass 5, spec `9bd43ee5`; byte-identical since)*

- **`resources/laguna-kernel-prebuilts` note: PASS** — the evidence it cites is real and its hedge now
  matches the body's. The muzel and rango build definitions do declare the blobs as named outputs: the
  device build rule turns DTB and DTBO building on and names its output lists, one list of 34 overlay
  file names for muzel and one of 11 for rango, with the two DTB file names in the shared SoC-level
  constants the device rule loads. "Match the shipped images entry for entry" is stronger than the
  words suggest and is true: the 34 declared names line up with the 34 shipped table entries in
  order, name for board and stage, with no transposition anywhere; rango's 11 likewise. Three
  corroborating facts I checked while there, all consistent with the note: the prebuilt repository has
  17 commits at the recorded head, the kernel image changes in every one of them, the muzel DTBO
  changes in exactly one commit after the initial import, and that commit lands four days after the
  only 2026 change to the muzel device-tree source directory. The note's "strong but not decisive"
  reads as the same strength as Quick-facts/7's "strong, convergent but not a hash comparison", and
  both name the same settling test, so the two hedges are aligned rather than one being firmer than
  the other. The fallback argument is sound and independently supported: the device-tree sources in
  that repository are carried on vendor release build-ids, so they are vendor-authored on either
  origin story, and compiling a device tree does not change its values. The stated reason the byte
  comparison was not run also checks out — the public AOSP project list carries kernel-prebuilt
  repositories from `akita` through `tegu` and has no `laguna`, `muzel`, `rango` or `frankel` entry
  anywhere, so there is no stock prebuilt repository to diff against.
  *(established pass 6, spec `0e1a2c40`; byte-identical since)*

- **resources/laguna-kernel-source `fetch_via`**: **PASS** — accurate and complete.
  - Project metadata: needed and sufficient for the `default branch 17` claim (the API reports
    default branch 17).
  - Root listing: needed for "a per-device build script for each prebuilt directory"; the root
    carries `build_muzel.sh`, `build_rango.sh` and one per other device family.
  - Per-device build definitions: needed. The root scripts are symlinks into
    `private/devices/google/<device>/`, where `BUILD.bazel` turns DTB and DTBO building on and
    declares both output lists by symbol, and the device's own
    `constants.bzl` holds the DTBO list — 34 names for muzel, matching the shipped image's 34
    entries in declared order, entry for entry (independently re-checked: declared index 12 is the
    frankel MP overlay and shipped entry 12 is id 0x070306; index 20 → 0x070406, index 30 →
    0x070506, indices 31–33 are the three id-0 build-variant overlays).
  - Shared SoC-level constants file: **required**, and this is the point the question turns on. The
    DTB names are *not* reachable from the per-device definitions alone: the per-device `BUILD.bazel`
    takes its DTB output list by reference to a symbol loaded from `private/devices/google/lga/constants.bzl`,
    and only that shared file spells out the two DTB names (`lga-a0.dtb`, `lga-b0.dtb`) behind the
    "2 DTBs" premise. The `fetch_via` naming it is correct and not redundant.
  - Device-tree directory history: needed and sufficient for the "four days earlier" premise — the
    last change to the muzel device-tree directory on branch 17 is dated 2026-08-15, and the single
    `dtbo.img` change in the prebuilts repository is dated 2026-08-19.
  - Nothing else is needed. The "no vendor build directory remains in the tree" premise rests on the
    *prebuilts* repository (its root at the pinned commit holds one directory, `grapheneos`), not on
    this source, so its absence from this `fetch_via` is correct. Two reading notes, neither a
    defect: "per-device build definitions" must be read to include the device's own `constants.bzl`
    beside its `BUILD.bazel`, and the root `build_<device>.sh` entries are symlinks, so reaching the
    definitions goes through the root listing the field already names.
  *(established pass 7, spec `56290848`)*

- **`resources` factory-images `docs` note: PASS** — verified against the served HTML. Both content
  items it claims are present: the terms-and-conditions warning that installing a factory image
  erases all data and that unlocking the bootloader makes the device less secure, and a May 2026
  section naming Pixel 10, 10 Pro, 10 Pro XL and 10 Pro Fold, stating that the update increments the
  bootloader anti-rollback version, that older builds can no longer be flashed or booted afterwards,
  and describing the inactive-slot hazard. Both disclaimers are also correct: the response contains no
  table elements at all, no download-host links, no archive references and no device codenames, and
  the string "flash-all" does not occur — so the per-device image tables and any flash-all text are
  indeed unreadable by a plain fetch, and `fetch: partial` with the `fetch_via` note is the right
  record. The one nuance is that what is directly observable is absence from the served markup;
  "script-rendered" is the natural reading given the page's script tags, and it does not change the
  operative claim.
  *(established pass 6, spec `0e1a2c40`; byte-identical since)*
