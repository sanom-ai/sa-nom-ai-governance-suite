# Governed Document Release And Change-Control Scenario

This guide shows a practical governed-document workflow inside SA-NOM's Governed Document Center.

The point is to make the model concrete.
It shows how AI should do routine document work inside approved boundaries while humans step in only for approval, exception, waiver, or higher-risk control decisions.

## Scenario

A manufacturing organization needs to revise a controlled production work instruction after a process change on one assembly line.

The organization wants to:
- draft the revision quickly
- route it through the right review and approval path
- ensure the new version becomes the active release
- keep the superseded version for traceability
- retain the related approval and change record as evidence
- let supervisors ask for current status through Human Ask without bypassing authority boundaries

## Starting State

Before the change:
- the current released document is `PROD-WI-023` version `2.1`
- the document owner is assigned
- the reviewer and approver roles are already defined
- the numbering and metadata standard is active
- retention rules require superseded versions and approval traces to remain retained records

That means the system already has a governed base to work from.

## Step 1: Draft Preparation

AI begins inside the approved boundary.

AI can:
- create the draft from the governed base template
- classify the revision as `Work Instruction`
- carry forward the correct document code
- mark the new item as a draft revision instead of a fresh unrelated document
- prepare revision metadata and change summary
- link the draft to the superseded active version

Humans do not need to manually build the draft structure from zero.

## Step 2: Metadata And Routing Check

Before the draft moves forward, AI checks:
- owner present
- reviewer present
- approver present
- required linked form references present
- version progression appropriate
- release scope correct for the affected line or site

If any required metadata is missing, AI should not silently continue.
It should flag the gap and route the issue for correction.

## Step 3: Review Routing

AI routes the draft to the defined reviewer path.

AI can:
- prepare a review handoff summary
- explain what changed from version `2.1`
- list affected forms or related work instructions
- show whether the draft is still blocked by missing metadata

The reviewer remains the human checkpoint for quality, fit, and operational impact.

## Step 4: Approval Boundary

If review is successful, the document moves to approval.

This is where the core SA-NOM rule remains clear:
- AI moves the workflow forward
- humans confirm the controlled boundary crossing

The approver decides whether the revised work instruction may become the active released version.

AI should not approve the controlled release by itself.

## Step 5: Release

After approval, AI can prepare the release package.

AI can:
- mark the new version as active
- attach release date and approver trace
- link the new version to the superseded version
- prepare the superseded version for retained historical status
- update status views used by Human Ask

The high-risk control decision is already human-confirmed at approval.
So AI can do the routine release preparation work that follows from that approval.

## Step 6: Retention And Records Governance

After release, retention rules apply.

The system should:
- keep the prior version as a retained superseded record when policy requires it
- keep the approval trace as a retained record
- keep the change summary and linked evidence references
- prevent disposal if legal hold, audit hold, or investigation hold exists

This is where document governance becomes record governance, not only publishing.

## Step 7: Human Ask Reporting

Now supervisors, quality leads, or operations managers may call Human Ask.

Typical asks include:
- "Which version of `PROD-WI-023` is active now"
- "What changed from the previous release"
- "Who approved the new release"
- "Is the previous version still retained"
- "Which document updates are still waiting for approval this week"

AI should answer those questions from the governed metadata, routing state, and retention posture.

## What AI Did In This Scenario

Within boundary, AI handled:
- draft preparation
- classification
- numbering and metadata preparation
- route preparation
- change comparison
- release packaging after approval
- retention-state preparation
- Human Ask reporting

This is a large amount of useful work.
The model is not built around making humans click every routine step.

## What Stayed Human-Gated

Humans still owned:
- review judgment
- controlled approval of release
- any exception or waiver to standard route or metadata requirements
- any override to retention or disposal decisions

That is exactly how SA-NOM is supposed to work.

## Why This Scenario Matters

This scenario shows that the Governed Document Center is not only a library concept.
It is an operating workflow where:
- AI does the routine work
- humans confirm only at the real control boundaries
- audit and evidence remain attached
- superseded versions and retained records stay visible and governable

## Safe Public Claim

SA-NOM's Governed Document Center should support governed document release and change-control scenarios where AI handles routine drafting, routing, metadata, release preparation, retention preparation, and Human Ask reporting inside approved boundaries, while humans confirm approval, exception, and other higher-risk control decisions.

## Related Documents

- [GOVERNED_DOCUMENT_CENTER.md](GOVERNED_DOCUMENT_CENTER.md)
- [GOVERNED_DOCUMENT_TEMPLATE_MODEL.md](GOVERNED_DOCUMENT_TEMPLATE_MODEL.md)
- [GOVERNED_DOCUMENT_AUTHORITY_ROUTING.md](GOVERNED_DOCUMENT_AUTHORITY_ROUTING.md)
- [GOVERNED_DOCUMENT_NUMBERING_METADATA.md](GOVERNED_DOCUMENT_NUMBERING_METADATA.md)
- [GOVERNED_DOCUMENT_HUMAN_ASK_REPORTING.md](GOVERNED_DOCUMENT_HUMAN_ASK_REPORTING.md)
- [GOVERNED_DOCUMENT_RETENTION_RECORDS.md](GOVERNED_DOCUMENT_RETENTION_RECORDS.md)
