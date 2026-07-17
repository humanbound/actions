# SPDX-License-Identifier: Apache-2.0
"""Unit tests for scripts/to_sarif.py (stdlib only — run with `python -m unittest`)."""

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import to_sarif  # noqa: E402


def entry(result="fail", category="llm01", explanation="x", severity=60, **kw):
    return {
        "result": result,
        "fail_category": category,
        "explanation": explanation,
        "severity": severity,
        **kw,
    }


def build(logs, anchor="cfg.json", version="1.0.0"):
    return to_sarif.build_sarif(logs, anchor, version)


class TestResultFiltering(unittest.TestCase):
    def test_only_fails_become_results(self):
        logs = [entry(), entry(result="pass"), entry(result="error"), entry(result="FAIL")]
        results = build(logs)["runs"][0]["results"]
        self.assertEqual(len(results), 2)  # "fail" and case-insensitive "FAIL"

    def test_non_dict_entries_skipped(self):
        results = build([entry(), "garbage", None, 42])["runs"][0]["results"]
        self.assertEqual(len(results), 1)

    def test_empty_logs_produce_valid_empty_run(self):
        sarif = build([])
        self.assertEqual(sarif["version"], "2.1.0")
        self.assertEqual(sarif["runs"][0]["results"], [])
        self.assertEqual(sarif["runs"][0]["tool"]["driver"]["rules"], [])


class TestSeverityMapping(unittest.TestCase):
    # Boundaries mirror the CLI: >=75 critical, >=50 high, >=25 medium, >=1 low, else info
    def check(self, severity, expected_level, expected_label):
        r = build([entry(severity=severity)])["runs"][0]["results"][0]
        self.assertEqual(r["level"], expected_level)
        self.assertEqual(r["properties"]["severity-label"], expected_label)

    def test_critical_is_error(self):
        self.check(75, "error", "critical")

    def test_high_is_error(self):
        self.check(50, "error", "high")

    def test_medium_is_warning(self):
        self.check(25, "warning", "medium")

    def test_low_is_note(self):
        self.check(1, "note", "low")

    def test_info_is_note(self):
        self.check(0, "note", "info")

    def test_garbage_severity_treated_as_info(self):
        r = build([entry(severity="not-a-number")])["runs"][0]["results"][0]
        self.assertEqual(r["properties"]["severity-label"], "info")

    def test_security_severity_is_tenth_scale(self):
        r = build([entry(severity=82)])["runs"][0]["results"][0]
        self.assertEqual(r["properties"]["security-severity"], "8.2")


class TestRules(unittest.TestCase):
    def test_categories_dedupe_into_rules(self):
        logs = [entry(category="a"), entry(category="a"), entry(category="b")]
        rules = build(logs)["runs"][0]["tool"]["driver"]["rules"]
        self.assertEqual(sorted(r["id"] for r in rules), ["a", "b"])

    def test_rule_security_severity_keeps_max(self):
        # GitHub buckets alerts per-rule, so the rule must carry the worst case
        logs = [entry(category="a", severity=30), entry(category="a", severity=82)]
        rules = build(logs)["runs"][0]["tool"]["driver"]["rules"]
        self.assertEqual(rules[0]["properties"]["security-severity"], "8.2")

    def test_missing_category_becomes_uncategorized(self):
        r = build([entry(category="")])["runs"][0]["results"][0]
        self.assertEqual(r["ruleId"], "uncategorized")


class TestFingerprints(unittest.TestCase):
    def test_identical_findings_get_distinct_fingerprints(self):
        logs = [entry(explanation="same"), entry(explanation="same")]
        results = build(logs)["runs"][0]["results"]
        fps = {r["partialFingerprints"]["humanbound/v1"] for r in results}
        self.assertEqual(len(fps), 2)

    def test_fingerprint_stable_across_builds(self):
        a = build([entry()])["runs"][0]["results"][0]["partialFingerprints"]
        b = build([entry()])["runs"][0]["results"][0]["partialFingerprints"]
        self.assertEqual(a, b)


