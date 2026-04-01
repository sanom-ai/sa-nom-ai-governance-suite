# Governed HITL Human Ask Reporting

This document defines how Human Ask should work for SA-NOM's governed human-in-the-loop operations layer.

It should be read after:
- [Governed Human-In-The-Loop Operations](GOVERNED_HITL_OPERATIONS.md)
- [Minimal Human Approval Surface](MINIMAL_HUMAN_APPROVAL_SURFACE.md)

The purpose of this guide is to show how humans should ask the system for approval status, escalation posture, intervention history, and bottleneck visibility without bypassing governance.

## Why Human Ask Matters In HITL

Once a governed approval model exists, people immediately need reporting around it.

They ask questions like:
- what is waiting for my approval
- what is blocked right now
- what has already been escalated
- who approved the last high-risk action
- where are decisions stalling
- what rationale was given for rejection or escalation

Those questions are exactly where AI should help.

But if Human Ask is not designed carefully, it can accidentally become a bypass path around authority and confidentiality boundaries.

That is why HITL Human Ask must be governed from the start.

## Core Principle

`Human Ask` in the HITL model is a governed reporting and visibility surface.

It is not:
- a hidden admin shortcut
- an unrestricted search layer
- an alternate approval path
- a way to expose sensitive decision context to anyone who asks

The correct model is:
- approvals happen through the governed approval surface
- Human Ask reports on governed approval state inside access boundaries
- the same authority and evidence spine controls what can be seen

## What Human Ask Should Be Able To Answer

Inside approved authority scope, Human Ask should answer questions such as:
- what approvals are pending for me right now
- which actions are waiting for review
- which items have been escalated and to whom
- which decisions expired without response
- what rationale was recorded for the last rejected or escalated item
- which trigger classes are currently creating the most queue pressure
- which approval lane is the current bottleneck
- what evidence is attached to the item I am being asked to review
- what state transitions have already happened for a given approval item

These are high-value visibility tasks that should not require humans to manually dig through raw records or logs.

## Typical Human Ask Use Cases

Examples include:

- `My approvals ask`
  - "Show everything currently waiting for my approval"
- `Escalation ask`
  - "Which governed actions are currently escalated to the escalation owner"
- `Delay ask`
  - "Which approvals are older than 48 hours"
- `Rationale ask`
  - "Why was the last customer-facing action rejected"
- `Queue health ask`
  - "Where is the biggest approval bottleneck right now"
- `Meeting ask`
  - "Prepare a HITL approval posture summary for the governance meeting"

This is how Human Ask turns the HITL layer into an operational reporting surface rather than only a decision queue.

## What AI Should Do In This Reporting Path

Within governed boundaries, AI should be able to:
- retrieve approval items by role, owner, state, trigger class, or age
- summarize current approval posture
- explain why an item is waiting for human action
- show who owns the next step
- group items by bottleneck, escalation path, or risk posture
- retrieve recorded rationale and evidence references when the asker is allowed to see them
- prepare meeting-ready summaries of pending, approved, rejected, escalated, and expired items

This is the reporting layer that makes a human-in-the-loop system usable in daily operations.

## What Must Stay Bounded

Human Ask for HITL must still respect governance boundaries.

That means AI should not:
- expose approval items outside the asker's authority scope
- reveal sensitive evidence or rationale to a user without the correct view rights
- let a reporting request act as an approval action
- surface unresolved items as though they were already approved
- bypass role, escalation, or confidentiality rules just because the question sounds simple

Human Ask is a governed visibility layer, not a shortcut around the approval model.

## Relationship To The Approval Surface

The approval surface and Human Ask should work together.

Use this mental model:
- the approval surface is where a human acts
- Human Ask is where a human asks for visibility, summary, and posture

That means:
- approval inbox answers "what needs action"
- approval detail view answers "what should I decide"
- Human Ask answers "what is the overall state and why"

This separation is healthy because it keeps reporting and decision-taking connected without collapsing them into one noisy interface.

## Minimum Governed Fields Behind Human Ask

For Human Ask to work well, the governed approval model should expose at least:
- approval item id
- current state
- trigger class
- assigned approver, reviewer, or escalation owner
- created time and age
- prior state transitions
- rationale or comment references
- evidence references
- policy or role context when view authority allows it

This lets Human Ask operate on structured approval posture rather than free-form guesswork.

## Meeting And Reporting Pattern

A useful operating pattern is:
- AI and workflow progression continue until a governed pause is reached
- a human uses the approval surface when they need to decide
- a human uses Human Ask when they need summary, bottleneck, or meeting visibility
- the reporting result stays role-scoped and evidence-aware
- the next human action still happens through the governed decision lane

This preserves both usability and governance discipline.

## Escalation Visibility

One of the most valuable Human Ask uses is escalation visibility.

People should be able to ask:
- what has already been escalated
- who currently owns the escalated item
- how long it has waited
- what rationale or prior review notes already exist
- whether escalation is clustering around a specific trigger class or role

This is critical because organizations often lose trust when escalation becomes invisible or hard to inspect.

## Audit And Evidence Continuity

Human Ask should never break the audit chain.

That means reporting results should be grounded in the same governed records that support the approval surface.

When appropriate, Human Ask should be able to show:
- who acted
- when they acted
- what state changed
- what rationale was recorded
- what evidence reference was attached

This makes Human Ask useful for review and retrospectives without creating a second unofficial truth source.

## Safe Public Claim

SA-NOM should support Human Ask as a governed reporting layer for human-in-the-loop operations so people can ask about pending approvals, escalations, bottlenecks, rationale, and decision posture without bypassing approval authority, confidentiality, or evidence boundaries.

## Summary

Governed HITL Human Ask reporting gives SA-NOM the visibility half of the human-in-the-loop model.

It lets people ask the system what is waiting, what is blocked, what escalated, why a decision happened, and where the queue is under pressure, while keeping those answers inside the same governance boundaries that control the decisions themselves.
