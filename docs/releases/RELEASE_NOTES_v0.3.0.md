# Release Notes - v0.3.0

## Release Focus

`v0.3.0` is the usability-phase release after the `v0.2.x` enterprise execution baseline.

This release is focused on making governed runtime operation easier to start, easier to understand, and easier to operate in local/private environments without weakening authority, policy, evidence, or fail-closed behavior.

## Completed Scope

### Quick Start In 5-10 Minutes

- guided quick-start runtime path for local/private setup
- quick-start doctor checks for first-run readiness posture
- clearer first successful run path from bootstrap to runtime launch

### Dashboard And Operator Surface

- operator dashboard surfaces for workflow, readiness, and governed operations
- usability-proof visibility and refresh actions in operations views
- deterministic operator decision lanes and clearer human-required visibility

### First-Run Action Center

- first-run action-center aggregation for readiness gaps
- prioritized required/advisory first-run action items
- one-click first-run sync flow for usability proof + quick-start doctor refresh

### Review-Finding Hardening

- explicit lifetime validation for bootstrap access profiles
- regression coverage for invalid token lifetime inputs, including negative-value combinations

## Why This Release Matters

`v0.3.0` makes the runtime operationally approachable for non-deep technical operators while preserving governed execution semantics.

The platform now demonstrates a clearer bridge from enterprise execution capability (`v0.2.x`) to practical first-run usability:

- start quickly
- see runtime posture clearly
- identify required human actions
- export and inspect proof artifacts from operator surfaces

## Local Use-Case Proof Note

This release includes a phase-close proof note path for maintainers:

- confirm quick-start path executes on a real local/private machine
- confirm first-run action-center operations complete and refresh status
- capture a short machine-run summary in the GitHub release body for traceability

## Next Phase

The next milestone after `v0.3.0` should continue usability expansion (quick-start polish, dashboard clarity, non-technical operator flow), while keeping execution-core contracts stable unless a correctness issue requires change.

## Notes

- this release closes the `v0.3.0` usability phase
- governance boundaries remain explicit and fail-closed where required
- usability improvements are implemented against real runtime surfaces, not mock-only flows
