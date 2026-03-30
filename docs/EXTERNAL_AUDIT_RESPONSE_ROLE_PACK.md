# External Audit Response Role Pack

`External Audit Response Pack` is a pilot-ready public-safe starter pack for external auditor request review, evidence-gap posture, and governed response escalation.

## Goal

This pack helps teams show how SA-NOM can support external audit preparation and response without letting AI close findings, alter evidence, or release regulatory responses autonomously.

It is designed for organizations that need a governed role to summarize auditor requests, track evidence readiness, and route high-impact response decisions to human owners.

## Included Public-Safe Assets

- Role Private Studio template: `external_audit_response_pack`
- Starter example: `External Audit Response Lead`
- Public-safe example artifact: `examples/external_audit_response_role_pack.example.json`

## What This Pack Is For

Use this pack for:

- external auditor evidence-request review
- corrective-action and finding-response summaries
- management-response escalation
- governed reporting before human audit-response decisions

## What This Pack Is Not For

This pack is not an autonomous audit responder.

It should not:

- close an audit finding on its own
- release a regulatory response
- alter or reseal evidence without human approval
- bypass audit or executive authority

## Operating Shape

Suggested reporting line: `AUDIT`

Suggested business domain: `audit_response`

Suggested mode: `indirect`

This keeps the role positioned as a governed audit-review seat, not a direct autonomous authority over audit closure or regulatory filings.

## Authority Boundary

The pack intentionally keeps high-impact response decisions human-gated.

Examples of actions that still require human decision or override:

- `approve_audit_response_exception`
- `approve_regulatory_response`
- audit-finding closure
- management response approval
- regulatory filing release

## Example Story

An external auditor asks for supporting evidence, one corrective action is still open, and leadership needs a clear view of which responses are ready and which still require escalation.

SA-NOM can use this pack to generate one governed audit role that summarizes the response posture, flags missing evidence, and prepares escalation outputs for human audit leadership.

## How To Use It In A Demo Or Pilot

1. Open Role Private Studio
2. Start from `external_audit_response_pack`
3. Tailor the reporting line, assigned user, and handled resources to the target audit context
4. Review the generated PTAG and audit-response boundary
5. Publish only after the human gate and policy review are complete

## Example Artifact

See [external_audit_response_role_pack.example.json](../examples/external_audit_response_role_pack.example.json) for a public-safe sample output.

## Good Pilot Fit

This pack is a good fit when an organization wants to test:

- whether audit-response posture becomes faster and clearer
- whether evidence gaps are escalated earlier
- whether management-response decisions stay governed and reviewable

## Not A Good Pilot Fit

This pack is not a good fit if the organization expects AI to:

- close audit findings automatically
- send regulatory responses without approval
- rewrite evidence or approvals after the fact

## What This Opens Next

This pack leads naturally into:

- a guided external-audit response scenario
- regulator-response stories
- customer and certification audit-response workflows
