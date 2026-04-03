# v0.7.5 Handoff

## Purpose

This document defines the handoff for `v0.7.5` as the `AI Action Runtime` milestone after `v0.7.4`.

`v0.7.4` established the governed document runtime.

`v0.7.5` should be read as the milestone where AI execution becomes a real governed runtime lane inside the same operating story instead of staying implicit behind prompts and side effects.

## Completed In v0.7.5

The current `v0.7.5` line now includes:

- a governed AI action runtime package with action models, registry, action store, and runtime service behavior
- explicit action contracts with authority boundary, side-effect posture, next action, and next view metadata
- runtime lifecycle handling for `planned`, `running`, `waiting_human`, `completed`, and `failed_closed`
- governed action handlers for `summarize_case`, `draft_document`, and `request_human`
- a dedicated `AI Actions` lane in the dashboard with launch controls, rerun flow, runtime traces, artifacts, and continuity guidance
- AI action linkage into canonical cases, case timelines, linked work items, documents, Human Ask sessions, and audit proof
- action-runtime visibility in dashboard snapshot, work surface summaries, and runtime health

## Explicitly Not The Focus Of v0.7.5

`v0.7.5` should not be read as:

- the full master-data and enterprise assignment milestone
- a claim that every possible AI workflow is already actionized
- the complete productization and onboarding phase
- a replacement for the next search, assignment, and operating-data work in the product-grade plan
- a promise that every downstream business domain already has a specialized action pack

The point of the phase is to make governed AI execution real inside the runtime, not to solve every downstream operating-data concern at once.

## Release-Prep Status

As of the current handoff state:

- full test suite passes: `354 passed`
- coverage remains above the repo threshold: `84.58%`
- `docs/releases/RELEASE_NOTES_v0.7.5.md` and `docs/releases/PR_DESCRIPTION_v0.7.5.md` are prepared for the branch's PR/release-prep path
- the AI action runtime slice is pushed on `v0.7.5-ai-action-runtime`
- the dashboard now includes an `AI Actions` lane tied into case continuity and operator flow

## Current Warning State

The remaining local non-release artifact is unchanged:

- `coverage.xml` exists as a local test artifact and should not be treated as release material

This is not a blocker for PR review or release-prep docs.
It is a workspace hygiene reminder.

## Definition Of Success For Merge / Tag

`v0.7.5` is ready to merge and tag when:

- PR scope stays limited to AI action-runtime work already described in this handoff
- no unresolved required check or merge conflict remains on the branch
- release notes for `v0.7.5` remain aligned with the implementation actually merged
- action contracts, dashboard action lane, and canonical case continuity remain in sync
- `coverage.xml` and other local artifacts stay outside the release commit surface

## Suggested Internal Release Sequence

1. Merge the `v0.7.5` branch into `main`.
2. Use `docs/releases/RELEASE_NOTES_v0.7.5.md` as the release body.
3. Use `docs/V0_7_5_HANDOFF.md` as the internal reference for what this release does and does not claim.
4. Keep `coverage.xml` and other local runtime artifacts out of the release scope.
5. Start the next milestone only after the `v0.7.5` line is closed cleanly.

## Next-Phase Guardrails

The strongest follow-up after `v0.7.5` should continue from this stronger AI action-runtime line.

That means future work should prefer:

- canonical master data and ownership surfaces
- queue assignment, reminders, fallback-owner, and escalation routing depth
- stronger search and retrieval across cases, documents, work items, and evidence
- turning the runtime into an even more complete operating surface where one human can steer many AI workers cleanly

What should be avoided next:

- hiding AI execution behind implicit side effects again
- skipping the operating-data and assignment phase and jumping straight into domain sprawl
- adding action marketing language faster than lifecycle, continuity, and operator visibility can support
