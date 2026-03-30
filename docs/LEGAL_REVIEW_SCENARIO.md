# Guided Legal Review Scenario

Use this scenario when you want to show a real governed workflow for the public-safe legal review pack, not only infrastructure readiness.

## Goal

By the end of this scenario you should be able to show that SA-NOM can:
- accept a legal-review style workload
- keep the AI role inside a bounded review scope
- escalate exception approval to a human instead of approving it automatically
- retain a reviewable evidence-oriented output shape

## Recommended Starting Point

Before running this scenario, make sure you already have:
- a passing guided smoke report from `python scripts/guided_smoke_test.py --registration-code DEMO-ORG`
- a ready Ollama lane from `python scripts/ollama_demo_environment.py`
- a passing provider probe from `python scripts/provider_demo_flow.py --provider ollama --probe`
- familiarity with the pack in [LEGAL_REVIEW_ROLE_PACK.md](LEGAL_REVIEW_ROLE_PACK.md)

## Scenario Story

This scenario models a vendor contract review where:
- a vendor master-services agreement arrives for review
- the AI role summarizes key legal and compliance concerns
- a non-standard clause requires exception approval
- the runtime keeps approval with a human legal owner
- the final output includes a review summary, escalation note, and evidence-oriented state

## Scenario Inputs

Use the role-pack baseline from:
- [../examples/legal_review_role_pack.example.json](../examples/legal_review_role_pack.example.json)

Scenario assumptions:
- contract type: vendor MSA
- issue type: non-standard liability clause plus policy exception
- provider lane: Ollama
- operating mode: indirect
- reporting line: `LEGAL`

## What The AI Role Should Do

Inside the governed lane, the legal role may:
- review the packet
- summarize non-standard clauses
- flag compliance exposure
- prepare escalation notes

Inside the governed lane, the legal role must not:
- sign the contract
- waive a regulatory obligation
- approve the contract exception autonomously

## Suggested Demo Flow

1. Start from the legal pack definition in [LEGAL_REVIEW_ROLE_PACK.md](LEGAL_REVIEW_ROLE_PACK.md).
2. Explain that this is an indirect legal operator, not an autonomous legal approver.
3. Show the scenario output in [../examples/legal_review_scenario.example.json](../examples/legal_review_scenario.example.json).
4. Call out these fields in the example output:
   - `scenario_id`
   - `selected_provider`
   - `role_pack.template_id`
   - `review_result.summary`
   - `review_result.escalation_required`
   - `review_result.wait_human_actions`
   - `evidence.summary`
5. Explain that the role can prepare the exception path but the approval still belongs to a human legal owner.

## Expected Outcome

The governed outcome should show:
- a successful review pass
- an escalation requirement for the exception path
- no autonomous approval of the contract exception
- evidence-oriented output that can be reviewed later

## Matching Example Artifact

See [../examples/legal_review_scenario.example.json](../examples/legal_review_scenario.example.json).

This sanitized example is meant to help evaluators understand the expected shape before building a richer live scenario implementation.

## Why This Scenario Matters

This scenario is one of the first bridges between:
- technical readiness
- pilot-ready role packs
- buyer-facing workflow stories

It shows that SA-NOM is not only proving provider health or startup readiness. It is showing how a governed AI role behaves inside a real organizational workflow.

## Next Steps

- For the pack definition: [LEGAL_REVIEW_ROLE_PACK.md](LEGAL_REVIEW_ROLE_PACK.md)
- For the private demo lane: [OLLAMA_DEMO_ENVIRONMENT.md](OLLAMA_DEMO_ENVIRONMENT.md)
- For the customer walkthrough: [LIVE_CUSTOMER_WALKTHROUGH.md](LIVE_CUSTOMER_WALKTHROUGH.md)
- For the commercial path after a strong scenario fit: [COMMERCIAL_DISCOVERY_CHECKLIST.md](COMMERCIAL_DISCOVERY_CHECKLIST.md)
