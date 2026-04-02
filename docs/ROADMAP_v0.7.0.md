# Roadmap - v0.7.0

This roadmap opens the `v0.7.0` phase after the `v0.6.x` Global Harmony baseline line.

## Theme

From governed runtime features toward a cleaner autonomous governed runtime foundation.

## Milestone Goal

By the end of `v0.7.0`, SA-NOM should look less like a fast-growing repository with strong governed features and more like a disciplined platform foundation that organizations can evaluate for serious long-running use.

This phase should establish one coherent direction:

`Autonomous Governed Runtime Foundation`

The goal is not to remove humans from the system.
The goal is to let AI carry more operational load safely by improving structure, runtime cleanliness, observability, portability, deterministic defaults, and automation-first execution paths.

## Core Position

`v0.7.0` should not try to become a broad expansion release with ten unrelated feature tracks.
It should make the current runtime foundation cleaner, more automatic, easier to trust, and more believable for real organizational evaluation.

That means the phase should answer questions such as:
- how can SA-NOM automate more governed work without blurring approval and escalation boundaries
- how can the runtime become more portable and less dependent on repository-root assumptions
- how should failure states, invalid role surfaces, and degraded governance conditions become visible to operators instead of disappearing silently
- how can performance and startup discipline improve while the runtime grows more capable
- what foundation should be in place before larger post-`v0.7.0` automation or enterprise add-on ideas continue

## Primary Structure

### 1. Runtime Portability And Packaging Discipline

Target areas:
- remove core runtime assumptions that depend on the current working directory or source-tree layout
- align resource loading, startup configuration, and packaged execution paths
- make runtime dependencies and static resources easier to reason about in private deployment and install-based execution

Expected outcomes:
- SA-NOM is easier to run from a cleaner installed or packaged posture
- runtime behavior depends more on explicit configuration than on repository location
- foundational deployment trust improves before more automation is added

### 2. Automation-First Governed Execution

Target areas:
- increase the amount of governed work AI can move forward automatically inside bounded policy paths
- keep `WHEN ... THEN ...` and runtime effect execution aligned with approval, escalation, and audit evidence
- make autonomous flow advancement feel intentional rather than scattered across special cases

Expected outcomes:
- AI can carry more routine operational work without weakening governance boundaries
- the runtime looks more like an active governed operator and less like a passive policy checker
- later enterprise orchestration work can build on one coherent base

### 3. Failure Visibility And Operator Trust

Target areas:
- stop hiding invalid role, hierarchy, or configuration failures behind silent skips
- surface degraded states through health, dashboard, audit, and operator-facing metadata
- distinguish between safe fallback behavior and silent governance erosion

Expected outcomes:
- operators can see when governance materials fail to load or degrade
- audit and health surfaces become more trustworthy as operational signals
- SA-NOM looks more production-serious to security, audit, and platform reviewers

### 4. Deterministic Defaults And Runtime Predictability

Target areas:
- replace implicit default behavior that depends on file ordering or incidental repository state
- make foundational defaults explicit, explainable, and testable
- tighten startup and runtime contracts around alignment, hierarchy, and policy execution

Expected outcomes:
- behavior becomes easier to explain and harder to change accidentally
- later automation work rests on more stable runtime semantics
- the repo feels cleaner and more disciplined without feature sprawl

### 5. Performance And Execution Discipline

Target areas:
- review hot runtime paths for avoidable repeated work, unbounded scans, or unnecessary parsing
- define small but meaningful verification around startup/runtime budgets and execution efficiency
- preserve a strong quality posture while AI takes on more system work

Expected outcomes:
- runtime growth does not quietly become runtime drag
- performance becomes part of the governance platform story, not an afterthought
- the system remains believable as automation depth increases

## Non-Goals

- no attempt to remove human approval from high-risk or high-authority actions
- no broad UI redesign as the main point of `v0.7.0`
- no uncontrolled expansion into unrelated product concepts
- no overclaim that SA-NOM is fully enterprise-hardened in one release
- no major rewrite that sacrifices current working behavior for architectural purity alone

## Candidate Deliverables

- a `v0.7.0` roadmap centered on autonomous governed runtime foundations
- issue drafts covering runtime portability, automation depth, failure visibility, deterministic defaults, and performance
- cleanup of resource-loading and packaging assumptions
- operator-visible degraded-state surfacing for invalid or failed governance materials
- focused performance and startup-discipline checks
- release framing that positions `v0.7.0` as a quality-and-foundation milestone, not a hype milestone

## Exit Criteria

- SA-NOM can explain one coherent `v0.7.0` direction for cleaner, more autonomous governed runtime execution
- the runtime no longer depends on fragile repository-root assumptions in critical paths
- invalid governance materials and degraded runtime states become visible instead of silently disappearing
- deterministic defaults are clearer, safer, and test-backed
- `v0.7.0` reads as a serious platform-foundation release that improves trust, automation depth, and operational readiness together
