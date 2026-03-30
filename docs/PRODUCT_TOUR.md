# Product Tour

Use this guide when you want a compact walkthrough of how SA-NOM moves from role definition to governed runtime execution.

## What This Tour Shows

SA-NOM is not only a control layer around AI.
It is a runtime for organizations that want AI to hold a role, stay inside boundaries, escalate when necessary, and leave evidence behind.

## Tour Map

```mermaid
flowchart LR
    A["Role pack"] --> B["Owner and access setup"]
    B --> C["Trusted registry and startup checks"]
    C --> D["Provider lane readiness"]
    D --> E["Governed runtime"]
    E --> F["Evidence, compliance, and review"]
```

## 1. Role Packs And Policy Shape

Start with the PTAG role packs under `resources/roles/`.
They define the boundaries the runtime will respect before any provider is called.

Look at:
- `resources/roles/GOV.ptn`
- `resources/roles/LEGAL.ptn`
- `resources/config/role_transition_matrix.json`

This is the layer that turns AI from a general assistant into a governed operating role.

## 2. Owner And Delegated Access

The runtime becomes organization-aware once an executive owner and delegated profiles are present.

Fastest path:
- `python scripts/guided_smoke_test.py --registration-code DEMO-ORG`

Manual path:
- `python scripts/register_owner.py --registration-code DEMO-ORG`
- `python scripts/bootstrap_access_profiles.py --output _runtime/access_profiles.json --tokens-output _runtime/generated_access_tokens.json`

This creates the authority surface the dashboard and API will use.

## 3. PT-OSS Structural Intelligence

Before a role is treated as publication-ready or structurally trustworthy, SA-NOM already carries a PT-OSS layer that can apply structural posture, readiness scoring, blockers, and recommendations.

That means the product is not only checking whether the runtime starts. It is also checking whether the role and workflow are structurally safe enough to trust.

See [PT_OSS_CORE.md](PT_OSS_CORE.md).

## 4. Trusted Registry And Startup Readiness

Before the runtime is treated as ready, SA-NOM verifies owner identity, delegated access, registry state, and session posture.

Run:
- `python scripts/dashboard_server.py --check-only`

The one-command guided flow also writes:
- `_review/guided_smoke_test.json`

That report is the fastest way to show a stakeholder that the runtime is prepared before go-live.

## 5. Provider Lane Strategy

SA-NOM separates runtime governance from model-provider choice.

Default private demo lane:
- Ollama

Optional hosted evaluation lanes:
- OpenAI
- Claude

Private-first probe flow:
- `python scripts/provider_demo_flow.py --provider ollama --probe`

This keeps the product story aligned with private AI operations while still allowing hosted evaluation when needed.

## 6. Runtime, Escalation, And Evidence

Once the baseline is prepared, the runtime can expose dashboard, health, evidence, integration, and provider surfaces in one governed path.

Run:
- `python scripts/private_server_smoke_test.py`
- `python scripts/run_private_server.py --host 127.0.0.1 --port 8080`

The important point in a demo is not only that the runtime answers.
It is that the runtime shows:
- ownership
- delegated authority
- escalation-aware behavior
- evidence export
- provider posture
- compliance alignment

## Best Demo Order

1. Run `python scripts/guided_smoke_test.py --registration-code DEMO-ORG`.
2. Show `_review/guided_smoke_test.json`.
3. Run `python scripts/provider_demo_flow.py --provider ollama --probe` if a local model is ready.
4. Run `python scripts/private_server_smoke_test.py`.
5. Open the runtime and explain the dashboard, evidence, and go-live readiness surfaces.

## Where To Go Next

- [GUIDED_EVALUATION.md](GUIDED_EVALUATION.md)
- [DISCOVERY_DEMO.md](DISCOVERY_DEMO.md)
- [PROVIDER_SETUP.md](PROVIDER_SETUP.md)
- [DEPLOYMENT.md](DEPLOYMENT.md)

