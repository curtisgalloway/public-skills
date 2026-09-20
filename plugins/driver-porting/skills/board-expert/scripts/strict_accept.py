#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Strict documentary acceptance for the ENC28J60 pilot, not legacy board records.

Imported by the pilot scorer. Semantic judgments remain the reviewers' responsibility.
No implementation or hardware result can be inferred from this decision.
"""

VERSION = "enc28j60-documentary-1"


def decide(rows, claims, gates, stale):
    reasons = []
    for row in rows:
        if row["eligible"] and row["verdict"] != "covered":
            reasons.append(f"{row['id']}: mandatory requirement is {row['verdict']}")
    for claim in claims:
        if claim["verdict"] == "FAIL":
            reasons.append(f"{claim['id']}: known factual or attribution failure")
        if claim["verdict"] in ("ADJUDICATE", "PENDING"):
            reasons.append(f"{claim['id']}: unresolved claim")
        if claim["weight"] == "critical":
            if claim["verdict"] != "PASS":
                reasons.append(f"{claim['id']}: critical claim is not PASS")
            if len(claim["reviewers"]) < 2:
                reasons.append(f"{claim['id']}: critical claim lacks two independent reviews")
    for name, passed in gates.items():
        if not passed:
            reasons.append(f"{name}: required review gate has not passed")
    return {
        "policy_version": VERSION,
        "spec_ready": {
            "status": "stale" if stale else "blocked" if reasons else "accepted",
            "reasons": stale + reasons,
        },
        "implementation_validated": {"status": "blocked", "reasons": ["not evaluated"]},
        "hardware_validated": {"status": "blocked", "reasons": ["not evaluated"]},
    }
