# Demo Checklist

Use this one-page checklist during a live SA-NOM demo so you do not have to rely on memory while presenting.

## Demo Goal

Show that SA-NOM can:
- run AI in governed operational roles
- keep the default demo lane private through Ollama
- prove readiness before real use
- connect runtime behavior to evidence, escalation, and deployment posture

## Default Demo Lane

Use this configuration unless the customer explicitly wants a hosted evaluation lane:
- `SANOM_MODEL_PROVIDER_DEFAULT=ollama`
- `SANOM_OLLAMA_MODEL=gemma3:1b`
- Ollama daemon reachable at `http://localhost:11434`

## Before The Call

Confirm these are ready:
- `python scripts/ollama_demo_environment.py --probe --output _review/ollama_demo_environment.json`
- `python scripts/provider_demo_flow.py --provider ollama --probe --output _review/provider_demo_flow.ollama.json`
- `python scripts/private_server_smoke_test.py`
- browser tab prepared for the dashboard
- [LIVE_CUSTOMER_WALKTHROUGH.md](LIVE_CUSTOMER_WALKTHROUGH.md) or [LIVE_CUSTOMER_WALKTHROUGH_TH.md](LIVE_CUSTOMER_WALKTHROUGH_TH.md)
- [ROI_ONE_PAGER.md](ROI_ONE_PAGER.md) ready for the budget or business-value part of the conversation

## 60-Second Opening

Say:

> This is not a hosted AI toy. This is a private AI operations lane that runs inside the environment, proves its own readiness, and keeps governance attached to live runtime behavior.

Then say:

> For this demo I am using Ollama as the default private lane, so model traffic stays inside the environment.

## Live Demo Sequence

1. Run `python scripts/ollama_demo_environment.py`
   Call out:
   `status: ready`, `default_private_demo_lane: ollama`, `daemon.reachable: true`, `daemon.model_present: true`

2. Run `python scripts/provider_demo_flow.py --provider ollama --probe`
   Call out:
   `selected_provider: ollama`, `probe.status: ok`, `response_excerpt: PONG`

3. Run `python scripts/private_server_smoke_test.py`
   Call out:
   `passed: true`, `errors: 0`, `warnings: 0`, `MODEL_PROVIDER_PROBE: ok`, `GO_LIVE_READINESS: ok`

4. Run `python scripts/run_private_server.py --host 127.0.0.1 --port 8080`
   Show:
   dashboard summary, model providers, compliance/evidence views, or operator-facing runtime state

## Key Messages To Repeat

Repeat these ideas during the call:
- SA-NOM is about governed AI operations, not only chatbot usage
- Ollama is the default private lane
- OpenAI and Claude remain optional hosted evaluation lanes
- readiness, provider health, runtime health, and evidence are checked explicitly
- commercial scope starts when rollout, support, compliance tailoring, or enterprise packaging is needed

## Fast Fallbacks

If Ollama is down:
- rerun `python scripts/ollama_demo_environment.py`
- explain that the operator helper shows exactly what needs fixing next

If the model is missing:
- run `ollama pull gemma3:1b`
- explain that SA-NOM keeps the private lane explicit instead of silently shifting to a hosted path

If the dashboard is not the best screen:
- stay in the terminal and use the JSON and smoke outputs as live evidence

## Close The Call

Ask one of these:
- Would your next step be a guided evaluation, a paid pilot, or a production rollout discussion?
- Does your first production lane need to stay private from day one?
- Which workflow would be the right first pilot?

Then move into:
- [COMMERCIAL_DISCOVERY_CHECKLIST.md](COMMERCIAL_DISCOVERY_CHECKLIST.md)
- [ROI_ONE_PAGER.md](ROI_ONE_PAGER.md)
- [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md)
