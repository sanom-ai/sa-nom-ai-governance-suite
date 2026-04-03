# Input Process Output Model

This document defines the end-to-end input, process, and output model of SA-NOM.

It should be read together with [System Architecture](SYSTEM_ARCHITECTURE.md).

The purpose of this guide is to explain what enters the system, what happens inside the system, and what leaves the system as a governed result.

## Why This Document Exists

The architecture blueprint explains the major layers of SA-NOM.

What was still needed was a simpler operational model that answers:
- what goes in
- what gets transformed
- what decisions are made
- what artifacts or actions come out

That is the purpose of this document.

## Core Position

SA-NOM is not designed as a loose request-response chatbot.
It is designed as a governed operating system for AI work.

That means:
- inputs should enter in structured form whenever practical
- processing should happen through policy, structure, and authority boundaries
- outputs should leave evidence, status, or controlled artifacts behind

## 1. Input Model

SA-NOM accepts multiple classes of input.

### Governance Inputs

These define the operating shape of the system.

Examples:
- role packs
- PTAG role and policy definitions
- authority rules
- constraint sets
- organization-specific position inputs
- role-private-studio organization-defined hats

These inputs shape what the system is allowed to do before action begins.

### Structural Inputs

These help the system judge whether the surrounding operating environment is strong enough to trust.

Examples:
- workflow structure
- approval path structure
- override path structure
- concentration-of-control signals
- dependency and fragility signals

These inputs help SA-NOM evaluate whether a governed role is structurally safe enough to progress.

### Work Inputs

These are the operational tasks the system is asked to handle.

Examples:
- runtime requests
- document drafting requests
- reporting requests
- exception coordination
- compliance-oriented requests
- Human Ask prompts
- issue workflow items

These are the inputs that trigger system work.

### Reference Inputs

These provide context the system should use while working.

Examples:
- controlled documents
- templates
- standards and procedures
- policy references
- compliance baseline documents
- release and workflow artifacts
- issue history and linked follow-up

These inputs help the system work from approved or known context instead of improvising from nothing.

### Environment And Signal Inputs

These describe runtime or operational state.

Examples:
- provider readiness
- deployment state
- health and readiness signals
- security findings
- audit or evidence signals
- backup or recovery state

These inputs influence whether a process should proceed, pause, escalate, or fail safely.

## 2. Process Model

SA-NOM does not move directly from input to output.
It processes work through governed transformation steps.

### Stage A: Intake And Classification

The system first identifies what kind of input it has received.

Typical actions:
- classify the request or artifact type
- identify the relevant role, workflow, or document context
- link the input to the right operating lane
- determine whether the input is routine, sensitive, or structurally significant

At this stage, AI can do substantial preparation work.

### Stage B: Policy And Boundary Interpretation

The system then determines what the role is allowed to do.

Typical actions:
- interpret PTAG or equivalent policy structure
- identify allowed actions
- identify denied actions
- identify conditional actions that require stronger review
- determine whether the request remains inside or outside approved authority

This stage is where role logic becomes operational.

### Stage C: Structural Trust Evaluation

The system then determines whether the surrounding structure is safe enough to trust.

Typical actions:
- apply PT-OSS or equivalent structural analysis
- detect fragility, dependency, override weakness, or asymmetry
- identify blockers, warnings, or trust-degrading conditions
- decide whether the workflow should remain active, guarded, or stopped for redesign

This stage prevents policy-only permission from being treated as sufficient trust.

### Stage D: Governed Execution

If the work remains inside policy and structural boundaries, the system proceeds with the task.

Typical actions:
- draft or prepare outputs
- route work forward
- update workflow state
- prepare reports, document changes, or issue records
- maintain linked references and metadata

This is where AI performs the heavy operating work.

### Stage E: Human Decision Gate

If the workflow reaches a trust-sensitive boundary, a human decision is required.

Typical triggers:
- escalation
- exception handling
- override
- approval
- release of high-impact outputs
- trust-critical security decisions
- legal or compliance review boundary

This is not a sign of failure.
It is a designed control point.

### Stage F: Evidence And State Update

After work progresses or stops, the system should update visible state and evidence.

Typical actions:
- record what happened
- attach evidence or decision context
- update issue state or workflow state
- update document or record posture
- preserve traceability for later review

This stage makes the process inspectable rather than hidden.

## 3. Output Model

SA-NOM does not produce only text responses.
It produces governed outputs.

### Operational Outputs

Examples:
- completed or partially completed task actions
- routed work items
- prepared drafts
- role-based execution outcomes

### Human Review Outputs

Examples:
- approval requests
- escalation items
- exception records
- Human Ask summaries
- decision-ready reports

### Artifact Outputs

Examples:
- controlled document drafts
- released document metadata
- issue records
- follow-up items
- evidence-linked artifacts
- audit-supporting records

### Visibility Outputs

Examples:
- dashboard posture
- readiness status
- structural warning signals
- workflow status views
- compliance posture summaries

## 4. Control Boundary Model Inside The Flow

The input-process-output model should always be read with control boundaries in mind.

The most important boundaries are:
- policy boundary
- authority boundary
- structural trust boundary
- escalation boundary
- override boundary
- approval boundary
- evidence boundary

These boundaries determine whether the process continues autonomously, pauses, or hands the decision to a human.

## 5. AI Versus Human Role In The Model

The system is intentionally asymmetric.

### AI-Heavy Responsibilities

AI should do most of the operational preparation work, such as:
- classification
- summarization
- routing preparation
- draft generation
- context linkage
- template filling
- issue preparation
- status reporting

### Human-Decision Responsibilities

Humans should remain responsible for:
- final exception acceptance
- escalation decisions
- trust-sensitive approval
- merge-blocking or release-blocking decisions
- override of higher-risk boundaries
- final legal, regulatory, or accountability decisions

This is the core operating model of SA-NOM.

## 6. Simplified End-To-End View

A simplified view of the full system looks like this:

1. structured input enters
2. the system classifies the input
3. policy and authority boundaries are interpreted
4. structural trust is evaluated
5. AI performs work inside approved scope
6. humans intervene only at trust-sensitive decision points
7. evidence, state, and artifacts are recorded
8. outputs become visible as governed work results

## Summary

SA-NOM's input-process-output model is designed to turn structured inputs into governed operational outputs through policy interpretation, structural trust evaluation, bounded AI execution, human decision gates, and evidence-rich state updates.

That is what makes the system a governed operating architecture rather than only an AI interface.
