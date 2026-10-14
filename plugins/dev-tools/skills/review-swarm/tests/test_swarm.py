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

ARMS = ("security", "correctness", "compat", "docs", "history", "conventions", "perf")


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

    def table(self, *extra):
        return subprocess.run(
            [sys.executable, str(SWARM), "table", "--run", str(self.run), *extra],
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
        self.assertIn("All 7 arms delivered.", proc.stdout)
        self.assertIn("No findings survived.", proc.stdout)
        self.assertIn("referee dropped 1", proc.stdout)

    def test_table_without_any_result_is_a_precondition_error(self):
        proc = self.table()
        self.assertEqual(proc.returncode, 3)

    def test_pr_format_links_every_finding_and_names_failed_arms(self):
        for arm in ARMS[:-1]:
            self.write_arm(arm, [])
        self.write_arm("correctness", [finding()])
        self.verify()
        blob = "https://github.com/o/r/blob/" + "a" * 40
        proc = self.table("--format", "pr", "--blob-url", blob + "/")
        self.assertEqual(proc.returncode, 1)
        out = proc.stdout
        self.assertIn("**ARM FAILED: perf**", out)
        self.assertIn("UNREFEREED", out)
        self.assertIn(f"{blob}/src/main.rs#L2-L5", out)
        self.assertNotIn("| F", out)

    def test_pr_format_needs_blob_url(self):
        self.write_all()
        self.verify()
        self.assertEqual(self.table("--format", "pr").returncode, 2)
        self.assertEqual(
            self.table("--format", "pr", "--blob-url", "https://x/blob/s", "--json").returncode, 2
        )


PATCH = """\
diff --git a/src/main.rs b/src/main.rs
--- a/src/main.rs
+++ b/src/main.rs
@@ -2,3 +2,4 @@ fn main() {
     let port = open_port();
+    for attempt in 0..RETRIES {
         port.write_all(&image)?;
         if ack(&port) { break; }
diff --git a/src/gone.rs b/src/gone.rs
--- a/src/gone.rs
+++ /dev/null
@@ -1,2 +0,0 @@
-fn gone() {}
-
"""


class DiffTests(SwarmCase):
    def test_finding_outside_every_hunk_is_marked_not_dropped(self):
        (self.run / "diff.patch").write_text(PATCH)
        lock = finding(
            claim="Lock held across a blocking call.",
            line_range=[7, 8],
            evidence_quote="let lock = STATE.lock().unwrap();\n    do_blocking_call();",
        )
        self.write_all({"correctness": [finding()], "perf": [lock]})
        proc, data = self.verify()
        self.assertEqual(proc.returncode, 0)
        self.assertTrue(data["diff_checked"])
        by_line = {f["line_range"][0]: f for f in data["findings"]}
        self.assertNotIn("outside_diff", by_line[3])
        self.assertTrue(by_line[7]["outside_diff"])
        self.assertIn("1 finding(s) touch no hunk", proc.stdout)
        self.assertIn("(outside diff)", self.table().stdout)

    def test_without_a_patch_nothing_is_marked_and_the_gap_is_said(self):
        self.write_all({"correctness": [finding(line_range=[9, 9], evidence_quote="drop(lock);")]})
        proc, data = self.verify()
        self.assertFalse(data["diff_checked"])
        self.assertNotIn("outside_diff", data["findings"][0])
        self.assertIn("not checked against the diff", proc.stdout)

    def test_pure_deletion_hunk_counts_as_its_line(self):
        (self.run / "diff.patch").write_text(
            "+++ b/src/main.rs\n@@ -9,2 +8,0 @@\n-    old();\n-    older();\n"
        )
        self.write_all(
            {"correctness": [finding(line_range=[8, 8], evidence_quote="do_blocking_call();")]}
        )
        _, data = self.verify()
        self.assertNotIn("outside_diff", data["findings"][0])


def patch_for(path, added, removed=()):
    """A one-hunk unified diff adding `added` lines (and removing `removed`) in `path`."""
    body = [f"-{l}" for l in removed] + [f"+{l}" for l in added]
    return (
        f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n"
        f"@@ -1,{len(removed)} +1,{len(added)} @@\n" + "\n".join(body) + "\n"
    )


class PlanTests(SwarmCase):
    def plan(self, patch, *extra):
        (self.run / "diff.patch").write_text(patch)
        proc = subprocess.run(
            [sys.executable, str(SWARM), "plan", "--run", str(self.run), *extra],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc, json.loads((self.run / "plan.json").read_text())

    def names(self, plan):
        return [a["name"] for a in plan["arms"]]

    def test_prose_only_diff_is_light_at_any_size(self):
        _, plan = self.plan(patch_for("docs/guide.md", [f"line {i}" for i in range(800)]))
        self.assertEqual(plan["tier"], "light")
        self.assertEqual(self.names(plan), ["light"])
        self.assertEqual(plan["arms"][0]["model"], "cheap")
        self.assertEqual(plan["arms"][0]["tool_budget"], 40)

    def test_small_code_diff_is_light_on_the_strong_model(self):
        _, plan = self.plan(patch_for("src/calc.py", ["def add(a, b):", "    return a + b"]))
        self.assertEqual(plan["tier"], "light")
        self.assertEqual(plan["arms"][0]["model"], "strong")
        self.assertEqual(plan["arms"][0]["tool_budget"], 25)

    def test_larger_code_diff_is_standard_with_context_arm(self):
        lines = [f"    total += item_{i}" for i in range(80)]
        _, plan = self.plan(patch_for("src/calc.py", lines))
        self.assertEqual(plan["tier"], "standard")
        self.assertEqual(self.names(plan), ["correctness", "docs", "compat", "context"])
        models = {a["name"]: a["model"] for a in plan["arms"]}
        self.assertEqual(models["correctness"], "strong")
        self.assertEqual(models["docs"], "cheap")

    def test_security_surface_adds_security_arm_to_standard(self):
        lines = [f"    x_{i} = {i}" for i in range(60)] + ["    subprocess.run(cmd)"]
        _, plan = self.plan(patch_for("src/run.py", lines))
        self.assertEqual(plan["tier"], "standard")
        self.assertEqual(self.names(plan)[0], "security")

    def test_risk_trigger_makes_even_a_small_diff_full(self):
        proc, plan = self.plan(patch_for("src/state.rs", ["let guard = STATE.lock();"]))
        self.assertEqual(plan["tier"], "full")
        self.assertEqual(self.names(plan), list(ARMS))
        self.assertIn("concurrency", plan["triggers"])
        self.assertIn("risk trigger", proc.stdout)

    def test_trigger_owner_arm_gets_the_strong_model(self):
        _, plan = self.plan(patch_for("src/cfg.py", ['API_KEY = "x"']))
        models = {a["name"]: a["model"] for a in plan["arms"]}
        self.assertEqual(models["security"], "strong")
        self.assertEqual(models["compat"], "cheap")

    def test_trigger_words_in_prose_do_not_escalate(self):
        _, plan = self.plan(patch_for("README.md", ["Set the API_KEY and the password."]))
        self.assertEqual(plan["tier"], "light")

    def test_migration_path_is_a_trigger(self):
        _, plan = self.plan(patch_for("db/migrations/0002_add.sql", ["ADD COLUMN x int;"]))
        self.assertEqual(plan["tier"], "full")

    def test_close_escalates_code_but_not_prose(self):
        lines = [f"    total += item_{i}" for i in range(80)]
        _, plan = self.plan(patch_for("src/calc.py", lines), "--close")
        self.assertEqual(plan["tier"], "full")
        _, plan = self.plan(patch_for("docs/notes.md", ["a", "b"]), "--close")
        self.assertEqual(plan["tier"], "light")

    def test_requested_tier_overrides(self):
        _, plan = self.plan(patch_for("docs/notes.md", ["a"]), "--tier", "full")
        self.assertEqual(plan["tier"], "full")
        self.assertEqual(len(plan["arms"]), 7)

    def test_huge_diff_requires_split(self):
        proc, plan = self.plan(patch_for("src/big.py", [f"x{i} = {i}" for i in range(3100)]))
        self.assertTrue(plan["split_required"])
        self.assertIn("SPLIT REQUIRED", proc.stdout)

    def test_plan_without_patch_is_a_precondition_error(self):
        proc = subprocess.run(
            [sys.executable, str(SWARM), "plan", "--run", str(self.run)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 3)

    def test_verify_takes_arms_from_the_plan(self):
        self.plan(patch_for("src/main.rs", ["    let port = open_port();"]))
        self.write_arm("light", [finding(severity="low")])
        proc, data = self.verify()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertEqual(list(data["arms"]), ["light"])


class RefereeRuleTests(SwarmCase):
    def test_low_findings_need_no_referee_and_table_says_so(self):
        self.write_all({"docs": [finding(severity="medium")]})
        proc, data = self.verify()
        self.assertFalse(data["referee_needed"])
        self.assertIn("referee: not needed", proc.stdout)
        out = self.table()
        self.assertEqual(out.returncode, 0)
        self.assertNotIn("UNREFEREED", out.stdout)
        self.assertIn("not refereed: no high/critical", out.stdout)

    def test_high_finding_needs_referee_and_is_unrefereed_without_one(self):
        self.write_all({"correctness": [finding(severity="high")]})
        proc, data = self.verify()
        self.assertTrue(data["referee_needed"])
        self.assertIn("referee: NEEDED", proc.stdout)
        out = self.table()
        self.assertEqual(out.returncode, 1)
        self.assertIn("UNREFEREED", out.stdout)

    def test_duplicate_group_needs_referee(self):
        other = finding(severity="low", claim="Completely different words about allocation.")
        self.write_all({"correctness": [finding(severity="low")], "perf": [other]})
        _, data = self.verify()
        self.assertTrue(data["dup_candidates"])
        self.assertTrue(data["referee_needed"])


class RecheckTests(SwarmCase):
    def write_recheck(self, resolved, findings=()):
        (self.run / "recheck.json").write_text(
            json.dumps(
                {"arm": "recheck", "status": "complete", "resolved": resolved,
                 "unresolved": [], "findings": list(findings)}
            )
        )

    def test_confirmed_resolution_passes(self):
        self.write_recheck(
            [{"id": "F1", "file": "src/main.rs", "line_range": [5, 5],
              "evidence_quote": "if ack(&port) { break; }"}]
        )
        proc, data = self.verify("--arms", "recheck")
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertTrue(data["resolved"][0]["confirmed"])

    def test_resolution_quote_not_in_code_is_loud(self):
        self.write_recheck(
            [{"id": "F1", "file": "src/main.rs", "line_range": [5, 5],
              "evidence_quote": "resume_from(last_ack);"}]
        )
        proc, data = self.verify("--arms", "recheck")
        self.assertEqual(proc.returncode, 1)
        self.assertFalse(data["resolved"][0]["confirmed"])
        self.assertIn("!!! RESOLUTION NOT CONFIRMED F1", proc.stdout)

    def test_new_findings_from_the_fix_are_checked_like_any_other(self):
        self.write_recheck([], [finding(severity="low"), finding(evidence_quote="not in the file")])
        _, data = self.verify("--arms", "recheck")
        self.assertEqual(len(data["findings"]), 1)
        self.assertEqual(len(data["dropped"]), 1)


if __name__ == "__main__":
    unittest.main()
