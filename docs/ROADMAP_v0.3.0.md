# Roadmap - v0.3.0

This roadmap opens the `v0.3.0` usability phase after the `v0.2.x` line established the enterprise execution baseline.

## Theme

Make the governed runtime easy to start, easy to see, and easy to operate without weakening the execution-core guarantees built in `v0.2.x`.

## Milestone Goal

By the end of `v0.3.0`, SA-NOM should feel materially easier to evaluate and operate on a local/private environment, especially for users who are not deeply familiar with the codebase.

## Core Position

`v0.3.0` is not a restart of the execution engine.  
It is the usability and operator-surface phase.

The runtime, authority engine, policy contracts, evidence model, workflow state, recovery, proof artifacts, and CI reliability gates now exist as the baseline. `v0.3.0` should expose those capabilities through simpler startup, clearer operator views, and lower-friction first-run flows.

## Workstreams

### 1. Quick Start In 5-10 Minutes

Target areas:
- one-command or near-one-command local/private startup path
- clearly documented first successful run flow
- reduced manual setup friction for model/provider and runtime prerequisites
- example workflow path that validates the system is actually alive

Expected outcomes:
- a new user can get the system running quickly
- first-run success no longer depends on reading large parts of the repo
- local/private evaluation becomes repeatable and confidence-building

### 2. Dashboard And Operator Surface

Target areas:
- simple web dashboard backed by real runtime surfaces
- workflow state, readiness, inbox, recovery, and proof visibility
- operator-readable actions for human-confirmed steps
- clear separation between AI-prepared work and human decision responsibilities

Expected outcomes:
- operators can understand runtime posture without opening internal files
- the runtime becomes visible, not just technically available
- non-technical stakeholders can inspect system state more safely

### 3. Demo And First-Run Experience

Target areas:
- guided local/private demo path
- working example flows tied to the governed runtime, not mock-only paths
- clear proof of success on a real machine
- fewer hidden assumptions about environment setup

Expected outcomes:
- the product becomes easier to show, not just easier to describe
- demo runs become more consistent across machines
- usability improvements reinforce product credibility directly

### 4. Operator Experience Hardening

Target areas:
- clearer status language for runtime states and human checkpoints
- simpler proof-export and handoff paths from operator surfaces
- safer defaults around human-required and blocked flows
- visible mapping from dashboard actions to governed runtime contracts

Expected outcomes:
- operators can act with less guesswork
- trust-sensitive transitions stay explicit in the UI layer
- usability grows without eroding governance semantics

## Non-Goals

- no major rewrite of the execution core without a concrete correctness need
- no dependency-heavy architecture shift just for appearance
- no bypass around authority, policy, evidence, or workflow-state contracts
- no UX layer that hides blocked, human-required, or fail-closed runtime states

## Candidate Deliverables

- `v0.3.0` quick-start flow and runnable example path
- baseline dashboard for workflow, readiness, inbox, and proof visibility
- first-run demo path for local/private validation
- operator-facing UX tightening for human-required and recovery paths
- `v0.3.0` release notes and usability closeout summary

## Exit Criteria

- a new operator can start the system in 5-10 minutes on a local/private machine
- the dashboard exposes real workflow, readiness, inbox, and proof data
- the first-run demo path proves the runtime is working end to end
- human-required and blocked states remain explicit and understandable
- `v0.3.0` materially improves ease of use without weakening governed runtime behavior
