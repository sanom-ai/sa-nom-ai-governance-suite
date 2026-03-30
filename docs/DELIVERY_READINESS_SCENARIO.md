# Delivery Readiness Scenario

This guided scenario shows how SA-NOM can use the `delivery_readiness_pack` inside a governed workflow that covers finished-goods release posture, dispatch exceptions, and customer-commitment risk.

It is designed to demonstrate how AI can summarize delivery status while still stopping at the human approval boundary.

## Scenario Goal

Show that SA-NOM can support the final release-to-shipment lane when finished goods are almost ready to dispatch but one or more exceptions still require human review.

## Suggested Setup

- Role pack: `delivery_readiness_pack`
- Starter role: `Delivery Readiness Lead`
- Default private demo lane: Ollama
- Supporting materials: shipment readiness packet, FG release snapshot, dispatch exception, customer commitment record

## Example Story

A batch is nearly ready to leave the warehouse, but delivery still has one dispatch exception open and sales is asking whether the promised ship date will slip.

The AI role is allowed to review the readiness packet, summarize the risk, and prepare an escalation note. It is not allowed to release the shipment, change the customer commitment, or override an export-control hold on its own.

## Human Ask Layer

This scenario is a good fit for `Human Ask` because a person can call the role in for reporting or a cross-functional meeting.

Examples:

- ask the delivery role to summarize the current shipment-readiness posture
- call a meeting with quality, delivery, and sales roles to review the dispatch exception
- request an evidence-backed status note before leadership decides whether to release the shipment

## Governed Flow

1. A shipment readiness packet and dispatch exception are prepared
2. The delivery role reviews release posture and customer-commitment risk
3. SA-NOM summarizes the delivery exception chain
4. The role prepares a governed dispatch report
5. If shipment release or commitment change is required, the flow stops for human decision
6. Evidence is preserved for later review and audit traceability

## Human-Gated Boundaries

The AI role must not:

- release a shipment
- change a customer delivery commitment
- override an export-control hold

Those remain human decisions, even if the AI has already summarized the situation and recommended an escalation path.

## Why This Scenario Matters

This scenario helps evaluators see that SA-NOM can carry the governed workflow all the way to the shipment boundary, not only the planning and quality stages.

It also creates a natural bridge to the next lanes:

- customer escalation and service recovery
- external audit response
- fulfillment and logistics exception workflows

## Example Artifact

See [delivery_readiness_scenario.example.json](../examples/delivery_readiness_scenario.example.json) for a public-safe scenario output.

## Demo Tip

During a live walkthrough, combine this scenario with the quality scenario and use the `Human Ask` layer to show a final cross-functional shipment review before any dispatch decision is made.
