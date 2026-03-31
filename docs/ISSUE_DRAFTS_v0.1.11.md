# Issue Drafts - v0.1.11

Use these drafts to seed the security and operational hardening milestone after `v0.1.10`.

## 1. Add secrets and credentials handling guide

- Title: `Add secrets and credentials handling guide`
- Labels: `security`, `operations`, `documentation`, `v0.1.11`
- Milestone: `v0.1.11`

```md
## Summary
Add a clear secrets and credentials handling guide for SA-NOM.

## Problem
The repo now has stronger engineering discipline, but it still needs clearer guidance on how secrets, tokens, and runtime credentials should be handled in development and deployment.

## Proposed Direction
Document secret boundaries, safe local practices, and deployment expectations for self-managed and private environments.

## Acceptance Criteria
- secrets handling rules are explicit
- local and deployment boundaries are documented
- the guidance stays compatible with self-managed and private deployment
```

## 2. Add security and dependency hygiene guide

- Title: `Add security and dependency hygiene guide`
- Labels: `security`, `engineering`, `documentation`, `v0.1.11`
- Milestone: `v0.1.11`

```md
## Summary
Add a security and dependency hygiene guide for SA-NOM.

## Problem
The project is intentionally dependency-light, but it still needs a clearer public posture on how dependency risk and security hygiene should be handled.

## Proposed Direction
Document dependency review expectations, security-oriented maintenance rules, and the boundary between lightweight design and weak security posture.

## Acceptance Criteria
- dependency hygiene expectations are documented
- security posture is easier to explain to technical reviewers
- the guidance does not force a dependency-heavy rewrite
```

## 3. Add runtime failure and recovery guide

- Title: `Add runtime failure and recovery guide`
- Labels: `operations`, `documentation`, `resilience`, `v0.1.11`
- Milestone: `v0.1.11`

```md
## Summary
Add a runtime failure and recovery guide for SA-NOM.

## Problem
The repo has deployment and governance depth, but it still needs a clearer explanation of failure-mode expectations and recovery posture.

## Proposed Direction
Document runtime failure scenarios, operator responsibilities, and practical recovery expectations for self-managed environments.

## Acceptance Criteria
- failure and recovery posture are explained clearly
- operator responsibility is explicit
- the guidance fits private and air-gapped deployment stories
```

## 4. Add backup and restore validation guide

- Title: `Add backup and restore validation guide`
- Labels: `operations`, `documentation`, `resilience`, `v0.1.11`
- Milestone: `v0.1.11`

```md
## Summary
Add a backup and restore validation guide for SA-NOM.

## Problem
The project needs a stronger operational story around backup integrity and restore confidence.

## Proposed Direction
Document what should be backed up, how restore validation should be approached, and how this fits the broader self-managed runtime posture.

## Acceptance Criteria
- backup scope is documented
- restore validation expectations are documented
- the guidance is practical for operators and technical reviewers
```

## 5. Add security-oriented CI and workflow follow-up

- Title: `Add security-oriented CI and workflow follow-up`
- Labels: `security`, `engineering`, `ci`, `v0.1.11`
- Milestone: `v0.1.11`

```md
## Summary
Add the next practical security-oriented CI and workflow improvements for SA-NOM.

## Problem
The project now has lint, mypy, and coverage visibility, but it still needs a clearer next step for security-facing automation and workflow checks.

## Proposed Direction
Identify low-friction security-oriented checks or workflow rules that strengthen hardening without destabilizing the self-managed philosophy.

## Acceptance Criteria
- the next security automation step is explicit
- contributor workflow remains practical
- the hardening direction remains incremental and credible
```
