## Summary

This PR delivers `v0.7.1` as a flagship capability proof hardening release.

It does not open a broad new product family.
It tightens the gap between SA-NOM's strongest capability claims and the implementation, tests, dashboard summaries, and release surfaces that support them.

Key scope in this PR:
- stronger Human Ask freshness and confidence posture
- stronger Role Private Studio publication and restore visibility
- clearer PT-OSS structural posture and guardrail operator proof
- stronger evidence-pack and trusted-registry operator visibility
- more explicit outbound integration and human-alert readiness
- release-prep docs that align the flagship story to the current implementation

## Why This Change

The goal of `v0.7.1` is to make SA-NOM's flagship story easier to defend during serious evaluation.

The runtime already had many of these capabilities, but their most visible operator-facing proof surfaces still needed tightening:
- publication readiness needed to be easier to inspect
- Human Ask needed clearer freshness and confidence posture
- PT-OSS and guardrail states needed stronger operator continuity
- evidence and trusted publication posture needed clearer summaries
- outbound routing and alert readiness needed more explicit language

This PR strengthens those proof surfaces without changing SA-NOM into a different product.

## Validation

- [x] `python -m pytest _support\tests`
- [x] Focused tests for evidence pack, role private studio, and dashboard operator surface
- [x] Current full-suite status: `337 passed`
- [x] Current coverage posture: `84.08%`
- [x] Docs updated when behavior changed

## Notes

- this PR is a flagship-hardening release, not a feature-sprawl release
- the strongest outcome is better continuity between code, tests, dashboard surfaces, and capability language
- `coverage.xml` remains a local artifact and is not part of the PR surface
