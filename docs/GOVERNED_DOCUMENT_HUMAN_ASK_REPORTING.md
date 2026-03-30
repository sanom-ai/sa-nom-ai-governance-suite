# Governed Document Human Ask And Reporting

This guide explains how Human Ask should work for SA-NOM's Governed Document Center.

The goal is not only to store or route documents.
The goal is to let humans call AI into document reporting, lookup, and status review without losing governance boundaries.

## Why Human Ask Matters Here

Document governance creates a lot of routine questions.

People need to ask things such as:
- which version is active
- what is waiting for approval
- who owns the next step
- what changed from the previous version
- which documents are overdue for review
- which forms or records are linked to a released procedure

Those are exactly the kinds of tasks where AI should help heavily.

## Core Principle

`Human Ask` is human-initiated reporting and meeting behavior.

That means people call AI into the document process when they want:
- a status report
- a lookup result
- a summary
- a meeting-ready document posture view
- a structured answer about released or in-flight documents

It does not mean AI is asking humans for permission at every step.
The normal mode is still:
- AI does routine document work in boundary
- humans call AI when they want reporting or review
- humans confirm only when approval, waiver, exception, or higher-risk release decisions are required

## What Human Ask Should Be Able To Answer

Inside approved authority boundaries, Human Ask should be able to answer questions such as:
- what is the current active version of this document
- which draft is waiting for review
- who is the assigned owner, reviewer, or approver
- what documents are overdue for review or refresh
- which policy or standard this form belongs to
- what changed between the last two versions
- which documents are blocked because metadata or approval is missing
- which records are linked to a released document
- which obsolete documents were superseded by the current release

These are high-value information tasks that consume human time if done manually.

## Typical Human Ask Use Cases

Examples include:

- `Document status ask`
  - "Show the status of all controlled HR policies waiting for approval"
- `Version ask`
  - "Which QA standard is currently active and what superseded the prior version"
- `Owner ask`
  - "Who owns this procedure and who is the current approver"
- `Gap ask`
  - "Which released procedures are missing linked forms or records"
- `Review ask`
  - "Which policies will hit next review date this quarter"
- `Meeting ask`
  - "Prepare a document-governance posture summary for the compliance meeting"

This is where Human Ask turns the Document Center into an operating system, not just a controlled archive.

## What AI Should Do

Within approved boundaries, AI should be able to:
- retrieve the right released or in-flight document context
- summarize document status and workflow posture
- compare current and previous versions
- explain which authority checkpoint is blocking release
- group documents by class, owner, status, or review date
- prepare meeting-ready summaries
- answer role-scoped questions without exposing unauthorized content

This is the practical reporting layer that makes governed documents usable in daily work.

## What Should Remain Bounded

Human Ask should still respect authority, confidentiality, and release boundaries.

That means AI should not expose:
- restricted draft content to unauthorized viewers
- confidential document details outside policy
- approval actions that the asking user is not authorized to trigger
- unreleased content as if it were the active version
- retention-protected records to a user without the right view authority

Human Ask is a governed reporting layer, not a shortcut around access control.

## Relationship To Authority Routing

Human Ask works best when it can read the same governed structure used by the rest of the document system.

That includes:
- document class
- lifecycle state
- owner, reviewer, approver, and custodian roles
- numbering and version metadata
- release and supersession references
- linked forms, records, and evidence

That is why the Human Ask layer should be attached to the same governance spine rather than built as a separate search silo.

## Meeting And Reporting Pattern

A useful mental model is:
- the document workflow keeps moving through routing and approval
- humans call Human Ask when they need visibility
- AI returns structured summaries, status, gaps, and next-step posture
- humans intervene only when the result reveals a true approval, exception, or control decision

This keeps Human Ask aligned with SA-NOM's core design.

## Safe Public Claim

SA-NOM's Governed Document Center should support Human Ask as a governed reporting and lookup layer so humans can call AI into document status, version, review, and meeting workflows without bypassing authority, release, or confidentiality boundaries.

## Related Documents

- [GOVERNED_DOCUMENT_CENTER.md](GOVERNED_DOCUMENT_CENTER.md)
- [GOVERNED_DOCUMENT_AUTHORITY_ROUTING.md](GOVERNED_DOCUMENT_AUTHORITY_ROUTING.md)
- [GOVERNED_DOCUMENT_NUMBERING_METADATA.md](GOVERNED_DOCUMENT_NUMBERING_METADATA.md)
- [PRIVATE_RULE_POSITION.md](PRIVATE_RULE_POSITION.md)
