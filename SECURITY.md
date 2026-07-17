# Security Policy

If you believe you have found a security vulnerability in this action,
please report it privately using one of the channels below.

## Reporting a vulnerability

**Please do not open a public GitHub Issue.** Report vulnerabilities via either:

- **Email:** [security@humanbound.ai](mailto:security@humanbound.ai)
- **GitHub Security Advisories:** the "Report a vulnerability" button on the
  Security tab of this repository

A clear report will include:

- A description of the issue and its impact
- Steps to reproduce (a minimal workflow file helps)
- Affected version/tag of the action

## What to expect

| Timeframe | Action |
|---|---|
| Within 72 hours | Acknowledgement that the report was received |
| As soon as practical | Coordinated fix, with credit to the reporter unless anonymity is preferred |

## Scope notes

This action executes the [Humanbound CLI](https://github.com/humanbound/humanbound)
inside your workflow. Vulnerabilities in the CLI or platform should be reported
to the same channels; issues specific to workflow wiring (input handling,
credential exposure, SARIF generation) belong here.
