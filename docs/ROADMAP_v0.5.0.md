# Roadmap - v0.5.0

This roadmap opens the `v0.5.0` phase after the PTAG public-opening and PTAG polish releases.

## Theme

Move SA-NOM from a quality prototype to a serious organizational candidate.

## Milestone Goal

By the end of `v0.5.0`, SA-NOM should feel less like a well-structured prototype and more like a governed AI operations system that real organizations can seriously evaluate for pilot use.

The center of that shift is a single new layer:

`Governed Human-in-the-Loop Operations`

This layer should connect PTAG, runtime control, human approvals, auditability, and operational reliability into one coherent operational surface rather than a scattered set of separate features.

## Core Position

`v0.5.0` should not try to build five unrelated products.
It should build one operational structure that covers the most important trust questions an organization will ask before considering real adoption.

That means the phase should answer questions such as:
- what actions can proceed automatically
- what actions must wait for human approval
- who is the approver, reviewer, or escalation owner
- where the rationale and evidence are recorded
- how operators inspect the system when bottlenecks or risks appear
- how runtime and governance posture stay visible enough for serious internal evaluation

The result should be a single governed operations layer that is broad enough to matter, but narrow enough to finish cleanly.

## Primary Structure

### 1. Governed HITL Operations Layer

Target areas:
- connect PTAG authority and policy logic to real human approval paths
- define trigger classes for actions that require human review or approval
- represent approval, review, escalation, and override as explicit governed operations
- capture rationale and evidence for each intervention

Expected outcomes:
- SA-NOM can show a real human-in-the-loop control loop rather than only policy definitions
- high-risk actions remain visible and governed
- organizations can understand where AI stops and where human authority begins

### 2. Operational Maintenance And Runtime Reliability Surface

Target areas:
- basic runtime gates, health posture, and failure-sensitive operational checks
- clearer operational signals around governance bottlenecks, policy violations, and escalation frequency
- reliability framing that makes the governed operations layer more credible in real evaluation settings

Expected outcomes:
- the governed HITL layer is supported by a more inspectable runtime posture
- the system looks safer to evaluate for real pilot use
- operational trust no longer depends only on documentation claims

### 3. Human-Facing Evaluation Surface

Target areas:
- a simple approval-facing interface story such as inbox, approval board, or comment-and-rationale flow
- Human Ask reporting that lets people ask status questions without bypassing governance
- examples and use cases that show how the HITL model works in realistic organizational scenarios

Expected outcomes:
- humans can understand and interact with the governed control loop more directly
- evaluation becomes easier for technical and non-technical stakeholders
- the repo shows how governance is experienced, not only how it is described

### 4. Integration And Compliance Continuity

Target areas:
- the smallest useful integration surface needed to make governed operations believable in context
- continuity between HITL operations and the repo's compliance/localization posture
- disciplined extension points rather than a broad connector explosion

Expected outcomes:
- SA-NOM feels easier to imagine inside an existing organizational stack
- Thai and broader compliance-oriented readers can connect the operational layer to real governance expectations
- integration work supports the core governed operations story rather than distracting from it

## Non-Goals

- no major PTAG syntax migration in `v0.5.0`
- no attempt to become a fully finished enterprise platform in one release
- no sprawling integration catalog
- no broad feature split that turns this phase into multiple unrelated tracks
- no removal of human authority from high-risk or trust-sensitive decisions

## Candidate Deliverables

- a core governed HITL operations model
- a primary governed HITL operations architecture document
- explicit human-approval and escalation triggers
- a simple approval/rationale/audit interaction surface
- a minimal human approval surface document and first interface model
- Human Ask reporting for governed status visibility
- a governed HITL Human Ask reporting document and reporting model
- a small set of realistic role-pack or use-case examples for HITL operations
- a compact HITL role-packs and use-cases reference document
- reliability and observability framing that supports serious organizational evaluation
- a governed HITL reliability and observability baseline document
- `v0.5.0` planning and release materials

## Exit Criteria

- SA-NOM can explain one coherent governed HITL operations layer instead of scattered governance ideas
- PTAG is connected to real approval and escalation paths
- human intervention is visible, reviewable, and auditable
- runtime and governance posture are credible enough for serious organizational consideration
- `v0.5.0` clearly advances SA-NOM from quality prototype toward pilot-ready evaluation status

