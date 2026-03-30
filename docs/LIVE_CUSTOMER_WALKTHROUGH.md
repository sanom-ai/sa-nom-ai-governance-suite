# Live Customer Walkthrough (Ollama Lane)

Use this script when you want to demo SA-NOM as a private AI operations platform with a real local-model lane, not only a documentation or governance story.

## Goal

By the end of the call, the customer should understand that SA-NOM can:
- run AI in real operational flows, not only as a chatbot
- keep model traffic inside the organization's own environment through Ollama
- prove readiness, provider health, runtime health, and evidence-oriented state before go-live
- scale later into rollout, support, compliance tailoring, and enterprise packaging when needed

## Demo Promise

Use this sentence near the start of the call:

> Today I am not showing a hosted AI toy. I am showing a private AI operations lane that stays inside the environment, proves its own readiness, and keeps governance attached to live runtime behavior.

## Recommended Demo Configuration

For the current default private lane, use:
- `SANOM_MODEL_PROVIDER_DEFAULT=ollama`
- `SANOM_OLLAMA_MODEL=gemma3:1b`
- Ollama daemon running on `http://localhost:11434`

Recommended local preparation:
- `ollama pull gemma3:1b`
- `python scripts/ollama_demo_environment.py --probe --output _review/ollama_demo_environment.json`
- `python scripts/provider_demo_flow.py --provider ollama --probe --output _review/provider_demo_flow.ollama.json`
- `python scripts/private_server_smoke_test.py`

## Before The Call

Prepare these artifacts in advance:
- `_review/ollama_demo_environment.json`
- `_review/provider_demo_flow.ollama.json`
- the latest passing private-server smoke output
- your selected one-pager from [ONE_PAGER.md](ONE_PAGER.md) or [ONE_PAGER_TH.md](ONE_PAGER_TH.md)
- pricing and commercial next-step material from [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md) and [COMMERCIAL_DISCOVERY_CHECKLIST.md](COMMERCIAL_DISCOVERY_CHECKLIST.md)

Have these windows ready:
- a terminal in the repo root
- the dashboard browser tab
- the repo README or one-pager for closing context

## Suggested 12-Minute Flow

### 1. Frame The Problem (1 minute)

Say:

> Most teams can already prompt a model. The harder problem is letting AI participate in real work without losing authority boundaries, traceability, and operational control. SA-NOM is built for that second problem.

Then say:

> For this demo I am using the private default lane. The model runs locally through Ollama instead of sending traffic to a hosted provider.

### 2. Prove The Private Demo Lane Is Ready (2 minutes)

Run:
- `python scripts/ollama_demo_environment.py`

What to say:
- this helper shows whether the local model lane is actually ready, not only assumed to be ready
- it checks the daemon, the requested model, and the next operator actions in one report
- this is the first proof point that the private lane is operational

Call out on screen:
- `status: ready`
- `default_private_demo_lane: ollama`
- `daemon.reachable: true`
- `daemon.model_present: true`
- the recommended next actions for probe and runtime validation

### 3. Prove The Model Provider Responds (2 minutes)

Run:
- `python scripts/provider_demo_flow.py --provider ollama --probe`

What to say:
- this is a live provider check against the local Ollama endpoint
- SA-NOM separates provider readiness from runtime readiness so operators can catch issues early
- if a customer later wants OpenAI or Claude, that is supported, but this is the private default lane

Call out on screen:
- `selected_provider: ollama`
- `recommended_provider: ollama`
- `probe.status: ok`
- `response_excerpt: PONG`

### 4. Prove The Governed Runtime Path Works (3 minutes)

Run:
- `python scripts/private_server_smoke_test.py`

What to say:
- this is not just a model ping
- the smoke path validates login, dashboard, health, evidence, integrations, and model-provider surfaces together
- this is where SA-NOM moves from an AI demo into an operational system demo

Call out on screen:
- `passed: true`
- `errors: 0`
- `warnings: 0`
- `MODEL_PROVIDER_PROBE: ok`
- `EVIDENCE_EXPORT: ok`
- `GO_LIVE_READINESS: ok`

### 5. Open The Live Runtime (2 minutes)

Run:
- `python scripts/run_private_server.py --host 127.0.0.1 --port 8080`

Then open the dashboard and say:

> The important point here is not only that the dashboard exists. It is that the runtime, provider lane, evidence path, and operational checks all line up with the same governed system.

Suggested areas to show:
- dashboard summary or health status
- model providers panel
- compliance or evidence surfaces
- role or operator-facing runtime sections

### 6. Close On The Buying Path (2 minutes)

Say:

> The community baseline shows the governed private runtime and the default local-model lane. Commercial engagement starts when you want rollout support, enterprise packaging, tailored compliance work, or a guided implementation path.

Then move to one of these:
- [COMMERCIAL_DISCOVERY_CHECKLIST.md](COMMERCIAL_DISCOVERY_CHECKLIST.md)
- [SALES_INTAKE_TEMPLATE.md](SALES_INTAKE_TEMPLATE.md)
- [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md)

Suggested closing question:

> If this became a serious internal evaluation, would your next step be a guided pilot, an infrastructure review, or a compliance and rollout discussion?

## Fast Fallbacks During The Demo

If the Ollama daemon is down:
- rerun `python scripts/ollama_demo_environment.py`
- explain that the helper is designed to show the operator exactly what must be fixed next

If the model is missing:
- run `ollama pull gemma3:1b`
- explain that SA-NOM keeps the private lane explicit instead of silently failing over to a hosted path

If the dashboard is not the best screen for the moment:
- stay in the terminal and use the JSON reports from:
  - `python scripts/ollama_demo_environment.py --probe`
  - `python scripts/provider_demo_flow.py --provider ollama --probe`
  - `python scripts/private_server_smoke_test.py`
- explain that the reports are still showing live operator evidence, not mock output

## Qualification Questions To Ask During Or After The Demo

Use one or two of these:
- Do you need the first production lane to stay fully private, or are hosted providers acceptable for evaluation only?
- Which team would own AI operations first: IT, product, compliance, or a cross-functional governance group?
- Is your first use case more about controlled internal operations, compliance posture, or business workflow execution?
- Would your next checkpoint be a technical pilot, a security review, or a commercial rollout discussion?

## After The Call

Archive or send forward:
- the Ollama environment report
- the provider probe report
- the runtime smoke result
- customer objections or deployment constraints noted during the call
- the recommended next step from the commercial discovery checklist

For the shorter demo runbook, see [DISCOVERY_DEMO.md](DISCOVERY_DEMO.md).
For the operator setup path, see [OLLAMA_DEMO_ENVIRONMENT.md](OLLAMA_DEMO_ENVIRONMENT.md).

For the Thai version, see [LIVE_CUSTOMER_WALKTHROUGH_TH.md](LIVE_CUSTOMER_WALKTHROUGH_TH.md).

