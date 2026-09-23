---
kind: board
id: pixel10
name: "Google Pixel 10 (family: Pixel 10 Pro, Pixel 10 Pro XL; Pixel 10 Pro Fold as far as public facts reach)"
triggers: [pixel 10, google pixel 10, frankel, glbw0]
not_triggers: [pixel 10a]
aliases: [frankel]
parts: [tensor-g5]
cache: pixel10-v4-resources
variants:
  - name: Google Pixel 10 Pro
    triggers: [pixel 10 pro, blazer]
    shares: [soc, parts, boot, console]
    differs: "display, cameras; its own lga-blazer.dts that differs from lga-frankel.dts only in model and compatible; dtbo board ids 0x0704xx (MP = 0x070406)"
    tag: DT
    source: "series v4 patch 3/4; dtbo.img entry 20, laguna-kernel-prebuilts"
  - name: Google Pixel 10 Pro XL
    triggers: [pixel 10 pro xl, mustang]
    shares: [soc, parts, boot, console]
    differs: "display size, cameras; its own lga-mustang.dts that differs from lga-frankel.dts only in model and compatible; dtbo board ids 0x0705xx (MP = 0x070506)"
    tag: DT
    source: "series v4 patch 3/4; dtbo.img entry 30, laguna-kernel-prebuilts"
  - name: Google Pixel 10 Pro Fold
    triggers: [pixel 10 pro fold, rango]
    shares: [soc]
    differs: "foldable; no public device-tree source; a separate prebuilt directory (rango) with an identical lga-b0.dtb and its own dtbo.img (11 entries, ids 0x0706xx, compatible google,lga-rango)"
    tag: DT
    source: "dtbo.img and lga-b0.dtb under grapheneos/rango, laguna-kernel-prebuilts"
