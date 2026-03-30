# New Model Launch Readiness Role Pack

Use this guide when you want a pilot-ready manufacturing NPI role pack that demonstrates governed launch-readiness review, cross-functional exception routing, and human approval boundaries on the private default SA-NOM lane.

## Goal

By the end of this guide you should understand:
- what the public-safe NPI role pack is designed to do
- which actions stay inside the AI lane and which actions must escalate to humans
- how to use the NPI pack during evaluation, demos, or pilot discussions
- which example artifacts match the pack

## Included Public-Safe Assets

This role-pack starter currently ships as:
- a library template in `resources/studio/role_private_studio_templates.json`
- a starter example in `resources/studio/role_private_studio_examples.json`
- a sanitized example artifact in [../examples/new_model_launch_readiness_role_pack.example.json](../examples/new_model_launch_readiness_role_pack.example.json)

The current library template id is:
- `new_model_launch_readiness_pack`

The starter example name is:
- `New Model Launch Readiness Lead`

## What This Pack Is For

This pack is meant to show how SA-NOM can help a manufacturing organization with:
- new model launch-readiness review
- APQP and trial-build exception summaries
- supplier, tooling, and control-plan gap review
- PPAP and launch-gate escalation routing
- cross-functional launch note preparation

It is intentionally not meant to:
- release a new model launch
- approve process changes on its own
- waive customer requirements
- replace human manufacturing authority

## Default Operating Shape

The pack is designed around an indirect operating mode:
- `reporting_line = NPI`
- `operating_mode = indirect`
- `assigned_user_id = NPI_MANAGER_01`
- `executive_owner_id = EXEC_OWNER`

That means the AI lane is explicitly positioned as a governed launch-readiness operator, not as an autonomous launch approver.

## Default Authority Boundaries

Default allowed actions include:
- `review_launch_readiness`
- `summarize_npi_exception`
- `prepare_launch_report`
- `approve_launch_exception`

Default forbidden actions include:
- `release_new_model_launch`
- `approve_process_change`
- `waive_customer_requirement`

Default wait-human actions include:
- `approve_launch_exception`
- `approve_process_change`

This is important: the role pack can help analyze and prepare the launch exception path, but a human NPI or manufacturing owner still owns the final release decision.

## Suggested Demo Or Pilot Story

Use this pack when you want to show a real manufacturing story rather than only infrastructure readiness.

Recommended talk track:
- a new model approaches the launch gate with open readiness issues
- the AI role summarizes APQP, trial-build, supplier, and control-plan exposure
- the role prepares an escalation note when it sees a launch or process-change exception path
- the governed runtime keeps release and waiver decisions with a human owner
- the result can be reviewed through evidence and escalation-oriented outputs

## How To Use It In Role Private Studio

1. Start with the template library item `new_model_launch_readiness_pack`.
2. Adjust the assigned user id, executive owner id, and seat id for the target environment.
3. Keep launch release, process changes, and customer waivers outside the autonomous lane.
4. Generate and review the PTAG output.
5. Run the normal studio validation and simulation flow before publication.

## Matching Example Artifact

See [../examples/new_model_launch_readiness_role_pack.example.json](../examples/new_model_launch_readiness_role_pack.example.json) for a sanitized payload that matches the intended pack shape.

You can also compare it with:
- [../examples/purchasing_supplier_risk_role_pack.example.json](../examples/purchasing_supplier_risk_role_pack.example.json)
- [../examples/guided_smoke_test.example.json](../examples/guided_smoke_test.example.json)

## Good Pilot Fit

This pack is a good early pilot candidate when the customer wants to evaluate:
- governed new model launch review
- APQP, PPAP, and trial-build exception escalation
- cross-functional launch readiness routing instead of autonomous release
- a private local-model path through Ollama

## Not A Good Fit

This pack is not a good first pilot if the customer expects:
- AI to release a new model launch on its own
- unsupervised process-change approval
- waiver of customer requirements without human review

## What This Opens Next

This NPI lane is the natural bridge into the next deeper manufacturing layers:
- warehouse shortage and material-availability stories
- production line recovery and schedule-exception stories
- QC and QA release-readiness stories

## Next Steps

- Use this pack in a live demo with the private default Ollama lane.
- Pair it with a guided NPI scenario in the next implementation step.
- Connect it to supplier-risk, finance, and audit lanes during pilot scoping.