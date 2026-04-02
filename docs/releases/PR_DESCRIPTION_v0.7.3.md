## Summary

This PR delivers `v0.7.3` as the canonical case backbone release.

It makes SA-NOM treat one governed business issue as one readable operating record instead of leaving operators to reconstruct the story from separate runtime lanes.

Key scope in this PR:
- `case_id` across requests, overrides, Human Ask, studio, and audit-linked records
- a dedicated `Cases` dashboard lane with timeline and continuity cues
- linked work-item summaries for approvals, records, and proof surfaces
- proof-aware case posture and follow-up guidance
- case-scoped lane continuity across Requests, Overrides, Conflicts, Audit, Studio, and Human Ask
- continuous case actions so next-move, work-item, and timeline jumps keep the same issue context

## Why This Change

The goal of `v0.7.3` is to make SA-NOM feel more like one governed operating system and less like a set of adjacent runtime views.

Before this change, the runtime already captured the right kinds of work, but operators still had to connect the issue narrative themselves:
- requests, overrides, Human Ask records, and audit events were all present
- cross-lane focus existed, but not yet as one canonical case story
- proof and next-step signals existed, but they were not fully anchored to one issue object

This PR closes that gap by introducing a stronger case model and carrying it through the dashboard experience.

## Validation

- [x] `python -m pytest _support\tests`
- [x] `python -m pytest --no-cov _support\tests\test_dashboard_operator_surface.py`
- [x] `node --check .\sa_nom_governance\dashboard\static\dashboard_app.js`
- [x] `python scripts\dashboard_server.py --check-only`
- [x] Current full-suite status: `341 passed`
- [x] Current coverage posture: `84.33%`
- [x] Docs updated when behavior changed

## Notes

- this PR is the case-backbone milestone for `v0.7.3`, not the document-runtime milestone planned for `v0.7.4`
- the strongest outcome is that one business issue can now be followed more cleanly from one place
- `coverage.xml` remains a local artifact and is not part of the PR surface
