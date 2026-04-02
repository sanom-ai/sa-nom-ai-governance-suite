# Roadmap v0.7.1

`v0.7.1` is the flagship hardening release after `v0.7.0`.

The purpose of this round is not to add a new product family.
It is to make the eight flagship capability claims stronger, more explicit, and more evidence-backed.

## Release Theme

`v0.7.1` should move SA-NOM from "strong governed runtime foundation" toward "stronger flagship capability proof."

That means:
- tighten the gap between claim language and implementation reality
- improve operator confidence for the public feature story
- reduce the number of places where a claim is only partially implied by docs
- make the most visible product surfaces easier to defend during serious evaluation

## Hardening Targets

### 1. Role Private Studio

Goal:
- strengthen the authoring-to-publication story so history, readiness, review gates, and restore posture are clearer and easier to inspect

Target outcomes:
- revision and publication posture remain visible in dashboard and summary surfaces
- restore and diff language stays aligned with the current implementation contract
- publication blockers are easier to understand from operator-facing output

### 2. Human Ask

Goal:
- make Human Ask feel more operationally live, more governed, and easier to trust during role-scoped reporting

Target outcomes:
- freshness and reporting posture become easier to inspect
- confidence threshold behavior becomes more explicit in returned summaries
- meeting mode and governed reporting boundaries become easier to explain from product surfaces

### 3. PT-OSS Structural Intelligence

Goal:
- make structural posture easier to map to publication readiness, automation posture, and operator action

Target outcomes:
- posture language stays consistent across PT-OSS, Human Ask, dashboard, and release docs
- Thai structural mode remains clearly surfaced as a specialized evaluation lane
- blockers and recommended actions become easier to consume outside raw PT-OSS output

### 4. Authority Guard + Resource Lock

Goal:
- keep this as one of SA-NOM's strongest proof points by improving operator visibility and recovery clarity

Target outcomes:
- allow / deny / human-required outcomes remain legible in dashboard and audit surfaces
- resource lock conflicts become easier to trace and explain to operators
- override lifecycle and lock-release behavior remain strongly test-backed

### 5. Audit Chain + Evidence Pack

Goal:
- strengthen the evidence story from "tamper-evident" to "easier to inspect, package, and explain"

Target outcomes:
- evidence-chain language remains precise and non-overclaiming
- pack export posture, integrity health, and exception traces remain easy to surface
- retention and evidence continuity stay connected in dashboard and release-prep paths

### 6. Trusted Registry

Goal:
- make trusted publication posture more explicit across source, package bundle, and runtime loading

Target outcomes:
- bundled and source registry manifests remain synchronized
- signature status is surfaced more clearly in operator-facing role summaries
- registry fallback posture remains visible instead of silent

### 7. Integration Outbound

Goal:
- make outbound integration claims more explicit and closer to the implementation contract

Target outcomes:
- target presets clearly cover SIEM, chat-ops, ticketing, and custom webhook lanes
- retry, dead-letter, and HMAC posture remain inspectable from summaries
- connector/channel language becomes more explicit in dashboard and documentation

### 8. Human Alert + Escalation Notification

Goal:
- make notification posture stronger, more explicit, and easier to explain as a governed operator surface

Target outcomes:
- dashboard-first alert posture remains strong
- external routing readiness is broken down by channel family instead of a generic boolean only
- notification policy, dispatch candidates, and missing-channel posture become easier to inspect

## Release Discipline

`v0.7.1` should stay disciplined.

It should not become:
- a UI redesign release
- a broad integration explosion
- a new runtime architecture rewrite
- a new compliance product family

It should remain a focused hardening release that improves confidence in the existing flagship story.

## Suggested Slice Order

1. outbound integration and operator notification hardening
2. Human Ask freshness and confidence posture hardening
3. Role Private Studio publication and restore visibility hardening
4. trusted-registry and evidence-surface consistency pass
5. release-prep and flagship-claim alignment

## Definition Of Success

`v0.7.1` is successful when:
- each of the eight flagship claims becomes easier to defend from code, tests, and operator surfaces
- the product story needs fewer wording caveats than in `v0.7.0`
- tests remain green and the runtime still behaves coherently as one governed system
