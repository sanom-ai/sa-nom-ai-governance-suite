# Issue Drafts - v0.7.0

Use these issue drafts to deliver the `v0.7.0` autonomous governed runtime foundation phase.

## 1. Remove Repository-Root Runtime Assumptions

**Goal**
Make SA-NOM runtime startup and resource loading portable enough to behave predictably outside the source-tree happy path.

**Scope ideas**
- route Global Harmony and other runtime resources through explicit configuration instead of raw current-working-directory paths
- review packaging and install posture for static resources and runtime catalogs
- make resource lookup behavior testable in non-repo-root execution paths

**Success signal**
Critical runtime features still initialize correctly when execution context changes, and the platform no longer depends on incidental repository structure.

## 2. Surface Invalid Governance Materials Instead Of Hiding Them

**Goal**
Make broken role, hierarchy, or governance artifacts visible to operators and auditors rather than silently skipping them.

**Scope ideas**
- expose invalid-role and invalid-hierarchy conditions through health or operator-facing summaries
- preserve safe runtime behavior while clearly showing degraded governance state
- add tests for malformed or untrusted role materials reaching operator-visible surfaces

**Success signal**
Operators can tell the difference between a healthy runtime and a runtime that is silently missing governed materials.

## 3. Strengthen Autonomous Governed Execution Paths

**Goal**
Let AI advance more bounded work automatically without weakening human approval, escalation, or audit controls.

**Scope ideas**
- deepen the runtime action path behind `WHEN ... THEN ...`
- tighten approval-gated automation versus autonomy-ready automation
- make automated execution outcomes more visible in runtime metadata and evidence

**Success signal**
SA-NOM looks more like a governed autonomous runtime and less like a collection of disconnected decision helpers.

## 4. Make Foundational Defaults Explicit And Deterministic

**Goal**
Reduce hidden behavior shifts caused by file ordering, implicit discovery, or accidental fallback choices.

**Scope ideas**
- define explicit default alignment/runtime selections
- review startup assumptions that currently depend on incidental ordering
- add tests that lock deterministic default behavior into the runtime contract

**Success signal**
Core runtime defaults remain stable, explainable, and hard to change accidentally.

## 5. Add Performance And Startup Discipline Checks

**Goal**
Keep runtime growth efficient while the automation depth increases.

**Scope ideas**
- identify avoidable repeated parsing, scanning, or startup work in hot paths
- add lightweight verification for startup/runtime budgets where practical
- keep performance work tied to real operational flow rather than synthetic optimization theater

**Success signal**
`v0.7.0` improves automation depth and runtime seriousness without quietly making the platform heavier or slower.

## 6. Close v0.7.0 As A Foundation-Strengthening Release

**Goal**
Finish the phase with a clear story: cleaner structure, stronger autonomy, better visibility, and more trustworthy runtime behavior.

**Scope ideas**
- align roadmap, implementation slices, and release framing
- make the release read as disciplined platform strengthening rather than feature sprawl
- connect the milestone clearly to future enterprise runtime and orchestration work

**Success signal**
`v0.7.0` reads as the release where SA-NOM became cleaner, more automatic, and more operationally believable at the same time.
