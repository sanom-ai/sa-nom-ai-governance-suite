# Governed HITL Reliability And Observability

This document defines the reliability and observability baseline for governed approvals, reviews, escalations, and intervention reporting in SA-NOM.

It is the reliability continuation of the `v0.5.0` governed HITL operations layer and should be read as the point where the approval model becomes more operationally believable for serious organizational evaluation.

## Why This Layer Exists

SA-NOM already explains:
- when sensitive actions should stop for human control
- how a minimum approval surface should work
- how Human Ask can report governed status without bypassing authority
- what realistic HITL role packs may look like

What still needs to become explicit is how those governed approval paths remain inspectable when the system is under load, when escalations accumulate, when decision packets age, or when runtime health starts affecting trust in the decision flow.

Organizations do not only ask whether approvals exist.
They also ask:
- whether approvals can disappear into a black box
- whether escalations are piling up without visibility
- whether stalled decisions are easy to detect
- whether service health affects approval trust
- whether audit records remain intact when the runtime is degraded

This layer exists to answer those questions with one compact operational posture.

## Core Position

The governed HITL layer should not rely on a hidden operational story.

If SA-NOM is going to be considered for serious pilot evaluation, governed approvals need a reliability and observability model that makes it possible to see:
- whether the approval path is healthy
- where bottlenecks are forming
- which queues are at risk
- what approvals or escalations are aging out
- whether governance events are still being captured correctly

This does not require a full enterprise observability platform in `v0.5.0`.
It does require a clear public baseline that makes the approval model operationally legible.

## Reliability Questions That Matter Most

At this phase, the most important reliability questions are:
- can the system still surface pending approvals and escalations when runtime conditions worsen
- can operators see when a governed decision path is stalled or expired
- can Human Ask reporting continue to provide trustworthy status visibility
- can the system retain rationale, evidence, and intervention records under stress
- can the organization tell the difference between a policy block and a runtime-health problem

These questions matter more than broad infrastructure claims because they directly affect whether human authority remains effective during real operations.

## Observability Surface

The governed HITL reliability baseline should expose a compact set of operational signals.

Core signal groups:
- approval queue depth
- review queue depth
- escalation queue depth
- stalled or expired decision packets
- approval latency by trigger class
- escalation frequency by lane or owner
- rejection frequency for high-risk actions
- policy-violation events tied to governed actions
- Human Ask reporting availability for governed status views
- health signals for the services that carry approval and evidence traffic

These signals should be treated as governance-relevant operational data, not only engineering telemetry.

## Minimum Reliability States

To stay understandable, the HITL layer should normalize a small reliability posture model.

At minimum:
- `healthy`
- `degraded`
- `constrained`
- `blocked`
- `recovery_required`

Interpretation:
- `healthy` means approval and escalation flows are visible and moving within expected limits
- `degraded` means the flow is still functioning but latency, queue depth, or reporting fidelity is worsening
- `constrained` means the flow still operates, but trust-sensitive actions may need slower routing or stricter manual review
- `blocked` means governed actions cannot continue safely because approval visibility or routing is materially impaired
- `recovery_required` means operators must restore the approval path before sensitive governed work proceeds

These states should help operators distinguish runtime instability from policy decisions.

## Governance Signals Operators Should Inspect

The first operator view does not need to be complex, but it should answer the practical questions that matter during pilot evaluation.

Operators should be able to inspect:
- which approvals are currently pending
- which escalations have no active owner response
- which decision packets are nearing expiry
- where approval latency is highest
- which trigger classes are generating the most manual load
- whether Human Ask reporting is current or stale
- whether evidence capture is succeeding for recent interventions

This makes the approval layer feel governed and inspectable, rather than procedural but opaque.

## Approval Bottlenecks And Escalation Pressure

One of the most important operational trust questions is whether the system can show where friction is accumulating.

