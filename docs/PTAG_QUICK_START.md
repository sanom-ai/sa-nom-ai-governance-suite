# PTAG Quick Start

This guide is the shortest path for a new reader who wants to understand PTAG in this repository without reading the entire codebase first.

Use it when you want to answer three practical questions quickly:
- what PTAG is
- where the main example lives
- which files explain the current implementation baseline

## 1. Start With The Mental Model

PTAG is the policy and role-governance language used by SA-NOM to describe:
- roles
- authority boundaries
- constraints
- policy decisions
- when work can continue automatically and when a human must stay in control

If you want the public framing first, read [PTAG Framework](PTAG_FRAMEWORK.md).
If you want the technical baseline after that, read [PTAG Full Spec](PTAG_FULL_SPEC.md).

## 2. Open One Real PTAG File First

Start with [resources/roles/GOV.ptn](../resources/roles/GOV.ptn).

That file is a compact public-safe example that shows the current canonical PTAG text format in one place.
It includes:
- document headers such as `language`, `module`, `version`, `owner`, and `context`
- a `role` block
- an `authority` block
- a `constraint` block
- several `policy` blocks

A good first reading order is:
1. headers
2. `role GOV`
3. `authority GOV`
4. `constraint GOV_BOUNDARY`
5. the `policy` blocks that decide approve, escalate, or wait for human action

## 3. Read PTAG Like A Governed AI Contract

When you read PTAG, use this simple interpretation:
- `role` says who exists and what that role is for
- `authority` says what the role may or may not do
- `constraint` says what boundaries cannot be crossed
- `policy` says how decisions are made through a single `WHEN ... THEN ...` trigger rule for a specific action or situation

A practical reading shortcut for `policy` blocks is:

```ptag
policy BRAND_GUARD {
  WHEN action == send_customer_reply AND resonance_score < 0.85
  THEN rewrite_tone("diplomatic"), require_approval("reviewer")
  ELSE approve
}
```

This is the easiest way to connect PTAG back to the SA-NOM operating idea:
- AI can work inside defined boundaries
- sensitive actions can require human approval
- governance stays explicit instead of being hidden inside runtime code

## 4. Inspect The Current Reference Implementation

After reading `GOV.ptn`, inspect the PTAG implementation surface in this order:
1. `sa_nom_governance/ptag/ptag_parser.py`
2. `sa_nom_governance/ptag/ptag_validator.py`
3. `sa_nom_governance/ptag/ptag_semantic.py`
4. `sa_nom_governance/ptag/role_loader.py`
5. `sa_nom_governance/ptag/role_compiler.py`

That sequence helps because you move from syntax parsing to validation and then to semantic/runtime-facing usage.

## 5. Know The Current Public Syntax Position

The current canonical PTAG format in this repository is the existing PTAG text format used in `resources/roles/*.ptn`.

This quick start intentionally does not treat YAML as the main format yet.
YAML may become a future direction, but the public baseline today should stay aligned with the parser and validator that already exist in the repository.

## 6. Follow A Five-Minute Study Path

If you only have a few minutes, use this sequence:
1. read [PTAG Framework](PTAG_FRAMEWORK.md)
2. open [resources/roles/GOV.ptn](../resources/roles/GOV.ptn)
3. read [PTAG Full Spec](PTAG_FULL_SPEC.md)
4. inspect `sa_nom_governance/ptag/ptag_parser.py`
5. inspect `sa_nom_governance/ptag/ptag_validator.py`

That path is enough to understand what PTAG is, what it currently looks like, and where the repository implementation begins.

## 7. Where To Go Next

Choose the next document based on what you need:
- If you want the public positioning, stay with [PTAG Framework](PTAG_FRAMEWORK.md).
- If you want a guided walk through the example set, go to [PTAG Examples](PTAG_EXAMPLES.md).
- If you want syntax and validation detail, go to [PTAG Full Spec](PTAG_FULL_SPEC.md).
- If you want more example files directly, inspect `resources/roles/`.
- If you want to help improve PTAG, read [CONTRIBUTING](../CONTRIBUTING.md).

## Summary

PTAG quick start is simple:
- read the framework guide
- open one real example
- read the full spec
- inspect parser and validator

That is the shortest repository path from "What is PTAG?" to "I can now study and improve it with confidence."
