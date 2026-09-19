---
spec: pixel10
spec_file: pixel10.spec.md
spec_sha256: 23469e6bbd928019e80f365de573bb0d8e2f42f10fdc36a03a7dd1b044f13dbf
verified: 2026-09-19
verifier: >-
  Two independent verifier subagents (Claude Opus 5 under Claude Code), fourth pass, run
  concurrently in fresh contexts. Neither was given the previous record, this repository's git
  history, nor the other's findings. Pass A verified all 16 claims of the spec proper; pass B
  independently re-read the bring-up-critical facts SPEC-FORMAT requires two readers for, and
  additionally scored the three `variants:` frontmatter entries, which pass A did not. The two
  overlap on 11 claims and agree on all 11, so there is no adjudication item in this record. The
  passes were told that a correction which overshoots is as much a FAIL as the original defect.
  This pass exists because the third-pass record went stale: the two corrections it proposed were
  applied to the spec afterwards, which is the format's normal cycle.
sources:
  - name: linux-mainline
    url: https://github.com/torvalds/linux
    commit: 17e7b8eacf4cac800a4fc89a28729df72a2dabda
    fetch: ok
  - name: laguna-kernel-prebuilts
    url: https://github.com/GrapheneOS/device_google_laguna-kernels_6.6
    commit: 80c104d7e5591ebc3cd413f54b076d972484ff0b
    fetch: ok
  - name: laguna-kernel-source
    url: https://gitlab.com/grapheneos/kernel_pixel_6.6
    commit: e9d0c375485ebb49566c865472b1bfb813c5d9a0
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
  - name: Android bootloader locking and unlocking
    url: https://source.android.com/docs/core/architecture/bootloader/locking_unlocking
    fetch: ok
  - name: Android boot image header
    url: https://source.android.com/docs/core/architecture/bootloader/boot-image-header
    fetch: ok
  - name: Android DTB and DTBO partitions
    url: https://source.android.com/docs/core/architecture/dto/partitions
    fetch: ok
  - name: pixelscripts README
    url: https://gitlab.com/LinaroLtd/googlelt/pixelscripts/-/raw/clo/main/README.md
    fetch: ok
  - name: pixelscripts Makefile
    url: https://gitlab.com/LinaroLtd/googlelt/pixelscripts/-/raw/clo/main/Makefile
    fetch: ok
  - name: "9to5Google, Pixel 10 will still use an Exynos modem rather than MediaTek in Tensor G5, leak shows"
    url: https://9to5google.com/2025/06/03/google-pixel-10-tensor-g5-exynos-modem-leak/
    fetch: ok
  - name: GrapheneOS source page
    url: https://grapheneos.org/source
    fetch: ok
  - name: android.googlesource.com project list
    url: https://android.googlesource.com/
    fetch: ok
summary: {pass: 18, fail: 1, unverifiable: 0, gap: 0, adjudicate: 0}
---

# Verification of `pixel10`

Nineteen claims: the sixteen of the spec proper (Quick-facts/1-9, Gotchas/1-6, and the
`laguna-kernel-prebuilts` resource note) plus the three `variants:` frontmatter entries. Eleven were
read twice, by two verifiers who did not share a context; both readings agreed, so nothing here is
an adjudication item.

One FAIL, on `Quick-facts/7`, and it is a defect in a sentence rather than in a value: a pronoun
whose nearest antecedent is an artifact the same sentence says was never opened. The fact it states
is real and belongs to a different artifact. The correction is proposed below and **is not applied
here** -- applying it would stale this record again, and that is a decision for a person.

Pass B recorded three places where the spec is a shade more definite than its citations without
failing any of them, and pass A recorded three more. They are kept below because a note that a
claim is stronger than its evidence is worth having even when the claim is not wrong; none changed
a verdict.

## Pass A -- all sixteen claims of the spec

# Verification of `pixel10`

