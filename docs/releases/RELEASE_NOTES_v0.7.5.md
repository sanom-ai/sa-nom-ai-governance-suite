# Release Notes - v0.7.5

## Release Focus

`v0.7.5` is the governed AI action-runtime release after `v0.7.4`.

This release is where SA-NOM stops treating AI execution as implied behavior around the runtime and starts treating it as an explicit governed action lane with contracts, lifecycle, artifacts, and case continuity.

The central direction of the release is:

`AI Action Runtime`

That means `v0.7.5` focuses on turning AI execution into a true governed runtime lane with:

- canonical AI action models, registry, store, and service behavior
- explicit action contracts for authority boundary and side-effect posture
- execution lifecycle states such as planned, running, waiting_human, completed, and failed_closed
- built-in action handlers for `summarize_case`, `draft_document`, and `request_human`
- case, document, Human Ask, and audit continuity stitched into one runtime story
- an `AI Actions` dashboard lane with launch, rerun, artifact visibility, and next-step guidance
- operator-facing action summaries in work inbox, case continuity, and runtime health

The result is a stronger operating model where AI work is no longer hidden behind generic prompts or disconnected side effects. It becomes governed execution that can be launched, followed, reviewed, and explained from the same runtime surface.

## Completed Scope

### Governed AI Action Runtime Foundation

- added a governed AI action runtime package with action models, store, and service behavior
- introduced a canonical action registry with labels, primary views, authority boundaries, and side-effect policies
- added runtime lifecycle handling for `planned`, `running`, `waiting_human`, `completed`, and `failed_closed`
- made AI actions produce explicit runtime outputs, artifacts, next actions, and next views instead of implicit side effects

### Executable AI Action Contracts

- implemented governed action handlers for `summarize_case`, `draft_document`, and `request_human`
- made `summarize_case` produce proof-aware case summaries without side effects
- made `draft_document` create governed document drafts inside the document runtime with case linkage preserved
- made `request_human` open governed Human Ask records while preserving canonical case continuity

### Dashboard Action Lane And Work Continuity

- added a dedicated `AI Actions` lane to the dashboard
- surfaced action registry entries, action cards, artifact cards, runtime traces, and rerun controls
- made action results flow back into `Cases`, `Documents`, `Human Ask`, and `Audit` instead of leaving the operator to reconnect them manually
- added action-aware work surface cues, next-step guidance, and related views so execution feels like live runtime work instead of a detached catalog

### Canonical Case And Artifact Linkage

- stitched AI actions into canonical cases through `case_id`, work-item linkage, and timeline events
- made action-created documents refresh into the dashboard document lane as live governed artifacts
- preserved `origin_action_id`, `case_id`, and `case_reference` through Human Ask handoff so human review stays inside the same canonical issue
- surfaced action runtime posture through case continuity, linked work items, and runtime health

### Controlled Access And Runtime Visibility

- added explicit action runtime permissions for read, create, and execute
- mapped AI action runtime access into the same governed access-control surface as the rest of the product
- exposed action runtime summary and store posture through dashboard snapshot and health reporting
- kept the action line aligned with audit recording so execution remains explainable and reviewable

## Why This Release Matters

`v0.7.5` matters because product-grade governed automation cannot stop at work surfaces, case continuity, and document runtime objects.

Before this release, SA-NOM already had:
- stronger work surface continuity through `v0.7.2`
- canonical case continuity through `v0.7.3`
- governed document runtime behavior through `v0.7.4`

But one more move was required for the core thesis to become more real:
- AI needed to act through explicit runtime contracts instead of implied background logic
- AI execution needed to stay inside the same case, document, human-review, and audit story
- operators needed to see not only what exists in the system, but what AI is doing inside the system

After `v0.7.5`, the product is more coherent:
- AI work is launched through governed actions with visible lifecycle states
- AI-generated documents and Human Ask handoffs remain inside the same canonical case
- operators can follow AI execution from the `AI Actions` lane instead of guessing where the side effects went
- action runtime becomes part of the same dashboard language as requests, cases, documents, and evidence

This is an important step toward the SA-NOM thesis that one human can govern an organization through one dashboard because AI carries most of the operational work inside explicit authority, evidence, and escalation boundaries.

## Verification

Validated during the current `v0.7.5` AI action-runtime line with:

- `python -m compileall -q sa_nom_governance _support	ests`
- `python -m pytest _support	ests`
- `python -m pytest --no-cov _support	ests	est_action_runtime.py _support	ests	est_dashboard_operator_surface.py`
- `node --check .\sa_nom_governance\dashboard\static\dashboard_app.js`
- `python scripts\dashboard_server.py --check-only`
- current full-suite status: `354 passed`
- current coverage posture: `84.58%`

## Next Phase

After `v0.7.5`, the strongest continuation is `v0.7.6`.

That next phase should move from governed AI action runtime toward stronger operating-data realism:
- canonical master data and ownership surfaces
- search and retrieval across work, cases, documents, and evidence
- assignment, routing, reminder, and fallback-owner logic
- stronger queue behavior that makes the runtime feel even closer to a real operating system for organizational work

## Notes

- `v0.7.5` should be read as the AI action-runtime milestone, not as the full master-data or enterprise assignment milestone
- the goal of this release is to make AI execution behave like governed runtime work, not to claim that every downstream AI workflow is fully specialized already
- `coverage.xml` remains a local artifact and is not part of the release surface
