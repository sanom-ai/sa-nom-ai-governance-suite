# Release Notes - v0.1.15

## Release Focus

`v0.1.15` strengthens SA-NOM's GitHub security workflow by making ownership, labels, and issue-template structure more operational.

The goal of this milestone is not to add a new runtime feature. The goal is to make repository-level security work read more clearly as an AI-heavy operational workflow with explicit human decision authority for trust-sensitive outcomes.

## What Changed

### Planning And Direction

- added `docs/ROADMAP_v0.1.15.md`
- added `docs/ISSUE_DRAFTS_v0.1.15.md`

### Ownership And Workflow Signals

- added `docs/SECURITY_OWNERSHIP_AND_LABELS.md`
- refined security issue template labels to align with a clearer workflow vocabulary

### Template Clarity

- refined `.github/ISSUE_TEMPLATE/security_exception.md`
- refined `.github/ISSUE_TEMPLATE/security_follow_up.md`
- separated `AI-Prepared Context` from `Human-Confirmed Decision Fields`

### Workflow Surface And Forms Direction

- added `docs/SECURITY_ISSUE_FORMS_EVALUATION.md`
- updated `.github/ISSUE_TEMPLATE/config.yml`
- updated `CONTRIBUTING.md`
- updated `docs/README.md`

## Why This Release Matters

After `v0.1.14` introduced structured security issue templates and escalation rules, the next maturity step was to make the GitHub workflow itself more readable and more accountable.

`v0.1.15` gives SA-NOM a clearer public workflow for:
- who owns security follow-up
- how security issue state should be labeled
- which issue fields AI can help prepare
- which fields humans must still confirm directly
- why markdown templates remain the right lightweight baseline for now

## Community Baseline In This Release

The public baseline now includes:
- a security ownership and labels model
- clearer separation between AI-prepared context and human-confirmed decision fields in security issue templates
- a documented evaluation of markdown templates versus future issue forms
- a tighter GitHub issue-template configuration for structured security workflow

## Operating Boundary

This milestone keeps SA-NOM's operating model explicit:
- AI or automation may surface findings, summarize trust impact, suggest labels, and prepare issue structure
- humans still decide ownership, escalation, temporary exception acceptance, and merge-blocking outcomes

## Upgrade Notes

- `v0.1.15` is a GitHub security workflow milestone, not a runtime feature milestone
- the release strengthens repository workflow clarity without claiming full workflow automation
- markdown templates remain the active security intake baseline for now because they still fit an AI-assisted, human-confirmed workflow best

## Verification Snapshot

Validated during `v0.1.15` work with:
- `python -m compileall -q .`
- local review of roadmap, ownership, issue-template, and workflow wording
- local verification that the new release notes are linked from `docs/README.md`

## Suggested Next Step

After `v0.1.15`, the next useful step would be to decide whether to formalize labels and ownership patterns even further through issue forms, label automation, or release-level workflow reporting.
