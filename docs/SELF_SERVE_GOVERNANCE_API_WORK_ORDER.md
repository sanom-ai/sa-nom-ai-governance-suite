# Self-Serve Governance API Work Order

SA-NOM will operate as a single-axis self-serve governance API platform where customers define policy, the runtime enforces policy automatically, and the platform team focuses only on reliability, security, release, and billing.

## Scope Lock

This work order applies to one operating model only.

- Product model: API product (not managed service).
- Decision authority: customer-owned policy and customer-owned approver model.
- SA-NOM responsibility: platform operations only (`uptime`, `security`, `release`, `billing`).
- Excluded by default: per-case advisory, daily customer operations, unlimited custom support.

## Operating Goal

Build a passive-by-default governance runtime where routine decisions are automated and owner intervention is limited to platform stewardship and exceptional events.

## Work Orders

## WO-01: Scope And Boundary Freeze (Week 1)

Objective: Freeze one product line and remove mixed operating modes.

Deliverables:
- `PRODUCT_SCOPE.md` with non-negotiable scope.
- Updated boundary statement between core governance and optional provider lane.
- Responsibility matrix (`customer` vs `platform`).

Exit criteria:
- No repository docs claim managed baseline support.
- Team can explain the model in one sentence consistently.

## WO-02: Contract v1 Standardization (Week 1-2)

Objective: Define one dispatch contract for all AI providers.

Deliverables:
- `dispatch-v1` request/response schema.
- Standard error model (`policy_denied`, `provider_unavailable`, `approval_required`).
- Contract examples for OpenAI, Claude, and Gemini lanes.

Exit criteria:
- Provider adapter changes do not break client contract.
- Contract tests pass for all registered adapters.

## WO-03: Policy Decision Layer (Week 2-4)

Objective: Enforce governance before outbound provider calls.

Deliverables:
- Policy checks for role authority, risk thresholds, and data handling rules.
- Deterministic decision outcomes: `allow`, `deny`, `require_approval`.
- Pre-dispatch decision trace object.

Exit criteria:
- 100% of outbound requests pass through policy decision layer.
- Denied and approval-required requests are never forwarded.

## WO-04: Provider Governance Gateway (Week 4-5)

Objective: Control provider access by environment with instant shutdown options.

Deliverables:
- Provider allow-list per environment.
- Runtime toggles (`enabled`/`disabled`) and kill switch.
- Retry and timeout strategy with bounded fallback logic.

Exit criteria:
- Provider can be disabled without deployment downtime.
- Unauthorized providers return controlled rejection.

## WO-05: Audit Chain And Evidence Pack (Week 5-6)

Objective: Make every decision and outbound action auditable.

Deliverables:
- Immutable trace ID propagation from request to final response.
- Structured decision and dispatch logs.
- Evidence pack export format for audit and regulator review.

Exit criteria:
- Any response can be traced to policy outcome and provider call history.
- Evidence pack can be generated without manual reconstruction.

## WO-06: Tenant Isolation And API Keys (Week 6-7)

Objective: Secure multi-tenant operation and consumption control.

Deliverables:
- Tenant-scoped API keys and key rotation flow.
- Rate limit and quota policy.
- Isolation checks for data and logs.

Exit criteria:
- Cross-tenant access tests fail as expected (blocked).
- Quota and rate limiting are enforced at runtime.

## WO-07: Billing And Metering Core (Week 7-8)

Objective: Convert runtime usage into recurring revenue safely.

Deliverables:
- Metering events tied to tenant and plan.
- Subscription plan model (`base + usage`).
- Invoice-ready usage aggregation pipeline.

Exit criteria:
- Usage records reconcile with runtime logs.
- Billing export matches tenant consumption by period.

## WO-08: Control Room Self-Serve Surfaces (Week 8-9)

Objective: Let customers configure policy and providers without human support.

Deliverables:
- Policy editor and provider governance panel.
- Approval-path configuration UI.
- Environment-level control toggles and confirmation flows.

Exit criteria:
- New tenant can configure minimum production profile without external help.
- High-risk changes require explicit confirmation.

## WO-09: Reliability Automation (Week 9-10)

Objective: Remove daily manual monitoring burden.

Deliverables:
- Health checks, SLO alerts, and incident trigger rules.
- Runbook automation for common recoverable failures.
- Status page data feed.

Exit criteria:
- Platform does not require continuous manual watch.
- Priority incidents are auto-alerted with actionable context.

## WO-10: Security Hardening (Week 10-11)

Objective: Harden platform trust posture for real customers.

Deliverables:
- Secret handling standards and rotation runbook.
- Outbound network policy and egress controls.
- Security verification checklist and release gate.

Exit criteria:
- Release fails if critical security gates are not met.
- No plaintext secrets are stored in repository paths.

## WO-11: Go-Live Package (Week 11-12)

Objective: Make customer onboarding repeatable and fast.

Deliverables:
- SLA policy, service terms, and API onboarding guide.
- Quick-start template for tenant bootstrap.
- Production readiness checklist.

Exit criteria:
- New customer onboarding can complete within one business day.
- Support requests for basic setup drop to minimal levels.

## WO-12: Scale Loop (Week 13+)

Objective: Keep growth recurring while maintaining low owner workload.

Deliverables:
- Monthly release train with contract compatibility checks.
- KPI review rhythm (MRR, renewal, incidents, owner intervention).
- Backlog prioritization rule focused on self-serve maturity.

Exit criteria:
- Recurring revenue trend is stable or increasing.
- Owner intervention remains constrained to stewardship-level work.

## KPI Targets For Passive-Real Operation

- `>=95%` requests resolved by automated governance flow.
- Owner intervention `<=2 hours/week` on average.
- P1 incidents `<=1 per quarter` with post-incident review completed.
- Renewal rate `>=85%`.
- Onboarding completion within one business day for standard tenants.

## Definition Of Done (Program Level)

- Customers can use governance API end-to-end without managed operations from SA-NOM.
- Policy decisions, outbound actions, and outcomes are fully auditable.
- Billing and subscription flow supports recurring revenue at runtime level.
- Platform ownership stays at stewardship level, not per-case customer operation.
