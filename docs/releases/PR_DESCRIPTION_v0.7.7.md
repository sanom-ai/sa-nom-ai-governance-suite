## Summary

This PR delivers `v0.7.7` as the productization-hardening release.

It turns the recent runtime foundations into a cleaner pilot-facing product by splitting SA-NOM into:
- a simple `Command Surface` for normal users
- a protected `Control Room` for advanced governance work
- a guided `Setup Assistant` for first-run continuity and doctor posture
- privileged `Backup & Restore` and `Admin Settings` tools for pilot operation

Key scope in this PR:
- a new Home dashboard that leads with posture, next actions, AI activity, and department quick access
- a role-gated Control Room route for founder, admin, owner, and IT sessions only
- setup continuity across onboarding, registration, doctor, and pilot preparation
- Control Room tools for runtime recovery, backup posture, and administrative operating settings
- command-surface polish including an English-first Home heading, a live ticking timestamp, and README documentation with a real product screenshot

## Why This Change

The goal of `v0.7.7` is to make SA-NOM feel less like a powerful internal runtime and more like a serious pilot product.

Before this change, SA-NOM already had stronger work surfaces, canonical cases, governed documents, explicit AI actions, and master-data-aware assignment/search.
But the product still needed one more move:
- simple users needed a command center instead of a collection of technical operator lanes
- advanced governance surfaces needed clearer separation and access control
- setup, diagnostics, recovery, and administrative posture needed to feel like part of the product, not repo knowledge

This PR closes that gap by making the normal user surface simpler while keeping the deeper governance tools intact and intentionally disclosed only when needed.

## Validation

- [x] `python -m compileall -q .`
- [x] `node --check .\sa_nom_governance\dashboard\static\dashboard_app.js`
- [x] `python scripts\dashboard_server.py --check-only`
- [x] `python -m pytest _support\tests`
- [x] Current full-suite status: `359 passed`
- [x] Current coverage posture: `85.02%`
- [x] Docs updated when behavior changed

## Notes

- this PR is the productization-hardening milestone for `v0.7.7`
- the key product move is progressive disclosure: Home stays simple while deeper governance tooling lives in Control Room
- the live timestamp now advances without refresh while preserving the Thai datetime format on the surface
- `coverage.xml` remains a local artifact and is not part of the PR surface
