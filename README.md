# SA-NOM AI Governance Suite

[![CI](https://github.com/sanom-ai/sa-nom-ai-governance-suite/actions/workflows/ci.yml/badge.svg)](https://github.com/sanom-ai/sa-nom-ai-governance-suite/actions/workflows/ci.yml)
[![License: AGPL-3.0-only](https://img.shields.io/badge/License-AGPL%203.0--only-blue.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/sanom-ai/sa-nom-ai-governance-suite)](https://github.com/sanom-ai/sa-nom-ai-governance-suite/releases)

SA-NOM is a private AI operations platform for organizations that want AI in real roles, with governance built in.

Instead of treating AI as a loose chatbot or an unsafe automation layer, SA-NOM lets teams define governed AI roles, route work through authority boundaries, let humans pull reports and meetings through Human Ask, keep escalation and override paths explicit, and retain evidence for every important decision.

## Quick Start

If you want the shortest real first run, start with the private local lane and let SA-NOM bootstrap the runtime artifacts for you:
- copy `examples/.env.ollama.example` into your local environment setup
- run `python scripts/quick_start_path.py`
- if the quick-start report passes, start the runtime with `python scripts/run_private_server.py --host 127.0.0.1 --port 8080`

The quick-start path seeds public resources, owner registration, access profiles, trusted registry files, startup validation, and an end-to-end runtime smoke test in one guided command.

Choose the path that matches what you want to see first:
- use [docs/GUIDED_EVALUATION.md](docs/GUIDED_EVALUATION.md) when you want the shortest evaluator path with smoke tests and a private-dashboard walkthrough
- stay on the quick-start lane above when you want the fastest local bootstrap into a working private runtime
- use [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) when you want the longer deployment path and infrastructure posture details

## What SA-NOM Actually Does

SA-NOM helps organizations move from "AI that answers" to "AI that works inside the business."

With SA-NOM, teams can:
- define AI roles with explicit responsibilities and allowed authority
- route work through approval, escalation, and reporting paths
- keep human override available for sensitive or ambiguous decisions
- maintain evidence, audit context, and deployment readiness records
- run the whole stack in private infrastructure controlled by the organization

The result is not only safer AI. It is AI that can participate in operations, coordination, and managed execution without falling outside organizational control.

## Flagship Capability Proof

The current flagship proof line in SA-NOM is not a single feature.
It is the way eight operator-facing capabilities work together inside one governed runtime:

- `Role Private Studio`
- `Human Ask`
- `PT-OSS Structural Intelligence`
- `Authority Guard + Resource Lock`
- `Audit Chain + Evidence Pack`
- `Trusted Registry`
- `Integration Outbound`
- `Human Alert + Escalation Notification`

By the `v0.7.1` line, these surfaces are easier to defend from code, tests, and operator summaries because publication posture, reporting freshness, structural readiness, guardrail recovery, evidence integrity, registry trust, outbound routing, and alert readiness are all more explicit than before.

See [docs/FEATURE_MATRIX.md](docs/FEATURE_MATRIX.md) for the current capability boundary and [docs/PRODUCT_TOUR.md](docs/PRODUCT_TOUR.md) for the guided walkthrough.

## PTAG Governance Language

SA-NOM includes PTAG as the policy and role-governance language that helps define roles, authority boundaries, constraints, and policy logic in a structured, reviewable way.

PTAG is now public in this repository. The PTAG documentation, reference implementation, and public-safe examples shipped here are available under the repository's AGPL-3.0-only license posture.

That means teams can study PTAG, use it, evaluate it, and contribute improvements through the normal repository workflow.

See [docs/PTAG_FRAMEWORK.md](docs/PTAG_FRAMEWORK.md) for the public explanation of what PTAG is, [docs/PTAG_QUICK_START.md](docs/PTAG_QUICK_START.md) for the shortest onboarding path, [docs/PTAG_EXAMPLES.md](docs/PTAG_EXAMPLES.md) for the example map, [docs/PTAG_FAQ_AND_COMPARISON.md](docs/PTAG_FAQ_AND_COMPARISON.md) for common questions and positioning notes, and [docs/PTAG_FULL_SPEC.md](docs/PTAG_FULL_SPEC.md) for the current repository-level technical specification baseline.

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

PT-OSS is a creator-developed embedded framework integrated into SA-NOM to assess structural dependency, fragility, human-override integrity, and power asymmetry before AI roles and workflows are treated as safely governed.

See [docs/PT_OSS_CORE.md](docs/PT_OSS_CORE.md) for the core explanation of what is already embedded in the codebase and [docs/PT_OSS_METRICS.md](docs/PT_OSS_METRICS.md) for the plain-language metric explainer.

## Governed Document Center

SA-NOM's Governed Document Center is a controlled system for creating, organizing, approving, publishing, and retaining policies, standards, procedures, forms, templates, and records under role-based authority and audit-ready governance.

It is designed so AI can do routine document work inside defined boundaries, while humans step in only when approval, exception handling, or higher-risk control decisions are required.

See [docs/GOVERNED_DOCUMENT_CENTER.md](docs/GOVERNED_DOCUMENT_CENTER.md) for the concept, [docs/GOVERNED_DOCUMENT_CLASSES.md](docs/GOVERNED_DOCUMENT_CLASSES.md) for the class model, [docs/GOVERNED_DOCUMENT_LIFECYCLE.md](docs/GOVERNED_DOCUMENT_LIFECYCLE.md) for the lifecycle and authority model, [docs/GOVERNED_DOCUMENT_TEMPLATE_MODEL.md](docs/GOVERNED_DOCUMENT_TEMPLATE_MODEL.md) for the single-template rule-driven design, and [docs/GOVERNED_DOCUMENT_AUTHORITY_ROUTING.md](docs/GOVERNED_DOCUMENT_AUTHORITY_ROUTING.md) for explicit authority and approval routing.

Document routing should also stay governed. The right model is explicit authority and approval routing where AI can move routine document work forward inside approved boundaries, while humans confirm approvals, exceptions, waivers, and higher-risk release decisions.

Controlled documents also need a rule-driven numbering and metadata standard so each release, revision, superseded reference, owner, approver, and retention posture stays identifiable and auditable. See [docs/GOVERNED_DOCUMENT_NUMBERING_METADATA.md](docs/GOVERNED_DOCUMENT_NUMBERING_METADATA.md).

The same document layer should also support Human Ask reporting, so people can call AI to retrieve active versions, pending approvals, ownership, review gaps, and meeting-ready document posture without bypassing authority or confidentiality boundaries. See [docs/GOVERNED_DOCUMENT_HUMAN_ASK_REPORTING.md](docs/GOVERNED_DOCUMENT_HUMAN_ASK_REPORTING.md).

Controlled document work also needs retention and records governance so archive, hold, disposal, and record-custody decisions stay explicit and auditable. See [docs/GOVERNED_DOCUMENT_RETENTION_RECORDS.md](docs/GOVERNED_DOCUMENT_RETENTION_RECORDS.md).

The module should also have a real role story, not only architecture. See [docs/DOCUMENT_GOVERNANCE_ROLE_PACK.md](docs/DOCUMENT_GOVERNANCE_ROLE_PACK.md) for a public-safe role pack that ties document drafting, routing, metadata, Human Ask, and retention work back to a governed AI role.

A governed release scenario should also be visible, so readers can see how draft, review, approval, release, retained records, and Human Ask reporting fit together in one workflow. See [docs/GOVERNED_DOCUMENT_RELEASE_SCENARIO.md](docs/GOVERNED_DOCUMENT_RELEASE_SCENARIO.md).

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


## Security And Operational Posture

SA-NOM is designed for private, self-managed, and air-gapped deployment scenarios where operators keep control of infrastructure and secrets.

That means the public repository should be read as a governance and operational baseline, not as a place where real credentials, emergency access material, or deployment secrets belong.

See [docs/SECRETS_AND_CREDENTIALS_HANDLING.md](docs/SECRETS_AND_CREDENTIALS_HANDLING.md) for the first public handling guide and [docs/SECURITY_AND_DEPENDENCY_HYGIENE.md](docs/SECURITY_AND_DEPENDENCY_HYGIENE.md) for the dependency-light security posture.






