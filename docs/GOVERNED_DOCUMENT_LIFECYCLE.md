# Governed Document Lifecycle

This guide explains the lifecycle and authority model for SA-NOM's Governed Document Center.

It is meant to show how documents should move under governance, not just where they are stored.

## Why Lifecycle Matters

A document system is not governed just because files are versioned.

A governed lifecycle matters because the organization needs to know:
- who is allowed to create a draft
- when review is required
- who can approve release
- what counts as the active version
- how revisions and obsolete documents are controlled
- which document actions should remain human-gated

## Lifecycle States

### Draft

`Draft` is the working state where a document is being created or revised.

AI can help heavily here by:
- preparing structure from approved templates
- drafting sections within approved boundaries
- classifying the document correctly
- collecting missing metadata

### Review

`Review` is the state where the document is being checked for quality, completeness, and fit.

AI can route and summarize, but human review is still important when:
- the content is high impact
- policy interpretation is sensitive
- the draft crosses legal, audit, regulatory, or organizational boundaries

### Approve

`Approve` is the formal decision point that confirms the document is allowed to progress toward controlled use.

This should remain human-gated for important controlled documents.

### Release

`Release` is the state where the document becomes the approved active version for organizational use.

At this point, the system should know:
- version
- owner
- approval trace
- release date
- superseded version if any

### Revise

`Revise` is the controlled return to draft or review for changes to an already released document.

The important point is that revision should not erase history.
The system should preserve version trace and reason-for-change context.

### Archive / Obsolete

`Archive / Obsolete` is the state where a document is no longer the active operational version.

The old document may still need to be retained for:
- audit evidence
- historical traceability
- legal or regulatory reasons
- controlled record retention

## Authority Roles

A governed lifecycle usually depends on authority roles such as:

- `Creator`
- `Reviewer`
- `Approver`
- `Owner`
- `Viewer`
- `Records Custodian`

These roles should be mapped through policy and runtime authority rather than informal team habits.

## What AI Should Do In The Lifecycle

Within approved boundaries, AI should be able to:
- prepare draft structures
- classify lifecycle state
- route work to the right reviewer or approver
- summarize changes between versions
- detect missing metadata or missing linked forms
- answer status questions through Human Ask
- prepare release or archive packages for human confirmation

This is where AI reduces document workload without replacing governance.

## What Should Stay Human-Gated

Humans should confirm or intervene when the action goes beyond the AI boundary.
That often includes:
- approving controlled release
- waiving required review
- authorizing retention overrides
- approving deletion of retained records
- handling off-template exceptions
- approving documents with legal, regulatory, or organization-wide impact

## Suggested Operating Rule

A simple operating rule for SA-NOM is:

- AI should do routine document work inside approved boundaries
- humans should step in only for approval, exception, or higher-risk control decisions

This keeps the Document Center aligned with the rest of the platform.

## Related Documents

- [GOVERNED_DOCUMENT_CENTER.md](GOVERNED_DOCUMENT_CENTER.md)
- [GOVERNED_DOCUMENT_CLASSES.md](GOVERNED_DOCUMENT_CLASSES.md)