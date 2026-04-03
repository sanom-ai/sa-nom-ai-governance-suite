## Summary

This PR delivers `v0.7.6` as the master-data, search, and assignment release.

It makes SA-NOM treat ownership, routing, and searchability as first-class governed runtime surfaces instead of leaving them as implied context around cases, documents, and AI actions.

Key scope in this PR:
- a canonical master-data runtime package with persisted organization, people, seat, and team baselines
- an assignment engine that routes governed work to real owners with priority, SLA posture, age, and next-step guidance
- a global search layer across people, assignments, cases, requests, documents, actions, Human Ask records, roles, evidence, and sessions
- a dedicated `Directory & Search` dashboard lane for ownership, assignment, and searchable continuity
- runtime-health visibility for the master-data store and dashboard snapshot exposure for the new surfaces

## Why This Change

The goal of `v0.7.6` is to make governed work feel like real organizational work instead of disconnected runtime records.

Before this change, SA-NOM already had stronger work surfaces, canonical cases, governed documents, and governed AI actions.
But the product still needed one more product-grade move:
- governed work needed visible owners and teams
- search needed to cross module boundaries instead of staying implicit inside each lane
- operators needed a way to move from ownership and search directly back into the right governed lane

This PR closes that gap by turning organization baseline, assignment routing, and searchable continuity into a live runtime surface.

## Validation

- [x] `python -m compileall -q .`
- [x] `node --check .\sa_nom_governance\dashboard\static\dashboard_app.js`
- [x] `python scripts\dashboard_server.py --check-only`
- [x] `python -m pytest _support\tests`
- [x] Current full-suite status: `356 passed`
- [x] Current coverage posture: `84.88%`
- [x] Docs updated when behavior changed

## Notes

- this PR is the master-data, search, and assignment milestone for `v0.7.6`, not the broader productization-hardening milestone planned next
- the strongest outcome is that governed work can now be routed to real owners with SLA/aging visibility and searched across the same case and evidence story
- `coverage.xml` remains a local artifact and is not part of the PR surface
