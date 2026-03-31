# Release Notes v0.1.10

## Release Focus

This release strengthens SA-NOM's engineering discipline without changing its core philosophy. The goal of `v0.1.10` is to make the codebase read more like a serious, hardening production track by adding lint enforcement, scoped static type-checking, coverage visibility, package metadata alignment, and a clearer contributor workflow.

## Highlights

- added the first CI-backed lint gate using `ruff`
- added the first scoped static type-checking baseline using `mypy`
- added test coverage visibility in CI with `pytest-cov`
- aligned package metadata with the current release cadence
- added a dedicated contributor development workflow guide
- kept the hardening work incremental and compatible with SA-NOM's dependency-light, self-managed, and air-gapped-friendly direction

## Why This Release Matters

SA-NOM already had meaningful governance design, workflow depth, and test breadth.

What it still needed was stronger engineering discipline around code consistency, typed boundaries, test visibility, and contributor workflow clarity.

`v0.1.10` begins that work in a staged way.

It shows that the project can accept technical feedback and turn it into structured hardening without abandoning the product's practical deployment philosophy.

## What Was Added In v0.1.10

### Engineering Hardening Planning

- `docs/ROADMAP_v0.1.10.md`
- `docs/ISSUE_DRAFTS_v0.1.10.md`

### Lint And Format Foundation

- `ruff` added as the first CI lint gate
- initial conservative lint policy documented in `pyproject.toml`
- contributor guidance updated in `CONTRIBUTING.md`

### Scoped Static Type-Checking Baseline

- `mypy` added as a scoped baseline
- initial scope starts in `sa_nom_governance.guards`
- first typed hardening fixes landed in guard-layer code paths

### Coverage Visibility Baseline

- `pytest-cov` added to development tooling
- CI now surfaces coverage output
- `docs/TEST_COVERAGE_POLICY.md` added

### Contributor Workflow And Packaging Cleanup

- `docs/DEVELOPMENT_WORKFLOW.md` added
- package metadata aligned in `pyproject.toml`
- local coverage artifacts ignored via `.gitignore`

## Community Baseline In This Release

The public baseline now includes a clearer engineering-quality story around:
- CI-backed lint enforcement
- a first scoped static type-checking baseline
- visible coverage reporting
- contributor workflow documentation
- package metadata that better matches the project's real release state

## Commercial And Trust Direction

This release is not primarily about commercial packaging. It is about trust and technical credibility.

By improving engineering discipline in public, SA-NOM becomes easier to evaluate for technical buyers, reviewers, and contributors who want evidence that governance claims are backed by disciplined implementation work.

## Upgrade Notes

- `v0.1.10` is an engineering hardening milestone, not a new runtime feature milestone
- lint, type-checking, and coverage visibility all begin with intentionally scoped baselines rather than repo-wide enforcement in one step
- package metadata now better reflects the active development line
- contributor workflow expectations are now documented in one place

## Verification Snapshot

Validated during `v0.1.10` work with:
- `python -m ruff check .`
- `python -m mypy`
- `python -m compileall -q .`
- `python -m pytest _support/tests`
- `python -m pytest --cov=sa_nom_governance --cov-report=term-missing _support/tests`

## Post-Release Follow-Up

Recommended next steps after `v0.1.10`:
- decide whether to deepen static typing into more modules or introduce a stricter scope gate
- decide whether to add a real coverage threshold after more module-level testing work
- consider whether contributor workflow automation or pre-commit support should be added in the next hardening round

## Contact

- Community/commercial/security contact: `sanomaiarch@gmail.com`
