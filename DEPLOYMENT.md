# Deployment Guide

This guide describes the public deployment baseline for the open-source SA-NOM AI Governance Suite repository.

## Goals

Use this guide when you want to:
- run the local dashboard and API
- validate a configuration before serving traffic
- verify hosted or local model-provider readiness
- package the runtime into Docker
- move the runtime into Helm or raw Kubernetes manifests

## Prerequisites

- Python 3.12 or newer
- a writable local `_runtime/` directory
- a secure value for `SANOM_API_TOKEN`
- a secure value for `SANOM_TRUSTED_REGISTRY_KEY`

## Minimal Local Run

1. Prepare environment variables from [`.env.production.example`](.env.production.example).
2. Register an example organization owner:
   - `python register_owner.py --registration-code DEMO-ORG`
3. Generate delegated access profiles:
   - `python bootstrap_access_profiles.py --output _runtime/access_profiles.json --tokens-output _runtime/generated_access_tokens.json`
4. Validate the deployment baseline:
   - `python dashboard_server.py --check-only`
5. Run the runtime smoke tests:
   - `python private_server_smoke_test.py`
   - `python provider_smoke_test.py`
6. Start the runtime:
   - `python run_private_server.py --host 127.0.0.1 --port 8080`

## Model Provider Setup

The public baseline now supports probeable provider configurations for:
- OpenAI via the Responses API
- Anthropic Claude via the Messages API
- Ollama via the local generate API

Use the example files in [examples/](examples/) to start quickly:
- [examples/.env.openai.example](examples/.env.openai.example)
- [examples/.env.claude.example](examples/.env.claude.example)
- [examples/.env.ollama.example](examples/.env.ollama.example)

## Docker Compose

Use the included [docker-compose.yml](docker-compose.yml) for a single-node baseline:

- `docker compose up --build`
- `docker compose --profile local-llm up --build` if you want the bundled Ollama lane
- `docker compose down`

The compose file is intended for local evaluation and controlled private deployments.
Review every environment variable before public exposure.

## Kubernetes And Helm

Use [KUBERNETES.md](KUBERNETES.md) for the cluster path.

Included assets:
- `helm/sa-nom-ai-governance-suite/`
- `k8s/`
- [examples/helm-values.production.example.yaml](examples/helm-values.production.example.yaml)

## Runtime State

`_runtime/` is local generated state, not source code.
For public repositories and examples:
- do not commit live runtime audit logs
- do not commit generated tokens
- do not commit organization-specific owner registrations
- keep only placeholders, `.gitkeep`, or sanitized examples

## Production Hardening Checklist

- set a unique owner token
- set a unique trusted registry signing key
- keep generated access tokens out of version control
- rotate delegated access tokens before expiry
- use HTTPS and a controlled reverse proxy in front of the dashboard
- verify the trusted registry manifest path and signing posture
- keep `_runtime/` on persistent storage owned by the deployment environment
- run [SECURITY_AUDIT_CHECKLIST.md](SECURITY_AUDIT_CHECKLIST.md) before each regulated rollout
- archive the latest provider probe report with the release record

## Regulated Deployment Templates

For Thai banking or public-sector environments, start with the templates in [templates/compliance/README.md](templates/compliance/README.md).

## Legacy Note

The older [PRIVATE_SERVER_DEPLOYMENT.md](PRIVATE_SERVER_DEPLOYMENT.md) filename is retained for compatibility, but this document is the public deployment reference going forward.