resources:
  repos:
    - name: linux-mainline
      url: https://github.com/torvalds/linux
      ref: master
      license: GPL-2.0-only
      verified: 2026-09-18
      fetch: ok
      fetch_via: raw
      files:
        - {path: arch/arm64/boot/dts/google/lga-frankel.dts, status: unmerged, note: "lands with the Laguna series"}
        - {path: arch/arm64/boot/dts/google/lga-pixel-common.dtsi, status: unmerged, note: "lands with the Laguna series"}
      note: >-
        The board device tree is the unmerged series listed in the tensor-g5 spec; at commit
        17e7b8eacf4cac800a4fc89a28729df72a2dabda mainline has no arch/arm64/boot/dts/google
        directory. Read for behavior only.
    - name: laguna-kernel-prebuilts
      url: https://github.com/GrapheneOS/device_google_laguna-kernels_6.6
      ref: "17"
      license: "unstated: the repository carries no licence file and its host reports none; prebuilt kernel binaries and device-tree blobs"
      verified: 2026-09-18
      fetch: ok
      fetch_via: raw
      files:
        - grapheneos/muzel/dtbo.img
        - grapheneos/muzel/lga-b0.dtb
        - grapheneos/muzel/Image.lz4
        - grapheneos/muzel/init.insmod.frankel.cfg
        - grapheneos/muzel/modules.load
        - grapheneos/rango/dtbo.img
      note: >-
        A third-party prebuilt repository for the Pixel 10 family maintained by GrapheneOS, commit
        80c104d7e5591ebc3cd413f54b076d972484ff0b: the production DTB, the dtbo table with the
        per-board overlays (muzel dtbo.img sha256
        b61cf25b95eada6ae1dd64b05191d316ec166a1c00bdbb97c90a61d300cb09a7, 34 entries), the
        kernel image, and the module lists. PROVENANCE: obtained from this repository, which carries
        no README or licence, and whose one-line host description states only what it holds and not
        where the builds came from; the GrapheneOS source page is what states that
        its kernel builds are GrapheneOS builds from kernel_pixel_6.6, replacing the AOSP prebuilts.
        The DTB and DTBO images are, on strong but not decisive evidence, outputs of that same
        build rather than copied-in vendor blobs -- they are declared by name in the muzel and rango
        build definitions and match the shipped images entry for entry; Quick-facts/7 carries the
        same conclusion as an [inference] with its premises and confidence. Either way they are
        compiled from vendor-authored device-tree sources and compiling a device tree does not
        change its values, so a [DT] value read from them is the vendor's regardless of which it is.
        Byte-identity with a stock vendor artifact was not checked here: AOSP publishes no laguna
        kernel-prebuilt repository, so the only stock artifact to compare against is the DTBO image
        inside Google's published Pixel 10 factory or full-OTA image, which this spec did not
        unpack. Values from it are tagged with this name.
    - name: laguna-kernel-source
      url: https://gitlab.com/grapheneos/kernel_pixel_6.6
      ref: "17"
      license: "see the repository"
      verified: 2026-09-18
      fetch: ok
      fetch_via: "project metadata, root listing, the per-device build definitions and the shared SoC-level constants file they load, and the device-tree directory history"
      note: >-
        The monolithic kernel source repository for 10th-generation Pixel devices, linked from
        the GrapheneOS source page as what the laguna prebuilts are built from. Its root carries
        a per-device build script for each prebuilt directory.
    - name: pixelscripts
      url: https://gitlab.com/LinaroLtd/googlelt/pixelscripts
      ref: clo/main
      license: "see the repository"
      verified: 2026-09-18
      fetch: ok
      fetch_via: raw
      files:
        - README.md
        - Makefile
        - lga-ufs-placeholder.dtso
      note: >-
        Linaro's build-and-flash scripts for upstream kernels on Pixel phones (frankel, blazer,
        mustang, oriole, raven), read at commit 156bd361b39c55303cb4de33cd66ace9b1f610f2: how the
        images are packed and flashed, the fastboot oem commands that turn the console on, and the
        ufs0 placeholder overlay the shipped bootloader needs.
  docs:
    - title: Google Store, Pixel 10 tech specs
      url: https://store.google.com/us/product/pixel_10_specs?hl=en-US
      access: public
      cite: true
      verified: 2026-09-18
      fetch: ok
      note: "SoC, security chip, memory, storage, radios, port; the model number GLBW0 on the 5G mmWave line"
    - title: Factory images for Nexus and Pixel devices (developers.google.com)
      url: https://developers.google.com/android/images
      access: public
      cite: true
      verified: 2026-09-18
      fetch: partial
      fetch_via: "curl; the per-device image tables are rendered by script and were not readable"
      note: "the unlock warning and the May 2026 Pixel 10 bootloader anti-rollback note; the per-device image tables, and any flash-all text, are script-rendered and were not readable"
    - title: Android bootloader locking and unlocking (source.android.com)
      url: https://source.android.com/docs/core/architecture/bootloader/locking_unlocking
      access: public
      cite: true
      verified: 2026-09-18
      fetch: ok
      note: "fastboot flashing unlock / lock, the OEM unlocking setting, the data wipe, bootconfig lock state"
    - title: Android boot image header (source.android.com)
      url: https://source.android.com/docs/core/architecture/bootloader/boot-image-header
      access: public
      cite: true
      verified: 2026-09-18
      fetch: ok
    - title: Android DTB and DTBO partitions (source.android.com)
      url: https://source.android.com/docs/core/architecture/dto/partitions
      access: public
      cite: true
      verified: 2026-09-18
      fetch: ok
    - title: pixelscripts README (Linaro)
      url: https://gitlab.com/LinaroLtd/googlelt/pixelscripts/-/raw/clo/main/README.md
      access: public
      cite: true
      verified: 2026-09-18
      fetch: ok
      note: "flashing an upstream kernel: boot and vendor_boot images, dtbo erased, the serial-console notes (written for the Pixel 6)"
    - title: pixelscripts Makefile (Linaro)
      url: https://gitlab.com/LinaroLtd/googlelt/pixelscripts/-/raw/clo/main/Makefile
      access: public
      cite: true
      verified: 2026-09-18
      fetch: ok
      note: "the prepare-device, flash, and run targets: the fastboot oem uart commands, the partitions erased and flashed, the earlycon passed"
    - title: "9to5Google, Pixel 10 will still use an Exynos modem rather than MediaTek in Tensor G5, leak shows"
      url: https://9to5google.com/2025/06/03/google-pixel-10-tensor-g5-exynos-modem-leak/
      access: public
      cite: false
      verified: 2026-09-18
      fetch: ok
      note: "a hands-on report of a Pixel 10 Pro prototype's baseband string, concluding the same Exynos 5400 modem as the Pixel 9 family; press, not a vendor statement"
    - title: GrapheneOS source page
      url: https://grapheneos.org/source
      access: public
      cite: true
      verified: 2026-09-18
      fetch: ok
      note: >-
        lists the laguna kernel prebuilt repository, and in the following section the kernel
        source repository those prebuilts are built from (kernel_pixel_6.6)
  tools: []
