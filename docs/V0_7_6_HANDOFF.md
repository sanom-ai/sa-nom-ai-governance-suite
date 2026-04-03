# v0.7.6 Handoff

## Release Thesis

`v0.7.6` is the milestone where SA-NOM becomes organization-aware and searchable in a way that feels closer to real operational software.

The release adds three connected layers:
- canonical master data
- assignment routing with SLA/aging posture
- searchable continuity across governed work and supporting records

## What Landed

- master-data runtime with persisted organization / people / seat / team baseline
- assignment queue derived from overrides, Human Ask, studio, documents, actions, and fallback work signals
- SLA, priority, age, owner, team, and next-action contract on assignment items
- global search index across people, assignments, cases, requests, documents, actions, Human Ask records, studio requests, roles, evidence exports, and sessions
- new `Directory & Search` dashboard lane
- master-data summary and store visibility in dashboard snapshot and runtime health
- direct tests for master-data runtime plus dashboard summary coverage

## Operator Outcome

After `v0.7.6`, the dashboard no longer treats work ownership as implied context.
Operators can now:
- see who owns what
- see which team or seat a work item belongs to
- see which assignments are aged, critical, or waiting on a human
- search continuity across case, document, action, evidence, and session records
- move from a search result or assignment directly into the right governed lane without losing context

## Verification Status

Validated with:
- `python -m compileall -q .`
- `node --check .\sa_nom_governance\dashboard\static\dashboard_app.js`
- `python scripts\dashboard_server.py --check-only`
- `python -m pytest _support\tests`

Latest result:
- `356 passed`
- coverage `84.88%`

## Remaining Notes

- `coverage.xml` is still a local artifact and should stay out of the release surface
- this release intentionally keeps the master-data model lightweight and derived from runtime behavior rather than expanding into every ERP-class entity already
- deeper admin settings, onboarding, migration, and pilot hardening remain scoped to `v0.7.7`

## Recommended Next Release

`v0.7.7` should focus on productization hardening:
- admin settings
- first-run assistant
- diagnostics / doctor / preflight continuity
- backup / restore UX
- migration / upgrade process
