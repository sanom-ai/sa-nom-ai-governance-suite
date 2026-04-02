# Release Notes - v0.7.0

## Release Focus

`v0.7.0` is the autonomous governed runtime foundation release after the `v0.6.x` Global Harmony baseline line.

This release is not about opening another broad feature family.
It is about making the existing runtime cleaner, more portable, more automatic, easier to trust, and more believable for serious organizational evaluation.

The central direction of the release is:

`Autonomous Governed Runtime Foundation`

That means `v0.7.0` strengthens the system where real operational confidence matters:

- runtime portability instead of repository-root assumptions
- governed autonomy signals instead of scattered workflow state
- degraded-state visibility instead of silent governance erosion
- deterministic defaults instead of incidental file-order behavior
- release and performance discipline instead of late-stage hygiene work

## Completed Scope

### Runtime Portability And Install-Safe Packaging

- removed critical alignment loading assumptions that depended on the current working directory
- made public runtime resources available through explicit bundled package data under `sa_nom_governance/_bundled_resources`
- updated configuration bootstrap behavior so fresh runtime bases can seed required public-safe resources automatically
- aligned guided bootstrap and role-private-studio resource loading with the same bundled source of truth
- made package discovery explicit in `pyproject.toml` and verified local wheel creation for the `0.7.0` package line
- refreshed the trusted registry manifest so the bundled public role catalog stays trusted and consistent in both source-tree and packaged execution

### Failure Visibility And Operator Trust

- stopped invalid role and hierarchy materials from disappearing silently in the operator surface
- surfaced invalid governance materials through health, dashboard, and role-library summaries
- made degraded governance posture machine-readable so operators can distinguish safe runtime fallback from missing governed materials

### Deterministic Defaults And Runtime Predictability

- made the Global Harmony default region deterministic and test-backed
- removed implicit default selection based on incidental file ordering
- kept alignment/runtime selection behavior explainable and easier to reason about during evaluation and future extension

### Automation-First Governed Execution

- added governed autonomy posture to workflow state so the runtime can show whether AI should continue, pause, recover, fail closed, or wait for humans
- exposed machine-readable runtime action recommendations through operational readiness and dashboard summaries
- strengthened the runtime's ability to look like an active governed operator rather than a passive policy helper

### Performance And Release Discipline

- reduced repeated work in dashboard, readiness, and health paths by reusing shared runtime snapshots more consistently
- added runtime performance baseline artifacts for health, operational readiness, and dashboard build latency
- added public release preflight guardrails that now inspect release notes targeting, quick-start doctor posture, runtime performance posture, and runtime hygiene expectations
- aligned package metadata and docs index with the current `v0.7.0` line and filled the missing `v0.6.2` release notes gap

## Why This Release Matters

`v0.7.0` matters because it makes SA-NOM more believable as a governed runtime platform, not only as a repository with strong ideas.

Before this release, the system already had strong governed features, but some of the operational trust story still depended on assumptions that were easy to miss:
- running from the source tree happy path
- allowing broken governance materials to hide behind silent skips
- letting foundational defaults depend on incidental ordering
- treating performance and release posture as secondary concerns

After `v0.7.0`, SA-NOM presents a cleaner story for serious evaluators:
- AI can carry more bounded operational load without blurring human approval boundaries
- operators can see degraded governance conditions instead of discovering them too late
- runtime behavior is more portable, more explicit, and more test-backed
- the repository can support a stronger build-and-release posture for future milestones

That is important because organizational trust is not built only from policy concepts.
It is built from whether the runtime feels disciplined, inspectable, and repeatable when it actually runs.

## Verification

Validated during `v0.7.0` release preparation with:

- `python -m compileall -q sa_nom_governance _support\tests scripts`
- `python -m pytest _support\tests`
- `python -m pytest --no-cov _support\tests\test_public_release_preflight.py -q`
- `python -m pip wheel . --no-deps -w _review\build_smoke`
- `python scripts\trusted_registry_refresh.py`
- wheel inspection confirming bundled public runtime resources are present in the built package
- `python scripts\quick_start_path.py --doctor`
- `python scripts\runtime_performance_baseline.py --iterations 2`
- `python scripts\public_release_preflight.py --release-version 0.7.0 --json`

## Next Phase

After `v0.7.0`, the next phase should build on this cleaner runtime foundation rather than reopening structural ambiguity.

The strongest continuation is deeper governed execution on top of the new base:
- strengthen autonomous workflow advancement inside bounded policy paths
- continue improving release/runtime discipline with explicit operational budgets and recovery posture
- extend higher-level orchestration or enterprise add-on work only after the runtime foundation stays coherent

## Notes

- `v0.7.0` should be read as a quality-and-foundation milestone, not a hype milestone
- this release intentionally favors coherence, portability, operator trust, and runtime discipline over broad new surface area
- the release strengthens SA-NOM's position as a serious governed AI runtime candidate for organizational evaluation while preserving clear human control boundaries