- resources/laguna-kernel-prebuilts note: PASS — every checkable element of the note holds at the
  recorded commit. The repository's tree at that commit resolves, and the commit is the head of the
  branch the entry names (17 commits total, the newest dated 2026-09-14). The muzel DTBO image
  hashes to the sha256 the note records and its table header declares 34 entries. The repository
  carries no README and no licence file, and its host reports no licence; its one-line host
  description names only the four Pixel 10 models whose kernel prebuilts it holds and says nothing
  about where the builds came from, exactly as the note states. The GrapheneOS source page carries
  the sentence the note attributes to it: a list of repositories it calls forks of AOSP kernel
  prebuilt repositories whose builds are replaced with GrapheneOS kernels built from the source
  repositories in the following section, with this repository and the 10th-generation monolithic
  kernel source repository each named in their respective lists. The declared-output premise holds:
  the two per-device build definitions in the kernel source repository switch on DTB and DTBO
  building and name their output lists, which contain 34 overlay file names for muzel, 11 for rango
  and 2 DTB names, matching the shipped images' entry counts, and the shipped entry order matches
  the declared name order one for one (not merely group for group). The limiting statement is also
  correct: the public Android source host's project list carries per-device kernel prebuilt
  repositories only up to the previous generation and has no laguna entry, so no stock prebuilt
  repository exists to compare against, and the note says plainly that byte-identity was not
  checked and names the factory/OTA DTBO image as the artifact that would settle it. One
  observation, not a defect: the note asserts the build-output conclusion flatly while the body
  bullet correctly labels the same conclusion an inference of strong but non-decisive confidence;
  the note earns this by giving its evidence inline and immediately stating what was not checked,
  but aligning the two wordings would remove the asymmetry.
- Quick-facts/1 "What is on the board": PASS — the vendor store page lists the SoC, the security
  coprocessor, 12 GB of RAM with 128 GB and 256 GB storage options, 5G mmWave plus sub-6 GHz with
  the model designator the spec quotes on the mmWave line, Wi-Fi 6E with 2x2 MIMO, and a USB
  Type-C 3.2 port — every figure as written. In the frankel mass-production overlay the modem node
  carries the Samsung cellular-processor compatible the spec names, its link type is recorded as
  PCIe, and a separate node carries the Google modem-PMIC-over-SPMI compatible, so the "over PCIe
  with a SPMI-attached modem PMIC" reading is supported by the blob itself. The press citation
  checks out: the linked article reports a hands-on Pixel 10 Pro unit whose baseband string begins
  with a 5400-family token and concludes the same Exynos 5400 modem as the Pixel 9 family, and it
  is a leak report rather than a vendor statement. Worth noting for a future revision, though it
  does not make the claim as written wrong: the modem node in the same overlay carries a name
  property whose value is that same 5400-family part token, so the part number is arguably a `[DT]`
  fact and not press-only.
- Quick-facts/2 "Partitions and boot images": PASS — the Android boot-image-header page states that
  from header version 3 onward the device tree blob lives in the vendor boot partition rather than
  the boot image, that version 4 vendor boot images support multiple vendor ramdisk fragments, and
  that a GKI boot image holds the kernel and the generic ramdisk only. The DTB/DTBO partitions page
  defines the dt table the bootloader matches per entry by id and revision. The upstream build
  recipe invokes the Android boot-image packer with header version 4, passing the assembled board
  DTB, the kernel, a vendor bootconfig file and two named vendor ramdisk fragments, and emits both
  boot and vendor_boot images — matching the spec sentence exactly. The device-preparation target
  erases boot, dtbo and vendor_boot unconditionally and erases vendor_kernel_boot and init_boot only
  when the partition probe succeeds ("where present" is right); the flash target then writes
  vendor_boot and boot, and a separate target stages vendor_boot and boots the kernel without
  flashing. The target-selection variable and the flash target named in the spec both exist. A/B
  slots and the inactive slot holding the older bootloader are stated verbatim in the factory-images
  page's May 2026 section.
