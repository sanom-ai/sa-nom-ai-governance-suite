# SA-NOM AI Governance Suite

[![CI](https://github.com/sanom-ai/sa-nom-ai-governance-suite/actions/workflows/ci.yml/badge.svg)](https://github.com/sanom-ai/sa-nom-ai-governance-suite/actions/workflows/ci.yml)
[![License: AGPL-3.0-only](https://img.shields.io/badge/License-AGPL%203.0--only-blue.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/sanom-ai/sa-nom-ai-governance-suite)](https://github.com/sanom-ai/sa-nom-ai-governance-suite/releases)

SA-NOM AI Governance Suite is an open-core governance and orchestration toolkit for teams that need structured policy control around AI-assisted operations.

The community baseline in this repository is designed for evaluation, internal deployment, and self-managed governance experiments on your own infrastructure.

## Why Teams Use SA-NOM

- Keep AI-assisted operations inside explicit governance, audit, and escalation boundaries.
- Model role authority and review flows with PTAG rather than leaving critical behavior implicit.
- Start self-managed under AGPL, then move into commercial rollout or enterprise support only if needed.

## Community Baseline

The public repository currently includes:
- PTAG parsing and validation
- governed request execution and audit chaining
- Role Private Studio authoring flows
- Human Ask escalation flows
- deployment readiness and operational health checks
- Docker and local private-server deployment paths

## Open-Core Model

This repository is published as the community baseline of SA-NOM under AGPL-3.0-only.

- Community: self-managed core runtime, dashboard, PTAG tooling, audit chain, deployment checks, examples, and local ops workflows
- Commercial: enterprise-only features, dedicated support, rollout hardening, compliance tailoring, custom integrations, and on-site enablement

If you run a modified networked version of this software, AGPL requires you to make the corresponding source available to users of that service. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

See [FEATURE_MATRIX.md](FEATURE_MATRIX.md) for the intended open-core boundary and [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md) for pricing and commercial terms.

## Start Here

Choose the path that matches your situation:
- Self-managed community path: start with the quick start below, review [DEPLOYMENT.md](DEPLOYMENT.md), and use the examples in `examples/`.
- Commercial path: review [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md), prepare [SALES_INTAKE_TEMPLATE.md](SALES_INTAKE_TEMPLATE.md), and contact `sanomaiarch@gmail.com`.

## Quick Start

### Local Python runtime

1. Use Python 3.12 or newer.
2. Create a local environment file from [`.env.production.example`](.env.production.example) or export the variables directly.
3. Register an organization owner:
   - `python register_owner.py --registration-code DEMO-ORG`
4. Generate delegated access profiles:
   - `python bootstrap_access_profiles.py --output _runtime/access_profiles.json --tokens-output _runtime/generated_access_tokens.json`
5. Run a startup validation:
   - `python dashboard_server.py --check-only`
6. Start the server:
   - `python run_private_server.py --host 127.0.0.1 --port 8080`

### Docker

1. Review [DEPLOYMENT.md](DEPLOYMENT.md).
2. Set the required environment variables.
3. Start the containerized runtime:
   - `docker compose up --build`

## Current Release

- Current public release: [v0.1.0](https://github.com/sanom-ai/sa-nom-ai-governance-suite/releases/tag/v0.1.0)
- Release notes: [RELEASE_NOTES_v0.1.0.md](RELEASE_NOTES_v0.1.0.md)
- Next roadmap: [ROADMAP_v0.1.1.md](ROADMAP_v0.1.1.md)
- Backlog seeds: [BACKLOG_SEEDS.md](BACKLOG_SEEDS.md)

## Public Docs

- [DEPLOYMENT.md](DEPLOYMENT.md): public deployment guide
- [FEATURE_MATRIX.md](FEATURE_MATRIX.md): community vs commercial boundary
- [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md): pricing, support tiers, and buying path
- [CONTRIBUTING.md](CONTRIBUTING.md): development workflow and contribution rules
- [SECURITY.md](SECURITY.md): vulnerability disclosure policy
- [TRADEMARKS.md](TRADEMARKS.md): brand and naming guidance
- [NOTICE](NOTICE): project-specific license, trademark, and commercial notice
- [SUPPORT.md](SUPPORT.md): community, commercial, and security contact path
- [ONE_PAGER.md](ONE_PAGER.md): concise product and commercial summary aligned with the public repo
- [OPEN_SOURCE_RELEASE_CHECKLIST.md](OPEN_SOURCE_RELEASE_CHECKLIST.md): launch checklist for publishing a clean public release
- [PUBLIC_UPLOAD_RUNBOOK.md](PUBLIC_UPLOAD_RUNBOOK.md): step-by-step upload procedure for the first public push
- [SALES_INTAKE_TEMPLATE.md](SALES_INTAKE_TEMPLATE.md): intake template for commercial inquiries

## Repository Layout

- Root: active runtime, dashboard, policy, and deployment code
- `_support/tests/`: regression tests and fixtures
- `_runtime/`: generated local runtime state only; do not commit real organization state
- `examples/`: sanitized example artifacts for documentation and onboarding
- `_review/`: local review outputs and handoff material

## Development

The open-source baseline currently runs on the Python standard library.

For contributor tooling:
- `python -m pip install -r requirements-dev.txt`
- `python -m pytest _support/tests`

GitHub Actions CI is configured in [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Security and Sensitive Data

- Never commit real `_runtime/` data, generated access tokens, or organization-specific secrets.
- Treat `_runtime/generated_access_tokens.json` as secret output.
- Use the files in `examples/` for documentation, demos, and onboarding.
- Report vulnerabilities privately to `sanomaiarch@gmail.com`.

## Commercial Path

Commercial licensing is intended for organizations that need one or more of the following:
- enterprise-only features or integration packs
- dedicated support or SLA-backed response expectations
- rollout, migration, or air-gapped deployment help
- compliance tailoring or government delivery support

Start with [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md) and email `sanomaiarch@gmail.com`.

