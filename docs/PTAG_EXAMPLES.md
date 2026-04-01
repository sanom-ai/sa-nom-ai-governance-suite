# PTAG Examples

This guide explains the public-safe PTAG example set in this repository and what each file is trying to teach.

Use it after [PTAG Quick Start](PTAG_QUICK_START.md) when you want more than one example pattern.

## How To Read The Example Set

The examples are arranged so readers can move from smaller patterns to more enterprise-shaped governance scenarios.

A practical reading order is:
1. `resources/roles/core_terms.ptn`
2. `resources/roles/OPS_REVIEW.ptn`
3. `resources/roles/GOV.ptn`
4. `resources/roles/LEGAL.ptn`
5. `resources/roles/CHANGE_CONTROL.ptn`
6. `resources/roles/VENDOR_RISK.ptn`

## Example Map

### `resources/roles/core_terms.ptn`

Purpose:
- show the smallest PTAG document in the current public set
- introduce the `dictionary` block
- give readers shared vocabulary before they read larger role files

Good for:
- first-time PTAG readers
- checking the simplest document structure

### `resources/roles/OPS_REVIEW.ptn`

Purpose:
- show a compact role with authority, constraints, and a small number of policies
- demonstrate a low-risk review lane that escalates when confidence drops

Pattern highlights:
- simple role definition
- clear allow and deny boundaries
- a single conditional review path

Good for:
- understanding the minimum useful PTAG role pack
- seeing how `approve` and `escalate` appear in practice

### `resources/roles/GOV.ptn`

Purpose:
- show a governance-focused control role
- demonstrate explicit high-authority boundaries and emergency-stop logic

Pattern highlights:
- governance stratum role
- authority with `require human_override`
- policies that combine direct approval, escalation, and `wait_human`

Good for:
- reading the public governance baseline
- understanding how SA-NOM keeps sensitive decisions visible

### `resources/roles/LEGAL.ptn`

Purpose:
- show a department-shaped specialist role
- demonstrate legal review and contract-risk signaling without allowing final contract execution

Pattern highlights:
- specialist role under governance supervision
- explicit denies for signing and ethical bypass
- policy checks tied to contract and compliance work

Good for:
- comparing PTAG across business functions
- understanding authority below the top governance layer

### `resources/roles/CHANGE_CONTROL.ptn`

Purpose:
- show a human-required lane around production release approval
- demonstrate how PTAG can let AI prepare work while keeping final release authority with a human

Pattern highlights:
- `require human_override` in authority and constraint blocks
- a `wait_human` policy for production release approval
- support actions that AI can still perform safely before approval

Good for:
- teams thinking about governed production change workflows
- readers who want a clear human-in-the-loop example

### `resources/roles/VENDOR_RISK.ptn`

Purpose:
- show an enterprise-shaped cross-functional role that touches vendor review, legal escalation, and evidence completeness
- demonstrate a richer mix of `approve`, `escalate`, and `wait_human`

Pattern highlights:
- multiple governed resources
- evidence-sensitive decision logic
- explicit boundary around high-risk vendor onboarding

Good for:
- readers who want a more complete business-facing example
- teams studying how PTAG can represent review gates before sensitive onboarding decisions

## What These Examples Intentionally Do Not Try To Be

These examples are public-safe teaching artifacts.

They are not:
- full production policy packs for every organization
- legal or regulatory advice
- proof that one PTAG file alone is enough to run a complete enterprise workflow

They exist to make PTAG easier to study, compare, and evolve responsibly in public.

## Where To Go Next

After this examples guide:
- read [PTAG FAQ And Comparison](PTAG_FAQ_AND_COMPARISON.md) for positioning and common questions
- return to [PTAG Full Spec](PTAG_FULL_SPEC.md) for syntax and validation detail
- inspect `sa_nom_governance/ptag/` to see how the parser and validator consume PTAG files
- read [CONTRIBUTING](../CONTRIBUTING.md) if you want to add or improve public-safe PTAG examples

## Summary

The PTAG example set now gives readers a clearer path from:
- vocabulary
- to a compact role example
- to governance and specialist examples
- to human-in-the-loop and enterprise-shaped patterns

That makes the public PTAG surface easier to learn without pretending the repository already contains every deployment-specific policy pack.
