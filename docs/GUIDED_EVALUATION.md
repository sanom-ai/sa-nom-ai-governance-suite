# Guided Evaluation

Use this path when you want to confirm the public community baseline quickly without wandering through every document first.

## Goal

Complete a first evaluation in about 10 to 15 minutes.
By the end you should have:
- an owner registration
- delegated access profiles
- a successful startup validation
- an optional Ollama environment report when you want the default private live-model lane
- an optional provider probe result when you want a live model lane
- a successful runtime smoke test

## Prerequisites

- Python 3.14 or newer
- a writable `_runtime/` directory
- local environment variables prepared from [`.env.production.example`](../.env.production.example)

## Fastest Path

Run:

- `python scripts/guided_smoke_test.py --registration-code DEMO-ORG`

Optional when Ollama is already available and you want a live private-model probe:

- `python scripts/guided_smoke_test.py --registration-code DEMO-ORG --probe`
- `python scripts/ollama_demo_environment.py`

Expected result:
- `_review/guided_smoke_test.json` is written
- public resources are available under `resources/`
- owner registration, delegated access profiles, and trusted registry artifacts exist
- startup readiness is reported inline
- runtime smoke completes end-to-end
- the provider guidance defaults to Ollama as the private demo lane
- you can compare the output with [../examples/guided_smoke_test.example.json](../examples/guided_smoke_test.example.json) and [../examples/runtime_startup_smoke.example.json](../examples/runtime_startup_smoke.example.json)

If you want to inspect each step manually, use the breakdown below.

## Step 1: Register The Executive Owner

Run:

- `python scripts/register_owner.py --registration-code DEMO-ORG`

Expected result:
- `_runtime/owner_registration.json` is created
- the command prints the normalized owner registration payload

Reference example:
- [../examples/owner_registration.example.json](../examples/owner_registration.example.json)

## Step 2: Generate Delegated Access Profiles

Run:

- `python scripts/bootstrap_access_profiles.py --output _runtime/access_profiles.json --tokens-output _runtime/generated_access_tokens.json`

Expected result:
- `_runtime/access_profiles.json` contains hashed profile entries
- `_runtime/generated_access_tokens.json` contains raw tokens for secure storage

Reference example:
- [../examples/access_profiles.example.json](../examples/access_profiles.example.json)

## Step 3: Refresh Trusted Registry Artifacts

Run:

- `python scripts/trusted_registry_refresh.py`

Expected result:
- trusted registry manifest and cache are regenerated from the current PTAG role packs

Reference example:
- [../examples/trusted_registry_manifest.example.json](../examples/trusted_registry_manifest.example.json)

## Step 4: Validate Startup Readiness

Run:

- `python scripts/dashboard_server.py --check-only`

Expected result:
- a JSON deployment-readiness report with `ready: true`

