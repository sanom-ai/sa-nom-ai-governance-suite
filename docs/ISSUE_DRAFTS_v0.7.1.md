# Issue Drafts v0.7.1

This file collects draft implementation issues for the `v0.7.1` flagship hardening round.

## 1. Harden outbound connector presets and routing posture

Problem:
- outbound integration language is currently stronger than the explicit target model

Draft scope:
- add explicit preset families for SIEM, Slack, Teams, Jira, ServiceNow, and custom webhook lanes
- expose configured and active channel families in integration health
- surface missing external channels in operator notification readiness

Acceptance:
- dashboard can show which external channels are configured, active, or missing
- integration target catalog clearly maps to named channel families
- tests cover chat-ops, ticketing, SIEM, retry, and dead-letter posture

## 2. Improve Human Ask freshness and confidence visibility

Problem:
- Human Ask is governed and capable, but freshness and confidence posture are not surfaced strongly enough

Draft scope:
- add freshness metadata and staleness posture to Human Ask summaries
- make confidence threshold and automation state easier to inspect in operator views
- strengthen meeting-mode posture summaries

Acceptance:
- Human Ask responses expose freshness posture
- confidence threshold behavior is visible without digging into raw metadata
- dashboard and docs use the same language for governed reporting posture

## 3. Strengthen Role Private Studio publication visibility

Problem:
- the studio workflow is strong, but publication readiness and revision posture could be easier to read in summaries

Draft scope:
- surface revision, approval, and publication-state details more clearly
- make restore-ready posture easier to explain without overclaiming
- improve operator-facing summary wording for blockers and review state

Acceptance:
- publication workflow status is easier to inspect from dashboard/runtime summaries
- revision/diff/restore posture is documented and test-backed

## 4. Harden evidence and audit packaging posture

Problem:
- audit integrity is strong, but evidence-pack story can be made easier to defend operationally

Draft scope:
- improve evidence-pack summary surfaces
- align integrity language around tamper evidence and verification
- connect evidence continuity more directly with retention and release-prep checks

Acceptance:
- evidence-pack posture is visible without opening raw logs
- wording stays precise and technically correct

## 5. Strengthen trusted-registry operator visibility

Problem:
- trusted-registry enforcement exists, but operator surfaces can still be clearer

Draft scope:
- expose registry signature posture more clearly in role summaries
- keep source and bundled manifests aligned through tooling
- make fallback-to-last-known-good posture explicit in health surfaces

Acceptance:
- invalid, fallback, and verified states are easier to inspect
- registry consistency remains test-backed

## 6. Tighten PT-OSS posture continuity

Problem:
- PT-OSS signals exist across several surfaces, but posture language can drift

Draft scope:
- normalize posture wording across Human Ask, dashboard, and docs
- improve blocker/recommendation summaries
- keep Thai structural lane explicit but bounded

Acceptance:
- posture language is consistent across runtime and docs
- publication and automation gates are easier to understand

## 7. Clarify authority and resource-lock operator recovery

Problem:
- authority and lock enforcement are strong, but recovery and trace surfaces can be more operator-friendly

Draft scope:
- improve resource-lock conflict summaries
- surface override and resume posture more clearly
- reinforce recovery guidance in operator surfaces

Acceptance:
- blocked and waiting-human resource situations are easy to diagnose from summaries

## 8. Release-prep for flagship claims

Problem:
- flagship marketing language should stay synced to implementation reality

Draft scope:
- align feature matrix, product tour, and release notes to the improved `v0.7.1` surfaces
- produce a stronger internal handoff for the next phase

Acceptance:
- `v0.7.1` claim language is stronger, cleaner, and easier to defend without overclaiming
