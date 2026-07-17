<p align="center">
  <img src="https://raw.githubusercontent.com/humanbound/humanbound/main/assets/logo-dark.svg" alt="Humanbound" width="280"/>
</p>

<h3 align="center">Humanbound Test Action</h3>

<p align="center">
  Adversarial security testing for AI agents, on every push.
  <br/>
  Wraps <a href="https://github.com/humanbound/humanbound"><code>hb test</code></a> in a GitHub Action:
  OWASP agentic attacks, prompt injection, and behavioral checks —
  <br/>
  findings gate your build and land in GitHub's Security tab.
</p>

<p align="center">
  <a href="#usage">Usage</a> &middot;
  <a href="#scenarios">Scenarios</a> &middot;
  <a href="#security-tab-sarif">Security Tab</a> &middot;
  <a href="https://docs.humanbound.ai/">Documentation</a> &middot;
  <a href="#contributing">Contributing</a>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-FD9506?style=flat-square" alt="License"/></a>
  <a href="https://docs.humanbound.ai/"><img src="https://img.shields.io/badge/docs-humanbound.ai-FD9506?style=flat-square" alt="Docs"/></a>
  <a href="https://discord.gg/WgTMpmSFtN"><img src="https://img.shields.io/badge/discord-community-FD9506?style=flat-square" alt="Discord"/></a>
</p>

---

- **OWASP agentic attacks** — multi-turn prompt injection, data exfiltration, excessive agency, and more
- **A real quality gate** — `fail-on: high` turns findings into a red build
- **Findings in GitHub's Security tab** — [native SARIF output](#security-tab-sarif)
- **Results where you work** — severity summary on the workflow run page, full JSON as an artifact
- **Two ways to run** — local mode (no account, your LLM key) or platform mode (results in your Humanbound dashboard)

