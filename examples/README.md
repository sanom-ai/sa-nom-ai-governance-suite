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
- `access_profiles.example.json`: hashed delegated access profile structure.
- `trusted_registry_manifest.example.json`: trusted-registry manifest shape after a refresh.

## Suggested Evaluation Order

1. Register an owner:
   - `python register_owner.py --registration-code DEMO-ORG`
2. Generate delegated access:
   - `python bootstrap_access_profiles.py --output _runtime/access_profiles.json --tokens-output _runtime/generated_access_tokens.json`
3. Refresh the trusted registry:
   - `python trusted_registry_refresh.py`
4. Validate startup:
   - `python dashboard_server.py --check-only`
5. Probe providers:
   - `python provider_smoke_test.py`
6. Run the end-to-end smoke test:
   - `python private_server_smoke_test.py`

Use [GUIDED_EVALUATION.md](../GUIDED_EVALUATION.md) for the full first-run path and [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) if any validation step fails.

## Provider Demo Commands

- `python provider_demo_flow.py --provider openai --probe`: build a demo artifact for an OpenAI lane.
- `python provider_demo_flow.py --provider anthropic --probe`: build a demo artifact for a Claude lane.
- `python provider_demo_flow.py --provider ollama --probe`: build a demo artifact for a local Ollama lane.

See [PROVIDER_SETUP.md](../PROVIDER_SETUP.md) for provider configuration details and [DISCOVERY_DEMO.md](../DISCOVERY_DEMO.md) for a short customer-demo flow.
