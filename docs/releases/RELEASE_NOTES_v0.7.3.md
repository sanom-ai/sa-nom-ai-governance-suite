# Release Notes - v0.7.3

## Release Focus

`v0.7.3` is the canonical case backbone release after `v0.7.2`.

This release is where SA-NOM starts treating one governed business issue as one readable operating record instead of forcing operators to reconstruct the story from separate lanes by hand.

The central direction of the release is:

`Canonical Case Backbone`

That means `v0.7.3` focuses on stitching together the work that already exists across the runtime:

- requests
- human overrides
- Human Ask records
- Role Private Studio requests
- audit and proof events

The result is a stronger command-surface model where one issue can be followed from one place with clearer continuity, next moves, and proof posture.

## Completed Scope

### Case Id Across Core Workflow Objects

- surfaced `case_id` across request, override, Human Ask, studio, and audit-linked dashboard records
- added canonical case references so core workflow objects point back to the same governed issue
- made case context available to cross-lane actions instead of leaving each lane isolated

### Canonical Case Lane And Timeline

- added a dedicated `Cases` lane to the dashboard as the canonical operating view for linked governed issues
- introduced case cards with timeline history, linked references, current posture, and continuity cues
- made the case lane answer the operator question: "what is happening with this issue across the system?"

### Linked Work Items, Approvals, And Escalation Context

- added a case work-item model for linked requests, overrides, Human Ask records, studio drafts, and audit events
- surfaced pending-human, blocked, active, and attention-required posture at the case level
- connected approval pressure and human-boundary states back into the case view so the operator follows the issue instead of guessing from queue fragments

### Proof-Aware Continuity

- added proof posture, latest proof event, workflow-proof totals, and follow-up actions into case continuity
- made case summaries explain whether proof is attached, partial, or still starting
- strengthened the connection between the working lane and the evidence lane so closure decisions are easier to justify

### Case-Scoped Lane Continuity

- added case spotlight and case-scoped lane filtering across Requests, Overrides, Conflicts, Audit, Human Ask, and Studio
- carried `case_id` through lane jumps so the operator stays inside the same business issue while moving between surfaces
- added "show full lane" recovery so operators can step back out of a scoped case view without losing orientation

### Continuous Case Detail Actions

- made next-move, work-item, and timeline actions preserve case continuity instead of dropping context on navigation
- turned case timeline entries into actionable lane jumps tied to the same case
- tightened the sense that SA-NOM is handling one governed issue across many lanes rather than showing unrelated records side by side

## Why This Release Matters

`v0.7.3` matters because product-grade governed automation needs a readable issue model, not just strong individual lanes.

Before this release, SA-NOM already had meaningful work surfaces for requests, overrides, Human Ask, audit, and studio activity.
But operators still had to mentally stitch the business issue together across those surfaces:
- the same issue could appear in several lanes without one canonical record
- continuity existed, but it still depended too much on operator memory
- proof and next-move cues were available, but they were not yet anchored to one case object
- jumping between lanes could keep focus on a row, but not always on the full issue story

After `v0.7.3`, the product is more coherent:
- one governed issue can be followed from a dedicated case lane
- the operator can move between lanes while preserving issue context
- proof posture and follow-up guidance are attached to the case itself
- SA-NOM looks more like one operating system for governed work and less like a collection of adjacent runtime views

## Verification

Validated during the current `v0.7.3` case-backbone line with:

- `python -m pytest _support\tests`
- `python -m pytest --no-cov _support\tests\test_dashboard_operator_surface.py`
- `node --check .\sa_nom_governance\dashboard\static\dashboard_app.js`
- `python scripts\dashboard_server.py --check-only`
- current full-suite status: `341 passed`
- current coverage posture: `84.33%`

## Next Phase

After `v0.7.3`, the strongest continuation is `v0.7.4`.

That next phase should make the case backbone even more real by attaching governed document runtime behavior to the same issue model:
- document lifecycle and document classes
- publish and supersede flow
- document-linked evidence and review posture
- document continuity inside the same case story

## Notes

- `v0.7.3` should be read as the case-backbone milestone, not as a document-runtime milestone
- the goal of this release is not feature sprawl; it is issue continuity across the governed runtime
- `coverage.xml` remains a local artifact and is not part of the release surface
