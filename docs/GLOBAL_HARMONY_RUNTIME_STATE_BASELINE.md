# Global Harmony Runtime State Baseline

This document describes the first invisible runtime layer that sits between the constitution catalog and any future dashboard or operator surface.

## Purpose

`v0.6.1` should establish a real internal contract for Global Harmony before introducing broader UI controls. The runtime state layer makes the currently selected constitution explicit, auditable, and available to other services.

## Baseline Runtime Contract

- `available_regions`: the catalog-visible constitutions that can be selected safely
- `active_selection`: the currently effective regional constitution, including who selected it and why
- `safe_claim`: the safe positioning statement published by the selected constitution
- `evaluation`: an optional governed alignment evaluation for a supplied context
- `notes`: system reminders that keep the feature inside safe claims

## What This Slice Does

- applies baseline switching guardrails so constitution changes stay attributable and justified
- initializes an active constitution from the registry
- allows operator-controlled switching to another region
- exposes a runtime snapshot that can be consumed by later API or dashboard layers
- keeps evaluation optional so callers can ask for state only or state plus alignment signals

## What This Slice Does Not Do

- it does not add automatic geolocation or country inference
- it does not claim legal compliance automation
- it does not replace local human experts
- it does not add fully calibrated resonance scoring or automatic cultural truth claims

## Why This Matters

This layer turns Global Harmony from a set of files into a governed runtime posture. Later UI work should read from this runtime state instead of inventing its own version of the truth.

## Adoption-Value Mapping

- **Last-mile social fit**: runtime evaluation now carries a `resonance_score` and `resonance_band` with region-aware concerns, so teams can spot cultural drift before external output is released.
- **High ROI by design**: alignment behavior is injected through PTAG principles and constitution documents at runtime; no model retraining is required for each country or business unit.
- **Enterprise credibility**: selection intent, approval-required states, and runtime metadata are all traceable through governed audit and human-override paths, including private and air-gapped deployment posture.

## Preview And Audit Handoff

- `preview_switch(...)` lets operators inspect the target constitution and its governed evaluation before a switch is applied
- `audit_handoff` gives later audit or event layers a stable record shape for alignment selection intent
- this keeps switching reviewable before any dashboard-heavy implementation appears

## Ingestion Contract

- uploaded constitution documents should pass through a single ingestion contract before they become selectable
- ingestion requires `source_document_id`, `requested_by`, a structured payload, and at least one principle
- ingestion results now return accepted/errors/warnings plus a normalized constitution summary
- this keeps later document-center integration conservative and auditable

## Selection Intent Policy

- `blocked`: actor or rationale is not sufficient to justify the switch
- `preview_only`: context is missing or guarded enough that the switch should stay in review mode first
- `require_approval`: sensitive or externally visible contexts require an approval actor before the switch can activate
- `direct_switch`: low-risk governed contexts can activate directly under the baseline policy

## Runtime Decision Integration

- requests can now supply `global_harmony` metadata to evaluate cultural alignment during runtime
- low-risk aligned cases are annotated in metadata and trace notes
- preview-only or approval-required cases can pause the runtime with a human review gate
- active-region evaluation can attach guarded or escalated signals to runtime outputs without changing dashboard layers first
