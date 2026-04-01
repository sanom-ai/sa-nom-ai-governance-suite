# Release Notes - v0.4.1

## Release Focus

`v0.4.1` is the PTAG polish-and-hardening release after the `v0.4.0` public-opening milestone.

This release focuses on making PTAG easier to start with, easier to evaluate from examples, easier to explain honestly, and safer to evolve through stronger validator coverage.

## Completed Scope

### PTAG Quick Start

- added a short PTAG onboarding path for new readers
- linked the PTAG reading path from the repository README and docs index
- gave readers a simple progression from framework guide to one real PTAG example to the full spec and implementation files

### PTAG Public Examples Expansion

- added a PTAG examples guide that explains what each public-safe example file demonstrates
- expanded the public example set with compact, human-in-the-loop, and enterprise-shaped role packs
- improved the bridge from PTAG syntax to role intent and governance patterns

### PTAG FAQ And Comparison Surface

- added a reusable PTAG FAQ for common reader and evaluator questions
- explained what PTAG is, what it is not, and how it differs from prompts, generic policy configuration, policy engines, orchestration layers, and guardrail layers
- made PTAG easier to position without overstating its current repository scope

### PTAG Validation And Test Hardening

- expanded validator-focused test coverage around structural and semantic PTAG behavior
- added explicit tests for no-block, unsupported-block, missing-authority, unknown-authority, and constraint-coverage paths
- strengthened regression protection for the current PTAG public contract

## Why This Release Matters

`v0.4.1` turns the PTAG public opening from a good announcement into a sturdier working surface.

The repository now gives readers a clearer path to:
- start learning PTAG quickly
- move through a more useful example progression
- answer common PTAG questions without maintainers repeating the same explanation by hand
- trust the validator contract more as PTAG continues to evolve

## Verification

- `python -m pytest _support/tests` passed with `273 passed`
- coverage passed at `82.03%`

## Next Phase

The next milestone after `v0.4.1` should move beyond PTAG polish into broader SA-NOM operational maintenance and human-in-the-loop readiness work, while keeping the PTAG surface stable enough for outside readers and future contributors.

## Notes

- this release closes the PTAG polish-and-hardening phase
- `v0.4.1` strengthens the PTAG public surface without changing the current PTAG syntax contract
- PTAG remains grounded in the existing `.ptn` format while documentation, examples, and validation discipline improve around it
