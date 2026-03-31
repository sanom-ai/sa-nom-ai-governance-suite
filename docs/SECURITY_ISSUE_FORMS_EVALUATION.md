# Security Issue Forms Evaluation

This guide evaluates whether SA-NOM should keep using markdown issue templates for security workflow or move toward GitHub issue forms in a later step.

## Why This Guide Exists

`v0.1.15` already clarified ownership, labels, and the split between AI-prepared context and human-confirmed decision fields.

The next question is whether GitHub issue forms would make that workflow stronger, or whether markdown templates are still the better fit for the repository at this stage.

## Core Position

SA-NOM should optimize for a workflow where:
- AI can help prepare issue context, summarize findings, and prefill repeatable structure
- humans still confirm trust-sensitive decision fields such as escalation, ownership, temporary exception acceptance, and merge-blocking outcomes

Any future move to issue forms should reinforce that split rather than obscure it.

## Current Baseline

The repository currently uses markdown issue templates for:
- security exceptions
- security follow-up
- bug reports
- documentation
- feature requests

This keeps the workflow lightweight and easy to evolve, and it remains friendly to AI-assisted drafting.

## Strengths Of Staying With Markdown Templates For Now

Markdown templates are still strong when the repository needs:
- fast iteration on wording
- low process weight
- easy copy-paste and AI-assisted drafting
- minimal GitHub workflow overhead
- flexibility while the security workflow is still evolving

For SA-NOM's current maturity, these are meaningful advantages.

## Where Issue Forms Could Improve Workflow Later

Issue forms could become useful when the repository wants:
- stronger field-by-field consistency
- required inputs for owner, revisit point, escalation owner, or trust-boundary flags
- easier filtering of structured inputs across issues
- less ambiguity about what must be human-confirmed before an issue is treated as complete

Forms are especially attractive when the workflow is stable enough that field structure will not change every few PRs.

## Recommended Direction

Do not migrate the security workflow to issue forms yet.

Instead:
1. keep markdown templates as the active baseline
2. continue refining the wording around AI-prepared versus human-confirmed fields
3. tighten label and ownership usage in real issues first
4. revisit GitHub issue forms only after the repository has more evidence that the field structure has stabilized

## What AI Can Prepare Reliably

Good candidates for AI-assisted prefilling:
- finding summary
- related PR, commit, package, or file references
- likely trust-boundary signals
- draft mitigation context
- draft closure criteria or revisit checkpoints

## What Humans Must Still Confirm

These fields should remain human-confirmed even if AI drafts them:
- human decision owner
- escalation owner
- whether escalation is required
- whether a temporary exception is acceptable
- whether merge should block
- whether follow-up visibility is adequate

## Practical Evaluation Result

The current recommendation is:
- `markdown templates now`
- `issue forms later, if the workflow stabilizes and structured enforcement becomes more valuable than flexibility`

## Relationship To Existing Docs

Read this guide with:
- [docs/SECURITY_OWNERSHIP_AND_LABELS.md](SECURITY_OWNERSHIP_AND_LABELS.md)
- [docs/SECURITY_ESCALATION_RULES.md](SECURITY_ESCALATION_RULES.md)
- [docs/SECURITY_EXCEPTION_WORKFLOW.md](SECURITY_EXCEPTION_WORKFLOW.md)
- [docs/SECURITY_FOLLOW_UP_VISIBILITY.md](SECURITY_FOLLOW_UP_VISIBILITY.md)
- [CONTRIBUTING.md](../CONTRIBUTING.md)

## Practical Summary

The right public message is:

SA-NOM currently keeps security intake lightweight with markdown issue templates because that still fits an AI-assisted, human-confirmed workflow best. Issue forms remain a future option once the structure becomes stable enough to justify stronger field enforcement.
