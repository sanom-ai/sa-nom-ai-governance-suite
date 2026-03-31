# Release Verification Baseline

This document defines the current release verification baseline for SA-NOM.

It should be read together with [Quality Check Matrix](QUALITY_CHECK_MATRIX.md).

The purpose of this guide is to make release readiness explicit so milestone closes and public tags are not treated as informal or purely narrative events.

## Why This Guide Exists

The repository now has a visible quality check matrix.

What was still needed was a simpler answer to a more specific question:
- what should pass before a release is tagged?
- what is required versus recommended?
- what should not be overclaimed yet?

This guide provides that release-focused baseline.

## Core Position

A public release in SA-NOM should mean:
- the repository state is reviewable
- the current baseline checks were considered intentionally
- the project is not pretending to have a deeper enterprise validation stack than it actually has

This guide is meant to improve release discipline without creating unnecessary process weight.

## Current Release Verification Baseline

The current recommended release baseline is:

1. install the development verification toolchain
   - `python -m pip install -r requirements-dev.txt`
2. run lightweight dependency audit
   - `python -m pip_audit -r requirements-dev.txt`
3. run lint checks
   - `python -m ruff check .`
4. run scoped static type checks
   - `python -m mypy`
5. confirm sources compile cleanly
   - `python -m compileall -q .`
6. run the test suite
   - `python -m pytest _support/tests`

## Required Versus Recommended

### Required For The Current Public Baseline

These should be treated as required before tagging a release:
- `python -m ruff check .`
- `python -m mypy`
- `python -m compileall -q .`
- `python -m pytest _support/tests`

### Strongly Recommended For Release Confidence

These should be treated as strongly recommended for a release:
- `python -m pip_audit -r requirements-dev.txt`
- local review that release notes and docs index are aligned
- local review that the release framing does not overclaim feature or security maturity

## Release Readiness Questions

Before tagging a release, maintainers should ask:
- do the current baseline checks pass?
- do the release notes describe the milestone honestly?
- does the release overclaim runtime, security, or enterprise maturity?
- are the relevant docs linked and readable from the docs index?
- if the release closes a phase, does it clearly explain what the next phase will deepen?

If the answer to those questions is unclear, the release is probably not ready yet.

## What This Baseline Does Not Mean

This baseline does not mean that SA-NOM already has:
- full enterprise performance validation
- exhaustive resilience testing
- deep production-failure simulation
- comprehensive end-to-end integration coverage for every future operating lane
- full enterprise security assurance beyond the current public baseline

It means the current public release process is becoming more explicit and repeatable.

## Practical Release Gate Model

Use this simple model:

- `required checks pass`
- `release framing is honest`
- `docs are aligned`
- `tag and release are created intentionally`

That is the right baseline for the current phase of the repository.

## Relationship To Phase Close

For `0.1.xx`, this baseline matters because the project is closing a structure-first phase.

That means the release should communicate not only what changed, but also that the repository now has a more explicit verification posture than it did earlier in the series.

## Relationship To 0.2.xx

This baseline is not the end state.
It is the bridge.

The point of `v0.1.17` is to make the transition into `0.2.xx` cleaner by ensuring:
- the architecture baseline is closed
- the quality baseline is visible
- the release discipline is explicit

That makes deeper enterprise-tier implementation work easier to justify and easier to evaluate.

## Practical Summary

The right public message is:

SA-NOM now has a release verification baseline that makes public tagging more intentional. It is not the final enterprise release gate, but it is explicit, repeatable, and appropriate for closing the `0.1.xx` structure-first phase with clearer quality discipline.
