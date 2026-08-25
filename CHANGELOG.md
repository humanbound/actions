# Changelog

All notable changes to this action are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [SemVer](https://semver.org/).
Users pin the moving major tag (`v1`) or an exact release (`v1.0.0`).

## [Unreleased]

### Changed
- Discord links in `README.md` and the new-issue chooser now use
  `discord.gg/QFTD6tr9zu` (#9), which opens in `#start-here` and matches
  www.humanbound.ai. The previous invite still works but lands in `#general`.

## [1.2.0] - 2026-07-30

### Added

- **Platform mode is now available.** `api-key` accepts a Humanbound **user** API
  key (`hb_…` from `hb api-keys create`), which authenticates headlessly via the
  `x-api-key` header — no `hb login`, no browser. Results land in your dashboard.
- `org-id` and `project-id` inputs (mapping to `HUMANBOUND_ORG_ID` and
  `HUMANBOUND_PROJECT_ID`). Both are required in platform mode: a headless run has
  no stored selection, and the results export resolves the organisation from
  `org-id`. `project-id` is validated in the detect step, so a missing value fails
  before the CLI is installed.

### Changed

- The `version` input now defaults to `2.8.0` — the CLI release that adds headless
  `HUMANBOUND_API_KEY` auth, and the release this action is tested against.
  Platform mode requires it; the action checks the installed version and fails with
  a clear message on older releases.
- `api-key` is documented as a **user** API key, not a project key — they are
  different credentials.

### Removed

- The "platform mode is coming soon" gate. Platform mode previously exited with an
  error regardless of inputs; it now runs.

## [1.1.0] - 2026-07-20

### Changed

- The `version` input now defaults to `2.6.0` — the CLI release this action is
  tested against — instead of installing the latest published release. Set
  `version: ""` to opt back into the latest release.
- Local mode now **requires an explicit `model`** for every provider except
  ollama, enforced with a clear error in the detect step — the current CLI
  crashes with `KeyError: 'model'` when none is set (its docs call the model
  optional, but no provider default is implemented). All README examples now
  include `model: gpt-4.1`. The check will be relaxed once a CLI release ships
  provider defaults.

### Security

- Pinned every third-party and first-party GitHub Action used in the workflows
  to a full commit SHA (with a version comment), so a moved tag cannot inject
  code between Dependabot updates. Grouped Dependabot action updates into a
  single weekly PR.

### Added

- CI now validates every `action.yml` in the repository (the root action plus
  any future subdirectory action).

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
