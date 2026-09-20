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
| Hash / digest | A fingerprint of file contents; identifies bytes, not their correctness. |
| Requirement ledger | The independently authored answer key of hardware requirements used for evaluation scoring; called the ledger in evaluation documents. |
| Provenance ledger | A record of where facts came from and what crossed the clean-room boundary; distinct from the evaluation answer key. |
| Candidate | The generated specification or driver being evaluated. |
| Reference driver | The existing driver selected as comparison evidence; it can contain defects. |
| Arm | One experimental condition: specification generation with or without the skill, or downstream implementation from that condition's spec. Generation and implementation pairing are assessed separately. |
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
| Evidence channel | A means of collecting observations, such as a traffic peer or instrument capture; its suitability must be established for the observation. |
| Test envelope | The approved equipment configuration, operations, rates, duration, and other limits of a test. |
| Held-out test | An evaluation case kept out of development and tuning, used afterward to assess transfer to unfamiliar cases. |
| Regression test | A repeatable check that detects the return of a previously prevented defect. |
| Test model | A simplified executable description of expected behavior; its assumptions also need validation. |
| Convergence | Progress toward predefined acceptance conditions as defects and uncertainty are resolved; repeated agreement alone does not establish correctness. |
| Adjudication | Resolving conflicting readings of evidence, with unresolved questions kept explicit. |
| Clean-room boundary | Separation of source-reading and implementation contexts, controlling which evidence crosses. |
| SPI | Serial Peripheral Interface, a bus used to communicate with a peripheral. |
| Erratum | A documented hardware defect or deviation, often specific to a device revision. |