If this action is useful to you, a ⭐ on this repo and [humanbound/humanbound](https://github.com/humanbound/humanbound) helps others find it.

## Which mode?

The action auto-detects the mode from which credential you provide:

|                            | **Local mode**                    | **Platform mode**                                 |
| -------------------------- | --------------------------------- | ------------------------------------------------- |
| **Credential**             | `provider-api-key` (your LLM key) | `api-key` (Humanbound project key)                |
| **Where the engine runs**  | Inside the runner                 | On humanbound.ai                                  |
| **Who reaches your agent** | The runner (boot it in the job)   | Humanbound's servers (needs a public/staging URL) |
| **Attacker/judge LLM**     | Your key, in CI                   | A provider configured on the platform             |
| **Account needed**         | No                                | Yes (+ a project)                                 |
| **Results**                | CI artifact + run summary         | CI artifact + run summary + dashboard             |

> **Platform mode is coming soon.** Headless project-key auth is not yet released in the CLI; today the action supports **local mode**. The `api-key` input and platform path are wired and will light up when the CLI ships — your workflow won't need to change.

# Usage

<!-- start usage -->

```yaml
- uses: humanbound/hb-test@v1
  with:
    # LOCAL MODE credential. API key for the attacker/judge LLM provider
    # (maps to HB_API_KEY). Pass a repository secret. Setting this selects
    # local mode.
    provider-api-key: ''

    # PLATFORM MODE credential. Humanbound project API key (maps to
    # HUMANBOUND_API_KEY). Pass a repository secret. Setting this selects
    # platform mode. Provide exactly one of the two credentials.
    api-key: ''

    # Agent integration config — path to a JSON file (relative to the
    # workspace) or an inline JSON string. Same shape as `hb connect
    # --endpoint`. Required in local mode. Optional in platform mode
    # (defaults to the project's stored integration).
    endpoint: ''

    # LOCAL MODE. LLM provider used as attacker/judge: openai, anthropic,
    # ollama, ...
    # Default: openai
    provider: ''

    # LOCAL MODE. Model override for the attacker/judge LLM
    # (e.g. llama3.1:8b for ollama).
    model: ''

    # LOCAL MODE. Custom provider endpoint (e.g. a self-hosted ollama URL).
    provider-endpoint: ''

    # Test depth: quick | unit (~20 min) | system (~45 min) | acceptance (~90 min).
    # Note: quick currently runs at unit depth in the CLI (~20 min); a true
    # short scan is planned upstream.
    # Default: quick
    level: ''

    # Test category: humanbound/adversarial/owasp_agentic,
    # humanbound/adversarial/owasp_single_turn, humanbound/behavioral/qa.
    # Default: the CLI default (OWASP agentic)
    category: ''

    # Fail the job when findings of this severity (or higher) exist:
    # critical | high | medium | low | any. Empty string = report-only.
    # Default: high
    fail-on: ''

    # Path to a scope file (YAML/JSON with permitted/restricted intents)
    # so the judge knows what the agent is supposed to do.
    scope: ''

    # Path to the agent's system prompt file, used for scope extraction
    # (alternative to `scope`).
    system-prompt: ''

    # Repository path to scan for scope discovery (system prompts, tool
    # definitions). In CI, '.' scans the checked-out workspace.
    repo: ''

    # Extra context for the judge (string or path to a .txt file),
    # e.g. 'Authenticated as Alice, her PII is expected'.
    context: ''

    # Humanbound CLI version to install (e.g. 2.6.0).
    # Default: latest
    version: ''

    # Path where the JSON results export is written.
    # Default: humanbound-results.json
    results-file: ''

    # Path where SARIF is written for GitHub code scanning.
    # Empty string disables SARIF generation.
    # Default: humanbound.sarif
    sarif-file: ''
```

<!-- end usage -->

The agent integration config (`endpoint`) tells the tester bot how to call your agent — `$PROMPT` is replaced with each attack message; replies can be plain text or JSON (common content fields are detected automatically):

```json
{
  "streaming": null,
  "chat_completion": {
    "endpoint": "http://127.0.0.1:8000/chat",
    "headers": { "Authorization": "Bearer <your-agent-auth>" },
    "payload": { "content": "$PROMPT" }
  }
}
```

Full config reference — payload templating, `$CONVERSATION` for stateless agents, streaming/WebSocket agents, response extraction: [Agent Configuration](https://docs.humanbound.ai/getting-started/agent-config/).

# Scenarios

**Local mode** (works today, no account):

- [Quick PR gate](#quick-pr-gate)
- [Keep agent credentials in secrets](#keep-agent-credentials-in-secrets)
- [Teach the judge your agent's scope](#teach-the-judge-your-agents-scope)
- [Free local testing with Ollama](#free-local-testing-with-ollama)

**Platform mode** (coming soon — [see above](#which-mode)):

- [Platform PR gate](#platform-pr-gate)
- [Test a preview deployment against your project](#test-a-preview-deployment-against-your-project)

**Both modes & mixed setups:**

- [Security tab (SARIF)](#security-tab-sarif)
- [Choosing a test category](#choosing-a-test-category)
- [Nightly deep scan](#nightly-deep-scan)
- [Keep results as artifacts](#keep-results-as-artifacts)
- [Mixed: local gate on PRs, platform depth nightly](#mixed-local-gate-on-prs-platform-depth-nightly)

## Local mode

### Quick PR gate

Boot your agent inside the job, run the quick scan (currently ~20 min — `quick` is a CLI alias for `unit` today), fail on high-severity findings:

```yaml
jobs:
  security-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - run: docker compose up -d agent # or however your agent starts

      - uses: humanbound/hb-test@v1
        with:
          endpoint: ./bot-config.json
          provider-api-key: ${{ secrets.OPENAI_API_KEY }}
          level: quick
          fail-on: high
```

In local mode `localhost` means the runner itself, so start the agent in the job (a background process or [service container](https://docs.github.com/en/actions/using-containerized-services/about-service-containers)). The engine runs entirely in the runner — same orchestrators, attacks, and judge as the platform; see [Local Engine](https://docs.humanbound.ai/local-engine/) for how it works.

### Keep agent credentials in secrets

If your agent needs auth, don't commit a `bot-config.json` containing the token — generate the config in the job and inject the secret. Two equivalent ways:

**Inline JSON** (the `endpoint` input accepts JSON directly, not just a path):

```yaml
- uses: humanbound/hb-test@v1
  with:
    endpoint: >-
      {"streaming": null, "chat_completion": {"endpoint":
      "https://staging.my-agent.com/chat",
      "headers": {"Authorization": "Bearer ${{ secrets.AGENT_TOKEN }}"},
      "payload": {"content": "$PROMPT"}}}
    provider-api-key: ${{ secrets.OPENAI_API_KEY }}
```

**Or render the file in a step** — easier to read once headers grow (`jq` is preinstalled on runners, and passing secrets via `env:` keeps them out of the script text):

```yaml
- name: Render agent config
  env:
    AGENT_URL: ${{ vars.AGENT_URL }}
    AGENT_TOKEN: ${{ secrets.AGENT_TOKEN }}
  run: |
    jq -n --arg url "$AGENT_URL" --arg auth "Bearer $AGENT_TOKEN" \
      '{streaming: null, chat_completion: {endpoint: $url,
        headers: {Authorization: $auth}, payload: {content: "$PROMPT"}}}' \
      > bot-config.json

