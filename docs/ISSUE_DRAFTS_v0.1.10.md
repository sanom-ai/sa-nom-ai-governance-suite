# Issue Drafts - v0.1.10

Use these drafts to seed the engineering hardening milestone after `v0.1.9`.

## 1. Add repository lint and format policy

- Title: `Add repository lint and format policy`
- Labels: `engineering`, `quality`, `v0.1.10`
- Milestone: `v0.1.10`

```md
## Summary
Add an enforceable lint and formatting layer for the SA-NOM Python codebase.

## Problem
The repo has meaningful functionality and test coverage, but style and consistency are still enforced mostly by manual discipline.

## Proposed Direction
Introduce lightweight lint and formatting tooling, document the standard, and wire it into CI.

## Acceptance Criteria
- lint and formatting commands are documented
- CI fails on lint or formatting drift
- the chosen tooling remains compatible with the project's dependency-light philosophy
```

## 2. Add static type-checking baseline for core modules

- Title: `Add static type-checking baseline for core modules`
- Labels: `engineering`, `quality`, `v0.1.10`
- Milestone: `v0.1.10`

```md
## Summary
Add a first static type-checking baseline for the most critical SA-NOM modules.

## Problem
The codebase already uses some type hints, but there is no enforced type-checking layer that protects core contracts.

## Proposed Direction
Choose `pyright` or `mypy`, configure it realistically, and begin with core modules such as API, audit, compliance, PT-OSS, and key registries.

## Acceptance Criteria
- a type-checking tool is configured and documented
- CI runs the type checker
- at least the initial critical-module scope is covered
- partial typing is explicit rather than accidental
```

## 3. Add test coverage reporting and baseline policy

- Title: `Add test coverage reporting and baseline policy`
- Labels: `engineering`, `quality`, `testing`, `v0.1.10`
- Milestone: `v0.1.10`

```md
## Summary
Add coverage reporting and a practical coverage policy for SA-NOM.

## Problem
The repo has many tests, but there is no visible coverage signal or shared rule for how coverage should be interpreted.

## Proposed Direction
Introduce coverage reporting, define a baseline policy, and distinguish smoke coverage from deeper correctness coverage.

## Acceptance Criteria
- coverage reporting is part of the standard test flow
- coverage results are visible in CI or review output
- the baseline policy is documented
- core governance-critical areas are identified for stronger edge-case testing
```

## 4. Harden CI quality gates

- Title: `Harden CI quality gates`
- Labels: `engineering`, `quality`, `ci`, `v0.1.10`
- Milestone: `v0.1.10`

```md
## Summary
Expand CI from basic compile-and-test verification into clearer engineering quality gates.

## Problem
Current CI proves that code compiles and tests run, but it does not yet enforce lint, type safety, or coverage expectations.

## Proposed Direction
Add lint, format, type-checking, and coverage steps to CI with readable job output and clear failure boundaries.

## Acceptance Criteria
- CI includes quality gates beyond compile and pytest
- failures are easy to interpret
- contributor workflow stays practical for a self-managed repo
```

## 5. Align package metadata with release practice

- Title: `Align package metadata with release practice`
- Labels: `engineering`, `quality`, `release`, `v0.1.10`
- Milestone: `v0.1.10`

```md
## Summary
Clean up package metadata so the Python package story matches the actual release cadence and maturity of the repo.

## Problem
Project metadata can undercut confidence when package versioning and release practice drift apart.

## Proposed Direction
Review and update `pyproject.toml`, package versioning, and release-facing metadata to reduce ambiguity.

## Acceptance Criteria
- package metadata is reviewed and updated
- versioning no longer looks disconnected from tagged releases
- development and install expectations are documented more clearly
```

## 6. Document contributor development workflow

- Title: `Document contributor development workflow`
- Labels: `documentation`, `engineering`, `v0.1.10`
- Milestone: `v0.1.10`

```md
## Summary
Document the local development workflow for linting, type-checking, tests, and coverage.

## Problem
Even strong tooling can be underused if the contributor workflow remains implicit.

## Proposed Direction
Add a contributor-focused workflow guide that shows the standard local commands and explains the expected quality gates.

## Acceptance Criteria
- contributors can see the expected local workflow in one place
- lint, type-check, test, and coverage commands are documented
- the guide stays lightweight and readable
```
