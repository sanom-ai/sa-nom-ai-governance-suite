# SA-NOM Operating Model

This document defines how SA-NOM is intended to operate at a system level.

It should be read together with:
- [System Architecture](SYSTEM_ARCHITECTURE.md)
- [Input Process Output Model](INPUT_PROCESS_OUTPUT_MODEL.md)

The purpose of this guide is to make the operating principle of SA-NOM explicit before later milestones deepen enterprise-grade implementation.

## Core Operating Principle

SA-NOM is designed so AI does the work inside approved boundaries, while humans step in only when the task or decision goes beyond what AI is allowed or trusted to handle.

This is the operating model.
It is not a side note.
It is the core design of the system.

## What SA-NOM Is Trying To Avoid

SA-NOM is not trying to create a workflow where:
- humans manually do every important step
- AI only drafts while humans perform all real operating work
- governance means slowing work down so much that AI cannot function as an operating actor
- AI is treated as an unrestricted autonomous agent with no accountable control boundary

Instead, SA-NOM is trying to create a system where:
- AI can operate meaningfully
- work can move quickly inside explicit boundaries
- humans remain accountable for trust-sensitive decisions
- evidence and reviewability remain attached to important actions

## Default Operating Mode

The default mode should be:
- AI receives structured input
- AI classifies and interprets the task
- AI works inside the approved role and policy boundary
- AI prepares drafts, routing, summaries, issue context, or governed work products
- AI keeps the workflow moving until a real control boundary is reached

This means the normal operating state is not `wait for human on every step`.
The normal operating state is `AI proceeds until a defined human decision point is reached`.

## Human Role In The Operating Model

Humans are not removed from the system.
Their role becomes more specific and more valuable.

Humans remain responsible for:
- approval
- escalation
- override
- temporary exception acceptance
- trust-sensitive release decisions
- higher-risk legal, regulatory, or accountability judgments
- structural redesign when PT-OSS signals that the workflow is not safe to trust

The human role is not to shadow every AI action.
The human role is to intervene where judgment, accountability, or authority should not be delegated fully.

## Four Operating Zones

Use this model to understand how work is split.

### 1. AI-Only Zone

This is work AI can perform without waiting for real-time human confirmation.

Examples:
- classification
- summarization
- template filling
- routing preparation
- draft generation
- issue preparation
- document organization
- reporting preparation

This is where the system should save the most human time.

### 2. AI-Prepared / Human-Confirmed Zone

This is the main boundary zone in SA-NOM.

AI prepares the work.
Humans confirm the decision.

Examples:
- security exception records
- follow-up ownership
- escalation choices
- controlled document approval
- trust-sensitive publication
- high-impact workflow release decisions

This zone is often the most important operating pattern in SA-NOM.

### 3. Human-Only Zone

This is work that should remain under direct human control.

Examples:
- final legal acceptance
- regulator-facing accountability positions
- exceptional override of trust-sensitive control boundaries
- deletion, disposal, or irreversible control actions where policy requires direct human responsibility

This zone should stay explicit.

### 4. Blocked Or Escalated Zone

This is where the workflow should not continue normally.

Examples:
- policy conflict
- structural fragility severe enough to stop progression
- missing authority
- unresolved trust-boundary risk
- security findings that require stronger human scrutiny before merge or release

This zone exists to stop the system from pretending everything is routine when it is not.

## How AI Should Behave In Practice

Inside the approved operating boundary, AI should:
- move work forward
- prepare useful outputs instead of only commentary
- classify and structure information
- maintain context across linked artifacts
- prepare decision-ready material for humans when a control boundary is reached
- avoid pretending it has authority it does not have

The system should feel like AI is doing the operational load, not simply narrating it.

## How Human Decision Points Should Work

A human decision point should happen when one or more of these conditions is true:
- the action requires approval authority
- the issue crosses a trust boundary
- escalation is needed
- the current path requires exception handling
- a structural warning means the workflow may be unsafe to trust
- the decision carries legal, regulatory, or organization-wide accountability beyond approved automation scope

At that point, AI should stop trying to finalize the decision and instead prepare the decision surface for the human reviewer.

## Human Ask In The Operating Model

Human Ask is not only a query feature.
It is one of the main ways humans enter the system without taking over the system.

Human Ask allows humans to:
- call AI into reporting and status review
- retrieve decision-ready summaries
- inspect active workflow posture
- review evidence, ownership, gaps, and readiness state

This fits the operating model because it keeps humans informed without forcing them to manually perform all upstream work.

## Relationship To PTAG And PT-OSS

The operating model depends on both.

- `PTAG` defines what a role is allowed to do
- `PT-OSS` helps determine whether the surrounding structure is safe enough to trust

That means SA-NOM does not say:
- `AI can act because the model is capable`

Instead it says:
- `AI can act when role policy allows it and the structural conditions are trustworthy enough to support it`

## Relationship To Document, Compliance, And Security Workflows

The same operating model should repeat across system modules.

### Governed Document Center

- AI drafts, classifies, routes, and reports
- humans approve, waive, release, or override when control boundaries are reached

### Compliance Workflow

- AI can answer from baseline, map posture, and prepare structured responses
- humans still decide when legal review, regulator review, or formal completion is required

### Security Workflow

- AI can surface findings, summarize trust impact, suggest labels, and prepare issue structure
- humans still decide exception acceptance, escalation, ownership, and merge-blocking outcomes

The operating model should feel consistent everywhere.

## What This Means For 0.1.xx And 0.2.xx

In `0.1.xx`, the primary task is to make the structure explicit.
That means documenting:
- architecture
- input-process-output flow
- operating model
- governance and trust boundaries

In `0.2.xx`, the next task is to deepen implementation quality so the runtime behaves more like the operating model already described.

That means the operating model should lead the implementation roadmap, not trail behind it.

## Summary

SA-NOM is designed around an AI-heavy, human-gated operating model.

AI should do most of the operational work inside approved boundaries.
Humans should intervene at the points where trust-sensitive judgment, accountability, escalation, approval, or exception handling must remain under direct control.

That is the model the rest of the system is supposed to support.
