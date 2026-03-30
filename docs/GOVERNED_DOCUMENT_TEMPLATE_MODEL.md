# Governed Document Template Model

This guide explains the preferred document-template model for SA-NOM's Governed Document Center.

The main idea is not to create a separate hardcoded template for every document type.
The preferred model is one governed base template that can be shaped by rules, metadata, lifecycle, authority, and document-class overlays.

## Why One Base Template Is Better

A document-governance system becomes harder to scale when every department or document class introduces a different template structure with its own rules.

A one-template model is better because it creates:
- one governed document structure
- one metadata shape
- one versioning pattern
- one authority pattern
- one audit model
- one rule-driven way to adapt behavior for different document classes

That means the system stays flexible without becoming fragmented.

## The Core Idea

The recommended model is:

- one governed base template
- document class selected by rule
- lifecycle behavior selected by rule
- numbering and release metadata selected by rule
- owner, reviewer, approver, and retention requirements selected by rule
- additional sections or required fields selected by rule

So the template stays structurally unified, while the operating behavior changes according to governance rules.

## Why This Fits SA-NOM

This is very similar to how `Private Rule Position` works.

In `Private Rule Position`, the platform does not need a completely different engine for every organization-specific hat.
Instead, it keeps one governed model and lets rule logic define the boundaries, actions, and escalation behavior.

The same approach is useful here:
- one document template foundation
- rule-driven shaping for different document classes and operating contexts

That gives the system consistency and flexibility at the same time.

## What The Base Template Should Always Contain

The base template should always support a stable core structure such as:

- document id or code
- title
- document class
- owner
- reviewer
- approver
- version
- status
- effective date
- superseded version or related document
- retention or record-handling hint
- change summary
- body sections
- linked forms, records, or evidence references

This gives every document a common governance spine.

## What Rules Should Control

Rules should decide things such as:

- whether the document behaves as `Policy`, `Standard`, `Procedure`, `Form`, `Template`, or `Record`
- which metadata fields are required
- whether approval is mandatory
- whether release is organization-wide or local
- what numbering pattern applies
- whether a document generates a retained record
- whether a checklist or supporting form is required
- whether legal, audit, or compliance review must be added

This means the template does not need to split into many disconnected structures just to express different governance needs.

## Example Mental Model

Use this simple model:

- `Base template` = the common document skeleton
- `Rule layer` = the logic that decides how the document should behave
- `Lifecycle layer` = draft, review, approve, release, revise, archive
- `Authority layer` = creator, reviewer, approver, owner, viewer, records custodian
- `Audit layer` = evidence of creation, review, release, change, and archive

That is why the design should be read as one governed template with controlled overlays, not as a pile of unrelated forms.

## What AI Should Do In This Model

Inside approved boundaries, AI should be able to:
- generate the base document skeleton
- classify the requested document into the correct class
- apply the correct rule-set for fields and sections
- prepare numbering and revision metadata
- route the document to the right review or approval path
- detect when required metadata, linked forms, or required authorities are missing

This is how the system reduces manual effort while still protecting governance.

## What Should Remain Human-Gated

Humans should still confirm or intervene when the rule layer says the action is beyond the AI boundary.
That often includes:
- final approval of released controlled documents
- overrides to required fields or approval steps
- exceptions to numbering or retention policy
- changes that affect compliance, legal, audit, or public-sector accountability
- release of high-impact organization-wide documents

## Why This Creates Benefit Across The Whole System

A one-template governed model is useful because it helps all sides at once:

- operations get consistency
- document owners get a repeatable structure
- reviewers and approvers get clear control points
- audit teams get traceability
- AI gets one governed structure to work inside
- the organization avoids template sprawl and inconsistent metadata

That is why this model can be more powerful than creating a different template for every case.

## Safe Public Claim

The preferred SA-NOM document-governance model is a single governed base template shaped by rule-driven document class, lifecycle, authority, numbering, and release behavior.

This keeps the system flexible enough for many document types while preserving one controlled governance structure.

## Related Documents

- [GOVERNED_DOCUMENT_CENTER.md](GOVERNED_DOCUMENT_CENTER.md)
- [GOVERNED_DOCUMENT_CLASSES.md](GOVERNED_DOCUMENT_CLASSES.md)
- [GOVERNED_DOCUMENT_LIFECYCLE.md](GOVERNED_DOCUMENT_LIFECYCLE.md)
- [PRIVATE_RULE_POSITION.md](PRIVATE_RULE_POSITION.md)