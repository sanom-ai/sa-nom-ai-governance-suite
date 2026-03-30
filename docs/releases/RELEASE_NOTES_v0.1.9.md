# Release Notes v0.1.9

## Release Focus

This release turns SA-NOM's Governed Document Center into a much clearer public product module by expanding it from a single concept into a governed operating model with structure, routing, metadata, Human Ask reporting, retention governance, scenario guidance, and a public-safe role pack.

## Highlights

- added a broader Governed Document Center architecture for controlled documents, forms, templates, and records
- added document classes, lifecycle, authority routing, and numbering/metadata guidance
- added Human Ask reporting guidance for governed document lookup, status, and meeting workflows
- added retention and records governance guidance including archive, hold, and disposal posture
- added a governed document release and change-control scenario
- added a public-safe `Document Governance Coordination Lead` role pack and example artifact

## Why This Release Matters

The repo already showed how SA-NOM governs AI roles, but it still needed a clearer answer for document-heavy organizations that want AI to work inside a controlled document system without drifting outside approval, authority, audit, or records-governance boundaries.

`v0.1.9` gives that answer.

It shows that SA-NOM can describe a document-governance module where:
- AI handles routine document work
- humans confirm only at true control boundaries
- released versions, superseded versions, records, and holds stay governable
- Human Ask becomes a practical reporting layer instead of a vague lookup feature

## What Was Added In v0.1.9

### Governed Document Center Architecture

- `docs/GOVERNED_DOCUMENT_CENTER.md`
- `docs/GOVERNED_DOCUMENT_CLASSES.md`
- `docs/GOVERNED_DOCUMENT_LIFECYCLE.md`
- `docs/GOVERNED_DOCUMENT_TEMPLATE_MODEL.md`
- `docs/GOVERNED_DOCUMENT_AUTHORITY_ROUTING.md`
- `docs/GOVERNED_DOCUMENT_NUMBERING_METADATA.md`
- `docs/GOVERNED_DOCUMENT_HUMAN_ASK_REPORTING.md`
- `docs/GOVERNED_DOCUMENT_RETENTION_RECORDS.md`
- `docs/GOVERNED_DOCUMENT_RELEASE_SCENARIO.md`

### Role Story And Example Artifact

- `docs/DOCUMENT_GOVERNANCE_ROLE_PACK.md`
- `examples/document_governance_role_pack.example.json`

## Community Baseline In This Release

The public baseline now includes a much clearer document-governance story for:
- controlled document classes such as policies, standards, procedures, work instructions, forms, checklists, templates, and records
- role-based authority and approval routing
- numbering and metadata discipline
- Human Ask reporting on active versions, pending approvals, gaps, and retained posture
- retention, archive, hold, and disposal guidance
- a public-safe role pack showing how AI can work inside governed document operations

## Commercial Direction

Commercial offerings remain separate from the AGPL community baseline and may include rollout support, tailored document models, controlled-template libraries, records-governance support, custom approval workflows, and organization-specific operating design.

See `docs/FEATURE_MATRIX.md`, `docs/COMMERCIAL_LICENSE.md`, `docs/GOVERNED_DOCUMENT_CENTER.md`, and `docs/DOCUMENT_GOVERNANCE_ROLE_PACK.md` for the current public positioning.

## Upgrade Notes

- `v0.1.9` is a product-architecture and workflow-definition milestone, not a runtime feature-engine milestone
- the release does not claim that a full document-management engine is already implemented in the public baseline
- the operating rule remains consistent: AI performs routine governed document work inside approved boundaries, and humans step in for approval, exception, waiver, disposal, hold, and other higher-risk control decisions

## Verification Snapshot

Validated during `v0.1.9` release preparation with:
- docs-only review of the Governed Document Center module, numbering/metadata, Human Ask, retention, release scenario, and role-pack materials
- local verification that the new release notes are linked from `docs/README.md`

## Post-Release Follow-Up

Recommended next steps after `v0.1.9`:
- decide whether to keep deepening the Governed Document Center before release hardening work in `v0.1.10`
- consider a governed document scenario artifact or runtime-facing implementation slice next
- prepare the `v0.1.10` engineering-discipline milestone for formatting, type-safety, and test-hardening improvements