- Quick-facts/3 "Unlock and boot policy": PASS — the Android locking/unlocking page says most
  devices ship locked and retail devices should ship locked, that the unlock command is refused
  unless the developer-options OEM unlocking toggle has been enabled, that unlocking triggers a
  factory data reset, that the lock command reverses it, and that critical sections have their own
  lock/unlock states which devices must not ship unlocked. The verified-boot coupling appears there
  too, in the form of the orange verified-boot state corresponding to the unlocked flash state. The
  factory-images page confirms Google publishes factory images for this device family and that the
  May 2026 update increments the bootloader anti-rollback version so older builds can no longer be
  flashed and booted. The fatal missing-`ufs0`-alias behavior is stated in the v4 cover letter and
  again in the placeholder overlay's own header comment. The upstream recipe's device-preparation
  target issues the verity-disable, verification-disable and ramdump-disable commands on every
  target and the watchdog-disable command only when the target is frankel or blazer, exactly as
  written.
- Quick-facts/4 "Physical console access": PASS — the series' SoC device tree defines the console
  node at the address the spec gives with the Google and Synopsys DesignWare UART compatibles, and
  the common board include sets the first serial alias to that node and points the standard output
  path at it. The production blob's chosen node carries a command line whose console parameter names
  the tty the spec gives at 115200n8, and it also enables SysRq unconditionally. The upstream recipe
  leaves the console parameter empty for this SoC (it is supplied only for the older Pixel
  generation) and its comment states that the bootloader adds the console parameter itself depending
  on whether the UART was enabled in fastboot and at what rate, and that this generation uses the
  ordinary ttyS0 name — both spec statements. The recipe issues the UART-enable command on every
  target and the rate-setting command with the 3 Mbaud value the spec quotes. The README describes
  the USB-C debug dongle by name, instructs selecting the 1.8 V setting, warns it has no orientation
  detection so the plug should be flipped when the console is silent, and says it splits the debug
  UART from the ADB/fastboot connection. It also gives the power-plus-volume-down entry to fastboot
  at power-on, the roughly 60-second long press to recover a crashed kernel, and a SysRq-over-serial
  reboot. The hedge that the cable notes were written for the Pixel 6 is well founded: those notes
  and their example photo were added in early 2024, when the repository covered only the older
  generation, and were not rewritten when Pixel 10 support landed in mid-2026.
- Quick-facts/5 "Per-revision device trees": PASS — the v4 series adds exactly three board files,
  each a fifteen-line file that includes the common board dtsi and sets only a model string and a
  two-entry compatible; the frankel one carries the model name and the compatible pair the spec
  quotes, and the other two differ from it in nothing but those two properties. The cover letter and
  the board patch both state that the upstream trees target mass-production B0 silicon and that they
  also boot EVT boards with A0 silicon. On the production side the SoC blob's root node has no model
  property at all and a single-entry compatible naming only the SoC, while the frankel
  mass-production overlay supplies the model string the spec quotes and the same two-entry
  compatible as upstream. The prebuilt directory for these three boards is named as the spec says
  and holds the B0 DTB, the A0 DTB and one DTBO image, and nothing else of that kind.
