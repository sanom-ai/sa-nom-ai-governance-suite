# Roadmap - v0.2.5

This roadmap defines the next execution milestone after `v0.2.4` completed runtime control hardening.

## Theme

Governed multi-step execution: AI should be able to carry real work across step chains, role handoffs, and bounded workflow state while humans intervene only at explicit trust-sensitive checkpoints.

## Milestone Goal

By the end of `v0.2.5`, SA-NOM should show that governed execution is not only safe at the single-request level, but composable across multi-step runtime flows that remain deterministic, auditable, and enterprise-readable.

## Core Position

`v0.2.5` does not remove human authority.  
It reduces unnecessary human operational burden by turning more of the workflow body into AI-executed, policy-bounded, stateful runtime behavior.

## Workstreams

### 1. Execution Plan Contract

Target areas:
- machine-readable execution plan object for multi-step runtime work
- explicit step ids, step intent, expected outputs, and stop conditions
- bounded plan mutation / resume semantics
- fail-closed handling when plan state drifts from policy or evidence

Expected outcomes:
- runtime can execute more than one isolated decision safely
- step chains become inspectable instead of implicit
- reviewers can understand what the AI intended to do next

### 2. Stateful Task Routing And Role Handoffs

Target areas:
- step-level role assignment and handoff rules
- role transition evidence across workflow stages
- routing rules for blocked, escalated, and resumed steps
- deterministic handoff validation before execution continues

Expected outcomes:
- AI can move work across roles inside bounded workflow logic
- handoffs stop looking ad hoc
- human review only appears when trust or authority actually changes

### 3. Human-Minimized Decision Queue

Target areas:
- AI-prepared decision bundle for human confirmation points
- batched approval / escalation queue model
- explicit `ready_for_human`, `human_pending`, `returned_to_ai` states
- fewer fragmented human interrupts for routine workflow progress

Expected outcomes:
- humans review prepared decisions instead of doing operational glue work
- AI carries more of the workflow body autonomously
- trust-sensitive decisions stay visible without slowing all steps equally

### 4. Workflow Evidence Bundle

Target areas:
- workflow-level evidence object linking plan -> steps -> handoffs -> decisions
- reusable workflow correlation chain beyond single request ids
- release/workflow proof artifact generation
- audit-friendly snapshot of why a workflow stopped, resumed, or completed

Expected outcomes:
- multi-step execution becomes reviewable end to end
- runtime evidence supports diligence, incident review, and release proof
- enterprise evaluators can inspect workflow correctness without guessing

### 5. Enterprise Execution Hooks

Target areas:
- workflow-scale retry / timeout / dead-letter posture
- stronger local-private execution validation path
- cleaner operator-facing run controls for private deployments
- implementation hooks that prepare `v0.2.x` to transition toward enterprise execution tier

Expected outcomes:
- workflow runtime looks more production-shaped
- private/self-managed operation becomes more believable as a product surface
- `v0.2.x` starts to bridge from structure-first into enterprise execution behavior

## Non-Goals

- no uncontrolled autonomous execution outside explicit authority boundaries
- no dependency-heavy rewrite for the sake of fashion alone
- no claim of complete enterprise orchestration in one milestone

## Candidate Deliverables

- execution-plan schema and runtime planner baseline
- step-state and handoff enforcement slice
- human decision queue contract and state transitions
- workflow evidence bundle and correlation artifact slice
- runtime workflow reliability and operator control slice
- `v0.2.5` release notes and closeout validation summary

## Exit Criteria

- multi-step execution plans are explicit and enforceable
- role handoffs are validated and evidenced in runtime
- human confirmation is batched and structured where possible
- workflow-level evidence bundles connect plan, steps, decisions, and outcomes
- private execution path looks materially closer to enterprise runtime behavior
