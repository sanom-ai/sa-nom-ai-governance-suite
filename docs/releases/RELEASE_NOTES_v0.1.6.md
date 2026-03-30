# v0.1.6 - Enterprise workflow expansion and Private Rule Positions

## Release Focus

`v0.1.6` turns SA-NOM into a much stronger pilot-ready enterprise workflow platform by expanding the public-safe role-pack library across manufacturing, finance, accounting, audit, regulator response, and organization-defined private positions.

This release is where the product starts to read less like a small set of examples and more like a governed operating model that can stretch across real enterprise lanes.

## Highlights

- expanded the public-safe role-pack library across procurement, finance, accounting, treasury, manufacturing, quality, delivery, audit, and regulator-response lanes
- added guided scenarios across the new manufacturing and oversight lanes so role packs now connect to reusable pilot and demo stories
- clarified `Private Rule Studio` as a core platform capability rather than a separately sold unlock
- introduced `Private Rule Position` as the term for organization-defined hats that can be created from uploaded JD inputs or starter materials
- strengthened the public story that starter JD/rules/hats accelerate adoption while commercial work focuses on tailoring and rollout support

## What Landed In This Milestone

### Enterprise workflow expansion

Public-safe role packs were added for:
- purchasing and supplier risk
- finance budget and cost variance
- accounting close-readiness and exception handling
- banking and treasury control
- new model / NPI launch readiness
- warehouse material shortage
- production line exception
- quality release and audit readiness
- delivery readiness
- external audit response
- regulator response

### Guided operational scenarios

Guided scenarios now cover:
- legal review
- HR policy review
- purchasing supplier-risk review
- finance budget-variance review
- new model launch readiness
- production line exception
- quality and audit readiness
- delivery readiness
- external audit response
- regulator response

### Core product-definition clarification

The docs now state clearly that:
- `Private Rule Studio` is a core capability
- organizations can create flexible `Private Rule Positions` of their own
- starter JD/rules/hats are accelerator support, not a paywall
- commercial scope should focus on tailoring, workshops, starter-library support, and rollout help rather than artificial limits on rule creation

## Community Baseline In This Release

The public baseline now includes:
- a much broader enterprise function map covering manufacturing, finance, accounting, audit, IT, and regulator-facing workflows
- a larger public-safe role-pack catalog that supports real pilot stories instead of only abstract platform descriptions
- a matching guided-scenario catalog that helps evaluators show how governed runtime behavior works inside business workflows
- clearer product language for how organizations define their own custom hats through `Private Rule Studio` and `Private Rule Positions`
- continued support for the private-first Ollama demo lane with governed reporting, escalation, and evidence paths

## Commercial Direction

Commercial offerings remain separate from the AGPL community baseline and may include rollout support, enterprise controls, tailored compliance programs, air-gapped delivery, industry-specific starter libraries, and custom integrations.

`Private Rule Studio` itself should be read as part of the core platform story. Commercial work is centered on organization-specific design, starter-library tailoring, workshops, and rollout execution.

Related documents:
- [../FEATURE_MATRIX.md](../FEATURE_MATRIX.md)
- [../COMMERCIAL_LICENSE.md](../COMMERCIAL_LICENSE.md)
- [../COMMERCIAL_DISCOVERY_CHECKLIST.md](../COMMERCIAL_DISCOVERY_CHECKLIST.md)
- [../PRIVATE_RULE_POSITION.md](../PRIVATE_RULE_POSITION.md)

## Upgrade Notes

- `v0.1.6` is documentation and product-surface heavy, but it materially expands the public role-pack and scenario catalog
- the repository now carries a much broader enterprise workflow story across manufacturing, audit, and regulator lanes
- `Private Rule Position` is now the public term for flexible organization-defined hats created through `Private Rule Studio`
- no runtime contract was removed, but evaluators and commercial readers should now see a clearer open-core boundary around rule creation versus tailored implementation support

## Verification Snapshot

Validated during `v0.1.6` release preparation with:
- `python -m pytest _support/tests`

The milestone also included repeated targeted checks for:
- `python -m pytest _support/tests/test_role_private_studio.py`
- `python -m pytest _support/tests/test_example_artifacts.py`

## Post-Release Follow-Up

Recommended next steps after `v0.1.6`:
- decide whether to publish `v0.1.6` immediately or extend the milestone with another lane before release
- continue sector-specific expansion using the same role-pack plus scenario pattern
- consider whether the next milestone should emphasize deeper runtime behavior or more domain libraries

## Contact

- Community/commercial/security contact: `sanomaiarch@gmail.com`
