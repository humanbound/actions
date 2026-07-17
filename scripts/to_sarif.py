# SPDX-License-Identifier: Apache-2.0
"""Convert Humanbound JSON results into SARIF 2.1.0 and/or a job-summary table.

Usage:
    python to_sarif.py <results.json> --sarif OUT --anchor PATH [--cli-version V]
    python to_sarif.py <results.json> --summary-append FILE [--mode local|platform]

Both outputs can be requested in one invocation; they share a single parse.

`--anchor` is a repo-relative path every SARIF alert is attached to — Humanbound
findings are conversation-level, not line-level, so (like container/dependency
scanners) all alerts anchor to one file.

Reads the `{"logs": [...]}` shape emitted by `hb logs --format json`. Only
`result == "fail"` entries become SARIF alerts. Severity values may be numeric
(0-100, the local-engine shape) or label strings ("critical"/"high"/..., seen
in platform-side data) — both are handled.
"""

import argparse
import hashlib
import json
import sys

# Fallback boundaries, mirrored from the CLI (humanbound_cli/engine/schemas.py
# SEVERITY_LABEL_BOUNDARIES). The import below is preferred so the two can't
# drift; this list is used only when the CLI isn't importable.
SEVERITY_BOUNDARIES = [(75, "critical"), (50, "high"), (25, "medium"), (1, "low"), (0, "info")]

try:  # the action pip-installs the CLI before this script runs, in both modes
    from humanbound_cli.engine.schemas import severity_to_label as _cli_severity_to_label
except Exception:  # pragma: no cover - exercised only without the CLI installed
    _cli_severity_to_label = None

# SARIF has only error/warning/note/none; map label → level.
LABEL_TO_LEVEL = {
    "critical": "error",
    "high": "error",
    "medium": "warning",
    "low": "note",
    "info": "note",
}

# Representative GitHub security-severity for label-only severities
# (GitHub buckets: >=9.0 critical, 7.0-8.9 high, 4.0-6.9 medium, 0.1-3.9 low).
LABEL_TO_SCORE = {"critical": 9.5, "high": 7.5, "medium": 5.0, "low": 2.0, "info": 0.0}

# Ranking used by the summary's "max severity" when values are labels.
LABEL_RANK = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


def severity_label(severity):
    """Return (label, security_severity_str) for a numeric 0-100 or label-string severity."""
    if isinstance(severity, str):
        s = severity.strip().lower()
        if s in LABEL_TO_LEVEL:
            return s, f"{LABEL_TO_SCORE[s]:.1f}"
    try:
        val = float(severity or 0)
    except (TypeError, ValueError):
        return "info", "0.0"
    if _cli_severity_to_label is not None:
        label = _cli_severity_to_label(val)
        if label not in LABEL_TO_LEVEL:
            label = "info"
    else:
        label = "info"
        for threshold, name in SEVERITY_BOUNDARIES:
            if val >= threshold:
                label = name
                break
    return label, f"{val / 10.0:.1f}"


def load_logs(path):
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, dict):
        return data.get("logs", [])
    return data if isinstance(data, list) else []