---

<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Google Pixel 10

## Orientation

The Pixel 10 (board codename `frankel`, model GLBW0 in the US) is a handset built on the
**Google Tensor G5** (see the `tensor-g5` spec) with a Titan M2 security coprocessor, 12 GB of
RAM, 128 or 256 GB of UFS storage, a Samsung Exynos modem on PCIe, Wi-Fi 6E, and a USB-C 3.2
port that also carries the debug UART. The Pixel 10 Pro (`blazer`) and Pro XL (`mustang`) share
the SoC, the boot chain, and the console and differ in size, display, and cameras; the
Pro Fold (`rango`) shares the SoC and the production SoC blob and has no public device-tree
source. Everything an early bring-up can reach is on the SoC: the debug UART, the GIC, and the
timers; every clock, reset, and regulator is a firmware mailbox request. The bootloader is closed
and locked by default, the kernel source for this generation is published as a single monolithic
repository, and the only public device trees are the unmerged mainline series and the production
blobs in a separate prebuilt repository maintained by a third party, whose blobs are that
project's own build outputs from vendor-authored device-tree sources.
The SoC spec carries the addressing model, hand-off facts, GIC, UART, and timers; this spec
carries what the handset decides on top: partitions and images, unlock policy, console access,
the per-board device-tree selection, and the companion parts.

## Quick-facts

