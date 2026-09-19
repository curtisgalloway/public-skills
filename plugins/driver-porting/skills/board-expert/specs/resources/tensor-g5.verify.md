---
spec: tensor-g5
spec_file: tensor-g5.spec.md
spec_sha256: e9e1e8e25acd162960a0241135706c0e5d38ec762444298f94d20e48b6434183
verified: 2026-09-18
verifier: >-
  Claude Opus 5 (1M context) under Claude Code, orchestrating spec-verifier. Third and final pass,
  frozen: verdicts here are recorded as returned, and the corrections they propose were deliberately
  NOT applied, to end a correct-then-reverify cycle in which three successive corrections to the
  addressing bullet each introduced a new phrasing defect. Verdict lines say which pass and which
  spec hash established them; a line marked "carried forward" was established against an earlier
  hash on bullet text that has not changed since. The addressing claim is additionally backed by a
  hash-tied extraction artifact at resources/tensor-g5.addressing.txt, whose figures three
  independent readers reproduced.
sources:
  - name: linux-mainline
    url: https://github.com/torvalds/linux
    commit: 17e7b8eacf4cac800a4fc89a28729df72a2dabda
    fetch: partial
    fetch_via: "the four bindings and booting.rst only; drivers/ deliberately left closed"
  - name: laguna-kernel-prebuilts
    url: https://github.com/GrapheneOS/device_google_laguna-kernels_6.6
    commit: 80c104d7e5591ebc3cd413f54b076d972484ff0b
    fetch: ok
    fetch_via: "lga-b0.dtb sha256 f238c200f7cf7ae14265047af6a62fdc54ab39f58a4042e844564e39cfbca030, recomputed by three readers"
  - name: "Add Laguna/Tensor G5 SoC and Frankel, Blazer & Mustang boards (v4)"
    url: https://lore.kernel.org/all/20260918-contrib-pg-pixel10-initial-dts-v4-0-745eaca28b1a@linaro.org/
    fetch: ok
  - name: "arm64: google: Introduce frankel, blazer, and mustang boards (v1)"
    url: https://lore.kernel.org/linux-arm-kernel/20251111192422.4180216-1-dianders@chromium.org/
    fetch: ok
  - name: Linux arm64 booting.rst
    url: https://www.kernel.org/doc/Documentation/arch/arm64/booting.rst
    fetch: ok
  - name: GrapheneOS build documentation
    url: https://grapheneos.org/build
    fetch: ok
  - name: Android boot image header
    url: https://source.android.com/docs/core/architecture/bootloader/boot-image-header
    fetch: ok
  - name: Android DTB and DTBO partitions
    url: https://source.android.com/docs/core/architecture/dto/partitions
    fetch: ok
  - name: Android bootloader locking and unlocking
    url: https://source.android.com/docs/core/architecture/bootloader/locking_unlocking
    fetch: ok
  - name: pixelscripts Makefile (Linaro)
    url: https://gitlab.com/LinaroLtd/googlelt/pixelscripts/-/raw/clo/main/Makefile
    fetch: ok
  - name: Build Pixel kernels (source.android.com)
    url: https://source.android.com/docs/setup/build/building-pixel-kernels
    fetch: ok
  - name: android.googlesource.com project list
    url: https://android.googlesource.com/
    fetch: ok
  - name: GrapheneOS source page
    url: https://grapheneos.org/source
    fetch: ok
  - name: Synopsys DesignWare ABP UART devicetree binding (snps-dw-apb-uart)
    url: https://www.kernel.org/doc/Documentation/devicetree/bindings/serial/snps-dw-apb-uart.yaml
    fetch: ok
  - name: "Google Tensor Series G5 (Laguna) DWC3 USB SoC Controller binding (google,lga-dwc3)"
    url: https://raw.githubusercontent.com/torvalds/linux/master/Documentation/devicetree/bindings/usb/google,lga-dwc3.yaml
    fetch: ok
  - name: "Google Tensor G5 USB PHY binding (google,lga-usb-phy)"
    url: https://raw.githubusercontent.com/torvalds/linux/17e7b8eacf4cac800a4fc89a28729df72a2dabda/Documentation/devicetree/bindings/phy/google,lga-usb-phy.yaml
    fetch: ok
  - name: "Arm architecture documents (IHI 0069, IHI 0070, DEN 0022, DDI 0487)"
    url: https://developer.arm.com/documentation/
    fetch: blocked
summary: {pass: 45, fail: 1, unverifiable: 0, gap: 0, adjudicate: 0}
---

# Verification of `tensor-g5`

