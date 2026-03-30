# Governed Document Authority And Approval Routing

This guide explains how authority and approval routing should work inside SA-NOM's Governed Document Center.

The goal is not only to know that a document exists.
The goal is to know who is allowed to move it, who must confirm it, and when AI should stop and hand the decision to a human.

## Why Routing Matters

A governed document system fails when routing is informal.

If a team does not know who can review, approve, release, or override a document, then version control alone is not enough.

Authority routing matters because the organization needs to know:
- who can create a draft
- who must review it
- who has approval power
- when release can happen
- when a route must escalate
- when AI must stop because the next action exceeds its boundary

## Core Principle

SA-NOM is designed so AI can do the work inside an approved boundary, while humans step in only when the task goes beyond that boundary.

That means document routing should follow the same rule:
- AI can prepare, classify, route, remind, summarize, and detect gaps
- humans confirm approvals, exceptions, waivers, and higher-risk routing decisions

The system should not be designed around humans clicking every step manually.
It should be designed around bounded AI work with explicit human control points.

## Core Authority Roles

The authority model should be simple and clear.

Typical roles include:
- `Creator`
- `Reviewer`
- `Approver`
- `Owner`
- `Publisher` or `Release Authority`
- `Viewer`
- `Records Custodian`

Organizations may add more specialized roles through PTAG and Private Rule logic, but the public model should remain understandable.

## Typical Routing Pattern

The common route for a controlled document should look like this:

1. `Create`
2. `Review`
3. `Approve`
4. `Release`
5. `Revise` or `Archive`

In practice, the system should know:
- which role is responsible for the current step
- which role is next
- whether the next step is AI-allowed
- whether the next step is human-gated
- which evidence must be attached before progression

## Example Routing Logic

A simple example looks like this:

- `Creator` prepares the draft
- `Reviewer` checks completeness and fit
- `Approver` confirms controlled use
- `Release Authority` publishes the active version
- `Records Custodian` controls retention after release or obsolescence

Some organizations may let one person hold multiple roles.
Others may split them for stronger control.

The important point is not the org chart title.
The important point is that authority is explicit and routable.

## What Rules Should Decide

Rules should determine:
- whether review is required
- whether one reviewer or multiple reviewers are required
- whether approval is mandatory
- who can act as approver for each document class
- whether release can happen automatically after approval or requires a separate release authority
- when legal, audit, compliance, or executive review must be inserted
- when a route must escalate instead of continuing
- which actions AI may perform without asking for human confirmation

This keeps routing controlled without hardcoding separate flows for every department.

## What AI Should Do

Within approved boundaries, AI should be able to:
- classify the document and apply the right route
- assign the next role according to the approved rule set
- prepare handoff notes for reviewers and approvers
- summarize changes since the previous version
- detect missing metadata, missing linked forms, or missing approvals
- remind the next authority that a document is waiting
- answer Human Ask questions such as:
  - what is pending
  - who owns the next step
  - what blocks release
  - which version is active

This is where the system saves labor.
Humans should not need to manually orchestrate routine routing every time.

## What Should Remain Human-Gated

Humans should still confirm when the next action exceeds the AI boundary.

That commonly includes:
- approving controlled documents
- waiving required review
- releasing high-impact policies or standards
- overriding numbering, metadata, or retention rules
- bypassing a required approver
- approving urgent exceptions outside the normal route
- retiring or deleting controlled records

The principle is simple:
- AI moves the workflow
- humans authorize the boundary crossings

## Escalation And Exception Routing

Routing should not assume the happy path is always available.

The system should support escalation when:
- the required approver is missing
- review takes too long
- required evidence is missing
- a document class triggers legal, audit, or compliance exposure
- the requested release route exceeds the approved authority pattern

At that point, SA-NOM should:
- stop the next unsafe action
- record the route condition
- notify the right human path
- keep the evidence chain intact

## Relationship To PTAG And Private Rule Logic

PTAG and Private Rule logic are what make routing flexible without making it chaotic.

Use this mental model:
- `PTAG` defines policy logic and authority boundaries
- `Private Rule Position` defines organization-specific hats when needed
- `Governed Document Template Model` provides one stable document structure
- `Authority Routing` determines how the document moves between controlled human checkpoints

That is why authority routing should be rule-driven, not improvised by email habits.

## Safe Public Claim

SA-NOM's Governed Document Center should use explicit authority and approval routing so AI can move routine document work inside approved boundaries while humans confirm approval, exception, and higher-risk control decisions.

## Related Documents

- [GOVERNED_DOCUMENT_CENTER.md](GOVERNED_DOCUMENT_CENTER.md)
- [GOVERNED_DOCUMENT_CLASSES.md](GOVERNED_DOCUMENT_CLASSES.md)
- [GOVERNED_DOCUMENT_LIFECYCLE.md](GOVERNED_DOCUMENT_LIFECYCLE.md)
- [GOVERNED_DOCUMENT_TEMPLATE_MODEL.md](GOVERNED_DOCUMENT_TEMPLATE_MODEL.md)
- [PRIVATE_RULE_POSITION.md](PRIVATE_RULE_POSITION.md)
