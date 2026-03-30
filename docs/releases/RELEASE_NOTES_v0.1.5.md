# Release Notes - v0.1.5

## Release Focus

This release moves SA-NOM from demo-ready toward pilot-ready by adding the first public-safe role-pack workflow for legal operations, tightening product terminology around Human Ask, and extending the commercial path from discovery into scoped pilot proposals.

## Highlights

- Added a public-safe legal review role pack for governed review-and-escalation workflows
- Added a guided legal review scenario that connects the legal role pack to a reusable demo and pilot story
- Clarified `Human Ask` as a human-initiated reporting and meeting layer, separate from override and alert paths
- Added a pilot proposal template that connects discovery, ROI framing, and scoped paid-pilot planning
- Added a Thai one-page demo checklist for live customer calls

## Community Baseline In This Release

- legal review starter assets that show how SA-NOM can support governed organizational work without claiming autonomous legal approval
- scenario-aligned example artifacts that make guided evaluation and demo storytelling more concrete
- clearer public language for how humans call AI into reporting and meetings
- stronger Thai-language sales and operator assets for live demo execution
- a more complete bridge from repository evaluation into a pilot-ready conversation

## Commercial Direction

Commercial offerings remain separate from the AGPL community baseline and may include rollout support, enterprise controls, tailored compliance programs, air-gapped delivery, and custom integrations.

See [../COMMERCIAL_DISCOVERY_CHECKLIST.md](../COMMERCIAL_DISCOVERY_CHECKLIST.md), [../ROI_ONE_PAGER.md](../ROI_ONE_PAGER.md), and [../PILOT_PROPOSAL_TEMPLATE.md](../PILOT_PROPOSAL_TEMPLATE.md) for the current discovery-to-pilot path.

## Upgrade Notes

- `docs/LEGAL_REVIEW_ROLE_PACK.md` introduces the first pilot-ready public-safe role pack for legal review and escalation
- `docs/LEGAL_REVIEW_SCENARIO.md` provides the first guided operational scenario built on top of that role pack
- `Human Ask` now reads consistently as a human-initiated reporting and meeting layer across the public docs
- `docs/PILOT_PROPOSAL_TEMPLATE.md` can be used to move a qualified prospect into a scoped paid-pilot discussion
- `docs/DEMO_CHECKLIST_TH.md` gives Thai-language live calls a short operator cheat sheet without gendered or polite sentence endings

## Verification Snapshot

Validated during `v0.1.5` release preparation with:
- `python -m compileall -q .`
- `python -m pytest _support/tests`

The `v0.1.5` milestone also included targeted checks during implementation for:
- `python -m pytest _support/tests/test_role_private_studio.py`
- `python -m pytest _support/tests/test_example_artifacts.py`

## Post-Release Follow-Up

Recommended next steps after `v0.1.5`:
- add a second pilot-ready role pack, such as HR policy or internal audit
- build another guided scenario so pilot conversations are not limited to the legal lane
- prepare a `v0.1.5` GitHub release using these notes

## Contact

- Community/commercial/security contact: `sanomaiarch@gmail.com`
