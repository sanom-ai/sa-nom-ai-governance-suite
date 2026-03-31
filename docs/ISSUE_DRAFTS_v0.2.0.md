# Issue Drafts - v0.2.0

Use these draft issues to turn the `v0.2.0` roadmap into implementation work.

## 1. Add Governed Runtime Orchestration Baseline

**Goal**
Create a clearer runtime model for how governed AI work moves through state, routing, and role execution.

**Scope ideas**
- state flow
- task routing
- role execution lifecycle
- AI-prepared to human-confirmed transitions

**Success signal**
Runtime behavior reads as one governed system instead of isolated execution steps.

## 2. Add Authority And Decision Engine Baseline

**Goal**
Make approval, escalation, override, and human-required states more explicit in runtime behavior.

**Scope ideas**
- approval gates
- escalation rules
- override path
- blocked and exception states

**Success signal**
Trust-sensitive decisions are easier to locate, explain, and enforce.

## 3. Define Policy And Runtime Contracts

**Goal**
Translate blueprint language into structured contracts that runtime code can follow more consistently.

**Scope ideas**
- role, task, and decision schemas
- state contracts
- evidence object contracts
- boundary enforcement rules

**Success signal**
Governance language becomes more enforceable in code and easier to extend.

## 4. Strengthen Evidence And Audit Execution

**Goal**
Improve how runtime actions, decisions, and exceptions are recorded.

**Scope ideas**
- decision records
- action trace
- exception trace
- workflow evidence objects

**Success signal**
Audit posture is supported by stronger execution artifacts, not only documentation.

## 5. Improve Demo And Ease Of Use

**Goal**
Make local private-first evaluation easier for maintainers, reviewers, and technical buyers.

**Scope ideas**
- simpler quickstart path
- easier Ollama setup
- guided demo flow
- local exploration path

**Success signal**
Trying SA-NOM locally takes less setup work and feels more intentional.

## 6. Add Runtime Reliability And Recovery Baseline

**Goal**
Make runtime flow more resilient when interrupted or degraded.

**Scope ideas**
- failure modes
- retries
- resume behavior
- operator recovery path

**Success signal**
The runtime story covers degraded execution, not only happy-path behavior.

## 7. Close v0.2.0 With A Capstone Validation Use Case

**Goal**
Plan for a real end-to-end use case at the end of the milestone that proves the implementation direction on a real machine.

**Scope ideas**
- cross-layer local validation flow
- phase-close release framing
- real-machine runtime proof
- explicit statement of what was validated and what remains open

**Success signal**
`v0.2.0` closes with a concrete capstone use case instead of only a list of implementation slices.
