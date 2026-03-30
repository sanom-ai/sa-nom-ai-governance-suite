# Provider Setup

Use this guide when you want to configure a live model lane for SA-NOM.

Recommended default demo lane:
- Ollama

Optional hosted evaluation lanes:
- OpenAI
- Claude (Anthropic)

For a real private-model setup path, see [OLLAMA_DEMO_ENVIRONMENT.md](OLLAMA_DEMO_ENVIRONMENT.md).

## Fastest Check

Run:

- `python scripts/ollama_demo_environment.py`
- `python scripts/provider_demo_flow.py`

This shows:
- whether the default private Ollama lane is actually reachable
- which providers are configured
- which environment variables are still missing
- which example file to start from
- what to run next for a demo-ready provider lane

## Shared Settings

Across all providers, these settings matter most:
- `SANOM_MODEL_PROVIDER_DEFAULT`
- `SANOM_MODEL_PROVIDER_TIMEOUT_SECONDS`

For the default private demo path, set:
- `SANOM_MODEL_PROVIDER_DEFAULT=ollama`

Use OpenAI or Claude as the default only when you intentionally want a hosted evaluation lane.

## Ollama

Recommended use:
- default private demo lane
- local or semi-air-gapped evaluation
- keeping model traffic inside your own environment

Start from:
- [../examples/.env.ollama.example](../examples/.env.ollama.example)

Required settings:
- `SANOM_OLLAMA_MODEL`

Typical command flow:
- `python scripts/ollama_demo_environment.py`
- `python scripts/ollama_demo_environment.py --probe`
- `python scripts/provider_demo_flow.py --provider ollama --probe`
- `python scripts/provider_smoke_test.py --provider ollama`

## OpenAI

Recommended use:
- optional hosted evaluation lane
- managed API access for external demos or comparisons

Start from:
- [../examples/.env.openai.example](../examples/.env.openai.example)

Required settings:
- `SANOM_OPENAI_API_KEY`
- `SANOM_OPENAI_MODEL`

Typical command flow:
- `python scripts/provider_demo_flow.py --provider openai --probe`
- `python scripts/provider_smoke_test.py --provider openai`

## Claude (Anthropic)

Recommended use:
- optional hosted evaluation lane
- Anthropic-specific commercial or policy review scenarios

Start from:
- [../examples/.env.claude.example](../examples/.env.claude.example)

Required settings:
- `SANOM_ANTHROPIC_API_KEY`
- `SANOM_ANTHROPIC_MODEL`

Typical command flow:
- `python scripts/provider_demo_flow.py --provider anthropic --probe`
- `python scripts/provider_smoke_test.py --provider anthropic`

## Recommended Validation Order

1. Configure Ollama completely if you want the default private demo lane.
2. Run `python scripts/ollama_demo_environment.py` to confirm the daemon and model state.
3. Set `SANOM_MODEL_PROVIDER_DEFAULT=ollama`.
4. Run `python scripts/ollama_demo_environment.py --probe`.
5. Run `python scripts/provider_demo_flow.py --provider ollama --probe`.
6. Run `python scripts/provider_smoke_test.py --provider ollama`.
7. Run `python scripts/dashboard_server.py --check-only`.
8. Run `python scripts/private_server_smoke_test.py`.

If you intentionally want a hosted evaluation lane, swap `ollama` for `openai` or `anthropic` in the commands above.

## Demo Artifact

For customer evaluation or internal rollout review, save the JSON output from:

- `python scripts/ollama_demo_environment.py --probe --output _review/ollama_demo_environment.json`
- `python scripts/provider_demo_flow.py --provider <provider-id> --probe --output _review/provider_demo_report.json`

These give you public-safe artifacts you can attach to discovery notes or release records.
