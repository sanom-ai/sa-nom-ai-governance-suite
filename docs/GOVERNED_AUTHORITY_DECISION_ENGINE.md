# Governed Authority And Decision Engine

This document defines the authority and decision engine baseline for SA-NOM in `v0.2.0`.

It should be read together with:
- [Governed Runtime Orchestration](GOVERNED_RUNTIME_ORCHESTRATION.md)
- [SA-NOM Operating Model](SA_NOM_OPERATING_MODEL.md)
- [PTAG Framework](PTAG_FRAMEWORK.md)

The purpose of this guide is to make trust-sensitive decision boundaries explicit in runtime behavior.

## Core Decision Principle

SA-NOM should default to AI-driven progression inside approved boundaries.

When a trust-sensitive boundary is reached, the decision engine should:
- stop silent progression
- classify the boundary type
- prepare a decision surface
- require explicit human confirmation where authority cannot be delegated

This is how SA-NOM keeps speed and control at the same time.

## What The Decision Engine Does

The authority and decision engine determines whether a workflow step may:
- continue under AI
- pause for human confirmation
- escalate for stronger review
- move into exception handling
- remain blocked until prerequisites are satisfied

It also records why each decision posture was selected.

## Decision Postures

Use these postures as the baseline decision states.

- `ai_allowed`
- `human_confirmation_required`
- `escalation_required`
- `exception_required`
- `blocked`

These should represent governance posture, not only technical state.

## Authority Levels

The engine should evaluate decision requests against authority levels.

### 1. Operational Authority

Used for routine execution inside approved role scope.

Typical outcome:
- AI continues automatically

### 2. Confirming Authority

Used when policy allows AI preparation but requires a human to confirm.

Typical outcome:
- pause and request human confirmation

### 3. Escalation Authority

Used when sensitivity exceeds normal confirming paths.

Typical outcome:
- route to escalation reviewer or reviewer group

### 4. Exception Authority

Used when the workflow cannot proceed under normal policy but may proceed under temporary exception.

Typical outcome:
- require explicit exception owner, rationale, and revisit point

### 5. Override Authority

Used only for trust-critical decisions that intentionally bypass normal flow under accountable human control.

Typical outcome:
- require strong human decision trace and explicit reason

## Decision Inputs

The engine should evaluate at least these input classes:
- role scope and PTAG boundary
- workflow context and current state
- trust sensitivity level
- required approval path
- structural trust posture from PT-OSS where relevant
- evidence sufficiency for safe continuation
- exception and prior decision history

A decision should not be based only on model confidence or convenience.

## Approval Gates

Approval gates are explicit points where AI must not finalize progression on its own.

Typical gate types:
- release gate
- external-facing gate
- policy-signoff gate
- compliance-signoff gate
- records-disposal gate
- security exception gate

Baseline approval gate behavior:
- capture gate type
- capture decision owner
- capture required evidence
- capture final human outcome
- resume or block runtime accordingly

## Escalation Rules

Escalation should be triggered when normal confirmation is insufficient.

Common triggers:
- high trust sensitivity
- unresolved policy conflict
- repeated exception behavior
- missing or inconsistent evidence
- boundary crossing outside approved role scope

Escalation outcomes:
- `escalated_for_review`
- `escalated_and_blocked`
- `escalated_and_confirmed`

Escalation should remain explicit and attributable.

## Exception Path

Exception handling should be treated as governed deviation, not silent workaround.

Required baseline fields:
- exception reason
- exception owner
- scope and duration
- revisit date or event
- decision rationale
- closure condition

Exception should never erase the original boundary condition that caused the pause.

## Override Path

Override is a narrow path for high-trust human intervention.

Baseline requirements:
- explicit human authority identity
- explicit reason
- explicit impact note
- explicit trace linkage to affected workflow item
- explicit record of whether the path is temporary or final

Override should be auditable by default.

## Blocked State Rules

Blocked states are safety controls, not failure noise.

A workflow should remain blocked when:
- required authority is absent
- required evidence is absent
- unresolved conflict remains
- escalation has not been resolved
- decision prerequisites are incomplete

The engine should report blocked reason clearly so resolution is actionable.

## Human-Confirmed Decision Surface

When human decision is required, the engine should expose a concise decision surface.

Minimum decision surface elements:
- current posture
- why automation paused
- what decision is requested
- who is expected to decide
- evidence summary
- risk summary
- available outcomes (`approve`, `escalate`, `exception`, `reject`, `override` when allowed)

This keeps human work focused on judgment, not reconstruction.

## Runtime Integration Model

The decision engine should integrate with runtime orchestration using a simple checkpoint model.

At each checkpoint:
- runtime submits context
- decision engine returns posture
- runtime takes one of three actions:
  - continue AI
  - pause for human
  - block or escalate

This keeps orchestration and decision logic coupled but separable.

## Evidence Expectations

For each trust-sensitive decision, the engine should produce decision evidence.

Minimum evidence expectations:
- decision timestamp
- decision posture
- deciding authority
- rationale
- outcome
- linkage to workflow item and state transition

This is essential for audit and release confidence.

## Non-Goals For This Baseline

- do not claim every module already enforces all decision postures in code
- do not turn normal workflow into heavyweight bureaucracy
- do not allow AI to self-approve trust-sensitive outcomes
- do not treat exception or override as default operating paths

## Summary

The SA-NOM authority and decision engine baseline ensures that AI can keep work moving quickly inside approved scope while trust-sensitive outcomes remain explicitly human-authorized, attributable, and auditable.

This is the boundary system that keeps AI-heavy operations governable.
