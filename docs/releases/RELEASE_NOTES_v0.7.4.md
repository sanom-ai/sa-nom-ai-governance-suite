# Release Notes - v0.7.4

## Release Focus

`v0.7.4` is the governed document runtime release after `v0.7.3`.

This release is where SA-NOM starts treating documents as live governed operating objects inside the runtime instead of leaving them as static files adjacent to the workflow.

The central direction of the release is:

`Document Center Runtime`

That means `v0.7.4` focuses on turning the document line into a true runtime lane with:

- governed document classes
- numbering and metadata discipline
- draft, review, approval, publish, supersede, and archive flow
- active-version logic
- case linkage
- Human Ask document reporting
- work-inbox and dashboard continuity
- runtime retrieval and filtered document search

The result is a stronger operating model where documents are no longer side artifacts. They become first-class governed records that can be worked, reviewed, found, and audited from the same runtime story.

## Completed Scope

### Governed Document Runtime Foundation

- added a governed document runtime package with document models, store, and service behavior
- introduced governed document classes, document numbering, metadata handling, and revision structure
- added create, update, review, approve, publish, archive, and next-revision behavior as runtime actions
- established active-version logic so a published revision stays active until a newer approved revision is published

### Document Lane In The Dashboard

- added a dedicated `Documents` lane to the dashboard
- surfaced document counts, lifecycle posture, class catalog, and Human Ask document reporting
- added document editor, review queue, publish queue, and document cards as part of the operator surface
- made document actions behave like governed workflow moves instead of standalone file edits

### Case And Work Continuity

- linked governed documents back into canonical cases
- stitched document lifecycle audit events into case continuity and audit proof
- added document work queues into the unified work inbox
- made document actions preserve case context and next-step continuity in the dashboard

### Runtime Permissions And Controlled Release

- added explicit document permissions for read, create, review, publish, and archive
- mapped those permissions into default and privileged operator profiles
- enforced document actions through the same governed runtime access-control path already used elsewhere in SA-NOM

### Runtime Retrieval And Filtered Search

- added filtered document retrieval through the document service and dashboard API
- added runtime document search by query, status, class, case, and active-only posture
- made the Documents lane behave more like a real operator work surface where the user can narrow and retrieve governed documents intentionally
- kept Human Ask document reporting aligned with the filtered runtime scope

## Why This Release Matters

`v0.7.4` matters because product-grade governed automation cannot treat documents as passive attachments.

Before this release, SA-NOM already had strong governance, case continuity, role controls, and evidence posture.
But the document line still needed to become a real operating lane:
- document governance existed as product direction and supporting docs
- the runtime could govern work, but documents were not yet first-class lifecycle objects in the same way requests or overrides were
- operators could follow cases, but document revision, publication, and retrieval needed to become part of the same command surface

After `v0.7.4`, the product is more coherent:
- documents now move through a governed lifecycle inside the runtime
- document state is visible from the same dashboard language as the rest of the system
- document publication and archival now sit inside permissions, audit, and case continuity
- document search and retrieval now behave like runtime work, not like manual file hunting

This is an important step toward a product-grade system where one human can govern an organization through one dashboard while AI and workflow lanes carry most of the operational work.

## Verification

Validated during the current `v0.7.4` document-runtime line with:

- `python -m pytest _support\tests`
- `python -m pytest --no-cov _support\tests\test_document_runtime.py`
- `python -m pytest --no-cov _support\tests\test_dashboard_operator_surface.py`
- `node --check .\sa_nom_governance\dashboard\static\dashboard_app.js`
- `python scripts\dashboard_server.py --check-only`
- current full-suite status: `351 passed`
- current coverage posture: `84.69%`

## Next Phase

After `v0.7.4`, the strongest continuation is `v0.7.5`.

That next phase should move from document runtime objects toward stronger governed execution around them:
- AI action registry and execution contracts
- action-level side-effect discipline
- resumable execution and richer follow-up actions
- deeper linkage between governed documents, cases, and executable AI work

## Notes

- `v0.7.4` should be read as the document-runtime milestone, not as the full AI action-runtime milestone
- the goal of this release is to make governed documents work like runtime objects, not to claim that every document-management concern is solved in one release
- `coverage.xml` remains a local artifact and is not part of the release surface
