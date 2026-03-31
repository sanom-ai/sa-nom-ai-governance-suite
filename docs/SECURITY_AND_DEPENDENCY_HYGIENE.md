# Security And Dependency Hygiene

This guide defines the first public baseline for how SA-NOM should talk about dependency hygiene, security posture, and repository-level security discipline.

## Why This Guide Exists

SA-NOM intentionally keeps a lightweight dependency story so the platform remains easier to inspect, easier to self-manage, and easier to deploy in private or air-gapped environments.

A lightweight dependency posture is useful only if it stays deliberate. This guide explains how the project should think about dependency risk, security review, contributor expectations, and the difference between a dependency-light design and neglecting security hygiene.

## Core Position

SA-NOM should be read as:
- dependency-light by design
- security-conscious in contributor workflow
- explicit about what is and is not automated yet
- incremental in hardening rather than performative about enterprise tooling

The goal is not to imitate a large dependency-heavy platform. The goal is to show that lightweight architecture and disciplined security hygiene can coexist.

## Current Baseline

At the current public baseline, the repository already has:
- a public [SECURITY.md](../SECURITY.md) vulnerability-reporting policy
- CI checks for linting, scoped type-checking, compile validation, and tests
- a small development dependency surface in `requirements-dev.txt`
- contributor guidance that already warns against committing secrets and runtime artifacts

At the same time, the repository should remain honest that it does not yet claim:
- comprehensive automated dependency scanning
- full supply-chain attestation
- enterprise-grade runtime hardening by default
- complete vulnerability automation across every deployment environment

## Dependency-Light Does Not Mean Dependency-Negligent

A lightweight dependency posture helps with:
- easier private deployment
- lower third-party attack surface
- simpler air-gapped review
- fewer package-resolution and transitive-risk surprises

But a lightweight posture still requires discipline.

The project should treat every new dependency as an explicit design decision, not as a convenience reflex.

Questions maintainers should ask before adding one:
- does this solve a real correctness, security, or maintainability problem?
- can the same need be met safely with the standard library or existing tooling?
- does this add transitive risk or operational burden for self-managed deployments?
- does this create friction for air-gapped or private-install scenarios?
- does this improve security, or only make the stack look more modern?

## Contributor Expectations

Before adding or upgrading dependencies, contributors should:
- justify why the dependency is needed
- prefer small, well-maintained packages over broad convenience stacks
- keep changes reviewable so dependency impact is easy to inspect
- update docs when the local or CI workflow changes
- avoid sneaking in dependency growth through unrelated pull requests

For development dependencies specifically:
- prefer tooling that strengthens correctness or reviewability
- keep the hardening path incremental
- avoid turning the repo into a dependency-heavy framework pile just to satisfy aesthetics

## Repository Hygiene Expectations

Security hygiene in this repo should include:
- keeping dependency lists short and intentional
- reviewing new tooling additions for operational impact
- making CI checks visible and understandable
- avoiding committed secrets, runtime state, and generated credentials
- treating auth, token, session, audit-integrity, and data-exposure paths as security-sensitive

## CI And Automation Posture

The public baseline should clearly distinguish between what is automated now and what is still manual.

Currently automated in CI:
- `python -m ruff check .`
- `python -m mypy`
- `python -m compileall -q .`
- `python -m pytest _support/tests`

Not yet claimed as fully automated:
- dependency vulnerability scanning
- package provenance or supply-chain attestation
- runtime configuration scanning across deployment environments
- environment-specific secret exposure detection outside the repository workflow

This distinction matters because SA-NOM should look honest, not overstated.

## Security Review Posture For Pull Requests

Security-minded review should be especially alert when a PR changes:
- authentication or authorization behavior
- bootstrap access profiles or credential handling
- session management
- audit integrity or evidence paths
- deployment scripts or environment assumptions
- provider integrations and external service boundaries
- dependency manifests or CI security behavior

If a PR touches one of those areas, reviewers should assume higher scrutiny is appropriate even if the code diff is small.

## Dependency Upgrades And Maintenance

For dependency updates, the preferred posture is:
- keep upgrades intentional, not noisy
- understand why the version is changing
- avoid bundle upgrades with unrelated work where possible
- keep the public docs aligned when tooling expectations change

The project does not need frantic churn. It needs understandable movement.

## Private Deployment And Buyer Trust

Private-deployment buyers often read dependency posture as a signal of operational maturity.

A short dependency list can be a strength if it is paired with:
- explicit review discipline
- clear contributor workflow
- documented security handling expectations
- honest statements about what is and is not automated yet

That is the posture SA-NOM should present.

## Public Baseline And Future Work

This guide defines a public baseline only.

Future hardening may add:
- dependency scanning in CI
- stronger security workflow automation
- more explicit operational recovery checks
- deeper contributor guidance around high-risk code paths

Until then, the right message is:

SA-NOM keeps dependencies intentionally light, but still expects disciplined security review, explicit contributor hygiene, and honest communication about the current automation boundary.
