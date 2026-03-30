# SA-NOM AI Governance Suite

[![CI](https://github.com/sanom-ai/sa-nom-ai-governance-suite/actions/workflows/ci.yml/badge.svg)](https://github.com/sanom-ai/sa-nom-ai-governance-suite/actions/workflows/ci.yml)
[![License: AGPL-3.0-only](https://img.shields.io/badge/License-AGPL%203.0--only-blue.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/sanom-ai/sa-nom-ai-governance-suite)](https://github.com/sanom-ai/sa-nom-ai-governance-suite/releases)

SA-NOM is a private AI operations platform for organizations that want AI in real roles, with governance built in.

Instead of treating AI as a loose chatbot or an unsafe automation layer, SA-NOM lets teams define governed AI roles, route work through authority boundaries, let humans pull reports and meetings through Human Ask, keep escalation and override paths explicit, and retain evidence for every important decision.

## What SA-NOM Actually Does

SA-NOM helps organizations move from "AI that answers" to "AI that works inside the business."

With SA-NOM, teams can:
- define AI roles with explicit responsibilities and allowed authority
- route work through approval, escalation, and reporting paths
- keep human override available for sensitive or ambiguous decisions
- maintain evidence, audit context, and deployment readiness records
- run the whole stack in private infrastructure controlled by the organization

The result is not only safer AI. It is AI that can participate in operations, coordination, and managed execution without falling outside organizational control.

## PTAG Governance Language

SA-NOM includes PTAG as the policy and role-governance language that helps define roles, authority boundaries, constraints, and policy logic in a structured, reviewable way.

PTAG is a proprietary framework developed by the creator and integrated into SA-NOM as a foundational governance layer.

See [docs/PTAG_FRAMEWORK.md](docs/PTAG_FRAMEWORK.md) for the public explanation of what PTAG is and why it matters in the product.

## Private Rule Studio And Private Rule Position

`Private Rule Studio` is a core platform capability, not a paid unlock.

Organizations can upload their own JD inputs, start from JD and rule accelerators prepared by SA-NOM, and create a `Private Rule Position` for any organization-specific hat they need.

That means SA-NOM is not limited to standard titles. Teams can define flexible positions such as a cross-functional recovery lead, a regulator liaison, or an exception coordinator, then govern that position through explicit authority, escalation, and evidence boundaries.

See [docs/PRIVATE_RULE_POSITION.md](docs/PRIVATE_RULE_POSITION.md) for the concept and [examples/private_rule_position.example.json](examples/private_rule_position.example.json) for a public-safe example.

## Compliance Knowledge Baseline

SA-NOM now treats compliance-oriented content as a documented baseline, not as an automatic compliance claim.

That means the repo can help organizations with internal governance, evidence, workflow discipline, and standards-oriented readiness while still being explicit that legal review and regulator-facing completion may remain outside the software itself.

See [docs/COMPLIANCE_KNOWLEDGE_BASELINE.md](docs/COMPLIANCE_KNOWLEDGE_BASELINE.md), [docs/ISO_42001_NIST_CROSSWALK.md](docs/ISO_42001_NIST_CROSSWALK.md), [docs/THAI_AI_REGULATORY_GAP_MAP.md](docs/THAI_AI_REGULATORY_GAP_MAP.md), [docs/PDPA_AI_GUIDELINE_MAP.md](docs/PDPA_AI_GUIDELINE_MAP.md), [docs/LOCAL_REPRESENTATIVE_READINESS.md](docs/LOCAL_REPRESENTATIVE_READINESS.md), and [docs/COMPLIANCE_SKILL_LAYER_CONTRACT.md](docs/COMPLIANCE_SKILL_LAYER_CONTRACT.md), and [docs/COMPLIANCE_RESPONSE_TEMPLATES.md](docs/COMPLIANCE_RESPONSE_TEMPLATES.md).

## PT-OSS Structural Intelligence

SA-NOM includes PT-OSS as an embedded structural intelligence layer.

PT-OSS is a proprietary framework developed by the creator and integrated into SA-NOM to assess structural dependency, fragility, human-override integrity, and power asymmetry before AI roles and workflows are treated as safely governed.

See [docs/PT_OSS_CORE.md](docs/PT_OSS_CORE.md) for the core explanation of what is already embedded in the codebase and [docs/PT_OSS_METRICS.md](docs/PT_OSS_METRICS.md) for the plain-language metric explainer.

## Governed Document Center

SA-NOM's Governed Document Center is a controlled system for creating, organizing, approving, publishing, and retaining policies, standards, procedures, forms, templates, and records under role-based authority and audit-ready governance.

It is designed so AI can do routine document work inside defined boundaries, while humans step in only when approval, exception handling, or higher-risk control decisions are required.

See [docs/GOVERNED_DOCUMENT_CENTER.md](docs/GOVERNED_DOCUMENT_CENTER.md) for the concept, [docs/GOVERNED_DOCUMENT_CLASSES.md](docs/GOVERNED_DOCUMENT_CLASSES.md) for the class model, [docs/GOVERNED_DOCUMENT_LIFECYCLE.md](docs/GOVERNED_DOCUMENT_LIFECYCLE.md) for the lifecycle and authority model, [docs/GOVERNED_DOCUMENT_TEMPLATE_MODEL.md](docs/GOVERNED_DOCUMENT_TEMPLATE_MODEL.md) for the single-template rule-driven design, and [docs/GOVERNED_DOCUMENT_AUTHORITY_ROUTING.md](docs/GOVERNED_DOCUMENT_AUTHORITY_ROUTING.md) for explicit authority and approval routing.

Document routing should also stay governed. The right model is explicit authority and approval routing where AI can move routine document work forward inside approved boundaries, while humans confirm approvals, exceptions, waivers, and higher-risk release decisions.

## Why Teams Use SA-NOM

Organizations do not only need AI governance. They need AI that can actually operate.

SA-NOM is designed for teams that want to:
- assign AI to real work, not just experiments
- give AI bounded roles instead of broad unrestricted access
- keep reporting lines, escalation paths, and auditability intact
- deploy AI in private or air-gapped environments
- show legal, IT, audit, and leadership teams how the system stays accountable

## Product Direction

SA-NOM follows an operations-first model:
- AI takes a role
- AI works inside boundaries
- humans stay in control of escalation
- evidence stays attached to important actions
- governance, compliance, and private deployment are built in from the start

That means SA-NOM should be read as a governed AI operations system, not only as a governance utility.
