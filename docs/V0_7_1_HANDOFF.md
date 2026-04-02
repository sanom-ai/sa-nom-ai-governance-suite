# v0.7.1 Handoff

## Purpose

This document defines the handoff for `v0.7.1` as the flagship capability proof hardening milestone after `v0.7.0`.

`v0.7.0` made the runtime cleaner, more portable, and more operationally believable.
`v0.7.1` should be read as the follow-on milestone where SA-NOM's strongest public claims become easier to defend from code, tests, dashboard summaries, and release materials.

## Completed In v0.7.1

The current `v0.7.1` line now includes:

- explicit outbound target families and clearer notification-readiness posture for SIEM, chat-ops, ticketing, and custom webhook lanes
- Human Ask freshness, confidence-band, and governed-reporting posture surfaced more clearly in runtime and dashboard summaries
- stronger Role Private Studio publication, restore, revision, and publisher-readiness visibility
- stronger evidence-pack integrity-contract posture and easier-to-read trusted-registry status
- clearer PT-OSS structural posture with blocker counts, high-risk metric totals, and Thai public-sector lane visibility
- clearer guardrail summaries for blocked, human-required, resumed, and resource-lock-conflict situations
- aligned flagship-facing docs through the feature matrix, product tour, root README, release notes, and this handoff

## Explicitly Not The Focus Of v0.7.1

`v0.7.1` should not be read as:

- a major UI redesign release
- a new model-provider expansion release
- a rewrite of SA-NOM's architecture for its own sake
- a claim that every enterprise deployment concern is solved in one milestone
- a broad compliance-product expansion beyond the current governed-runtime story

The point of the phase is to strengthen the existing flagship proof line, not to create feature sprawl.

## Release-Prep Status

As of the current handoff state:

- current full-suite test posture: `337 passed`
- current coverage posture: `84.08%`
- `FEATURE_MATRIX.md` now describes the eight-claim flagship proof line explicitly
- `PRODUCT_TOUR.md` and the root `README.md` now point readers toward the same flagship proof surface
- `docs/releases/RELEASE_NOTES_v0.7.1.md` and `docs/releases/PR_DESCRIPTION_v0.7.1.md` are prepared for the branch's PR/release-prep path

## Current Warning State

The remaining local non-release artifact is unchanged:

- `coverage.xml` exists as a local test artifact and should not be treated as release material

This is not a blocker for code review or release-prep docs.
It is a workspace hygiene reminder.

## Definition Of Success For Merge / Tag

`v0.7.1` is ready to merge and tag when:

- the branch scope remains within flagship-hardening work already described in this handoff
- no unresolved required check or merge conflict remains on the PR
- the final release notes remain aligned with the code and operator surfaces actually merged
- `coverage.xml` and other local artifacts remain outside the release commit surface
- the flagship language stays strong without overclaiming capabilities that are still only partially surfaced

## Suggested Internal Release Sequence

1. Merge the `v0.7.1` branch into `main`.
2. Use `docs/releases/RELEASE_NOTES_v0.7.1.md` as the release body.
3. Use `docs/V0_7_1_HANDOFF.md` as the internal reference for what this release does and does not claim.
4. Keep `coverage.xml` and any other local runtime artifacts out of the release scope.
5. Start the next milestone only after the `v0.7.1` line is closed cleanly.

## Next-Phase Guardrails

The strongest follow-up after `v0.7.1` should continue from this cleaner flagship-proof line.

That means future work should prefer:

- deeper end-to-end workflow proof on top of the existing flagship capabilities
- operator-surface improvements only where they increase evidence-backed clarity
- more release-discipline and implementation-proof continuity before broad new feature families

What should be avoided next:

- reopening wording drift between docs and implementation
- hiding operator-critical posture inside raw internal metadata again
- expanding marketing language faster than the test-backed runtime surface
