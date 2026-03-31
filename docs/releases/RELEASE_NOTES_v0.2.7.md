# Release Notes - v0.2.7

## Release Focus

`v0.2.7` is the phase-close milestone for the `v0.2.x` enterprise execution line.

This release is intended to prove that the enterprise execution runtime is not only implemented, but validated, exportable, regression-protected, and ready to hand off into the `v0.3.0` usability phase.

## Completed Scope

### Enterprise Validation

- enterprise validation suite for human-gated workflow pause, resume, restart continuity
- enterprise validation suite for recovery failure, dead-letter capture, replay, and restart continuity

### Workflow Proof And Handoff Evidence

- workflow proof bundle export for workflow state, readiness, recovery, dead letters, human sessions, and audit excerpts
- workflow-scoped proof listing for operator and audit handoff

### Reliability Hardening

- focused enterprise-runtime CI verification job
- enterprise runtime coverage enforcement
- regression protection around validation, proof, readiness, workflow state, and recovery paths

### Metadata And Phase Alignment

- package metadata aligned to the close of the `v0.2.x` execution phase
- docs index updated to surface `v0.2.7` phase-close and `v0.3.0` handoff materials

## Why This Release Matters

`v0.2.7` is the point where `v0.2.x` can claim an enterprise execution baseline with evidence.

The project now has governed runtime orchestration, authority and decision enforcement, policy contracts, evidence objects, state flow, task routing, persistence, recovery, proof export, and focused CI gates around the most trust-sensitive runtime paths.

That closes the execution-system phase and creates a clean boundary before `v0.3.0`, which should focus on ease of use rather than more execution-core invention.

## Enterprise Execution Baseline Complete

The `v0.2.x` line now includes:

- governed runtime orchestration
- authority and decision engine enforcement
- policy runtime contracts and preflight checks
- structured evidence and audit execution
- stateful workflow persistence and runtime recovery
- governed task packets and human decision inbox contracts
- operational readiness and workflow proof artifacts
- enterprise validation and focused runtime reliability gates

## Next Phase

`v0.3.0` is the usability handoff phase.

It should focus on:

- quick start in 5-10 minutes
- clearer local/private deployment entry points
- simple dashboard and operator visibility for non-technical users
- smoother demo and first-run experience

## Notes

- this release note closes the `v0.2.x` enterprise execution line
- further execution-core work after this point should be justified carefully against the usability priority of `v0.3.0`
