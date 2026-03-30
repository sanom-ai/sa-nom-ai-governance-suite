# Guided Purchasing Supplier-Risk Scenario

Use this scenario when you want to show a real governed workflow for the public-safe purchasing supplier-risk pack, not only infrastructure readiness.

## Goal

By the end of this scenario you should be able to show that SA-NOM can:
- accept a procurement-review style workload
- keep the AI role inside a bounded supplier-risk and exception-review scope
- escalate sourcing and policy exceptions to a human instead of approving them automatically
- retain a reviewable evidence-oriented output shape

## Recommended Starting Point

Before running this scenario, make sure you already have:
- a passing guided smoke report from `python scripts/guided_smoke_test.py --registration-code DEMO-ORG`
- a ready Ollama lane from `python scripts/ollama_demo_environment.py`
- a passing provider probe from `python scripts/provider_demo_flow.py --provider ollama --probe`
- familiarity with the pack in [PURCHASING_SUPPLIER_RISK_ROLE_PACK.md](PURCHASING_SUPPLIER_RISK_ROLE_PACK.md)

## Scenario Story

This scenario models a purchasing exception review where:
- a purchase request enters review under lead-time pressure
- the AI role summarizes supplier, sourcing, and compliance concerns
- a single-source or approved-supplier override requires human approval
- the runtime keeps approval with a human procurement owner
- the final output includes a review summary, escalation note, and evidence-oriented state

## Scenario Inputs

Use the role-pack baseline from:
- [../examples/purchasing_supplier_risk_role_pack.example.json](../examples/purchasing_supplier_risk_role_pack.example.json)

Scenario assumptions:
- request type: single-source procurement exception
- issue type: lead-time disruption plus approved-supplier override
- provider lane: Ollama
- operating mode: indirect
- reporting line: `PROCUREMENT`

## What The AI Role Should Do

Inside the governed lane, the purchasing role may:
- review the request
- summarize supplier risk
- flag lead-time exposure
- prepare escalation notes

Inside the governed lane, the purchasing role must not:
- appoint a supplier
- sign a supplier contract
- release funds
- approve the procurement exception autonomously

## Suggested Demo Flow

1. Start from the purchasing pack definition in [PURCHASING_SUPPLIER_RISK_ROLE_PACK.md](PURCHASING_SUPPLIER_RISK_ROLE_PACK.md).
2. Explain that this is an indirect procurement operator, not an autonomous sourcing approver.
3. Show the scenario output in [../examples/purchasing_supplier_risk_scenario.example.json](../examples/purchasing_supplier_risk_scenario.example.json).
4. Call out these fields in the example output:
   - `scenario_id`
   - `selected_provider`
   - `role_pack.template_id`
   - `review_result.summary`
   - `review_result.escalation_required`
   - `review_result.wait_human_actions`
   - `evidence.summary`
5. Explain that the role can prepare the exception path but the approval still belongs to a human procurement owner.

## Expected Outcome

The governed outcome should show:
- a successful review pass
- an escalation requirement for the sourcing exception path
- no autonomous approval of the procurement exception
- evidence-oriented output that can be reviewed later

## Matching Example Artifact

See [../examples/purchasing_supplier_risk_scenario.example.json](../examples/purchasing_supplier_risk_scenario.example.json).

This sanitized example is meant to help evaluators understand the expected shape before building a richer live scenario implementation.

## Why This Scenario Matters

This scenario is an upstream manufacturing workflow bridge between:
- technical readiness
- pilot-ready procurement packs
- buyer-facing workflow stories for supply risk and sourcing governance

It shows that SA-NOM is not only proving provider health or startup readiness. It is showing how a governed AI role behaves inside a real organizational workflow.

## What This Unlocks Next

After this procurement lane, the next high-value expansion is:
- finance budget and cost-variance review
- accounting close-readiness and exception handling
- banking or treasury-facing approval and control stories where needed by the customer

That means this scenario can be used as the upstream entrypoint before the product story moves into finance, accounting, and bank-facing controls.

## Next Steps

- For the pack definition: [PURCHASING_SUPPLIER_RISK_ROLE_PACK.md](PURCHASING_SUPPLIER_RISK_ROLE_PACK.md)
- For the private demo lane: [OLLAMA_DEMO_ENVIRONMENT.md](OLLAMA_DEMO_ENVIRONMENT.md)
- For the customer walkthrough: [LIVE_CUSTOMER_WALKTHROUGH.md](LIVE_CUSTOMER_WALKTHROUGH.md)
- For the commercial path after a strong scenario fit: [COMMERCIAL_DISCOVERY_CHECKLIST.md](COMMERCIAL_DISCOVERY_CHECKLIST.md)
