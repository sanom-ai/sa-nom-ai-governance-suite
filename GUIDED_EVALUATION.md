# Guided Evaluation

Use this path when you want to confirm the public community baseline quickly without wandering through every document first.

## Goal

Complete a first evaluation in about 10 to 15 minutes.
By the end you should have:
- an owner registration
- delegated access profiles
- a successful startup validation
- an optional provider probe result when you want a live model lane
- a successful runtime smoke test

## Prerequisites

- Python 3.14 or newer
- a writable `_runtime/` directory
- local environment variables prepared from [`.env.production.example`](.env.production.example)

## Step 1: Register The Executive Owner

Run:

- `python register_owner.py --registration-code DEMO-ORG`

Expected result:
- `_runtime/owner_registration.json` is created
- the command prints the normalized owner registration payload

Reference example:
- [examples/owner_registration.example.json](examples/owner_registration.example.json)

## Step 2: Generate Delegated Access Profiles

Run:

- `python bootstrap_access_profiles.py --output _runtime/access_profiles.json --tokens-output _runtime/generated_access_tokens.json`

Expected result:
- `_runtime/access_profiles.json` contains hashed profile entries
- `_runtime/generated_access_tokens.json` contains raw tokens for secure storage

Reference example:
- [examples/access_profiles.example.json](examples/access_profiles.example.json)

## Step 3: Refresh Trusted Registry Artifacts

Run:

- `python trusted_registry_refresh.py`

Expected result:
- trusted registry manifest and cache are regenerated from the current PTAG role packs

Reference example:
- [examples/trusted_registry_manifest.example.json](examples/trusted_registry_manifest.example.json)

## Step 4: Validate Startup Readiness

Run:

- `python dashboard_server.py --check-only`

Expected result:
- a JSON deployment-readiness report with `ready: true`

If this step fails, go directly to [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Step 5: Optional Provider Probe

Run:

- `python provider_smoke_test.py`

Expected results:
- `status: disabled` if no provider has been configured yet
- or a provider report if a provider lane is configured

Recommended default private demo lane:
- [examples/.env.ollama.example](examples/.env.ollama.example)

Optional hosted evaluation lanes:
- [examples/.env.openai.example](examples/.env.openai.example)
- [examples/.env.claude.example](examples/.env.claude.example)

## Step 6: Run The Runtime Smoke Test

Run:

- `python private_server_smoke_test.py`

Expected result:
- the runtime path passes end-to-end
- a provider warning is acceptable if no provider is configured yet

## Step 7: Start The Local Server

Run:

- `python run_private_server.py --host 127.0.0.1 --port 8080`

At this point the community baseline is operational for local evaluation.

## Success Checklist

You are in a good evaluation state if all of the following are true:
- `register_owner.py` created the owner registration file
- `bootstrap_access_profiles.py` created hashed profiles successfully
- `dashboard_server.py --check-only` reports `ready: true`
- `provider_smoke_test.py` is either configured successfully or clearly reports `disabled` when you have not enabled a provider yet
- `private_server_smoke_test.py` passes

## Next Steps

- For deployment details: [DEPLOYMENT.md](DEPLOYMENT.md)
- For Helm and Kubernetes: [KUBERNETES.md](KUBERNETES.md)
- For startup failures: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- For licensing and commercial questions: [FAQ.md](FAQ.md) and [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md)
