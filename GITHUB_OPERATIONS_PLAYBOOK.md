# GitHub Operations Playbook

This document captures the next GitHub-facing setup steps after the first public release.

## Repository Positioning

### Suggested repository description

Open-core governance and orchestration toolkit for structured AI operations on private infrastructure.

### Suggested website field

- Preferred: a future SA-NOM product page when it exists
- Temporary fallback: leave blank
- Avoid using a pricing-request form as the primary website field unless no product page exists yet

### Suggested topics

- `ai-governance`
- `open-core`
- `self-hosted`
- `private-ai`
- `audit`
- `compliance`
- `workflow-governance`
- `enterprise-ai`
- `air-gapped`
- `ptag`
- `human-in-the-loop`
- `governance-runtime`

## What To Configure On GitHub

### Repository settings

- Keep the repository public
- Keep Issues enabled
- Consider enabling Discussions after the first public issues arrive
- Keep Releases visible and continue using tagged releases
- Add the repository description and topics

### Items to highlight in the repo

Point visitors to these files first:
- `README.md`
- `ONE_PAGER.md`
- `ONE_PAGER_TH.md`
- `COMMERCIAL_LICENSE.md`
- `RELEASE_NOTES_v0.1.0.md`

## Suggested labels

Create at least these labels:
- `bug`
- `documentation`
- `enhancement`
- `roadmap`
- `commercial`
- `community`
- `good first issue`
- `help wanted`
- `v0.1.1`

## Suggested milestone

### Milestone name

`v0.1.1`

### Milestone goal

Stabilize the first public community baseline, improve evaluator onboarding, and turn the initial public release into a cleaner contributor and customer entry point.

### Suggested milestone criteria

- docs improved for first-time evaluators
- at least one setup-friction issue reduced
- full pytest run attempted in a clean environment
- community vs commercial boundary remains clear

## Suggested first GitHub actions

1. Add the repository description and topics.
2. Create the `v0.1.1` milestone.
3. Create the first issue batch from `ISSUE_DRAFTS_v0.1.1.md`.
4. Label at least one issue as `good first issue`.
5. Close the loop in future releases by linking resolved issues from release notes.

