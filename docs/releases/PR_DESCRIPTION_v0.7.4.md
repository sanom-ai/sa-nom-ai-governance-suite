## Summary

This PR delivers `v0.7.4` as the governed document runtime release.

It makes SA-NOM treat documents as first-class governed operating objects inside the runtime instead of leaving them as static files adjacent to the workflow.

Key scope in this PR:
- governed document models, store, service, classes, numbering, metadata, and revision behavior
- document lifecycle actions for draft, review, approval, publish, supersede, and archive
- a dedicated `Documents` dashboard lane with editor, work queues, Human Ask document reporting, and lifecycle visibility
- document linkage into canonical cases, work inbox summaries, and audit continuity
- explicit document permissions across read, create, review, publish, and archive lanes
- filtered runtime retrieval for documents by query, status, class, case, and active-only scope

## Why This Change

The goal of `v0.7.4` is to make the document line feel like real governed runtime work instead of a sidecar document concept.

Before this change, SA-NOM already had stronger issue continuity through cases, requests, overrides, Human Ask, and audit proof.
But the product still needed one more product-grade move:
- documents needed to become lifecycle-controlled runtime objects
- document review and publication needed to live inside the same authority and audit system
- operators needed a way to retrieve the right governed document from the runtime without falling back to manual file-hunting

This PR closes that gap by turning the document line into a live operating lane that is searchable, reviewable, publishable, and linked back into case and evidence continuity.

## Validation

- [x] `python -m pytest _support\tests`
- [x] `python -m pytest --no-cov _support\tests\test_document_runtime.py`
- [x] `python -m pytest --no-cov _support\tests\test_dashboard_operator_surface.py`
- [x] `node --check .\sa_nom_governance\dashboard\static\dashboard_app.js`
- [x] `python scripts\dashboard_server.py --check-only`
- [x] Current full-suite status: `351 passed`
- [x] Current coverage posture: `84.69%`
- [x] Docs updated when behavior changed

## Notes

- this PR is the document-runtime milestone for `v0.7.4`, not the broader AI action-runtime milestone planned for the next phase
- the strongest outcome is that documents now behave like governed runtime objects with lifecycle, retrieval, case linkage, and proof continuity
- `coverage.xml` remains a local artifact and is not part of the PR surface
