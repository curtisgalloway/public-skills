<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Glossary

Shared terminology for this repository. This initial glossary covers driver-specification
evaluation; add other terms as the documents that use them are updated.

| Term | Meaning |
| --- | --- |
| Agent | An AI assistant with tools; here, an author, implementer, or reviewer in a recorded session. |
| Skill | Instructions and optional supporting tools that guide an agent through a task. |
| Plugin | A package of related skills and optional tools. |
| Specification (spec) | A document describing hardware behavior precisely enough to implement a driver. |
| Driver | Software through which an operating system controls a device. |
| OS / kernel | Operating system / its core that manages hardware and supplies driver interfaces. |
| API | An interface a program uses to call another software component. |
| SDK | Software development kit: headers, libraries, and tools for building against a platform. |
| Corpus | The pinned collection of source code and documents used as reference evidence. |
| Pin | An exact revision, edition, or file digest identifying an input. |
| QEMU / device model | An open-source machine emulator / its software imitation of a hardware device, which a guest OS drives as if it were real. A device model is a separate implementation, not the silicon. |
| Differential test | Running a reference driver and a candidate under identical scenarios and comparing their outcomes and register traces. |
| Emulated evidence | A result observed on a QEMU device model (proposed class `[emulated]`); weaker than a hardware measurement because models are often lenient. |
| RTL | Register-transfer level: the hardware design written in a language such as Verilog or VHDL. As evidence (`[rtl]`), the strongest authority for digital register behavior on the revision it names. |
| Conflict entry | A recorded disagreement between evidence sources, kept beside the claim with both readings, the resolution, and the assumption that justified it. |
| Hash / digest | A fingerprint of file contents; identifies bytes, not their correctness. |
| Claim / verification record | A statement checked against evidence / the separate report recording that comparison and its limits. |
| Carry-forward | Retaining an earlier finding for unchanged text; it is not a fresh reading of its sources. |
| UART / baud | A serial communication controller / the signaling rate of its connection. |
| Mux | A selector that routes a connection; its selected mode can change which setup steps apply. |
| GIC | Arm's Generic Interrupt Controller, which routes interrupt requests to processor cores. |
| Requirement ledger | The independently authored answer key of hardware requirements used for evaluation scoring; called the ledger in evaluation documents. |
| Provenance ledger | A record of where facts came from and what crossed the clean-room boundary; distinct from the evaluation answer key. |
| Candidate | The generated specification or driver being evaluated. |
| Reference driver | The existing driver selected as comparison evidence; it can contain defects. |
| Evaluator | The preparation and testing side allowed to inspect reference material; separate from an isolated implementer. |
| Guest | An operating system running inside a virtual machine or container environment, separate from the host. |
| OCI image | A container image stored in the standardized Open Container Initiative format, with content identified by digests. |
| Initramfs | An initial filesystem loaded into memory with the kernel, used for startup or as a small self-contained system. |
| Netboot | Fetching boot files over the network before starting the operating system. |
| NFS root | A root filesystem accessed over the Network File System protocol; it requires working networking during startup. |
| Arm / experimental arm | Arm is the processor architecture company in hardware references. An experimental arm is one study condition: specification generation with or without the skill, or downstream implementation from that condition's spec. Generation and implementation pairing are assessed separately. |
| Baseline / treatment | The without-skill / with-skill generation conditions. |
| Paired run | Runs with recorded conditions held constant except for the intended experimental difference. |
| Recall / precision | Coverage of required facts / correctness and support of the claims actually made. |
| Reconstruction | Implementing a driver from a spec on the same OS as the reference driver. |
| Differential testing | Running implementations through shared scenarios and comparing observable behavior. |
| Fixture | The prepared hardware and connections used to execute repeatable tests. |
| Fault injection | Deliberately provoking a failure condition to test recovery. |
| Mutation check | Deliberately introducing a defect to verify that a test detects it. |
| Acceptance gate | A predefined condition that must be met before an artifact advances or is accepted. |
| Milestone | A bounded deliverable with dependencies, acceptance criteria, verification, review, and a recorded checkpoint. |
| Validation contract | A test's requirements, independently supported expected observations, decision rule, setup, and limits. |
| Run manifest | The record identifying an experiment's inputs, settings, versions, access rules, and output artifacts. |
| Preparation manifest | An input and decision record that lists unresolved launch prerequisites; it is not a frozen execution manifest or permission to run. |
| Sidecar | A separate record linked to existing artifacts by identity or digest, without modifying those artifacts. |
| Custody | Locating and recovering the exact archived bytes used in an earlier run. |
| Qualification | Demonstrating that a build, access control, fixture, or check works within its declared scope. |
| Device tree / DTB | A hardware description supplied to a kernel / its compiled binary form. |
| GPIO / IRQ | General-purpose input/output pin / an interrupt request that signals an event to a processor. |
| FCS | Ethernet frame check sequence: the error-detection bytes that a capture may include or strip. |
| defconfig | A kernel's starting configuration; the resolved build configuration must still be recorded. |
| Evidence channel | A means of collecting observations, such as a traffic peer or instrument capture; its suitability must be established for the observation. |
| Test envelope | The approved equipment configuration, operations, rates, duration, and other limits of a test. |
| Held-out test | An evaluation case kept out of development and tuning, used afterward to assess transfer to unfamiliar cases. |
| Regression test | A repeatable check that detects the return of a previously prevented defect. |
| Test model | A simplified executable description of expected behavior; its assumptions also need validation. |
| Convergence | Progress toward predefined acceptance conditions as defects and uncertainty are resolved; repeated agreement alone does not establish correctness. |
| Adjudication | Resolving conflicting readings of evidence, with unresolved questions kept explicit. |
| Clean-room boundary | Separation of source-reading and implementation contexts, controlling which evidence crosses. |
| SPI | Serial Peripheral Interface in bus discussions; Shared Peripheral Interrupt in Arm GIC descriptions. |
| Erratum | A documented hardware defect or deviation, often specific to a device revision. |
| Blind requirement list | Requirements written from a device manual before any spec exists, used afterward to measure what the spec left out; the e1000 list is `evals/e1000/requirements.yaml` in [driver-lab](https://github.com/curtisgalloway/driver-lab). |
| Transfer review | The clean-room gate a spec passes before anyone else may read it: a mechanical leak scan plus checks for copied code, structure, attractants, and the usage notice. It does not judge accuracy. |
| Attractant | Anything in a clean-room spec that would pull a reader back to the encumbered source, such as a source file path or "the driver does X in function Y" narration. |
| SDM | The Intel 8254x Software Developer's Manual (document 317453-006, revision 4.0), the e1000 hardware reference. |
| Operator | In the driver-porting runs, the coordinating agent session that prepares inputs and briefs, launches the other agents, and writes the evidence; it writes no driver code. |
| Review swarm | The `review-swarm` skill: four reviewer agents with narrow mandates, a mechanical check that drops findings not quotable from the code, and a referee. |
| Lab notebook | Append-only, timestamped notes per unit of work (chapters) plus an index, kept as the work happens (`lab-notebook` skill); the driver-porting notebook is `notebook/` in [driver-lab](https://github.com/curtisgalloway/driver-lab). |
| Process log | A per-project log of where the agent's process cost time, as input for improving instructions and skills; for driver-porting, `PROCESS-NOTES.md` in [driver-lab](https://github.com/curtisgalloway/driver-lab). |
