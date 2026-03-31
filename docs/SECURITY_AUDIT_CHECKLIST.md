# Security Audit Checklist

Use this checklist before any production rollout, major provider change, or regulated deployment review.

## Release Gate

- Run `python -m pytest _support/tests`.
- Run `python scripts/private_server_smoke_test.py`.
- Run `python scripts/provider_smoke_test.py --require-configured` if any external or local LLM provider will be used in production.
- Verify `python scripts/dashboard_server.py --check-only` returns a ready deployment profile.
- Review the latest evidence export and confirm audit integrity remains verified.

## Secrets And Identity

- Replace every placeholder value in `.env.production.example`.
- Keep `SANOM_API_TOKEN`, trusted-registry keys, and provider API keys in a secret manager or Kubernetes Secret.
- Verify owner registration is present and `trusted_registry_signed_by` matches the production executive owner.
- Confirm access profiles use token hashes, not plain tokens.

## Governance And Publication

- Confirm trusted-registry signatures are enabled in production.
- Review the latest Role Private Studio drafts for guarded or blocked structural findings.
- Confirm escalation ownership and safety ownership are defined for live roles.
- Export a fresh evidence pack after any policy-pack publication.

## Data Protection And Retention

- Review retention windows for audit, session, override, Human Ask, and studio datasets.
- Confirm legal-hold workflow is documented for regulated incidents.
- Validate backup and restore paths for `_runtime`, evidence exports, and trusted registry artifacts.
- Ensure PDPA or sector-specific data handling constraints are reflected in local deployment procedures.

## Model Provider Controls

- Pin the production default provider with `SANOM_MODEL_PROVIDER_DEFAULT`.
- Verify provider endpoints, models, and timeouts before go-live.
- Probe each enabled provider and archive the result with the release record.
- Restrict outbound egress so the runtime can reach only approved provider endpoints.
- Review vendor data handling terms before enabling a hosted model provider.

## Container And Kubernetes Controls

- Run the container as non-root.
- Mount `_runtime` to durable storage when state must survive restarts.
- Apply network policy, secret management, and image provenance controls in the cluster.
- Wire liveness and readiness probes before exposing the service.
- Keep one replica until runtime state is externalized or shared safely.

## Recommended Evidence Bundle

- Startup smoke report
- Provider probe report
- Latest evidence export manifest
- Deployment profile / go-live readiness output
- Access-control health snapshot
- Backup summary

## Restore Validation Reference

For the broader public baseline on backup scope, restore discipline, and post-restore validation expectations, see [BACKUP_AND_RESTORE_VALIDATION.md](BACKUP_AND_RESTORE_VALIDATION.md).

