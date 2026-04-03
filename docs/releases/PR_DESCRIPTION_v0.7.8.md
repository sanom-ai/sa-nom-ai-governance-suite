## Summary

This PR delivers `v0.7.8` as the private-first tablet command-surface release.

It strengthens SA-NOM for organizational tablet use without changing the product thesis:
- Home stays simple and human-directed
- AI remains the visible primary workforce
- deeper governance tooling stays protected behind Control Room
- private session continuity becomes part of the product surface instead of an invisible runtime detail

Key scope in this PR:
- tablet-first command shell and touch-target improvements
- persona-aware Home focus guidance for founder, admin, operator, and executive sessions
- touch-first work lanes and lane rail for `Work Inbox`, `Cases`, `Documents`, `AI Actions`, and `Directory & Search`
- private session continuity cues, renewal actions, and soft recovery for safe dashboard refresh paths
- role-based lane emphasis so each tablet persona sees the most important next lane first

## Why This Change

The goal of `v0.7.8` is to make SA-NOM feel credible on a private organizational tablet, not only on a desktop development screen.

Before this change, the command surface had already become simpler and more product-like in `v0.7.7`.
But it still needed another move:
- touch-first work needed stronger lane cards and shell behavior
- session continuity needed to be visible instead of hidden behind runtime knowledge
- persona routing needed to feel intentional, not generic
- the private-first story needed to survive real tablet behavior such as idle cooling and reconnect pressure

This PR closes that gap while keeping the founder doctrine intact.

## Validation

- [x] `python -m compileall -q sa_nom_governance _support	ests`
- [x] `node --check sa_nom_governance\dashboard\static\dashboard_app.js`
- [x] `python scripts\dashboard_server.py --check-only`
- [x] `python -m pytest --no-cov _support	ests	est_dashboard_operator_surface.py -q`
- [x] `python -m pytest _support	ests`
- [x] Current full-suite status: `362 passed`
- [x] Current coverage posture: `85.04%`
- [x] Docs updated when behavior changed

## Notes

- this PR is the private-first tablet productization milestone for `v0.7.8`
- the command surface remains simple while session continuity and persona routing become clearer on tablet
- `coverage.xml` remains a local artifact and is not part of the PR surface
