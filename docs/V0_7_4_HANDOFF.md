# v0.7.4 Handoff

## Purpose

This document defines the handoff for `v0.7.4` as the `Document Center Runtime` milestone after `v0.7.3`.

`v0.7.3` established the canonical case backbone.

`v0.7.4` should be read as the milestone where governed documents become real runtime objects inside the same operating story instead of staying conceptually adjacent to the workflow.

## Completed In v0.7.4

The current `v0.7.4` line now includes:

- a governed document runtime package with document models, document store, and runtime service behavior
- document classes, numbering, metadata handling, revision structure, and active-version logic
- document lifecycle actions for draft, review, approval, publish, next revision, supersede, and archive
- a dedicated `Documents` lane in the dashboard with editor, queue posture, Human Ask document reporting, and lifecycle visibility
- explicit document permissions for read, create, review, publish, and archive, mapped into operator and reviewer surfaces
- document linkage into canonical cases, work inbox summaries, and audit continuity
- runtime retrieval and filtered search for documents by query, status, class, case, and active-only scope

## Explicitly Not The Focus Of v0.7.4

`v0.7.4` should not be read as:

- a full enterprise document-management suite in one milestone
- the complete AI action-runtime phase
- a broad product-family expansion beyond document runtime behavior
- a claim that every document governance workflow is fully domain-specialized already
- a replacement for the next action-runtime and master-data phases in the product-grade plan

The point of the phase is to make governed documents work as runtime objects, not to solve every downstream business-document problem at once.

## Release-Prep Status

As of the current handoff state:

- full test suite passes: `351 passed`
- coverage remains above the repo threshold: `84.69%`
- `docs/releases/RELEASE_NOTES_v0.7.4.md` and `docs/releases/PR_DESCRIPTION_v0.7.4.md` are prepared for the branch's PR/release-prep path
- the document runtime slice is pushed on `v0.7.4-document-runtime`
- the Documents lane now includes retrieval behavior in addition to lifecycle control

## Current Warning State

The remaining local non-release artifact is unchanged:

- `coverage.xml` exists as a local test artifact and should not be treated as release material

This is not a blocker for PR review or release-prep docs.
It is a workspace hygiene reminder.

## Definition Of Success For Merge / Tag

`v0.7.4` is ready to merge and tag when:

- PR scope stays limited to document-runtime work already described in this handoff
- no unresolved required check or merge conflict remains on the branch
- release notes for `v0.7.4` remain aligned with the implementation actually merged
- the document runtime lane, retrieval behavior, permissions, and tests remain in sync
- `coverage.xml` and other local artifacts stay outside the release commit surface

## Suggested Internal Release Sequence

1. Merge the `v0.7.4` branch into `main`.
2. Use `docs/releases/RELEASE_NOTES_v0.7.4.md` as the release body.
3. Use `docs/V0_7_4_HANDOFF.md` as the internal reference for what this release does and does not claim.
4. Keep `coverage.xml` and other local runtime artifacts out of the release scope.
5. Start the next milestone only after the `v0.7.4` line is closed cleanly.

## Next-Phase Guardrails

The strongest follow-up after `v0.7.4` should continue from this stronger document-runtime line.

That means future work should prefer:

- AI action-runtime depth on top of the document and case backbone
- stronger execution contracts, resumability, and follow-up actions
- deeper linkage between governed documents, cases, and executable work

What should be avoided next:

- treating documents as separate from the runtime again
- adding document marketing language faster than lifecycle and retrieval behavior can support
- skipping the action-runtime phase and jumping straight into broader domain sprawl