Three passes over 46 claims. The first found five defects; the second, after corrections, found two
failures and one adjudication item; this third re-verified the corrected bullets and closed the
adjudication. One failure stands, recorded rather than fixed.

- Quick-facts/1 "Addressing model": FAIL — pass 3 micro-check at `e9e1e8e2`, the current hash.
  **Third consecutive pass to fail this bullet, each time on a different node class, each time in a
  clause meant to be exhaustive.**
  Not in dispute, and not re-derived this pass: the counted quantities, reproduced independently by
  three readers and by the extraction artifact — 2774 nodes, 20 declaring `ranges`, 10 `simple-bus`
  of which 8 translate, the eight wrappers and their cell counts (five with one address cell, three
  with two, all one size cell), 40 `reg`-bearing descendants split 19 MMIO / 21 graph, both `pcie@*`
  identity once the three-cell PCI `phys.hi` tag is separated, `simple_usb_bus` and `odm` empty
  identity, the series GIC declaring no `ranges` against the blob's empty one, and the display
  controller's `0x20_0000` → `0x0EE0_0000`. A whole-tree closure check establishes the 40 are the
  complete set: 645 nodes carry `reg`, exactly 40 sit under a non-empty-`ranges` ancestor.
  Verified this pass: the narrowed direct-child list is true as stated — debug UART, GIC, all 90
  aggregators (zero below the root) and all 7 SMMUs (zero below the root) are direct children of `/`
  with a 2/2-cell `reg`. The added sentence is true for what it names — `simple_usb_bus` and its
  `usb3@c450000` child both carry a zero-length `ranges`, and `/reserved-memory` likewise, so the
  USB pair and all 40 reserved-memory regions resolve untranslated.
  **The defect.** `0x200C_0504`, cited in Quick-facts/3, lives at `/ehld-coreinstr/coreinstr_base` —
  one level below the root, and in neither class the bullet describes. Its parent has **no `ranges`
  property at all**, not the empty identity `ranges;` the bullet gives as the reason a deeper node
  stays CPU-physical, and declares **one** address cell, so the window's `reg` is a single 32-bit
  cell rather than the 64-bit `reg` the bullet describes. The value itself is right, and the
  neighbouring watchdogs at `0x200C_4000`/`0x200C_5000` are root children corroborating it as a real
  CPU address — but a reader applying the bullet's rules lands nowhere. Its three siblings are in
  the same position; only this one's address appears in the spec.
  Proposed correction: keep the empty-identity explanation for the two containers and add the
  early-hardlockup detector as a third case — its register windows sit one level down under a parent
  declaring one address cell and no `ranges` at all, so their single-cell `reg` is CPU-physical
  because nothing maps it, a different reason from the identity pair.
  **Second defect, in the footnote added this pass.** "That property decodes sensibly only as two
  address cells plus one size cell" is refuted as a general statement: a sixth `alloc-ranges` in the
  same container, on `google_gem_dma_region`, is 4 cells long, cannot be divided under 2+1, and
  decodes cleanly as 2+2 to base `0x8000_0000` size `0x4000_0000`. The claim holds only of the five
  12-cell properties that establish the span. Related: "the span holds under either reading" is
  generous — the `0xA_0000_0000` top endpoint is derivable only under 2+1.
  Standing recommendation from three passes: this bullet keeps failing because it states universals
  over a blob with at least four distinct placement rules (root child; under an empty-identity
  container; under a translating wrapper; under a parent with no `ranges` and one address cell).
  Enumerating the rules would end the cycle; another "all X are Y" sentence probably will not.
- Quick-facts/2 "Boot chain and entry state": PASS — carried forward from pass 2 at `18100d5d`,
  bullet unchanged; two verifiers agreed.
  Recorded: `goog_bl31_mem_log_buff` establishes a node *name*; that BL31 means a TF-A-style EL3
  runtime is a conclusion from it, better tagged `[inference]` than `[DT]`.
- Quick-facts/3 "Silicon revisions and SoC id": PASS — pass 3 at `e77ae510`, bullet unchanged since.
  The corrected node names verified by a node-by-node, property-by-property diff of both blobs:
  `/soc_compatible` is root-level with exactly one child renamed `A0`→`B0` and `major` 0 versus 1
  while `product_id`, `minor` and `pkg_mode` are identical; the early-hardlockup detector is
  `/pmu-ehld` on A0 and `/ehld-coreinstr` on B0; `/hardlockup-watchdog` is separate and byte-
  identical in both. B0 does restructure it into `reg`-bearing children, add the `0x200C_0504`
  window of `0x24` bytes with no A0 counterpart, and add a clock input A0's node lacks. "No
  peripheral address, interrupt or clock differs" holds; the only other differing shared nodes are
  frequency-voting, DVFS-governor, energy-model and memory-frequency tables.
  Recorded, not failed: phandle numbering and the symbol table also shift as a consequence of the
  node-count change, which "differ only in" does not mention; and only 2 of the 8 chip-info children
  carry a revision-specific compatible, so the plural is right but broader than the evidence if read
  as "all of them".