- uses: humanbound/hb-test@v1
  with:
    endpoint: ./bot-config.json
    provider-api-key: ${{ secrets.OPENAI_API_KEY }}
```

GitHub automatically masks secret values if they ever appear in logs, and the action never prints the config contents. The scope file rarely needs this treatment — permitted/restricted intents usually aren't secret, and versioning them with the agent is a feature — but the same render-a-file pattern works for `scope:` too, or skip the file entirely with `repo: .` / `system-prompt:` extraction.

### Teach the judge your agent's scope

Without scope, the judge only has generic security expectations. Telling it what your agent is _supposed_ to do produces targeted attacks and far fewer false positives — "agent processed a refund" is a finding for a weather bot and normal behavior for a support bot. Three ways, most precise first:

```yaml
# 1. Explicit scope file — most precise
- uses: humanbound/hb-test@v1
  with:
    endpoint: ./bot-config.json
    provider-api-key: ${{ secrets.OPENAI_API_KEY }}
    scope: ./scope.yaml

# 2. Scan the checked-out repo for system prompts and tool definitions
- uses: humanbound/hb-test@v1
  with:
    endpoint: ./bot-config.json
    provider-api-key: ${{ secrets.OPENAI_API_KEY }}
    repo: .

# 3. Point at the system prompt file directly
- uses: humanbound/hb-test@v1
  with:
    endpoint: ./bot-config.json
    provider-api-key: ${{ secrets.OPENAI_API_KEY }}
    system-prompt: ./prompts/system.txt
```

A scope file lists permitted and restricted intents:

```yaml
# scope.yaml
business_scope: 'Customer support for Acme Bank'
permitted:
  - Provide account balance and transaction info
  - Process routine transfers within limits
restricted:
  - Close accounts directly
  - Access internal system records
