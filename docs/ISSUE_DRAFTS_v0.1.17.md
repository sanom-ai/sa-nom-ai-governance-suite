# Issue Drafts - v0.1.17

Use these draft issues to turn the `v0.1.17` roadmap into implementation work.

## 1. Add Quality Check Matrix

**Goal**
Create a clear matrix for the repository's current quality checks and their purpose.

**Scope ideas**
- lint
- mypy
- compileall
- pytest
- coverage-aware test posture
- pip-audit

**Success signal**
Contributors and reviewers can see the verification surface in one place.

## 2. Add Release Verification Baseline

**Goal**
Document what should be run before a release or phase-close milestone.

**Scope ideas**
- required checks
- optional checks
- environment-sensitive checks
- release readiness expectations

**Success signal**
Release quality posture becomes easier to explain and repeat.

## 3. Align Local Workflow With Quality Baseline

**Goal**
Make local workflow guidance match the quality checks and release gate expectations more clearly.

**Scope ideas**
- local command order
- PR-ready versus release-ready expectations
- artifact hygiene
- repeatability notes

**Success signal**
Contributors can follow a clearer path from local work to release-quality readiness.

## 4. Frame v0.1.xx Phase Close Around Verification Discipline

**Goal**
Prepare phase-close wording so the end of `0.1.xx` reads as both structure-complete and quality-aware.

**Scope ideas**
- release note framing
- docs wording
- explicit statement of what the quality baseline does and does not claim yet

**Success signal**
The transition from `0.1.xx` to `0.2.xx` reads as deliberate and credible.
