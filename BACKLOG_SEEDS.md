# Backlog Seeds

Use these as candidate issues for the first post-launch refinement cycle.

## Community Baseline

- Add a documented `pyproject.toml` or packaging path for cleaner local setup.
- Add troubleshooting guidance for common startup validation failures.
- Expand examples for owner registration, access profiles, and trusted registry refresh.
- Add a public-safe smoke-test script for first-time evaluators.
- Review CI coverage and decide whether compile-only verification should expand.

## Documentation

- Add screenshots or a short product tour to the README or docs.
- Document common operator workflows: registration, delegated access, readiness, and release hygiene.
- Add a FAQ covering AGPL obligations, self-hosting, and commercial support boundaries.

## Commercial Layer

- Clarify commercial feature packaging for Starter vs Professional.
- Define a standard discovery-call checklist based on the sales intake template.
- Prepare a concise evaluation guide for organizations deciding between community and commercial paths.

## Quality and Operations

- Run full `pytest` in a clean environment and capture any failures as concrete issues.
- Audit line-ending normalization and decide on a `.gitattributes` policy.
- Review `_support/tests` fixtures for any remaining assumptions that should become more public-neutral.