```

The `context` input adds run-specific judge context on top of any scope source — e.g. `context: 'Authenticated as Alice, her PII is expected'` stops "leaked Alice's data" false positives in an authenticated test session. Full details: [Scope Discovery](https://docs.humanbound.ai/local-engine/scope-discovery/).

These three scope inputs are **local-mode only** — in platform mode, scope is captured on the project when you run `hb connect` (the action warns if you set them there). `context` works in both modes.

### Free local testing with Ollama

No paid LLM key: run the attacker/judge on Ollama inside the job. This works on GitHub-hosted runners, with an honest caveat: they are CPU-only (4 vCPU on `ubuntu-latest`), so use a **small model** and expect the scan to take considerably longer than with a cloud provider — and [local models produce lower-quality attacks](https://docs.humanbound.ai/local-engine/provider-config/). Good for zero-cost smoke coverage; use a cloud key or a GPU self-hosted runner for serious scans.

```yaml
- name: Start Ollama
  run: |
    curl -fsSL https://ollama.com/install.sh | sh
    # The installer starts the server (systemd) on GitHub runners; start it
    # ourselves only if it isn't up, then wait until the API answers.
    pgrep -x ollama >/dev/null || (ollama serve &)
    for i in $(seq 1 30); do curl -sf http://127.0.0.1:11434/ >/dev/null && break; sleep 1; done
    ollama pull llama3.2:3b

- uses: humanbound/hb-test@v1
  with:
    endpoint: ./bot-config.json
    provider: ollama
    provider-api-key: unused # ollama needs no key; any value selects local mode
    model: llama3.2:3b
    provider-endpoint: http://127.0.0.1:11434
```

## Platform mode

> **Coming soon.** Headless project-key auth is not yet released in the CLI; the `api-key` input and platform path are wired and will light up when it ships — these workflows won't need to change.

For teams on [humanbound.ai](https://humanbound.ai): the engine runs server-side (no LLM key in CI) and results land in your dashboard with full experiment history. One-time setup at your terminal — [`hb connect --endpoint ./bot-config.json`](https://docs.humanbound.ai/getting-started/quick-start/#step-2-connect-your-agent) creates the project, extracts scope, and stores your agent config — then copy the project's API key into a repository secret.

Because the engine runs on humanbound.ai, your agent must be reachable from the internet (a staging or production URL) — a `localhost` agent booted in the job won't work in platform mode; use local mode for that.

### Platform PR gate

```yaml
- uses: humanbound/hb-test@v1
  with:
    api-key: ${{ secrets.HUMANBOUND_API_KEY }}
    # endpoint optional — defaults to the project's stored integration
    level: quick
    fail-on: high
```

No checkout, no agent boot, no LLM key: the project already knows how to reach your agent, and every run lands in the dashboard next to your test history.

### Test a preview deployment against your project

`endpoint` in platform mode _overrides_ the project's stored integration for that run — same project history, different target. Useful for per-PR preview environments:

```yaml
- uses: humanbound/hb-test@v1
  with:
    api-key: ${{ secrets.HUMANBOUND_API_KEY }}
    endpoint: >-
      {"streaming": null, "chat_completion": {"endpoint":
      "https://pr-${{ github.event.number }}.preview.example.com/chat",
      "headers": {}, "payload": {"content": "$PROMPT"}}}
    level: quick
    fail-on: high
```

## Both modes & mixed setups

### Security tab (SARIF)

Findings appear in **Security → Code scanning** with severity buckets and PR annotations. Add the upload step and its permission:

```yaml
permissions:
  contents: read
  security-events: write # required to upload SARIF

steps:
  - uses: actions/checkout@v4

  - uses: humanbound/hb-test@v1
    id: hb
    with:
      endpoint: ./bot-config.json
      provider-api-key: ${{ secrets.OPENAI_API_KEY }}
      fail-on: '' # report-only, so findings land as alerts, not red builds

  - uses: github/codeql-action/upload-sarif@v3
    # the != '' check matters: on an early failure the action has no SARIF to
    # output, and upload-sarif hard-fails on an empty sarif_file input
    if: always() && steps.hb.outputs.sarif-file != ''
    with:
      sarif_file: ${{ steps.hb.outputs.sarif-file }}
