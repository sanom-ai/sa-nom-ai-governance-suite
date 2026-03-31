# Roadmap - v0.1.14

This roadmap captures the next engineering step after `v0.1.13`.

## Theme

Turn SA-NOM's security exception and follow-up discipline into a more operational GitHub workflow through structured issue templates and clearer escalation rules.

## Milestone Goal

By the end of `v0.1.14`, a serious evaluator should be able to see that SA-NOM not only documents how security findings are accepted or deferred, but also provides a more structured workflow for recording, escalating, and tracking those decisions in day-to-day repository operations.

## Core Operating Note

SA-NOM is designed so AI does the work inside approved boundaries, while humans step in only when the decision goes beyond what AI is allowed or trusted to handle.

That same philosophy should carry into security workflow:
- AI or automation can surface findings, summarize context, and help prepare follow-up structure
- humans still decide whether a finding blocks merge, qualifies for temporary exception, or requires escalation

## Engineering Priorities

### 1. Structured Security Issue Templates

Add repository-level templates that make deferred security work easier to record consistently.

Target areas:
- issue templates for accepted security exceptions
- issue templates for deferred follow-up work
- required fields for owner, reason, revisit point, and affected area

Expected outcomes:
- deferred security work becomes easier to capture consistently
- follow-up ownership becomes more visible
- GitHub workflow looks more intentional and operationally usable

### 2. Escalation Rules For Sensitive Findings

Clarify which findings require stronger human scrutiny.

Target areas:
- criteria for escalation when auth, token, session, audit, backup, recovery, or deployment trust boundaries are affected
- clearer separation between lower-impact development-tool findings and trust-critical runtime findings
- plain-language reviewer guidance on when human approval should be mandatory

Expected outcomes:
- escalation becomes more consistent
- reviewers can explain why some findings require stronger action than others
- the repo's security posture reads as more mature and proportionate

### 3. Follow-Up Workflow Continuity

Strengthen the path from finding to visible follow-up.

Target areas:
- link accepted exceptions to a structured follow-up record
- align issue templates with the existing security exception and follow-up visibility guides
- keep the workflow lightweight enough for a fast-moving repository

Expected outcomes:
- accepted findings are less likely to disappear after merge
- GitHub becomes a clearer operating surface for deferred security work
- documentation and practice stay aligned

### 4. AI And Human Role Clarity In Security Workflow

Make the role split clearer inside the public docs.

Target areas:
- AI can surface findings, summarize impact, and organize context
- humans make escalation, exception, and trust-boundary decisions
- documentation should reinforce that AI is not the final authority on higher-risk security tradeoffs

Expected outcomes:
- the AI-first but human-gated model becomes clearer in security workflow
- SA-NOM's operating philosophy stays consistent across product, governance, and security docs

## Non-Goals For v0.1.14

- do not turn the repository into a heavy governance bureaucracy
- do not imply that issue templates alone solve security risk
- do not replace maintainer judgment with automation or form-filling
- do not blur the line between AI assistance and human approval for high-risk decisions

## Documentation And Contributor Priorities

- document issue-template usage in practical language
- document which findings deserve escalation instead of routine follow-up
- keep the workflow light enough for contributors to follow consistently
- reinforce that AI can assist, but humans decide beyond AI boundaries

## Commercial And Trust Priorities

- strengthen trust with technical buyers who want to see that deferred risk handling is not ad hoc
- make SA-NOM easier to discuss in diligence conversations where governance, workflow, and operational discipline all matter together
- show a believable progression from security automation, to exception handling, to structured security workflow operations

## Candidate Deliverables

- `v0.1.14` roadmap and issue drafts
- structured issue templates for security exceptions and deferred follow-up
- escalation rules guide for higher-sensitivity findings
- updated contributor and security docs that reinforce AI-assist plus human-decision boundaries

## Exit Criteria For v0.1.14

- the repo has a more structured path for recording deferred security work
- escalation expectations are clearer for higher-sensitivity findings
- issue-driven follow-up becomes easier to use in GitHub workflow
- the AI-assist and human-decision boundary is clearer in the security narrative
