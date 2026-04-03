# Release Notes - v0.7.6

## Release Focus

`v0.7.6` is the master-data, search, and assignment release after `v0.7.5`.

This release is where SA-NOM stops treating ownership, routing, and searchability as implied metadata around governed work and starts treating them as explicit runtime surfaces.

The central direction of the release is:

`Master Data, Search, Assignment`

That means `v0.7.6` focuses on making governed work organization-aware and searchable with:

- a canonical master-data runtime for organization, people, seats, and teams
- an assignment queue that routes governed work to real owners with priority, SLA status, and aging
- a searchable continuity layer across cases, requests, documents, AI actions, evidence, sessions, and roles
- a new `Directory & Search` dashboard lane that turns ownership, routing, and search into one operator surface
- runtime health visibility for the master-data store so the new layer is part of the same operational contract as the rest of the product

The result is a stronger operating model where governed work no longer floats as disconnected records. It becomes real organizational work that can be routed to real people, grouped by teams and seats, and searched across the same case and evidence story.

## Completed Scope

### Canonical Master-Data Runtime Baseline

- added a master-data runtime package with a persisted store and derived runtime snapshots
- introduced baseline organization, people, seat, and team modeling derived from owner registration, access profiles, and observed runtime actors
- made the master-data store part of the same persisted runtime contract as audit, Human Ask, document, and AI action stores
- exposed master-data summary posture through the dashboard snapshot and runtime health surface

### Assignment Engine With SLA, Aging, And Ownership

- added an assignment queue that converts overrides, Human Ask sessions, studio work, governed documents, and AI actions into routed owned work items
- attached owner, team, priority, SLA posture, age, and next-step guidance to assignment items
- preserved fallback-owner behavior when a specific person is not resolved so the queue remains operable instead of dropping work on the floor
- made assignment ordering stable and urgency-aware so the highest-pressure work surfaces first

### Global Search And Relationship Browsing

- added a global search index across people, teams, seats, assignments, cases, requests, documents, actions, Human Ask records, studio requests, roles, evidence exports, and sessions
- kept search results aligned with canonical case continuity so linked records still open in the right governed lane
- made relationship browsing visible across case, role, document, evidence, and session records from one searchable surface
- kept the search model light by deriving one search text contract per item instead of layering separate search systems per module

### Directory And Search Dashboard Surface

- added a dedicated `Directory & Search` lane to the dashboard
- surfaced people, seats, teams, owned assignments, and searchable continuity in one operator-facing work surface
- made search case-aware so case context can carry into directory browsing without losing the active governed issue
- added next-step guidance and related views so the directory lane routes operators back into the right working lane instead of acting like a detached catalog

### Runtime And Verification Integration

- wired master-data state into `AppConfig`, `EngineApplication`, and `DashboardSnapshotBuilder`
- exposed the master-data store through runtime health alongside the existing persisted stores
- added direct tests for the master-data service and extended dashboard surface tests to cover summary exposure and runtime posture
- validated the full runtime, dashboard, and test surface with full-suite verification

## Why This Release Matters

`v0.7.6` matters because product-grade governed automation cannot stop at cases, documents, and AI actions.

Before this release, SA-NOM already had:
- stronger work surfaces through `v0.7.2`
- canonical case continuity through `v0.7.3`
- governed document runtime behavior through `v0.7.4`
- explicit AI action runtime through `v0.7.5`

But one more product-grade move was required:
- governed work needed to be routed to real owners instead of staying implicit inside lane-level summaries
- the system needed to become searchable across people, cases, documents, actions, and evidence
- ownership and organizational continuity needed to become first-class operating signals instead of inferred context

After `v0.7.6`, the product is more realistic:
- real governed work can be routed to real owners with visible aging and SLA posture
- people, teams, seats, and owned work live in the same operator surface
- search becomes a continuity tool instead of a disconnected lookup
- operators can move from ownership to action, and from search result to governed lane, without losing case context

This is an important step toward the SA-NOM thesis that one human can govern an organization through one dashboard because AI carries most of the operational work inside explicit authority, evidence, ownership, and escalation boundaries.

## Verification

Validated during the current `v0.7.6` master-data, search, and assignment line with:

- `python -m compileall -q .`
- `node --check .\sa_nom_governance\dashboard\static\dashboard_app.js`
- `python scripts\dashboard_server.py --check-only`
- `python -m pytest _support\tests`
- current full-suite status: `356 passed`
- current coverage posture: `84.88%`

## Next Phase

After `v0.7.6`, the strongest continuation is `v0.7.7`.

That next phase should move from organizational work realism toward full pilot hardening:
- admin settings and runtime control surfaces
- first-run assistant and setup continuity
- diagnostics, doctor, and preflight continuity
- backup and restore UX
- migration and upgrade process hardening

## Notes

- `v0.7.6` should be read as the master-data, search, and assignment milestone, not as the full productization-hardening milestone
- the goal of this release is to make governed work organization-aware and searchable, not to claim that every ERP-style master-data domain is already complete
- `coverage.xml` remains a local artifact and is not part of the release surface
