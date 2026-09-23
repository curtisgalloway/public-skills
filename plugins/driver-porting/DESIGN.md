<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Hardware specifications: from source investigation to measured quality

## Terms

- **Skill:** instructions in a `SKILL.md` file that tell an agent when and how to perform a task.
- **Plugin:** a themed package of skills and supporting files that a harness can install together.
- **Harness:** the application that runs the agent and supplies its tools and access controls.
- **Agent:** a model-driven worker that reads instructions, calls tools, and produces artifacts.
- **Subagent:** a separately prompted agent context assigned part of another agent's work.
- **Context:** the instructions, conversation, and tool results available to one agent session.
- **Orchestrator:** the agent coordinating questions, delegated work, checks, and artifact handoffs.
- **Spec:** a written description of hardware facts or a peripheral's programming requirements.
- **Board spec:** a reusable hardware map; the format also covers SoCs, companion chips, and IP.
- **SoC spec:** a board-spec file describing one system on a chip and its peripheral placements.
- **IP spec:** a board-spec file describing a reusable silicon block independently of its placement.
- **Chip spec:** a board-spec file for a companion chip, its connection, and the blocks it contains.
- **Driver spec:** a per-peripheral implementation document covering hardware and target-OS work.
- **Instance:** one placement of an IP block, with its address, interrupt, clocks, and local quirks.
- **Stub:** a thin board-name skill that selects a spec and delegates to the shared board reader.
- **Overlay:** a separate spec file that adds material to another spec by its identifier.
- **Root:** a directory marked by `board-specs.yaml`, beneath which board-spec files are discovered.
- **Layer:** a root's position in the ordered merge, from public material through local additions.
- **Frontmatter:** the YAML metadata between `---` lines at the beginning of a Markdown file.
- **Composition:** resolving a board's component specs and the IP specs its instances name.
- **Provenance:** the recorded origin of a fact or artifact and the evidence behind it.
- **Provenance tag:** a marker identifying a fact's support, such as a datasheet or observed code.
- **Anchor:** a citation to a repository-relative file, line range, and usually symbol at a pin.
- **Pin:** an exact source revision or document edition and hash used to make a reading repeatable.
- **RTL:** the hardware design in a description language such as Verilog; the `[rtl]` class.
- **Conflict entry:** a recorded disagreement between sources, kept beside the claim with its resolution.
- **Clean room:** a workflow separating source readers from implementers through checked reports.
- **Encumbered source:** source the workflow treats as unavailable for copying into the target.
- **Dirty side:** the contexts authorized to read encumbered driver or firmware source.
- **Clean side:** the contexts consuming cleared facts without reading that encumbered source.
- **Cache:** an out-of-tree store of reference sources and documents managed by the investigator.
- **Investigator:** the source-reading worker that extracts facts, evidence, and mechanism prose.
- **Verifier:** a fresh reader that independently checks the artifact under a named procedure.
- **Verification record:** a separate file of claim verdicts, source identities, and the spec hash.
- **Source:** a document, device tree, code revision, or observation used to support a claim.
- **Authority:** the evidence cited as establishing a claim, rather than just suggesting where to
  look.
- **Sidecar:** a separate supporting file stored alongside an artifact or in its evidence directory.
- **Provenance map:** the exact reference-file list used by clean-room verifiers and output scans.
- **Attestation:** a recorded declaration about procedure or review that a script cannot establish.
- **Claim:** a statement being checked; its unit varies between verification and evaluation.
- **Verdict:** a recorded decision such as `PASS`, `FAIL`, `UNVERIFIABLE`, `GAP`, or `ADJUDICATE`.
- **Candidate:** the generated driver spec being evaluated.
- **Ledger:** a structured list; here either an evaluation answer key or a clean-room event log.
- **Gold ledger:** the evaluation answer key, authored from sources without seeing any candidate.
- **Corpus:** the fixed collection of source code and documents from which the answer key is made.
- **Requirement:** an independently judgeable obligation or proposition represented in the ledger.
- **Facet:** a stable ledger category, such as registers, receive behavior, or interrupts.
- **Recall:** how much of the eligible answer key the candidate states sufficiently to implement.
- **Precision:** how many candidate claims meet the scoring policy's correctness rule.
- **Denominator:** the eligible rows or claims over which a reported fraction is calculated.
- **Recoverable:** derivable at all from the sources the candidate was given, whatever it omitted.
- **Weight:** a ledger requirement's consequence category, used to report recall separately.
- **Adjudication:** a person's recorded resolution of conflicting readings or provisional decisions.
- **Freeze:** fixing reviewed inputs and scoring rules before generating candidates for comparison.
- **Lock:** the file recording a freeze's date, content hashes, policy identity, and attestation.
- **Hash:** a content fingerprint, used here to detect changes rather than preserve missing files.
- **Gap:** a missing fact; a spec-gap is an implementer's filed question for the authoring workflow.
- **Fork:** an unanswered choice that changes the work, such as which peripheral instance to use.
- **Drift:** a change in a spec or source that may invalidate an earlier verification result.
- **Ablation:** a comparison with a component removed, here a run without the skill.
- **Fixture:** the equipment and configuration used to exercise and observe real hardware.
- **Acceptance:** a decision that stated conditions for using a spec or implementation are met.
- **Mutation:** a deliberate fault or change used to see whether a test detects it.

## The problem and the two walls

A vendor kernel can make a board work without explaining why. The address in a device-tree node may
require several bus translations before it is a CPU physical address. A reset sequence may mix
required ordering, a workaround for one silicon revision, and a delay chosen experimentally. A
shared driver may apply a workaround to an entire family even when an erratum names one part. An
engineer starting another OS needs to separate those facts before deciding what to implement.

