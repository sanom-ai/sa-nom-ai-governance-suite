# Release Notes - v0.1.3

## Release Focus

This release turns the default private Ollama demo lane into a more operational, repeatable setup by adding a concrete environment helper and validating the full SA-NOM runtime path against a real local Ollama model.

## Highlights

- Added an Ollama demo-environment helper to show daemon reachability, model presence, compose commands, and next actions in one place
- Added dedicated Ollama demo-environment documentation and connected it to the main README, guided evaluation, provider setup, and discovery demo docs
- Kept Ollama as the default private demo lane while preserving OpenAI and Claude as optional hosted evaluation lanes
- Validated the full local private demo flow on a real machine using `gemma3:1b`

## Community Baseline In This Release

- environment-level helper via `python scripts/ollama_demo_environment.py`
- private-first provider guidance that points operators at a real local-model workflow instead of a docs-only setup
- clearer next-step commands for provider probes, smoke tests, compose startup, and full runtime validation
- updated docs so first-time evaluators can move from repo read-through to a working private demo lane faster

## Commercial Direction

Commercial offerings remain separate from the AGPL community baseline and may include rollout support, enterprise controls, tailored compliance programs, air-gapped delivery, and custom integrations.

See [../COMMERCIAL_LICENSE.md](../COMMERCIAL_LICENSE.md) for the commercial model and [../COMMERCIAL_DISCOVERY_CHECKLIST.md](../COMMERCIAL_DISCOVERY_CHECKLIST.md) for the first qualified discovery path.

## Upgrade Notes

- Ollama remains the default private demo lane and now has a dedicated environment helper at `python scripts/ollama_demo_environment.py`
- The recommended local private demo model has been validated with `gemma3:1b`
- OpenAI and Claude remain optional hosted evaluation lanes for teams that want that tradeoff
- The fastest private verification path is now:
  - `python scripts/ollama_demo_environment.py`
  - `python scripts/provider_demo_flow.py --provider ollama --probe`
  - `python scripts/private_server_smoke_test.py`

## Verification Snapshot

Validated during `v0.1.3` release preparation with:
- `python -m compileall -q .`
- `python -m pytest _support/tests`
- `python scripts/ollama_demo_environment.py`
- `python scripts/dashboard_server.py --check-only`
- `python scripts/provider_demo_flow.py --provider ollama --probe`
- `python scripts/provider_smoke_test.py --provider ollama`
- `python scripts/private_server_smoke_test.py`

Local runtime verification on this machine used:
- `SANOM_MODEL_PROVIDER_DEFAULT=ollama`
- `SANOM_OLLAMA_MODEL=gemma3:1b`
- Ollama daemon reachable at `http://localhost:11434`

## Post-Release Follow-Up

Recommended next steps after `v0.1.3`:
- publish the `v0.1.3` GitHub release with these notes
- persist the local Ollama demo configuration for repeatable customer walkthroughs
- expand the discovery demo script so it can narrate the live local-model path end to end
- continue adding production-oriented examples and operational runbooks around the private default lane

## Contact

- Community/commercial/security contact: `sanomaiarch@gmail.com`
