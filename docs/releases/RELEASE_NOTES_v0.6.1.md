# Release Notes - v0.6.1

## Release Focus

`v0.6.1` is the first controlled implementation slice after the directional `v0.6.0` Global Harmony announcement.

This release moves SA-NOM Global Harmony from concept-only positioning into governed runtime behavior. The scope stays deliberately narrow and credible:

- runtime-attached regional alignment evaluation
- approval-gated constitution switching for sensitive or externally visible contexts
- resonance scoring that makes cultural-fit signals visible without claiming perfect cultural truth

`v0.6.1` is not a full global alignment product release. It is the first working runtime baseline that proves the direction can operate inside SA-NOM's existing governance model.

## Completed Scope

### Runtime Global Harmony Integration

- wired `global_harmony` request metadata into the runtime decision path
- added governed preview behavior for requested regional constitution changes before activation
- attached active-region alignment metadata to runtime results so later operator surfaces can read one consistent source of truth

### Resonance Scoring Baseline

- added `resonance_score` and `resonance_band` to cultural alignment evaluation results
- established a conservative `high` / `moderate` / `low` signal model for aligned, guarded, and escalated contexts
- kept the scoring model explainable and auditable rather than over-claiming machine certainty

### Human Approval And Risk Gating

- sensitive or externally visible alignment-switch requests now pause behind a human approval gate
- low-risk governed contexts can continue through the direct-switch path under baseline policy
- runtime traces and policy basis now identify when a Global Harmony selection decision triggered the pause

### Evidence And Documentation

- added runtime integration coverage for aligned, guarded, and approval-required cases
- updated the runtime baseline document to map the implementation back to adoption, ROI, and enterprise-governance value
- preserved the safe-claims boundary introduced in `v0.6.0`

## Why This Release Matters

`v0.6.1` matters because it turns Global Harmony into a real governed runtime capability instead of leaving it as architecture language alone.

The repository now demonstrates that SA-NOM can:

- evaluate culturally sensitive runtime context without retraining the base model
- require human review when alignment switching becomes externally visible or risk-sensitive
- expose a measurable cultural-fit signal that later workflows, dashboards, and policy packs can build on

That combination is important because it addresses the enterprise "last mile" problem directly: AI may be technically capable, but organizations still need it to behave appropriately across regions, brands, and regulatory contexts while staying auditable.

## Verification

- `python -m compileall -q .`
- `python -m pytest _support/tests`

## Next Phase

After `v0.6.1`, the next step should continue the same narrow runtime-first discipline:

- extend the trigger-and-action model around the current runtime contract
- deepen regional constitution coverage and evidence signals
- keep dashboard work secondary to the core policy and runtime engine

## Notes

- `v0.6.1` should be read as the first operational proof slice of the Global Harmony line
- the resonance model in this release is a governed baseline, not a claim of universal cultural correctness
- this release strengthens SA-NOM's enterprise story by combining cultural alignment signals with approval routing, auditability, and private-runtime posture
