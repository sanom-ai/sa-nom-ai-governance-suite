# Minimal Human Approval Surface

This document defines the first human-facing interaction surface for SA-NOM's governed human-in-the-loop operations layer.

It should be read after [Governed Human-In-The-Loop Operations](GOVERNED_HITL_OPERATIONS.md).

The purpose of this guide is not to design a large workflow suite.
The purpose is to define the smallest believable human approval surface that lets organizations see how approval, rejection, escalation, and rationale capture work in practice.

## Core Principle

The human approval surface is not a shortcut around governance.
It is the visible operator-facing expression of governance.

That means the surface should help a human:
- inspect a governed action
- understand why the action is waiting
- make the right authority decision
- leave rationale behind
- pass the item forward or upward without losing evidence

The human should decide.
The system should do the preparation work.

## Why A Minimal Surface Matters

Organizations will not seriously evaluate SA-NOM if the only answer to human approval is "the system would ask a person somehow."

A serious evaluation candidate needs a clear answer to questions like:
- where do pending approvals appear
- what context does the approver actually see
- how is escalation handled
- how is rationale captured
- how do we know who owns the next step
- how does this avoid turning into manual chaos

The minimal approval surface is the first direct answer to those questions.

## Surface Components

A minimum believable approval surface should include four connected parts.

### 1. Approval Inbox

The inbox is the operator's default entry point.

It should show:
- pending approval items
- pending review items
- escalated items
- expired or stalled items
- ownership and priority cues

The inbox should help a human understand what needs attention now.
It should not force them to reconstruct the workflow from raw logs.

### 2. Approval Detail View

Each governed item should open into a detail surface that explains:
- the requested action
- current decision state
- why human involvement was required
- the role, policy, trigger class, and risk posture involved
- the evidence or supporting context attached
- who can act now and who owns escalation if needed

This is the most important view in the surface because it prepares the decision rather than merely listing it.

### 3. Decision Controls

The minimum action set should include:
- `approve`
- `reject`
- `escalate`
- `request_review`
- `stop`

Not every operator should see every control.
The visible controls should depend on role, authority, and decision state.

### 4. Rationale And Comment Capture

A human decision should not be treated as a button click alone.

The surface should allow or require:
- decision rationale
- comment or note
- reference to supporting evidence when appropriate
- structured explanation for escalation or rejection when useful

This matters because the audit story depends on more than the final outcome label.

## State Model In The Surface

The approval surface should reflect the same governed states defined in the HITL model.

At minimum:
- `pending_review`
- `approved`
- `rejected`
- `escalated`
- `overridden`
- `stopped`
- `expired`

The operator should be able to see:
- the current state
- the prior state transitions
- what event caused the current pause
- what action is allowed next

This makes the surface more than a queue. It becomes a readable governance lane.

## Approval Triggers

The approval surface exists because some actions should not proceed automatically.

Typical trigger classes include:
- high-risk actions
- financial-impact actions
- legal or compliance-sensitive actions
- customer-facing actions with meaningful external effect
- emergency or exception-granting actions
- any PTAG path that resolves to `wait_human` or requires `human_override`

The surface should make the trigger class visible so the human understands why the item is here.

## Role-Aware Interaction Model

The human surface should support more than one kind of actor.

Minimum role expectations:
- `approver` sees items that are within their authority scope
- `reviewer` can inspect and comment before final decision
- `escalation_owner` receives items that exceed the current operator's decision scope

This is important because flat approval models break down quickly in real organizations.

## Escalation Path

Escalation should be first-class, not an afterthought.

A useful minimum path is:
- AI prepares the item
- approver reviews it
- if uncertain or out of scope, the item is escalated
- escalation owner receives the item with the full context and prior rationale attached
- the decision path remains auditable end to end

The surface should never force escalation owners to start from zero.

## Human Ask Continuity

Human Ask should complement the approval surface.

That means a human should be able to ask questions such as:
- what is waiting for my approval
- which items are currently escalated
- which decisions expired without response
- what rationale was recorded for the last rejected item
- where the largest approval bottleneck exists right now

But Human Ask should remain governed.
It should report from the same controlled approval data, not from an informal side channel.

## Audit Requirements For The Surface

Every decision taken through the approval surface should create an auditable record.

Minimum audit fields:
- decision item id
- actor identity
- actor role in the decision path
- timestamp
- selected outcome
- rationale or comment
- evidence references
- prior state and resulting state

This is necessary for trust, internal review, and later incident or compliance analysis.

## Operator Experience Rules

The minimum surface should follow a few discipline rules:
- show the smallest useful amount of information first
- reveal the reason for human pause clearly
- make next allowed actions obvious
- never hide escalation ownership
- never treat rationale as optional for high-trust actions
- preserve evidence continuity across approval states

The design should feel governed and calm, not noisy.

## Relationship To Runtime Reliability

The approval surface should connect naturally to runtime and operational visibility.

Operators should be able to see at least:
- queue depth
- age of pending items
- escalation accumulation
- expired items
- service health signals that affect approval processing

This is how the approval surface becomes part of serious operational evaluation rather than only a workflow sketch.

## What This Minimal Surface Is Not

This first surface is not trying to be:
- a full enterprise case-management platform
- a generalized ticketing product
- a complete BPM suite
- a claim that every future UI decision is already settled

It is the minimum human-facing governance surface needed to make SA-NOM's HITL model believable.

## Suggested First Implementation Shape

A realistic first implementation can stay simple:
1. one approval inbox or board
2. one approval detail view
3. one comment/rationale area
4. one escalation action path
5. one audit summary section

That is enough to make the governed control loop concrete.

## Summary

The minimal human approval surface is the operator-facing half of SA-NOM's HITL model.

It gives organizations a visible, governed place where sensitive actions can be reviewed, approved, rejected, escalated, and explained without losing authority boundaries, evidence continuity, or auditability.