def build_sarif(logs, anchor, cli_version):
    rules = {}
    results = []
    seen_fingerprints = {}

    for entry in logs:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("result", "")).lower() != "fail":
            continue

        rule_id = entry.get("fail_category") or "uncategorized"
        explanation = entry.get("explanation") or f"Failed check: {rule_id}"
        label, security_severity = severity_label(entry.get("severity"))

        if rule_id not in rules:
            rules[rule_id] = {
                "id": rule_id,
                "name": rule_id,
                "shortDescription": {"text": f"Humanbound finding: {rule_id}"},
                "fullDescription": {
                    "text": "Adversarial security finding from Humanbound agent testing."
                },
                "helpUri": "https://docs.humanbound.ai/",
                "properties": {
                    "security-severity": security_severity,
                    "tags": ["security", "ai-agent", "humanbound"],
                },
            }
        else:
            # GitHub buckets every result of a rule by the rule's security-severity,
            # so keep the worst severity seen for this category (safe over-flag).
            prior = float(rules[rule_id]["properties"]["security-severity"])
            if float(security_severity) > prior:
                rules[rule_id]["properties"]["security-severity"] = security_severity

        # Stable-ish alert identity across re-runs. Adversarial runs are
        # non-deterministic, so this is best-effort: identical (rule, message)
        # pairs within a run are disambiguated by an occurrence counter.
        base = f"{rule_id}|{explanation}"
        occ = seen_fingerprints.get(base, 0)
        seen_fingerprints[base] = occ + 1
        fingerprint = hashlib.sha256(f"{base}|{occ}".encode()).hexdigest()

        result = {
            "ruleId": rule_id,
            "level": LABEL_TO_LEVEL.get(label, "warning"),
            "message": {"text": explanation},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": anchor},
                        "region": {"startLine": 1},
                    }
                }
            ],
            "partialFingerprints": {"humanbound/v1": fingerprint},
            "properties": {
                "security-severity": security_severity,
                "severity-label": label,
                "severity-score": entry.get("severity"),
            },
        }
        thread_id = entry.get("thread_id")
        if thread_id:
            result["properties"]["thread_id"] = thread_id
        confidence = entry.get("confidence")
        if confidence is not None:
            result["properties"]["confidence"] = confidence

        results.append(result)

    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Humanbound",
                        "informationUri": "https://humanbound.ai",
                        "version": cli_version or "unknown",
                        "rules": list(rules.values()),
                    }
                },
                "results": results,
            }
        ],
    }


def build_summary(logs, mode=""):
    """Return the job-summary markdown for the run page."""
    totals = {"pass": 0, "fail": 0, "error": 0}
    by_category = {}
    max_numeric = 0.0
    max_label_rank = 0

    for entry in logs:
        if not isinstance(entry, dict):
            continue
        result = str(entry.get("result", "")).lower()
        if result in totals:
            totals[result] += 1
        if result == "fail":
            cat = entry.get("fail_category") or "uncategorized"
            by_category[cat] = by_category.get(cat, 0) + 1
        severity = entry.get("severity")
        if isinstance(severity, str) and severity.strip().lower() in LABEL_RANK:
            max_label_rank = max(max_label_rank, LABEL_RANK[severity.strip().lower()])
        else:
            try:
                max_numeric = max(max_numeric, float(severity or 0))
            except (TypeError, ValueError):
                pass

    if max_numeric > 0:
        max_display = f"{max_numeric:.0f}/100"
    elif max_label_rank > 0:
        max_display = next(k for k, v in LABEL_RANK.items() if v == max_label_rank)
    else:
        max_display = "0/100"

    mode_suffix = f" ({mode} mode)" if mode else ""
    lines = [
        f"## Humanbound security test results{mode_suffix}",
        "",
        "| Passed | Failed | Errors | Max severity |",
        "|---|---|---|---|",
        f"| {totals['pass']} | {totals['fail']} | {totals['error']} | {max_display} |",
    ]
    if by_category:
        lines += ["", "### Failures by category", ""]
        for cat, n in sorted(by_category.items(), key=lambda kv: -kv[1]):
            lines.append(f"- `{cat}`: {n}")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", help="path to the hb logs JSON export")
    parser.add_argument("--sarif", help="write SARIF 2.1.0 to this path")
    parser.add_argument("--anchor", help="repo-relative file URI for SARIF alert locations")
    parser.add_argument("--cli-version", default="", help="CLI version for the SARIF tool block")
    parser.add_argument("--summary-append", help="append the summary markdown to this file")
    parser.add_argument("--mode", default="", help="mode label shown in the summary heading")
    args = parser.parse_args(argv)

    if not args.sarif and not args.summary_append:
        parser.error("nothing to do: pass --sarif and/or --summary-append")
    if args.sarif and not args.anchor:
        parser.error("--sarif requires --anchor")

    logs = load_logs(args.results)

    if args.sarif:
        sarif = build_sarif(logs, args.anchor, args.cli_version)
        with open(args.sarif, "w") as f:
            json.dump(sarif, f, indent=2)
        n = len(sarif["runs"][0]["results"])
        print(f"Wrote {n} SARIF result(s) to {args.sarif} (anchor: {args.anchor})")

    if args.summary_append:
        with open(args.summary_append, "a") as f:
            f.write(build_summary(logs, args.mode))
        print(f"Appended summary to {args.summary_append}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
