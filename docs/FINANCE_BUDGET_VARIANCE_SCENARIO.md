# Guided Finance Budget-Variance Scenario

Use this scenario when you want to show a real governed workflow for the public-safe finance budget-variance pack, not only infrastructure readiness.

## Goal

By the end of this scenario you should be able to show that SA-NOM can:
- accept a finance-review style workload
- keep the AI role inside a bounded budget, variance, and exception-review scope
- escalate CAPEX and budget exceptions to a human instead of approving them automatically
- retain a reviewable evidence-oriented output shape

## Recommended Starting Point

Before running this scenario, make sure you already have:
- a passing guided smoke report from `python scripts/guided_smoke_test.py --registration-code DEMO-ORG`
- a ready Ollama lane from `python scripts/ollama_demo_environment.py`
- a passing provider probe from `python scripts/provider_demo_flow.py --provider ollama --probe`
- familiarity with the pack in [FINANCE_BUDGET_VARIANCE_ROLE_PACK.md](FINANCE_BUDGET_VARIANCE_ROLE_PACK.md)

## Scenario Story

This scenario models a finance exception review where:
- a monthly budget packet enters review under spend pressure
- the AI role summarizes cost variance, margin exposure, and CAPEX pressure
- a budget exception requires human approval
- the runtime keeps fund release and commitment authority with a human finance owner
- the final output includes a review summary, escalation note, and evidence-oriented state

## Scenario Inputs

Use the role-pack baseline from:
- [../examples/finance_budget_variance_role_pack.example.json](../examples/finance_budget_variance_role_pack.example.json)

Scenario assumptions:
- request type: budget exception review
- issue type: overtime and supplier cost variance driving an adverse month-end forecast
- provider lane: Ollama
- operating mode: indirect
- reporting line: `FINANCE`

## What The AI Role Should Do

Inside the governed lane, the finance role may:
- review the budget packet
- summarize cost variance
- highlight margin pressure
- prepare an escalation note for the finance owner

Inside the governed lane, the finance role must not:
- release funds
- approve a CAPEX commitment
- change customer pricing
- approve the budget exception autonomously

## Suggested Demo Flow

1. Start from the finance pack definition in [FINANCE_BUDGET_VARIANCE_ROLE_PACK.md](FINANCE_BUDGET_VARIANCE_ROLE_PACK.md).
2. Explain that this is an indirect finance operator, not an autonomous budget approver.
3. Show the scenario output in [../examples/finance_budget_variance_scenario.example.json](../examples/finance_budget_variance_scenario.example.json).
4. Call out these fields in the example output:
   - `scenario_id`
   - `selected_provider`
   - `role_pack.template_id`
   - `review_result.summary`
   - `review_result.escalation_required`
   - `review_result.wait_human_actions`
   - `evidence.summary`
5. Explain that the role can prepare the exception path but the approval still belongs to a human finance owner.

## Expected Outcome

The governed outcome should show:
- a successful review pass
- an escalation requirement for the budget-exception path
- no autonomous release of funds or CAPEX approval
- evidence-oriented output that can be reviewed later

## Matching Example Artifact

See [../examples/finance_budget_variance_scenario.example.json](../examples/finance_budget_variance_scenario.example.json).

This sanitized example is meant to help evaluators understand the expected shape before building a richer live scenario implementation.

## Why This Scenario Matters

This scenario is the bridge between:
- upstream procurement and cost-pressure review
- finance budget governance
- downstream accounting and bank-facing control stories

It shows that SA-NOM is not only proving provider health or startup readiness. It is showing how a governed AI role behaves inside a real financial-control workflow.

## What This Unlocks Next

After this finance lane, the next high-value expansion is:
- accounting close-readiness and exception handling
- GR/IR or accrual review workflows
- banking or treasury-facing approval and control stories where needed by the customer

That means this scenario can be used as the midpoint between procurement governance and deeper financial-control operations.

## Next Steps

- For the pack definition: [FINANCE_BUDGET_VARIANCE_ROLE_PACK.md](FINANCE_BUDGET_VARIANCE_ROLE_PACK.md)
- For the private demo lane: [OLLAMA_DEMO_ENVIRONMENT.md](OLLAMA_DEMO_ENVIRONMENT.md)
- For the customer walkthrough: [LIVE_CUSTOMER_WALKTHROUGH.md](LIVE_CUSTOMER_WALKTHROUGH.md)
- For the commercial path after a strong scenario fit: [COMMERCIAL_DISCOVERY_CHECKLIST.md](COMMERCIAL_DISCOVERY_CHECKLIST.md)