An agent can turn this material into a convincing document while preserving the wrong meaning. It
may read a quirk table without following the control flow, mistake a driver's preference for a
hardware requirement, or attach a plausible citation to a statement the cited lines do not support.
It can also omit an entire recovery path. Checking only the claims it wrote cannot discover that
missing path. These are the concrete failure modes behind [the investigation
method](skills/os-investigator/SKILL.md) and [the evaluation plan](EVAL-PLAN.md).

There is a separate risk when the reference is GPL or otherwise encumbered relative to the target. A
document that reproduces source structure, invented identifiers, or implementation text may be
unusable as a clean-room input even when its register values are correct. The repository therefore
preserves evidence of who read what and what crossed into the implementation context. Its rules are
a workflow for handling that boundary, not a legal determination about a particular project.

**The licensing wall controls transfer.** `os-investigator` reads encumbered source in a separate
context and returns original descriptions of facts. `cleanroom-spec` adds a file-based handoff,
independent boundary review, scanning, and provenance records. Its verifier checks five things:
mechanical overlap, possible reproduction, hardware-derived organization, source-reading
attractants, and the usage notice. It deliberately does not determine technical accuracy.

**The accuracy problem controls belief.** `spec-verifier` asks whether each statement follows from
its cited authority. The evaluation adds the opposite question: which independently identified
requirements did the document leave out? A boundary `PASS` is not an accuracy `PASS`, and an
accuracy `PASS` is not evidence that the source-access boundary was enforced. Keep the results
separate.

Source that the target may derive from takes a different route:
[`anchored-peripheral-spec`](skills/anchored-peripheral-spec/SKILL.md) keeps direct code citations
and permits source reading. That route is deliberately unsuitable as a substitute for the clean-room
route on encumbered material. The skill tells an uncertain caller to use the clean-room route. This
document describes those repository rules, rather than deciding license compatibility.

## How the hardware map is organized

The [repository README](../../README.md) and [repository instructions](../../AGENTS.md) describe
skills as directories under `plugins/<theme>/skills/<name>/`. A skill contains instructions and may
include scripts or templates. Installing this plugin makes those instructions available to the
harness; it does not automatically install enforcement into a consuming OS project. Much of this
system is a procedure agents follow, with deterministic scripts checking selected properties.

There are two different kinds of specification. Board specs are reusable maps of hardware and its
references. Driver specs are implementation documents for one peripheral. A board map helps the
investigator find the right tree, instance, and datasheet; it is not a complete replacement for a
peripheral programming specification. The distinction is explicit in
[`SPEC-FORMAT.md`](skills/board-expert/SPEC-FORMAT.md).

### Separate identity, placement, and wiring

A `kind: board` file describes what is fitted and connected on a board. Its `parts` entries name SoC
and companion-chip specs. An SoC or chip's `instances` rows place reusable IP blocks at concrete
addresses with interrupts, clocks, and quirks. The IP spec describes the block's programming model
without assuming any particular SoC address. Several boards can share one SoC description, and
several SoCs can place the same IP description.

For example, [the Pi 4 board spec](skills/board-expert/specs/rpi4.spec.md) names `bcm2711` in
`parts`, lists repositories and documents, and records board console routing separately from the SoC
facts it references. [The Pi 4 stub](skills/rpi4-expert/SKILL.md) explains the next relation: that
SoC places the `pl011` IP as UART0. Its entire job is to select `spec: rpi4` and hand the question
to `board-expert` with `os-investigator`.

The other named entry points have the same shape: [`rpi-expert`](skills/rpi-expert/SKILL.md) selects
`rpi5`, [`indiedroid-nova-expert`](skills/indiedroid-nova-expert/SKILL.md) selects
`indiedroid-nova`, and [`pixel10-expert`](skills/pixel10-expert/SKILL.md) selects `pixel10`. Their
descriptions help the harness match a user's hardware name. Keeping facts out of these stubs avoids
maintaining another copy of the hardware map and another copy of the investigation procedure.

### Discover roots, compose, then overlay

`board-expert` collects roots from its own `specs/`, root pointers in loaded skills, the checkout's
`board-specs.yaml`, and the user's `~/.config/board-specs/board-specs.yaml`. Markers can point to
further roots. It does not search the filesystem for markers. Within known roots, `*.spec.md` files
supply the identifiers that resolve `parts`, `instances[].ip`, and overlay targets.

Resolution prefers an explicit spec identifier, then matches names through triggers and aliases.
Exclusion triggers prevent accidental matches to similarly named hardware. An IP question tied to a
board resolves through the matching instance and that board's kernel tree. A generic IP question
uses the IP spec and its sources and explicitly carries no instance facts. The word "anchored" in
this board-resolution mode means attached to a board, not necessarily a driver spec with `[src:]`
anchors.

