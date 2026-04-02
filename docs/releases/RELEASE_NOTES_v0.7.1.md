# Release Notes - v0.7.1

## Release Focus

`v0.7.1` is the flagship hardening release after `v0.7.0`.

This release does not open a new product family.
It tightens the gap between SA-NOM's flagship capability language and the implementation, tests, and operator surfaces that support it.

The central direction of the release is:

`Flagship Capability Proof Hardening`

That means `v0.7.1` strengthens the parts of the product story that evaluators, operators, and reviewers are most likely to question:

- how role publication readiness is surfaced
- whether Human Ask feels governed and current enough to trust
- how structural PT-OSS posture maps into operator decisions
- whether authority and lock recovery are easy to diagnose
- how evidence integrity and trusted publication posture are explained
- how outbound routing and human-alert readiness are exposed without overclaiming

## Completed Scope

### Integration Outbound And Human Alert Readiness

- added explicit outbound target families for SIEM, Slack, Teams, Jira, ServiceNow, and custom webhook lanes
- surfaced configured, active, missing, and attention-required channel readiness in dashboard/operator views
- strengthened notification posture so dashboard-first alerting and outbound routing candidates are easier to inspect

### Human Ask Confidence And Freshness Posture

- made freshness posture visible in Human Ask summaries and operator-facing surfaces
- exposed confidence-band and governed-reporting posture more clearly
- made low-confidence reporting pause into human review more explicit instead of leaving it implicit in raw metadata

### Role Private Studio Publication And Restore Visibility

- strengthened studio summaries with clearer revision posture, restore state, publication blockers, and publisher readiness
- exposed manual-override, restore-aware, and registry-verified posture in studio and dashboard surfaces
- made publication-state inspection easier without depending on internal implementation knowledge

### Audit Chain, Evidence Pack, And Trusted Registry Proof

- improved evidence-pack posture with integrity-contract summaries, export status, and trusted-registry mismatch detection
- strengthened trusted-registry operator visibility with live-hash verification, drift detection, and publication trust posture
- kept wording precise around tamper evidence and verification rather than overclaiming immutability

### PT-OSS Structural Intelligence And Guardrail Operator Proof

- surfaced PT-OSS posture, blocker counts, high-risk indicators, and Thai public-sector mode more clearly in studio and dashboard summaries
- tied structural posture more directly to publication readiness and operator action
- exposed authority-guard, human-required, blocked, resumed, and resource-lock conflict posture in one guardrail summary surface
- added runtime alerts for structural pressure, authority attention, and resource-lock pressure

### Release-Prep And Flagship Surface Alignment

- expanded `FEATURE_MATRIX.md` into an explicit eight-capability flagship proof surface
- updated the product tour and root README so the strongest flagship claims are easier to follow from repository entry points
- prepared `v0.7.1` release notes, PR description, and handoff materials as one internal release-prep set

## Why This Release Matters

`v0.7.1` matters because strong governed-runtime ideas are not enough by themselves.
Serious evaluation depends on whether the runtime can explain its posture in operator-friendly language without weakening the technical contract behind it.

Before this release, many of SA-NOM's strongest capabilities already existed, but several of the most visible proof points still required too much inference:
- structural posture often lived deeper than the primary operator summaries
- Human Ask freshness and confidence needed more explicit surface area
- publication, evidence, and trust posture could feel stronger in code than in the first layer operators actually inspect
- outbound and alert readiness were present, but their surface language needed to be more explicit and easier to defend

After `v0.7.1`, the flagship story is more coherent:
- each major capability is easier to inspect without diving into raw internal state
- the dashboard and summary surfaces explain more of the runtime's real governance posture
- the product language stays closer to the implementation reality across docs, tests, and operator views
- SA-NOM looks more like one governed system and less like a collection of promising subsystems

## Verification

Validated during the current `v0.7.1` hardening line with:

- `python -m pytest _support\tests`
- focused tests for evidence pack, role private studio, and dashboard operator surface
- current full-suite status: `337 passed`
- current coverage posture: `84.08%`

## Next Phase

After `v0.7.1`, the next phase should build on this stronger flagship proof line rather than reopening wording drift.

The strongest continuation is:
- deeper end-to-end workflow proof for the same eight flagship surfaces
- tighter release-prep discipline around the final `v0.7.1` PR and tag
- continued operator-surface polish only where it improves evidence-backed clarity

## Notes

- `v0.7.1` should be read as a flagship-proof hardening milestone, not a brand-new architecture milestone
- this release intentionally favors clearer operator proof, stronger documentation alignment, and tighter implementation-to-claim continuity over broad new surface area
- the goal is not to say SA-NOM is perfect; the goal is to make its strongest capability claims easier to defend from real repository evidence
