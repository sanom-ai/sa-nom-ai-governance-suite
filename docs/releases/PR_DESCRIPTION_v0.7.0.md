## Summary

This PR delivers `v0.7.0` as an autonomous governed runtime foundation release.

It strengthens SA-NOM across one coherent direction rather than adding scattered feature tracks:
- runtime portability and install-safe packaging
- automation-first governed execution posture
- visible degraded governance state
- deterministic runtime defaults
- performance and release guardrails

## Why This Change

The goal of `v0.7.0` is to make SA-NOM look less like a fast-growing governed-AI repository and more like a platform foundation that organizations can seriously evaluate for longer-running use.

This change improves the operational trust story in concrete ways:

- critical runtime behavior no longer depends on fragile repository-root assumptions
- invalid governance materials stop disappearing silently and now surface through health and dashboard paths
- governed autonomy posture becomes easier to read across workflow, inbox, recovery, and operator readiness views
- runtime performance and release posture become part of the operating contract
- packaged public resources are now bundled explicitly so install-based execution is more believable
- bundled public roles and the trusted registry manifest now stay aligned, preventing avoidable degraded governance posture on fresh installs

## Validation

- [x] `python -m compileall -q sa_nom_governance _support\tests scripts`
- [x] `python -m pytest _support\tests`
- [x] `python -m pytest --no-cov _support\tests\test_public_release_preflight.py -q`
- [x] `python -m pip wheel . --no-deps -w _review\build_smoke`
- [x] Docs updated when behavior changed

## Notes

- this PR closes the first autonomous governed runtime foundation phase
- the release is about making the runtime cleaner, more automatic, more portable, and more trustworthy, not about expanding into a broad new product surface
- local build smoke confirmed that bundled public runtime resources are present in the built wheel
