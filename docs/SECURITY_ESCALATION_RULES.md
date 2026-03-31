# Security Escalation Rules

This guide defines when a security-related finding in SA-NOM should stay as routine follow-up and when it should be escalated for stronger human review.

## Why This Guide Exists

Issue templates and follow-up visibility help keep deferred work visible, but they are not enough on their own.

Reviewers still need a plain-language rule set for deciding when a finding should:
- block merge
- require stronger human review
- stay visible as follow-up instead of being treated as routine noise

The goal is not to create heavy process. The goal is to make higher-sensitivity decisions more consistent.

## Core Position

SA-NOM is designed so AI can do the work inside approved boundaries, while humans step in when the decision goes beyond what AI is allowed or trusted to handle.

That same model applies here:
- AI or automation may surface findings, summarize affected files, or prepare issue context
- humans decide whether a finding is trust-critical, whether merge should block, and whether a temporary exception or follow-up path is acceptable

## Escalate By Default When These Areas Are Affected

A finding should lean toward escalation when it affects:
- authentication or authorization paths
- tokens, sessions, credential issuance, or credential rotation
- audit integrity, evidence chains, retention posture, or records trust
- backup, restore, recovery, or operator-trust boundaries
- deployment trust, release trust, or signing-related behavior
- secrets handling or sensitive runtime configuration
- code paths that could silently weaken governance claims or human-override integrity

These areas matter more because they directly shape trust, control, or evidence posture.

## Lower-Impact Findings That May Stay Routine

A finding may remain routine follow-up when it is:
- confined to a low-impact development dependency
- limited to non-sensitive docs or examples
- unlikely to affect runtime trust boundaries
- already understood with a practical revisit point and visible owner

Even then, routine does not mean invisible. The issue should still be documented when it is intentionally deferred.

## Escalation Questions Reviewers Should Ask

Before accepting routine follow-up, reviewers should ask:
- does this finding touch a trust-critical runtime path?
- would a technical evaluator question our judgment if this were merged quietly?
- does the issue weaken auth, token, session, audit, backup, recovery, or deployment trust posture?
- if AI summarized this finding, has a human actually decided what the consequence should be?
- if the fix is deferred, is the owner and revisit point explicit enough to be meaningful?

If the answer is unclear, escalation is usually safer than casual acceptance.

## Practical Escalation Outcomes

A finding may lead to one of these outcomes:
- `block merge` when the trust impact is too high or the risk cannot be explained away credibly
- `escalate for stronger human review` when more scrutiny is needed before merge is acceptable
- `temporary exception with explicit issue` when the risk is understood, bounded, and owned
- `routine follow-up` when the impact is lower and visibility remains sufficient

The important thing is that the outcome is chosen consciously, not by inertia.

## Relationship To Existing Security Workflow

Use this guide together with:
- [docs/SECURITY_EXCEPTION_WORKFLOW.md](SECURITY_EXCEPTION_WORKFLOW.md)
- [docs/SECURITY_FOLLOW_UP_VISIBILITY.md](SECURITY_FOLLOW_UP_VISIBILITY.md)
- [docs/DEPENDENCY_REVIEW_WORKFLOW.md](DEPENDENCY_REVIEW_WORKFLOW.md)
- [SECURITY.md](../SECURITY.md)
- [CONTRIBUTING.md](../CONTRIBUTING.md)

The issue templates capture structure.
This guide explains when stronger human scrutiny should apply.

## Practical Summary

The right public message is:

SA-NOM allows AI and automation to surface and organize security context, but humans make the final decision when findings affect trust-critical boundaries.
