# Customer vs Platform Responsibility Matrix

This matrix defines accountability in the SA-NOM API product model.

## Core Rule

Customer owns governance decisions. SA-NOM owns platform reliability and security.

| Area | Customer Responsibility | SA-NOM Platform Responsibility |
| --- | --- | --- |
| Governance policy | Define policy, thresholds, and control intent | Execute policy engine exactly as configured |
| Role authority | Define approver model and authority boundaries | Enforce authority checks in runtime |
| Approval decisions | Approve or reject high-risk flows | Route and record approval state transitions |
| Business outcomes | Accept business impact of customer policy choices | Provide deterministic and auditable runtime behavior |
| Provider usage strategy | Choose enabled providers and allowed use cases | Enforce provider allow-list and environment controls |
| Data classification | Classify sensitive data and internal handling rules | Apply configured guardrails and redaction behavior |
| API credentials | Secure customer-side application credentials | Secure platform-issued API keys and key lifecycle |
| Runtime availability | Design internal fallback plans for their own operations | Meet SLA targets and monitor uptime/latency |
| Security posture | Operate secure usage patterns in customer applications | Operate platform hardening, patching, and incident response |
| Audit and compliance | Decide internal control framework and evidence use | Produce traceable logs and evidence exports |
| Billing governance | Track plan ownership and internal budget approval | Meter usage correctly and issue billing records |
| Release adoption | Decide when to adopt new versions | Publish release notes, compatibility posture, and safe upgrade path |

## Liability Boundary (Product Model)

- SA-NOM does not decide policy on behalf of the customer.
- SA-NOM does not operate as a daily managed service by default.
- Customer retains authority for final governance intent and approval logic.
- SA-NOM retains responsibility for platform operation quality.

## Escalation Rule

Only platform-level incidents are escalated to SA-NOM as owner responsibilities.
Policy intent disputes, approval decisions, and internal process ownership remain customer responsibilities.

## Related Documents

- [PRODUCT_SCOPE.md](PRODUCT_SCOPE.md)
- [SELF_SERVE_GOVERNANCE_API_WORK_ORDER.md](SELF_SERVE_GOVERNANCE_API_WORK_ORDER.md)
- [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md)