Composition happens before overlays. Every component receives its own applicable overlays in the
order `public`, `ip-vendor`, `soc-vendor`, `product`, `local`. Later scalar values win, resource
lists combine with replacement by matching identity, and body sections append under headings that
name the contributing layer and root. Identity, kind, and component membership cannot be overridden.
The exact rules belong in [the format
contract](skills/board-expert/SPEC-FORMAT.md#roots-and-layers).

This is configuration precedence, not a way to prove a later factual claim correct. Appending a
vendor statement beside a public statement preserves their origins; it does not resolve a factual
contradiction. Internal resources identify a `via:` skill that knows how to access them. An expert
without that skill reports the resource unavailable rather than inventing access commands.

A public root cannot contain internal resource entries or references to private skills. Vendor and
local facts do not flow back into public specs. A publicly supported fact can be added on the
strength of its public citation. The [vendor guide](skills/board-expert/VENDOR-GUIDE.md) also makes
clear that a private report, test, or log retains its source restrictions. A layer is not, by
itself, a confidentiality control or permission to publish.

### Make the kind of evidence visible

The investigation tags distinguish `[databook]`, `[standard]`, `[DT]`, `[source-observed]`, and
`[inference]`. Board specs add `[rtl]`, `[doc]`, `[hardware]`, and `[press]`. These mean,
respectively, hardware documentation, a standard, device-tree values, observed software, a
reasoned conclusion, the hardware design itself, project or vendor documentation, a measurement,
and third-party reporting. The format specifies
where tags go and what accompanying citations and cautions they require.

The important distinction is between seeing a driver do something and establishing that hardware
requires it. Source-only ordering carries "order not known to be required"; source-only tuning
constants carry "re-derive on hardware". An inference states its premises, derivation, confidence,
and how to test it. Board facts tagged as source-observed, press, or inference also retain an
explicit hardware-verification TODO. A tag makes limited support visible; it does not strengthen it.
What each class is trusted for, and what that trust assumes, is the next section.

## Evidence model: what we trust and why

A tag says what kind of evidence supports a fact. It does not say why that kind deserves belief
or how it goes wrong. Leaving that implicit makes two mistakes easy: treating a working driver's
behavior as a hardware requirement, and letting whichever source was read last win a
disagreement. This section states the assumptions so they can be checked and argued with.

### Every class rests on an assumption

| Evidence | Trusted for | Assumes | Known failure modes |
| --- | --- | --- | --- |
| `[rtl]` | Digital register behavior: field layout, reset values, side effects, access types | The design matches the silicon revision and configuration parameters in use | Analog, electrical, and PHY behavior, firmware, and board wiring are not in it; the wrong revision's RTL misleads with full confidence |
| `[hardware]` | What this board did under stated conditions | The measurement method observes what it claims to | One board, revision, temperature, and firmware image; absence of an effect is weak evidence |
| `[databook]`, `[standard]` | Documented programming model and required behavior | The edition applies to the silicon revision | Errata, stale editions, silicon that does not follow its own document |
| `[DT]` | Placement: addresses, interrupts, clocks, and wiring for the image it came from | It is the description the bootloader actually selects | Overlays and bootloader changes; binding examples that are not production values |
| `[source-observed]` | What a working driver does | The driver works on this revision | Workarounds for other revisions, delays nobody measured, bugs the driver happens to survive |
| Independent drivers agreeing (Linux and a BSD, for example) | Raises confidence in a `[source-observed]` fact | They were written independently | One copied from the other, or both from the same vendor code: agreement then adds nothing |
| `[doc]` | What a vendor or project says about its own work | The author knew and the text is current | Marketing pages, docs for a different part or revision |
| `[press]`, forums, other low-confidence reports | A lead worth checking | None | Allowed only with `TODO (verify on hardware)`, as today |
| `[inference]` | A conclusion from tagged premises | The derivation is sound | Carries its own confidence; never stronger than its weakest premise |
| Model recall | Nothing | n/a | Not evidence and never tagged; a fact with no source is a gap |

Two rules follow from the table:

- **Confidence is scoped.** `[rtl]` for revision A says nothing certain about revision B0, and a
  `[hardware]` result on one board is a result for that board. The citation must carry the scope:
  the revision, board, image, or conditions.
- **Low-confidence evidence is allowed, labeled.** A forum post that names a register quirk is
  worth recording as a lead. The tag and its TODO keep it from reading as settled fact.

### Conflicts are recorded, never overwritten

The table is not a strict ranking. `[rtl]` outranks a databook for digital behavior, and a
`[hardware]` observation outranks a databook when an erratum exists, but a databook outranks a
single board's measurement taken under unusual conditions. So a conflict between classes is not
settled by editing the losing claim. It becomes a conflict entry beside the claim: both readings,
their evidence and scope, the resolution, and which assumption from the table justified it. The
losing reading stays visible, the way an erratum stays visible beside the datasheet it corrects.
An unresolved conflict is a gap.

`reference-driver-review` already applies one instance of this ("the reference is evidence, not
truth: the databook breaks ties"). The ENC28J60 corpus already separates `vendor_confirmed` errata
from `implementation_observed` workarounds. The general conflict entry is proposed, not shipped.

### The spec learns from debugging and testing

A spec is not finished when it is accepted. Implementation, debugging, and testing produce
evidence, and that evidence belongs in the spec rather than in a test log nobody rereads:

1. A test or debugging result becomes a `[hardware]` fact, citing the test, board, revision,
   image, and conditions.
2. It confirms, contradicts, or narrows an existing claim. A `[source-observed]` ordering marked
   "order not known to be required" can become required, or shown not to be. A source-only
   constant can be re-derived.
3. A contradiction produces a conflict entry, as above, not a silent edit.
4. Only claims that depend on the changed fact are re-verified; the rest of the verification record
   stands. A hash change today marks the whole record stale, which is correct but coarse.
5. An answered spec gap is folded in the same way, with the evidence that answered it.

The first place this loop runs is the ENC28J60 Linux rebuild (L01 in
[`IMPLEMENTATION-PLAN.md`](IMPLEMENTATION-PLAN.md)): its differential tests against the original
driver produce exactly these results. A settled `[hardware]` result closes a claim without a person
reviewing it, which is the scalable path. Humans are needed for conflicts the table's assumptions do
not resolve. Dependency-scoped re-verification is the deferred M16 work; until it exists, a changed
spec is re-verified whole.

### When there is no existing driver

Everything above is easier while a working driver exists: it supplies the facts, it is the
reference for differential tests, and it breaks ties. For new hardware with no driver anywhere,
`[source-observed]` disappears and all three jobs move elsewhere:

- **Facts** come from `[rtl]`, the databook, and the hardware designers.
- **The reference** becomes a simulation or emulation of the design (RTL simulation, an FPGA
  build, a behavioral model) and published conformance suites where they exist.
- **Ties** are broken by independent implementations from the same spec, whose disagreements
  expose ambiguity but not a misreading they share, and by questions to the designers.

In that setting the spec's gap list is the main product: a precise list of questions for the
people who designed the hardware, each tied to the claim it blocks. This mode is not designed or
tested yet; it is recorded here so the evidence model does not assume a reference driver.

## The pieces, grouped by role

### Investigation

A person asks a hardware question or requests a driver spec. The orchestrator delegates source
reading; an implementation context must not invoke these investigator roles to fill its own gaps.
[`QUESTIONS.md`](skills/board-expert/QUESTIONS.md) defines the shared intake protocol. Choices that
change the answer are asked together. A subagent returns a `Needs decision` block for the
orchestrator to ask, while continuing work independent of that choice. Missing facts become gaps.

[`os-investigator`](skills/os-investigator/SKILL.md) takes a hardware question, target identity, and
source revision, usually with a board expert's map. It produces tagged facts, original mechanism
prose, confidence limits, and pinned provenance. It refuses source excerpts, close structural
paraphrase, source-invented naming, and unmarked assumptions about ordering. Board research-fill and
`cleanroom-spec` consume its output; the verifier also loads its boundary rules.

[`board-expert`](skills/board-expert/SKILL.md) takes a question plus optional board and IP
identifiers. It composes specs, manages its reference cache, invokes resource skills, and uses
`os-investigator`'s method to answer. The report adds contributing roots, layers, overlays, source
commits, and verification status. It refuses to guess material identity choices or edit a spec
without being asked. With no spec, it reports best-effort findings and suggests scaffolding.

The four board stub skills are user-discoverable names for that same delegated role. They produce no
independent hardware database. `cleanroom-spec`, research-fill, and reference selection can invoke
the shared expert through a stub or directly. Source acquisition remains the expert's job, not a set
of source-reading commands performed by the clean-side orchestrator.

### Authoring

[`board-spec-scaffold`](skills/board-spec-scaffold/SKILL.md) is a person-invoked authoring workflow.
It takes identity, root, source, document, and coverage choices. It creates missing board, SoC,
chip, or IP files, and optionally a root marker, overlay, vendor-tool skill, or board stub. Its
[templates](skills/board-spec-scaffold/templates/) cover those artifacts. Public-source research
normally delegates to an investigator. The scaffold does not itself read driver bodies or answer
hardware questions; its final verification phase hands the files to `spec-verifier`.

[`cleanroom-spec`](skills/cleanroom-spec/SKILL.md) takes one peripheral, its board or generic IP
scope, reference provenance, and the target OS tree. It produces `docs/<device>-spec.md`, a source
map, boundary-scan evidence, and clean-room ledger entries. Its two
[templates](skills/cleanroom-spec/templates/) brief the spec author and boundary verifier. It
refuses to bring unverified draft text into the orchestrator context. `cleanroom-implementer`
consumes the landed document; `spec-verifier` supplies a separate accuracy pass.

The driver spec names the IP and canonical references, groups registers by hardware function, and
describes initialization, data or descriptor formats, interrupts, DMA/addressing, and sub-protocols.
Its target-OS half identifies existing drivers to reuse or model, interfaces, binding, packaging,
and implementation milestones. Confidence, unresolved details, and the usage notice tell the
implementer which statements are established and which still need investigation or hardware work.

[`anchored-peripheral-spec`](skills/anchored-peripheral-spec/SKILL.md) takes source the target may
derive from, source and target pins, and a peripheral scope. It produces a driver spec of the same
broad shape, but every source-derived claim points to performing statements or definitions. `[src:]`
addresses the reference tree, `[tgt:]` the target tree, and `[doc:]` a document section.
Implementers can read the code. The skill refuses the encumbered-source use case and fabricated
anchors; it does not load the clean-room investigation role for its source-reading workflow.

Its hardware statements distinguish documented requirements, comment explanations, driver choices,
and behavior that is merely implemented. It normally delegates slices of larger drivers before
drafting and independently derives register tables twice. Anchor and inventory checkers precede a
fresh accuracy reader. `spec-verifier` can later rerun that process and preserve per-anchor verdicts
outside the document.

[`reference-driver-review`](skills/reference-driver-review/SKILL.md) is a person-invoked comparison
workflow for an existing implementation. It takes two pinned trees, locating the reference through a
board expert or the user, and produces `docs/<driver>-review.md`. Findings have `[impl:]` and
`[ref:]` anchors, a consequence, and a verdict: bug, suspect, benign, or reference issue. The
databook can settle a divergence in either implementation's favor. This skill produces neither a new
implementation spec nor driver code. Its checkers and later verification reuse the anchored route;
it is not an alternative input channel for a clean-room implementer.

### Verification

[`spec-verifier`](skills/spec-verifier/SKILL.md) is an orchestration skill a person can invoke on
demand. Authoring workflows also point to it for verification or re-verification. It takes a spec or
review and its declared sources, runs mechanical checks, and delegates fresh readings. The verifiers
do not receive the author's reasoning or a previous verdict record. They propose fixes but never
edit the spec. The output is the external verification record and associated reports.

The independent second reading depends on the artifact: bring-up-critical addressing, boot, and
console facts for board specs; register tables for anchored specs; register maps and initialization
sequences for clean-room driver specs. Agreement is evidence of repeatability, not proof of truth.
The lifecycle below explains how failures and disagreements remain visible.

### Implementation

[`cleanroom-implementer`](skills/cleanroom-implementer/SKILL.md) supplies standing rules, install
material, access blocking, and auditing for a consuming project. Its inputs are a landed spec,
prefetched public references, and the target OS tree. Implementation work produces target code; gaps
produce `docs/spec-gaps/<device>.md`. The supplied hook and audit scripts produce logs and audit
reports. The role refuses encumbered-source access, provenance-sidecar reading, and delegated source
investigation. Gaps go back through the orchestrator and authoring workflow.

A separate context is insufficient access isolation: subagents can inherit environment and
permissions. The install guidance therefore separates investigator/verifier processes and
implementation launch settings. Environment restrictions are the strongest boundary; hooks,
permissions, restricted agents, and instructions add defense and evidence. The installation material
targets Antigravity, while the scripts describe harness-neutral event handling. Verify actual
enforcement in the consuming harness; installing the plugin alone does not establish it.

### Evaluation

Evaluation is a collection of files and procedures, not another shipped spec-authoring skill.
[`EVAL-PLAN.md`](EVAL-PLAN.md) defines the comparison, and
[`evals/enc28j60/`](evals/enc28j60/README.md) holds the pilot inputs, answer key, rules, and
checkers. People authorize and review evaluation work. Candidate production uses `cleanroom-spec`;
claim checking uses `spec-verifier`; coverage scoring runs in the opposite direction against the
ledger. A scored comparison is still to be run. No skill-quality percentage is supplied by this
document.

## A peripheral's lifecycle

Follow an ENC28J60 Ethernet peripheral attached to a board supported by a vendor kernel, through a
differently licensed target OS port. The board attachment is illustrative; the evaluation corpus is
the existing pilot. Paths below are consuming-project artifacts unless explicitly under this plugin.
This walkthrough describes how to reach a measurement, not a completed ENC28J60 comparison.

### 1. Set the scope and establish the board map

The person identifies the board revision, SPI attachment, peripheral revision, vendor tree, and
target OS. `cleanroom-spec` resolves any material forks using the question catalog. If the board
lacks a map, `board-spec-scaffold` writes `<root>/<board>.spec.md`, references an existing SoC or
writes `<root>/<soc>.spec.md`, and adds any missing host-controller IP spec and instance row. A new
root receives `board-specs.yaml`. An optional `<board>-expert/SKILL.md` makes the entry point
discoverable.

`spec_check.py` checks the board files and cross-root references. The scaffold's verification phase
produces `<root>/resources/<id>.verify.md` for each file, including overlays under their own roots.
Board mapping and peripheral authoring are separate products: fixing a board-console fact belongs in
the board map; the Ethernet controller's programming sequence belongs in the driver spec.

If measurement is part of this task, establish the corpus and blind ledger before generating the
ENC28J60 candidate. An evaluator who has already read the candidate cannot retroactively construct a
blind answer key for it. The evaluation section gives the required ordering and the existing pilot
paths. For the ENC28J60 comparison, source inputs must match `corpus.yaml`; an arbitrary vendor
kernel revision cannot silently replace its pinned reference. Without that preparation, proceed with
ordinary spec work but do not call it a blind test.

### 2. Investigate behind the boundary

The orchestrator chooses a scratch draft path and delegates to an investigator loading
`os-investigator` plus the appropriate board expert. The expert resolves the board, SoC, bus
attachment, and IP documents, then materializes reference sources in `~/src/<cache>/`. It records
actual commits rather than relying on a moving branch name.

The investigator uses the device tree for bus attachment and host-controller placement, translating
any mapped host addresses explicitly. It seeks hardware documentation for peripheral behavior, then
uses source to investigate remaining mechanisms. Source-only facts retain their caveats. Similar IP
is a lead to investigate, not evidence that every fact transfers unchanged to this instance.

The author writes the full draft at the scratch path and the exact reference-file list at
`docs/provenance/<device>-map.txt`. The reply contains only the draft path, a short summary, and
repository/commit provenance. The orchestrator has enough to route the next step without reading the
unverified document. The target-OS integration half can cite the target's own files directly.

### 3. Check what crosses the licensing wall

A fresh verifier receives the scratch path and provenance map and runs the five-check procedure from
`cleanroom-spec`. Its mandatory `leak_scan.py` comparison detects shared token sequences and
identifier reuse, allowing explicitly listed hardware nomenclature. The scanner reports locations,
lengths, and hashes rather than reproducing matched source passages.

A failure returns section and line references plus reasons, never offending text. A fresh author
repairs the scratch file, and another verification follows. After two failures on the same section,
the workflow stops and escalates the verdict to a person. If source is the only authority for a
mechanism, that person must decide whether and how it can be expressed within the workflow. The
absence of another authority does not permit relabeling a boundary failure as a pass.

On a boundary pass, the orchestrator lands `docs/<device>-spec.md`, hashes its contents, and appends
the revision and scan report to `docs/provenance-ledger.md`. Scan reports live under
`docs/provenance/`; transcripts are retained as evidence. The prescribed project index receives a
summary entry. This ledger records clean-room events, not the evaluation's list of requirements.

### 4. Establish accuracy separately

Invoke `spec-verifier` for the landed clean-room spec. It runs the boundary procedure unchanged and
then checks tagged facts against their documents, device trees, or pinned source. Its source reader
may compare source-observed behavior with the reference; the eventual implementer may not. An
inference is checked as an argument: true premises do not excuse an unsupported conclusion.

The external record lands at `docs/resources/<spec-basename>.verify.md`, or in the project's
existing `docs/provenance/` location as the verifier documents. It includes the spec hash, date,
verifier identity, sources actually consulted, and verdict totals. The body keys individual facts by
section and ordinal, table row, or sequence step. A board record instead lives beside the root
marker in `resources/`. [The Pixel 10 record](skills/board-expert/specs/resources/pixel10.verify.md)
shows actual source metadata and explanations of what each reading compared.

A wrong value, an unsupported derivation, or a citation that cannot be located is `FAIL`, with a
proposed correction. A source that cannot be reached, for example a blocked document, is
`UNVERIFIABLE`. A cited section that can be opened but does not support the statement is a failure,
not an access limitation. A TODO-only item is `GAP`. The author corrects failures and re-verifies;
`spec-verifier` itself never edits the spec.

If the independent readers disagree, record both readings as `ADJUDICATE` and exclude the item from
pass/fail counts until a person decides. Disagreement alone does not establish an error.
Adjudication may find a false fact or excessive certainty, either of which earns a failure on its
merits. Zero failures can still leave important gaps, inaccessible evidence, or unsettled readings.
The current accuracy procedure has no common repair bound; the two-failure bound above is for the
boundary check, and extending it to accuracy is proposed work.

### 5. Implement without reopening the reference

A different implementer receives the cleared spec, its public references under `docs/references/`,
and the target OS tree. It builds the Ethernet driver in the restricted environment. If a reset
condition is missing, it appends a question to `docs/spec-gaps/<device>.md`, marks the code site
`TODO(spec-gap)`, and works on another part. It does not open the source map or ask a research agent
to answer the question directly.

The orchestrator routes that question to a fresh investigation, edits a scratch copy, verifies it,
lands the new spec revision, adds a new ledger line, and closes the gap. Editing a landed spec
without this loop invalidates its earlier hash-based evidence. Before driver merge, the workflow
requires an output scan against the original provenance map and audits of every implementation
session and its artifacts. A contaminated session's entire diff is discarded and regenerated in a
fresh restricted session, as `cleanroom-implementer` specifies.

### 6. Measure, preserve, and revisit

With an independently frozen ENC28J60 ledger in place, the evaluator maps ledger requirements into
the candidate for recall, then checks candidate claims against sources for precision. The result
must name its frozen inputs and policy and preserve separate counts. The pilot artifacts live under
`evals/enc28j60/`: `corpus.yaml`, `ledger.yaml`, `SCORING-POLICY.md`, and the prescribed
`ledger.lock`. The scored comparison is unfinished, and the opened procedures specify no universal
score-output filename. A verified spec alone cannot supply this measurement.

Later spec edits make record hashes stale. Later source revisions require a new reading at the new
pin. On the anchored route, `anchor_check.py --drift` identifies unchanged, moved, and changed
citations; `--rewrite` moves safe anchors and marks changed ones stale. Removing a stale marker
requires re-verifying the claim. None of those operations establishes behavior on the actual board.

## Evaluation: measure omissions and errors separately

### Why verification is not a quality score

A verifier begins with what the candidate says. If the candidate contains no interrupt recovery
section, there may be no recovery claim to fail. `GAP` catches an explicit TODO, but it does not
create a requirement for an omission the author never acknowledged. Anchor inventories help find
unmentioned header names, yet those names are not an independently reviewed list of everything a
working driver needs. This is why the evaluation requires a separate answer key.

[The evaluation plan](EVAL-PLAN.md) asks whether another implementer could write a working driver
and meaningful tests without reading the original source. Documentary scoring measures necessary
parts of that question: coverage and correctness. Whether the implementation actually works still
needs execution evidence. The ENC28J60 pilot calibrates the method on a small public peripheral; it
is not evidence about performance on a complex SoC driver.

### Build the answer key before seeing the answer

[`corpus.yaml`](evals/enc28j60/corpus.yaml) identifies the permitted sources: driver and header
content at an exact commit, document editions and hashes, and an edition-specific errata map.
Documents are referenced rather than redistributed. The same URL can serve changed bytes, and the
same issue number can denote different problems in different errata editions. Edition identity and
located evidence are therefore part of the input, not bibliographic decoration.

Ledger authors read only that corpus and no candidate. Otherwise, the candidate can teach them which
requirements to remember, making its omissions disappear from the answer key. The rule also excludes
someone who has already seen a candidate from authoring rows for that device. Independent readers
derive critical requirements; merging preserves disagreements for adjudication rather than silently
taking the first writer's answer.

[`ledger.yaml`](evals/enc28j60/ledger.yaml) has a header recording the pilot, corpus date, authoring
rule, and reader/merge conventions, followed by `rows`. Each row has an immutable identifier,
statement, class, derivation, applicability, weight, scope, recoverability, and status. Reader and
review metadata record independent support. [The format](evals/enc28j60/LEDGER-FORMAT.md) is the
contract; current rows and unresolved decisions live in the ledger and its companion files.

Identifiers use `ENC28J60-<FACET>-<NNN>`, independent of both document and candidate headings. They
are never reused or renumbered. Withdrawn rows remain with reasons. A derivation names a corpus
source and a locator such as a section or mechanism, not just a page number. Separate applicability
fields preserve what the vendor confirms, what the implementation does, and what remains unresolved.
Silence in an erratum is not proof that a revision is unaffected.

Rows distinguish documented hardware requirements, observed software behavior, inference,
implementation choice, and unresolved conflict. That classification prevents a faithfully reported
software policy from becoming a falsely mandatory hardware rule. Rows should be atomic; the pilot
policy enumerates bounded exceptions for composite scoring units and their verdict rules. Do not
infer a general permission to bundle unrelated requirements from those exceptions.

### Freeze the inputs and decisions

Freezing is more than adding a date. Resolve provisional classifications and weights, dispose of
overlaps so one requirement is not credited twice, establish independent support for critical rows,
and preserve unresolved matters explicitly. Run corpus drift checks, the ledger schema/freeze
checks, and the clean-room scan prescribed by the [pilot README](evals/enc28j60/README.md). The gold
ledger is itself a clean-side artifact; source quotations do not become acceptable merely because
they are in an evaluation file.

`ledger_check.py` checks schema, identifiers, derivations against corpus pins, and structured freeze
conditions. It cannot establish blind authorship, semantic uniqueness, or the adequacy of a reader's
work. Those require the adjudicator's recorded attestation. Its `--freeze` mode checks readiness; it
is not permission to generate a candidate regardless of unresolved human decisions.

The lock records the ledger and corpus hashes, the policy version and content hash, the freeze date,
and the attestation. A version label alone cannot bind mutable policy text. `--lock` compares these
identities with the files used for a run. Consult the current
[checker](evals/enc28j60/ledger_check.py) and pilot README for the operative interface and remaining
freeze work. This directory is actively maintained; this document deliberately fixes neither its row
totals, remaining gate totals, nor a scoring-policy version.

Only after that freeze are candidates generated for the comparison. The planned with-skill and
without-skill arms use the same model, sources, tools, and budget. The answer key is not extracted
from either candidate. Candidate-informed corrections belong in a separately identified benchmark
revision; preserved candidates can be rescored with both old and new rules made explicit. Quietly
changing the denominator would confound a changed answer key with a changed skill.

### Recall: walk from the ledger into the candidate

The frozen policy determines which active, in-scope, recoverable rows enter recall. Recoverability
asks whether the candidate's supplied material could establish the requirement at all. A candidate
cannot remove rows by declaring a narrower scope, changing headings, or writing TODOs. Rows excluded
at authoring time remain visible with reasons rather than disappearing from the corpus.

The pilot's [scoring policy](evals/enc28j60/SCORING-POLICY.md) includes documented requirements,
unresolved conflicts, and inference rows. It reports observed software behavior separately and
excludes implementation choices from recall. A conflict is covered by accurately stating both
readings, not by pretending one is settled. Inference coverage must preserve its conditions and its
status as reasoning rather than documentation.

Each eligible row receives `covered`, `partial`, `missing`, or `misstated`. Full credit requires
enough information to implement the requirement. Partial credit covers incomplete statements;
TODO-only or absent content is missing. A misstatement earns no recall credit and also affects
precision. The formula is `(covered + 0.5 * partial) / eligible rows`, reported overall and within
each weight category, with the component counts. An empty category is reported as not applicable.

Weights distinguish critical, important, and minor consequences. The current policy's consequence
rule also limits the weight of requirements that matter only when an optional feature is used. Read
the exact weight rules in the ledger format rather than treating "critical" as a synonym for any
serious-looking register. Reporting categories separately prevents minor detail from masking missing
essentials. Partial counts remain visible because identical percentages can hide different patterns
of incompleteness.

### Precision: walk from candidate claims back to evidence

Precision checks every factual proposition, including ones without a ledger row. The policy splits
compound sentences and table assertions into independently falsifiable claims, then deduplicates
repeated propositions at their strongest statement. A claim matching several ledger rows is still
one claim. That avoids multiplying one mistake because the answer key has overlapping evidence.

A contradicted statement is an error. An accurately attributed observation of driver behavior is
judged as software behavior; declaring the same policy a hardware necessity can be an error.
Conditions matter: a revision-specific fact stated universally can be wrong even if its numerical
value came directly from a source. An inference presented as documented fact also has an attribution
error, even when its underlying content earns recall credit.

There is a substantive source inconsistency here. `EVAL-PLAN.md` defines precision in terms of
correct, supported claims and says unsupported extras count against it. The current
`SCORING-POLICY.md` instead defines precision by non-error claims and explicitly reports unsupported
claims separately without counting them as errors. It likewise reports true but underspecified
claims separately. Consequently, this pilot's precision must be read with its unsupported and
partial counts; it does not by itself mean the fraction independently supported by the corpus.

A scored run must identify the exact frozen policy rather than silently blend these definitions.
`spec-verifier` is a source of claim-verification evidence, not an automatic conversion from its
verdict totals into the pilot's claim segmentation and scoring. An unlocatable claimed citation, a
blocked authority, and an unsupported proposition also have different meanings and must not be
collapsed just because none produced a simple pass.

Recall and precision are never averaged. A short document can avoid errors while omitting nearly
everything needed; a comprehensive document can include a fatal false requirement. A combined number
conceals the difference. Report both directions, recall by consequence, unsupported claims, partial
statements, unresolved readings, and the input identities needed to interpret them.

## What is shipped, what is unfinished, and what is proposed

The investigation, authoring, verification, and implementation skills are shipped, with checkers and
tests. Existing board specs and verification records show their use. The plugin README lists test
commands. These components provide practical procedures and mechanical checks now; they do not
constitute the entire proposed validation architecture.

The main mechanical tools each have a narrower purpose than "prove this spec":

- [`spec_check.py`](skills/board-expert/scripts/spec_check.py) checks format, references, tag
  placement, selected public-root restrictions, stub resolution, and verification metadata.
- [`leak_scan.py`](skills/os-investigator/scripts/leak_scan.py) checks source overlap and reused
  identifiers; human or agent judgment still evaluates structure and close paraphrase.
- [`anchor_check.py`](skills/anchored-peripheral-spec/scripts/anchor_check.py) resolves citations,
  flags suspect literals and missing support, renders source beside claims, and detects drift.
- [`inventory_check.py`](skills/anchored-peripheral-spec/scripts/inventory_check.py) uses C-oriented
  patterns and device-tree inventory to find omissions and value conflicts, not
  semantic completeness.
- [`ledger_check.py`](evals/enc28j60/ledger_check.py) checks answer-key structure and freeze inputs;
  it is not the scored with-skill/without-skill comparison.

The ENC28J60 evaluation is partly built: corpus, format, ledger, scoring policy, conflict and
adjudication material, and checker exist. The scored comparison has not been run. Current freeze
readiness belongs in the pilot README, ledger, adjudication files, and checker output. The presence
of an answer-key file is neither proof that it is frozen nor a measured result for the skill.

[`VALIDATION-PROPOSAL.md`](VALIDATION-PROPOSAL.md) is a reviewed proposal, not an implementation. It
proposes links from requirements to tests, preserved attempts, separate decisions for spec
readiness, implementation validation, and physical validation, and strict treatment of unresolved
critical evidence. It also proposes test expectations derived independently of generated code,
mutation checks, and hardware observations tied to the actual image and fixture. None should be
inferred from an ordinary verification record's zero-failure summary.

The proposed delivery sequence starts with the blind ledger, then minimal scoring and acceptance
tools, then test contracts and synthetic execution, then separately gated physical work. Full vendor
workflows, feedback automation, and broader evaluation infrastructure are deferred. Fuchsia
integration is a separately scoped follow-on in a companion package. The proposal explicitly does
not authorize implementation or a paid evaluation campaign.

### Reading sources that disagree

Some discrepancies are historical text lag; others affect interpretation today:

- `EVAL-PLAN.md` and parts of the proposal/review say no ledger exists. The pilot now has
  `ledger.yaml`; existence does not establish freeze completion or a score.
- `SPEC-FORMAT.md` says a stale record cannot merge under default CI, but its own warning rules,
  the plugin README, and `spec_check.py` allow staleness unless `--require-verified` is used.
  A nonzero failure count is an error even when the record is stale.
- `VALIDATION-REVIEW.md` describes the stale-hash check hiding recorded failures. The proposal
  marks that bug fixed, and the current checker checks failures despite a stale hash.
- The scaffold says there is no shipped handset example, although `pixel10.spec.md` exists.
  Its "always verify" wording also differs from `QUESTIONS.md`, which offers verification later.
  Treat deferred verification as explicitly unverified, not as completion of its quality bar.
- The vendor guide calls same-layer overlay order undefined; the format specifies pointer order.
  Both warn about duplicate overlays for the same target in a layer. Consolidate them rather than
  relying on the disagreement about ordering.
- The evaluation plan and pilot scoring policy disagree about unsupported claims, as explained in
  the precision section. A result needs the locked rule, not an assumed shared definition.

The evaluation files may change during active ledger work, including whether policy-hash checking is
described as pending or implemented. Check the current script and rules together before a freeze.
This document does not resolve that moving work by inventing a completion status.

## Extending the system

For a new board, invoke [board-spec-scaffold](skills/board-spec-scaffold/SKILL.md). Choose the root
and hardware identity, reuse existing SoC/chip/IP specs, and put each new fact in the appropriate
file. Add a board stub only when a named skill entry point is useful. A new spec requires no skill
registration, but a new stub does: the scaffold lists the README and metadata updates, and the
repository registration checker catches missing README entries. Run structural and independent
verification over all roots needed to resolve the new references.

For a vendor overlay, follow [the vendor guide](skills/board-expert/VENDOR-GUIDE.md) and the
scaffold's overlay and vendor-tool templates. Put private resources in an appropriate nonpublic
root, declare it through supported pointers, and use `via:` for access instructions. Preserve the
public baseline and the origins of additions. Test discovery through a report's provenance block;
then verify the overlay under its own root. Do not treat a successful merge as factual adjudication.

For a new peripheral driver spec, choose the clean-room or anchored authoring skill based on the
reference relationship to the target. Resolve the IP and instance first, produce the programming and
OS-integration document, and follow that route's checks. A new generic IP map may also be needed,
but that is a separate reusable artifact. If quality measurement is wanted, establish a corpus and
blind ledger before candidate generation; copying the pilot's categories without reviewing
device-specific requirements does not create an answer key.

## Limits and unresolved boundaries

A spec that passes every check can still be wrong in the same way both readers were wrong.
Independent contexts reduce shared drafting history; they do not eliminate shared assumptions, model
errors, incorrect source documents, or mistakes in extracting a device tree. The review of the
validation proposal gives examples of false requirements surviving through specs and tests.

Verification establishes what claims were supported at a pin, not that they are right now or on
every revision. Spec hashes detect edits only when checked. Source hashes cannot retrieve a missing
document or establish access rights. A maintained branch name is not an immutable source identity,
and moved line numbers are not the only way a claim becomes obsolete.

A clean-room boundary check is about the wall, not accuracy. Mechanical dissimilarity and session
audits provide evidence about a particular process and its outputs; they cannot establish that a
model never encountered reference code during training. The source-access restrictions must also be
installed and tested in the actual harness. Prompt instructions alone do not provide isolation.

The current board checker reads verification frontmatter rather than independently redoing the
body's reasoning. `--require-verified` rejects missing or stale records but is not the proposal's
strict acceptance policy for every critical unresolved claim. Some anchor findings are warnings;
inventory omission checking is pattern-based. Passing these programs does not prove completeness.

The files do not establish a scored skill comparison, a working driver produced by this pilot, or a
qualified physical fixture for all proposed validation. They also leave general board/SoC claim
identities, policy placement, record migration, and follow-on hardware setup as proposal choices.
Consult the proposal's open-design section rather than assuming those interfaces exist.

Finally, no amount of this substitutes for running the driver on the hardware. A test that passes
under one revision, load, or timing condition does not prove a sequence universally unnecessary.
Even a captured target message saying `PASS` is still the target's assertion. The proposed hardware
work calls for observations such as externally received traffic or an instrument reading, tied to a
known device and image. Specifications and their evidence make that work better directed and more
reviewable; they do not perform it.
