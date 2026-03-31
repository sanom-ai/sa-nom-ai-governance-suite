# Release Notes v0.1.12

## Release Focus

This release moves SA-NOM from documented security posture into lightweight security automation by turning `v0.1.12` into a clearer baseline for repository-level dependency auditing and dependency review workflow discipline.

The goal of this milestone is not to claim a complete security platform. The goal is to make security hygiene more visible and repeatable in normal repository work while preserving SA-NOM's dependency-light and self-managed philosophy.

## Highlights

- added a lightweight security automation baseline using `pip-audit` in CI
- added a dependency review workflow guide for contributors and maintainers
- updated contributor and security guidance so dependency-related changes have a clearer response path
- kept the automation intentionally narrow, review-oriented, and honest about scope

## Why This Release Matters

After `v0.1.11` improved SA-NOM's security and operational posture in documentation, the next credibility step was to make part of that posture visible in automation.

Technical reviewers want to see not only what the project says about security, but also what the repository actually checks during normal contribution flow.

`v0.1.12` gives SA-NOM an early but practical answer by introducing lightweight dependency auditing in CI and a documented workflow for how humans should respond to dependency-related findings.

## What Was Added In v0.1.12

### Security Automation Planning

- `docs/ROADMAP_v0.1.12.md`
- `docs/ISSUE_DRAFTS_v0.1.12.md`

### Lightweight Security Automation Baseline

- `docs/SECURITY_AUTOMATION_BASELINE.md`
- CI now runs `python -m pip_audit -r requirements-dev.txt`
- `requirements-dev.txt` now includes `pip-audit`

### Dependency Review Workflow

- `docs/DEPENDENCY_REVIEW_WORKFLOW.md`
- `SECURITY.md` and `CONTRIBUTING.md` now point more clearly at the dependency-review response path

## Community Baseline In This Release

The public baseline now includes a clearer security-automation story around:
- lightweight Python dependency auditing in CI
- explicit contributor expectations when dependency-related findings appear
- clearer maintainer review posture for dependency changes
- a more believable progression from documentation-only posture to automation-backed repository hygiene

## Commercial And Trust Direction

This release is about technical trust and reviewability.

It helps SA-NOM look more credible in technical diligence conversations by showing that security posture is starting to appear in repeatable repository controls, not only in markdown guidance.

## Upgrade Notes

- `v0.1.12` is a lightweight security automation milestone, not a full security platform milestone
- the release adds Python dependency auditing in CI, not complete vulnerability coverage for every deployment environment
- dependency findings are still treated as prompts for human review rather than as an autonomous merge policy
- the dependency-light philosophy remains intact while security review becomes more visible in workflow

## Verification Snapshot

Validated during `v0.1.12` work with:
- `python -m compileall -q .`
- `python -m pytest _support/tests`
- local review of the new security automation baseline and dependency review workflow docs
- local review of updated links across CI, contributor, security, and docs-index materials

## Post-Release Follow-Up

Recommended next steps after `v0.1.12`:
- decide whether to introduce additional lightweight security automation beyond Python dependency auditing
- consider whether maintainers want issue-driven follow-up for accepted dependency exceptions
- continue improving the balance between automation signals and explicit human review

## Contact

- Community/commercial/security contact: `sanomaiarch@gmail.com`