- Quick-facts/4 "SMP topology": PASS — carried forward from pass 2 at `18100d5d`, bullet unchanged.
  Recorded: the blob's cpu compatible list begins `gem5,armv8` before `arm,armv8`, unmentioned.
- Quick-facts/5 "Interrupts": PASS — pass 3 at `e77ae510`, aggregator sentence verified by count:
  exactly 90 `google,level-gia` nodes, every one a direct child of `/`, every one a 16-byte window
  with one interrupt cell; the three low-speed-island aggregators decode to SPI 694 / 704 / 684.
  Recorded: a further 3 nodes carry `google,wide-level-gia`, so a substring match yields 93.
- Quick-facts/6 "Debug UART": PASS — carried forward from pass 2 at `18100d5d`, bullet unchanged;
  two verifiers agreed, and both the personality-offset and `earlycon` corrections verified there.
  Recorded by both: "configurable low-speed interface" appears in no consulted authority — an
  authorial gloss inside a `[DT]`-tagged bullet.
- Quick-facts/7 "Other UARTs": PASS — carried forward from pass 2 at `18100d5d`.
- Quick-facts/8 "Timers": PASS — carried forward from pass 2 at `18100d5d`.
- Quick-facts/9 "Clocks and power": PASS — carried forward from pass 2 at `18100d5d`.
  Recorded: "Renesas/Dialog" is a vendor gloss on the part number, not a DT string.
- Quick-facts/10 "GPIO and pinmux": PASS — carried forward from pass 2 at `18100d5d`.
  Recorded: the banks' own compatibles are `google,lga-*-pinctrl`; it is the CLI blocks that carry
  `pinctrl-single`, so "pinctrl-single-style banks" is a characterization, which the bullet's TODO
  already concedes.
- Quick-facts/11 "USB": PASS — carried forward from pass 2 at `18100d5d`. Read from the two mainline
  binding YAMLs with `linux/drivers/` deliberately left closed.
- Quick-facts/12 "UFS, PCIe, and the modem": PASS — carried forward from pass 2 at `18100d5d`.
- Quick-facts/13 "Security, IOMMU, and interconnect": PASS — carried forward from pass 2 at
  `18100d5d`.
  Recorded: IHI 0070 is the only Arm document cited with no matching `resources.docs` entry; it
  passes under the format's "the document id is the citation" rule for Arm documents.
- Quick-facts/14 "Reserved memory beyond the series": PASS — carried forward from pass 2 at
  `18100d5d`.
- Quick-facts/15 "DTB runtime patching": PASS — carried forward from pass 2 at `18100d5d`; two
  verifiers agreed.
- Gotchas/1 "Google publishes no kernel for this part": PASS — carried forward from pass 2 at
  `18100d5d`; the citation correction verified there.
- Gotchas/2: PASS — carried forward from pass 2 at `18100d5d`; both verifiers agreed.
- Gotchas/3: PASS — carried forward from pass 2 at `18100d5d`; both agreed.
- Gotchas/4: PASS — carried forward from pass 2 at `18100d5d`; both agreed.
- Gotchas/5: PASS — carried forward from pass 2 at `18100d5d`; both agreed.
  Recorded: "if the bootloader's console is off the line is silent whatever the kernel does" is one
  derivation step past what patch 3/4 states.
- Gotchas/6: PASS — carried forward from pass 2 at `18100d5d`; the citation correction verified.
- Gotchas/7: PASS — carried forward from pass 2 at `18100d5d`; both verifiers re-established the
  negative independently, one identifying the "All CPU(s) started at EL2" log as Pixel 6 material.
- Gotchas/8: PASS — carried forward from pass 2 at `18100d5d`; both agreed.
- Gotchas/9 "This is not the Pixel 10a's chip": PASS — pass 3 at `e77ae510`. The v4 cover letter has
  exactly one sentence on the earlier generation: it says the G1–G4 parts were offshoots of the
  Samsung family and parenthesizes the devices they are found in, the Pixel 10a last. The corrected
  bullet groups the 10a with that generation without saying which, tracking the sentence without
  going past it.