If this step fails, go directly to [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Step 5: Optional Provider Probe

Run:

- `python scripts/ollama_demo_environment.py`
- `python scripts/provider_smoke_test.py`

Expected results:
- `scripts/ollama_demo_environment.py` tells you whether the Ollama daemon is reachable and whether the requested model is already installed
- `status: disabled` from `scripts/provider_smoke_test.py` is acceptable if no provider has been configured yet
- or a provider report if a provider lane is configured

Recommended default private demo lane:
- [../examples/.env.ollama.example](../examples/.env.ollama.example)

Optional hosted evaluation lanes:
- [../examples/.env.openai.example](../examples/.env.openai.example)
- [../examples/.env.claude.example](../examples/.env.claude.example)
- [../examples/provider_demo_flow.ollama.example.json](../examples/provider_demo_flow.ollama.example.json) shows the default private demo-lane output shape
- use [OLLAMA_DEMO_ENVIRONMENT.md](OLLAMA_DEMO_ENVIRONMENT.md) when you want a real local private-model path before the provider probe

## Step 6: Run The Runtime Smoke Test

Run:

- `python scripts/private_server_smoke_test.py`

Expected result:
- the runtime path passes end-to-end
- a provider warning is acceptable if no provider is configured yet

## Step 7: Start The Local Server

Run:

- `python scripts/run_private_server.py --host 127.0.0.1 --port 8080`

At this point the community baseline is operational for local evaluation.

## Success Checklist

You are in a good evaluation state if all of the following are true:
- `scripts/guided_smoke_test.py` returns a passing JSON report or writes `_review/guided_smoke_test.json`
- `scripts/register_owner.py` created the owner registration file
- `scripts/bootstrap_access_profiles.py` created hashed profiles successfully
- `scripts/dashboard_server.py --check-only` reports `ready: true`
- `scripts/ollama_demo_environment.py` clearly reports what is missing for a real private-model lane
- `scripts/provider_smoke_test.py` is either configured successfully or clearly reports `disabled` when you have not enabled a provider yet
- `scripts/private_server_smoke_test.py` passes

## Private Rule Studio Path

If you want to evaluate how SA-NOM handles organization-specific hats instead of only standard packs, use the platform as follows:

- enter `Private Rule Studio` with your own JD or operating brief
- start from a starter JD, starter rule set, or starter hat prepared by SA-NOM when you want a faster starting point
- adapt that material into a `Private Rule Position` that matches your own organization
- then move that governed position into the broader role-publication flow

Reference:
- [PRIVATE_RULE_POSITION.md](PRIVATE_RULE_POSITION.md)
- [../examples/private_rule_position.example.json](../examples/private_rule_position.example.json)

## Next Steps

- For deployment details: [DEPLOYMENT.md](DEPLOYMENT.md)
- For Helm and Kubernetes: [KUBERNETES.md](KUBERNETES.md)
- For startup failures: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- For licensing and commercial questions: [FAQ.md](FAQ.md) and [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md)
- For a pilot-ready use-case pack: [LEGAL_REVIEW_ROLE_PACK.md](LEGAL_REVIEW_ROLE_PACK.md)
- For a second pilot-ready use-case pack: [HR_POLICY_ROLE_PACK.md](HR_POLICY_ROLE_PACK.md)
- For a procurement-focused pilot-ready pack: [PURCHASING_SUPPLIER_RISK_ROLE_PACK.md](PURCHASING_SUPPLIER_RISK_ROLE_PACK.md)
- For a procurement workflow story: [PURCHASING_SUPPLIER_RISK_SCENARIO.md](PURCHASING_SUPPLIER_RISK_SCENARIO.md)
- For a finance-focused pilot-ready pack: [FINANCE_BUDGET_VARIANCE_ROLE_PACK.md](FINANCE_BUDGET_VARIANCE_ROLE_PACK.md)
- For a finance workflow story: [FINANCE_BUDGET_VARIANCE_SCENARIO.md](FINANCE_BUDGET_VARIANCE_SCENARIO.md)
- For an accounting-focused pilot-ready pack: [ACCOUNTING_CLOSE_EXCEPTION_ROLE_PACK.md](ACCOUNTING_CLOSE_EXCEPTION_ROLE_PACK.md)
- For a bank-facing treasury control pack: [BANKING_TREASURY_CONTROL_ROLE_PACK.md](BANKING_TREASURY_CONTROL_ROLE_PACK.md)
- For an NPI and launch-readiness pack: [NEW_MODEL_LAUNCH_READINESS_ROLE_PACK.md](NEW_MODEL_LAUNCH_READINESS_ROLE_PACK.md)
- For an NPI workflow story: [NEW_MODEL_LAUNCH_READINESS_SCENARIO.md](NEW_MODEL_LAUNCH_READINESS_SCENARIO.md)
- For a warehouse shortage pack: [WAREHOUSE_MATERIAL_SHORTAGE_ROLE_PACK.md](WAREHOUSE_MATERIAL_SHORTAGE_ROLE_PACK.md)
- For a production line-exception pack: [PRODUCTION_LINE_EXCEPTION_ROLE_PACK.md](PRODUCTION_LINE_EXCEPTION_ROLE_PACK.md)
- For a guided production workflow story: [PRODUCTION_LINE_EXCEPTION_SCENARIO.md](PRODUCTION_LINE_EXCEPTION_SCENARIO.md)
- For a QC QA and audit-ready quality pack: [QUALITY_AUDIT_READINESS_ROLE_PACK.md](QUALITY_AUDIT_READINESS_ROLE_PACK.md)
- For a guided QC QA and audit workflow story: [QUALITY_AUDIT_READINESS_SCENARIO.md](QUALITY_AUDIT_READINESS_SCENARIO.md)
- For a delivery release pack: [DELIVERY_READINESS_ROLE_PACK.md](DELIVERY_READINESS_ROLE_PACK.md)
- For a first role-based scenario: [LEGAL_REVIEW_SCENARIO.md](LEGAL_REVIEW_SCENARIO.md)
- For an HR policy workflow story: [HR_POLICY_SCENARIO.md](HR_POLICY_SCENARIO.md)



