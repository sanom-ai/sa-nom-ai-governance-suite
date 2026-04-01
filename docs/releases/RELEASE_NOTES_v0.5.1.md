# Release Notes - v0.5.1

## Release Focus

`v0.5.1` is the operator-surface hardening release after the first governed HITL operations milestone in `v0.5.0`.

This release is focused on turning the private dashboard into a more usable operator control plane by improving onboarding, approval discipline, queue attention, focused navigation, and audit continuity without changing the broader governed HITL structure.

## Completed Scope

### Dashboard Onboarding And Private Runtime Entry

- clarified the private-token entry screen so first-time evaluators can tell the difference between viewer, operator, and reviewer lanes
- made the local development tokens easier to understand as evaluation-only paths rather than production access posture
- gave the private dashboard a clearer first-run path for people trying the governed runtime for the first time

### Unified Operator Alert Policy And Queue Health

- added one shared operator alert policy for aging, backlog, and notification routing across pending overrides, Human Ask waiting sessions, blocked workflows, recovery backlog, and dead letters
- surfaced queue-health posture directly in the dashboard so operators can see which lane is aging, how old the oldest item is, and when the queue crosses warning, critical, or stale posture
- connected the operator alert model to notification posture and delivery readiness instead of treating queue pressure and routing as separate stories

### Operator Action Plan And Focused Handoff Flow

- added a shared operator action plan that turns runtime pressure into a clear next-step order instead of leaving operators to infer what to do from multiple cards and tables
- introduced focused handoff flows so view jumps carry context, preserve operator focus, and keep the current action visible across requests, overrides, Human Ask, health, and integration views
- added sticky focus persistence and focused-subset jumps so operators land on the most relevant part of a page instead of searching manually through the full surface

### Human Approval Guardrails

- tightened the approve and veto flow in the override lane so human decisions open with structured rationale templates instead of a blank note prompt
- added lightweight validation so approvals require a `Decision basis:` line and vetoes require a `Blocking concern:` line before the dashboard will send the review note
- reinforced the idea that human intervention is part of governed execution and not a silent bypass of the control model

### Backend-Driven Focused Subsets

- moved focused subset definitions into the dashboard snapshot so the frontend reads one shared truth source for requests, overrides, and Human Ask slices
- reduced duplicated client-side filtering logic and made focused operator flows more deterministic
- expanded operator-surface tests so these focused subsets are verified as part of the runtime-facing snapshot contract

### Audit And Evidence Handoff

- added a shared audit handoff summary that connects override decisions to the audit ledger so reviewers can see how the latest human decision should be traced forward
- surfaced pending approvals, reviewed decisions, and the latest override review in both the override lane and the audit view
- made the dashboard more consistent with SA-NOM's governed model by keeping approvals, rationale, and audit trace in one connected operational story

## Why This Release Matters

`v0.5.1` makes the `v0.5.0` governed HITL model feel more like an operator-ready system and less like a document-only architecture phase.

The repository now gives evaluators and operators a clearer path to:
- enter the correct runtime lane on first use
- understand which queue needs attention first
- follow one operator action order across multiple dashboard views
- record human approval decisions with stronger rationale discipline
- move from a human approval packet to the relevant audit trace without losing context

## Verification

- `node --check sa_nom_governance\dashboard\static\dashboard_app.js`
- `python -m compileall -q .`
- `python -m pytest _support/tests`
- `274 passed`, coverage `82.19%`

## Next Phase

The next milestone after `v0.5.1` should continue turning the governed HITL model into a stronger runtime and operator-evaluation surface while keeping the dashboard, private runtime, and audit continuity aligned under one coherent control-plane story.

## Notes

- this release is intentionally a hardening and operator-surface phase rather than a large new architecture phase
- `v0.5.1` keeps the unified governed HITL structure from `v0.5.0` and improves how operators actually move through it
- the focus of this release is not feature sprawl, but clearer execution, review, and evidence continuity in the private runtime
