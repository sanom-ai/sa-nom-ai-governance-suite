# Discovery Demo

Use this runbook for a short customer or stakeholder demo of the community baseline.

For a sales-led live talk track using the default private Ollama lane, see [LIVE_CUSTOMER_WALKTHROUGH.md](LIVE_CUSTOMER_WALKTHROUGH.md).

## Demo Goal

Show that SA-NOM can:
- stay inside explicit governance boundaries
- prove deployment readiness before go-live
- validate a real model-provider lane
- run on private infrastructure with a clear operator path

## Before The Call

Prepare:
- a passing guided smoke report from `python scripts/guided_smoke_test.py --registration-code DEMO-ORG`
- owner registration in `_runtime/owner_registration.json`
- delegated access profiles in `_runtime/access_profiles.json`
- one configured provider lane, preferably Ollama for the default private demo story
- a passing Ollama environment report from `python scripts/ollama_demo_environment.py --probe --output _review/ollama_demo_environment.json` when using the default private lane
- a passing provider report from `python scripts/provider_demo_flow.py --provider <provider-id> --probe`
- a passing runtime smoke result from `python scripts/private_server_smoke_test.py`

## Suggested 10-Minute Flow

### 1. Show deployment posture

Run:
- `python scripts/dashboard_server.py --check-only`

Explain:
- SA-NOM does not treat production posture as implicit
- the runtime validates owner identity, access profiles, trusted registry, and operational readiness first

### 2. Show provider readiness

Run:
- `python scripts/ollama_demo_environment.py --probe` for the default private lane
- `python scripts/provider_demo_flow.py --provider <provider-id> --probe` for the provider-specific report

Explain:
- which provider lane is active
- that Ollama is the default private demo lane when you want model traffic to stay in your environment
- that OpenAI and Claude remain optional hosted evaluation lanes
- that the provider path can be probed before exposing the runtime to real operator traffic

### 3. Show end-to-end runtime validation

Run:
- `python scripts/private_server_smoke_test.py`

Explain:
- the runtime path covers login, dashboard, health, evidence, integrations, and provider surfaces

### 4. Show the dashboard or API

Run:
- `python scripts/run_private_server.py --host 127.0.0.1 --port 8080`

Explain:
- the runtime is self-managed
- governance and operational state stay inside the organization's own environment

### 5. Close on governance and commercial path

Use:
- [ONE_PAGER.md](ONE_PAGER.md)
- [ONE_PAGER_TH.md](ONE_PAGER_TH.md)
- [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md)

Explain:
- the community baseline is public and self-managed
- commercial engagement is for rollout, support, compliance tailoring, and enterprise packaging

## Recommended Demo Commands

- `python scripts/ollama_demo_environment.py --probe`
- `python scripts/provider_demo_flow.py --provider ollama --probe`
- `python scripts/provider_demo_flow.py --provider openai --probe`
- `python scripts/provider_demo_flow.py --provider anthropic --probe`

## After The Demo

Archive:
- the guided smoke report
- the Ollama environment report when you used the default private lane
- the provider demo report
- the startup readiness report
- the smoke-test report
- the next-step notes for the customer or internal team


