# Governed HITL Integration And Compliance Continuity

This document defines the smallest useful integration and compliance-continuity layer for governed human-in-the-loop operations in SA-NOM.

It is the integration and accountability continuation of the `v0.5.0` governed HITL model and should be read as the point where the HITL layer becomes easier to imagine inside a real organizational stack.

## Why This Layer Exists

SA-NOM already explains:
- when actions must stop for human approval
- how a minimal human approval surface should work
- how Human Ask reports governed status
- how role packs and use cases make the model concrete
- how reliability and observability support approval trust

What still needs to be explicit is how this governed HITL layer connects to the outside world without losing its approval, audit, and evidence posture.

That matters because serious evaluators will ask:
- which provider lanes can sit behind the governed loop
- how document and API touchpoints preserve approval visibility
- whether external integration breaks audit continuity
- how Thai and broader compliance readers should interpret the HITL layer
- what the repo honestly supports today versus what still belongs to organization-specific implementation

This layer exists to answer those questions with a narrow, believable continuity model.

## Core Position

`v0.5.0` should not try to become a broad connector marketplace.

The right move in this phase is smaller and more disciplined:
- define the minimum integration surface that keeps governed approvals believable
- preserve PTAG authority, approval state, and audit continuity across those surfaces
- connect the HITL model to the repo's compliance and localization posture without pretending to complete legal work automatically

The result should be one governed operations story that still makes sense when provider, document, or API boundaries are involved.

## Minimum Integration Surface

At this phase, the most useful integration continuity comes from surfaces the repo already points toward.

The baseline lanes are:
- private or self-managed provider lanes such as Ollama
- hosted evaluation lanes such as OpenAI and Claude (Anthropic)
- governed document workflows and document-centered approval requests
- API or service boundaries where a governed role needs to emit, pause, or report a decision packet

The important point is not how many connectors exist.
The important point is whether the governed approval model survives these boundaries intact.

## Provider Continuity

The provider layer should not erase governance context.

When a provider lane is used inside a governed HITL workflow, the system should preserve:
- the governed role or decision packet identity
- the trigger class that required human review
- the approval state before and after provider-assisted work
- the evidence context that informed the human decision
- the audit record showing how provider output influenced the path

This means provider integration should support the governed loop rather than shortcut around it.

In repo terms, the current believable public position is:
- Ollama remains the strongest private-lane story
- OpenAI and Claude remain optional hosted evaluation lanes
- provider choices belong inside governed authority and approval boundaries, not outside them

## Document And Workflow Continuity

Many organizations first encounter HITL through document release, policy review, contract review, incident response, or customer-facing case handling.

That means document and workflow touchpoints need a continuity model.

At minimum, document-facing governed HITL flow should preserve:
- who owns the approval decision
- which version, packet, or case was under review
- what rationale and evidence were attached
- whether the action was approved, rejected, returned, or escalated
- whether a document release or external action remained blocked pending human authority

This connects the HITL layer naturally to the repo's governed document material without needing a broad ECM platform story in `v0.5.0`.

## API And Service Continuity

A serious organizational candidate also needs a small service-boundary story.

When governed roles interact through APIs or service layers, the public baseline should preserve:
- stable decision-state labels
- approver, reviewer, and escalation-owner visibility
- timestamps and evidence references for interventions
- clear separation between automated preparation and human authority
- reporting paths that remain governed when queried through Human Ask or operator views

The point is not a finished public SDK catalog.
The point is a stable contract for governed actions across boundaries.

## Human Ask And Integration Boundaries

Human Ask should remain a governed reporting surface even when information comes from multiple systems.

That means Human Ask responses about governed HITL status should:
- report from approved data paths
- respect authority and evidence boundaries
- distinguish operational status from legal or policy conclusions
- avoid becoming an informal bypass into restricted systems or pending decisions

This matters even more once organizations imagine the HITL loop spanning providers, documents, and service integrations.

## Compliance Continuity

The public repo already has an honest compliance posture.

The HITL layer should continue that posture rather than weaken it.

The right continuity model is:
- SA-NOM supports governed operations, auditability, evidence discipline, and human authority boundaries
- the repo helps organizations structure accountability-sensitive AI workflows
- legal completion, sector-specific interpretation, and regulator-facing completion still require human ownership

This is especially important when HITL is discussed in serious organizational settings because human approval alone does not equal legal completion.

## Thailand And PDPA Continuity

For Thailand-facing evaluation, the HITL layer should be legible against the repo's existing guidance.

The most important continuity points are:
- high-risk or personal-data-sensitive AI actions should remain clearly human-gated
- rationale and evidence capture support review readiness, but do not replace privacy or legal analysis
- governed approval states help show accountability discipline in Thai organizational contexts
- PDPA-sensitive workflows still require role-specific privacy review, lawful-basis analysis, and operational data-handling controls
- Thai regulatory and localization expectations should attach to the HITL control loop through clear ownership, not broad marketing claims

The safe public position remains consistent with the repo's existing maps:
- SA-NOM helps organizations structure governed, evidence-aware, human-supervised AI operations in Thailand
- formal regulator-facing readiness still requires legal and compliance review

## Safe Public Claim

A safe claim for this slice is:

SA-NOM now provides a governed human-in-the-loop operations model that can be connected to provider, document, and service boundaries while preserving approval visibility, evidence posture, and accountability continuity. Organizations should still pair this with their own legal, privacy, security, and deployment review before treating it as complete organizational compliance.

## Unsafe Claims To Avoid

Do not say:
- SA-NOM now completes compliance automatically because it has HITL approvals
- any provider or connector becomes compliant simply by routing through PTAG
- document integration alone makes external release decisions safe
- Human Ask can be used as a shortcut around authority boundaries
- the public repo already delivers every integration needed for enterprise deployment

## Design Boundaries

This slice should remain disciplined.

It is not:
- a promise of full enterprise connector coverage
- a complete regulator-response pack
- a claim that localization work is finished
- a replacement for organization-specific legal, security, or privacy implementation

It is the narrow continuity layer that keeps the governed HITL story believable beyond the core approval screen.

## What Success Looks Like

This slice is successful when a serious organizational reader can see that SA-NOM now has:
- a believable integration surface for governed approvals
- a provider continuity story that keeps authority and audit visible
- document and service-boundary continuity for approval and escalation flow
- compliance wording that stays honest while remaining useful
- clear Thailand and PDPA continuity for human-supervised AI operations

That is enough to make the `v0.5.0` governed HITL layer feel more deployable in real organizational evaluation.

## Next Steps

The implementation slices that should follow this document are:
1. a compact `v0.5.0` release-prep slice
2. release notes and evaluation framing for serious organizational review

## Summary

Governed HITL integration and compliance continuity makes the approval model legible beyond the core interface.

It shows how SA-NOM can preserve authority, auditability, and evidence posture across provider, document, and service boundaries while staying honest about what still belongs to organization-specific compliance and deployment work.
