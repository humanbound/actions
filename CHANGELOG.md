# Changelog

All notable changes to this action are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [SemVer](https://semver.org/).
Users pin the moving major tag (`v1`) or an exact release (`v1.0.0`).

## [Unreleased]

## [1.0.0] - 2026-07-17

### Added

- Initial release of the Humanbound GitHub Action.
- **Local mode**: run `hb test --local` against your agent with your own LLM
  provider key (`provider-api-key`) — no Humanbound account required.
- **Platform mode (gated)**: `api-key` input reserved for Humanbound project-key
  auth; errors with a clear message until headless auth ships in the CLI.
- Mode auto-detection from which credential input is provided.
- `fail-on` severity gate (default `high`) mapping findings to the job's exit code.
- JSON results export (`results-file` output) for `actions/upload-artifact`.
- **SARIF 2.1.0 output** (`sarif-file` output) for GitHub code scanning /
  Security tab via `github/codeql-action/upload-sarif`.
- Severity summary table on the workflow run page.
- Test depth levels: `quick` (currently a CLI alias for `unit`), `unit` (~20 min),
  `system` (~45 min), `acceptance` (~90 min).
- SARIF and job summary share one tested parser (`scripts/to_sarif.py`), which
  handles both numeric and label-string severities.
