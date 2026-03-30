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
- provider probes for OpenAI, Claude, and Ollama
- Docker, Helm, Kubernetes, and local private-server deployment paths
- security audit and Thai regulated-deployment templates

## Open-Core Model

This repository is published as the community baseline of SA-NOM under AGPL-3.0-only.

- Community: self-managed core runtime, dashboard, PTAG tooling, audit chain, deployment checks, examples, and local ops workflows
- Commercial: enterprise-only features, dedicated support, rollout hardening, compliance tailoring, custom integrations, and on-site enablement

If you run a modified networked version of this software, AGPL requires you to make the corresponding source available to users of that service. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

See [FEATURE_MATRIX.md](FEATURE_MATRIX.md) for the intended open-core boundary and [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md) for pricing and commercial terms.

## Start Here

Choose the path that matches your situation:
- Guided evaluation path: follow [GUIDED_EVALUATION.md](GUIDED_EVALUATION.md) for the fastest first run.
- Self-managed community path: start with the quick start below, review [DEPLOYMENT.md](DEPLOYMENT.md), [TROUBLESHOOTING.md](TROUBLESHOOTING.md), and use the examples in `examples/`.
- Commercial path: review [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md), prepare [SALES_INTAKE_TEMPLATE.md](SALES_INTAKE_TEMPLATE.md), and contact `sanomaiarch@gmail.com`.

## Quick Start

### Local Python runtime

1. Use Python 3.14 or newer.
2. Create a local environment file from [`.env.production.example`](.env.production.example) or export the variables directly.
3. Register an organization owner:
   - `python register_owner.py --registration-code DEMO-ORG`
4. Generate delegated access profiles:
   - `python bootstrap_access_profiles.py --output _runtime/access_profiles.json --tokens-output _runtime/generated_access_tokens.json`
5. Run a startup validation:
   - `python dashboard_server.py --check-only`
6. Run the smoke tests:
   - `python private_server_smoke_test.py`
   - `python provider_smoke_test.py`
   - `provider_smoke_test.py` returning `disabled` is expected until a provider is configured
7. Build a provider-ready demo report when you want to validate one lane deeply:
   - `python provider_demo_flow.py --provider openai --probe`
8. Start the server:
   - `python run_private_server.py --host 127.0.0.1 --port 8080`

If startup validation or smoke tests fail, go to [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

### Docker

1. Review [DEPLOYMENT.md](DEPLOYMENT.md) and [KUBERNETES.md](KUBERNETES.md).
2. Set the required environment variables.
3. Start the containerized runtime:
   - `docker compose up --build`
4. If you want a local private-model lane with Ollama:
   - `docker compose --profile local-llm up --build`

## Current Release

- Current public release: [v0.1.0](https://github.com/sanom-ai/sa-nom-ai-governance-suite/releases/tag/v0.1.0)
- Release notes: [RELEASE_NOTES_v0.1.0.md](RELEASE_NOTES_v0.1.0.md)
- Next roadmap: [ROADMAP_v0.1.1.md](ROADMAP_v0.1.1.md)
- Backlog seeds: [BACKLOG_SEEDS.md](BACKLOG_SEEDS.md)

## Public Docs

- [GUIDED_EVALUATION.md](GUIDED_EVALUATION.md): fastest first-run path for evaluators
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md): recovery steps for common startup and provider issues
- [FAQ.md](FAQ.md): AGPL, self-hosting, and commercial-boundary answers
- [PROVIDER_SETUP.md](PROVIDER_SETUP.md): provider configuration, probe flow, and demo artifact path
- [DISCOVERY_DEMO.md](DISCOVERY_DEMO.md): short customer demo runbook for provider-backed evaluations
- [DEPLOYMENT.md](DEPLOYMENT.md): public deployment guide
- [KUBERNETES.md](KUBERNETES.md): Helm chart and raw Kubernetes deployment guide
- [FEATURE_MATRIX.md](FEATURE_MATRIX.md): community vs commercial boundary
- [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md): pricing, support tiers, and buying path
- [CONTRIBUTING.md](CONTRIBUTING.md): development workflow and contribution rules
- [SECURITY.md](SECURITY.md): vulnerability disclosure policy
- [SECURITY_AUDIT_CHECKLIST.md](SECURITY_AUDIT_CHECKLIST.md): production security and release checklist
- [TRADEMARKS.md](TRADEMARKS.md): brand and naming guidance
- [NOTICE](NOTICE): project-specific license, trademark, and commercial notice
- [SUPPORT.md](SUPPORT.md): community, commercial, and security contact path
- [templates/compliance/README.md](templates/compliance/README.md): Thai banking and government compliance starter templates
- [ONE_PAGER.md](ONE_PAGER.md): concise product and commercial summary aligned with the public repo
- [ONE_PAGER_TH.md](ONE_PAGER_TH.md): Thai one-pager for customer-facing sales conversations
- [OPEN_SOURCE_RELEASE_CHECKLIST.md](OPEN_SOURCE_RELEASE_CHECKLIST.md): launch checklist for publishing a clean public release
- [PUBLIC_UPLOAD_RUNBOOK.md](PUBLIC_UPLOAD_RUNBOOK.md): step-by-step upload procedure for the first public push
- [SALES_INTAKE_TEMPLATE.md](SALES_INTAKE_TEMPLATE.md): intake template for commercial inquiries
- [GITHUB_OPERATIONS_PLAYBOOK.md](GITHUB_OPERATIONS_PLAYBOOK.md): GitHub setup, milestone, label, and repo-positioning guidance
- [ISSUE_DRAFTS_v0.1.1.md](ISSUE_DRAFTS_v0.1.1.md): ready-to-use issue drafts for the first post-launch milestone

## Repository Layout

- `sa_nom_governance/`: main Python package grouped by domain (`api`, `audit`, `compliance`, `core`, `dashboard`, `deployment`, `guards`, `human_ask`, `integrations`, `ptag`, `studio`, `utils`)
- Root wrappers: compatibility entrypoints such as `dashboard_server.py`, `run_private_server.py`, and `provider_smoke_test.py`
- `_support/tests/`: regression tests and fixtures
- `_runtime/`: generated local runtime state only; do not commit real organization state
- `examples/`: sanitized example artifacts for documentation and onboarding
- `_review/`: local review outputs and handoff material

## Development

The open-source baseline currently runs on the Python standard library.

For contributor tooling:
- `python -m pip install -r requirements-dev.txt` or `python -m pip install -e .[dev]`
- `python -m pytest _support/tests`
- `python provider_smoke_test.py` when validating provider wiring

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

