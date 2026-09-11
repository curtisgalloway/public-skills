#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for scripts/swarm.py.

Run:  python3 -m unittest discover -s plugins/dev-tools/skills/review-swarm/tests -v

Fixtures are built at runtime: a tiny "repo" with one source file and a
run directory with whatever arm files each test needs. The tests that
matter most are the liveness ones — a missing or malformed arm must come
out as ARM FAILED in capitals and a non-zero exit, never as a quiet
zero-finding arm — and the evidence ones: a quote that is not in the cited
lines is dropped, not kept "because it is probably close".
"""

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
SWARM = HERE.parent / "scripts" / "swarm.py"

SOURCE = """\
fn main() {
    let port = open_port();
    for attempt in 0..RETRIES {
        port.write_all(&image)?;
        if ack(&port) { break; }
    }
    let lock = STATE.lock().unwrap();
    do_blocking_call();
    drop(lock);
}
"""

ARMS = ("security", "correctness", "compat", "docs")


def finding(**over):
    base = {
        "severity": "high",
        "file": "src/main.rs",
        "line_range": [3, 4],
        "claim": "The retry loop re-sends the whole image after a partial write.",
        "evidence_quote": "for attempt in 0..RETRIES {\n        port.write_all(&image)?;",
        "suggested_fix": "Resume from the last acknowledged offset.",
    }
    base.update(over)
    return base


class SwarmCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = pathlib.Path(self.tmp.name)
        self.repo = root / "repo"
        (self.repo / "src").mkdir(parents=True)
        (self.repo / "src" / "main.rs").write_text(SOURCE)
        self.run = root / "run"
        self.run.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def write_arm(self, arm, findings, status="complete", raw=None):
        path = self.run / f"{arm}.json"
        if raw is not None:
            path.write_text(raw)
        else:
            path.write_text(json.dumps({"arm": arm, "status": status, "findings": findings}))

    def write_all(self, findings_by_arm=None):
        findings_by_arm = findings_by_arm or {}
        for arm in ARMS:
            self.write_arm(arm, findings_by_arm.get(arm, []))

    def verify(self, *extra):
        proc = subprocess.run(
            [sys.executable, str(SWARM), "verify", "--repo", str(self.repo), "--run", str(self.run), *extra],
            capture_output=True,
            text=True,
            check=False,
        )
        data = json.loads((self.run / "verified.json").read_text())
        return proc, data

    def table(self):
        return subprocess.run(
            [sys.executable, str(SWARM), "table", "--run", str(self.run)],
            capture_output=True,
            text=True,
            check=False,
        )


class LivenessTests(SwarmCase):
    def test_missing_arm_is_failed_loudly(self):
        for arm in ("security", "correctness", "compat"):
            self.write_arm(arm, [])
        proc, data = self.verify()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("!!! ARM FAILED: docs", proc.stdout)
        self.assertIn("no output file", proc.stdout)
        self.assertEqual(data["arms"]["docs"]["status"], "FAILED")
        for arm in ("security", "correctness", "compat"):
            self.assertEqual(data["arms"][arm]["status"], "OK")

    def test_malformed_json_is_failed_not_empty(self):
        self.write_all()
        self.write_arm("security", None, raw="I found nothing wrong, great code!")
        proc, data = self.verify()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("!!! ARM FAILED: security", proc.stdout)
        self.assertIn("unparsable JSON", data["arms"]["security"]["reason"])

    def test_prose_json_without_findings_list_is_failed(self):
        self.write_all()
        self.write_arm("compat", None, raw=json.dumps({"summary": "looks fine"}))
        proc, data = self.verify()
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(data["arms"]["compat"]["status"], "FAILED")

    def test_partial_arm_keeps_findings_and_is_loud(self):
        self.write_all()
        path = self.run / "docs.json"
        path.write_text(
            json.dumps(
                {"arm": "docs", "status": "partial", "note": "budget", "findings": [finding()]}
            )
        )
        proc, data = self.verify()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("!!! ARM PARTIAL: docs", proc.stdout)
        self.assertEqual(data["arms"]["docs"]["verified"], 1)
        self.assertEqual(len(data["findings"]), 1)

    def test_all_arms_ok_exits_zero(self):
        self.write_all({"correctness": [finding()]})
        proc, data = self.verify()
        self.assertEqual(proc.returncode, 0)
        self.assertNotIn("ARM FAILED", proc.stdout)
        self.assertEqual(len(data["findings"]), 1)


class EvidenceTests(SwarmCase):
    def test_exact_quote_in_range_is_verified(self):
        self.write_all({"correctness": [finding()]})
        _, data = self.verify()
        self.assertEqual(len(data["findings"]), 1)
        self.assertEqual(data["dropped"], [])
        self.assertEqual(data["findings"][0]["line_range"], [3, 4])

    def test_quote_absent_from_file_is_dropped(self):
        self.write_all({"security": [finding(evidence_quote="port.write_all(image.as_bytes())")]})
        _, data = self.verify()
        self.assertEqual(data["findings"], [])
        self.assertEqual(len(data["dropped"]), 1)
        self.assertIn("not found", data["dropped"][0]["reason"])

    def test_paraphrase_is_dropped(self):
        self.write_all({"security": [finding(evidence_quote="for each attempt up to RETRIES, write the image")]})
        _, data = self.verify()
        self.assertEqual(data["findings"], [])

    def test_quote_near_range_is_corrected_within_slack(self):
        self.write_all({"correctness": [finding(line_range=[1, 2])]})
        _, data = self.verify()
        self.assertEqual(len(data["findings"]), 1)
        self.assertEqual(data["findings"][0]["line_range"], [3, 4])
        self.assertIn("corrected", data["findings"][0]["check_note"])

    def test_quote_far_from_range_is_dropped_with_location_hint(self):
        self.write_all({"correctness": [finding(line_range=[9, 10])]})
        _, data = self.verify("--slack", "1")
        self.assertEqual(data["findings"], [])
        self.assertIn("exists in", data["dropped"][0]["reason"])
        self.assertIn("not within lines 9-10", data["dropped"][0]["reason"])

    def test_wide_range_is_tightened(self):
        self.write_all({"correctness": [finding(line_range=[1, 10])]})
        _, data = self.verify()
        self.assertEqual(data["findings"][0]["line_range"], [3, 4])
        self.assertIn("tightened", data["findings"][0]["check_note"])

    def test_bad_severity_and_missing_field_are_dropped(self):
        bad_sev = finding(severity="urgent")
        no_fix = finding()
        del no_fix["suggested_fix"]
        self.write_all({"compat": [bad_sev, no_fix]})
        _, data = self.verify()
        self.assertEqual(data["findings"], [])
        reasons = " ".join(d["reason"] for d in data["dropped"])
        self.assertIn("unknown severity", reasons)
        self.assertIn("missing field", reasons)

    def test_path_escape_and_missing_file_are_dropped(self):
        self.write_all(
            {
                "security": [
                    finding(file="../etc/passwd"),
                    finding(file="src/nothere.rs"),
                    finding(file="/src/main.rs"),
                ]
            }
        )
        _, data = self.verify()
        self.assertEqual(data["findings"], [])
        self.assertEqual(len(data["dropped"]), 3)

    def test_range_past_end_of_file_is_dropped(self):
        self.write_all({"security": [finding(line_range=[40, 41])]})
        _, data = self.verify()
        self.assertIn("exceeds file length", data["dropped"][0]["reason"])


class DedupTests(SwarmCase):
    def test_same_claim_from_two_arms_is_merged_with_higher_severity(self):
        self.write_all(
            {
                "correctness": [finding(severity="medium")],
                "compat": [
                    finding(
                        severity="critical",
                        claim="Retry loop re-sends the whole image after a partial write, duplicating blocks.",
                    )
                ],
            }
        )
        _, data = self.verify()
        self.assertEqual(len(data["findings"]), 1)
        f = data["findings"][0]
        self.assertEqual(f["severity"], "critical")
        self.assertEqual(sorted(f["arms"]), ["compat", "correctness"])
        self.assertEqual(f["merged_from"], ["F2"])
        self.assertEqual(data["dup_candidates"], [])

    def test_overlapping_but_different_claims_are_flagged_not_merged(self):
        self.write_all(
            {
                "correctness": [finding()],
                "docs": [
                    finding(
                        claim="README says flashing is atomic; this loop shows it is not.",
                        evidence_quote="port.write_all(&image)?;",
                        line_range=[4, 4],
                    )
                ],
            }
        )
        _, data = self.verify()
        self.assertEqual(len(data["findings"]), 2)
        self.assertEqual(data["dup_candidates"], [["F1", "F2"]])


class TableTests(SwarmCase):
    def test_table_ranks_by_severity_then_agreement_and_shows_failed_arm(self):
        for arm in ("security", "correctness", "compat"):
            self.write_arm(arm, [])
        self.write_arm(
            "correctness",
            [
                finding(severity="low", claim="A low thing."),
                finding(
                    severity="critical",
                    claim="Lock held across a blocking call.",
                    line_range=[7, 8],
                    evidence_quote="let lock = STATE.lock().unwrap();\n    do_blocking_call();",
                ),
            ],
        )
        self.verify()
        proc = self.table()
        self.assertEqual(proc.returncode, 1)
        out = proc.stdout
        self.assertIn("!!! ARM FAILED: docs", out)
        self.assertIn("UNREFEREED", out)
        rows = [l for l in out.splitlines() if l.startswith("| ") and "| F" in l]
        self.assertEqual(len(rows), 2)
        self.assertIn("critical", rows[0])
        self.assertIn("low", rows[1])

    def test_table_prefers_final_json_and_reports_referee_counts(self):
        self.write_all({"correctness": [finding()]})
        self.verify()
        verified = json.loads((self.run / "verified.json").read_text())
        final = {
            "schema": "review-swarm/1",
            "arms": verified["arms"],
            "findings": [],
            "referee": {
                "status": "complete",
                "reviewed": 1,
                "dropped": [{"id": "F1", "reason": "the loop breaks on ack; no duplicate write"}],
                "merged": [],
                "severity_changes": [],
            },
        }
        (self.run / "final.json").write_text(json.dumps(final))
        proc = self.table()
        self.assertEqual(proc.returncode, 0)
        self.assertNotIn("UNREFEREED", proc.stdout)
        self.assertIn("All 4 arms delivered.", proc.stdout)
        self.assertIn("No findings survived.", proc.stdout)
        self.assertIn("referee dropped 1", proc.stdout)

    def test_table_without_any_result_is_a_precondition_error(self):
        proc = self.table()
        self.assertEqual(proc.returncode, 3)


if __name__ == "__main__":
    unittest.main()