- Quick-facts/6 "Device-tree selection by the bootloader": PASS — the v1 binding patch's message
  gives the field widths and worked example the spec encodes: an 8-bit platform id of 0x07 for this
  three-board family, an 8-bit product id, a 4-bit stage, and major/minor/variant bytes, with the
  Pro XL mass-production board yielding board id 0x070506 and board rev 0x010000; the stage values
  the spec lists follow directly from the same patch's per-revision compatible table (0x02 Proto,
  0x03 EVT, 0x04 DVT, 0x05 PVT, 0x06 MP). The same message states the matching rule verbatim in
  substance: on no exact match the bootloader picks the best match but never a device tree for a
  different product, only different revisions of the same product. The DTBO partitions page supplies
  the table magic, the per-entry id/rev/custom fields and the selection procedure. Every counted
  fact about the shipped image holds: the header magic is the documented value, entries are 32 bytes,
  the page size field is 4096, the count is 34, and every entry's custom words are zero. The frankel
  ids run 0x070302 through 0x070305 for Proto/EVT/DVT/PVT, mass production is entry 12 at id
  0x070306 rev 0x010000, blazer occupies the 0x0704xx block with mass production at entry 20,
  mustang the 0x0705xx block with mass production at entry 30, the two development-board overlays
  sit at 0x070101, the two pre-silicon emulator overlays at 0x078000 carry the model strings the
  spec quotes, and entries 31 to 33 are the three id-zero build-variant overlays named eng, user and
  userdebug, each setting a small security property group and a bootloader dump-policy group.
  The frankel PVT and mass-production overlays differ in exactly two properties, the board id and
  the model string, as claimed. The frankel and blazer mass-production overlays differ in the panel
  compatibles, the touch-controller compatible and a display-PMIC compatible present only on blazer,
  among other things. The emulator overlays disable the CoreSight path (per-core trace units,
  funnels, buffers, the replicator, the system trace macrocell and the routers) and a long list of
  interrupt aggregator nodes, carry ten pinctrl nodes' full line-name tables, and mark the GPU node
  pre-silicon — the first as a virtual platform, the hybrid one as an emulator — with virtio devices
  present only in the hybrid entry.
- Quick-facts/7 "Kernel family and branch": FAIL — most of the bullet verifies. The v4 series is
  dated 2026-09-18, its base commit is the next tree of that date, it adds the frankel board file,
  and both the cover letter and the board patch say the result boots to a busybox initramfs shell.
  The monolithic kernel source repository exists at the host the spec names with default branch 17
  and carries a per-device build script at its root for each prebuilt directory. The GrapheneOS
  source page does describe this prebuilt repository as a fork of an AOSP kernel prebuilt repository
  with the builds replaced by its own kernels built from the 10th-generation monolithic source
  repository, so "a GrapheneOS build, not the stock vendor binary" follows. The inference carries
  what its class requires — named premises each classed, an explicit derivation, a stated confidence
  and a verification method — and every premise holds at the pinned commits: the build definitions
  declare the blobs as named outputs, the declared counts (34 muzel overlays, 11 rango, 2 DTBs)
  match the shipped images and the declared order matches the shipped order one for one; the muzel
  DTBO image changed exactly once in the repository's 17 commits, on 2026-08-19, four days after the
  only 2026 change to that device's device-tree sources on 2026-08-15, while the kernel image
  changed in all 17; and the prebuilt repository's tree contains a single top-level directory, the
  project's own, with no vendor build directory beside it. The conclusion follows from those
  premises at the confidence stated. The module claim also holds: the frankel module config loads a
  Broadcom Wi-Fi driver, a Cirrus haptics pair and a FocalTech touch driver after the common set,
  and the two Pro configs load a Synaptics touch driver in its place.
  The discrepancy is the sentence beginning "That image reports". Its nearest antecedent is "the
  DTBO image inside Google's published Pixel 10 factory or full-OTA image, which this spec did not
  unpack" — an artifact that cannot carry a kernel version string at all and that the same sentence
  says was never opened. The version string and build date the spec quotes are in fact the version
  banner of the compressed kernel image in the prebuilt repository's muzel directory: decompressed
  at the pinned commit it reports exactly the string the spec gives, with a build timestamp of
  2026-09-14, and that is also what the bullet's own `[source-observed]` tag ("the prebuilt image's
  version string") points at. As written the bullet asserts a measured property of an artifact it
  declares unexamined, and it puts the kernel-image evidence on the wrong side of the very
  distinction the rest of the bullet is built to keep. Proposed correction: give the sentence an
  explicit subject naming the prebuilt kernel image in the muzel directory instead of the pronoun —
  for example, "The prebuilt kernel image in that directory reports `6.6.143-android15-8-…-4k`
  (built 2026-09-14), and its module set is loaded per board from …" — leaving the preceding
  byte-identity caveat untouched, so the factory/OTA image remains named only as the comparison that
  was not made.
