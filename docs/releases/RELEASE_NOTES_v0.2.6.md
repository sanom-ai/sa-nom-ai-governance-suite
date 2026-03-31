# Release Notes - v0.2.6

## Release Focus

`v0.2.6` is the runtime-durability milestone for the `v0.2.x` enterprise execution line.

This release is intended to make governed execution survive and recover through pause, restart, retry, and operator-facing runtime conditions before `v0.2.7` closes the phase with validation, proof, reliability, and final closeout.

## Planned Scope

### Runtime Durability Baseline

- workflow state store baseline
- cross-step resume and recovery controls
- governed task packet contract

### Human And Operator Runtime Surfaces

- human decision inbox / console contract
- operational readiness hooks for execution health, backlog, and operator visibility

### Documentation Index Alignment

- update `docs/README.md` to surface `v0.2.6` materials

## Why This Release Matters

`v0.2.6` closes the gap between "AI can execute governed workflows" and "the runtime can survive like an enterprise system."

If `v0.2.5` proved that governed multi-step execution can exist in code, `v0.2.6` should prove that the same execution can persist, resume, recover, and remain operable when real runtime conditions interrupt the flow.

## Notes

- this release note starts as a milestone baseline and should be updated as implementation slices land
- `v0.2.7` is reserved for validation, proof, reliability tightening, and `v0.2.x` phase close
- `v0.3.0` remains the usability phase for quick start, dashboard, and non-technical operator experience
