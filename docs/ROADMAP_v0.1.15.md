# Roadmap - v0.1.15

This roadmap captures the next engineering step after `v0.1.14`.

## Theme

Turn SA-NOM's structured security workflow into a more operational GitHub system through ownership rules, labels, and issue-form discipline that keeps AI in the heavy operational role while humans remain the final decision-makers on higher-risk security questions.

## Milestone Goal

By the end of `v0.1.15`, a serious evaluator should be able to see that SA-NOM not only records security exceptions and deferred follow-up, but also gives GitHub workflow a clearer operational structure for who owns the next action, how findings are labeled, and where human approval is required.

## Core Operating Note

SA-NOM is designed so AI does the work inside approved boundaries, while humans step in only when the decision goes beyond what AI is allowed or trusted to handle.

That same model should become clearer in the repository workflow:
- AI or automation can surface findings, suggest labels, prefill issue context, summarize trust impact, and prepare follow-up structure
- humans still decide escalation, temporary exception acceptance, ownership of trust-critical work, and whether merge should block

## Engineering Priorities

### 1. Security Ownership Rules

Clarify how ownership should work for accepted exceptions, deferred follow-up, and escalated findings.

Target areas:
- define follow-up owner expectations
- define escalation owner expectations
- define how ownership should be visible in issue workflow

Expected outcomes:
- deferred security work becomes easier to assign responsibly
- trust-critical findings have clearer human accountability
- GitHub workflow reads as more operational and less ad hoc

### 2. Labels And Structured Workflow Signals

Define a small but meaningful label vocabulary for repository security workflow.

Target areas:
- labels for security exception, security follow-up, escalation required, trust boundary, and routine follow-up
- clearer distinction between lower-impact workflow items and trust-sensitive findings
- labels that help reviewers and maintainers understand status quickly

Expected outcomes:
- security issues become easier to triage visually
- follow-up state becomes more inspectable
- issue templates and docs feel more connected to actual GitHub operations

### 3. Issue Forms Or Template Refinement

Decide whether the next iteration should remain markdown templates or move toward structured issue forms.

Target areas:
- fields that AI can prefill or summarize reliably
- fields that must remain human-confirmed
- ownership, revisit point, escalation check, and closure criteria

Expected outcomes:
- issue creation becomes more consistent
- AI-assist plus human-decision boundaries become clearer in form design
- reviewers have less ambiguity about what must be filled in before merge decisions

### 4. AI-Assist And Human-Decision Clarity In Workflow Ownership

Make the role split even more explicit.

Target areas:
- AI as classification, summary, and issue-preparation layer
- humans as exception, escalation, and merge-blocking authority
- wording that avoids implying autonomous AI risk acceptance

Expected outcomes:
- the AI-first but human-gated model reads clearly in GitHub workflow operations
- SA-NOM's operating philosophy stays consistent across governance, security, and contributor docs

## Non-Goals For v0.1.15

- do not turn the repository into a heavy approval bureaucracy
- do not imply that labels or issue forms replace real review judgment
- do not treat AI as the autonomous authority on trust-sensitive security tradeoffs
- do not add process weight that is disproportionate to repository scale

## Documentation And Contributor Priorities

- define ownership and escalation expectations in plain language
- keep labels and forms lightweight enough to be used consistently
- make issue templates easier for AI to prefill without blurring human authority
- reinforce that humans decide beyond AI boundaries

## Commercial And Trust Priorities

- strengthen trust with technical evaluators who want to see accountable security workflow, not only issue templates
- make SA-NOM easier to position in diligence conversations where governance, security, and workflow maturity must line up
- show a believable progression from automation, to exception handling, to structured issue workflow, to accountable ownership

## Candidate Deliverables

- `v0.1.15` roadmap and issue drafts
- security ownership and label workflow guide
- refined issue-template or issue-form direction
- updated contributor and security docs that reinforce AI-heavy operations with human decision authority

## Exit Criteria For v0.1.15

- the repo has a clearer ownership model for security follow-up and escalation
- labels or equivalent workflow signals make issue state easier to read
- issue structure better separates AI-preparable context from human decision fields
- the AI-assist and human-decision boundary is clearer in day-to-day GitHub workflow
