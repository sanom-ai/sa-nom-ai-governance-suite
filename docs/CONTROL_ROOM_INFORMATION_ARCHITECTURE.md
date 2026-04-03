# Control Room Information Architecture

SA-NOM uses a split surface model:

- `Home` is the simple command surface for normal users.
- `Governance > Control Room` is the advanced governance and system operations surface.

This document defines what belongs in Control Room, what must stay out of it, and how the information architecture should be grouped so the product stays aligned with the founder doctrine:

- one human governs the organization through one clean dashboard
- AI is the primary workforce
- humans act as directors and governors, not clerks
- low-level runtime plumbing stays behind progressive disclosure

## Purpose

Control Room exists for advanced setup, trust, recovery, and governance operations.

It is not the normal operating surface for day-to-day business work.

Users should enter Control Room when they need to:

- configure the governed runtime
- create or publish AI workforce roles
- review trust, evidence, and signature posture
- change routing, retention, integration, or provider settings
- perform recovery, backup, restore, or diagnostics tasks
- complete first-run or pilot-hardening setup

## Audience

Control Room is restricted to advanced operators only.

Primary personas:

- Founder
- Executive Owner
- Platform Admin
- IT Operator
- Governance Lead

Normal users should not rely on Control Room for their daily work.

Normal-user personas:

- Executive
- Department Head
- Operator
- Reviewer
- Standard business user

These users should operate from `Home`, `Work Inbox`, `Cases`, `Documents`, `AI Actions`, and governed business flows.

## Top-Level Principle

Control Room should answer:

- is the governed runtime correctly configured
- is trust intact
- is the system ready to run
- what advanced action is required next

Home should answer:

- what is the posture right now
- what do I need to do next
- what is AI doing right now

If a surface is mostly about setup, configuration, trust, diagnostics, or recovery, it belongs in Control Room.

If a surface is mostly about executing business work, reviewing work items, reading documents, or following AI work in progress, it does not belong in Control Room.

## What Must Stay Out Of Control Room

The following surfaces remain on the normal command surface and should not be primary Control Room tools:

- `Home`
- `Work Inbox`
- `Cases` for daily business operation
- `Documents` for daily governed document work
- `AI Actions` for normal action monitoring
- `Ask AI anything`
- `Quick Access by Department`
- `AI Activity Feed`
- `Human Ask` for normal report or meeting usage

These are operating surfaces, not setup or governance-administration surfaces.

## What Must Live In Control Room

Control Room should group all advanced setup and governance tools under one protected IA.

### 1. Control Room Overview

Purpose:

- give advanced operators one summary page for governance and runtime posture

Includes:

- go-live posture
- runtime readiness
- trust and evidence posture
- first-run blockers
- critical alerts
- setup blockers
- recovery warnings

### 2. Setup And Onboarding

Purpose:

- make first-run and pilot hardening explicit and repeatable

Includes:

- Setup Assistant
- First-Run Action Center
- Owner Registration
- Quick-Start Doctor
- Usability Proof
- first-run continuity guidance
- deployment bootstrap readiness

### 3. AI Workforce And Roles

Purpose:

- create, review, publish, and govern the AI workforce

Includes:

- Role Private Studio
- role review and publication posture
- trusted role publication status
- PTAG role pack lifecycle
- hierarchy posture
- authority boundary posture
- draft readiness
- restore and revision governance

### 4. Structural Risk And Alignment

Purpose:

- review structural governance pressure and alignment posture

Includes:

- PT-OSS Structural Intelligence
- structural readiness posture
- structural fragility and pressure posture
- publication risk posture
- AI workforce structural review
- Global Harmony and alignment governance
- alignment default region
- constitution selection posture
- resonance and regulatory posture

### 5. Trust And Evidence

Purpose:

- protect the chain of trust and auditability

Includes:

