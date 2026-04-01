# HITL Role Packs And Use Cases

This document defines the first public-safe role-pack and use-case surface for SA-NOM's governed human-in-the-loop operations layer.

It should be read after:
- [Governed Human-In-The-Loop Operations](GOVERNED_HITL_OPERATIONS.md)
- [Minimal Human Approval Surface](MINIMAL_HUMAN_APPROVAL_SURFACE.md)
- [Governed HITL Human Ask Reporting](GOVERNED_HITL_HUMAN_ASK_REPORTING.md)

The purpose of this guide is to make the HITL model feel concrete in realistic organizational scenarios without exploding into a large catalog of separate packs.

## Why This Document Exists

Architecture, approval surfaces, and reporting models are necessary, but organizations also need to see where the model applies.

They want to know:
- what kind of work enters the HITL lane
- who is expected to approve or escalate
- what evidence matters
- why the decision cannot remain fully autonomous
- what a realistic operational story looks like

This document answers those questions with a small number of public-safe use cases.

## Core Design Rule

This guide does not try to provide every possible role pack.

It provides a compact set of examples that cover distinct HITL patterns:
- external/customer-sensitive resolution work
- legal/commercial review work
- operational recovery or incident work

Those patterns are broad enough to matter and small enough to stay readable.

## Included Use-Case Lanes

The initial public-safe HITL use-case set includes:
- `Customer Complaint Resolver`
- `Contract Reviewer`
- `Incident Recovery Lead`

These are not final production packs for every organization.
They are example lanes that show how the governed HITL model behaves in practice.

## 1. Customer Complaint Resolver

### What This Lane Is For

This lane is for customer-facing cases where AI can prepare summaries, route the complaint, gather evidence, and recommend next steps, but final customer-impacting actions may still require human approval.

### Typical AI Work

AI can:
- summarize the complaint
- classify severity and product/service context
- collect related records or prior incidents
- prepare a proposed response path
- flag whether compensation, legal sensitivity, or reputation risk is involved

### Typical Human Trigger Points

Human review or approval should be required when:
- the case has legal exposure
- compensation or refund exceeds a threshold
- the proposed action affects customer rights or commitments
- escalation reaches executive or regulator-sensitive territory

### Typical Human Roles

- `approver`: customer support owner or service manager
- `reviewer`: quality or legal reviewer when needed
- `escalation_owner`: executive owner or complaint authority owner for exceptional cases

### Evidence And Audit Expectations

Useful evidence includes:
- original complaint summary
- customer history or incident references
- proposed response
- rationale for approval, rejection, or escalation

### Why This Lane Matters

This example shows how HITL protects external-facing actions without forcing humans to do all the preparation work manually.

## 2. Contract Reviewer

### What This Lane Is For

This lane is for contract, clause, or approval-sensitive commercial review where AI can analyze and prepare, but final acceptance, exception, or commitment decisions remain human-owned.

### Typical AI Work

AI can:
- summarize key clauses
- highlight non-standard terms
- compare contract posture against expected templates or policy boundaries
- prepare a risk summary and recommended path
- identify where legal or executive attention is required

### Typical Human Trigger Points

Human review or approval should be required when:
- non-standard legal terms appear
- financial commitments exceed delegated authority
- indemnity, liability, or termination posture becomes sensitive
- an exception or waiver is proposed

### Typical Human Roles

- `approver`: legal or commercial owner with delegated review authority
- `reviewer`: finance, procurement, or specialist legal reviewer
- `escalation_owner`: executive owner for high-impact commitments or exceptions

### Evidence And Audit Expectations

Useful evidence includes:
- clause summary
- deviation or exception notes
- financial and legal risk posture
- rationale for approval, rejection, or escalation

### Why This Lane Matters

This example shows how HITL supports serious commercial review without pretending AI should sign or approve sensitive agreements on its own.

## 3. Incident Recovery Lead

### What This Lane Is For

This lane is for incident response or operational recovery where AI can help assess, summarize, route, and prepare recovery actions, but human authority remains explicit for high-impact production decisions.

### Typical AI Work

AI can:
- summarize the incident state
- classify severity and affected systems
- prepare candidate recovery steps
- identify operational dependencies and rollback implications
- assemble a meeting-ready recovery posture summary

### Typical Human Trigger Points

Human review or approval should be required when:
- production-impacting recovery actions are proposed
- service interruption crosses a severity threshold
- rollback, shutdown, or emergency exception decisions are needed
- the incident reaches external reporting or regulator-sensitive posture

### Typical Human Roles

- `approver`: operations or incident owner
- `reviewer`: platform, security, or quality reviewer depending on the incident
- `escalation_owner`: executive or crisis authority owner for major incidents

### Evidence And Audit Expectations

Useful evidence includes:
- incident timeline summary
- severity and impact classification
- proposed recovery path
- prior review notes and escalation rationale

### Why This Lane Matters

This example shows how HITL helps organizations trust AI in operational recovery without surrendering high-trust incident authority.

## Common HITL Pattern Across All Lanes

Even though the business context changes, the governed pattern stays consistent:
- AI prepares and structures the case
- trigger class determines whether human review is required
- the approval surface lets a human inspect and decide
- Human Ask provides governed visibility and meeting posture
- audit captures the rationale and state transition history

This consistency is one of the strongest reasons to treat HITL as one operational layer instead of a set of isolated exceptions.

## What These Role Packs Are Not

These role packs are not:
- full production policy packs for every organization
- legal, financial, or operational advice
- proof that AI should own final authority in high-risk scenarios
- a claim that one pack fits every company unchanged

They are public-safe examples that make the governed HITL model easier to understand and evaluate.

## Suggested Evaluation Sequence

A strong evaluation sequence is:
1. read the HITL architecture layer
2. read the minimal approval surface
3. read the Human Ask reporting model
4. use these role-pack examples to see how the same HITL model applies across different work types

This progression helps the operational model feel reusable rather than one-off.

## Summary

The first HITL role-pack set gives SA-NOM a realistic use-case surface for governed customer, legal, and incident work.

That makes `v0.5.0` feel closer to something an organization can seriously evaluate, because the repo now shows not only how the HITL model is designed, but also where it can be used responsibly.
