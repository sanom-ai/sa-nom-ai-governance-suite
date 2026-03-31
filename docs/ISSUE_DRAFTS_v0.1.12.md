# Issue Drafts - v0.1.12

Use these draft issues to turn the `v0.1.12` roadmap into implementation work.

## 1. Add Lightweight Security Scanning Baseline

**Goal**
Add a first conservative security-oriented CI check that improves repository trust without introducing heavy operational complexity.

**Scope ideas**
- choose a lightweight scanning step appropriate for the current stack
- document what the check covers and what it does not cover
- keep the setup compatible with self-managed and private review expectations

**Success signal**
CI exposes a visible security-oriented check and the repo stays honest about the resulting automation boundary.

## 2. Add Dependency Review Workflow Guidance

**Goal**
Make dependency additions and upgrades easier to review and justify.

**Scope ideas**
- document review questions for new packages and upgrades
- define pull-request expectations for dependency-related changes
- align contributor and maintainer guidance with the dependency-light philosophy

**Success signal**
Dependency changes look more intentional and reviewers have a clearer checklist for evaluating them.

## 3. Extend CI With Security-Hardening Continuity

**Goal**
Connect security automation into the existing hardening pipeline without turning CI into a noisy or inflated system.

**Scope ideas**
- add a security-aware CI step or reporting layer
- clarify which checks are implemented now versus future work
- keep CI readable and proportionate to the repo's maturity

**Success signal**
The hardening pipeline reads as cumulative and security-aware rather than fragmented.

## 4. Update Contributor And Maintainer Security Workflow

**Goal**
Document what contributors and maintainers should do when security-oriented checks fail or when a PR touches security-sensitive areas.

**Scope ideas**
- contributor expectations for responding to failed checks
- maintainer review posture for auth, token, session, audit, and dependency changes
- tighter linkage between `SECURITY.md`, contributor docs, and new CI behavior

**Success signal**
The human review path around new automation becomes clearer and easier to follow.
