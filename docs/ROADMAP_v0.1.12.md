# Roadmap - v0.1.12

This roadmap captures the next engineering step after `v0.1.11`.

## Theme

Introduce lightweight security automation and dependency review discipline so SA-NOM moves from documented security posture toward visible, repeatable repository checks without abandoning its dependency-light and self-managed philosophy.

## Milestone Goal

By the end of `v0.1.12`, a serious technical evaluator should be able to see that SA-NOM is not only documenting security expectations, but also starting to automate practical repository-level security checks and dependency review signals.

## Engineering Priorities

### 1. Lightweight Security Scanning Baseline

Add a conservative first automation layer for security-oriented repository checks.

Target areas:
- built-in or low-friction security scanning in CI where practical
- repository-level checks that fit self-managed and air-gapped review culture
- explicit documentation of what is scanned and what is not scanned yet

Expected outcomes:
- security posture becomes more visible in CI
- reviewers get evidence of security hygiene beyond prose alone
- the automation boundary stays honest and incremental

### 2. Dependency Review Discipline

Make dependency changes easier to inspect and reason about.

Target areas:
- lightweight dependency review workflow
- pull-request expectations when dependencies change
- documentation of how maintainers should evaluate new packages or upgrades
- basic automation signals where feasible

Expected outcomes:
- dependency changes look intentional instead of ad hoc
- security-minded reviewers can inspect risk more quickly
- dependency-light philosophy becomes operationally clearer

### 3. CI Security Continuity

Extend the `v0.1.10` and `v0.1.11` hardening work with security-aware CI structure.

Target areas:
- security-oriented checks that complement lint, type-checking, compile validation, and tests
- clearer separation between implemented checks and future-check aspirations
- CI wording that reflects repository trust boundaries accurately

Expected outcomes:
- CI reads more like a practical hardening pipeline
- automation remains understandable instead of bloated
- the repo looks more mature in technical diligence conversations

### 4. Contributor And Maintainer Workflow Hardening

Clarify the human workflow that surrounds new automation.

Target areas:
- contributor instructions for security-sensitive changes
- maintainer expectations for reviewing dependency deltas
- escalation guidance when automation catches suspicious conditions
- consistency between docs, CI, and review habits

Expected outcomes:
- automation is backed by explicit human process
- contributors know what to do when a security-oriented check fails
- maintainers can explain the review path more clearly

## Non-Goals For v0.1.12

- do not market the repo as fully supply-chain-hardened based on this milestone alone
- do not force a large dependency stack just to add fashionable security tooling
- do not blur the line between repository checks and deployment-environment security guarantees
- do not overclaim vulnerability coverage across self-managed operator environments

## Documentation And Contributor Priorities

- document security automation boundaries clearly
- explain dependency-review expectations in plain language
- keep contributor instructions practical and not overly ceremonial
- ensure CI and docs say the same thing about current security scope

## Commercial And Trust Priorities

- strengthen trust with buyers and reviewers who want visible security discipline
- make SA-NOM easier to discuss in technical due diligence and rollout conversations
- show a believable progression from code hardening, to operational hardening, to early automation-backed security posture

## Candidate Deliverables

- `v0.1.12` roadmap and issue drafts
- lightweight security scanning baseline in CI
- dependency review guidance or automation support
- updated contributor and maintainer workflow guidance
- clearer security automation boundary docs

## Exit Criteria For v0.1.12

- the repo has at least one visible lightweight security automation layer
- dependency review expectations are documented more clearly
- CI tells a more complete security-hardening story
- the new automation remains compatible with dependency-light and self-managed deployment philosophy
- SA-NOM looks more operationally and technically credible without overclaiming enterprise security maturity