- Quick-facts/8 "Companion parts": PASS — every part named is present as a compatible string in the
  frankel mass-production overlay: the Maxim main battery-side PMIC with separate charger, fuel
  gauge and voltage-monitor functions all on SPMI, the Maxim Type-C port controller, the NXP direct
  charger, the CPS wireless-charging part, the Richtek and TI regulators, the Dialog regulator, the
  Samsung cellular-processor and GNSS nodes, a Broadcom wireless node plus a Broadcom Bluetooth
  node, the ST NFC controller with its ST secure-element SPI node, the FocalTech touch controller,
  the Cirrus amplifier and haptics parts, the Qualcomm fingerprint handler, and all six Google
  display-panel compatibles the spec lists. The deferral of the main PMIC to the SoC spec is
  consistent with where that node lives (the SoC blob, not the overlay).
- Quick-facts/9 "Power": PASS — the production SoC blob carries the multi-function device node the
  spec names, with regulator, RTC and two GPIO children, each reached through a mailbox handle and a
  destination-channel number, which supports the "driven through the SoC's mailbox" description; the
  SoC spec is where the mailbox controller itself is identified. The counts are exact: the first
  regulator set has 41 rails of which 34 carry the monitor-only marker, and the companion set beside
  it has 42 of which 30 do; of the 12 unmarked rails in that companion set, 11 are LDOs and one is a
  buck, so "almost all LDOs" is right. The battery-side Maxim family appears on SPMI in the
  mass-production overlay as stated.
