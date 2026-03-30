# Guided New Model Launch-Readiness Scenario

Use this scenario when you want to show a real governed workflow for the public-safe NPI launch-readiness pack, not only infrastructure readiness.

## Goal

By the end of this scenario you should be able to show that SA-NOM can:
- accept a new-model launch-review style workload
- keep the AI role inside a bounded launch-readiness and exception-review scope
- escalate launch and process-change exceptions to a human instead of approving them automatically
- retain a reviewable evidence-oriented output shape

## Recommended Starting Point

Before running this scenario, make sure you already have:
- a passing guided smoke report from `python scripts/guided_smoke_test.py --registration-code DEMO-ORG`
- a ready Ollama lane from `python scripts/ollama_demo_environment.py`
- a passing provider probe from `python scripts/provider_demo_flow.py --provider ollama --probe`
- familiarity with the pack in [NEW_MODEL_LAUNCH_READINESS_ROLE_PACK.md](NEW_MODEL_LAUNCH_READINESS_ROLE_PACK.md)

## Scenario Story

This scenario models a launch-readiness review where:
- a new model approaches the launch gate with open APQP, trial-build, and supplier readiness issues
- the AI role summarizes launch risk, cross-functional gaps, and control-plan exposure
- a launch exception requires human approval
- the runtime keeps launch release and process-change authority with a human manufacturing owner
- the final output includes a review summary, escalation note, and evidence-oriented state

## Scenario Inputs

Use the role-pack baseline from:
- [../examples/new_model_launch_readiness_role_pack.example.json](../examples/new_model_launch_readiness_role_pack.example.json)

Scenario assumptions:
- request type: launch readiness review
- issue type: APQP and trial-build exception blocking launch release
- provider lane: Ollama
- operating mode: indirect
- reporting line: `NPI`

## What The AI Role Should Do

Inside the governed lane, the NPI role may:
- review the launch packet
- summarize APQP and trial-build exceptions
- highlight supplier, tooling, and control-plan exposure
- prepare an escalation note for the manufacturing owner

Inside the governed lane, the NPI role must not:
- release a new model launch
- approve a process change
- waive a customer requirement
- approve the launch exception autonomously

## Suggested Demo Flow

1. Start from the NPI pack definition in [NEW_MODEL_LAUNCH_READINESS_ROLE_PACK.md](NEW_MODEL_LAUNCH_READINESS_ROLE_PACK.md).
2. Explain that this is an indirect manufacturing launch operator, not an autonomous release approver.
3. Show the scenario output in [../examples/new_model_launch_readiness_scenario.example.json](../examples/new_model_launch_readiness_scenario.example.json).
4. Call out these fields in the example output:
   - `scenario_id`
   - `selected_provider`
   - `role_pack.template_id`
   - `review_result.summary`
   - `review_result.escalation_required`
   - `review_result.wait_human_actions`
   - `evidence.summary`
5. Explain that the role can prepare the launch exception path but the release decision still belongs to a human manufacturing owner.

## Expected Outcome

The governed outcome should show:
- a successful review pass
- an escalation requirement for the launch-exception path
- no autonomous launch release or process-change approval
- evidence-oriented output that can be reviewed later

## Matching Example Artifact

See [../examples/new_model_launch_readiness_scenario.example.json](../examples/new_model_launch_readiness_scenario.example.json).

This sanitized example is meant to help evaluators understand the expected shape before building a richer live scenario implementation.

## Why This Scenario Matters

This scenario is the bridge between:
- upstream supplier and material-readiness review
- launch and APQP governance
- downstream warehouse, production, QC, and QA release stories

It shows that SA-NOM is not only proving provider health or startup readiness. It is showing how a governed AI role behaves inside a real manufacturing launch workflow.

## What This Unlocks Next

After this NPI lane, the next high-value expansion is:
- warehouse shortage and material-availability stories
- production line recovery and schedule-exception stories
- QC and QA release-readiness stories

That means this scenario can be used as the midpoint between supplier-risk governance and deeper shop-floor operations.

## Next Steps

- For the pack definition: [NEW_MODEL_LAUNCH_READINESS_ROLE_PACK.md](NEW_MODEL_LAUNCH_READINESS_ROLE_PACK.md)
- For the private demo lane: [OLLAMA_DEMO_ENVIRONMENT.md](OLLAMA_DEMO_ENVIRONMENT.md)
- For the customer walkthrough: [LIVE_CUSTOMER_WALKTHROUGH.md](LIVE_CUSTOMER_WALKTHROUGH.md)
- For the commercial path after a strong scenario fit: [COMMERCIAL_DISCOVERY_CHECKLIST.md](COMMERCIAL_DISCOVERY_CHECKLIST.md)