# Warehouse Material Shortage Role Pack

Use this guide when you want a pilot-ready warehouse role pack that demonstrates governed material-shortage review, allocation escalation, and human approval boundaries on the private default SA-NOM lane.

## Goal

By the end of this guide you should understand:
- what the public-safe warehouse role pack is designed to do
- which actions stay inside the AI lane and which actions must escalate to humans
- how to use the warehouse pack during evaluation, demos, or pilot discussions
- which example artifacts match the pack

## Included Public-Safe Assets

This role-pack starter currently ships as:
- a library template in `resources/studio/role_private_studio_templates.json`
- a starter example in `resources/studio/role_private_studio_examples.json`
- a sanitized example artifact in [../examples/warehouse_material_shortage_role_pack.example.json](../examples/warehouse_material_shortage_role_pack.example.json)

The current library template id is:
- `warehouse_material_shortage_pack`

The starter example name is:
- `Warehouse Material Shortage Lead`

## What This Pack Is For

This pack is meant to show how SA-NOM can help a warehouse or material-control team with:
- material-shortage review
- allocation exception summaries
- stock-out and line-starvation routing
- inventory-exception escalation
- warehouse note preparation for cross-functional decisions

It is intentionally not meant to:
- issue material to the line autonomously
- adjust inventory balances on its own
- override cycle-count results
- replace human warehouse authority

## Default Operating Shape

The pack is designed around an indirect operating mode:
- `reporting_line = WAREHOUSE`
- `operating_mode = indirect`
- `assigned_user_id = WAREHOUSE_MANAGER_01`
- `executive_owner_id = EXEC_OWNER`

That means the AI lane is explicitly positioned as a governed warehouse operator, not as an autonomous material controller.

## Default Authority Boundaries

Default allowed actions include:
- `review_material_shortage`
- `summarize_stock_risk`
- `prepare_warehouse_report`
- `approve_allocation_exception`

Default forbidden actions include:
- `issue_material_to_line`
- `adjust_inventory_balance`
- `override_cycle_count_result`

Default wait-human actions include:
- `approve_allocation_exception`
- `approve_inventory_override`

This is important: the role pack can help analyze and prepare the shortage-exception path, but a human warehouse owner still owns the approval decision.

## Suggested Demo Or Pilot Story

Use this pack when you want to show a real operational story rather than only infrastructure readiness.

Recommended talk track:
- a material-shortage packet enters review
- the AI role summarizes stock-out risk, allocation exposure, and line impact
- the role prepares an escalation note when it sees a shortage or inventory exception
- the governed runtime keeps issue, allocation, and override decisions with a human warehouse owner
- the result can be reviewed through evidence and escalation-oriented outputs

## How To Use It In Role Private Studio

1. Start with the template library item `warehouse_material_shortage_pack`.
2. Adjust the assigned user id, executive owner id, and seat id for the target environment.
3. Keep material issue, inventory adjustments, and cycle-count overrides outside the autonomous lane.
4. Generate and review the PTAG output.
5. Run the normal studio validation and simulation flow before publication.

## Matching Example Artifact

See [../examples/warehouse_material_shortage_role_pack.example.json](../examples/warehouse_material_shortage_role_pack.example.json) for a sanitized payload that matches the intended pack shape.

You can also compare it with:
- [../examples/new_model_launch_readiness_role_pack.example.json](../examples/new_model_launch_readiness_role_pack.example.json)
- [../examples/guided_smoke_test.example.json](../examples/guided_smoke_test.example.json)

## Good Pilot Fit

This pack is a good early pilot candidate when the customer wants to evaluate:
- governed shortage review support
- stock-risk and allocation escalation
- exception routing instead of autonomous warehouse decisions
- a private local-model path through Ollama

## Not A Good Fit

This pack is not a good first pilot if the customer expects:
- AI to issue material or adjust inventory on its own
- unsupervised warehouse authority
- removal of human review from allocation and stock-control decisions

## What This Opens Next

This warehouse lane is the natural bridge into the next deeper manufacturing layers:
- production line recovery and schedule-exception stories
- QC hold, defect triage, and release-risk stories
- QA deviation, waiver, and shipment-release stories

## Next Steps

- For the live private-model lane: [OLLAMA_DEMO_ENVIRONMENT.md](OLLAMA_DEMO_ENVIRONMENT.md)
- For the evaluator path: [GUIDED_EVALUATION.md](GUIDED_EVALUATION.md)
- For the demo talk track: [LIVE_CUSTOMER_WALKTHROUGH.md](LIVE_CUSTOMER_WALKTHROUGH.md)
- For commercial qualification: [COMMERCIAL_DISCOVERY_CHECKLIST.md](COMMERCIAL_DISCOVERY_CHECKLIST.md)