At minimum, SA-NOM should be able to frame:
- bottlenecks by approver role
- bottlenecks by trigger class
- bottlenecks by business lane or governed role pack
- escalation pressure by escalation owner
- repeated reject-or-return patterns that suggest unclear policy or poor evidence quality

The system does not need perfect analytics in `v0.5.0`.
It does need a baseline way to explain where governed work is slowing down and why.

## Runtime Gates For Governed Approval Flow

The governed approval path should be connected to basic runtime gates rather than treated as a separate UI story.

Important gate questions include:
- is the approval surface reachable
- is decision-state persistence available
- is evidence storage available
- is audit recording functioning
- is Human Ask reporting current enough to trust
- are notification or routing dependencies failing

If any of these gates are materially impaired, operators should be able to classify the governed approval path as degraded or blocked instead of guessing.

## Human Ask Reporting Under Reliability Stress

Human Ask should stay helpful during degraded conditions without pretending that everything is normal.

When the reliability posture worsens, Human Ask responses should prefer clarity over polish:
- state whether the approval system is healthy, degraded, constrained, blocked, or in recovery
- surface queue pressure and stale-decision indicators
- identify whether reporting freshness is current or delayed
- separate governance outcomes from runtime-health issues
- explain when a person must inspect or intervene directly

This matters because status reporting becomes more important, not less, when approval trust is under pressure.

## Audit And Evidence Continuity

Reliability is not only about queues and service health.
It is also about whether the governance record survives operational stress.

For governed HITL interventions, continuity should preserve:
- who acted
- when they acted
- what decision packet they touched
- what rationale they recorded
- what evidence bundle was attached
- whether the action completed, retried, expired, or was escalated during degraded conditions

If audit or evidence capture is impaired, the system should say so explicitly.
Silent partial records are more dangerous than visible degradation.

## Operational Maintenance Expectations

This slice should also connect the governed HITL layer to the broader maintenance posture of the suite.

At minimum, maintenance expectations should include:
- health inspection for approval-routing services
- operator-led recovery steps for stale or blocked decision lanes
- visibility into whether notifications, routing, and evidence persistence are working
- a documented distinction between local evaluation issues and live controlled deployment issues
- clear operator ownership when the approval path enters `blocked` or `recovery_required`

This keeps the HITL layer aligned with SA-NOM's broader readiness-first philosophy.

## Integration And Compliance Continuity

The reliability story should stay connected to the rest of the platform without exploding scope.

That means:
- integrations should preserve approval-state visibility and audit continuity
- document or API connectors should not hide pending decisions or escalation ownership
- compliance-oriented readers should be able to map degraded or blocked HITL states to accountability expectations
- Thai and broader governance readers should see that reliability posture supports real human oversight, not just system uptime

The point is not to implement every enterprise connector in this slice.
The point is to make the governed HITL layer credible in a wider organizational context.

## Design Boundaries

This slice should stay disciplined.

It is not:
- a promise of full site-reliability engineering automation
- a complete observability platform
- a claim that every approval failure mode is already automated
- a replacement for deployment-specific operator runbooks

It is the first public reliability and observability baseline for governed approval trust.

## What Success Looks Like

This slice is successful when a serious organizational reader can see that SA-NOM now has:
- a defined reliability posture for governed approvals and escalations
- operator-visible queue, bottleneck, and expiry signals
- a way to distinguish runtime-health problems from governance decisions
- Human Ask status reporting that remains governed during degraded conditions
- audit and evidence continuity expectations for human interventions

That is what helps move SA-NOM from a quality prototype toward a serious organizational candidate.

## Next Steps

The implementation slices that should follow this document are:
1. a compact integration-continuity slice for governed approval paths
2. compliance and localization continuity for HITL operations
3. `v0.5.0` release-prep and evaluation framing

## Summary

Governed HITL reliability and observability is the operational trust layer around approval, escalation, and intervention flow.

It makes SA-NOM more credible by showing not only how humans decide inside the governed loop, but how operators can tell when that loop is healthy, pressured, degraded, or blocked.
