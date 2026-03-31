# Governed Runtime Orchestration

This document defines the baseline runtime orchestration model for SA-NOM as `v0.2.0` begins.

It should be read together with:
- [System Architecture](SYSTEM_ARCHITECTURE.md)
- [Input Process Output Model](INPUT_PROCESS_OUTPUT_MODEL.md)
- [SA-NOM Operating Model](SA_NOM_OPERATING_MODEL.md)

The purpose of this guide is to explain how SA-NOM should behave once work is actually moving through the system, not only being described at the architecture level.

## Core Runtime Principle

SA-NOM runtime orchestration should reflect the same operating rule used across the system:
- AI is the default operating actor
- runtime flow should continue automatically inside approved boundaries
- humans should be brought in only when a trust-sensitive transition, approval need, escalation condition, or blocked state is reached

The runtime should feel like governed progress, not repeated manual prompting.

## What Runtime Orchestration Means In SA-NOM

Runtime orchestration is the layer that turns governed intent into governed progression.

It is responsible for:
- moving work from one state to the next
- routing work to the right role or workflow path
- preserving the current decision posture
- deciding whether the next step is AI-only, AI-prepared and human-confirmed, human-only, or blocked
- creating enough evidence so the workflow can be reviewed later

This layer is not supposed to replace policy, role design, or human authority.
It is supposed to make those boundaries actionable during real execution.

## Runtime Objects

At the orchestration level, SA-NOM should be understood as moving a set of governed runtime objects.

Typical objects include:
- task
- request
- issue
- governed document action
- compliance action
- security follow-up
- approval item
- exception item
- evidence object
- workflow result

A real runtime path may involve several of these objects, but orchestration should make the progression readable as one governed flow.

## Baseline Runtime Stages

Use this stage model as the default execution path.

### 1. Intake

Work enters the system in a structured or semi-structured form.

Examples:
- Human Ask
- document request
- issue or finding
- policy-driven trigger
- scheduled workflow step
- provider or integration event

Expected orchestration behavior:
- register the incoming work item
- assign an initial type or class
- record the source and time of intake
- prepare the item for routing

### 2. Classification And Boundary Check

The system interprets what the work is and what policy boundary applies.

Expected orchestration behavior:
- classify the work item
- identify the role or workflow type involved
- determine whether the item stays in AI-operable scope
- determine whether the item already starts in a human-required or blocked posture

At this stage, the system is not deciding the final business outcome.
It is deciding whether the workflow may proceed and under what boundary.

### 3. Routing

The system decides where the work should go next.

Expected orchestration behavior:
- route the item to the correct role or module
- attach the current posture, owner, or decision state
- preserve upstream evidence and classification context
- avoid sending the same item into conflicting paths without an explicit reason

Routing should feel governed, not improvised.

### 4. AI Execution

The normal operating state begins here.

Expected orchestration behavior:
- let AI perform drafting, summarization, comparison, structuring, preparation, reporting, or analysis work inside policy scope
- keep intermediate state visible enough to be reviewed later
- continue progressing automatically when no trust-sensitive decision point has been reached

This is where SA-NOM should reduce human workload the most.

### 5. Decision Surface Preparation

When a control boundary is reached, runtime should stop trying to silently continue and instead prepare a human-usable decision surface.

Expected orchestration behavior:
- summarize the current context
- show the relevant state, owner, and reason for pause or escalation
- attach evidence and prior actions
- present the next decision clearly enough that a human does not have to reconstruct the workflow manually

This stage is central to the SA-NOM model.
The runtime should do the preparation work so the human only needs to decide.

### 6. Human Decision Or Confirmation

A human steps in only when the current boundary requires it.

Typical examples:
- approval
- escalation confirmation
- exception acceptance
- override
- release decision
- high-impact trust judgment

Expected orchestration behavior:
- pause normal AI progression until a valid decision is recorded
- preserve the exact reason human confirmation was required
- record the resulting decision state clearly

### 7. Resolution, Output, And Evidence Closure

The workflow ends with a governed result rather than an ambiguous stop.

