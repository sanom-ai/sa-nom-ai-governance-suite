# Governed Document Center

This guide explains the Governed Document Center as a controlled document system inside SA-NOM.

It should not be read as a simple file-storage area.
It should be read as a governed operating layer for creating, organizing, approving, publishing, using, and retaining organizational documents under role-based authority and audit-ready control.

## What It Is

The Governed Document Center is SA-NOM's document-governance layer for policies, standards, procedures, forms, templates, work instructions, and records.

In simple terms, it is the part of the system that helps an organization answer:
- what document exists
- who is allowed to create it
- who is allowed to review and approve it
- which version is active
- which documents are obsolete or archived
- which records should be retained as evidence

That means the goal is not only to store files.
The goal is to keep documents governed, traceable, usable, and aligned with operational authority.

## Why It Fits SA-NOM

SA-NOM is designed so AI can do the work inside an approved boundary, while humans step in only when the task goes beyond that boundary.

The same logic fits document governance.

Inside the Governed Document Center:
- AI should be able to help draft, classify, organize, route, and prepare documents within policy boundaries
- humans should step in when approval, exception handling, high-risk publication, or off-boundary changes are required

That makes the Document Center consistent with the broader SA-NOM operating model:
- AI works
- humans confirm only when the boundary is exceeded
- audit and evidence remain attached

## Document Classes

The Governed Document Center should support classic document classes such as:

- `Policy`
- `Standard`
- `Procedure`
- `Work Instruction`
- `Form`
- `Template`
- `Checklist`
- `Record`

This makes the concept usable for both enterprise and public-sector document structures, including ISO-style document systems.

## Lifecycle

The intended document lifecycle is:

- `Draft`
- `Review`
- `Approve`
- `Release`
- `Revise`
- `Archive / Obsolete`

That means the system is not only about authorship.
It is about controlled progression from creation into approved operational use.

## Authority Model

The Governed Document Center should support clear authority roles such as:

- `Creator`
- `Reviewer`
- `Approver`
- `Owner`
- `Viewer`
- `Records Custodian` or equivalent retention authority

These roles can be mapped through PTAG, runtime authority boundaries, and Human Ask reporting patterns.

## What AI Should Do

Within approved boundaries, AI should be able to:

- draft document skeletons from approved templates
- classify documents into the right document class
- prepare revision summaries and change notes
- route documents for review
- answer structured questions about released documents through Human Ask
- link records and evidence to the correct workflow context
- help detect gaps such as missing owners, missing reviewers, or missing linked forms

This is where the system saves human time.
Humans should not need to perform every routine document step manually.

## What Should Remain Human-Gated

Humans should still confirm or approve when the task goes beyond the AI boundary.
That may include:

- final approval of controlled documents
- release of high-impact policies or standards
- exception handling outside approved templates
- retention overrides or deletion of controlled records
- changes that affect legal, regulatory, or audit posture
- organization-wide publication of sensitive document sets

This keeps the Document Center aligned with SA-NOM's core principle of bounded autonomy.

## ISO And Public-Sector Fit

The Governed Document Center should be usable across:

- private enterprises with ISO-style document control
- factories with standards, procedures, work instructions, forms, and records
- public-sector organizations that need formal approval chains and document accountability
- regulated environments that need version control, evidence retention, and approval history

That is why the concept should be presented as broader than a policy library and more controlled than simple storage.

## Relationship To Other SA-NOM Layers

Use this mental model:

- `PTAG` defines document roles, authority boundaries, and policy conditions
- `Governed Document Center` manages the controlled document lifecycle and document classes
- `Human Ask` lets humans call AI into document reporting, lookup, and status review
- `Authority Guard` stops actions that exceed approved authority
- `Audit Chain` records what was created, reviewed, approved, changed, or archived
- `Evidence Pack` can connect document state to operating evidence and compliance review

This makes the Document Center a natural extension of the current platform, not a disconnected storage feature.

## Safe Public Claim

The correct public claim is:

SA-NOM's Governed Document Center is a controlled system for creating, organizing, approving, publishing, and retaining policies, standards, procedures, forms, templates, and records under role-based authority and audit-ready governance.

## What This Does Not Mean

This does not mean:
- every enterprise document-management feature is already implemented in the public baseline today
- the system should be presented as only a file repository
- AI should publish or approve every document autonomously

The intended model is governed document work, not uncontrolled auto-publication.

## Related Guides

- [Governed Document Classes](GOVERNED_DOCUMENT_CLASSES.md)
- [Governed Document Lifecycle](GOVERNED_DOCUMENT_LIFECYCLE.md)

## Summary

The Governed Document Center is the document-governance layer that fits naturally into SA-NOM's operating model.

It is designed so AI can do routine document work inside defined boundaries, while humans step in only when approval, exception handling, or higher-risk control decisions are required.