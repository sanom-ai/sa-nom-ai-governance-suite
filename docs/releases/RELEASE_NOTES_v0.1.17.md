# Release Notes - v0.1.17

## Release Focus

`v0.1.17` closes the `0.1.xx` phase with a clearer quality and release verification baseline.

The goal of this milestone is not to add a new runtime feature. The goal is to make SA-NOM's phase-close posture more credible by showing that the project now ends its structure-first phase with both architecture clarity and explicit verification discipline.

## What Changed

### Planning And Phase-Close Direction

- added `docs/ROADMAP_v0.1.17.md`
- added `docs/ISSUE_DRAFTS_v0.1.17.md`

### Quality Baseline Artifacts

- added `docs/QUALITY_CHECK_MATRIX.md`
- added `docs/RELEASE_VERIFICATION_BASELINE.md`

### Workflow Alignment

- updated `CONTRIBUTING.md`
- updated `docs/README.md`

## Why This Release Matters

By the end of `v0.1.16`, SA-NOM had already completed the structure-first blueprint set.

What was still useful before entering `0.2.xx` was one more release that made the repository's current verification baseline easier to inspect and easier to repeat.

`v0.1.17` provides that phase-close discipline by making the following explicit:
- what quality checks exist
- which checks are expected before a release
- what the current public verification baseline does and does not claim
- that SA-NOM's private-first local model path was also exercised successfully on a real machine before the phase was closed

## What Was Added In v0.1.17

### Quality Check Matrix

- `docs/QUALITY_CHECK_MATRIX.md`

This document explains the repository's current quality checks in one place, including local versus CI expectations and pull-request versus release relevance.

### Release Verification Baseline

- `docs/RELEASE_VERIFICATION_BASELINE.md`

This document explains what should be treated as required or strongly recommended before a release is tagged.

## Community Baseline In This Release

The public baseline now includes:
- a clearer quality check matrix
- a clearer release verification baseline
- contributor guidance that points more directly at those quality expectations
- a small but real local private-model validation use case on the maintainer machine

This means the `0.1.xx` line now ends with both:
- structure-first documentation completeness
- a more visible and repeatable verification posture

## What 0.1.xx Now Represents

With `v0.1.17`, the `0.1.xx` series should be read as the completed structure-first and verification-baseline phase for SA-NOM.

That phase now includes:
- product identity and system narrative
- governance language and structural intelligence framing
- document, compliance, and security workflow baselines
- engineering hardening baseline
- system blueprint documents
- quality and release verification baseline

## Upgrade Notes

- `v0.1.17` is a quality-baseline phase-close milestone, not a runtime feature milestone
- the release is meant to close `0.1.xx` cleanly before enterprise-tier implementation work in `0.2.xx`
- the verification baseline is explicit and repeatable, but it should not be mistaken for a final enterprise validation stack
- the local Ollama validation in this release is a phase-close use case that shows the private-model path works on a real machine, not a claim of full production readiness

## Verification Snapshot

Validated during `v0.1.17` work with:
- `python -m compileall -q .`
- local review of quality matrix and release verification wording
- local verification that the new release notes are linked from `docs/README.md`
- local Ollama validation with `SANOM_OLLAMA_MODEL=gemma3:1b`
- `python scripts/provider_demo_flow.py --provider ollama --probe`
- `python scripts/provider_smoke_test.py --provider ollama`
- `python scripts/private_server_smoke_test.py`
- successful local probe and smoke results including provider readiness, `PONG` response, and a passing private-server smoke path

## Suggested Next Step

After `v0.1.17`, the natural next step is `0.2.xx` work focused on enterprise-tier implementation depth: governed runtime orchestration, authority and decision engine hardening, stronger evidence execution, and deeper operational robustness in code.
