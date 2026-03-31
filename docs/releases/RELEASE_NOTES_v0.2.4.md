# Release Notes - v0.2.4

## Release Focus

`v0.2.4` turns the governed execution-control plan into working runtime hardening across reasoning control, authority enforcement, policy-contract expansion, evidence-object hardening, and runtime-governance CI gates.

## What Changed

### Planning Baseline

- added `docs/ROADMAP_v0.2.4.md`
- added `docs/ISSUE_DRAFTS_v0.2.4.md`

### Runtime Implementation Slices

- added governed runtime reasoning control for `standard`, `think`, and `deep_think`
- enforced authority transition order before override resume
- expanded runtime `policy_contract` rules with governed preflight checks for `human_required`, `exception`, and `override_path`
- hardened evidence-event objects for `authority_decision`, `override_resolution`, `exception_trace`, and end-to-end correlation
- added focused runtime-governance matrix tests and CI coverage gates for authority/policy/evidence modules

### CI And Reliability Hardening

- added `_support/tests/test_runtime_governance_matrix.py`
- added `scripts/check_runtime_governance_coverage.py`
- updated `.github/workflows/ci.yml` with:
  - dedicated `runtime-governance-verify` job
  - runtime-governance coverage gate
  - governed runtime summary in GitHub Actions step summary

### Validation Snapshot

- full local suite passed: `216 passed`
- total repository coverage gate passed: `80.29%`
- runtime governance coverage gate passed: `90.59%`
- `ruff` and `mypy` passed for implementation slices

## Why This Release Matters

`v0.2.4` is the first release where the execution-control model is not only documented, but materially enforced in code:

- reasoning depth is governed instead of implicit
- trust-sensitive resume paths fail closed when state/order is invalid
- policy contracts now validate compatibility before deeper execution
- audit evidence carries cleaner authority/override/exception linkage
- CI watches the governed runtime path as a first-class reliability surface

## Included Work

- `v0.2.4 reasoning control plane baseline`
- `v0.2.4 authority engine enforcement on override transitions`
- `v0.2.4 policy contract expansion with governed preflight checks`
- `v0.2.4 evidence object hardening for authority and override chains`
- `v0.2.4 reliability and CI gate for governed runtime paths`

## Notes

- this release closes the full `v0.2.4` implementation set across all five planned workstreams
- the next logical step is `v0.2.5`, where the project can move from execution-control hardening into broader runtime composition and enterprise execution layers
