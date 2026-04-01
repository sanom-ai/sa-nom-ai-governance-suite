# Release Notes - v0.5.2

## Release Focus

`v0.5.2` is a small patch-and-polish release after the governed HITL baseline in `v0.5.0` and the dashboard/operator improvements in `v0.5.1`.

This release is focused on reducing evaluator friction without opening a new concept phase. The work stays deliberately narrow: smoother private-dashboard first-run flow, clearer evaluation-path guidance, and better recovery when a user lands in the wrong permission lane.

## Completed Scope

### Private Dashboard Trial Flow

- added first-run lane shortcuts for local dashboard evaluation so a user can enter the `viewer`, `operator`, or `reviewer` lane without translating development tokens by hand
- improved the auth card copy so the private dashboard explains which lane to use and where each lane should begin
- added a short dashboard walkthrough to the guided evaluation flow so local evaluators can move from smoke tests into the live operator surface more easily

### Evaluation-Path Guidance

- clarified the top-level README so new users can choose between quick local bootstrap, guided evaluation, and the longer deployment path more quickly
- added a focused evaluation-path chooser to the docs index so readers can pick the right self-serve path without scanning the whole docs tree first
- tightened the patch story around evaluation and first-run use rather than expanding product scope

### Permission Recovery UX

- turned the dashboard permission-denied view into a guided recovery surface instead of a dead end
- added lane guidance that explains which views fit `viewer`, `operator`, and `reviewer` roles
- allowed evaluators to switch directly to the correct lane when they hit a permission boundary during live trials

## Why This Release Matters

`v0.5.2` does not introduce a new strategic layer. Its value is in making the existing serious-evaluation surface easier to approach and less fragile during real use.

The repository now gives evaluators a cleaner first-run path to:
- get into the private dashboard with the right lane faster
- understand which documentation path matches their goal
- recover from permission mistakes without losing momentum during a live review

## Verification

- `node --check sa_nom_governance/dashboard/static/dashboard_app.js`
- `python -m pytest _support/tests`

## Next Phase

After `v0.5.2`, the next major line should remain separate from patch work. The planned `v0.6.0` direction can now start from a cleaner evaluation baseline without pulling new concepts into the patch line.

## Notes

- this release is intentionally narrow and should be read as a patch-hardening milestone
- `v0.5.2` closes the small trial-friction and evaluation-path polish line before the next concept-driven phase
