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
4. Run the test suite:
   - `python -m pytest _support/tests`

This first `v0.1.10` quality gate is intentionally conservative. It starts with critical Ruff checks so the repo can improve engineering discipline without forcing a full style rewrite in one pull request.

## Contribution Rules

- prefer small, reviewable pull requests
- add or update tests when behavior changes
- keep examples sanitized and public-safe
- avoid committing `_runtime/` state or generated credentials
- document operator-facing behavior changes in the relevant markdown file
- keep Python linting clean before opening a pull request

## Pull Request Checklist

- lint checks pass locally
- tests added or updated when behavior changes
- docs updated when needed
- no secrets or runtime state committed
- no machine-local paths left in public docs
- public-facing examples remain generic

## Communication

Open an issue for bug reports, feature requests, or design discussion before large changes.
For security issues, follow [SECURITY.md](SECURITY.md) instead of opening a public issue.
