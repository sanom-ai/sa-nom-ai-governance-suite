# Issue Drafts - v0.2.6

Use these issue drafts to deliver the `v0.2.6` execution-runtime durability milestone.

## 1. Add Workflow State Store Baseline

**Goal**
Introduce durable workflow and step state storage so governed execution can survive restarts and long-running runtime conditions.

**Scope ideas**
- define workflow-state object and persistence boundary
- store active, blocked, resumed, completed, and failed workflow states
- link state records to execution plan, queue, and evidence correlation ids
- protect against state drift between runtime results and stored workflow state

**Success signal**
Workflow state becomes durable, inspectable, and usable as a source of truth.

## 2. Add Cross-Step Resume And Recovery Controls

**Goal**
Make recovery after pause, timeout, restart, or partial failure deterministic and fail closed when conditions are invalid.

**Scope ideas**
- resume contract for human-wait and restart scenarios
- governed retry and replay controls
- dead-letter posture for unrecoverable workflow states
- recovery evidence object and state-transition tests

**Success signal**
Interrupted workflows can recover safely without relying on manual reconstruction.

## 3. Add Governed Task Packet Contract

**Goal**
Wrap cross-step work in a stable packet envelope that carries authority, policy, correlation, and evidence references.

**Scope ideas**
- define task packet schema for role, queue, and integration handoff
- validate packet integrity before route or resume
- capture packet correlation to execution plan, queue, and workflow state
- reject malformed packets in a deterministic fail-closed path

**Success signal**
Handoffs across runtime boundaries become structured, replayable, and auditable.

## 4. Add Human Decision Inbox / Console Contract

**Goal**
Turn human review checkpoints into a stable inbox contract that future operator surfaces can consume directly.

**Scope ideas**
- inbox item schema for required action, lane, priority, and decision context
- explicit inbox-to-AI return states
- correlation from inbox item to workflow step and decision queue
- evidence for review, approval, veto, and send-back outcomes

**Success signal**
Human review becomes decision-ready and UI-ready without changing governance semantics later.

## 5. Add Operational Readiness Hooks

**Goal**
Expose enough runtime health and operator visibility for enterprise execution to be believable in private/self-managed environments.

**Scope ideas**
- readiness and health signals for workflow runtime
- blocked, retry, dead-letter, and backlog counters
- operator-facing execution summary artifacts
- integration of release/workflow evidence into runtime operations view

**Success signal**
Operators can observe workflow health and backlog posture instead of inferring it indirectly.

## 6. Close v0.2.6 With Runtime Durability Proof

**Goal**
Finish the milestone with evidence that the governed runtime can survive and recover in practice.

**Scope ideas**
- end-to-end workflow pause/resume validation
- restart and recovery proof run
- release note closeout with runtime durability summary
- phase-handoff note that positions `v0.2.7` around validation, proof, reliability, and phase close

**Success signal**
`v0.2.6` closes with runtime survival and recovery proof, not only implementation claims.
