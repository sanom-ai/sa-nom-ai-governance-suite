# Legal Review Role Pack

Use this guide when you want a pilot-ready legal role pack that demonstrates governed contract review, exception routing, and human approval boundaries on the private default SA-NOM lane.

## Goal

By the end of this guide you should understand:
- what the public-safe legal role pack is designed to do
- which actions stay inside the AI lane and which actions must escalate to humans
- how to use the legal pack during evaluation, demos, or pilot discussions
- which example artifacts match the pack

## Included Public-Safe Assets

This role-pack starter currently ships as:
- a library template in `resources/studio/role_private_studio_templates.json`
- a starter example in `resources/studio/role_private_studio_examples.json`
- a sanitized example artifact in [../examples/legal_review_role_pack.example.json](../examples/legal_review_role_pack.example.json)

The current library template id is:
- `legal_review_escalation_pack`

The starter example name is:
- `Vendor Contract Risk Counsel`

## What This Pack Is For

This pack is meant to show how SA-NOM can help a legal or compliance-adjacent team with:
- vendor contract review
- non-standard clause analysis
- policy-exception routing
- escalation note preparation
- governed legal-risk summaries

It is intentionally not meant to:
- sign contracts
- waive obligations
- finalize external commitments
- replace human legal authority

## Default Operating Shape

The pack is designed around an indirect operating mode:
- `reporting_line = LEGAL`
- `operating_mode = indirect`
- `assigned_user_id = LEGAL_MANAGER_01`
- `executive_owner_id = EXEC_OWNER`

That means the AI lane is explicitly positioned as a governed legal operator, not as an autonomous approver.

## Default Authority Boundaries

Default allowed actions include:
- `review_contract`
- `summarize_legal_risk`
- `advise_compliance`
- `approve_contract_exception`

Default forbidden actions include:
- `sign_contract`
- `waive_regulatory_obligation`

Default wait-human actions include:
- `approve_contract_exception`

This is important: the role pack can help analyze and prepare the exception path, but a human still owns the approval decision.

## Suggested Demo Or Pilot Story

Use this pack when you want to show a real operational story rather than only infrastructure readiness.

Recommended talk track:
- a contract packet enters review
- the AI role summarizes non-standard clauses and legal/compliance exposure
- the role prepares an escalation note when it sees an exception path
- the governed runtime keeps the approval with a human legal owner
- the result can be reviewed through evidence and escalation-oriented outputs

## How To Use It In Role Private Studio

1. Start with the template library item `legal_review_escalation_pack`.
2. Adjust the assigned user id, executive owner id, and seat id for the target environment.
3. Keep signing and exception approval outside the autonomous lane.
4. Generate and review the PTAG output.
5. Run the normal studio validation and simulation flow before publication.

## Matching Example Artifact

See [../examples/legal_review_role_pack.example.json](../examples/legal_review_role_pack.example.json) for a sanitized payload that matches the intended pack shape.

You can also compare it with:
- [../examples/guided_smoke_test.example.json](../examples/guided_smoke_test.example.json)
- [../examples/runtime_startup_smoke.example.json](../examples/runtime_startup_smoke.example.json)

## Good Pilot Fit

This pack is a good early pilot candidate when the customer wants to evaluate:
- governed contract review support
- exception routing instead of autonomous approval
- a legal or compliance use case that needs evidence and escalation
- a private local-model path through Ollama

## Not A Good Fit

This pack is not a good first pilot if the customer expects:
- AI to sign or finalize contracts
- unsupervised legal authority
- removal of human legal review from sensitive commitments

## Next Steps

- For the live private-model lane: [OLLAMA_DEMO_ENVIRONMENT.md](OLLAMA_DEMO_ENVIRONMENT.md)
- For the evaluator path: [GUIDED_EVALUATION.md](GUIDED_EVALUATION.md)
- For the demo talk track: [LIVE_CUSTOMER_WALKTHROUGH.md](LIVE_CUSTOMER_WALKTHROUGH.md)
- For commercial qualification: [COMMERCIAL_DISCOVERY_CHECKLIST.md](COMMERCIAL_DISCOVERY_CHECKLIST.md)
