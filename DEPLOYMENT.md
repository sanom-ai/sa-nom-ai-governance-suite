# Deployment Guide

This guide describes the public deployment baseline for the open-source SA-NOM AI Governance Suite repository.

## Goals

Use this guide when you want to:
- run the local dashboard and API
- validate a configuration before serving traffic
- package the runtime into Docker
- create a clean demonstration or evaluation environment

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
5. Start the runtime:
   - `python run_private_server.py --host 127.0.0.1 --port 8080`

## Docker Compose

Use the included [docker-compose.yml](docker-compose.yml) for a single-node baseline:

- `docker compose up --build`
- `docker compose down`

The compose file is intended for local evaluation and controlled private deployments.
Review every environment variable before public exposure.

## Runtime State

`_runtime/` is local generated state, not source code.
For public repositories and examples:
- do not commit live runtime audit logs
- do not commit generated tokens
- do not commit organization-specific owner registrations
- keep only placeholders, `.gitkeep`, or sanitized examples

## Example Artifacts

Use the sanitized files in [examples/](examples/) when you need a starting point for docs, demos, or onboarding.
They are examples only and should be replaced before a real deployment.

## Production Hardening Checklist

- set a unique owner token
- set a unique trusted registry signing key
- keep generated access tokens out of version control
- rotate delegated access tokens before expiry
- use HTTPS and a controlled reverse proxy in front of the dashboard
- verify the trusted registry manifest path and signing posture
- keep `_runtime/` on persistent storage owned by the deployment environment

## Legacy Note

The older [PRIVATE_SERVER_DEPLOYMENT.md](PRIVATE_SERVER_DEPLOYMENT.md) filename is retained for compatibility, but this document is the public deployment reference going forward.
