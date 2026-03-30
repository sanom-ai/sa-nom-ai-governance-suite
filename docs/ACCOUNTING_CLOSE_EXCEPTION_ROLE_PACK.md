# Accounting Close-Readiness Role Pack

Use this guide when you want a pilot-ready accounting role pack that demonstrates governed close-readiness review, reconciliation exception escalation, and human approval boundaries on the private default SA-NOM lane.

## Goal

By the end of this guide you should understand:
- what the public-safe accounting role pack is designed to do
- which actions stay inside the AI lane and which actions must escalate to humans
- how to use the accounting pack during evaluation, demos, or pilot discussions
- which example artifacts match the pack

## Included Public-Safe Assets

This role-pack starter currently ships as:
- a library template in `resources/studio/role_private_studio_templates.json`
- a starter example in `resources/studio/role_private_studio_examples.json`
- a sanitized example artifact in [../examples/accounting_close_exception_role_pack.example.json](../examples/accounting_close_exception_role_pack.example.json)

The current library template id is:
- `accounting_close_exception_pack`

The starter example name is:
- `Accounting Close Exception Lead`

## What This Pack Is For

This pack is meant to show how SA-NOM can help an accounting team with:
- month-end close readiness review
- reconciliation and accrual exception summaries
- GR/IR and period-end exposure review
- manual-adjustment exception routing
- escalation note preparation

It is intentionally not meant to:
- post manual journal entries
- close the financial period
- release payments
- replace human accounting authority

## Default Operating Shape

The pack is designed around an indirect operating mode:
- `reporting_line = ACCOUNTING`
- `operating_mode = indirect`
- `assigned_user_id = ACCOUNTING_MANAGER_01`
- `executive_owner_id = EXEC_OWNER`

That means the AI lane is explicitly positioned as a governed accounting operator, not as an autonomous close approver.

## Default Authority Boundaries

Default allowed actions include:
- `review_close_readiness`
- `summarize_accounting_exception`
- `prepare_close_report`
- `approve_close_exception`

Default forbidden actions include:
- `post_manual_journal`
- `close_financial_period`
- `release_payment`

Default wait-human actions include:
- `approve_close_exception`
- `approve_manual_adjustment`

This is important: the role pack can help analyze and prepare the exception path, but a human accounting owner still owns the approval decision.

## Suggested Demo Or Pilot Story

Use this pack when you want to show a real operational story rather than only infrastructure readiness.

Recommended talk track:
- a month-end close packet enters review
- the AI role summarizes reconciliation and accrual exceptions
- the role prepares an escalation note when it sees a manual-adjustment or close-readiness exception path
- the governed runtime keeps approval with a human accounting owner
- the result can be reviewed through evidence and escalation-oriented outputs

## How To Use It In Role Private Studio

1. Start with the template library item `accounting_close_exception_pack`.
2. Adjust the assigned user id, executive owner id, and seat id for the target environment.
3. Keep journal posting, period close, and payment release outside the autonomous lane.
4. Generate and review the PTAG output.
5. Run the normal studio validation and simulation flow before publication.

## Matching Example Artifact

See [../examples/accounting_close_exception_role_pack.example.json](../examples/accounting_close_exception_role_pack.example.json) for a sanitized payload that matches the intended pack shape.

You can also compare it with:
- [../examples/finance_budget_variance_role_pack.example.json](../examples/finance_budget_variance_role_pack.example.json)
- [../examples/runtime_startup_smoke.example.json](../examples/runtime_startup_smoke.example.json)

## Good Pilot Fit

This pack is a good early pilot candidate when the customer wants to evaluate:
- governed close-readiness support
- reconciliation and accrual exception escalation
- exception routing instead of autonomous accounting decisions
- a private local-model path through Ollama

## Not A Good Fit

This pack is not a good first pilot if the customer expects:
- AI to post journals or close a period on its own
- unsupervised accounting authority
- removal of human review from sensitive financial-control decisions

## What This Opens Next

This accounting lane is the natural bridge into the next deeper layers:
- bank-facing treasury controls and payment-approval stories
- external-audit evidence response workflows
- internal-audit exception review for financial controls

## Next Steps

- For the live private-model lane: [OLLAMA_DEMO_ENVIRONMENT.md](OLLAMA_DEMO_ENVIRONMENT.md)
- For the evaluator path: [GUIDED_EVALUATION.md](GUIDED_EVALUATION.md)
- For the demo talk track: [LIVE_CUSTOMER_WALKTHROUGH.md](LIVE_CUSTOMER_WALKTHROUGH.md)
- For commercial qualification: [COMMERCIAL_DISCOVERY_CHECKLIST.md](COMMERCIAL_DISCOVERY_CHECKLIST.md)