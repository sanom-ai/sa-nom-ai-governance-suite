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
- provider_demo_flow.ollama.example.json: sanitized example output for the default private demo lane.
- legal_review_role_pack.example.json: sanitized example payload for the pilot-ready legal review role pack.
- hr_policy_role_pack.example.json: sanitized example payload for the pilot-ready HR policy role pack.
- purchasing_supplier_risk_role_pack.example.json: sanitized example payload for the pilot-ready purchasing supplier-risk role pack.
- finance_budget_variance_role_pack.example.json: sanitized example payload for the pilot-ready finance budget-variance role pack.
- finance_budget_variance_scenario.example.json: sanitized example output for the guided finance budget-variance scenario.
- accounting_close_exception_role_pack.example.json: sanitized example payload for the pilot-ready accounting close-readiness role pack.
- banking_treasury_control_role_pack.example.json: sanitized example payload for the pilot-ready banking and treasury control role pack.
- new_model_launch_readiness_role_pack.example.json: sanitized example payload for the pilot-ready NPI launch-readiness role pack.
- new_model_launch_readiness_scenario.example.json: sanitized example output for the guided NPI launch-readiness scenario.
- warehouse_material_shortage_role_pack.example.json: sanitized example payload for the pilot-ready warehouse material-shortage role pack.
- purchasing_supplier_risk_scenario.example.json: sanitized example output for the guided purchasing supplier-risk scenario.
- hr_policy_scenario.example.json: sanitized example output for the guided HR policy scenario.
- role_private_studio.example.json: sanitized example showing how an organization-specific hat can be created from Role Private Studio plus starter support.
- document_governance_role_pack.example.json: sanitized example payload for the public-safe Document Governance Coordination Lead role pack.

Use [../docs/OLLAMA_DEMO_ENVIRONMENT.md](../docs/OLLAMA_DEMO_ENVIRONMENT.md) and `python scripts/ollama_demo_environment.py` when you want a real local private-model setup path.

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
5. Inspect the real Ollama demo lane:
   - `python scripts/ollama_demo_environment.py`
6. Probe providers:
   - `python scripts/provider_smoke_test.py`
7. Run the end-to-end smoke test:
   - `python scripts/private_server_smoke_test.py`

Use [../docs/GUIDED_EVALUATION.md](../docs/GUIDED_EVALUATION.md) for the full first-run path and [../docs/TROUBLESHOOTING.md](../docs/TROUBLESHOOTING.md) if any validation step fails.

## Provider Demo Commands

- `python scripts/ollama_demo_environment.py`: inspect the real local Ollama daemon and model state before probing.
- `python scripts/ollama_demo_environment.py --probe`: build an Ollama environment report for the default private demo lane.
- `python scripts/provider_demo_flow.py --provider openai --probe`: build a demo artifact for an OpenAI lane.
- `python scripts/provider_demo_flow.py --provider anthropic --probe`: build a demo artifact for a Claude lane.
- `python scripts/provider_demo_flow.py --provider ollama --probe`: build a demo artifact for a local Ollama lane.
- provider_demo_flow.ollama.example.json: sanitized example output for the default private demo lane.
- legal_review_role_pack.example.json: sanitized example payload for the pilot-ready legal review role pack.
- hr_policy_role_pack.example.json: sanitized example payload for the pilot-ready HR policy role pack.
- purchasing_supplier_risk_role_pack.example.json: sanitized example payload for the pilot-ready purchasing supplier-risk role pack.
- finance_budget_variance_role_pack.example.json: sanitized example payload for the pilot-ready finance budget-variance role pack.
- finance_budget_variance_scenario.example.json: sanitized example output for the guided finance budget-variance scenario.
- accounting_close_exception_role_pack.example.json: sanitized example payload for the pilot-ready accounting close-readiness role pack.
- banking_treasury_control_role_pack.example.json: sanitized example payload for the pilot-ready banking and treasury control role pack.
- new_model_launch_readiness_role_pack.example.json: sanitized example payload for the pilot-ready NPI launch-readiness role pack.
- new_model_launch_readiness_scenario.example.json: sanitized example output for the guided NPI launch-readiness scenario.
- warehouse_material_shortage_role_pack.example.json: sanitized example payload for the pilot-ready warehouse material-shortage role pack.
- purchasing_supplier_risk_scenario.example.json: sanitized example output for the guided purchasing supplier-risk scenario.
- hr_policy_scenario.example.json: sanitized example output for the guided HR policy scenario.
- role_private_studio.example.json: sanitized example showing how an organization-specific hat can be created from Role Private Studio plus starter support.
- document_governance_role_pack.example.json: sanitized example payload for the public-safe Document Governance Coordination Lead role pack.

See [../docs/PROVIDER_SETUP.md](../docs/PROVIDER_SETUP.md) for provider configuration details, [../docs/OLLAMA_DEMO_ENVIRONMENT.md](../docs/OLLAMA_DEMO_ENVIRONMENT.md) for the real private-model setup path, and [../docs/DISCOVERY_DEMO.md](../docs/DISCOVERY_DEMO.md) for a short customer-demo flow.

