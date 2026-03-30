# Quality Release and Audit Readiness Scenario

This guided scenario shows how SA-NOM can use the `quality_audit_readiness_pack` inside a governed workflow that combines QC defect posture, QA release-readiness review, and audit-evidence escalation.

It is designed to demonstrate how AI can summarize quality and audit status while still stopping at the human approval boundary.

## Scenario Goal

Show that SA-NOM can support quality operations when a defect trend, an open deviation, and an evidence gap all exist at the same time before product release.

## Suggested Setup

- Role pack: `quality_audit_readiness_pack`
- Starter role: `Quality Audit Readiness Lead`
- Default private demo lane: Ollama
- Supporting materials: defect triage packet, deviation report, release-readiness packet, audit-evidence packet

## Example Story

A production run is nearing release, but QC has recorded a defect spike, QA still has an open deviation review, and the internal audit team is asking for missing control evidence tied to the same batch history.

The AI role is allowed to review the exception chain, summarize the readiness posture, and prepare an escalation note. It is not allowed to release held product, waive a requirement, or close an audit finding on its own.

## Human Ask Layer

This scenario is a good fit for `Human Ask` because a person can call the role in for reporting or a cross-functional meeting.

Examples:

- ask the quality role to summarize the current defect and release-readiness posture
- call a meeting with production, quality, and audit roles to review the control gap
- request an evidence-backed status note before leadership decides whether to release the lot

## Governed Flow

1. A defect triage packet and deviation report are prepared
2. The quality role reviews defect posture, release readiness, and audit-evidence gaps
3. SA-NOM summarizes the combined quality and audit risk
4. The role prepares a governed exception report
5. If release depends on a deviation waiver or quality-hold release, the flow stops for human decision
6. Evidence is preserved for later internal or external audit review

## Human-Gated Boundaries

The AI role must not:

- release a quality hold
- waive a specification requirement
- close an audit finding

Those remain human decisions, even if the AI has already summarized the situation and recommended an escalation path.

## Why This Scenario Matters

This scenario helps evaluators see that SA-NOM can connect plant-floor quality, release posture, and audit readiness inside one governed operating model.

It also creates a natural bridge to the next lanes:

- delivery-readiness escalation
- internal audit response
- external audit response
- customer-facing containment and release communication

## Example Artifact

See [quality_audit_readiness_scenario.example.json](../examples/quality_audit_readiness_scenario.example.json) for a public-safe scenario output.

## Demo Tip

During a live walkthrough, combine this scenario with the production line-exception story and use the `Human Ask` layer to show a cross-functional review before any release decision is made.