- Gotchas/1 "The console is a DesignWare 8250, left disabled in the DT, and silent until `fastboot
  oem uart enable`": PASS — the series' SoC device tree gives the console node the Synopsys
  DesignWare APB UART compatible (a 16550-class block, not a PL011) and an explicitly disabled
  status; the v4 board patch's message says the UART only looks as if it is never enabled because
  the bootloader enables it when the console is turned on; and the upstream recipe issues the
  UART-enable fastboot command on every target before booting.
- Gotchas/2 "Keep `dtbo` and the DTB consistent with the flow you chose": PASS — the README states
  that because upstream does not support device-tree overlays the way Android does, the flow packs
  whole board DTBs into the vendor boot image and erases the dtbo partition, and the recipe does
  erase it. The missing-`ufs0`-alias failure is documented twice: the v4 cover letter calls it a
  fatal error in the bootloader pending a bootloader release, and the placeholder overlay's own
  header comment says the same; the recipe compiles that overlay and applies it to each board DTB,
  which is the "patches the alias in" step. One wording note: the cited documents establish the
  incompatibility and the erase, not the specific failure mode, so "a production `dtbo` table
  applied on top of an upstream DTB … fails in the bootloader" is a slightly sharper statement than
  the sources make; softening it to the documented form (upstream DTBs do not take Android-style
  production overlays, which is why the flow erases the partition) would make the bullet exactly as
  strong as its citations.
- Gotchas/3 "Do not flash a pre-May-2026 bootloader after the May 2026 update": PASS — the factory
  images page's warning for the May 2026 release names this device family, says the update
  increments the bootloader anti-rollback version to prevent rolling back to previously vulnerable
  bootloaders, and says older builds can no longer be flashed and booted afterwards.
- Gotchas/4 "Unlocking wipes the phone": PASS — the locking/unlocking page says the unlock command
  is denied unless the developer-options OEM unlocking toggle has set the unlock-ability flag, and
  that on acknowledgement the device performs a factory data reset before the persistent flag is set.
- Gotchas/5 "The watchdog bites a kernel that does not feed it": PASS — the production SoC blob
  carries two per-cluster watchdog nodes under the Google watchdog compatible (plus a separate
  hard-lockup watchdog), and the upstream recipe's device-preparation target issues the
  watchdog-disable fastboot command guarded by a target filter that admits only frankel and blazer,
  exactly the two boards the spec names.
- Gotchas/6 "'Pixel 10a' is not this board": PASS — the v4 cover letter groups the Pixel 10a with
  the Pixel 6 through Pixel 9 generation of SoCs, which it describes as offshoots of another vendor
  family, and contrasts that with this generation's entirely in-house SoC.

No source code reproduced; facts and mechanism only.

## Pass B -- independent second reading

The bring-up-critical facts, plus the three `variants:` rows.
# Verification of `pixel10` — independent second pass, bring-up-critical scope

## Verdicts

- Quick-facts/2 "Partitions and boot images": PASS — the boot-image header page gives a version-4
  boot header with both a kernel and a ramdisk field and states that the device tree moved to the
  vendor boot partition from header version 3 on, and that version 4 vendor boot images take several
  vendor ramdisk fragments; the DTB/DTBO partitions page gives the device-tree table header and the
  per-entry identification fields the bootloader matches on. The upstream flow in the pixelscripts
  Makefile at the pinned commit builds both images in one `mkbootimg` invocation at header version 4,
  passing the whole board device-tree blob and a vendor bootconfig file, erases the boot, dtbo and
  vendor boot partitions plus the vendor-kernel-boot and init-boot partitions when the device reports
  them, then flashes the vendor boot and boot images; a separate target stages the vendor boot image
  and boots the kernel without flashing. The cover letter gives the `RUNTARGET=frankel flash`
  invocation. The A/B slot claim matches the factory-images May 2026 warning, which describes the
  inactive slot holding the older bootloader and links seamless updates. Note, not a discrepancy: in
  this particular flow the built boot image carries only a kernel, both ramdisks being vendor ramdisk
  fragments in the vendor boot image; the bullet's "kernel plus generic ramdisk" describes the
  layout the header allows rather than what this flow emits.
- Quick-facts/3 "Unlock and boot policy": PASS — the locking page states that the unlock command is
  denied unless the unlock-ability flag is set, which the user sets through the OEM unlocking item in
  developer options; that the device performs a factory data reset on unlock; that the lock command
  reverses it; and that devices support locking and unlocking of critical sections as a separate
  state, with retail devices shipped locked and never shipped in the unlocked-critical state. The
  factory-images page carries the May 2026 warning for the Pixel 10, 10 Pro, 10 Pro XL and 10 Pro
  Fold: that update increments the bootloader anti-rollback version and older builds will no longer
  flash and boot. The fatal missing-alias behavior is stated in the v4 cover letter and repeated in
  the header of the placeholder overlay in the pixelscripts repository. The four fastboot oem
  commands and their targeting were read directly in the Makefile's device-preparation target:
  verity-disable, verification-disable and ramdump-disable unconditionally, watchdog-disable guarded
  on frankel and blazer only. Two wording notes: the spec says "critical partitions" where the page
  says critical sections and does not itself name the unlock-critical fastboot command; and "lowers
  the verified-boot state" is the weakest-supported phrase in the bullet — the page relates an
  unlocked bootloader to the orange verified-boot state only in passing, while the underlying fact is
  standard verified-boot behavior rather than something that page asserts.
- Quick-facts/4 "Physical console access": PASS — the series v4 device tree places the console at the
  node and label the bullet names, with a 256-byte window and the node left disabled; the common
  board include supplies the serial0 alias pointing at that label and a stdout path of serial0. The
  production blob's alias table points serial0 at the same controller and its command line selects
  the ttyS0 console at 115200n8, which is what the bullet says the production command line says. The
  pixelscripts README at the pinned commit describes the debug dongle by name, the 1.8 V selector,
  the absence of orientation detection with the instruction to flip if the console is dead, the split
  of the debug UART from the ADB/fastboot connection, entering fastboot by holding power and
  volume-down as the phone first turns on, the roughly sixty-second power and volume-down press to
  recover from a crashed development kernel, and rebooting over the line with a break-r SysRq; its
  cable photograph and worked example log are from the Pixel 6 generation, as the bullet says. The
  Makefile enables the UART and requests the 3 000 000 rate, and a comment there states the
  bootloader adds the console argument itself depending on whether the UART is enabled and at what
  rate. The console tty for these targets is ttyS0 in that same Makefile. The USB-C port is on the
  Google Store specification page under buttons and ports. Definiteness note for a person to settle:
  the bullet says the bootloader enables the UART "only after" that one fastboot command, while the
  patch 3/4 message says only that the bootloader enables the UART when its console is turned on, and
  the Makefile shows console state is persistent bootloader configuration (it also probes the current
  mux and skips the rate command when muxing is virtual). A more exact wording would be that the
  bootloader enables the UART only when its console is turned on, and that the upstream flow turns it
  on with that command; the operational instruction is unaffected.
- Quick-facts/5 "Per-revision device trees": PASS — patch 3/4 of the v4 series adds exactly three
  board files, one per board, each a fifteen-line file that includes the common Pixel dtsi and sets
  only a model and a two-entry compatible; the frankel file's model and compatible pair are exactly
  as quoted. The patch message states that only B0 silicon found in mass-production phones is
  supported and that these trees nevertheless boot on EVT devices with A0 silicon, which the cover
  letter repeats for a specific EVT 1.1 board. The production SoC blob's root node was parsed in this
  pass: it carries a single-entry compatible naming the SoC family and no model property at all, and
  the frankel mass-production overlay supplies both the quoted model string and the same two-entry
  compatible pair. The directory listing at the pinned commit shows one prebuilt directory for these
  boards holding both silicon-revision blobs and exactly one device-tree overlay image.
- Quick-facts/6 "Device-tree selection by the bootloader": PASS — the v1 patch 1/4 message states
  that the bootloader treats the SoC tree as the base and board revisions as overlays; gives the
  eight-bit platform, eight-bit product, four-bit stage, and eight-bit major/minor/variant fields with
  the worked Pixel 10 Pro XL mass-production example whose identifier and revision words are exactly
  the shifts the bullet states; and states the fallback rule that a non-exact match picks the closest
  revision of the same product and never another product. The DTB/DTBO partitions page supplies the
  table magic word, the header and entry layout, and the statement that the per-entry identification
  fields exist for the bootloader to select with; the boot-image header page supplies the SoC tree
  living in the vendor boot image. Every number in the bullet was re-derived from the table in this
  pass: the magic word, thirty-two-byte entries, a 4096-byte page size, thirty-four entries and all
  optional custom words zero; frankel proto through production at the four consecutive identifiers
  named, with the mass-production entry at the stated identifier and revision and at the stated entry
  index; the Pro family at its identifier block with its mass-production entry at the stated index;
  the Pro XL family likewise; a development-board identifier; a pair of pre-silicon emulator entries
  at the stated identifier, whose models name an emulator board and a SoC-hybrid emulator board; and
  three trailing zero-identifier entries whose variant properties are the three Android build
  variants and whose two child groups set security and dump policy. The emulator pair's content was
  checked too: both disable the whole CoreSight trace path (trace units, funnels, buffers, the
  replicator, the STM and the address-translation unit) and a long run of interrupt aggregators, both
  carry the same ten pin-line-name tables the shipping board overlays carry, the plain emulator marks
  its GPU fragment as a virtual platform and the hybrid marks its GPU fragment as an emulator and
  pre-silicon, and only the hybrid adds memory-mapped virtio block devices. Finally the two
  comparisons the bullet asserts were run as structural diffs: frankel production-validation versus
  mass-production differ in exactly two properties, the board identifier and the model string; and
  frankel versus Pro mass-production differ in the panel set, the touch controller and the
  display-side power-management part, along with camera and other differences.
- Gotchas/1 "The console is a DesignWare 8250, left disabled in the DT, and silent until `fastboot
  oem uart enable`": PASS — the series node's compatible pair is the Google-specific string falling
  back to the DesignWare APB UART string, with a 32-bit register stride, and the node's status is
  disabled; the patch 3/4 message explains that the bootloader enables it when the console is turned
  on; the Makefile issues the enable command. The same definiteness note as Quick-facts/4 applies to
  the word "until".
- Gotchas/2 "Keep `dtbo` and the DTB consistent with the flow you chose": PASS — the Makefile erases
  the dtbo partition in the device-preparation target and compiles and applies the alias placeholder
  overlay onto every board blob whose name begins with the SoC prefix; the cover letter and the
  overlay's own header state that the alias was removed upstream and that a shipped bootloader treats
  its absence as fatal.
- Gotchas/3 "Do not flash a pre-May-2026 bootloader after the May 2026 update": PASS — the
  factory-images warning names these devices, says the update increments the bootloader anti-rollback
  version, and says older builds will not flash and boot afterwards, with the inactive-slot
  unbootable-state failure described in detail.
- Gotchas/4 "Unlocking wipes the phone": PASS — the locking page requires a factory data reset before
  the persistent unlock flag may be set, and denies the unlock command until the OEM unlocking item is
  enabled in developer options; the factory-images terms text independently warns that installing a
  factory image erases all data.
- Gotchas/5 "The watchdog bites a kernel that does not feed it": PASS — the Makefile's watchdog-disable
  command is guarded to the frankel and blazer targets only, and the production SoC blob carries two
  watchdog nodes with the vendor watchdog compatible, as the tag clause claims.
- Gotchas/6 "'Pixel 10a' is not this board": PASS — the v4 cover letter groups the Pixel 10a with the
  Pixel 6 to Pixel 9 generation, whose SoCs it describes as offshoots of a different vendor's family,
  in explicit contrast to the in-house SoC this series adds.
- variants/Google Pixel 10 Pro: PASS — the v4 series adds a board file for this model that differs
  from the Pixel 10's only in its model string and its compatible pair (the file's copyright-header
  comment naturally names a different board, which is not device-tree content); the overlay table
  carries this product's five stage entries in the identifier block the row states, with the
  mass-production entry at the stated identifier and at the stated entry index; and the structural
  diff against the Pixel 10 mass-production overlay shows display and camera differences, as the row
  says. Sharing the SoC, parts, boot chain and console follows from the board file including the same
  common Pixel dtsi and from the composition naming the same SoC.
- variants/Google Pixel 10 Pro XL: PASS — same checks: a board file differing only in model and
  compatible; the stated identifier block with the mass-production entry at the stated identifier and
  entry index; a structural diff showing a different panel and camera complement.
- variants/Google Pixel 10 Pro Fold: PASS — this model has no board file in the v4 series, which adds
  only the other three, so "no public device-tree source" holds at that series. The separate prebuilt
  directory named in the row was fetched at the pinned commit: its SoC blob is byte-identical to the
  one under the other directory (same digest), and its overlay image parses to exactly eleven entries,
  every identifier in the block the row states and every overlay carrying the product compatible the
  row quotes.

## Scope notes (no verdict; not counted)

- **Addressing model.** This board spec carries no addressing-model bullet of its own; it defers to
  the SoC spec and names only one address, the console controller's, inside the console bullet and
  the first gotcha. That one address was re-derived in this pass from the series device tree: the
  root node and the peripheral bus both declare two address and two size cells, the bus carries an
  identity translation over the low 64 GiB, so the controller's register base is the CPU-physical
  address as written, and it agrees with the address in the production command line's early-console
  argument. Nothing in scope here is wrong; there is simply no board-level bullet to score.
- **Provenance caveat inherited.** Every value this pass drew from the production blobs and the
  overlay table comes from a third-party prebuilt repository, as the spec's own resource note says.
  This pass confirmed the artifacts are what that repository holds at the pinned commit; it did not
  and could not compare them against a vendor-published factory image, which the spec also says.
- **Not scored here** (left to the whole-spec pass): Quick-facts/1, /7, /8, /9.

No source code reproduced; facts and mechanism only.