```

Humanbound findings are conversation-level, not line-level, so (like container and dependency scanners) every alert is anchored to one file — your agent config if it's in the repo, otherwise the workflow file. Set `sarif-file: ""` to disable SARIF entirely.

### Choosing a test category

Three built-in test engines (orchestrators), selected with `category`:

| Category                                         | What it does                                                  | When to use                    |
| ------------------------------------------------ | ------------------------------------------------------------- | ------------------------------ |
| `humanbound/adversarial/owasp_agentic` (default) | Multi-turn adversarial attacks with score-guided escalation   | The main security gate         |
| `humanbound/adversarial/owasp_single_turn`       | Single-prompt attacks at maximum strength — fast, high-volume | Quick, broad coverage          |
| `humanbound/behavioral/qa`                       | Intent boundaries, response quality, functional correctness   | "Does the agent stay on task?" |

```yaml
- uses: humanbound/hb-test@v1
  with:
    endpoint: ./bot-config.json
    provider-api-key: ${{ secrets.OPENAI_API_KEY }}
    category: humanbound/behavioral/qa
    fail-on: medium
```

More on how each engine works: [Orchestrators](https://docs.humanbound.ai/local-engine/orchestrators/).

### Nightly deep scan

Quick gate on PRs; deeper levels on a schedule:

```yaml
on:
  pull_request:
  schedule:
    - cron: '0 3 * * *'

jobs:
  security-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker compose up -d agent
      - uses: humanbound/hb-test@v1
        with:
          endpoint: ./bot-config.json
          provider-api-key: ${{ secrets.OPENAI_API_KEY }}
          level: ${{ github.event_name == 'schedule' && 'system' || 'quick' }}
          fail-on: high
```

### Keep results as artifacts

```yaml
- uses: humanbound/hb-test@v1
  id: hb
  with:
    endpoint: ./bot-config.json
    provider-api-key: ${{ secrets.OPENAI_API_KEY }}

- uses: actions/upload-artifact@v4
  if: always() && steps.hb.outputs.results-file != ''
  with:
    name: security-results
    path: ${{ steps.hb.outputs.results-file }}
```

### Mixed: local gate on PRs, platform depth nightly

The two modes complement each other: local mode tests the ephemeral agent you boot in the job (fast feedback, no public endpoint needed); platform mode tests your staging deployment nightly with results accumulating in the dashboard.

```yaml
on:
  pull_request:
  schedule:
    - cron: '0 3 * * *'

jobs:
  pr-gate:
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker compose up -d agent
      - uses: humanbound/hb-test@v1
        with:
          endpoint: ./bot-config.json
          provider-api-key: ${{ secrets.OPENAI_API_KEY }}
          level: quick
          fail-on: high

  nightly-platform:
    if: github.event_name == 'schedule'
    runs-on: ubuntu-latest
    steps:
      - uses: humanbound/hb-test@v1 # platform mode: coming soon
        with:
          api-key: ${{ secrets.HUMANBOUND_API_KEY }}
          level: system
          fail-on: high
```

# Recommended permissions

The action itself needs no special permissions. The jobs around it do:

```yaml
permissions:
  contents: read # checkout
  security-events: write # only if uploading SARIF to the Security tab
```

# Outputs

| Output         | Description                                                      |
| -------------- | ---------------------------------------------------------------- |
| `mode`         | Which mode ran: `local` or `platform`                            |
| `results-file` | Path to the JSON results (for `actions/upload-artifact`)         |
| `sarif-file`   | Path to the SARIF file (for `github/codeql-action/upload-sarif`) |

# Time & cost

Attacker/judge calls cost LLM tokens (your key in local mode; the platform's provider in platform mode). Levels: `quick` (currently equal to `unit`, ~20 min), `system` ~45 min, `acceptance` ~90 min — run the deep levels nightly, not on every PR.

# Contributing

Contributions welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) (DCO sign-off required). Bugs in `hb test` itself belong in the [CLI repo](https://github.com/humanbound/humanbound/issues); action wiring issues belong [here](https://github.com/humanbound/hb-test/issues). Security reports: [SECURITY.md](SECURITY.md), never a public issue. Release history: [CHANGELOG](CHANGELOG.md).

# License

The scripts and documentation in this project are released under the [Apache-2.0](LICENSE)
