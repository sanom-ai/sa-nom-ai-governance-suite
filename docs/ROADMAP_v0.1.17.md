# Roadmap - v0.1.17

This roadmap captures the next engineering step after `v0.1.16`.

## Theme

Close the `0.1.xx` structure-first phase with a stronger quality-check baseline so SA-NOM enters `0.2.xx` with clearer verification discipline, release gating, and repository-level quality posture.

## Milestone Goal

By the end of `v0.1.17`, a serious evaluator should be able to see that SA-NOM does not only have strong system structure and documentation, but also a clearer and more repeatable verification model for everyday work and release readiness.

## Core Position

The purpose of this milestone is not to chase tool complexity for its own sake.

The purpose is to make the current engineering checks easier to understand, easier to run, and easier to trust before the project moves into deeper enterprise-tier implementation work in `0.2.xx`.

## Engineering Priorities

### 1. Quality Check Matrix

Create a single, readable matrix for the repository's current quality checks.

Target areas:
- lint
- static type checks
- compile checks
- test suite
- coverage-aware test posture
- security audit checks

Expected outcomes:
- contributors understand what exists today
- maintainers can explain which checks are release-relevant
- the repo feels less like hidden CI behavior and more like an explicit verification system

### 2. Release Verification Baseline

Clarify what should be run before a release or major milestone close.

Target areas:
- required checks
- optional checks
- environment-sensitive checks
- release readiness expectations

Expected outcomes:
- release preparation becomes more consistent
- public release discipline looks more intentional
- `0.1.xx` closes with a clearer quality gate posture

### 3. Local Workflow Alignment

Align local contributor workflow with CI and release expectations.

Target areas:
- recommended command sequence
- what should pass before opening a PR
- what should pass before tagging a release
- artifact hygiene and repeatability

Expected outcomes:
- less ambiguity between local work and CI behavior
- contributors can prepare work without guessing the quality bar
- the workflow is easier to scale into `0.2.xx`

### 4. Phase-Close Verification Narrative

Make the repository's quality posture legible as part of the phase close.

Target areas:
- explain what `full option` quality checking means for the current repo
- explain what is already enforced in CI versus documented as recommended baseline
- avoid overclaiming enterprise-grade validation where it does not yet exist

Expected outcomes:
- the end of `0.1.xx` reads as disciplined, not unfinished
- the transition to `0.2.xx` feels deliberate and credible

## Non-Goals For v0.1.17

- do not introduce heavy enterprise tooling just for optics
- do not overclaim that the repository already has every enterprise validation layer
- do not slow the project down with process weight that exceeds current needs
- do not confuse quality-check clarity with full enterprise implementation maturity

## Candidate Deliverables

- `v0.1.17` roadmap and issue drafts
- quality check matrix
- release verification baseline guide
- local workflow alignment updates
- phase-close release notes framing the quality baseline clearly

## Exit Criteria For v0.1.17

- the repository has a clear quality check matrix
- release verification expectations are more explicit
- local and CI quality signals are easier to compare
- `0.1.xx` can close with both structural completeness and a visible verification baseline
