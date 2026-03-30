# HR Policy Role Pack

Use this guide when you want a pilot-ready HR role pack that demonstrates governed policy review, employee-case routing, and human approval boundaries on the private default SA-NOM lane.

## Goal

By the end of this guide you should understand:
- what the public-safe HR role pack is designed to do
- which actions stay inside the AI lane and which actions must escalate to humans
- how to use the HR pack during evaluation, demos, or pilot discussions
- which example artifacts match the pack

## Included Public-Safe Assets

This role-pack starter currently ships as:
- a library template in `resources/studio/role_private_studio_templates.json`
- a starter example in `resources/studio/role_private_studio_examples.json`
- a sanitized example artifact in [../examples/hr_policy_role_pack.example.json](../examples/hr_policy_role_pack.example.json)

The current library template id is:
- `hr_policy_escalation_pack`

The starter example name is:
- `HR Policy Escalation Lead`

## What This Pack Is For

This pack is meant to show how SA-NOM can help an HR or people-operations team with:
- policy exception review
- leave and accommodation routing
- disciplinary-process checks
- employee-impact summaries
- escalation note preparation

It is intentionally not meant to:
- terminate employees
- waive statutory obligations
- finalize compensation changes
- replace human HR authority

## Default Operating Shape

The pack is designed around an indirect operating mode:
- `reporting_line = HR`
- `operating_mode = indirect`
- `assigned_user_id = HR_MANAGER_01`
- `executive_owner_id = EXEC_OWNER`

That means the AI lane is explicitly positioned as a governed HR operator, not as an autonomous decision maker on sensitive people matters.

## Default Authority Boundaries

Default allowed actions include:
- `review_hr_policy`
- `summarize_hr_risk`
- `advise_compliance`
- `approve_hr_policy_exception`

Default forbidden actions include:
- `terminate_employee`
- `waive_statutory_obligation`
- `finalize_compensation_change`

Default wait-human actions include:
- `approve_hr_policy_exception`
- `approve_compensation_exception`

This is important: the role pack can help analyze and prepare the exception path, but a human HR owner still owns the approval decision.

## Suggested Demo Or Pilot Story

Use this pack when you want to show a real operational story rather than only infrastructure readiness.

Recommended talk track:
- an HR policy exception enters review
- the AI role summarizes employee-impact and labor/compliance concerns
- the role prepares an escalation note when it sees an exception or compensation path
- the governed runtime keeps approval with a human HR owner
- the result can be reviewed through evidence and escalation-oriented outputs

## How To Use It In Role Private Studio

1. Start with the template library item `hr_policy_escalation_pack`.
2. Adjust the assigned user id, executive owner id, and seat id for the target environment.
3. Keep terminations, compensation changes, and policy exceptions outside the autonomous lane.
4. Generate and review the PTAG output.
5. Run the normal studio validation and simulation flow before publication.

## Matching Example Artifact

See [../examples/hr_policy_role_pack.example.json](../examples/hr_policy_role_pack.example.json) for a sanitized payload that matches the intended pack shape.

You can also compare it with:
- [../examples/guided_smoke_test.example.json](../examples/guided_smoke_test.example.json)
- [../examples/runtime_startup_smoke.example.json](../examples/runtime_startup_smoke.example.json)

## Good Pilot Fit

This pack is a good early pilot candidate when the customer wants to evaluate:
- governed HR policy review support
- exception routing instead of autonomous personnel decisions
- an HR or compliance use case that needs evidence and escalation
- a private local-model path through Ollama

## Not A Good Fit

This pack is not a good first pilot if the customer expects:
- AI to terminate employees or finalize compensation changes
- unsupervised HR authority
- removal of human review from sensitive people decisions

## Next Steps

- For the live private-model lane: [OLLAMA_DEMO_ENVIRONMENT.md](OLLAMA_DEMO_ENVIRONMENT.md)
- For the evaluator path: [GUIDED_EVALUATION.md](GUIDED_EVALUATION.md)
- For the demo talk track: [LIVE_CUSTOMER_WALKTHROUGH.md](LIVE_CUSTOMER_WALKTHROUGH.md)
- For commercial qualification: [COMMERCIAL_DISCOVERY_CHECKLIST.md](COMMERCIAL_DISCOVERY_CHECKLIST.md)
