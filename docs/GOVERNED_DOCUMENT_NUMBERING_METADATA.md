# Governed Document Numbering And Metadata Standard

This guide explains the preferred numbering and metadata standard for SA-NOM's Governed Document Center.

The goal is not only to store a document body.
The goal is to make every controlled document identifiable, routable, reviewable, and auditable across its full lifecycle.

## Why Numbering And Metadata Matter

A governed document system breaks down when documents are hard to identify or compare.

If teams cannot tell which document is current, who owns it, which class it belongs to, or what superseded it, then approval and audit control become weak even if the file itself exists.

That is why numbering and metadata should be treated as part of governance, not as decoration.

## Core Principle

The preferred model is still one governed base template shaped by rules.

That means:
- the base template stays structurally consistent
- numbering rules are selected by document class and organizational policy
- required metadata is selected by rule
- release and retention behavior are attached to the same governed metadata spine

This keeps the system flexible without losing control.

## Minimum Metadata Spine

Every controlled document should support a stable minimum metadata set such as:
- document code
- title
- document class
- owner
- reviewer
- approver
- version
- status
- effective date
- next review date when required
- superseded by or supersedes reference
- retention class or record-handling hint
- confidentiality or access class when required
- change summary
- linked forms, records, or supporting evidence references

This is the governance spine that lets AI and humans operate on the same controlled object.

## Numbering Model

The numbering model should be rule-driven, not manually improvised.

A simple public-safe structure can look like:
- `POL-HR-001`
- `STD-QA-014`
- `PROD-WI-023`
- `FORM-FIN-008`
- `REC-AUD-112`

The specific pattern can vary by organization, but the system should usually encode:
- document class
- domain or department
- sequential identifier
- optional site or unit code when needed

The important point is consistency, not one universal format for every customer.

## Version Syntax

Versioning should be explicit and easy to read.

A practical model is:
- `0.x` for early draft iterations
- `1.0` for first approved release
- `1.1`, `1.2` for minor controlled updates
- `2.0` for major controlled revision

The rule set should determine when a change is minor, major, or only draft-stage work.

## Metadata By Document Class

Rules should require different metadata emphasis depending on class.

Examples:

- `Policy`
  - owner
  - approver
  - effective date
  - organization-wide release scope
  - next review date
- `Standard`
  - owner
  - approver
  - linked procedures or work instructions
  - compliance or audit note when relevant
- `Procedure`
  - owner
  - reviewer
  - approver
  - related form or record references
- `Work Instruction`
  - owner
  - local release scope when needed
  - site or line reference when needed
- `Form`
  - linked procedure or standard
  - revision level
  - record-retention hint when submitted
- `Record`
  - source document reference
  - retention class
  - records custodian
  - archive or disposal rule

This is where rules make the single-template model powerful.

## What Rules Should Decide

Rules should determine:
- what numbering format applies by document class
- whether numbering is global, departmental, site-based, or program-based
- which metadata fields are mandatory
- which metadata fields are optional
- whether a review date is required
- whether confidentiality labeling is required
- whether linked forms or records are mandatory
- whether the document generates a retained record after release or use

This avoids template sprawl while still preserving strict control.

## What AI Should Do

Within approved boundaries, AI should be able to:
- assign the correct numbering pattern
- detect missing required metadata
- prepare draft metadata from the selected rule set
- suggest version progression based on change type
- identify superseded versions and related records
- answer Human Ask questions such as:
  - which version is active
  - what metadata is missing
  - which approver is assigned
  - which documents will be superseded after release

This is the practical work that saves people time.

## What Should Remain Human-Gated

Humans should still confirm when the metadata action exceeds the AI boundary.

That commonly includes:
- approving a first controlled release number
- overriding numbering rules
- changing confidentiality or access class
- changing retention class
- waiving required metadata
- approving major revision jumps
- allowing release with incomplete metadata under exception handling

The system should stay strict where governance risk is real.

## Safe Public Claim

SA-NOM's Governed Document Center should use rule-driven numbering and metadata standards so controlled documents remain identifiable, auditable, and routable across draft, approval, release, revision, and archive states.

## Related Documents

- [GOVERNED_DOCUMENT_CENTER.md](GOVERNED_DOCUMENT_CENTER.md)
- [GOVERNED_DOCUMENT_CLASSES.md](GOVERNED_DOCUMENT_CLASSES.md)
- [GOVERNED_DOCUMENT_LIFECYCLE.md](GOVERNED_DOCUMENT_LIFECYCLE.md)
- [GOVERNED_DOCUMENT_TEMPLATE_MODEL.md](GOVERNED_DOCUMENT_TEMPLATE_MODEL.md)
- [GOVERNED_DOCUMENT_AUTHORITY_ROUTING.md](GOVERNED_DOCUMENT_AUTHORITY_ROUTING.md)
