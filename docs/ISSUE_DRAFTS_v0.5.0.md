# Issue Drafts - v0.5.0

Use these issue drafts to deliver the `v0.5.0` governed human-in-the-loop operations phase.

## 1. Define The Governed HITL Operations Layer

**Goal**
Create one coherent operational model that connects PTAG, human approval, escalation, rationale capture, and auditability.

**Scope ideas**
- define the HITL operating model in one primary architecture document
- identify the trigger classes that must require human review or approval
- define the core states for approve, reject, review, escalate, override, and stop

**Success signal**
SA-NOM can explain a real governed human-in-the-loop control loop in one place.

## 2. Add A Minimal Human Approval Surface

**Goal**
Give the governed HITL model a simple but believable human interaction surface.

**Scope ideas**
- approval inbox, dashboard, or operator review lane
- rationale and comment capture for human decisions
- escalation owner visibility and basic approval routing

**Success signal**
A human can inspect, approve, reject, or escalate a governed action without bypassing the system.

## 3. Add Human Ask Reporting For Governed Status Visibility

**Goal**
Let humans ask the system about decision state, pending approvals, and intervention history without bypassing governance.

**Scope ideas**
- Human Ask queries for pending approvals and decision status
- visibility into approval bottlenecks or escalation posture
- reporting paths that stay inside governance boundaries

**Success signal**
Human Ask becomes a governed visibility surface for HITL operations, not just a convenience path.

## 4. Add HITL Role Packs, Use Cases, And Reliability Framing

**Goal**
Show how the new governed operations layer applies in realistic scenarios and why it is credible for serious evaluation.

**Scope ideas**
- 2-3 HITL-oriented role packs or use cases
- audit trail expectations for human interventions
- observability, runtime gate, and reliability notes that support the operational story
- the smallest useful integration/compliance continuity needed to support evaluation

**Success signal**
`v0.5.0` looks like one serious operational candidate rather than a pile of disconnected ideas.

## 5. Close v0.5.0 As A Serious-Evaluation Milestone

**Goal**
Finish the phase with a release story that clearly explains the step from quality prototype toward serious organizational consideration.

**Scope ideas**
- release notes for `v0.5.0`
- evaluation framing for what the system can now demonstrate
- explicit note about what still remains outside full production claims

**Success signal**
`v0.5.0` reads as a disciplined milestone that organizations can evaluate seriously, not as a vague expansion release.
