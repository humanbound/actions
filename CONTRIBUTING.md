# Contributing to hb-test

Thanks for your interest in improving the Humanbound GitHub Action.

## Quick orientation

This is a **composite action** — there is no build step and no `dist/`:

| Path | What it is |
|---|---|
| `action.yml` | The action itself: inputs, mode detection, CLI invocation, exports |
| `scripts/to_sarif.py` | JSON results → SARIF 2.1.0 transform (stdlib only) |
| `test/mock-agent.py` | Minimal agent used by the e2e workflow |
| `test/sample-results.json` | Fixture for the SARIF tests |
| `test/test_to_sarif.py` | Unit tests for the SARIF transform |
| `.github/workflows/ci.yml` | lint · sarif · smoke on every PR; e2e on main |

## Developing

- Edit `action.yml` / `scripts/` directly; no compilation.
- Validate YAML locally: `python -c "import yaml; yaml.safe_load(open('action.yml'))"`
- Run the test suite (stdlib only, no install):
  `python3 -m unittest discover -s test -v`
- Exercise the SARIF transform manually:
  `python scripts/to_sarif.py test/sample-results.json --sarif out.sarif --anchor test/bot-config.json`
- The e2e job needs an `OPENAI_API_KEY` repo secret and only runs on pushes to
  `main` — PRs stay green without it.

### Testing the action without pushing to GitHub

- **Static + unit** (instant, free): the YAML/bash checks above plus
  `python3 -m unittest discover -s test`.
- **Full fidelity with [act](https://github.com/nektos/act)** (needs Docker):
  runs the actual workflows in a runner-like container:

  ```bash
  act push -W .github/workflows/ci.yml -j lint    # or -j sarif / -j smoke
  act push -j e2e -s OPENAI_API_KEY=sk-...        # the real thing, costs tokens
  ```

Keep `scripts/to_sarif.py` dependency-free (Python stdlib only): it runs inside
users' workflows, and every dependency would become their dependency.

## Pull requests

- Target `main`. Small, focused PRs review fastest.
- Describe the user-visible behavior change; update `README.md` and
  `CHANGELOG.md` in the same PR when behavior changes.
- New inputs need: a description in `action.yml`, a row in the README inputs
  table, and validation in the "Detect mode" step if they're mode-dependent.

## Releasing (maintainers)

Same flow as the CLI repo — a release PR, then a tag; automation does the rest:

1. **Release PR**: branch `chore/release-v1.1.0`; in `CHANGELOG.md` rename
   `## [Unreleased]` to `## [1.1.0] - YYYY-MM-DD` and add a fresh empty
   `## [Unreleased]` above it. Commit as
   `chore(release): date CHANGELOG for v1.1.0` (signed off), open a PR, merge.
2. **Tag the merge commit**:

   ```bash
   git checkout main && git pull
   git tag v1.1.0 && git push origin v1.1.0
   ```

3. **`release.yml` does the rest**: creates the GitHub Release with the
   `[1.1.0]` CHANGELOG section as the notes (auto-generated notes as fallback),
   and force-moves the `v1` major tag so `@v1` users get the release.

Marketplace note: the **first** listing is manual (draft the release in the UI
once, tick "Publish this Action to the GitHub Marketplace", accept the
agreement). After that, verify a workflow-created release shows up on the
listing — if a version doesn't appear, edit the release in the UI and tick the
Marketplace checkbox.

## Developer Certificate of Origin (DCO) — required

Contributions must be signed off under the
[Developer Certificate of Origin](./DCO.md) — the same
mechanism used across Humanbound repositories. Every commit needs a
`Signed-off-by` trailer:

```bash
git commit -s -m "fix: ..."
```

Forgot one? `git commit --amend -s` (or `git rebase --signoff main` for a whole
branch) and force-push. CI enforces this on every PR.

## Reporting issues

- Bugs and feature requests: [GitHub Issues](https://github.com/humanbound/hb-test/issues)
- Security vulnerabilities: see [SECURITY.md](SECURITY.md) — never a public issue
