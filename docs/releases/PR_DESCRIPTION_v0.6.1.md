## Summary

This PR delivers the first controlled implementation slice of the Global Harmony direction introduced in `v0.6.0`.

It wires regional alignment evaluation into the runtime decision path, adds an explainable `resonance_score` / `resonance_band` signal, and pauses constitution switching behind human approval when the context is sensitive or externally visible.

## Why This Change

`v0.6.0` established Global Harmony as a strategic direction, but the repository still needed a credible runtime proof that stayed within SA-NOM's existing governance model.

This change closes that gap by showing that SA-NOM can:

- evaluate cultural and regional context during live governed execution
- surface a measurable alignment-strength signal without retraining the base model
- require human review when alignment switching becomes risk-sensitive, customer-facing, or externally visible

That makes the feature materially stronger for enterprise readers because it ties cultural alignment back to runtime controls, auditability, and approval routing instead of leaving it as concept-only positioning.

## Validation

- [x] `python -m compileall -q .`
- [x] `python -m pytest _support/tests`
- [x] Docs updated when behavior changed

## Notes

- this PR keeps scope intentionally narrow and does not claim full global readiness
- the resonance model is a governed baseline heuristic, not a claim of universal cultural truth
- likely follow-up work should extend the trigger/action model and deepen constitution packs before investing heavily in new dashboard surface area
