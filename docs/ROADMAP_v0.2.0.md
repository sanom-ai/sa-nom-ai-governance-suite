# Roadmap - v0.2.0

This roadmap captures the first enterprise-tier implementation step after the `0.1.xx` structure-first and verification-baseline phase.

## Theme

Turn SA-NOM from a strong architecture and workflow blueprint into a more operational governed AI runtime with clearer authority boundaries, stronger evidence behavior, and more usable local evaluation paths.

## Milestone Goal

By the end of `v0.2.0`, a serious evaluator should be able to see that SA-NOM is no longer only defining the system well, but also beginning to execute that system more credibly in runtime behavior.

## Core Position

The purpose of this milestone is not to bolt enterprise language onto a blueprint.

The purpose is to make SA-NOM act more like the system it already describes: AI does the heavy operational work inside approved boundaries, while humans step in only at trust-sensitive decision points.

## Enterprise Priorities

### 1. Governed Runtime Orchestration

Build a clearer runtime execution path for governed AI work.

Target areas:
- state flow
- task routing
- role execution lifecycle
- AI-prepared to human-confirmed transitions

Expected outcomes:
- runtime behavior becomes easier to explain and test
- role execution feels less like isolated functions and more like a governed flow
- transition points between automation and human decision become clearer

### 2. Authority And Decision Engine

Make trust-sensitive boundaries more explicit in runtime logic.

Target areas:
- approval gates
- escalation rules
- override path
- blocked, exception, and human-required states

Expected outcomes:
- decision boundaries are easier to enforce consistently
- approval and escalation behavior moves closer to code-backed behavior
- reviewers can see where AI stops and human authority begins

### 3. Policy And Runtime Contracts

Create clearer structured contracts between policy concepts and runtime execution.

Target areas:
- role, task, and decision schemas
- structured state contracts
- evidence object contracts
- boundary enforcement rules

Expected outcomes:
- blueprint language becomes easier to enforce in code
- runtime behavior becomes less ad hoc
- future implementation work becomes easier to scale without losing governance clarity

### 4. Evidence And Audit Execution

Strengthen how governed actions and decisions are recorded.

Target areas:
- decision records
- action trace
- exception trace
- release and workflow evidence objects

Expected outcomes:
- trust and audit claims become easier to support with real execution artifacts
- enterprise evaluators can see stronger accountability posture
- operational history becomes more legible and reusable

### 5. Demo And Ease Of Use

Make local evaluation easier without abandoning the private-first and self-managed posture.

Target areas:
- simpler quickstart path
- easier Ollama setup and model path
- guided demo flow
- evaluator-friendly local walkthrough
- minimal playground or exploration path where appropriate

Expected outcomes:
- fewer steps are needed to try SA-NOM locally
- non-authors can understand the product faster
- the private-first story becomes easier to demonstrate in practice

### 6. Runtime Reliability And Recovery

Improve how the system behaves when runtime flow is interrupted or degraded.

Target areas:
- failure modes
- retries
- resume behavior
- interruption handling
- operator recovery path

Expected outcomes:
- runtime orchestration is not limited to happy-path stories
- operational trust improves
- future enterprise deployment work has a stronger resilience baseline

### 7. Phase-Close Validation And Capstone Use Case

Plan from the start for a real capstone validation at the end of the milestone.

Target areas:
- end-to-end use case that crosses multiple runtime layers
- local execution proof on a real maintainer machine
- phase-close verification framing
- release-close narrative that shows what was proven and what remains open

Expected outcomes:
- `v0.2.0` closes with a concrete use case, not only implementation slices
- the release story is easier for technical evaluators to trust
- the transition from `0.2.0` to later enterprise work stays disciplined

## Non-Goals For v0.2.0

- do not claim full enterprise maturity in one milestone
- do not add heavy platform complexity before the runtime model is coherent
- do not confuse local demo usability with full production readiness
- do not let AI cross trust-sensitive decision boundaries that still require human authority

## Candidate Deliverables

- `v0.2.0` roadmap and issue drafts
- governed runtime orchestration baseline document or implementation slice
- authority and decision engine baseline
- policy and runtime contract definition work
- evidence and audit execution improvements
- demo and usability improvements for local private-first evaluation
- runtime reliability and recovery baseline work
- end-to-end capstone validation and release-close use case

## Exit Criteria For v0.2.0

- runtime execution is more visibly governed, not only documented
- authority and escalation boundaries are clearer in implementation behavior
- evidence and audit execution is stronger and easier to inspect
- local evaluation is easier than in `0.1.xx`
- the milestone closes with a real capstone validation use case on top of the implementation work
