# Roadmap - v0.1.10

This roadmap captures the next engineering step after `v0.1.9`.

## Theme

Harden SA-NOM's Python engineering discipline so the codebase better matches the seriousness of its governance domain without abandoning the project's dependency-light, self-managed, and air-gapped-friendly philosophy.

## Milestone Goal

By the end of `v0.1.10`, a serious evaluator should be able to see that SA-NOM is not only strong in governance design and workflow coverage, but also improving its engineering discipline around consistency, type safety, automated quality checks, and test visibility.

## Engineering Priorities

### 1. Formatting And Lint Discipline

Introduce a lightweight but enforceable formatting and lint layer.

Target areas:
- repository-wide lint policy
- consistent formatting policy
- import hygiene and unused-code detection
- CI enforcement for formatting and lint failures

Expected outcomes:
- contributors do not rely only on manual style discipline
- refactors become safer and easier to review
- the codebase reads more consistently across modules
- quality gates become more visible to outside evaluators

### 2. Static Type Checking Baseline

Add a realistic static type-checking baseline without pretending the entire repo can be fully typed in one milestone.

Target areas:
- choose and configure `pyright` or `mypy`
- define the first typed modules and boundaries
- add typed contracts for core service layers and registries
- document where partial typing is intentional and where stricter typing is required

Expected outcomes:
- policy, role, compliance, and runtime boundaries become easier to reason about
- regression risk drops in core modules
- contributors can see where stronger type guarantees are expected
- SA-NOM's explicit-governance story becomes more credible at the code level

### 3. Test Visibility And Coverage Discipline

Keep the current test breadth, but make test expectations easier to measure and harder to silently erode.

Target areas:
- add coverage reporting
- define a practical minimum coverage gate or baseline policy
- identify core correctness areas that deserve stronger edge-case tests
- separate smoke coverage from deeper correctness and regression coverage

Expected outcomes:
- the project can show not only that tests exist, but where confidence is strongest
- governance-critical areas such as audit integrity, PT-OSS, retention, and validation become easier to defend
- test growth becomes more intentional over time

### 4. CI Hardening

Upgrade CI from basic verification into clearer engineering quality enforcement.

Target areas:
- lint and format checks in CI
- static type checks in CI
- coverage reporting in CI
- clearer CI steps and failure visibility

Expected outcomes:
- contributors and reviewers get faster feedback
- the public repo looks more disciplined to technical evaluators
- the project moves closer to a production-grade engineering posture without changing its runtime philosophy

### 5. Packaging And Release Metadata Cleanup

Align package metadata and release posture so the Python package story does not lag behind the GitHub release story.

Target areas:
- sync package versioning with release cadence
- review `pyproject.toml` metadata quality
- document intended install and development flows more clearly
- reduce ambiguity around project maturity and release state

Expected outcomes:
- outside readers see a cleaner packaging story
- release mechanics look more intentional
- repo metadata stops undercutting the product and documentation progress

## Non-Goals For v0.1.10

- do not replace the standard-library-first philosophy with a dependency-heavy rewrite
- do not force a migration to FastAPI, Pydantic, or other framework swaps as the headline outcome
- do not treat engineering hardening as permission to weaken the private, air-gapped, self-managed posture
- do not pause product-direction work forever; this milestone should strengthen the foundation for later feature work

## Documentation And Contributor Priorities

- explain the new engineering quality gates clearly
- document local development commands for lint, type-checking, tests, and coverage
- make it easier for future contributors to follow the house rules without guesswork
- preserve the project's plain-language, operator-readable documentation style

## Commercial And Trust Priorities

- make the public repo look more credible to technical buyers and reviewers
- show that SA-NOM can accept serious engineering feedback and convert it into disciplined improvement
- strengthen confidence that governance claims are backed by improving implementation rigor

## Candidate Deliverables

- `v0.1.10` engineering roadmap and issue drafts
- lint and formatting tooling with CI integration
- first-pass static type-checking config and scoped typed modules
- coverage reporting and a documented test-visibility policy
- package metadata cleanup aligned with current release practice
- contributor-facing development workflow updates

## Exit Criteria For v0.1.10

- lint and format discipline exist and are enforced in CI
- a real static type-checking baseline exists for at least the most critical modules
- coverage reporting is visible and part of the engineering conversation
- package and release metadata look more intentional and less misleading
- SA-NOM still preserves its dependency-light, self-managed, and air-gapped-friendly identity while looking materially more production-ready