class TestLocations(unittest.TestCase):
    def test_every_result_anchored(self):
        results = build([entry()], anchor="test/bot-config.json")["runs"][0]["results"]
        loc = results[0]["locations"][0]["physicalLocation"]
        self.assertEqual(loc["artifactLocation"]["uri"], "test/bot-config.json")
        self.assertEqual(loc["region"]["startLine"], 1)


class TestLoadLogs(unittest.TestCase):
    def test_dict_shape(self):
        p = REPO_ROOT / "test" / "sample-results.json"
        logs = to_sarif.load_logs(str(p))
        self.assertEqual(len(logs), 5)

    def test_bare_list_shape(self, tmp="/tmp/_sarif_list.json"):
        Path(tmp).write_text(json.dumps([entry()]))
        self.assertEqual(len(to_sarif.load_logs(tmp)), 1)

    def test_sample_fixture_end_to_end(self):
        p = REPO_ROOT / "test" / "sample-results.json"
        sarif = build(to_sarif.load_logs(str(p)))
        self.assertEqual(len(sarif["runs"][0]["results"]), 3)  # 3 fails in fixture


class TestLabelStringSeverity(unittest.TestCase):
    # Platform-side data can carry severity as a label string, not a 0-100 float.
    def test_label_maps_to_level_and_github_bucket(self):
        r = build([entry(severity="High")])["runs"][0]["results"][0]
        self.assertEqual(r["level"], "error")
        self.assertEqual(r["properties"]["severity-label"], "high")
        self.assertEqual(r["properties"]["security-severity"], "7.5")

    def test_label_critical_bucket(self):
        r = build([entry(severity="critical")])["runs"][0]["results"][0]
        self.assertEqual(r["properties"]["security-severity"], "9.5")
        self.assertEqual(r["level"], "error")

    def test_label_medium_is_warning(self):
        r = build([entry(severity=" Medium ")])["runs"][0]["results"][0]
        self.assertEqual(r["level"], "warning")

    def test_unknown_string_still_degrades_to_info(self):
        r = build([entry(severity="not-a-label")])["runs"][0]["results"][0]
        self.assertEqual(r["properties"]["severity-label"], "info")


class TestSummary(unittest.TestCase):
    def test_counts_categories_and_mode(self):
        logs = [entry(), entry(result="pass"), entry(result="error"), entry(category="b")]
        md = to_sarif.build_summary(logs, "local")
        self.assertIn("(local mode)", md)
        self.assertIn("| 1 | 2 | 1 | 60/100 |", md)
        self.assertIn("`llm01`: 1", md)
        self.assertIn("`b`: 1", md)

    def test_label_severity_shown_as_label(self):
        md = to_sarif.build_summary([entry(severity="High")])
        self.assertIn("| 0 | 1 | 0 | high |", md)

    def test_empty_logs(self):
        md = to_sarif.build_summary([])
        self.assertIn("| 0 | 0 | 0 | 0/100 |", md)


class TestMainCLI(unittest.TestCase):
    def test_sarif_and_summary_in_one_invocation(self):
        out_sarif, out_sum = "/tmp/_sarif_main.sarif", "/tmp/_sarif_main_summary.md"
        Path(out_sum).write_text("")
        rc = to_sarif.main(
            [
                str(REPO_ROOT / "test" / "sample-results.json"),
                "--sarif", out_sarif,
                "--anchor", "test/bot-config.json",
                "--cli-version", "1.0.0",
                "--summary-append", out_sum,
                "--mode", "local",
            ]
        )
        self.assertEqual(rc, 0)
        sarif = json.loads(Path(out_sarif).read_text())
        self.assertEqual(len(sarif["runs"][0]["results"]), 3)
        self.assertIn("Humanbound security test results (local mode)", Path(out_sum).read_text())

    def test_summary_only_invocation(self):
        out_sum = "/tmp/_sarif_summary_only.md"
        Path(out_sum).write_text("")
        rc = to_sarif.main(
            [str(REPO_ROOT / "test" / "sample-results.json"), "--summary-append", out_sum]
        )
        self.assertEqual(rc, 0)
        self.assertIn("| Passed | Failed | Errors |", Path(out_sum).read_text())


if __name__ == "__main__":
    unittest.main()
