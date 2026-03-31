# Security Automation Baseline

This guide defines the first public baseline for how SA-NOM automates lightweight repository-level security checks.

## Why This Guide Exists

After `v0.1.11`, SA-NOM had a clearer documented posture around secrets, dependency hygiene, runtime recovery, and backup and restore validation.

The next step is to make part of that posture visible in automation so reviewers can see a practical security signal in pull requests without turning the repository into a heavy or misleading security platform.

## Core Position

SA-NOM should use security automation that is:
- lightweight
- review-oriented
- honest about scope
- compatible with dependency-light and self-managed deployment philosophy

The goal is not to claim full supply-chain protection. The goal is to make repository-level security hygiene more visible and repeatable.

## Current Automated Baseline

At this stage, the public repository should treat the following as the first security automation baseline:
- CI verification for linting, scoped type-checking, compile validation, and tests
- pull-request dependency review through GitHub automation when dependency manifests change

This baseline helps the repo surface risky dependency changes earlier without pretending that deployment-environment security is fully automated.

## What Dependency Review Helps With

Dependency review automation is useful because it can:
- highlight dependency manifest changes in pull requests
- surface known risk signals around added or changed packages
- make security-sensitive dependency changes easier to inspect before merge
- reinforce the rule that dependency changes should look intentional and reviewable

## What This Baseline Does Not Claim

This automation baseline does not claim:
- full runtime vulnerability scanning for every deployment environment
- enterprise-grade supply-chain attestation
- complete secrets scanning outside repository workflows
- complete operator-environment security validation

Repository automation should stay honest about that boundary.

## Reviewer Expectations

When the dependency review check is triggered, reviewers should still use judgment.

The check should be treated as:
- an early warning layer
- a prompt for human review
- a signal that dependency changes deserve closer attention

It should not be treated as a replacement for maintainer responsibility.

## Contributor Expectations

Contributors should expect that dependency-related pull requests now carry more visible scrutiny.

If a dependency review check fails or flags a concern, contributors should:
- explain why the dependency change is needed
- confirm whether the package is required for correctness, security, or maintainability
- keep the change narrow and easy to review
- update related docs when tooling or workflow expectations change

## Relationship To Existing Docs

This guide should be read with:
- [docs/SECURITY_AND_DEPENDENCY_HYGIENE.md](SECURITY_AND_DEPENDENCY_HYGIENE.md)
- [SECURITY.md](../SECURITY.md)
- [CONTRIBUTING.md](../CONTRIBUTING.md)

The dependency hygiene guide explains the posture.
This guide explains the first automation layer that reinforces it.

## Practical Summary

The right public message is:

SA-NOM now includes a lightweight security automation baseline for pull-request dependency review, while staying explicit that this is an early repository-level control rather than a complete security platform.
