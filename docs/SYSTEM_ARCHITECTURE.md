# System Architecture

This document defines the system-level architecture of SA-NOM.

It should be read as an architecture blueprint, not as a claim that the current public repository already implements every layer in full depth.

The goal is to make the overall structure legible before later milestones deepen runtime behavior, enterprise engineering, and production hardening.

## Why This Document Exists

SA-NOM already has many strong module-level guides: governance language, structural intelligence, governed document work, compliance baselines, security workflow, and deployment posture.

What was still missing was a single architecture document that explains how those parts fit together as one system.

This guide provides that view.

## Architecture Principle

SA-NOM follows a `structure-first` architecture.

That means the system is designed around:
- explicit role shape before freeform AI behavior
- explicit authority boundaries before autonomous action
- structural and governance checks before trust progression
- evidence and reviewability before hidden automation
- human decision authority at trust-sensitive boundaries

The implementation technology may evolve over time.
The architecture principle should remain stable.

## Core Operating Principle

SA-NOM is designed so AI does the work inside approved boundaries, while humans step in only when the task or decision goes beyond what AI is allowed or trusted to handle.

That means the architecture is not built around humans manually doing every step.
It is built around:
- AI as the primary operating actor inside governed scope
- humans as the authority layer for escalation, exception, override, approval, and trust-sensitive judgment

## System Layers

Use this mental model for the system as a whole.

### 1. Input Layer

This is where governed work enters the system.

Typical inputs include:
- role definitions and role packs
- job descriptions and organization-specific position inputs
- PTAG policies and authority definitions
- documents, forms, templates, and records
- compliance baselines and workflow assets
- runtime requests and operational tasks
- Human Ask prompts and reporting requests
- issue workflow items such as security exceptions or follow-up items
- provider signals, runtime events, and environment readiness data

The purpose of the input layer is not only intake.
It is structured intake.

### 2. Governance And Policy Layer

This layer defines what a role is, what it can do, what it cannot do, and under which conditions higher-risk actions require human control.

The main public architecture element here is PTAG.

This layer is responsible for:
- role definition
- authority boundaries
- constraints
- policy conditions
- decision references
- readable governance structure

This layer answers: `what is allowed in principle?`

### 3. Structural Intelligence Layer

This layer evaluates whether the surrounding organizational and control structure is strong enough to trust.

The main public architecture element here is PT-OSS.

This layer is responsible for:
- structural dependency assessment
- fragility assessment
- human override integrity assessment
- asymmetry and concentration-of-control signals
- structural blockers or readiness warnings

This layer answers: `even if the policy allows it, is the surrounding structure safe enough to trust?`

### 4. Execution And Orchestration Layer

This is the layer where AI performs actual work inside approved role boundaries.

It is responsible for:
- carrying work through a governed role
- routing actions through authority and policy checks
- producing working outputs, drafts, summaries, or task progression
- pausing or escalating when a boundary is exceeded

This layer answers: `what work can move forward right now inside the approved scope?`

### 5. Human Decision Layer

This is the control layer for decisions that should not be finalized autonomously.

It is responsible for:
- approval
- escalation
- override
- exception handling
- trust-sensitive confirmation
- higher-risk publication or release decisions

This layer exists so SA-NOM does not confuse AI assistance with final authority.

This layer answers: `what still requires accountable human judgment?`

### 6. Audit And Evidence Layer

This layer keeps the system reviewable.

It is responsible for:
- recording what happened
- attaching evidence to important actions
- retaining decision context
- making review, audit, and after-the-fact inspection possible
- supporting trust, compliance, and controlled operations

This layer answers: `how will we show what happened and why?`

### 7. Governed Work Modules

These are domain-facing operating layers built on top of the architecture.

Current public examples include:
- governed AI roles and scenarios
- Governed Document Center
- compliance workflow and response layers
- security workflow for exceptions, follow-up, labels, and escalation

These modules are where architecture becomes operationally useful.

### 8. Output And Integration Layer

This is the layer that makes system work visible and usable.

It may include:
- operational actions and governed task outcomes
- reports and Human Ask responses
- approved or released document artifacts
- security issues and workflow records
- audit and evidence outputs
- dashboard posture and readiness views
- deployment and provider-facing status signals

This layer answers: `what leaves the system as a visible result?`

## End-To-End Architecture Flow

A simplified flow looks like this:

1. structured inputs enter the system
2. governance and policy define the allowed boundary
3. structural intelligence evaluates trust posture
4. execution moves work forward inside approved scope
5. human decision points handle exception, escalation, approval, and override when needed
6. audit and evidence capture the path taken
7. outputs become visible through artifacts, reports, dashboards, issues, or governed actions

## Relationship Between Major Public Components

Use this practical model:

- `PTAG` defines role and policy structure
- `PT-OSS` evaluates structural trust posture
- `Authority Guard` or equivalent runtime controls enforce boundaries during action
- `Human Ask` brings humans into reporting, review, and meeting workflows
- `Governed Document Center` applies the same operating principle to controlled document work
- `Security workflow` applies the same operating principle to exception, follow-up, ownership, and escalation records
- `Audit and evidence` make the system inspectable instead of opaque

## Technology Boundary

This architecture should not be read as tied to one implementation language or one runtime shape forever.

The public `0.1.xx` series may currently surface specific implementation choices, but the architecture itself is broader than those details.

That means SA-NOM should be understood as:
- a governed AI operating architecture
- a role-and-boundary model
- a trust and evidence model
- a structured execution system

Implementation tiers can evolve in `0.2.xx` and beyond without changing the architectural logic.

## What This Architecture Is Not

This architecture is not:
- a loose chatbot wrapper
- an unrestricted automation engine
- a document storage bucket
- a compliance claim by itself
- a system where AI is treated as the final authority for trust-sensitive decisions

## Summary

SA-NOM is best understood as a structure-first governed AI operations architecture.

Its layers move from structured input, to policy, to structural trust, to governed execution, to human decision, to evidence, to visible operational output.

That is the foundation that later implementation tiers should build on.
