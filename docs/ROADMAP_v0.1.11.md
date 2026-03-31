# Roadmap - v0.1.11

This roadmap captures the next engineering step after `v0.1.10`.

## Theme

Strengthen SA-NOM's security posture and operational resilience so the platform looks more credible for self-managed, private, and air-gapped deployment scenarios without breaking its lightweight deployment philosophy.

## Milestone Goal

By the end of `v0.1.11`, a serious evaluator should be able to see that SA-NOM is not only improving code quality, but also becoming more intentional about secrets handling, operational recovery, dependency hygiene, and runtime-risk documentation.

## Engineering Priorities

### 1. Secrets And Credentials Handling Baseline

Make secrets handling more explicit and safer at the documentation and workflow level.

Target areas:
- secrets and credentials policy
- local-development secret hygiene
- deployment-facing credential expectations
- runtime artifact boundaries

Expected outcomes:
- contributors understand where secrets belong and where they do not
- local and deployment workflows are less likely to leak sensitive data
- the self-managed story looks more operationally mature

### 2. Security And Dependency Hygiene

Add a first security-hygiene layer around dependencies and repository health.

Target areas:
- dependency scanning or documentation of dependency review posture
- security-oriented CI checks where practical
- vulnerability-awareness workflow for contributors and maintainers
- clearer guidance on dependency-light posture versus dependency neglect

Expected outcomes:
- the repo looks more credible to security-minded reviewers
- dependency risk becomes more visible and less ad hoc
- security hardening looks intentional rather than implied

### 3. Runtime Failure And Recovery Posture

Document how SA-NOM should be understood under failure conditions.

Target areas:
- runtime failure modes
- recovery expectations
- backup and restore posture
- restore validation and operator responsibilities

Expected outcomes:
- the platform reads more like a real operational system
- teams can reason about recovery and continuity more clearly
- the gap between governance design and runtime operations narrows further

### 4. Operational Readiness Documentation

Deepen the operational guidance that surrounds private deployment.

Target areas:
- backup and restore validation
- resilience expectations
- environment-readiness checks
- security and runtime responsibilities for self-managed operators

Expected outcomes:
- technical buyers get a clearer picture of operational ownership
- air-gapped and private-deployment stories become more complete
- deployment trust increases without pretending full enterprise maturity already exists

### 5. CI And Hardening Continuity

Extend the `v0.1.10` hardening work into security and operational checks where feasible.

Target areas:
- CI hooks for security-oriented validation
- documentation of what is and is not automated yet
- keeping hardening incremental instead of turning it into a disruptive rewrite

Expected outcomes:
- the hardening story feels cumulative instead of fragmented
- contributors can see a clear path from code quality to operational quality

## Non-Goals For v0.1.11

- do not market the repo as fully enterprise-hardened or regulator-ready based on this milestone alone
- do not force a dependency-heavy security stack just to look modern
- do not blur the line between documented operational posture and fully automated runtime safeguards
- do not turn self-managed flexibility into a brittle operations burden

## Documentation And Contributor Priorities

- document secrets handling and local operational hygiene clearly
- explain recovery and restore expectations in plain language
- make the security and operational story easier to inspect for technical reviewers
- keep docs practical for self-managed and private-deployment users

## Commercial And Trust Priorities

- strengthen confidence for private-deployment buyers who care about operational rigor
- make SA-NOM easier to discuss in technical diligence conversations
- show that the project is evolving from governance and code hardening toward operational hardening as well

## Candidate Deliverables

- `v0.1.11` security and operational roadmap and issue drafts
- secrets and credentials handling guide
- security and dependency hygiene guide
- runtime failure and recovery guide
- backup and restore validation guide
- optional CI or contributor-facing security hardening updates

## Exit Criteria For v0.1.11

- secrets handling expectations are documented clearly
- the project has a clearer public position on dependency and security hygiene
- runtime failure and recovery posture are easier to explain
- operational hardening reads like a real next step after engineering hardening
- SA-NOM still preserves its dependency-light, self-managed, and private-deployment identity while looking more operationally credible
