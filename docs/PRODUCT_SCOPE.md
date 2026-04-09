# Product Scope

SA-NOM is a self-serve governance API runtime where customers define policy and authority, and the platform enforces policy automatically with auditable outcomes.

## Scope Statement

This product follows a single operating model only.

- Product type: API product
- Decision ownership: customer
- Platform ownership: uptime, security, release, billing
- Delivery mode: self-serve by default

## In Scope

- Governance decision engine for outbound AI usage
- Provider-neutral dispatch contract
- Policy checks before and after provider execution
- Audit chain and evidence exports
- Tenant isolation, API keys, quotas, and rate limits
- Control Room surfaces for policy and runtime governance
- Subscription and usage metering for recurring revenue

## Out Of Scope

- Managed operations as the default product path
- Daily case handling for customer business workflows
- Customer policy decision making by SA-NOM
- Unlimited support desk behavior
- Open-ended custom development without product alignment

## Non-Negotiable Rules

1. Every external AI request must pass governance checks before dispatch.
2. Policy and approval authority stay with the customer organization.
3. SA-NOM runtime must produce traceable, auditable evidence for decisions.
4. Platform changes must preserve contract compatibility and tenant isolation.
5. Commercial packaging must not blur product responsibility boundaries.

## Success Criteria

- Most requests are resolved through automated policy paths.
- Customers can onboard and run without managed operations.
- Recurring revenue is tied to API usage and subscription plans.
- Owner effort stays at platform stewardship level, not daily operations.

## Related Documents

- [SELF_SERVE_GOVERNANCE_API_WORK_ORDER.md](SELF_SERVE_GOVERNANCE_API_WORK_ORDER.md)
- [CUSTOMER_PLATFORM_RESPONSIBILITY_MATRIX.md](CUSTOMER_PLATFORM_RESPONSIBILITY_MATRIX.md)
- [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md)
