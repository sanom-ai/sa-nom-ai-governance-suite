# Regulator Response Scenario

This guided scenario shows how SA-NOM can use the `regulator_response_pack` inside a governed workflow that covers regulator requests, disclosure gaps, deadline posture, and official-response escalation.

It is designed to demonstrate how AI can summarize regulator-response posture while still stopping at the human approval boundary.

## Scenario Goal

Show that SA-NOM can support a regulator response when a deadline is active, one or more disclosure items are still incomplete, and leadership must decide whether the organization is ready to respond.

## Suggested Setup

- Role pack: `regulator_response_pack`
- Starter role: `Regulator Response Coordination Lead`
- Default private demo lane: Ollama
- Supporting materials: regulator request packet, regulatory evidence packet, response deadline record, regulator response draft

## Example Story

A regulator asks for clarification and supporting evidence within a fixed response window. One disclosure item is still incomplete, and compliance leadership needs a clear view of whether the planned response is ready or must be escalated.

The AI role is allowed to review the request, summarize the evidence posture, and prepare an escalation note. It is not allowed to release the official response, submit a filing, or waive a requirement on its own.

## Human Ask Layer

This scenario is a good fit for `Human Ask` because a person can call the role in for reporting or a cross-functional meeting.

Examples:

- ask the regulator-response role to summarize the current deadline and disclosure posture
- call a meeting with compliance, legal, and executive stakeholders to review the response gap
- request an evidence-backed status note before leadership approves the regulator response

## Governed Flow

1. A regulator request and evidence packet are prepared
2. The regulator-response role reviews disclosure posture and deadline exposure
3. SA-NOM summarizes the regulator-response risk
4. The role prepares a governed response report
5. If official response release or filing submission is required, the flow stops for human decision
6. Evidence is preserved for later review and traceability

## Human-Gated Boundaries

The AI role must not:

- release an official regulator response
- submit a regulatory filing
- waive a regulatory requirement

Those remain human decisions, even if the AI has already summarized the situation and recommended an escalation path.

## Why This Scenario Matters

This scenario helps evaluators see that SA-NOM can support not only operational review and audit posture, but also time-sensitive regulator-facing workflows where legal and compliance boundaries matter.

It also creates a natural bridge to the next lanes:

- sector-specific regulator workflows
- supervisory examination response
- enterprise remediation governance

## Example Artifact

See [regulator_response_scenario.example.json](../examples/regulator_response_scenario.example.json) for a public-safe scenario output.

## Demo Tip

During a live walkthrough, combine this scenario with the external-audit story and use the `Human Ask` layer to show how SA-NOM can pull together deadline-aware, evidence-backed reporting before leadership answers a regulator.
