# v0.3.0 Handoff

## Purpose

This document defines the handoff from the `v0.2.x` enterprise execution phase into the `v0.3.0` usability phase.

`v0.2.x` focused on making the governed execution core real, durable, provable, and safe.

`v0.3.0` should focus on making that system easier to start, easier to see, and easier to operate for users who are not deep in the codebase.

## Completed In v0.2.x

The execution-system baseline now includes:

- governed runtime orchestration
- authority engine enforcement and fail-closed decision boundaries
- policy contract expansion and runtime preflight validation
- evidence objects and end-to-end audit traceability
- state flow and role execution lifecycle tracking
- workflow state persistence across restart
- recovery, replay, dead-letter handling, and fail-closed resume posture
- governed task packet contracts for cross-step runtime handoff
- human decision inbox contract for operator-facing review work
- operational readiness view for backlog and runtime action pressure
- enterprise validation suite for pause, resume, recovery, and restart continuity
- workflow proof bundle export for audit/operator handoff
- focused CI coverage and reliability gates for enterprise runtime paths

## Explicitly Not The Focus Of v0.3.0

`v0.3.0` should not reopen broad execution-core scope by default.

That means the primary goal is not:

- inventing a new orchestration core
- redesigning authority logic from scratch
- replacing the runtime state/recovery model
- expanding proof artifacts into a new evidence architecture

Those areas are now baseline capabilities and should only change if a concrete usability need or correctness gap requires it.

## v0.3.0 Focus Areas

### Quick Start

- guided startup in 5-10 minutes
- cleaner local/private deployment flow
- fewer manual steps before first successful run

### Dashboard And Operator UX

- simple web dashboard for non-technical users
- visibility into workflow status, readiness, inbox, and proof exports
- clear actions for human-confirmed steps

### Demo And First-Run Experience

- smoother local demo setup
- easier example workflow execution
- clearer proof that the system is working on a real machine

## Guardrails For v0.3.0

- structure-first still applies
- reuse the `v0.2.x` runtime contracts rather than bypassing them
- UX should expose governed behavior, not hide or weaken it
- dashboard and quick start should consume real runtime surfaces already present in the system

## Definition Of Success

`v0.3.0` is successful if a new operator can:

- start the system quickly
- understand what the system is doing
- see when human action is required
- inspect workflow state and proof artifacts without digging through implementation files
- validate value on a local/private environment with minimal setup friction
