# Feature Matrix

This matrix shows the current public boundary between the self-managed community baseline and the guided / commercial path for SA-NOM.

It is a product-positioning guide, not a binding commercial contract. Final commercial scope depends on deployment shape, support expectations, compliance requirements, and whether the engagement is software-only or software plus rollout services.

## How To Read This Matrix

- `Community baseline` means the capability is present in the public AGPL repository and can be self-managed by the customer.
- `Guided / commercial path` means the capability may involve enterprise packaging, rollout hardening, tailored delivery, direct support, custom integration work, or quote-specific scope.
- `Why it matters` explains why the row is important for an operator, buyer, or deployment team.

## Flagship Capability Proof Line

By the `v0.7.1` line, SA-NOM's strongest public story is the way eight capabilities connect into one governed operating system rather than appearing as isolated features.

| Area | Community baseline | Guided / commercial path | Why it matters |
| --- | --- | --- | --- |
| Role Private Studio | Included in the public baseline with JD-to-role authoring, revision history, diff summaries, restore-aware revision posture, publication readiness, and trusted-registry-aware publication surfaces. Dashboard and studio summaries now show review blockers, restore state, revision posture, and publisher readiness instead of leaving those signals implicit. | Assisted authoring workshops, organization-specific role templates, tailored publication workflow design, and rollout operating model support. | Gives operators a readable path from role intent to governed publication instead of relying on prompt-only authoring or hidden workflow state. |
| Human Ask | Included in the public baseline with role-scoped reporting, meeting mode, confidence-threshold gating, freshness posture, evidence references, and governed reporting boundaries. Human Ask can now surface `fresh`, `stale`, and guarded-confidence posture directly in the response and operator views. | Guided reporting patterns, tailored executive reporting packs, operator training, and organization-specific reporting workflows. | Makes AI reporting feel operationally live and governed rather than ad hoc, while keeping low-confidence or out-of-scope situations visible to humans. |
| PT-OSS Structural Intelligence | Included in the public baseline as an embedded structural-intelligence layer with seven PT-OSS indicators, posture evaluation, blocker summaries, high-risk signal counts, and the Thai public-sector lane (`PT_OSS_FULL_CAL_TH`). Structural readiness now shows up in studio and dashboard summaries instead of staying trapped inside raw evaluator output. | Tailored evaluation thresholds, organization-specific structural interpretation, guided remediation planning, and rollout posture workshops. | Helps teams judge whether a role or workflow is structurally trustworthy enough to publish or automate, not only whether it technically parses or boots. |
| Authority Guard + Resource Lock | Included in the public baseline with allow / deny / human-required decisions, human override paths, request-level authority traces, resource locks, conflict detection, resume posture, and guardrail summaries. Dashboard surfaces now show guarded, blocked, resumed, and waiting-human states more explicitly. | Tailored approval routing, enterprise escalation design, custom authority policies, and operator-runbook adaptation. | Protects the runtime from unsafe actions, conflicting operations, and authority drift while giving operators a clearer recovery path. |
| Audit Chain + Evidence Pack | Included in the public baseline with tamper-evident audit chaining, evidence-pack export, role snapshots, compliance context, workflow proof bundles, retention posture, and integrity-contract summaries. Operator surfaces now show evidence export posture and integrity health more directly. | Tailored evidence-pack schemas, audit-readiness packaging, regulator-response tailoring, and evidence-retention operating support. | Gives reviewers and auditors something stronger than screenshots or chat logs: a structured evidence trail that is easier to inspect and verify. |
| Trusted Registry | Included in the public baseline with signed role-pack verification, trusted registry manifests, source-to-bundle manifest alignment, verified / invalid / drift posture, and role-loading enforcement. Studio publication summaries now show registry verification and live-hash posture more explicitly. | Managed signing operations, customer-specific trust hierarchies, hardware-key rollout support, and controlled release workflow design. | Keeps role publication and loading tied to explicit organizational trust instead of informal file movement or unverified runtime inputs. |
| Integration Outbound | Included in the public baseline as a webhook-first outbound foundation with explicit preset families for SIEM, chat-ops, ticketing, and custom webhook lanes. Retry, dead-letter, HMAC signing, and channel-family readiness are surfaced in operator summaries instead of being implied by implementation details only. | Tailored connector work, enterprise routing, destination-specific payload design, and production integration rollout support. | Lets SA-NOM hand governed events to the rest of the organization without pretending every enterprise connector is fully productized in the public baseline. |
| Human Alert + Escalation Notification | Included in the public baseline with dashboard-first alerting, policy-driven escalation, notification readiness by channel family, and outbound candidate summaries for human-required runtime situations. Operator surfaces now break alert posture down into configured, active, missing, or attention-required states. | Tailored alert-routing rules, organization-specific notification policies, chat-ops / ticketing rollout support, and escalation operating model design. | Helps humans see when AI is blocked, uncertain, escalating, or waiting on governance rather than discovering those states too late. |

## Reading The Current Boundary

The public baseline is already strong enough to evaluate these eight areas as one coherent governed runtime story.

The guided / commercial path still matters where organizations need:
- tailored rollout design
- enterprise-specific operating models
- custom integrations or signing infrastructure
- structured enablement for legal, audit, and executive stakeholders

That means the public repository should be read as an evidence-backed self-managed baseline, while the guided path remains the layer for deeper tailoring and rollout support.