Expected orchestration behavior:
- record the final workflow outcome
- emit the relevant output artifact, state, or report
- retain the supporting evidence chain
- preserve exception, approval, or release trace when relevant

## Baseline Runtime States

The runtime does not need every future state in `v0.2.0`, but it should already move toward a readable baseline.

Recommended baseline states:
- `received`
- `classified`
- `routed`
- `in_progress_ai`
- `awaiting_human_confirmation`
- `approved`
- `escalated`
- `blocked`
- `completed`
- `closed_with_exception`

These states should be read as governed posture markers, not only technical flags.

## AI-Prepared To Human-Confirmed Transition

This is the most important transition in the SA-NOM runtime.

The handoff should work like this:
- AI moves the work item as far as policy allows
- AI prepares the decision context, not just raw output
- the system records why human confirmation is required
- the human confirms, rejects, escalates, overrides, or sends back the item
- the runtime continues based on the recorded decision

The purpose is not to make humans do the preparatory work.
The purpose is to make humans decide only at the point where decision authority matters.

## Role Execution Lifecycle

Each governed role should be treated as having a simple runtime lifecycle.

### Role Lifecycle Stages

- `assigned`
- `active`
- `paused_for_human`
- `resumed`
- `completed`
- `stopped`

Expected behavior:
- a role becomes `assigned` when routing places work in that role path
- a role becomes `active` when AI is allowed to execute inside that role boundary
- a role becomes `paused_for_human` when approval, escalation, or exception handling is required
- a role becomes `resumed` if the workflow returns to AI-operable state after a human decision
- a role becomes `completed` when the work result is governed and closed
- a role becomes `stopped` if the path is blocked, withdrawn, or superseded

This lifecycle should remain simple enough to implement incrementally.

## Routing Rules

The orchestration layer should follow a small set of readable routing rules.

### Route To AI Execution When

- the task is inside role scope
- no trust-sensitive gate has been reached
- the current path is structurally safe enough to continue
- the workflow still has a legitimate next AI step

### Route To Human Confirmation When

- approval authority is required
- exception acceptance is required
- escalation is required
- a release or publication boundary is reached
- an override decision is required
- a trust-sensitive judgment exceeds approved AI scope

### Route To Blocked Or Escalated When

- policy conflict exists
- authority is missing
- evidence is insufficient for safe continuation
- structural trust posture is too weak
- the current path would overstep approved automation boundaries

## Evidence Expectations During Orchestration

Runtime orchestration should create evidence as work moves.

Minimum expectations:
- record intake source
- record state transitions
- record routing decisions
- record human-required boundaries
- record approvals, exceptions, and overrides
- preserve final workflow outcome

The evidence layer does not need to be fully mature in the first implementation slice, but orchestration should be designed so evidence is not an afterthought.

## Relationship To PTAG And PT-OSS

Runtime orchestration depends on both.

- `PTAG` helps determine what a role is allowed to do
- `PT-OSS` helps determine whether the structural context is trustworthy enough to continue normal flow

That means runtime progression should never be based only on model capability or convenience.
It should be based on governed scope plus structural trust posture.

## Demo And Ease-Of-Use Implications

This runtime model also affects local demo design.

A useful demo should show:
- work entering the system
- AI progressing the work automatically
- a visible trust-sensitive pause
- a human confirmation step
- resumed governed completion
- evidence retained at the end

That is the clearest way to show that SA-NOM is not only a static policy library.

## Non-Goals For This Baseline

- do not claim that every runtime state is already implemented everywhere
- do not pretend that full enterprise orchestration is complete in one document
- do not let orchestration language blur the boundary between AI assistance and human authority
- do not optimize for complexity before the baseline flow is coherent and testable

## Summary

The purpose of SA-NOM runtime orchestration is to make governed AI work progress automatically inside approved boundaries while making trust-sensitive transitions explicit, reviewable, and human-confirmed.

If the runtime behaves correctly, AI should carry most of the operational load and humans should mainly see well-prepared decision surfaces at the points where real authority is required.
