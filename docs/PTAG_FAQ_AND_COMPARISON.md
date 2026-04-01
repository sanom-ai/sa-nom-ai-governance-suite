# PTAG FAQ And Comparison

This guide answers the most common early questions about PTAG and helps readers place it in the broader landscape without overselling what it is.

Use it after [PTAG Quick Start](PTAG_QUICK_START.md) and [PTAG Examples](PTAG_EXAMPLES.md) when you want the shortest honest explanation of where PTAG fits.

## FAQ

### What is PTAG in one sentence?

PTAG is the policy and role-governance language used by SA-NOM to describe governed AI roles, authority boundaries, constraints, and decision logic in a readable, reviewable format.

### What does PTAG actually define?

PTAG defines the control shape around a role.

In the current public repository surface, that means PTAG can describe:
- roles
- authority boundaries
- explicit denies and constraints
- policy decisions
- human-required paths such as `wait_human` or `require human_override`
- shared governance vocabulary through blocks like `dictionary`

### Is PTAG the same thing as a prompt?

No.

A prompt tells a model how to behave in language.
PTAG defines the governance shape around behavior.

That distinction matters because PTAG is meant to make authority, boundaries, and approval conditions inspectable outside the prompt text itself.

### Is PTAG only a parser format?

Also no.

PTAG does have a parser and validator in this repository, but PTAG should be read as a governance-language layer, not just a text grammar.

Inside SA-NOM, PTAG helps connect:
- role definition
- authority and constraint boundaries
- policy logic
- human escalation and override expectations
- semantic validation around policy coverage and role-authority consistency

### Is PTAG a complete policy engine by itself?

Not by itself.

PTAG is the definition layer.
Runtime enforcement still depends on the rest of SA-NOM, including runtime guards, decision paths, and audit/evidence layers.

A useful mental model is:
- PTAG defines policy and role shape
- runtime components enforce or act on that shape
- audit and evidence layers explain what happened

### Is PTAG public now?

Yes, in this repository.

As of April 1, 2026, PTAG is presented here as a public repository surface under the repository's `AGPL-3.0-only` license posture, including public documentation, reference implementation, and public-safe examples.

That public position does not mean PTAG is already a frozen standard. It means the repository now treats PTAG as something people can read, evaluate, and improve openly.

### Is YAML the main PTAG format now?

No.

The current canonical public PTAG format in this repository is still the existing `.ptn` text format used by the parser, validator, and example files.

YAML may still become a useful future direction, but it is not the declared public baseline today.

### Does PTAG remove the need for humans?

No.

PTAG is explicitly designed to make human control legible where it still matters.

Examples in this repository already show patterns such as:
- `require human_override`
- `wait_human`
- escalation to a higher authority role

That fits SA-NOM's broader operating idea: AI can work, but sensitive decisions should remain visible and governable.

### Is PTAG meant only for enterprise use?

No, but enterprise-shaped governance is one of its strongest current examples.

The public examples range from smaller teaching artifacts to more enterprise-shaped patterns, because the main value of PTAG appears when authority and review boundaries need to stay explicit.

### Does PTAG replace legal review, compliance review, or executive accountability?

No.

PTAG can help represent governance structure, role boundaries, and approval paths, but it does not replace the actual human or institutional accountability behind those decisions.

## Comparison Notes

These comparisons are meant to orient readers quickly. They are intentionally high-level and should not be read as exhaustive product evaluations.

### PTAG vs Prompt-Only Governance

Prompt-only governance usually keeps operational rules inside natural-language instructions.

PTAG differs because it tries to externalize governance structure into a readable role and policy document.
That makes it easier to:
- inspect authority separately from prompts
- review constraints without reading the whole runtime
- discuss governance with operators, reviewers, and auditors more directly

### PTAG vs Generic Policy Configuration

Many systems have policy configuration files.

PTAG is narrower and more opinionated than a generic config format because it is centered on governed AI roles, authority, constraints, and decision paths rather than on arbitrary application settings.

That role-centric shape is one of PTAG's main strengths inside SA-NOM.

### PTAG vs Traditional Policy Engines

Traditional policy engines usually focus on evaluating allow/deny decisions against structured rules.

PTAG overlaps with that world in the sense that it expresses permissions, constraints, and decisions.
But PTAG is not presented here as a general replacement for every policy engine.

Its current public value is more specific:
- role definition for governed AI work
- human escalation visibility
- policy coverage-gap signaling
- a public-safe governance layer that stays legible to operators and reviewers

### PTAG vs Workflow Orchestration Tools

Workflow orchestration tools usually focus on task sequencing, branching, retries, and execution control.

PTAG is not trying to replace orchestration.
Instead, PTAG answers a different question: what authority shape and governance conditions should exist around the work being orchestrated?

That means orchestration and PTAG can be complementary rather than competing layers.

### PTAG vs Guardrail Layers

Guardrail layers usually focus on blocking unsafe behavior, filtering outputs, or enforcing safety checks at runtime.

PTAG overlaps with that space when it defines boundaries and human-required lanes, but its emphasis is broader than runtime filtering alone.

PTAG tries to make the governance contract legible before and around runtime behavior, not only during output control.

### PTAG vs Role Templates Or Job Descriptions

A role template or job description explains what a role is supposed to do.

PTAG goes further by representing:
- explicit permissions
- explicit denies
- constraints
- policy outcomes
- escalation and human-control expectations

So PTAG can be thought of as a governed operational form of role definition rather than only a descriptive role document.

## What PTAG Is Not Trying To Claim

PTAG is not being presented here as:
- a universal replacement for all governance tooling
- a complete enterprise policy stack by itself
- a frozen standard with every future design decision settled
- a substitute for legal, regulatory, or executive accountability

That restraint is intentional. The current public repository should describe what PTAG already is, not everything it might become later.

## Practical Evaluation Questions

If you are deciding whether PTAG is relevant to your team, these are good questions to ask:
- Do we need AI roles with explicit authority boundaries?
- Do we want human-required paths to be visible in documents instead of implied in prompts?
- Do we need policy logic that is easier to review than scattered runtime code?
- Do we want a governance layer that can be studied publicly and evolved with examples?

If the answer to several of those is yes, PTAG is probably worth deeper evaluation.

## Where To Read Next

After this guide:
- return to [PTAG Full Spec](PTAG_FULL_SPEC.md) for syntax and validation details
- inspect [PTAG Examples](PTAG_EXAMPLES.md) for concrete patterns
- inspect `sa_nom_governance/ptag/` for the reference implementation
- read [CONTRIBUTING](../CONTRIBUTING.md) if you want to help improve PTAG publicly

## Summary

PTAG is best understood as a public governance-language layer for AI roles and authority boundaries.

It is not just a prompt, not just a parser, and not a claim to replace every policy or orchestration tool. Its value is that it makes governed AI role structure more legible, reviewable, and enforceable inside SA-NOM.
