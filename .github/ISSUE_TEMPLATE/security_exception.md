---
name: Security exception
about: Record an accepted or deferred security finding that needs explicit ownership and follow-up
title: "[Security Exception] "
labels: security, security-exception
---

## AI-Prepared Context

Use this section for summary material that AI or automation may help prepare.

- Finding summary:
- Signal type: `pip-audit` / code review / dependency change / manual review / other
- Related PR:
- Related commit or release:
- Related package, file, or workflow area:
- Trust-boundary signals observed:

## Deferral Context

- Why this is not fixed immediately:
- Current mitigation or reason the risk is considered temporarily tolerable:

## Human-Confirmed Decision Fields

Use this section for decisions that a human maintainer must confirm directly.

- Decision type: accept temporarily / escalate / block merge / other
- Human decision owner:
- Escalation owner if stronger review is required:
- Trust-critical area affected: yes / no
- Affects auth, token, session, audit, backup, recovery, deployment, or secrets path: yes / no
- Escalation required: yes / no
- Why this decision is acceptable:

## Follow-Up Ownership

- Follow-up owner:
- Linked follow-up issue or milestone:
- Revisit by release, milestone, or date:

## AI Assistance Boundary

- AI or automation helped summarize or prefill this issue: yes / no
- Human maintainer confirmed the final decision fields: yes / no

## Notes

Use this template only for accepted or deferred security findings that remain visible for later review.
Do not use it to report a new suspected vulnerability publicly. For private disclosure, follow `SECURITY.md`.
