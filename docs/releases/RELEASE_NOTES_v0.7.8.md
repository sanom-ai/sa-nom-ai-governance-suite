# Release Notes - v0.7.8

## Release Focus

v0.7.8 is the private-first tablet productization release after v0.7.7.

This release turns the command surface into a touch-first operating shell for organizational tablet use while preserving the founder doctrine:

- one human governs through one clean dashboard
- AI remains the primary workforce
- deeper governance mechanics stay protected behind progressive disclosure
- the runtime stays private-first instead of drifting into a public or consumer-oriented surface

The central direction of the release is:

**Private-First Tablet Command Surface**

## Completed Scope

### Tablet Command Surface Foundation

- strengthened the command shell so Home, navigation, and primary action areas behave like a tablet-first surface instead of a desktop page squeezed onto a smaller screen
- increased touch-target clarity across the main command lanes
- prioritized department quick access using live work context so the surface reflects where the runtime is actually carrying pressure
- kept the Home surface clean while preserving the dark plus beige-gold command aesthetic

### Private Session Continuity And Persona Focus

- surfaced private session continuity directly on Home instead of leaving session state hidden in lower-level runtime lanes
- added persona-aware tablet focus guidance so founder, admin, operator, and executive-style sessions see a more intentional start point
- preserved the private-runtime story by keeping session continuity and governed routing visible without exposing raw session internals
- made the Home surface answer not only what the next work item is, but also whether the current private session is still safe to keep using on tablet

### Touch-First Work Lanes

- added larger touch-first lane cards for Work Inbox, Cases, Documents, AI Actions, and Directory & Search
- introduced a tablet lane rail so adjacent work lanes stay one tap away when moving through the live runtime
- made the session countdown move on the client so tablet operators can see time pressure without manual refresh
- kept lane movement tied to governed flows rather than falling back to low-level runtime navigation

### Control Room Consolidation And Governance Popup

- moved advanced governance entry points behind a dedicated Governance popup launcher instead of a cramped narrow dropdown
- grouped Role Private Studio, Structural Risk & Alignment, Trust & Evidence, Setup & Onboarding, Master Data & Routing, Integrations & Providers, Runtime & Recovery, and Admin Settings into a clearer Control Room access model
- polished the popup so it fits tablet and PC screens more cleanly without forcing unnecessary scroll for the main launcher state
- kept Home simple for normal users while making deeper governance tooling easier to discover for founder, admin, and IT sessions

## Why This Release Matters

v0.7.8 matters because the founder vision is not only about having a dashboard that looks clean on a laptop.
The product also needs to work in the realistic posture of a private organization where:

- one person may review the organization from a tablet while moving between meetings, rooms, or operations lanes
- the command surface must stay readable and touch-friendly
- the private runtime must not feel fragile just because the device sleeps or the session window tightens
- AI must remain visibly active while the human is only asked to intervene when it genuinely matters

After v0.7.8, SA-NOM is closer to that posture:

- Home feels more like a private command tablet than a desktop dashboard scaled down
- session continuity is easier to understand and recover without exposing runtime plumbing
- persona-specific lane emphasis makes the next touch target clearer
- advanced governance tooling is easier to find without leaking low-level mechanics back onto Home

## Validation

The release line was validated with:

- `python -m compileall -q sa_nom_governance _support\tests`
- `node --check sa_nom_governance\dashboard\static\dashboard_app.js`
- `python scripts\dashboard_server.py --check-only`
- `python -m pytest --no-cov _support\tests\test_dashboard_operator_surface.py -q`
- `python -m pytest _support\tests`

Current validation outcome:

- `363 passed`
- `coverage 85.04%`

## Release Notes Source

- [PR Description v0.7.8](PR_DESCRIPTION_v0.7.8.md)
- [v0.7.8 Handoff](../V0_7_8_HANDOFF.md)
