# Release Notes - v0.1.14

## Release Focus

`v0.1.14` turns SA-NOM's recent security workflow work into a more operational GitHub surface by adding structured issue templates and a plain-language escalation baseline.

The goal of this milestone is not to add a new runtime security engine. The goal is to make accepted exceptions, deferred security follow-up, and escalation decisions easier to record, review, and justify in day-to-day repository work.

## What Changed

### Structured Security Workflow Artifacts

- added `.github/ISSUE_TEMPLATE/security_exception.md`
- added `.github/ISSUE_TEMPLATE/security_follow_up.md`
- added `docs/SECURITY_ESCALATION_RULES.md`

### Planning And Governance Continuity

- added `docs/ROADMAP_v0.1.14.md`
- added `docs/ISSUE_DRAFTS_v0.1.14.md`

### Security Workflow Alignment

- updated `SECURITY.md`
- updated `CONTRIBUTING.md`
- updated `docs/SECURITY_FOLLOW_UP_VISIBILITY.md`
- updated `docs/README.md`

## Why This Release Matters

After `v0.1.13` clarified security exception handling and follow-up visibility, the next maturity step was to make that workflow easier to use in GitHub itself.

`v0.1.14` gives SA-NOM a clearer public workflow for:
- recording temporary security exceptions
- keeping deferred security work visible after merge
- distinguishing routine follow-up from findings that require stronger human review
- reinforcing that AI may help organize context, but humans decide exception, escalation, and merge-blocking outcomes

## Community Baseline In This Release

The public baseline now includes:
- a structured issue template for accepted or deferred security exceptions
- a structured issue template for deferred security follow-up
- a plain-language escalation guide for trust-sensitive findings
- clearer contributor and security wording around the AI-assist and human-decision boundary

## Operating Boundary

This milestone keeps SA-NOM's core operating model explicit:
- AI or automation may surface findings, summarize context, and help prepare follow-up structure
- humans still decide whether a finding blocks merge, qualifies for temporary exception, or requires escalation

## Upgrade Notes

- `v0.1.14` is a workflow-discipline milestone, not a runtime feature milestone
- the release improves repository-level security workflow structure without claiming full security process automation
- the templates and escalation guide are designed to stay lightweight, review-oriented, and proportionate to repository scale

## Verification Snapshot

Validated during `v0.1.14` work with:
- `python -m compileall -q .`
- local review of roadmap, issue-template, escalation, and security workflow wording
- local verification that the new release notes are linked from `docs/README.md`

## Suggested Next Step

After `v0.1.14`, the next useful step would be to decide whether to formalize issue labels, issue forms, or escalation ownership patterns more deeply in a future milestone.
