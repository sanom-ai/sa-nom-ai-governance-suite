# Release Notes - v0.2.3

## Release Focus

`v0.2.3` enforces policy contracts directly in runtime context and decision paths, then aligns repository metadata and release indexing with the active `v0.2.x` phase.

This release continues the structure-first execution model where AI handles operational enforcement while humans retain trust-sensitive approval authority.

## What Changed

### Runtime Policy Contract Enforcement

- enforced `metadata.policy_contract` schema validation (fail-closed)
- enforced context boundaries for:
  - `required_role`
  - `allowed_roles`
  - `allowed_actions`
  - `required_payload_fields`
- enforced decision boundaries for:
  - `allowed_outcomes`
  - `required_policy_basis_prefix`
  - `required_trace_sources`
- wired decision-stage contract checks to runtime context in core engine
- expanded decision-flow tests for policy-contract boundary cases

### Release And Metadata Hygiene

- aligned package metadata version to `0.2.3.dev0`
- added missing `v0.2.0`, `v0.2.1`, `v0.2.2` release-note files
- updated docs index links for `v0.2.x` and recent `v0.1.x` planning/release continuity

## Included Pull Request Scope

- `Enforce runtime policy contracts across context and decision`
- `Align v0.2.x metadata and release-note index hygiene`

## Why This Release Matters

`v0.2.3` moves governance from declared intent to executable boundary enforcement in code, while reducing operational drift in versioning and release discoverability.

## Validation Snapshot

Validated during this slice with:

- `python -m pytest _support/tests` (full suite previously executed in branch)
- `python -m ruff check sa_nom_governance/core/policy_runtime_contracts.py sa_nom_governance/core/core_engine.py _support/tests/test_decision_flow.py`
- `python -m mypy`
- `python -m compileall -q .`

## Notes

- this release strengthens runtime boundary enforcement and hygiene posture; it is not the final enterprise-runtime completion point
- review finding around bootstrap token lifetimes is already guarded in code and covered by tests in this code line
