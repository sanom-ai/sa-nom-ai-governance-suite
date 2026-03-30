# Guided HR Policy Scenario

Use this scenario when you want to show a real governed workflow for the public-safe HR policy pack, not only infrastructure readiness.

## Goal

By the end of this scenario you should be able to show that SA-NOM can:
- accept an HR policy-review style workload
- keep the AI role inside a bounded policy and employee-case review scope
- escalate compensation or policy exceptions to a human instead of approving them automatically
- retain a reviewable evidence-oriented output shape

## Recommended Starting Point

Before running this scenario, make sure you already have:
- a passing guided smoke report from `python scripts/guided_smoke_test.py --registration-code DEMO-ORG`
- a ready Ollama lane from `python scripts/ollama_demo_environment.py`
- a passing provider probe from `python scripts/provider_demo_flow.py --provider ollama --probe`
- familiarity with the pack in [HR_POLICY_ROLE_PACK.md](HR_POLICY_ROLE_PACK.md)

## Scenario Story

This scenario models an HR policy accommodation review where:
- a non-standard leave or accommodation request enters review
- the AI role summarizes employee-impact and labor/compliance concerns
- a compensation or policy exception requires human approval
- the runtime keeps approval with a human HR owner
- the final output includes a review summary, escalation note, and evidence-oriented state

## Scenario Inputs

Use the role-pack baseline from:
- [../examples/hr_policy_role_pack.example.json](../examples/hr_policy_role_pack.example.json)

Scenario assumptions:
- case type: policy accommodation request
- issue type: non-standard leave accommodation with compensation exception
- provider lane: Ollama
- operating mode: indirect
- reporting line: `HR`

## What The AI Role Should Do

Inside the governed lane, the HR role may:
- review the policy request
- summarize employee-impact risk
- flag labor and compliance exposure
- prepare escalation notes

Inside the governed lane, the HR role must not:
- terminate an employee
- finalize a compensation change
- approve the HR policy exception autonomously

## Suggested Demo Flow

1. Start from the HR pack definition in [HR_POLICY_ROLE_PACK.md](HR_POLICY_ROLE_PACK.md).
2. Explain that this is an indirect HR operator, not an autonomous personnel decision maker.
3. Show the scenario output in [../examples/hr_policy_scenario.example.json](../examples/hr_policy_scenario.example.json).
4. Call out these fields in the example output:
   - `scenario_id`
   - `selected_provider`
   - `role_pack.template_id`
   - `review_result.summary`
   - `review_result.escalation_required`
   - `review_result.wait_human_actions`
   - `evidence.summary`
5. Explain that the role can prepare the exception path but the approval still belongs to a human HR owner.

## Expected Outcome

The governed outcome should show:
- a successful review pass
- an escalation requirement for the exception path
- no autonomous approval of the HR policy exception
- evidence-oriented output that can be reviewed later

## Matching Example Artifact

See [../examples/hr_policy_scenario.example.json](../examples/hr_policy_scenario.example.json).

This sanitized example is meant to help evaluators understand the expected shape before building a richer live scenario implementation.

## Why This Scenario Matters

This scenario is a bridge between:
- technical readiness
- pilot-ready HR policy packs
- buyer-facing workflow stories for people operations

It shows that SA-NOM is not only proving provider health or startup readiness. It is showing how a governed AI role behaves inside a real organizational workflow.

## Next Steps

- For the pack definition: [HR_POLICY_ROLE_PACK.md](HR_POLICY_ROLE_PACK.md)
- For the private demo lane: [OLLAMA_DEMO_ENVIRONMENT.md](OLLAMA_DEMO_ENVIRONMENT.md)
- For the customer walkthrough: [LIVE_CUSTOMER_WALKTHROUGH.md](LIVE_CUSTOMER_WALKTHROUGH.md)
- For the commercial path after a strong scenario fit: [COMMERCIAL_DISCOVERY_CHECKLIST.md](COMMERCIAL_DISCOVERY_CHECKLIST.md)
