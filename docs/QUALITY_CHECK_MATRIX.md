# Quality Check Matrix

This document defines the current quality check matrix for SA-NOM.

It exists so contributors, maintainers, and evaluators can see the repository's current verification surface in one place instead of inferring it from CI, contributor guidance, and release habits separately.

## Why This Guide Exists

SA-NOM now has a meaningful quality baseline across linting, static checks, compile checks, tests, and lightweight security audit steps.

What was still missing was one document that explains:
- what checks exist
- where they run
- when they should run
- which checks matter most for pull requests versus releases

That is the purpose of this matrix.

## Core Position

The current quality baseline is intentionally practical.

The repository should be readable as:
- disciplined enough to support trust and contributor clarity
- not yet pretending to be a fully mature enterprise validation stack

The goal is explicitness, repeatability, and phase-close confidence.

## Quality Check Matrix

| Check | Purpose | Local | CI | Recommended Before PR | Recommended Before Release |
| --- | --- | --- | --- | --- | --- |
| `python -m pip install -r requirements-dev.txt` | install the development verification toolchain | yes | yes | yes | yes |
| `python -m pip_audit -r requirements-dev.txt` | lightweight dependency vulnerability signal | optional | yes | recommended for dependency-sensitive work | yes |
| `python -m ruff check .` | lint Python sources and catch basic quality issues | yes | yes | yes | yes |
| `python -m mypy` | scoped static type-checking baseline | yes | yes | yes | yes |
| `python -m compileall -q .` | confirm Python sources compile cleanly | yes | yes | yes | yes |
| `python -m pytest _support/tests` | run the repository's current test suite | yes | yes | yes | yes |

## How To Read The Matrix

### Required Baseline

The practical required baseline for the current repository is:
- lint
- mypy baseline
- compileall
- pytest

These are the checks that most directly reflect current CI expectations.

### Security-Oriented Baseline

`pip-audit` is also important, especially when:
- dependencies change
- a release is being prepared
- the repository is closing a milestone related to security or operational posture

It should be treated as part of the repository's quality signal, not as disposable noise.

## Pull Request Readiness

Before opening a pull request, the recommended local sequence is:

1. `python -m pip install -r requirements-dev.txt`
2. `python -m ruff check .`
3. `python -m mypy`
4. `python -m compileall -q .`
5. `python -m pytest _support/tests`

If the PR changes dependencies or security-sensitive workflow, also run:
6. `python -m pip_audit -r requirements-dev.txt`

## Release Readiness

Before tagging a release, the recommended baseline is:
- `python -m pip_audit -r requirements-dev.txt`
- `python -m ruff check .`
- `python -m mypy`
- `python -m compileall -q .`
- `python -m pytest _support/tests`

Release readiness should be read as a stronger expectation than ordinary PR readiness.

## What This Matrix Does Not Claim

This matrix does not claim that SA-NOM already has:
- full enterprise-grade performance testing
- deep resilience testing
- exhaustive security scanning across every deployment environment
- comprehensive integration testing for every future module

The matrix reflects the current public verification baseline, not the final enterprise state.

## Relationship To Other Docs

Read this guide with:
- [ROADMAP v0.1.17](ROADMAP_v0.1.17.md)
- [CONTRIBUTING.md](../CONTRIBUTING.md)
- [Security Automation Baseline](SECURITY_AUTOMATION_BASELINE.md)
- [Dependency Review Workflow](DEPENDENCY_REVIEW_WORKFLOW.md)

## Practical Summary

The right public message is:

SA-NOM now has a visible quality check baseline that covers linting, static checks, compile validation, test execution, and lightweight dependency audit signals. It is not the final enterprise validation stack, but it is explicit, repeatable, and strong enough to close the `0.1.xx` structure-first phase with clearer verification discipline.
