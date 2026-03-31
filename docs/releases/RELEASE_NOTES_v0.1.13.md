# Release Notes v0.1.13

## Release Focus

This release strengthens SA-NOM's security review maturity by turning `v0.1.13` into a clearer baseline for accepted security exceptions and follow-up visibility.

The goal of this milestone is not to normalize unresolved findings. The goal is to make temporary exceptions more explicit, more attributable, and easier to revisit so repository-level security signals do not disappear after merge.

## Highlights

- added a security exception workflow guide
- added a security follow-up visibility guide
- updated contributor and security guidance so accepted findings require explicit ownership and a visible follow-up path
- kept the workflow lightweight, review-oriented, and compatible with the repository's dependency-light philosophy

## Why This Release Matters

After `v0.1.12` introduced lightweight dependency auditing and a dependency review workflow, the next maturity step was to explain what happens when a finding is not fixed immediately.

Security posture is not only about scanning. It is also about whether accepted risk remains visible, justified, and revisit-able.

`v0.1.13` gives SA-NOM a clearer public answer by documenting how temporary exceptions should be handled and how deferred security work should stay visible after merge.

## What Was Added In v0.1.13

### Security Exception Planning

- `docs/ROADMAP_v0.1.13.md`
- `docs/ISSUE_DRAFTS_v0.1.13.md`

### Security Exception Workflow

- `docs/SECURITY_EXCEPTION_WORKFLOW.md`
- `SECURITY.md` and `CONTRIBUTING.md` now point more clearly at accepted-exception handling expectations

### Follow-Up Visibility Workflow

- `docs/SECURITY_FOLLOW_UP_VISIBILITY.md`
- contributor and security guidance now point to the follow-up path expected when findings are deferred

## Community Baseline In This Release

The public baseline now includes a clearer review-discipline story around:
- how temporary security exceptions should be justified
- how accepted risk should be owned and revisited
- how deferred findings should stay visible after merge
- how lightweight security automation is complemented by explicit human workflow

## Commercial And Trust Direction

This release is about review maturity and technical trust.

It helps SA-NOM look more credible in technical diligence conversations by showing that security findings are not only surfaced, but also handled in a disciplined and visible way when immediate fixes are not practical.

## Upgrade Notes

- `v0.1.13` is a security exception and follow-up discipline milestone, not a new runtime feature milestone
- the release does not lower security expectations; it makes accepted exceptions more explicit and accountable
- the repository remains lightweight and review-oriented rather than process-heavy
- automation still surfaces findings, but humans remain responsible for justification, ownership, and revisit timing

## Verification Snapshot

Validated during `v0.1.13` work with:
- `python -m compileall -q .`
- `python -m pytest _support/tests`
- local review of the new exception and follow-up visibility docs
- local review of updated links across security, contributor, and docs-index materials

## Post-Release Follow-Up

Recommended next steps after `v0.1.13`:
- decide whether to formalize issue templates or structured labels for accepted security exceptions
- decide whether to add stronger escalation guidance for high-sensitivity findings
- continue improving the connection between automation signals, exception handling, and follow-up ownership

## Contact

- Community/commercial/security contact: `sanomaiarch@gmail.com`
