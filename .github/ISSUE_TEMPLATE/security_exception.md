---
name: Security exception
about: Record an accepted or deferred security finding that needs explicit ownership and follow-up
title: "[Security Exception] "
labels: security, security-exception
---

## Summary

Describe the finding or risk in one short paragraph.

## Source Signal

- Signal type: `pip-audit` / code review / dependency change / manual review / other
- Related PR:
- Related commit or release:
- Related package, file, or workflow area:

## Why This Is Not Fixed Immediately

Explain why the issue is not being fixed in the current change.

## Current Risk Position

- Trust-critical area affected: yes / no
- Affects auth, token, session, audit, backup, recovery, deployment, or secrets path: yes / no
- Why the current risk is considered temporarily tolerable:

## Required Human Decision

- Decision type: accept temporarily / escalate / block merge / other
- Human owner making the decision:
- AI or automation assistance used for summarization or context prep: yes / no

## Follow-Up Owner And Revisit Point

- Follow-up owner:
- Linked follow-up issue or milestone:
- Revisit by release, milestone, or date:

## Escalation Check

Explain whether this finding should be escalated for stronger human review and why.

## Notes

Use this template only for accepted or deferred security findings that remain visible for later review.
Do not use it to report a new suspected vulnerability publicly. For private disclosure, follow `SECURITY.md`.

