# Roadmap - v0.2.6

This roadmap defines the next enterprise-runtime milestone after `v0.2.5` completed the first governed multi-step execution baseline.

## Theme

Execution runtime that survives and recovers: SA-NOM should be able to keep governed workflow state across interruptions, resume deterministically, and expose operator-facing execution posture without falling back to ad hoc recovery behavior.

## Milestone Goal

By the end of `v0.2.6`, SA-NOM should show that enterprise execution is not only structured and auditable, but durable enough to survive pause, restart, retry, and recovery conditions in a governed way.

## Core Position

`v0.2.6` does not chase usability polish yet.  
It closes the runtime durability gap so `v0.2.x` can move toward enterprise execution completion before `v0.3.0` shifts focus to quick start, dashboard, and non-technical ease of use.

## Workstreams

### 1. Workflow State Store

Target areas:
- persistent workflow and step state storage
- explicit workflow source-of-truth boundaries
- durable tracking for active, blocked, resumed, and completed states
- recovery-safe correlation between workflow state and evidence

Expected outcomes:
- workflow progress survives process restarts
- runtime can inspect current state without reconstructing everything from loose metadata
- step progression stops drifting across long-running execution

### 2. Cross-Step Resume And Recovery

Target areas:
- deterministic resume after human wait, timeout, restart, or partial failure
- governed retry, replay, and dead-letter posture
- fail-closed recovery when state or evidence is incomplete
- explicit recovery outcomes and runtime state transitions

Expected outcomes:
- interrupted workflows can continue safely
- recovery no longer depends on informal operator reconstruction
- failure handling looks enterprise-shaped instead of best-effort

### 3. Governed Task Packets

Target areas:
- machine-readable packet contract for step, role, queue, and integration handoff
- embedded authority, policy, correlation, and evidence references
- packet validation before routing or execution resumes
- stable packet boundaries for future UI and operator tooling

Expected outcomes:
- cross-step work moves through a consistent envelope
- role and queue transitions become easier to inspect and replay
- runtime can reject malformed or incomplete handoff payloads deterministically

### 4. Human Decision Inbox / Console Contract

Target areas:
- operator-facing contract for human review inbox items
- structured required-action, context, lane, and priority metadata
- explicit transitions between human inbox and returned-to-AI execution
- preparation for a later `v0.3.0` dashboard/UI surface

Expected outcomes:
- human checkpoints become clearer and more actionable
- the future UI can plug into an already-governed inbox model
- AI continues doing heavy workflow work while humans see only decision-ready items

### 5. Operational Readiness Hooks

Target areas:
- runtime health and readiness signals
- workflow backlog, blocked, retry, and dead-letter counters
- operator-readable execution summaries for private/self-managed deployments
- release and workflow evidence hooks for runtime operations

Expected outcomes:
- operators can see whether enterprise execution is healthy
- runtime failures and backlog posture become measurable
- `v0.2.x` gets materially closer to enterprise operation, not only enterprise structure

## Non-Goals

- no polished dashboard or non-technical user experience layer yet
- no dependency-heavy rewrite just to appear more modern
- no claim that `v0.2.6` alone finishes the full `v0.2.x` phase close

## Candidate Deliverables

- workflow state store baseline and state persistence contract
- resume/recovery runtime slice with retry and dead-letter posture
- governed task packet schema and validation slice
- human inbox/console contract baseline
- operational readiness and runtime visibility slice
- `v0.2.6` release notes and closeout summary

## Exit Criteria

- workflow state is durable across restart and pause conditions
- resume and recovery paths are explicit, governed, and fail closed when invalid
- task handoff packets are structured, validated, and correlated
- human decision inbox objects are ready for a future operator surface
- operators can inspect core execution health and backlog posture
- `v0.2.x` is materially closer to enterprise execution completion, with `v0.2.7` reserved for validation, proof, reliability, and phase close
