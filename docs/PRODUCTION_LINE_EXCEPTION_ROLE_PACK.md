# Production Line Exception Role Pack

`Production Line Exception Pack` is a pilot-ready public-safe starter pack for production-line exception review, stoppage posture, schedule-recovery routing, and governed escalation inside manufacturing operations.

## Goal

This pack helps teams show how SA-NOM can support production review work without letting AI run the line autonomously.

It is designed for scenarios where operators, supervisors, and plant leaders need a governed AI role that can summarize line exceptions, flag recovery risk, and prepare escalation outputs for human decision makers.

## Included Public-Safe Assets

- Role Private Studio template: `production_line_exception_pack`
- Starter example: `Production Line Exception Lead`
- Public-safe example artifact: `examples/production_line_exception_role_pack.example.json`

## What This Pack Is For

Use this pack for:

- line stoppage and downtime review
- schedule-recovery and throughput-risk summaries
- customer-commitment exposure routing
- governed escalation when production exceptions cross human approval boundaries

## What This Pack Is Not For

This pack is not an autonomous production controller.

It should not:

- release schedule changes on its own
- override quality holds
- change customer delivery commitments
- bypass human production authority

## Operating Shape

Suggested reporting line: `PRODUCTION`

Suggested business domain: `manufacturing_operations`

Suggested mode: `indirect`

This keeps the role positioned as a governed operational-review seat, not a direct autonomous executor on the line.

## Authority Boundary

The pack intentionally keeps high-impact decisions human-gated.

Examples of actions that still require human decision or override:

- `approve_recovery_exception`
- `approve_schedule_override`
- production schedule release
- quality-hold bypass
- customer-commitment changes

## Example Story

A production manager wants a governed AI role that can review daily line stoppage packets, summarize the likely throughput effect, and flag when recovery plans create customer-commitment risk.

SA-NOM can use this pack to generate the governed role definition, route it through review, and keep the authority boundary explicit: AI can summarize and escalate, but humans still approve schedule overrides and delivery-impact decisions.

## How To Use It In A Demo Or Pilot

1. Open Role Private Studio
2. Start from `production_line_exception_pack`
3. Tailor the reporting line, assigned user, and handled resources to the target plant or line
4. Review the generated PTAG and authority boundary
5. Publish only after the human gate and policy review are complete

## Example Artifact

See [production_line_exception_role_pack.example.json](../examples/production_line_exception_role_pack.example.json) for a public-safe sample output.

## Good Pilot Fit

This pack is a good fit when an organization wants to test:

- how AI can support production-exception reviews
- whether line-risk reporting becomes faster and clearer
- how escalation works across warehouse, production, and customer-commitment pressure

## Not A Good Pilot Fit

This pack is not a good fit if the organization expects AI to:

- change production schedules automatically
- bypass quality or compliance controls
- make autonomous release decisions on behalf of production leadership

## What This Opens Next

This pack leads naturally into:

- production line exception scenario guidance
- QC defect triage stories
- QA deviation and release-readiness stories
- delivery-readiness escalation stories
