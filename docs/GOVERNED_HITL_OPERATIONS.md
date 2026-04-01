# Governed Human-In-The-Loop Operations

This document defines the core governed human-in-the-loop operations layer for SA-NOM.

It is the first implementation anchor for `v0.5.0` and should be read as the bridge between PTAG's public governance surface and a more serious operational model that organizations can evaluate for real pilot use.

## Why This Layer Exists

SA-NOM already has:
- PTAG for role and policy definition
- governed runtime concepts
- Human Ask reporting concepts
- audit and evidence foundations
- private deployment and operational-readiness framing

What has been missing is one explicit operational layer that connects these pieces into a real control loop for sensitive work.

That gap matters because organizations do not only ask whether policy exists.
They ask whether the system can show:
- what actions can proceed automatically
- what actions must wait for a person
- who has authority to approve
- how escalation works
- how rationale is captured
- how interventions are audited
- how operators inspect bottlenecks or failures without bypassing governance

The governed HITL layer exists to answer those questions directly.

## Core Position

This layer should not be read as a generic approval widget.
It is a governed operational structure.

Its purpose is to make human authority explicit where trust, risk, or organizational accountability still require it, while letting AI continue to do meaningful preparation, routing, summarization, and governed execution work around those boundaries.

In short:
- AI can work
- humans keep authority where the stakes require it
- the system records why the decision path happened the way it did

## Operating Model

The governed HITL layer sits between policy definition and high-trust execution.

Use this mental model:
- `PTAG` defines the role, authority, and policy shape
- `HITL orchestration` determines when a step must stop for human control
- `human operators` approve, reject, comment, or escalate within explicit authority boundaries
- `audit and evidence` record the intervention and its rationale
- `runtime and observability` show where the system is blocked, risky, or unhealthy

This means HITL is not a bypass around governance.
It is one of the main expressions of governance.

## Trigger Classes

The first responsibility of this layer is to classify when work must pause for human involvement.

High-priority trigger classes should include:
- high-risk actions
- actions with material financial impact
- legal or compliance-sensitive actions
- customer-facing actions with meaningful external effect
- emergency stop, override, or exception-granting actions
- actions where PTAG explicitly requires `human_override` or resolves to `wait_human`

These classes should be visible and inspectable, not hidden in application behavior.

## Decision States

The governed HITL layer should normalize a small set of operational states.

At minimum:
- `pending_review`
- `approved`
- `rejected`
- `escalated`
- `overridden`
- `stopped`
- `expired`

These states are not only UI labels.
They are part of the governance contract because they explain how a sensitive action moved through the system.

## Human Roles In The Loop

The model should support a multi-level human path rather than a single generic approver.

Core human roles:
- `approver`: the human with authority to approve or reject the action
- `reviewer`: a human who assesses or comments before a final decision
- `escalation_owner`: the authority owner when the original path is blocked, disputed, or beyond delegated approval scope

This role separation matters because many organizations do not want one flat approval layer for every sensitive action.

## Minimal Human Interaction Surface

The first usable interface for this layer does not need to be large.
It does need to be clear.

A minimum believable HITL surface should allow a human to:
- see pending governed actions
- inspect the requested action, risk posture, and supporting evidence
- approve, reject, or escalate
- add rationale or comments
- see who owns the next step

This can appear as an approval inbox, approval board, or operator review lane, but the important part is the governed interaction model rather than the screen shape itself.

## Human Ask Reporting In The HITL Model

Human Ask should become a governed visibility surface for HITL operations.

That means a human should be able to ask questions like:
- what approvals are pending right now
- which actions are blocked waiting for review
- where escalation is accumulating
- who approved or rejected a given action
- what rationale was recorded for a sensitive intervention

But this must happen without bypassing governance boundaries.

Human Ask should report through governed access and evidence rules, not become an informal shortcut around them.

## Audit And Evidence Requirements

Every human intervention should create an auditable record.

At minimum, the record should capture:
- who acted
- when they acted
- what action or decision packet they acted on
- what outcome they selected
- what rationale or comment they recorded
- what evidence bundle or supporting context was attached

This is one of the most important reasons the HITL layer exists.
A serious organizational candidate must be able to explain not only that a person approved something, but why and under what evidence context that happened.

## Runtime And Reliability Continuity

The governed HITL layer must connect to operational reliability, not sit beside it as a separate story.

Operational visibility should include:
- approval queue depth
- escalation frequency
- stalled or expired decisions
- policy-violation signals
- bottlenecks by role or approval class
- service health signals that affect governed decision flow

This matters because organizations will not treat HITL as credible if approvals disappear into a black box or if runtime instability makes governance visibility unreliable.

## Integration And Compliance Continuity

This layer should also define a small but clear continuity path for integration and compliance.

That means:
- integrations should support the governed operations story rather than explode into a broad connector catalog
- document, provider, or API integrations should preserve approval and audit visibility
- Thai and broader compliance-oriented readers should be able to map HITL behavior to real accountability expectations

The goal is not to solve every compliance framework in one document.
The goal is to make the HITL layer legible enough that compliance and localization work can attach to it naturally.

## Design Boundaries

This layer should stay disciplined.

It is not trying to be:
- a full BPM suite
- a generic enterprise workflow platform
- a replacement for all policy engines or orchestration layers
- a claim that the system is already complete for every production environment

It is a governed operations layer that makes SA-NOM substantially more credible for serious evaluation.

## What Success Looks Like

This layer is successful when a serious organizational reader can understand that SA-NOM now has:
- explicit human approval triggers
- visible approval and escalation paths
- rationale and evidence capture for human decisions
- governed status visibility through Human Ask
- runtime and audit continuity around sensitive actions

That is the step from a quality prototype toward a serious organizational candidate.

## Next Steps

The implementation slices that should follow this document are:
1. a minimal human approval surface
2. Human Ask reporting for governed HITL status
3. HITL-oriented role packs and realistic use cases
4. reliability and observability support for governed approvals and escalations

## Summary

The governed HITL operations layer is the operational bridge between PTAG policy structure and real organizational trust.

It gives SA-NOM a coherent model for when AI can proceed, when humans must decide, how those decisions are recorded, and how the whole control loop remains visible enough for serious evaluation.
