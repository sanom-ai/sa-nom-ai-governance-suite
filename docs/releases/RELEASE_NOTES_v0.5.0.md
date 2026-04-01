# Release Notes - v0.5.0

## Release Focus

`v0.5.0` is the governed human-in-the-loop operations release after the PTAG public-opening and PTAG polish phases.

This release is focused on moving SA-NOM from a quality prototype toward a serious organizational candidate by defining one coherent governed operations layer that connects PTAG, human approval paths, Human Ask reporting, runtime trust signals, and integration/compliance continuity.

## Completed Scope

### Governed HITL Operations Layer

- added the core governed HITL operations document that defines trigger classes, decision states, human roles in the loop, and the relationship between PTAG, approvals, audit, and runtime visibility
- clarified where AI can continue governed work and where human authority must explicitly take control
- made the human-in-the-loop model a first-class operational layer rather than an implied governance idea

### Minimal Human Approval Surface

- defined the first compact approval-facing interaction model for governed actions
- described how operators should inspect pending actions, review evidence, approve or reject, add rationale, and escalate within authority boundaries
- gave `v0.5.0` a usable human-facing control surface without turning the phase into a broad UI platform effort

### Governed HITL Human Ask Reporting

- defined how Human Ask should report HITL status without bypassing governance
- made approval, escalation, and rationale visibility part of the governed reporting story
- clarified that status reporting must respect authority, evidence, and decision-boundary rules even when humans ask the AI for updates

### HITL Role Packs And Use Cases

- added realistic HITL-oriented use-case lanes such as customer complaints, contract review, and incident recovery
- connected the governed HITL model to concrete organizational scenarios instead of leaving it as abstract architecture only
- improved the repo's ability to explain where approval, review, and escalation logic matter in practice

### Governed HITL Reliability And Observability

- added a compact baseline for approval queue health, escalation pressure, stale decision packets, degraded reporting posture, and audit continuity under stress
- explained how operators should distinguish runtime-health problems from governance decisions
- made the governed approval loop more believable for serious evaluation by adding an operational trust layer around the approval model

### Governed HITL Integration And Compliance Continuity

- defined the smallest useful integration-continuity story for provider, document, and service boundaries inside governed HITL operations
- connected the HITL layer to the repo's existing PDPA and Thailand-facing compliance posture without overstating legal completion
- added safe and unsafe public claims for discussing governed HITL operations in more serious organizational settings

## Why This Release Matters

`v0.5.0` is the first release where SA-NOM starts to look less like a well-structured governance prototype and more like a system an organization could seriously evaluate for pilot use.

The repository now gives readers a clearer path to:
- understand where AI work should stop for human authority
- inspect a first credible approval and escalation model
- ask governed status questions through Human Ask without bypassing control boundaries
- reason about queue pressure, reliability posture, and audit continuity around sensitive actions
- imagine how the governed HITL loop fits provider, document, service, and Thailand-facing accountability contexts

## Verification

- docs-only phase slices were added through the normal PR flow
- each `v0.5.0` slice was merged through planning-first and implementation PRs before release-prep

## Next Phase

The next milestone after `v0.5.0` should focus on turning the governed HITL operations model into a stronger implementation and operator-evaluation surface, while keeping the current unified structure disciplined enough to avoid feature sprawl.

## Notes

- this release closes the first governed HITL operations phase
- `v0.5.0` intentionally favors one coherent operational story over a wide spread of loosely related features
- the public repo now has a clearer serious-evaluation narrative for organizations considering pilot adoption, while still staying honest about what remains deployment-specific or compliance-specific work
