# Security Exception Workflow

This guide defines the public workflow for how SA-NOM should handle security findings or dependency-audit results that are not fixed immediately.

## Why This Guide Exists

A lightweight security automation signal is useful only if the project also explains what happens when a finding cannot be resolved right away.

After `v0.1.12`, SA-NOM already had:
- a lightweight `pip-audit` baseline in CI
- a dependency review workflow for contributors and maintainers

The next step is to make accepted exceptions and deferred fixes explicit so security findings do not disappear silently.

## Core Position

A security exception in SA-NOM should be:
- explicit
- justified
- owned
- time-bound or milestone-bound when practical
- visible enough for future review

The goal is not to normalize unresolved findings. The goal is to keep temporary exceptions disciplined when an immediate fix is not yet practical.

## When This Workflow Applies

Use this workflow when:
- `pip-audit` or another lightweight security signal flags a finding
- the issue cannot be fixed immediately in the same PR
- maintainers still believe merge may be acceptable with additional review and follow-up

This workflow is not meant to justify silent acceptance of serious trust-impacting risk.

## What A Proper Exception Should Include

A temporary exception should record at least:
- what finding or risk is being accepted
- which package, version, or code path is affected
- why the issue cannot be fixed immediately
- why the current risk is still considered tolerable for now
- who owns the follow-up
- what milestone, issue, or review point should revisit the exception

## When A Finding Should Block Merge

A finding should lean toward blocking merge when it affects:
- authentication, authorization, token, or session paths
- audit integrity, evidence handling, or retention-sensitive flows
- deployment trust boundaries or signing posture
- secrets handling or recovery credentials
- high-confidence runtime-impacting vulnerabilities without a reasonable mitigation path

If maintainers cannot explain why the risk is acceptable, it should not be accepted casually.

## When A Temporary Exception May Be Reasonable

A temporary exception may be reasonable when:
- the finding affects a low-impact development dependency rather than a trust-critical runtime path
- there is no practical fix yet, but the limitation is understood
- the current repository use does not expose the issue in the same way as a production deployment would
- follow-up ownership is explicit and the issue will not disappear after merge

Even then, the exception should still be documented and reviewed.

## Recommended Exception Workflow

1. identify the finding clearly
2. determine whether it affects a trust-critical or lower-impact path
3. decide whether merge should block or whether a temporary exception is defensible
4. record the justification in the PR or linked follow-up item
5. assign clear follow-up ownership
6. revisit the exception in the stated milestone or maintenance cycle

This keeps exceptions visible and reviewable instead of accidental.

## Follow-Up Visibility

If an exception is accepted, maintainers should prefer that the follow-up remains visible through:
- a linked issue
- a milestone note
- explicit PR language describing the deferred fix

The important thing is that accepted risk stays attributable and revisit-able.

## Human And Automation Boundary

Automation may surface the finding.

Humans still decide:
- whether the finding is real and relevant
- whether the affected path is trust-critical
- whether a temporary exception is acceptable
- whether the issue must block merge
- who owns the follow-up

This boundary should remain explicit.

## Relationship To Existing Docs

This guide should be read with:
- [docs/SECURITY_AUTOMATION_BASELINE.md](SECURITY_AUTOMATION_BASELINE.md)
- [docs/DEPENDENCY_REVIEW_WORKFLOW.md](DEPENDENCY_REVIEW_WORKFLOW.md)
- [docs/SECURITY_AND_DEPENDENCY_HYGIENE.md](SECURITY_AND_DEPENDENCY_HYGIENE.md)
- [SECURITY.md](../SECURITY.md)
- [CONTRIBUTING.md](../CONTRIBUTING.md)

The automation baseline explains the signal.
The dependency review workflow explains how to read it.
This guide explains how to handle the cases that are not fixed immediately.

## Practical Summary

The right public message is:

SA-NOM does not treat unresolved security findings as invisible. If a finding is temporarily accepted, that exception should be explicit, justified, owned, and revisited.
