# Provider Setup

Use this guide when you want to configure OpenAI, Claude (Anthropic), or Ollama for a real SA-NOM evaluation, pilot, or customer demo.

## Fastest Check

Run:

- `python provider_demo_flow.py`

This prints a setup report that shows:
- which providers are configured
- which environment variables are still missing
- which example file to start from
- what to run next for a demo-ready provider lane

## Shared Settings

Across all providers, these settings matter most:
- `SANOM_MODEL_PROVIDER_DEFAULT`
- `SANOM_MODEL_PROVIDER_TIMEOUT_SECONDS`

If more than one provider is configured, set `SANOM_MODEL_PROVIDER_DEFAULT` so operators and demos use a stable default lane.

## OpenAI

Start from:
- [examples/.env.openai.example](examples/.env.openai.example)

Required settings:
- `SANOM_OPENAI_API_KEY`
- `SANOM_OPENAI_MODEL`

Typical command flow:
- `python provider_demo_flow.py --provider openai --probe`
- `python provider_smoke_test.py --provider openai`

## Claude (Anthropic)

Start from:
- [examples/.env.claude.example](examples/.env.claude.example)

Required settings:
- `SANOM_ANTHROPIC_API_KEY`
- `SANOM_ANTHROPIC_MODEL`

Typical command flow:
- `python provider_demo_flow.py --provider anthropic --probe`
- `python provider_smoke_test.py --provider anthropic`

## Ollama

Start from:
- [examples/.env.ollama.example](examples/.env.ollama.example)

Required settings:
- `SANOM_OLLAMA_MODEL`

Typical command flow:
- `python provider_demo_flow.py --provider ollama --probe`
- `python provider_smoke_test.py --provider ollama`

## Recommended Validation Order

1. Configure one provider lane completely.
2. Set `SANOM_MODEL_PROVIDER_DEFAULT`.
3. Run `python provider_demo_flow.py --provider <provider-id> --probe`.
4. Run `python provider_smoke_test.py --provider <provider-id>`.
5. Run `python dashboard_server.py --check-only`.
6. Run `python private_server_smoke_test.py`.

## Demo Artifact

For customer evaluation or internal rollout review, save the JSON output from:

- `python provider_demo_flow.py --provider <provider-id> --probe --output _review/provider_demo_report.json`

This gives you a public-safe artifact you can attach to discovery notes or release records.
