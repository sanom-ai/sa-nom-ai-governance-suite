# PTAG Framework

This guide explains the PTAG framework that already sits at the policy and role-definition layer of SA-NOM.

It should be read as the public-facing explanation of the governance language and policy-structure model that help turn SA-NOM from a general AI runtime into a governed AI operations platform.

## What PTAG Is

PTAG is the policy and role-governance language used inside SA-NOM.

PTAG is a proprietary framework developed by the creator and integrated into SA-NOM to define roles, authority boundaries, constraints, and policy logic in a structured, reviewable form.

In practical terms, PTAG is the layer that answers:
- what role exists
- what that role is allowed to do
- what it is denied from doing
- what conditions must be satisfied before sensitive actions can proceed
- which policies or constraints still need human control

## Two Meanings In One Name

The PTAG article describes the name as intentionally carrying two valid meanings:

- `Phasa Tawan for AI Government`
- `Policy TAG`

The first meaning emphasizes PTAG as a creator-designed language for AI governance.
The second meaning emphasizes PTAG as a practical policy-tagging structure that attaches permissions and rules to roles and actions.

In the public product story, both meanings matter:
- PTAG is a governance language with creator-defined structure
- PTAG is also the working policy layer that teams read, validate, and maintain

## Why PTAG Matters Inside SA-NOM

SA-NOM does not rely only on prompts or application code to decide what an AI role can do.

PTAG matters because it separates policy definition from business logic.
That gives teams a cleaner way to:
- define governed roles
- review authority boundaries
- validate policy coverage
- inspect constraints without reading all runtime code
- support audit and compliance review more directly

This is one of the reasons SA-NOM reads as a governed AI operations platform rather than only a model wrapper.

## What PTAG Defines

At a public product level, PTAG should be understood as the framework that defines:

- roles
- authority
- constraints
- policy conditions
- action references
- publication and validation readiness

The article also explains that PTAG documents include:
- headers for metadata such as module, version, and owner
- blocks such as `role`, `authority`, `constraint`, `policy`, `decision`, and `flow`

That structure is what makes PTAG readable by both engineering and governance stakeholders.

## Why This Is Useful For Organizations

PTAG helps organizations move away from hidden permission logic scattered through code.

That is useful when a team wants to:
- show who can do what
- review policy intent before deployment
- detect policy coverage gaps
- make role authority reviewable by technical and non-technical stakeholders
- reduce hardcoded permission mistakes

For SA-NOM, PTAG is the layer that turns AI from a broad assistant into a governed role with explicit boundaries.

## How PTAG Relates To The Rest Of SA-NOM

Use this simple mental model:

- `PTAG` defines the role and policy shape
- `Authority Guard` enforces the action boundary at runtime
- `PT-OSS` assesses whether the surrounding structure is safe enough to trust
- `Audit Chain` records what happened

So PTAG should not be read as just a parser.
It is the governance-language foundation that supports the rest of the product.

## Safe Public Claim

The correct public claim is:

SA-NOM includes PTAG as the policy and role-governance language that helps define roles, authority boundaries, constraints, and policy logic in a structured, reviewable way.

PTAG is a proprietary framework developed by the creator and integrated into SA-NOM as a foundational governance layer.

## What This Does Not Mean

This does not mean:
- every internal PTAG design decision is fully disclosed as an academic specification in the public repo
- every industry or government-specific PTAG pattern is already surfaced equally in the public docs
- the public repo should be read as a complete legal or regulatory policy library by default

The public repo currently surfaces PTAG as the core governance-language layer that powers role definition and policy readability inside SA-NOM.

## Recommended Reading Order

1. [Product Tour](PRODUCT_TOUR.md)
2. [Feature Matrix](FEATURE_MATRIX.md)
3. [Guided Evaluation](GUIDED_EVALUATION.md)
4. PTAG resources under `resources/roles/` and related runtime config files

## Summary

PTAG is the governance-language foundation inside SA-NOM.

It is a proprietary framework developed by the creator and used to define structured roles, authority boundaries, constraints, and policy logic before runtime enforcement begins.

If PT-OSS is SA-NOM's structural intelligence layer, PTAG is the policy and role-definition layer that makes governed AI operations legible and enforceable.