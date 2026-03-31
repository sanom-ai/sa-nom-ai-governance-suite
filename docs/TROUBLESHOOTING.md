# Troubleshooting

Use this guide when the quick start, startup validation, or smoke checks do not behave as expected.

## First Diagnostic Step

Start with:

- `python scripts/dashboard_server.py --check-only`

This prints the deployment-readiness report without starting the runtime server.
If a configuration gate is blocked, this is usually the fastest way to see why.

## Common Startup Failures

### Owner registration is missing

Typical symptom:
- `OWNER_REGISTRATION_READY` is missing, warning, or error

Recovery:
1. Register the executive owner:
   - `python scripts/register_owner.py --registration-code DEMO-ORG`
2. Confirm `_runtime/owner_registration.json` exists.
3. Re-run:
   - `python scripts/dashboard_server.py --check-only`

Reference example:
- [examples/owner_registration.example.json](examples/owner_registration.example.json)

### Access profiles are invalid

Typical symptom:
- `ACCESS_PROFILES_READY` or `ACCESS_PROFILES_INVALID` fails
- startup aborts in strict mode

Recovery:
1. Regenerate profiles with hashed tokens:
   - `python scripts/bootstrap_access_profiles.py --output _runtime/access_profiles.json --tokens-output _runtime/generated_access_tokens.json --force`
2. Store raw tokens from `_runtime/generated_access_tokens.json` in a secure secret manager.
3. Keep only hashes in `_runtime/access_profiles.json`.
4. Re-run startup validation.

What to check:
- every item is a JSON object
- `profile_id` values are unique
- `token_hash` is present instead of a raw token
- `rotate_after` is earlier than `expires_at`

Reference example:
- [examples/access_profiles.example.json](examples/access_profiles.example.json)

### Trusted registry signing is not ready

Typical symptom:
- `REGISTRY_KEY_READY` fails
- `REGISTRY_SIGNATURE_ENABLED` fails
- trusted registry manifest exists but does not verify

Recovery:
1. Set `SANOM_TRUSTED_REGISTRY_KEY` and `SANOM_TRUSTED_REGISTRY_KEY_ID`.
2. Confirm `SANOM_TRUSTED_REGISTRY_SIGNED_BY` matches the executive owner identity.
3. Refresh the manifest and cache:
   - `python scripts/trusted_registry_refresh.py`
4. Re-run startup validation.

Reference example:
- [examples/trusted_registry_manifest.example.json](examples/trusted_registry_manifest.example.json)

### Provider probe returns disabled

Typical symptom:
- `python scripts/provider_smoke_test.py` reports `status: disabled`

This is expected when no provider is configured yet.

Recovery:
1. Choose a provider example from [examples/README.md](examples/README.md).
2. Set `SANOM_MODEL_PROVIDER_DEFAULT`.
3. Set the matching credentials and model fields.
4. Re-run:
   - `python scripts/provider_smoke_test.py`

### Private server smoke test warns about model providers

Typical symptom:
- `python scripts/private_server_smoke_test.py` passes with a provider warning

Meaning:
- the core runtime path is healthy
- no outbound or local model provider is configured yet

You can continue local evaluation if provider-backed behavior is not required for the current step.

## Common Configuration Mistakes

- Placeholder secrets from [`.env.production.example`](.env.production.example) were not replaced.
- `_runtime/` is missing, read-only, or contains stale local state from an older run.
- Provider settings were mixed across OpenAI, Claude, and Ollama instead of choosing one default provider.
- Trusted registry files were copied manually instead of refreshed with `python scripts/trusted_registry_refresh.py`.

## Safe Reset Path For Local Evaluation

If your local evaluation artifacts are inconsistent and you do not need to preserve them:
1. Remove generated files inside `_runtime/` that came from the failed local run.
2. Re-register the owner.
3. Re-bootstrap access profiles.
4. Re-run startup validation.
5. Re-run the smoke tests.

Do not use this reset path against a live production deployment.

## Recommended Recovery Order

1. `python scripts/dashboard_server.py --check-only`
2. `python scripts/register_owner.py --registration-code DEMO-ORG` if owner registration is missing
3. `python scripts/bootstrap_access_profiles.py --output _runtime/access_profiles.json --tokens-output _runtime/generated_access_tokens.json --force` if access profiles are invalid
4. `python scripts/trusted_registry_refresh.py` if trusted registry artifacts are stale
5. `python scripts/provider_smoke_test.py` after configuring a provider
6. `python scripts/private_server_smoke_test.py`

## Need Commercial Help?

If you need rollout hardening, regulated deployment support, or a guided production path, contact `sanomaiarch@gmail.com`.

## Recovery Posture

For a broader explanation of what SA-NOM should look like under runtime failure conditions, and how operators should think about readiness-first recovery, see [RUNTIME_FAILURE_AND_RECOVERY.md](RUNTIME_FAILURE_AND_RECOVERY.md).

