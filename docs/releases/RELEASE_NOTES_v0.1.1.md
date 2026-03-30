# Release Notes - v0.1.1

## Release Focus

This release hardens SA-NOM AI Governance Suite into a stronger public community baseline for governed AI operations, provider-backed evaluation, and self-managed deployment in production-like environments.

## Highlights

- Refactored the codebase into the `sa_nom_governance` package layout organized by domain
- Added provider integration and evaluation support for OpenAI, Claude, and Ollama
- Added `scripts/provider_demo_flow.py` plus operator-facing provider setup and discovery-demo guides
- Added Helm chart and Kubernetes manifests for self-managed deployment paths
- Added security audit guidance and Thai banking / government compliance starter templates
- Expanded evaluator onboarding with troubleshooting, FAQ, and guided evaluation docs
- Repositioned public docs so SA-NOM is presented as governed AI operations, not only as an AI governance utility
- Kept protected-branch and CI workflows aligned with the documented Python 3.14 baseline

## Community Baseline In This Release

- PTAG parsing and validation
- governed runtime execution and decision flow
- audit chain and evidence-oriented execution paths
- Role Private Studio workflows
- Human Ask workflows
- provider smoke and demo-readiness flows
- deployment readiness checks
- Docker, Helm, Kubernetes, and local private-server paths
- security and compliance starter templates for regulated environments

## Commercial Direction

Commercial offerings remain separate from the AGPL community baseline and may include rollout support, enterprise controls, tailored compliance programs, air-gapped delivery, and custom integrations.

See [../COMMERCIAL_LICENSE.md](../COMMERCIAL_LICENSE.md) for the current commercial positioning.

## Upgrade Notes

- The repository now uses the `sa_nom_governance` package layout as the primary code organization model
- Root entrypoints such as `scripts/dashboard_server.py`, `scripts/run_private_server.py`, `scripts/provider_smoke_test.py`, and `scripts/provider_demo_flow.py` remain available as compatibility wrappers
- The documented validation baseline now assumes Python 3.14
- Provider probes may return `disabled` until real credentials or local-model endpoints are configured

## Verification Snapshot

Validated during `v0.1.1` release preparation with:
- `python -m compileall -q .`
- `python -m pytest _support/tests`
- `python scripts/dashboard_server.py --check-only`
- `python scripts/private_server_smoke_test.py`
- `python scripts/provider_smoke_test.py`
- `python scripts/provider_demo_flow.py`

## Post-Release Follow-Up

Recommended next steps after `v0.1.1`:
- publish the `v0.1.1` GitHub release with these notes
- configure real provider credentials or local endpoints for demo environments
- convert roadmap items and follow-up polish into issue-driven work for the next milestone
- keep `_runtime/` data private and continue using `examples/` for public demonstrations

## Contact

- Community/commercial/security contact: `sanomaiarch@gmail.com`
