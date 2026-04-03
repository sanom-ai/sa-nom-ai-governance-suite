## Summary

Advance `v0.7.9` as a confidence-hardening release for the governed runtime.

This PR improves trust in the parts of SA-NOM that matter most during serious pilot use:

- runtime and CLI entrypoints
- deployment, smoke, and recovery flows
- dashboard and API boundary behavior
- persistence and coordination fallbacks
- pilot confidence scenarios

## Why This Change

The product line from `v0.7.2` through `v0.7.8` established the work surface, case backbone, document runtime, AI action runtime, productization hardening, and private-first tablet surface.

`v0.7.9` is the release that makes those lines safer to operate. It is intentionally a confidence release rather than a feature-sprawl release. The goal is to reduce uncertainty around the orchestration seams that are hardest to debug when a pilot is live.

## Validation

- [x] `python -m compileall -q sa_nom_governance _support\tests`
- [x] `python -m pytest _support\tests`
- [x] Coverage updated and verified above `91%`
- [x] Docs updated for the `v0.7.9` release line

## Notes

Key outcomes in this PR:

- expanded runtime entrypoint coverage
- expanded deployment and recovery validation
- expanded dashboard server and API boundary coverage
- expanded persistence, retention, and coordination confidence
- added pilot confidence scenarios for governed document release and operational exception handling
- pushed repository coverage to `91.08%`

`coverage.xml` remains a local test artifact and is intentionally excluded from the PR.
