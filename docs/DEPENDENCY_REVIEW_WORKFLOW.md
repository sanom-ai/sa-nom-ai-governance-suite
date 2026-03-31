# Dependency Review Workflow

This guide defines the public workflow for how SA-NOM contributors and maintainers should review dependency changes now that the repository has a lightweight security automation baseline.

## Why This Guide Exists

A CI audit signal is useful only if people know how to respond to it.

After `v0.1.12` introduced `pip-audit` as a lightweight security automation layer, the next step is to make the human review path explicit so dependency changes are not handled ad hoc.

## Core Position

Dependency review in SA-NOM should be:
- lightweight but deliberate
- security-aware without becoming performative
- compatible with self-managed and air-gapped deployment expectations
- explicit about when human judgment overrides automation

The goal is not to ban dependency changes. The goal is to make them understandable, reviewable, and defensible.

## When This Workflow Applies

Use this workflow when a change touches:
- `requirements-dev.txt`
- `pyproject.toml`
- CI steps that install, audit, or validate dependencies
- any future dependency manifest or package-management file
- pull requests that indirectly introduce or remove Python packages

## Contributor Responsibilities

When proposing a dependency-related change, contributors should explain:
- what package is being added, removed, or upgraded
- why the change is needed
- whether the benefit is about correctness, security, maintainability, or workflow support
- what alternatives were considered, especially if the change increases dependency weight
- whether the change affects self-managed, private, or air-gapped usage expectations

A good dependency PR should be small enough that reviewers can understand it quickly.

## Maintainer Review Questions

Maintainers should review dependency changes with a few practical questions in mind:
- does this solve a real problem or only add convenience?
- is the package scope proportionate to the need?
- does this create new operational burden for self-managed deployments?
- does it weaken the dependency-light posture without a strong reason?
- does it change the repo's security or trust story?
- if the CI audit flags something, is the risk acceptable, mitigated, or a blocker?

## How To Read CI Audit Findings

`pip-audit` should be treated as an early warning signal, not an autonomous merge decision-maker.

A finding should trigger review of:
- the affected package and version
- whether a patched version exists
- whether the flagged package is used in a security-sensitive path
- whether the dependency is only a development tool or affects broader trust posture
- whether the issue should block merge or be documented and followed up

## Recommended Response Paths

### 1. Clear Fix Available

If a dependency finding has a clear safer version:
- prefer upgrading to the fixed version in the same PR or a tightly coupled follow-up
- note the resolution in the PR summary when useful

### 2. Acceptable Temporary Exception

If there is no immediate safe upgrade and the dependency is still needed:
- document why the dependency remains necessary
- describe the current limitation honestly
- open a follow-up issue if the risk should remain visible
- avoid pretending the audit result is irrelevant

### 3. Dependency Not Worth Keeping

If the dependency adds more operational or security cost than value:
- remove it
- replace it with a simpler approach where practical
- preserve the dependency-light philosophy when that remains the better engineering choice

## Security-Sensitive Dependency Changes

Dependency changes deserve higher scrutiny when they affect:
- authentication, authorization, token, or session handling
- audit, evidence, or retention paths
- deployment and operational tooling
- backup, restore, or security automation workflows
- provider connectivity or external communications

These changes should be treated as more than routine package maintenance.

## Relationship To Automation

The current automation layer helps surface dependency risk.

It does not replace:
- maintainer judgment
- release readiness review
- operational assessment for self-managed deployments
- documentation updates when the trust posture changes

That human layer remains necessary.

## Relationship To Existing Docs

This guide should be read with:
- [docs/SECURITY_AUTOMATION_BASELINE.md](SECURITY_AUTOMATION_BASELINE.md)
- [docs/SECURITY_AND_DEPENDENCY_HYGIENE.md](SECURITY_AND_DEPENDENCY_HYGIENE.md)
- [SECURITY.md](../SECURITY.md)
- [CONTRIBUTING.md](../CONTRIBUTING.md)

The automation baseline explains what the CI signal is.
This guide explains how people should respond to it.

## Practical Summary

The right public message is:

SA-NOM now treats dependency changes as explicit review events. Automation helps surface risk, but human reviewers still decide whether a dependency is justified, acceptable, or a blocker.
