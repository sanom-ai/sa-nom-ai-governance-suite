# Release Notes - v0.1.2

## Release Focus

This release makes SA-NOM easier to evaluate, demo, and qualify as a private AI operations platform without losing the governance and compliance posture established in `v0.1.1`.

## Highlights

- Made Ollama the default private demo lane while keeping OpenAI and Claude as optional hosted evaluation lanes
- Restructured the repository root into clearer `docs/`, `scripts/`, and `resources/` surfaces
- Added a one-command guided smoke-test path for first-time evaluators
- Added visual README product-tour diagrams plus a dedicated operator walkthrough
- Added a commercial discovery checklist to move serious prospects into qualified next steps
- Expanded the public-safe example catalog with realistic output-shaped artifacts

## Community Baseline In This Release

- guided evaluator entrypoint via `python scripts/guided_smoke_test.py --registration-code DEMO-ORG`
- private-first provider positioning with Ollama as the recommended demo lane
- cleaner repository layout for operators, contributors, and release workflows
- product-tour and discovery docs for faster first-read comprehension
- public-safe example outputs for startup validation, delegated access, guided smoke, and provider demos
- commercial qualification docs that connect repo evaluation to guided rollout conversations

## Commercial Direction

Commercial offerings remain separate from the AGPL community baseline and may include rollout support, enterprise controls, tailored compliance programs, air-gapped delivery, and custom integrations.

See [../COMMERCIAL_LICENSE.md](../COMMERCIAL_LICENSE.md) for the commercial model and [../COMMERCIAL_DISCOVERY_CHECKLIST.md](../COMMERCIAL_DISCOVERY_CHECKLIST.md) for the first qualified discovery path.

## Upgrade Notes

- Operator commands now live under `scripts/` and repository docs now live under `docs/`
- Packaged role packs, manifests, and public-safe resources now live under `resources/`
- The fastest first-run path is now `python scripts/guided_smoke_test.py --registration-code DEMO-ORG`
- Ollama is the default private demo lane when no hosted provider is configured
- OpenAI and Claude remain optional hosted evaluation lanes for teams that want that tradeoff

## Verification Snapshot

Validated during `v0.1.2` release preparation with:
- `python -m compileall -q .`
- `python -m pytest _support/tests`
- `python scripts/guided_smoke_test.py`
- `python scripts/dashboard_server.py --check-only`
- `python scripts/private_server_smoke_test.py`
- `python scripts/provider_demo_flow.py`

## Post-Release Follow-Up

Recommended next steps after `v0.1.2`:
- publish the `v0.1.2` GitHub release with these notes
- set up a real local Ollama demo environment for customer-facing walkthroughs and then run `python scripts/provider_demo_flow.py --provider ollama --probe`
- turn the new commercial discovery checklist into issue-driven sales and demo workflow improvements
- continue expanding production-oriented examples, demos, and operator onboarding for the next milestone

## Contact

- Community/commercial/security contact: `sanomaiarch@gmail.com`

