# Contributing

Thanks for helping improve SA-NOM AI Governance Suite.

## Before You Start

- Read [README.md](README.md) for project scope
- Read [SECURITY.md](SECURITY.md) before reporting vulnerabilities
- Keep runtime secrets and generated state out of commits

## Development Setup

1. Use Python 3.14 or newer.
2. Install development tooling:
   - `python -m pip install -r requirements-dev.txt`
3. Run lint checks:
   - `python -m ruff check .`
4. Run scoped static type checks:
   - `python -m mypy`
5. Run the test suite:
   - `python -m pytest _support/tests`

The current `v0.1.10` hardening work is intentionally incremental. Ruff starts with critical lint rules, and mypy starts with a small scoped baseline in `sa_nom_governance.guards` so engineering discipline can improve without forcing a repo-wide rewrite in one pull request.

## Contribution Rules

- prefer small, reviewable pull requests
- add or update tests when behavior changes
- keep examples sanitized and public-safe
- avoid committing `_runtime/` state or generated credentials
- document operator-facing behavior changes in the relevant markdown file
- keep Python linting and scoped type checks clean before opening a pull request

## Pull Request Checklist

- lint checks pass locally
- scoped type checks pass locally
- tests added or updated when behavior changes
- docs updated when needed
- no secrets or runtime state committed
- no machine-local paths left in public docs
- public-facing examples remain generic

## Communication

Open an issue for bug reports, feature requests, or design discussion before large changes.
For security issues, follow [SECURITY.md](SECURITY.md) instead of opening a public issue.
## Secrets Hygiene
- keep real secrets out of tracked files, examples, and docs
- use placeholders in public-safe examples and screenshots
- prefer local-only secret injection or deployment-managed secret stores
- rotate or replace credentials quickly if exposure is suspected
- do not treat AI as the autonomous owner of real deployment credentials

## Dependency Review Signals

- expect dependency-related pull requests to trigger additional review
- explain why any new package or version change is needed
- treat CI audit findings as prompts for human review, not as noise to bypass
- follow [docs/DEPENDENCY_REVIEW_WORKFLOW.md](docs/DEPENDENCY_REVIEW_WORKFLOW.md) when a pull request changes dependencies or audit results
- document accepted exceptions explicitly when a flagged issue is not fixed immediately, and follow [docs/SECURITY_EXCEPTION_WORKFLOW.md](docs/SECURITY_EXCEPTION_WORKFLOW.md)
- keep deferred security work visible through the follow-up path in [docs/SECURITY_FOLLOW_UP_VISIBILITY.md](docs/SECURITY_FOLLOW_UP_VISIBILITY.md)
- when a temporary exception is accepted, prefer opening the `Security exception` issue template so ownership, revisit timing, and escalation posture stay visible
- AI may help summarize the finding and prepare issue context, but human maintainers still decide exception, escalation, merge-blocking outcomes, and whether follow-up visibility is adequate
- when deferred work needs to stay visible after merge, prefer opening the `Security follow-up` issue template so ownership and revisit timing stay linked to the accepted risk