- **What is on the board.** Google Tensor G5 SoC; Titan M2 security coprocessor; 12 GB RAM;
  128 GB or 256 GB storage; 5G sub-6 and (model GLBW0) mmWave; Wi-Fi 6E 2×2; USB Type-C 3.2.
  The production device tree names the modem as a Samsung Exynos cellular processor over PCIe
  with a SPMI-attached modem PMIC, and names the part `s5400` in the modem node itself; press
  reports the same part as an Exynos 5400, the same as the Pixel 9 family. `[doc]` (Google Store, Pixel 10 tech specs), `[DT]` (`dtbo.img` entry 12,
  laguna-kernel-prebuilts: `samsung,exynos-cp` and `google,cp-pmic-spmi`, and the `mif,name`
  property on the modem node that carries `s5400`), `[press]` (a
  9to5Google report of a prototype's baseband string, in `docs`). `TODO (verify on hardware)`: the
  modem part number.
- **Partitions and boot images.** Android boot-image layout: the `boot` partition carries a v4
  boot image, which may hold a kernel and a generic ramdisk though this flow's own boot image
  carries only a kernel; the `vendor_boot` partition carries the DTB, the vendor ramdisk fragments
  (both of this flow's ramdisks are vendor fragments), and bootconfig; production builds keep per-board overlays in a `dtbo`
  partition as a dt table the bootloader matches by entry id and revision. The upstream flow
  builds `vendor_boot.img` with `mkbootimg --header_version 4` around the whole board DTB and a
  vendor bootconfig, erases `boot`, `dtbo`, and `vendor_boot` (and `vendor_kernel_boot` and
  `init_boot` where present), flashes `vendor_boot.img` and `boot.img`, and can instead stage
  `vendor_boot.img` and `fastboot boot` the kernel without flashing; `make RUNTARGET=frankel
  flash` drives it. Slots are A/B (the May 2026 update notes an inactive slot holding the older
  bootloader). `[doc]` (Android boot image header page; Android DTB/DTBO partitions page;
  pixelscripts README and Makefile; factory images page)
- **Unlock and boot policy.** The bootloader is locked at delivery; unlocking needs the
  **OEM unlocking** developer setting and `fastboot flashing unlock`, wipes user data, and lowers
  the verified-boot state; critical partitions need a separate `unlock_critical`; `fastboot
  flashing lock` reverses it. Google publishes factory images for the Pixel 10, and the May 2026
  update raised the bootloader anti-rollback version, so a bootloader older than that no longer
  boots after it is applied. A missing `ufs0` alias in the DTB is a fatal error on shipped
  bootloaders. The upstream flow also runs `fastboot oem disable-verity`,
  `disable-verification` and `ramdump disable` on every target, and `fastboot oem watchdog
  disable` only on frankel and blazer. `[doc]` (Android locking and unlocking page; factory
  images page; series v4 cover letter; pixelscripts Makefile)
- **Physical console access.** The console is the SoC's DesignWare UART `serial@db62000`
  (see `tensor-g5`, instance `lsion_cli16_uart`). The documented connection uses the USB-C port
  and a "USB-Cereal" debug dongle set to 1.8 V to separate serial from USB data; it advises
  reversing the plug if serial is unavailable. These directions illustrate a Pixel 6, not a
  measured Pixel 10 setup. The bootloader enables the UART only when its own console is turned
  on. The upstream flow issues `fastboot oem uart enable` during device preparation. Whether
  the setting survives reboot or power loss is not established by the cited material and remains
  a bootloader-documentation or hardware-test question. The flow requests 3,000,000 baud with
  `fastboot oem uart config 3000000` only when the UART mux query does not report virtual
  selection. With virtual muxing this step preserves the user's existing baud setup. The
  production command line separately records 115200n8; the baud of a particular live unit
  remains untested. The flow describes the bootloader appending `console=`; the console tty is
  `ttyS0`. The documented workflow enters fastboot with power plus volume-down at power-on,
  describes a roughly 60 s hold of those buttons to recover a hung development kernel, and
  describes serial system-request (SysRq) behavior. These are instructions, not Pixel 10
  measurements. `[doc]`
  (pixelscripts README, whose cable notes are written for the Pixel 6, and Makefile; series v4
  patch 3/4 message), `[DT]` (`lga-pixel-common.dtsi`, series v4, `chosen` and `aliases`;
  `lga-b0.dtb`, laguna-kernel-prebuilts, `chosen`). `TODO (verify on hardware)`: the Pixel 10
  cable and the baud a given unit is left at.
- **Per-revision device trees.** Upstream ships one tree per board for B0 (mass-production)
  silicon: `lga-frankel.dts` (`model = "Frankel"`, `compatible = "google,lga-frankel",
  "google,lga"`), `lga-blazer.dts`, and `lga-mustang.dts`, all including `lga-pixel-common.dtsi`,
  and the same tree boots EVT devices with A0 silicon. Production: the SoC blob has no `model`
  and only `compatible = "google,lga"`; the board overlay supplies `model = "FRANKEL MP based on
  LGA"` and the same compatible pair. The prebuilt directory for these three boards is `muzel`,
  holding `lga-b0.dtb`, `lga-a0.dtb`, and one `dtbo.img`. `[DT]` (`lga-frankel.dts` and
  `lga-pixel-common.dtsi`, series v4), `[DT]` (`lga-b0.dtb` and `dtbo.img` entry 12,
  laguna-kernel-prebuilts), `[doc]` (series v4 cover letter), `[source-observed]` (prebuilt
  file names). `TODO (verify on hardware)`: which blob a shipped device selects.
- **Device-tree selection by the bootloader.** The bootloader reads the SoC id and the board id,
  takes the SoC DTB from the vendor boot image, picks the overlay from the `dtbo` dt table whose
  `id`/`rev` match (the closest revision of the same product when there is no exact match, never
  another product), and merges them. `board_id` = platform id `0x07` (in the v1 message's words the frankel/blazer/mustang
  family) `<< 16` | product id `<< 8` | stage (`0x02` Proto, `0x03` EVT, `0x04` DVT, `0x05`
  PVT, `0x06` MP); `board_rev` = major `<< 16` | minor `<< 8` | variant. The muzel `dtbo.img`
  has 34 entries (magic `0xd7b7ab1e`, 32-byte entries, page size 4096, all `custom` fields 0):
  frankel Proto/EVT/DVT/PVT at ids `0x070302`–`0x070305`, **frankel MP at id `0x070306`, rev
  `0x010000` (entry 12)**, blazer at `0x0704xx` (MP entry 20), mustang at `0x0705xx` (MP entry
  30), a "deepspace" development board at `0x070101`, a pair of pre-silicon emulator board
  overlays at `0x078000` (`EMULATOR board based on LGA` and `SoC Hybrid emulator board based on
  LGA`), which disable the CoreSight trace path and several interrupt aggregators and carry a
  virtual or emulated GPU marker and, for the hybrid entry, virtio devices (the full pinctrl
  line-name tables they also carry are in the ordinary board overlays too, so they do not
  distinguish these entries), and three id-0 build-variant overlays (`eng`, `user`, `userdebug`)
  that set security and dump policy. Frankel PVT and MP overlays differ only in id and model;
  frankel and blazer MP differ in panels, touch, and display PMIC, among other things. `[DT]`
  (`dtbo.img` entries 0–33, laguna-kernel-prebuilts), `[doc]` (series v1 patch 1/4 message, for
  the encoding and the matching rule; Android DTB/DTBO partitions page).
- **Kernel family and branch.** Public: the unmerged mainline series (v4, 2026-09-18, on
  next-20260918) adds `arch/arm64/boot/dts/google/lga-frankel.dts` and boots to an initramfs
  shell. Production: a 6.6-based Android kernel. Source for this generation is published as a
  monolithic repository (`kernel_pixel_6.6`, GitLab, default branch `17`, with a per-device build
  script for each prebuilt directory). The binaries read here come from the GrapheneOS-maintained
  prebuilt repository, which the GrapheneOS source page describes as a fork of the AOSP kernel
  prebuilt repository **with the builds replaced by GrapheneOS kernels built from
  `kernel_pixel_6.6`** — so the kernel image here is a GrapheneOS build, not the stock vendor
  binary. The DTB and DTBO images beside it are outputs of that same build rather than copied-in
  vendor blobs. `[inference]` (premises, all `[source-observed]` from the two repositories' trees,
  build definitions and commit histories: the muzel and rango build definitions declare those blobs
  as named outputs and their declared entry counts match the shipped images exactly — 34 muzel
  overlays, 11 rango, 2 DTBs, and the shipped entry order matches the declared order entry for
  entry; the one muzel `dtbo.img` change in 17 commits follows a device-tree source change four days
  earlier while the kernel image changed in all 17; and no vendor build directory remains in the
  tree. Derivation: a copied blob is neither a declared build output nor tracks the source tree's
  clock. Confidence: strong, convergent but not a hash comparison — a byte comparison against the
  DTBO image in Google's published factory image would settle it). The device-tree *content* is vendor-authored either way, and compiling a device
  tree does not change its values, so `[DT]` values read from these blobs are the vendor's.
  Byte-identity with a stock vendor artifact was not checked here: AOSP publishes no laguna
  kernel-prebuilt repository, so the only stock artifact to compare against is the DTBO image inside
  Google's published Pixel 10 factory or full-OTA image, which this spec did not unpack. The
  GrapheneOS prebuilt kernel image in that directory reports `6.6.143-android15-8-gcf06d8aff8ae-4k`
  (built 2026-09-14) and its module set is loaded per board from `init.insmod.frankel.cfg` (a
  Broadcom Wi-Fi driver, a Cirrus haptics driver, and a FocalTech touch driver on top of the
  common set; the Pro models load a Synaptics touch driver instead). `[DT]`
  (`lga-frankel.dts`, series v4), `[doc]` (series v4 cover letter; GrapheneOS source page),
  `[source-observed]` (the prebuilt image's version string, the module lists, the source
  repository's root listing and build definitions, and both repositories' commit histories).
  `TODO (verify on hardware)`: the version string of a shipped build, which settles the kernel
  image; the inferred origin of the DTB and DTBO is settled instead by unpacking Google's published
  factory or full-OTA image for this device and comparing the DTBO image byte for byte.
- **Companion parts.** From the frankel MP overlay: Maxim MAX77779 PMIC, charger, fuel gauge,
  and voltage monitor over SPMI; MAX77759 Type-C port controller; NXP PCA9468 direct charger;
  CPS4041 wireless charging; Richtek RT6160 and TI TPS628600 regulators; Dialog SLG51002;
  Samsung Exynos modem and GNSS; Broadcom Wi-Fi/Bluetooth; ST21NFC NFC with an ST54 secure
  element; a FocalTech touch controller; Cirrus CS35L43 amplifiers and CS40L27B haptics; a
  Qualcomm fingerprint sensor; and `google,gs-flea`/`fleb`/`km4`/`tk4b`/`tk4c`/`tg4c` display
  panel entries. The main PMIC (Renesas/Dialog DA9188) is an SoC-tree fact: see `tensor-g5`.
  `[DT]` (`dtbo.img` entry 12, laguna-kernel-prebuilts). `TODO (verify on hardware)`: which of
  the listed panels and parts a given unit carries.
- **Power.** The main PMIC is a DA9188 driven through the SoC's CPM mailbox with most of its rails
  marked monitor-only for the OS (34 of 41 in the `da9188` set; a companion `da9189` set of 42
  beside it has 30 marked, the unmarked ones almost all LDOs), and the battery-side parts are the
  MAX77779 family over SPMI (see
  `tensor-g5` for the controllers). `[DT]` (`lga-b0.dtb`, laguna-kernel-prebuilts, `da9188mfd`;
  `dtbo.img` entry 12 for the SPMI clients). `TODO (verify on hardware)`: the rails and which of
  them the OS may touch.

## Gotchas

- **The console is a DesignWare 8250, left disabled in the DT, and silent until
  `fastboot oem uart enable`.** A correct base address and a working driver print nothing until
  the bootloader has enabled the block; PL011 assumptions do not apply. `[DT]` (`lga.dtsi`,
  series v4, `serial@db62000`), `[doc]` (series v4 patch 3/4 message; pixelscripts Makefile)
- **Keep `dtbo` and the DTB consistent with the flow you chose.** Two separate hazards, and only
  one of them is documented. An upstream DTB without the `ufs0` alias is a fatal error in the
  bootloader, and the upstream flow patches the alias in. Separately, upstream trees do not use the
  Android overlay scheme, so the flow packages whole board DTBs into the vendor boot image and
  erases the `dtbo` partition rather than relying on the table. What a shipped bootloader actually
  does with a production `dtbo` table over an upstream DTB is nowhere stated; the nearest
  documented data point runs the other way and is not near: some Pixel 6 bootloader versions crash
  when no DTBO is present in flash, four generations before this board, so it bears on this
  bootloader only weakly. `[doc]` (series v4 cover letter and the pixelscripts overlay source
  comment, for the `ufs0` alias; pixelscripts README and Makefile, for the overlay incompatibility
  and the erase, and the README's Pixel 6 bootloader section for the DTBO-absent crash), `[inference]` (premise, `[source-observed]`: a production
  overlay's fixups reference labels an upstream tree does not define. Derivation: an overlay whose
  target labels are absent cannot be resolved against that tree. Confidence: low on the outcome --
  it says the overlay cannot apply, not what the bootloader does about it).
  `TODO (verify on hardware)`: what a shipped bootloader does with a production `dtbo` table over
  an upstream DTB.
- **Do not flash a pre-May-2026 bootloader after the May 2026 update**: the anti-rollback
  version was raised and the device will not boot the older one. `[doc]` (factory images page)
- **Unlocking wipes the phone** and is refused until OEM unlocking is enabled in developer
  options. `[doc]` (Android locking and unlocking page)
- **The watchdog bites a kernel that does not feed it.** The upstream flow disables it from
  fastboot on frankel and blazer before booting a development kernel. `[doc]` (pixelscripts
  Makefile), `[DT]` (`lga-b0.dtb`, laguna-kernel-prebuilts, `google,wdt` nodes)
- **"Pixel 10a" is not this board**: different SoC family, nothing here applies. `[doc]` (series
  v4 cover letter)