- instances/lsion_cli16_uart: PASS — carried forward from pass 2 at `18100d5d`; verified clause by
  clause by both verifiers there.
- instances/lsios_cli0_uart: PASS — carried forward from pass 2 at `18100d5d`.
- instances/lsios_cli1_uart: PASS — carried forward from pass 2 at `18100d5d`.
- instances/lsios_cli2_uart: PASS — carried forward from pass 2 at `18100d5d`.
- instances/lsios_cli3_uart: PASS — carried forward from pass 2 at `18100d5d`.
- instances/lsios_cli4_uart: PASS — carried forward from pass 2 at `18100d5d`.
- instances/lsios_cli5_uart: PASS — carried forward from pass 2 at `18100d5d`.
- instances/lsios_cli6_uart: PASS — carried forward from pass 2 at `18100d5d`.
- instances/lsioe_cli7_uart: PASS — carried forward from pass 2 at `18100d5d`.
- instances/lsioe_cli8_uart: PASS — carried forward from pass 2 at `18100d5d`.
- instances/lsioe_cli9_uart: PASS — carried forward from pass 2 at `18100d5d`.
- instances/lsioe_cli10_uart: PASS — carried forward from pass 2 at `18100d5d`.
- instances/lsioe_cli11_uart: PASS — carried forward from pass 2 at `18100d5d`.
- instances/lsioe_cli12_uart: PASS — carried forward from pass 2 at `18100d5d`.
- instances/lsioe_cli13_uart: PASS — carried forward from pass 2 at `18100d5d`.
- instances/lsioe_cli14_uart: PASS — carried forward from pass 2 at `18100d5d`.
- instances/lsion_cli15_uart: PASS — carried forward from pass 2 at `18100d5d`.
- instances/lsion_cli_int0_uart: PASS — carried forward from pass 2 at `18100d5d`.
- instances/lsion_cli_int1_uart: PASS — carried forward from pass 2 at `18100d5d`.
- instances/lsion_cli_int2_uart: PASS — carried forward from pass 2 at `18100d5d`.
- instances/lsion_cli_int3_uart: PASS — carried forward from pass 2 at `18100d5d`.
- instances/lsion_cli_int4_uart: PASS — carried forward from pass 2 at `18100d5d`.

## Frontmatter

Not a fact bullet. The `laguna-kernel-prebuilts` `note:` was verified this pass: the pinned commit
is the one every cached file was fetched at, both blob sha256s match recomputation, "identical
copies under rango" is true byte for byte, and the PROVENANCE sentence is supported — GrapheneOS's
build documentation tells a builder to clone its kernel tree, build for a codename and replace the
files at that repository path with the output, which is the statement that the kernel builds are its
own, while saying nothing about the accompanying blobs.
Recorded, not failed: the fourth device under muzel rests on a module-config file name in the
directory listing, while the build documentation maps only frankel, blazer and mustang to muzel.
The note now says the directory *carries a config for* deepspace rather than asserting the mapping.

## Process notes

1. **Why this record is frozen.** Three successive corrections to the addressing bullet each
   introduced a new defect, and each was caught by the next pass at the cost of a full cycle. The
   corrections proposed above are recorded for a person to apply and re-verify deliberately.
2. **The `instances/*` parent labels drop an `_intr` suffix** on all 21 extended rows, against
   `SPEC-FORMAT.md`'s "names that controller by its DT label". Recorded rather than failed in pass 2
   because each row's note gives the aggregator address unambiguously; flagged then as the likeliest
   thing a stricter reader would score differently, and still open.
3. **Three authorial glosses sit inside `[DT]`-tagged bullets** — "configurable low-speed
   interface", "pinctrl-single-style banks", "Renesas/Dialog". The `[inference]` class now exists
   for exactly this.
4. **A third class of non-address `reg`** exists that neither the bullet nor the artifact mentions:
   111 `nvmem-layout` cells whose `reg` is a byte/bit offset. None sits under a translating bus, so
   the 19/21 split is unaffected, but a reader classifying "is this `reg` an address" tree-wide
   would get different numbers.
5. **Leak scan: findings across passes, all reviewed and cleared.** This pass's readers returned
   clean (0/0/0) and, in one case, FINDINGS with four device-tree node names — `coreinstr_base`,
   `google_gem_dma_region`, `simple_usb_bus`, `sswrp_dpu` — shared with the decompiled trees, two of
   which the spec already names in the failing bullet. All are `[DT]` hardware description, which
   the format admits. Earlier passes' hits were node labels, `clock-names` values, a tty name and a
   vendor name. Nothing was rewritten to satisfy the scanner, and no driver or firmware source is
   reproduced.
