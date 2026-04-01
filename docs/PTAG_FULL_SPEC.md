# PTAG Full Spec

This document is the current public technical specification companion to [PTAG Framework](PTAG_FRAMEWORK.md).

It describes the PTAG surface that is actually represented in this repository today.

## Specification Scope

This document covers:
- current document structure
- current header model
- current supported top-level block types
- current public syntax shape
- current validation behavior visible from the parser and validator
- current public example paths in the repository

This document does not claim that PTAG is finished or frozen.
It captures the current public baseline.

## Canonical Public Syntax

The canonical public syntax in this repository is the current PTAG text format used in `.ptn` files.

Example header + block shape:

```ptag
language "PTAG"
module "GOV_CORE"
version "1.0.0"
owner "Executive Owner"
context "SA-NOM AI Director"

role GOV {
  title: "GovAI-1"
  stratum: 0
  reports_to: NONE
}
```

## Document Model

A PTAG document has two major parts:
- headers
- blocks

The parser reads non-empty lines, collects recognized headers at the top level, and then collects block bodies between `{` and `}`.

## Headers

### Recognized Header Keys

The parser currently recognizes:
- `language`
- `module`
- `version`
- `owner`
- `context`

### Required Header Keys

The validator currently requires:
- `language`
- `module`
- `version`
- `owner`

If one or more required headers are missing, validation raises an error.

### Header Example

```ptag
language "PTAG"
module "GOV_CORE"
version "1.0.0"
owner "Executive Owner"
context "SA-NOM AI Director"
```

## Blocks

### Canonical Block Shape

```ptag
block_type block_id {
  ...content...
}
```

### Supported Top-Level Block Types

The validator currently allows:
- `role`
- `authority`
- `constraint`
- `policy`
- `dictionary`
- `decision`
- `flow`

If a block type falls outside this set, validation raises an error.

## Block Semantics

### Role

The `role` block defines the identity and operating shape of a governed role.

Example:

```ptag
role GOV {
  title: "GovAI-1"
  stratum: 0
  reports_to: NONE
  escalation_to: EXEC_OWNER
  safety_owner: EXEC_OWNER
  purpose: "Govern, approve, supervise, and stop the system when necessary."
  business_domain: "governance"
  handled_resources: [engine, role_card, audit]
}
```

Typical fields seen in public examples include:
- string values
- numeric values
- list values

### Authority

The `authority` block defines what a role can do, cannot do, or can do only with explicit conditions.

Example:

```ptag
authority GOV {
  allow: approve_policy, suspend_role, emergency_stop, review_audit
  deny: bypass_ethics
  require human_override for approve_group_policy
}
```

Supported public semantics currently include:
- `allow`
- `deny`
- `require X for Y`

### Constraint

The `constraint` block expresses broader boundary rules.

Example:

```ptag
constraint GOV_BOUNDARY {
  forbid GOV to bypass_ethics
  require human_override for approve_group_policy
}
```

### Policy

The `policy` block defines decision logic tied to actions and conditions.

Example:

```ptag
policy GOV_REVIEW_AUDIT {
  when action == review_audit
  and risk_score <= 0.60
  then approve
  else escalate
}
```

Example outcomes already visible in repository examples include:
- `approve`
- `escalate`
- `wait_human`

### Dictionary, Decision, Flow

The validator currently accepts `dictionary`, `decision`, and `flow` blocks as part of the public PTAG block model.

They represent:
- shared vocabulary
- explicit decision structures
- workflow progression structures

Their deeper public reference surface can continue to expand in future PTAG milestones.

## Validation Behavior

## Structural Validation

The validator currently checks that:
- required headers exist
- the document contains at least one block
- each block uses a supported top-level type

Failure in these areas raises a validation error.

## Semantic Validation

The semantic validator currently checks that:
- at least one role exists
- each role has a corresponding authority block
- no authority block exists for an unknown role
- governed actions are compared against policy and constraint coverage

## Policy Coverage Gap Signal

The semantic validator can emit a `POLICY_COVERAGE_GAP` warning when an allowed or required action is not covered by a policy or constraint.

This is one of the most important current PTAG public signals because it helps teams detect governance gaps before runtime trust assumptions drift silently.

## Repository Example Surface

Current public-safe PTAG examples include:
- `resources/roles/GOV.ptn`
- `resources/roles/LEGAL.ptn`
- `resources/roles/core_terms.ptn`

A good reading order is:
1. `resources/roles/GOV.ptn`
2. `sa_nom_governance/ptag/ptag_parser.py`
3. `sa_nom_governance/ptag/ptag_validator.py`
4. `sa_nom_governance/ptag/ptag_semantic.py`

## YAML Position

YAML may become a useful future PTAG interchange or authoring format.

However, this document does not declare YAML the canonical public PTAG syntax today, because:
- current examples are still `.ptn`
- current parser behavior still centers on the PTAG text format
- the repository does not yet expose a YAML-first PTAG implementation path

If a future milestone adopts YAML as the primary syntax, the implementation, examples, and validation tooling should change first, and only then should the canonical public syntax claim change.

## Package And Installation Position

This repository currently exposes PTAG through the SA-NOM codebase itself.

This document does not claim that there is already a separate standalone `ptag` package for installation. If such a package is created later, that should be documented as a separate milestone.

## Contribution Expectations

When PTAG changes affect syntax, parser behavior, validator behavior, semantic behavior, or public examples:
- update `docs/PTAG_FRAMEWORK.md`
- update this spec document when the technical public surface changes
- add or update tests in `_support/tests`
- keep examples public-safe and readable

## Summary

This document captures the current public PTAG technical baseline in the repository.

It is intended to help readers understand the language as it exists today, while leaving room for later milestones to deepen tooling, examples, validation, and authoring formats.
