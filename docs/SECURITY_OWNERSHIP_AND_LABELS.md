# Security Ownership And Labels

This guide defines a lightweight ownership and label model for SA-NOM's repository-level security workflow.

## Why This Guide Exists

Issue templates and escalation rules are useful, but reviewers still need a simple operating model for who owns the next step and how issue state should read at a glance.

The goal is not to create heavy process. The goal is to make security workflow easier to inspect, easier to route, and easier to explain.

## Core Position

SA-NOM is designed so AI does the heavy operational preparation inside approved boundaries, while humans step in when a decision goes beyond what AI is allowed or trusted to handle.

Applied to GitHub workflow, that means:
- AI or automation may surface findings, summarize trust impact, suggest labels, and prefill issue structure
- humans still decide who owns the issue, whether a finding should escalate, whether a temporary exception is acceptable, and whether merge should block

## Ownership Model

### Follow-Up Owner

Use the `follow-up owner` field for the person expected to drive the next visible action.

This owner should:
- keep the issue revisit-able
- coordinate the next fix or review checkpoint
- make sure the issue does not disappear silently

### Escalation Owner

Use an escalation owner when a finding affects trust-critical boundaries such as:
- auth or authorization
- token or session paths
- secrets handling
- audit integrity or evidence posture
- backup, restore, recovery, or deployment trust boundaries

This owner is the human decision-maker for whether the issue can remain open as follow-up or must block merge or trigger stronger review.

### AI Assistance Boundary

AI may:
- summarize the issue
- classify likely impact
- suggest labels
- prepare a follow-up structure

AI should not be treated as:
- the final escalation authority
- the final risk acceptance authority
- the final merge-blocking authority for trust-sensitive findings

## Recommended Label Vocabulary

Keep the label vocabulary small and readable.

Recommended labels:
- `security`
- `security-exception`
- `security-follow-up`
- `escalation-required`
- `trust-boundary`
- `routine-follow-up`

## How Labels Should Be Used

### `security`

Use on all security workflow items in this lane.

### `security-exception`

Use when a finding is temporarily accepted or deferred with explicit justification.

### `security-follow-up`

Use when work remains open after merge and needs a visible revisit point.

### `escalation-required`

Use when stronger human scrutiny is needed before the issue should be treated as routine follow-up.

### `trust-boundary`

Use when the issue affects auth, token, session, audit, secrets, backup, recovery, deployment trust, or other evidence-sensitive boundaries.

### `routine-follow-up`

Use when the issue is lower impact, still visible, and does not currently require stronger escalation.

## Practical Workflow

1. AI or automation surfaces a finding or prepares a draft issue
2. a human reviewer confirms the basic classification
3. the issue receives ownership and labels
4. the human reviewer decides whether the issue is routine follow-up, temporary exception, or escalation-required
5. the follow-up owner keeps the issue visible until the closure criteria are met

## Relationship To Existing Docs

Read this guide with:
- [docs/SECURITY_EXCEPTION_WORKFLOW.md](SECURITY_EXCEPTION_WORKFLOW.md)
- [docs/SECURITY_FOLLOW_UP_VISIBILITY.md](SECURITY_FOLLOW_UP_VISIBILITY.md)
- [docs/SECURITY_ESCALATION_RULES.md](SECURITY_ESCALATION_RULES.md)
- [SECURITY.md](../SECURITY.md)
- [CONTRIBUTING.md](../CONTRIBUTING.md)

The issue templates capture structure.
The escalation guide clarifies sensitivity.
This guide clarifies ownership and workflow signals.

## Practical Summary

The right public message is:

SA-NOM lets AI do the operational work of surfacing and organizing security context, but humans still own the decisions that determine accountability, escalation, and trust-sensitive outcomes.

