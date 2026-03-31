# Roadmap - v0.1.13

This roadmap captures the next engineering step after `v0.1.12`.

## Theme

Strengthen SA-NOM's security-review maturity by introducing explicit exception handling and follow-up discipline around lightweight security automation findings.

## Milestone Goal

By the end of `v0.1.13`, a serious technical evaluator should be able to see that SA-NOM not only surfaces dependency-related risk in CI, but also treats accepted exceptions, deferred fixes, and follow-up ownership in a more disciplined and reviewable way.

## Engineering Priorities

### 1. Security Exception Workflow

Define how maintainers should handle findings that are not fixed immediately.

Target areas:
- accepted-risk workflow for dependency findings
- when a finding should block merge versus allow follow-up
- expectation for documented justification and ownership
- boundaries for temporary exceptions versus unacceptable risk

Expected outcomes:
- accepted exceptions stop looking ad hoc
- reviewers can explain why a flagged dependency was or was not tolerated
- the repo looks more disciplined without pretending perfect security hygiene

### 2. Follow-Up Visibility

Make deferred security work easier to track after merge.

Target areas:
- issue-driven follow-up guidance
- references from PRs to follow-up items when needed
- expectations for revisit timing or milestone ownership
- keeping exceptions visible instead of implicit

Expected outcomes:
- deferred security work remains visible
- maintainers have a clearer operational memory for accepted gaps
- lightweight automation produces more durable workflow outcomes

### 3. Security Review Escalation Rules

Clarify when a finding should receive higher scrutiny.

Target areas:
- criteria for high-sensitivity dependency findings
- auth, token, session, audit, and deployment paths as escalation triggers
- clearer difference between dev-tool findings and runtime-trust findings
- stronger reviewer language around what requires escalation

Expected outcomes:
- security review looks more proportionate and less arbitrary
- maintainers can distinguish everyday dependency churn from trust-impacting changes
- technical buyers see a more mature review posture

### 4. Security Workflow Documentation Continuity

Extend the public docs so the new exception and follow-up process is easy to inspect.

Target areas:
- add exception workflow documentation
- tighten links between security automation, dependency review, and maintainer workflow docs
- keep repo messaging honest about what is automated versus what still depends on human review

Expected outcomes:
- the security story stays coherent across docs and workflow
- the next hardening step feels cumulative instead of fragmented

## Non-Goals For v0.1.13

- do not claim that every security finding can be safely waived through process alone
- do not replace maintainer judgment with a bureaucratic checklist
- do not turn the dependency-light posture into heavy governance theater
- do not imply complete supply-chain governance based on this milestone alone

## Documentation And Contributor Priorities

- document how accepted exceptions should be justified
- document when follow-up issues are expected
- document which findings deserve escalation instead of casual acceptance
- keep the process practical for a small, fast-moving repository

## Commercial And Trust Priorities

- strengthen trust with technical buyers who want to see that risk findings do not disappear silently
- make SA-NOM easier to discuss in diligence conversations where exception handling matters as much as scanning itself
- show progress from security documentation, to automation, to disciplined response workflow

## Candidate Deliverables

- `v0.1.13` roadmap and issue drafts
- security exception workflow guide
- follow-up issue discipline guide or template
- updated contributor and security docs for accepted-risk handling
- optional CI-facing notes or labels for exception-aware review

## Exit Criteria For v0.1.13

- the repo has a documented path for accepted or deferred security findings
- follow-up ownership is easier to explain and inspect
- reviewer escalation rules are clearer for higher-sensitivity findings
- the security workflow looks more mature without becoming heavy or performative
