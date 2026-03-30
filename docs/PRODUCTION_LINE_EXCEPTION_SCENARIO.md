# Production Line Exception Scenario

This guided scenario shows how SA-NOM can use the `production_line_exception_pack` inside a governed manufacturing workflow.

It is designed to demonstrate how AI can summarize line stoppage posture, flag schedule-recovery risk, and route production exceptions without crossing the human approval boundary.

## Scenario Goal

Show that SA-NOM can support production leaders when a line stoppage threatens throughput, schedule recovery, and customer commitments, while still keeping schedule overrides and release decisions human-gated.

## Suggested Setup

- Role pack: `production_line_exception_pack`
- Starter role: `Production Line Exception Lead`
- Default private demo lane: Ollama
- Supporting materials: line exception packet, stoppage report, recovery plan, customer-commitment snapshot

## Example Story

A constrained production line stops because a high-priority material and tooling issue blocks normal output. Operations wants to understand how much throughput is at risk, whether the proposed recovery plan is realistic, and whether a customer commitment is now exposed.

The AI role is allowed to review the exception packet, summarize the likely impact, and prepare an escalation note. It is not allowed to change the schedule, bypass quality controls, or revise the customer commitment on its own.

## Human Ask Layer

This scenario is a good fit for `Human Ask` because a person can call the role in for status reporting or cross-functional review.

Examples:

- ask the production role to summarize the current line-exception posture
- call a meeting with warehouse, production, and finance roles to review the recovery path
- request an evidence-backed status note before leadership decides on a schedule override

## Governed Flow

1. A line exception packet is prepared
2. The production role reviews stoppage details and recovery assumptions
3. SA-NOM summarizes throughput and customer-commitment exposure
4. The role prepares a governed exception report
5. If recovery requires a schedule override or commitment change, the flow stops for human decision
6. Evidence is preserved for later review

## Human-Gated Boundaries

The AI role must not:

- release a production schedule change
- bypass a quality hold
- change a customer commitment

Those remain human decisions, even if the AI has already summarized the situation and recommended an escalation path.

## Why This Scenario Matters

This scenario helps evaluators see that SA-NOM is not just for static governance documentation. It can participate in real production review work while keeping the operating boundary explicit.

It also creates a natural bridge to the next manufacturing lanes:

- warehouse shortage review
- QC defect triage
- QA release-readiness
- delivery-readiness escalation

## Example Artifact

See [production_line_exception_scenario.example.json](../examples/production_line_exception_scenario.example.json) for a public-safe scenario output.

## Demo Tip

During a live walkthrough, combine this scenario with the warehouse shortage story and ask for a cross-functional production meeting through the `Human Ask` layer. This helps show that SA-NOM supports operational coordination, not only one isolated role.
