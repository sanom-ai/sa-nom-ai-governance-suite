# Examples

This folder contains sanitized example artifacts for documentation and onboarding.

These files are not production-ready secrets or signed deployment outputs.
Use them as templates and replace every placeholder before a real deployment.

## Provider Examples

- `.env.openai.example`: Hosted OpenAI provider settings using the Responses API.
- `.env.claude.example`: Hosted Anthropic Claude provider settings using the Messages API.
- `.env.ollama.example`: Local Ollama provider settings for private inference.
- `helm-values.production.example.yaml`: Example Helm values for a production-style private deployment.

## Core Onboarding Examples

- `owner_registration.example.json`: executive-owner registration shape for a fresh evaluation.
- `access_profiles.example.json`: hashed delegated access profile structure aligned with the current enterprise profile ids.
- `generated_access_tokens.example.json`: sanitized token-bundle shape that shows how raw delegated tokens are exported.
- `trusted_registry_manifest.example.json`: trusted-registry manifest shape after a refresh.
- `guided_smoke_test.example.json`: example output from the one-command guided evaluator flow.
- `runtime_startup_smoke.example.json`: example end-to-end smoke report written to `_runtime/runtime_startup_smoke.json`.
- `provider_demo_flow.ollama.example.json`: example provider-demo output for the default private Ollama lane.

## Suggested Evaluation Order

Fastest first run:
- `python scripts/guided_smoke_test.py --registration-code DEMO-ORG`
- This creates the owner registration, access profiles, trusted registry artifacts, startup report, and runtime smoke result in one pass.
- Compare the output with `guided_smoke_test.example.json` and `runtime_startup_smoke.example.json` if you want to sanity-check the expected shape before running locally.

Manual order if you want to inspect each artifact:
1. Register an owner:
   - `python scripts/register_owner.py --registration-code DEMO-ORG`
2. Generate delegated access:
   - `python scripts/bootstrap_access_profiles.py --output _runtime/access_profiles.json --tokens-output _runtime/generated_access_tokens.json`
3. Refresh the trusted registry:
   - `python scripts/trusted_registry_refresh.py`
4. Validate startup:
   - `python scripts/dashboard_server.py --check-only`
5. Probe providers:
   - `python scripts/provider_smoke_test.py`
6. Run the end-to-end smoke test:
   - `python scripts/private_server_smoke_test.py`

Use [../docs/GUIDED_EVALUATION.md](../docs/GUIDED_EVALUATION.md) for the full first-run path and [../docs/TROUBLESHOOTING.md](../docs/TROUBLESHOOTING.md) if any validation step fails.

## Provider Demo Commands

- `python scripts/provider_demo_flow.py --provider openai --probe`: build a demo artifact for an OpenAI lane.
- `python scripts/provider_demo_flow.py --provider anthropic --probe`: build a demo artifact for a Claude lane.
- `python scripts/provider_demo_flow.py --provider ollama --probe`: build a demo artifact for a local Ollama lane.
- `provider_demo_flow.ollama.example.json`: sanitized example output for the default private demo lane.

See [../docs/PROVIDER_SETUP.md](../docs/PROVIDER_SETUP.md) for provider configuration details and [../docs/DISCOVERY_DEMO.md](../docs/DISCOVERY_DEMO.md) for a short customer-demo flow.
