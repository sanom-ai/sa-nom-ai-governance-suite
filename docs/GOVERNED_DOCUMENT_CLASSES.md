# Governed Document Classes

This guide explains the core document classes for SA-NOM's Governed Document Center.

The goal is to make document governance readable, reusable, and consistent across enterprise and public-sector environments.

## Why Document Classes Matter

A governed document system becomes hard to scale when every file is treated as the same thing.

Document classes matter because they help the organization answer:
- what this document is for
- who should own it
- how it should move through review and approval
- whether it should be released, filled out, retained, or archived

## Core Classes

### Policy

A `Policy` defines direction, rules, or mandatory principles that the organization expects people and systems to follow.

Typical examples:
- AI usage policy
- access-control policy
- document-control policy
- retention policy

A policy should usually be high-level, authority-backed, and formally approved.

### Standard

A `Standard` defines the required structure, format, or rule set that must be followed consistently.

Typical examples:
- naming standard
- classification standard
- approval metadata standard
- versioning standard

A standard turns policy intent into repeatable structure.

### Procedure

A `Procedure` defines the approved step-by-step way to perform a recurring activity.

Typical examples:
- document review procedure
- deviation handling procedure
- controlled release procedure
- change-request procedure

A procedure should answer what sequence the organization expects people or systems to follow.

### Work Instruction

A `Work Instruction` explains how a specific task should be performed in more operational detail than a procedure.

Typical examples:
- how to prepare a revision package
- how to classify a document record
- how to route a draft for review

Work instructions are often team-specific or task-specific.

### Form

A `Form` is a controlled input document used to capture structured information.

Typical examples:
- document change request form
- approval request form
- deviation request form
- document issue log form

Forms support consistency and auditability because they collect information in a repeatable shape.

### Template

A `Template` is a controlled starting structure used to create a document of another class.

Typical examples:
- policy template
- procedure template
- meeting-minutes template
- corrective-action template

Templates help AI and humans create documents faster without drifting away from the approved structure.

### Checklist

A `Checklist` is a controlled verification list used to confirm that required steps or conditions have been completed.

Typical examples:
- release checklist
- review checklist
- readiness checklist
- archive checklist

Checklists are especially useful when humans only need to confirm higher-risk items after AI has already prepared the routine work.

### Record

A `Record` is evidence that something happened.

Typical examples:
- approved form submission
- released version history
- review comments
- approval log
- distribution evidence

Records are usually retained as evidence rather than edited as live working documents.

## How The Classes Relate

A simple mental model is:

- `Policy` says what must be respected
- `Standard` says what structure must be used
- `Procedure` says what sequence must be followed
- `Work Instruction` says how a task is performed in detail
- `Form` captures structured input
- `Template` provides the approved starting structure
- `Checklist` verifies completion
- `Record` proves that something happened

## AI Fit

Inside the Governed Document Center, AI should be able to:
- identify the correct class for a document request
- start from the right template
- route the draft into the correct lifecycle
- keep records and working documents separated properly

That is important because a governed document system should not let every file behave the same way.

## Related Documents

- [GOVERNED_DOCUMENT_CENTER.md](GOVERNED_DOCUMENT_CENTER.md)
- [GOVERNED_DOCUMENT_LIFECYCLE.md](GOVERNED_DOCUMENT_LIFECYCLE.md)