- Audit posture
- Evidence Exports
- audit chain integrity
- evidence export attention state
- workflow proof posture
- Trusted Registry posture
- signature status
- manifest posture
- trusted role mismatch posture

### 6. Documents And Records

Purpose:

- govern the system of record for documents and records

Includes:

- document classes
- numbering rules
- approval routing rules
- publish and archive authority
- template governance
- retention category mapping
- records governance posture

### 7. Runtime And Recovery

Purpose:

- keep the private runtime healthy and recoverable

Includes:

- Runtime Health
- Conflicts And Locks
- Sessions posture
- Backup And Restore
- runtime recovery guidance
- runtime performance baseline
- startup and smoke readiness
- critical storage and persistence posture

### 8. Integrations And Providers

Purpose:

- configure system connections and model lanes safely

Includes:

- Integrations
- delivery posture
- outbound channels
- Model Providers
- fallback lane readiness
- notification and delivery diagnostics

### 9. Access And Security

Purpose:

- control who can access what and how runtime sessions behave

Includes:

- access profiles
- delegated privilege posture
- session policy posture
- revoke and continuity controls
- idle and expiry policy posture
- operator access posture
- Authority Guard posture
- Resource Lock posture
- privileged access posture

### 10. Master Data And Routing

Purpose:

- maintain organization structure and governed routing logic

Includes:

- master data governance
- people, seats, teams, departments
- routing ownership map
- assignment and escalation routing governance
- fallback owner logic
- SLA ownership posture
- searchable directory posture

### 11. Admin Settings

Purpose:

- provide one place for organization-wide settings

Includes:

- organization identity settings
- environment posture
- provider defaults
- integration defaults
- retention defaults
- routing defaults
- access defaults
- governance language defaults

## Recommended Governance Menu Structure

Top navigation:

- `Governance`

Dropdown:

- `Control Room`
- optional shortcuts for `Setup & Onboarding`, `Role Private Studio`, and `Admin Settings` may appear under `Governance` as long as they still open inside Control Room

Inside Control Room:

- `Overview`
- `Setup & Onboarding`
- `AI Workforce & Roles`
- `Structural Risk & Alignment`
- `Trust & Evidence`
- `Documents & Records`
- `Runtime & Recovery`
- `Integrations & Providers`
- `Access & Security`
- `Master Data & Routing`
- `Admin Settings`

## Recommended Immediate Moves

The next Control Room consolidation pass should clearly expose these existing capabilities:

- Role Private Studio
- Setup Assistant
- Owner Registration
- Retention
- Evidence Exports
- Trusted Registry posture
- Integrations
- Model Providers
- First-Run Action Center
- Quick-Start Doctor
- Usability Proof
- Master Data governance
- Assignment and routing governance
- Global Harmony and alignment governance

## Specific Product Notes

- `Role Private Studio` remains the canonical name. Operators fill a normal JD-style document and the runtime converts it into PTAG and publication governance behind the scenes.
- `Owner Registration` is primarily a SA-NOM team first-time setup lane, not a daily business-user tool.
- `PT-OSS Structural Intelligence` is not a setup wizard. It is a structural governance posture surface that should be visible as risk and readiness intelligence.

## Progressive Disclosure Rules

- show summary first
- hide low-level identifiers by default
- make advanced details opt-in
- every advanced card should answer what it means and what action comes next
- keep raw store paths, evidence identifiers, and signature internals out of normal-user surfaces

## Role Gating Rules

Minimum allowed roles:

- `founder`
- `owner`
- `admin`
- `it`

Normal users should still work from:

- `Home`
- `Work Inbox`
- `Cases`
- `Documents`
- `AI Actions`
- `Human Ask`

## Definition Of Done

This IA is working when:

- normal users can stay on Home and work surfaces most of the time
- advanced operators can find setup and governance tools under Control Room
- Role Private Studio is easy to find from Governance
- Control Room feels organized by purpose, not implementation detail
- low-level runtime plumbing is hidden from normal surfaces