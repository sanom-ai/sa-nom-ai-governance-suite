# Release Notes - v0.1.0

## Release Focus

This release prepares SA-NOM AI Governance Suite for its first public open-source baseline under AGPL-3.0-only, while keeping a clear open-core path for commercial licensing and rollout services.

## Highlights

- Added a public-safe owner identity model centered on `EXEC_OWNER`
- Sanitized policy packs, examples, and public-facing defaults for open-source release readiness
- Hardened access profile validation and deployment-readiness checks so malformed profile files fail cleanly instead of crashing core flows
- Preserved `registered_at` during owner registration reloads
- Rejected invalid bootstrap token lifetimes before unusable artifacts are generated
- Added a trusted-registry refresh path aligned with the sanitized public baseline
- Introduced GitHub Actions CI for compile and test verification
- Refreshed README, commercial licensing docs, notice files, and public release guidance

## Community Baseline In This Release

- PTAG parsing and validation
- governed runtime execution and audit chain
- Role Private Studio workflows
- Human Ask workflows
- deployment readiness checks
- local and Docker private-server paths

## Commercial Direction

Commercial offerings remain separate from the AGPL community baseline and may include enterprise-only features, direct support, rollout hardening, compliance tailoring, air-gapped delivery, and custom integrations.

See [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md) for the current commercial positioning.

## Upgrade Notes

- Public default executive-owner identity is now `EXEC_OWNER`
- Legacy `TAWAN` owner tokens are still recognized through compatibility logic for older local artifacts
- Trusted registry artifacts should be regenerated after policy-pack edits

## Verification Snapshot

Validated during release preparation with:
- `python -m py_compile` on touched Python files
- direct regression execution across key tests in `_support/tests`
- CI workflow configuration in `.github/workflows/ci.yml`

## Known Gaps Before Public Push

- This workspace still needs a real git remote and push target
- Full `pytest` should be re-run in an environment where dev dependencies are installed
- Final repository review should confirm `_runtime/` contains no real organization data

## Contact

- Community/commercial/security contact: `sanomaiarch@gmail.com`

