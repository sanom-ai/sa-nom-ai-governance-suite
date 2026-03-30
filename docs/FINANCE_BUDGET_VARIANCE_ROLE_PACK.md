# Finance Budget Variance Role Pack

Use this guide when you want a pilot-ready finance role pack that demonstrates governed budget review, cost-variance escalation, and human approval boundaries on the private default SA-NOM lane.

## Goal

By the end of this guide you should understand:
- what the public-safe finance role pack is designed to do
- which actions stay inside the AI lane and which actions must escalate to humans
- how to use the finance pack during evaluation, demos, or pilot discussions
- which example artifacts match the pack

## Included Public-Safe Assets

This role-pack starter currently ships as:
- a library template in `resources/studio/role_private_studio_templates.json`
- a starter example in `resources/studio/role_private_studio_examples.json`
- a sanitized example artifact in [../examples/finance_budget_variance_role_pack.example.json](../examples/finance_budget_variance_role_pack.example.json)

The current library template id is:
- `finance_budget_variance_pack`

The starter example name is:
- `Finance Budget Variance Lead`

## What This Pack Is For

This pack is meant to show how SA-NOM can help a finance team with:
- budget-versus-actual review
- cost variance summaries
- spend pressure and margin-risk review
- CAPEX or budget exception routing
- escalation note preparation

It is intentionally not meant to:
- release funds
- approve CAPEX commitments
- change customer pricing
- replace human finance authority

## Default Operating Shape

The pack is designed around an indirect operating mode:
- `reporting_line = FINANCE`
- `operating_mode = indirect`
- `assigned_user_id = FINANCE_MANAGER_01`
- `executive_owner_id = EXEC_OWNER`

That means the AI lane is explicitly positioned as a governed finance operator, not as an autonomous budget approver.

## Default Authority Boundaries

Default allowed actions include:
- `review_budget`
- `summarize_cost_variance`
- `prepare_finance_report`
- `approve_budget_exception`

Default forbidden actions include:
- `release_funds`
- `approve_capex_commitment`
- `change_customer_pricing`

Default wait-human actions include:
- `approve_budget_exception`
- `approve_capex_commitment`

This is important: the role pack can help analyze and prepare the exception path, but a human finance owner still owns the approval decision.

## Suggested Demo Or Pilot Story

Use this pack when you want to show a real operational story rather than only infrastructure readiness.

Recommended talk track:
- a budget or variance packet enters review
- the AI role summarizes cost variance, spend pressure, and margin impact
- the role prepares an escalation note when it sees a CAPEX or budget exception path
- the governed runtime keeps approval with a human finance owner
- the result can be reviewed through evidence and escalation-oriented outputs

## How To Use It In Role Private Studio

1. Start with the template library item `finance_budget_variance_pack`.
2. Adjust the assigned user id, executive owner id, and seat id for the target environment.
3. Keep funding, CAPEX commitments, and pricing decisions outside the autonomous lane.
4. Generate and review the PTAG output.
5. Run the normal studio validation and simulation flow before publication.

## Matching Example Artifact

See [../examples/finance_budget_variance_role_pack.example.json](../examples/finance_budget_variance_role_pack.example.json) for a sanitized payload that matches the intended pack shape.

You can also compare it with:
- [../examples/guided_smoke_test.example.json](../examples/guided_smoke_test.example.json)
- [../examples/runtime_startup_smoke.example.json](../examples/runtime_startup_smoke.example.json)

## Good Pilot Fit

This pack is a good early pilot candidate when the customer wants to evaluate:
- governed budget review support
- cost variance and margin-pressure escalation
- exception routing instead of autonomous finance decisions
- a private local-model path through Ollama

## Not A Good Fit

This pack is not a good first pilot if the customer expects:
- AI to release funds or approve CAPEX on its own
- unsupervised finance authority
- removal of human review from sensitive financial decisions

## What This Opens Next

This finance lane is the natural bridge into the next deeper layers:
- accounting close readiness and GR/IR exceptions
- bank-facing treasury controls or payment approval stories
- audit review of financial-control exceptions

## Next Steps

- For the live private-model lane: [OLLAMA_DEMO_ENVIRONMENT.md](OLLAMA_DEMO_ENVIRONMENT.md)
- For the evaluator path: [GUIDED_EVALUATION.md](GUIDED_EVALUATION.md)
- For the demo talk track: [LIVE_CUSTOMER_WALKTHROUGH.md](LIVE_CUSTOMER_WALKTHROUGH.md)
- For commercial qualification: [COMMERCIAL_DISCOVERY_CHECKLIST.md](COMMERCIAL_DISCOVERY_CHECKLIST.md)
