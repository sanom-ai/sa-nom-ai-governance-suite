# PTAG Framework

This guide explains PTAG as the public policy and role-governance language used inside SA-NOM.

It should be read as both:
- a public explanation of what PTAG is
- a repository-facing guide to the PTAG materials already available in this codebase

## Current Status (April 1, 2026)

PTAG is now public in this repository.

PTAG was previously described here as a proprietary framework. As of April 1, 2026, the PTAG documentation, reference implementation, and public-safe examples in this repository are being presented as a public repository surface under the repository's `AGPL-3.0-only` license posture.

That means developers, organizations, and public-sector teams can study PTAG, use it, evaluate it, adapt it within the repository license terms, and contribute improvements through the normal repository workflow.

This public opening should be read as a real repository change, not only a wording change:
- PTAG now has a clearer public framework document
- the repository points readers to the current parser, validator, semantic, and example files
- contribution guidance now covers PTAG-specific changes
- release and announcement materials for the PTAG public-opening phase are now part of the docs set

## What PTAG Is

PTAG is the policy and role-governance language used inside SA-NOM to define roles, authority boundaries, constraints, policy logic, and decision-ready control structure in a readable form.

Inside `policy` blocks, the canonical control structure is now a single `WHEN ... THEN ...` trigger grammar, with additional `AND` clauses and an optional `ELSE` fallback for governed runtime decisions.

In practical terms, PTAG is the layer that answers:
- what role exists
- what that role is allowed to do
- what it is denied from doing
- what conditions must be satisfied before sensitive actions can proceed
- when work can continue automatically and when human control is still required
Current runtime support now materializes the first governed trigger actions directly into execution metadata and audit-ready runtime effects: terminal outcomes plus `require_approval(...)`, `apply_policy_pack(...)`, `rewrite_tone(...)`, and `log_evidence(...)` become `runtime_effects`, `policy_runtime`, `output_guidance`, and audit evidence fields that downstream governance layers can inspect.

## Two Meanings In One Name

The PTAG name intentionally carries two valid meanings:

- `Phasa Tawan for AI Government`
- `Policy TAG`

The first meaning emphasizes PTAG as a governance-focused language shaped for AI operating environments.
The second meaning emphasizes PTAG as a practical policy-tagging structure that attaches permissions, constraints, and decisions to roles and actions.

Both meanings matter in public:
- PTAG is a language for governed AI operations
- PTAG is also a policy structure that teams can read, validate, and maintain

## Why PTAG Matters Inside SA-NOM

SA-NOM does not rely only on prompts or scattered application code to decide what an AI role can do.

PTAG matters because it separates policy definition from business logic.
That gives teams a cleaner way to:
- define governed roles
- review authority boundaries
- validate policy coverage
- inspect constraints without reading the entire runtime
- support audit and compliance review more directly

This is one of the reasons SA-NOM reads as a governed AI operations platform rather than only a model wrapper.

## Repository Reference Surface

The current public repository already includes PTAG-facing implementation and examples.

Reference implementation paths:
- `sa_nom_governance/ptag/ptag_parser.py`
- `sa_nom_governance/ptag/ptag_validator.py`
- `sa_nom_governance/ptag/ptag_semantic.py`
- `sa_nom_governance/ptag/role_loader.py`
- `sa_nom_governance/ptag/role_compiler.py`

Public-safe example paths:
- `resources/roles/GOV.ptn`
- `resources/roles/LEGAL.ptn`
- `resources/roles/core_terms.ptn`

These files should be treated as the current public PTAG reference surface for this repository.

## Public Syntax Position

The current canonical public syntax in this repository is the existing PTAG text format already used by the parser, validator, and example role files.

That means the public baseline today is the custom PTAG document format shown in files such as `resources/roles/GOV.ptn`.

YAML may still be a useful future evolution for PTAG, especially if the project later wants stronger tooling interoperability or a lower parser-maintenance burden. But YAML is not being declared here as the canonical PTAG format today because the current repository implementation still centers on the existing PTAG syntax.

This matters for professional release discipline: the public docs should not declare a syntax migration complete before the implementation actually changes.

## Validation Position

PTAG already has a meaningful public validation story in this repository.

At a high level, PTAG validation currently includes:
- structural validation for required headers and supported block types
- semantic validation for role and authority consistency
- policy coverage-gap signaling when governed actions lack supporting policy or constraint coverage
- trigger-shape signaling when a policy block is missing a governed `WHEN` or `THEN` clause

See [PTAG Full Spec](PTAG_FULL_SPEC.md) for the current public detail level.

## How PTAG Relates To The Rest Of SA-NOM

Use this mental model:
- `PTAG` defines the role and policy shape
- `Authority Guard` enforces action boundaries at runtime
- `PT-OSS` assesses whether the surrounding structure is safe enough to trust
- `Audit` layers record what happened and why

So PTAG should not be read as only a parser.
It is the governance-language foundation that helps the rest of the product stay legible and enforceable.

## What Public Here Does And Does Not Mean

Public here means:
- PTAG is described openly in the repository
- the current reference implementation is inspectable
- public-safe examples are available
- contributions can be proposed through the repository workflow

Public here does not mean:
- PTAG is already a frozen industry standard
- every future syntax decision is permanently settled
- every internal or commercial deployment pattern is already documented equally
- PTAG alone replaces legal, regulatory, or human accountability decisions

## Where To Read Next

If you want to go deeper:
1. read this guide first
2. read [PTAG Quick Start](PTAG_QUICK_START.md) for the shortest study path
3. read [PTAG Examples](PTAG_EXAMPLES.md) for the example progression
4. read [PTAG FAQ And Comparison](PTAG_FAQ_AND_COMPARISON.md) for positioning and common questions
5. read [PTAG Full Spec](PTAG_FULL_SPEC.md)
6. inspect `resources/roles/`
7. inspect `sa_nom_governance/ptag/`
8. read `CONTRIBUTING.md` if you want to help improve PTAG

## Summary

PTAG is now presented in this repository as a public governance-language layer for defining structured roles, authority boundaries, constraints, and policy logic.

If PT-OSS is SA-NOM's structural intelligence layer, PTAG is the policy and role-definition layer that makes governed AI operations legible, reviewable, and enforceable.
