# Ollama Demo Environment

Use this guide when you want a real private-model demo lane, not only a provider placeholder.

## Goal

By the end of this path you should have:
- Ollama running locally or through Docker Compose
- a model pulled and reachable by SA-NOM
- `SANOM_MODEL_PROVIDER_DEFAULT=ollama`
- a passing Ollama environment report
- a passing provider demo report for the private default lane

## Fastest Check

Run:

- `python scripts/ollama_demo_environment.py`

This prints a report that tells you:
- whether the Ollama daemon is reachable
- whether the requested model is already installed
- which Docker Compose commands to run next
- which commands should follow for the provider and runtime smoke paths

## Recommended Docker Path

1. Start from [../examples/.env.ollama.example](../examples/.env.ollama.example).
2. Make sure `SANOM_MODEL_PROVIDER_DEFAULT=ollama`.
3. Start the Ollama container:
   - `docker compose --profile local-llm up -d ollama`
4. Pull the recommended model:
   - `docker compose exec ollama ollama pull gemma3`
5. Build the Ollama environment report:
   - `python scripts/ollama_demo_environment.py --probe --output _review/ollama_demo_environment.json`
6. Capture the provider-specific report:
   - `python scripts/provider_demo_flow.py --provider ollama --probe --output _review/provider_demo_report.json`
7. Validate the runtime end-to-end:
   - `python scripts/private_server_smoke_test.py`

## Recommended Local Host Path

1. Install Ollama on the host machine.
2. Start the daemon:
   - `ollama serve`
3. Pull the recommended model:
   - `ollama pull gemma3`
4. Set these environment variables:
   - `SANOM_MODEL_PROVIDER_DEFAULT=ollama`
   - `SANOM_OLLAMA_BASE_URL=http://localhost:11434`
   - `SANOM_OLLAMA_MODEL=gemma3`
5. Run:
   - `python scripts/ollama_demo_environment.py --probe --output _review/ollama_demo_environment.json`
   - `python scripts/provider_demo_flow.py --provider ollama --probe`
   - `python scripts/private_server_smoke_test.py`

## Reading The Report

Key fields in the JSON output:
- `status`: `disabled`, `partial`, or `ready`
- `environment`: current Ollama env configuration and missing variables
- `compose`: exact Docker Compose commands for the local demo lane
- `daemon`: whether Ollama is reachable and whether the requested model is already installed
- `probe`: optional live-provider result when `--probe` is used
- `next_actions`: the next operator actions in the right order

## When The Report Is Ready

You are in a good demo state when:
- `status` is `ready`
- `default_provider` is `ollama`
- `daemon.status` is `ready`
- `daemon.model_present` is `true`
- the follow-up provider probe and runtime smoke test pass

## Follow-On Commands

After the environment report is ready, keep using:
- `python scripts/provider_demo_flow.py --provider ollama --probe`
- `python scripts/private_server_smoke_test.py`
- `python scripts/run_private_server.py --host 127.0.0.1 --port 8080`

For the broader provider matrix, see [PROVIDER_SETUP.md](PROVIDER_SETUP.md).
For the customer walkthrough, see [DISCOVERY_DEMO.md](DISCOVERY_DEMO.md).

For the sales-led live talk track, see [LIVE_CUSTOMER_WALKTHROUGH.md](LIVE_CUSTOMER_WALKTHROUGH.md).

