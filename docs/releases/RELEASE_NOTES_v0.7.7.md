# Release Notes - v0.7.7

## Release Focus

`v0.7.7` is the productization-hardening release after `v0.7.6`.

This release turns the recent runtime foundations into a cleaner pilot product by splitting the operator experience into:

- a simple `Command Surface` for normal users
- a protected `Control Room` for advanced governance work
- a guided `Setup Assistant` for onboarding, doctor continuity, and pilot preparation
- a clearer `Backup & Restore` plus `Admin Settings` surface for privileged operators

The central direction of the release is:

`Productization Hardening`

That means `v0.7.7` focuses on making SA-NOM easier to deploy, understand, and operate without weakening the founder doctrine that one human governs the organization while AI performs most of the operational work.

## Completed Scope

### Command Surface Foundation

- added a simple Home dashboard that leads with posture, next actions, AI activity, and department context instead of low-level runtime mechanics
- introduced a cleaner top navigation model around `Home`, `Work Inbox`, `Cases`, `Documents`, `AI Actions`, and `Governance`
- made the Home surface answer posture and next human move quickly through `Your Next Actions`, `System Posture Summary`, `AI Activity Feed`, and department quick access
- kept deeper governance, trust, audit, and technical diagnostics behind progressive disclosure instead of exposing them to all users by default

### Control Room And Role Gate

- added a dedicated `Control Room` route for advanced governance work
- restricted Control Room visibility to founder, admin, owner, and IT style sessions instead of exposing it to general operator lanes
- kept technical governance surfaces such as runtime health, conflicts, audit, trusted registry, sessions, backup/recovery, and admin posture behind the protected Control Room boundary
- reinforced the command-surface doctrine that normal users should see simple work-driving signals first, not governance plumbing

### First-Run, Doctor, And Onboarding Continuity

- added a stronger `Setup Assistant` lane for onboarding, diagnostics, doctor continuity, and pilot guidance
- preserved setup continuity so owner registration and first-run actions stay inside the setup lane when that is where the operator started
- surfaced setup accessibility in the session/runtime posture so command-surface users can continue pilot preparation without dropping into raw runtime tooling
- improved onboarding continuity between Home, Setup Assistant, and Control Room

### Backup, Restore, And Admin Settings Surfaces

- added a privileged `Backup & Restore` tool to Control Room
- surfaced backup history, restore doctrine, doctor/proof/baseline artifacts, and critical recovery paths in one governed tool
- added an `Admin Settings` tool that summarizes organization identity, access posture, providers, integrations, master-data posture, and retention posture without exposing raw internals first
- carried runtime performance baseline into the privileged operating surface so hardening and pilot discipline stay visible

### Command Surface Polish

- changed the Home heading to an English-first command-surface presentation
- made the live timestamp tick continuously on the client without forcing a manual refresh while preserving the Thai datetime format
- documented the command surface visually in the root README with a real `v0.7.7` screenshot

## Why This Release Matters

`v0.7.7` matters because product-grade governed automation is not only about having the right runtime foundations.

By `v0.7.6`, SA-NOM already had:

- a work-surface dashboard
- canonical case continuity
- governed document runtime behavior
- explicit AI action runtime
- master data, search, and assignment routing

But one more step was required before the product could feel like a serious pilot surface:

- normal users needed a simpler command center
- advanced governance tooling needed stronger separation
- onboarding and diagnostics needed continuity
- backup, restore, and administrative posture needed to be visible as part of the product, not as hidden operator knowledge

After `v0.7.7`, SA-NOM is closer to its founder thesis:

- one human can read the command surface and understand what should happen next
- AI remains the primary workforce in the visible operating model
- deeper governance mechanics still exist, but they are protected and intentionally disclosed
- pilot setup, recovery, and administration are more product-like and less dependent on repository familiarity

## Verification

Validated during the current `v0.7.7` productization-hardening line with:

- `python -m compileall -q .`
- `node --check .\sa_nom_governance\dashboard\static\dashboard_app.js`
- `python scripts\dashboard_server.py --check-only`
- `python -m pytest _support\tests`
- current full-suite status: `359 passed`
- current coverage posture: `85.02%`

## Next Phase

After `v0.7.7`, the strongest continuation is a dedicated hardening line that raises product confidence further through:

- broader coverage expansion across low-coverage deployment and API entry modules
- tighter first-run and backup/restore validation
- stronger persona-specific operator refinement
- additional pilot-grade scenarios and diagnostics coverage

## Notes

- `v0.7.7` should be read as the productization-hardening milestone for the current `v0.7.x` line
- the release intentionally keeps low-level governance details behind progressive disclosure rather than exposing them on the Home surface
- `coverage.xml` remains a local artifact and is not part of the release surface
