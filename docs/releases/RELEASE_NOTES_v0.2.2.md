# Release Notes - v0.2.2

## Release Focus

`v0.2.2` tightens state, authority metadata, and exception evidence contracts for governed runtime execution.

The release reinforces traceability so AI-driven operations remain auditable and bounded while humans stay responsible for trust-sensitive authority decisions.

## What Changed

### Runtime State And Authority Baseline Expansion

- added runtime state-flow engine baseline
- added authority gate runtime metadata hooks

### Evidence Contract Hardening

- added normalized evidence event contract
- tightened exception trace contract consistency
- covered blocked/rejected/escalated/conflicted/out_of_order exception outcomes

### Workflow Hardening

- hardened script wrappers and PT-OSS advisory summary flow

## Included Pull Requests

- `#121` Harden script wrappers and PT-OSS advisory summary
- `#122` Add v0.2.2 runtime state-flow engine baseline
- `#123` Add authority gate runtime metadata hooks
- `#124` Add normalized evidence event contract
- `#125` Tighten exception trace evidence contract baseline

## Why This Release Matters

`v0.2.2` improves runtime legibility and forensic quality by making exception behavior and authority transitions more explicit, machine-readable, and testable.

## Notes

- this release strengthens contract consistency and auditability
- it does not claim all domain modules enforce every posture yet
- next slices should continue policy enforcement and runtime execution depth (`v0.2.3+`)
