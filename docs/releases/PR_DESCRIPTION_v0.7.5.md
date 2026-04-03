## Summary

This PR delivers `v0.7.5` as the governed AI action-runtime release.

It makes SA-NOM treat AI execution as first-class governed runtime work instead of leaving it as implied behavior around prompts, queues, and side effects.

Key scope in this PR:
- a governed AI action runtime package with action models, registry, store, and service behavior
- explicit action contracts for authority boundary, side-effect posture, next action, and next view
- action lifecycle handling for `planned`, `running`, `waiting_human`, `completed`, and `failed_closed`
- built-in governed action handlers for `summarize_case`, `draft_document`, and `request_human`
- a dedicated `AI Actions` dashboard lane with launch, rerun, artifacts, traces, and case-aware continuity
- linkage from actions into canonical cases, documents, Human Ask, audit proof, work surface summaries, and runtime health

## Why This Change

The goal of `v0.7.5` is to make AI execution feel like real governed runtime work instead of background logic that operators have to infer after the fact.

Before this change, SA-NOM already had stronger work surface continuity, canonical cases, and governed document runtime behavior.
But the product still needed one more product-grade move:
- AI needed explicit runtime actions instead of implicit execution paths
- action side effects needed to stay tied to case and evidence continuity
- operators needed a way to launch, follow, and understand AI work from the same dashboard story

This PR closes that gap by turning AI execution into a live governed lane that is launchable, traceable, case-linked, artifact-aware, and reviewable.

## Validation

- [x] `python -m compileall -q sa_nom_governance _support	ests`
- [x] `python -m pytest _support	ests`
- [x] `python -m pytest --no-cov _support	ests	est_action_runtime.py _support	ests	est_dashboard_operator_surface.py`
- [x] `node --check .\sa_nom_governance\dashboard\static\dashboard_app.js`
- [x] `python scripts\dashboard_server.py --check-only`
- [x] Current full-suite status: `354 passed`
- [x] Current coverage posture: `84.58%`
- [x] Docs updated when behavior changed

## Notes

- this PR is the AI action-runtime milestone for `v0.7.5`, not the broader master-data and assignment milestone planned for the next phase
- the strongest outcome is that AI work now behaves like governed runtime execution with lifecycle, artifacts, case continuity, and human handoff discipline
- `coverage.xml` remains a local artifact and is not part of the PR surface
