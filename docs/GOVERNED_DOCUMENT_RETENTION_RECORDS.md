# Governed Document Retention And Records Governance

This guide explains how retention and records governance should work inside SA-NOM's Governed Document Center.

The goal is not only to release documents.
The goal is to control what must be retained, what can be archived, what may be disposed, and when humans must confirm sensitive record actions.

## Why Retention Matters

A governed document system is incomplete if it only manages drafting and approval.

Organizations also need to know:
- which outputs become retained records
- how long records should be kept
- who is responsible for record custody
- what can be archived or disposed
- when legal hold or audit hold should stop disposal
- which actions AI may prepare and which actions humans must approve

That is why retention must be treated as a first-class governance layer.

## Document Versus Record

A controlled document and a retained record are related, but they are not always the same thing.

A simple working distinction is:
- `Document` = a controlled artifact used to define, instruct, or govern work
- `Record` = evidence that work happened, a form was submitted, an approval occurred, or an event was captured

Examples:
- a `Procedure` is a controlled document
- a completed inspection form may become a retained record
- an approval trace for a released policy may become a retained record
- an obsolete version of a standard may remain a retained record for audit history

This distinction is important because not every document is disposable in the same way.

## Core Retention Principle

The retention model should remain rule-driven.

That means rules should determine:
- whether an item is only a working draft
- whether an item becomes a retained record
- how long it should be kept
- whether disposal is allowed after the retention period
- whether legal, audit, compliance, or investigation hold must block disposal
- which authority must confirm archive or dispose actions

This keeps retention aligned with the same governance spine as class, lifecycle, and authority routing.

## Typical Retention States

A practical public-safe model can include:
- `Active`
- `Released`
- `Retained`
- `Archived`
- `On Hold`
- `Approved For Disposal`
- `Disposed`

The exact labels may vary by customer, but the important point is that retention status must be explicit.

## Records Custody

The system should support clear custody responsibility.

Typical roles include:
- `Owner`
- `Approver`
- `Records Custodian`
- `Compliance or Audit Reviewer` when required

The `Records Custodian` role matters because retention, archive, hold, and disposal should not be informal side effects.

## What Rules Should Decide

Rules should determine:
- which document classes or workflows generate retained records
- the retention class for each record type
- default retention period or review point
- whether legal hold or audit hold can be applied
- whether disposal requires dual confirmation
- whether a superseded document must still be retained for traceability
- whether archived material remains searchable through Human Ask

This allows one governed base model to handle many retention patterns without splitting into disconnected systems.

## What AI Should Do

Within approved boundaries, AI should be able to:
- classify outputs into the right retention class
- detect when a released item should become a retained record
- prepare archive packages and retention metadata
- identify records approaching review or disposal thresholds
- flag conflicts such as active legal hold versus scheduled disposal
- answer Human Ask questions such as:
  - which records are on hold
  - which records are due for review
  - which obsolete versions are still retained
  - which records lack a custodian or retention class

This is useful operational work that reduces manual document-admin effort.

## What Should Remain Human-Gated

Humans should still confirm when the retention action exceeds the AI boundary.

That commonly includes:
- overriding retention class
- approving disposal of retained records
- applying or lifting legal hold
- applying or lifting audit hold
- approving exceptions to standard retention period
- authorizing deletion of sensitive or high-risk records

The principle stays the same:
- AI prepares and monitors
- humans authorize sensitive record-state changes

## Legal Hold And Audit Hold

A governed system should be able to stop normal disposal or archive progression when a hold applies.

Examples:
- legal investigation
- audit finding review
- regulatory response
- internal incident review
- dispute or claim handling

When a hold exists, the system should:
- prevent unsafe disposal
- record who applied the hold
- record why the hold exists
- keep the evidence chain intact
- make the hold visible through Human Ask and reporting

## Relationship To Other Document Layers

Use this mental model:
- `Document classes` define what the item is
- `Lifecycle` defines where it is in controlled use
- `Authority routing` defines who may move it
- `Numbering and metadata` define how it is identified
- `Retention governance` defines how long it must survive and under which hold or disposal conditions
- `Human Ask` makes the retained posture visible to humans

This makes retention part of the same governed system, not a disconnected archive silo.

## Safe Public Claim

SA-NOM's Governed Document Center should support rule-driven retention and records governance so documents, approvals, and derived records remain traceable through archive, hold, review, and disposal decisions under explicit authority control.

## Related Documents

- [GOVERNED_DOCUMENT_CENTER.md](GOVERNED_DOCUMENT_CENTER.md)
- [GOVERNED_DOCUMENT_LIFECYCLE.md](GOVERNED_DOCUMENT_LIFECYCLE.md)
- [GOVERNED_DOCUMENT_AUTHORITY_ROUTING.md](GOVERNED_DOCUMENT_AUTHORITY_ROUTING.md)
- [GOVERNED_DOCUMENT_NUMBERING_METADATA.md](GOVERNED_DOCUMENT_NUMBERING_METADATA.md)
- [GOVERNED_DOCUMENT_HUMAN_ASK_REPORTING.md](GOVERNED_DOCUMENT_HUMAN_ASK_REPORTING.md)
