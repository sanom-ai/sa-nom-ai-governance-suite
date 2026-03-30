# External Audit Response Scenario

This guided scenario shows how SA-NOM can use the `external_audit_response_pack` inside a governed workflow that covers external auditor requests, evidence gaps, corrective-action status, and management-response escalation.

It is designed to demonstrate how AI can summarize audit-response posture while still stopping at the human approval boundary.

## Scenario Goal

Show that SA-NOM can support an external audit response when evidence is still incomplete, a corrective action remains open, and management must decide how to respond.

## Suggested Setup

- Role pack: `external_audit_response_pack`
- Starter role: `External Audit Response Lead`
- Default private demo lane: Ollama
- Supporting materials: external audit request, evidence packet, corrective-action status, management response draft

## Example Story

An external auditor requests supporting evidence for an open finding. One corrective action is still incomplete, and leadership needs a clear view of whether the planned management response is ready or must be escalated.

The AI role is allowed to review the request, summarize the evidence posture, and prepare an escalation note. It is not allowed to close the finding, release the official response, or alter the audit evidence on its own.

## Human Ask Layer

This scenario is a good fit for `Human Ask` because a person can call the role in for reporting or a cross-functional meeting.

Examples:

- ask the audit role to summarize the current external-audit response posture
- call a meeting with audit, quality, and executive stakeholders to review the evidence gap
- request an evidence-backed status note before leadership approves the management response

## Governed Flow

1. An external audit request and evidence packet are prepared
2. The audit role reviews evidence posture, corrective-action status, and response readiness
3. SA-NOM summarizes the audit-response risk
4. The role prepares a governed response report
5. If official response release or finding closure is required, the flow stops for human decision
6. Evidence is preserved for later review and traceability

## Human-Gated Boundaries

The AI role must not:

- close an audit finding
- release a regulatory or auditor response
- alter audit evidence

Those remain human decisions, even if the AI has already summarized the situation and recommended an escalation path.

## Why This Scenario Matters

This scenario helps evaluators see that SA-NOM can support not only internal operational workflows, but also the external accountability layer that many regulated organizations care about most.

It also creates a natural bridge to the next lanes:

- regulator-response workflows
- certification and customer audit response
- enterprise-wide corrective-action governance

## Example Artifact

See [external_audit_response_scenario.example.json](../examples/external_audit_response_scenario.example.json) for a public-safe scenario output.

## Demo Tip

During a live walkthrough, combine this scenario with the quality and delivery stories and use the `Human Ask` layer to show how SA-NOM can pull together evidence-backed reporting across the entire workflow before leadership answers an external auditor.
