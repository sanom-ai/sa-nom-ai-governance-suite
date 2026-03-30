# Feature Matrix

This matrix shows the current public boundary between the self-managed community baseline and the guided / commercial path for SA-NOM.

It is a product-positioning guide, not a binding commercial contract. Final commercial scope depends on deployment shape, support expectations, compliance requirements, and whether the engagement is software-only or software plus rollout services.

## How To Read This Matrix

- `Community baseline` means the capability is present in the public AGPL repository and can be self-managed by the customer.
- `Guided / commercial path` means the capability may involve enterprise packaging, rollout hardening, tailored delivery, direct support, custom integration work, or quote-specific scope.
- `Why it matters` explains why the row is important for an operator, buyer, or deployment team.

## Core Authoring And Runtime

| Area | Community baseline | Guided / commercial path | Why it matters |
| --- | --- | --- | --- |
| PTAG parsing and validation | Included in the public baseline. Role packs can be parsed, validated, and checked before deployment. | Tailored policy modeling support, assisted role design, and organization-specific PTAG authoring patterns. | Gives teams a structured way to define governed AI roles instead of relying on prompt-only behavior. |
| Private Rule Studio and Private Rule Positions | Included in the public baseline. Teams can upload their own JD inputs, start from starter JD/rule/hat materials, and create organization-specific `Private Rule Positions` without artificial rule-count limits. | Tailored rule design workshops, industry-specific starter libraries, publication governance support, and rollout-specific operating models. | This is how SA-NOM supports custom hats that only make sense inside one organization, not only standard role templates. |
| Role Private Studio | Included in the public baseline with role-authoring workflows, history, and publication flow. | Assisted template design, publication workflow extensions, and guided operating models for enterprise teams. | Helps teams move from job descriptions, Private Rule Positions, and role intent into governed AI roles faster. |
| Governed runtime execution | Included in the public baseline. The runtime enforces role behavior, policy boundaries, and evidence-oriented execution paths. | Rollout hardening, organization-specific runtime design, and deployment support for production programs. | This is the core of SA-NOM as an AI operations platform rather than a loose assistant layer. |
| Human Ask | Included in the public baseline as human-initiated reporting and meeting workflows. Operators can call one or more AI roles to report status, summarize work, or answer scoped questions on demand. | Enterprise meeting patterns, role-based reporting design, and program-specific operating enablement. | Lets humans pull governed reports from AI roles without confusing reporting with escalation or approval paths. |
| Authority Guard | Included in the public baseline. Allow, deny, and human-override checks are enforced inside runtime behavior. | Tailored authority modeling and operating-boundary design during rollout. | Prevents AI from drifting outside explicit organizational boundaries. |
| Resource Lock | Included in the public baseline. Runtime coordination prevents conflicting access to the same resource path. | Rollout tuning for higher-volume or more complex operational environments. | Important when multiple requests or roles may touch the same governed asset or workflow. |
| Human alert and escalation notification | Included in the public baseline through runtime alerts, dashboard visibility, and webhook-oriented notification paths. | Managed escalation directories, enterprise routing, and stakeholder-specific notification patterns. | Makes blocked or high-risk decisions visible before they become silent runtime failures. |

## Governance, Publication Control, And Evidence

| Area | Community baseline | Guided / commercial path | Why it matters |
| --- | --- | --- | --- |
| PT-OSS structural intelligence | Included in the public baseline as an embedded structural intelligence layer. PT-OSS is a proprietary framework developed by the creator and integrated into SA-NOM to assess structural dependency, fragility, human-override integrity, and power asymmetry before AI roles and workflows are treated as safely governed. The public baseline already includes embedded modes, structural assessment support, posture-driven readiness logic, and related metrics. | Tailored calibration, deeper rollout interpretation, and regulated-environment operating guidance. | Helps organizations evaluate whether the structure around AI is ready, not only whether the model works. |
| Trusted Registry | Included baseline path for signed role publication and manifest verification. | Hardened key operations, rollout-specific signing programs, and regulated publication processes. | Protects who is allowed to publish or trust role packs in a real organization. |
| Owner registration and delegated access | Included in the public baseline through owner registration, access profiles, and token rotation-aware flows. | Rollout hardening, identity design, and enterprise packaging for larger operator groups. | Establishes who owns the runtime and which delegated actors can perform privileged operations. |
| Audit Chain | Included in the public baseline with hash-linked audit behavior and tamper-evident runtime history. | Audit-program support, rollout reviews, and tailored evidence handling workflows. | Gives audit and leadership teams a stronger evidence trail than ad hoc logging. |
| Evidence Pack and export | Included in the public baseline with export-oriented evidence paths. | Auditor-ready packaging support, evidence review workshops, and organization-specific export expectations. | Makes live runtime behavior easier to review, justify, and defend. |
| Go-live readiness and startup validation | Included in the public baseline through startup checks, dashboard validation, and runtime smoke paths. | Formal rollout gates, guided production-readiness reviews, and enterprise deployment signoff support. | Helps teams prove readiness before exposing the system to real operator traffic. |
| Security and compliance starter templates | Included in the public baseline with security checklists and Thai starter templates for regulated environments. | Tailored compliance mapping, regulated rollout support, sovereign packaging, and on-site enablement. | Helps organizations connect the runtime story to security, compliance, and internal review requirements. |

## Deployment, Provider Lanes, And Operator Readiness

| Area | Community baseline | Guided / commercial path | Why it matters |
| --- | --- | --- | --- |
| Guided smoke-test path | Included in the public baseline through `python scripts/guided_smoke_test.py`. | Guided evaluation support and operator onboarding assistance. | Gives first-time evaluators a fast path to a working baseline without stitching everything together manually. |
| Private Ollama lane | Included in the public baseline as the default private demo and evaluation lane. | Private rollout assistance, local-model operating guidance, and environment-specific rollout tuning. | Supports the private AI story where model traffic should stay inside the customer environment. |
| OpenAI and Claude lanes | Included in the public baseline as optional hosted evaluation lanes. | Hosted-provider rollout guidance, governance workshops, and environment-specific deployment design. | Lets teams evaluate hosted models without changing the product model or losing the provider boundary. |
| Provider probes and demo flows | Included in the public baseline through provider smoke, demo-flow, and environment helper scripts. | Guided provider rollout, validation support, and handoff into production programs. | Helps operators verify the provider lane before live runtime use. |
| Dashboard and local operations | Included in the public baseline with runtime health, integrations, evidence, and provider surfaces. | Production rollout support, custom operational playbooks, and direct response commitments. | Gives operators a visible control surface for the governed runtime. |
| Docker deployment path | Included in the public baseline with containerized runtime paths and Ollama profile support. | Hardened deployment patterns and rollout guidance for customer environments. | Important for self-managed evaluation and internal deployment reproducibility. |
| Helm chart and raw Kubernetes manifests | Included in the public baseline as starter packaging. | Hardened overlays, cluster rollout services, and environment-specific tuning. | Supports production-track organizations that need Kubernetes-native deployment paths. |
| Self-managed private deployment | Included in the public baseline. The repository is designed for customer-controlled deployment. | Air-gapped delivery design, sovereign packaging, and rollout planning support. | Reinforces that SA-NOM is meant to live inside the customer's own infrastructure boundary. |

## Integrations And Data Lifecycle

| Area | Community baseline | Guided / commercial path | Why it matters |
| --- | --- | --- | --- |
| Webhook and outbound integration hooks | Included in the public baseline with examples and baseline runtime integration flows. | Custom connector work, private APIs, enterprise delivery patterns, and partner-system rollout support. | Helps SA-NOM fit into the surrounding operational environment instead of living in isolation. |
| SIEM / service-desk oriented integration patterns | Baseline hooks and examples are included. | Custom adapters, enterprise connectors, and rollout-specific integration design. | Important when customers need SA-NOM events to land inside established operational tooling. |
| Retention and data lifecycle controls | Included in the public baseline through retention-oriented runtime behavior and evidence lifecycle handling. | Tailored policy mapping, legal-hold workflow design, and regulated retention support. | Matters for organizations that need stronger control over archive, hold, and purge behavior. |
| Example artifacts and public-safe outputs | Included in the public baseline through sanitized examples, demo artifacts, and operator-ready sample outputs. | Tailored handoff packs, rollout artifacts, and customer-specific demo enablement. | Makes evaluation and onboarding clearer without exposing real customer state. |

## Commercial Packaging, Support, And Services

| Area | Community baseline | Guided / commercial path | Why it matters |
| --- | --- | --- | --- |
| Support model | Community and self-managed only. Public docs, examples, and community-oriented support path are available. | Direct support, negotiated response targets, rollout assistance, and ongoing enablement. | Determines how much delivery and operational risk stays with the customer team. |
| Enterprise identity and account management | Not part of the current public baseline beyond baseline owner and delegated-access flows. | SSO, SCIM, larger identity rollout design, and enterprise account alignment. | Important for larger organizations with formal identity and access-management expectations. |
| Custom integrations and private APIs | Not part of the default public baseline beyond baseline hooks and examples. | Quote-specific connectors, private APIs, SIEM/SOAR design, and environment-specific adapters. | Needed when SA-NOM must plug into real enterprise systems and delivery workflows. |
| Air-gapped and sovereign delivery | The public baseline supports a private-first story and self-managed deployment. | Full air-gapped rollout planning, sovereign packaging, and environment-specific hardening. | Critical for government, defense, and tightly controlled environments. |
| Compliance tailoring | Public baseline includes examples, security checklists, and Thai starter templates. | Detailed mapping, tailored controls, auditor-facing packaging, and regulated rollout guidance. | Helps teams move from a promising prototype to something defensible in regulated review. |
| Training, workshops, and rollout enablement | Self-serve docs only in the public baseline. | Architecture review, governance workshops, operator enablement, on-site training, and guided implementation. | Often the difference between a technical evaluation and a successful organizational rollout. |
| Pilot and commercial rollout path | Public repo and docs support self-managed evaluation. | Guided evaluation, paid pilot, or full commercial rollout depending on fit and scope. | Gives prospects a structured path from curiosity to production-track adoption. |

## Decision Guide

A prospect is usually a strong `community baseline` fit when:
- they want a self-managed evaluation first
- they are comfortable operating the public baseline without direct vendor support
- they do not need enterprise identity, custom integrations, or rollout services immediately

A prospect is usually a strong `guided / commercial` fit when:
- they want production support, rollout planning, or formal response expectations
- they operate in a regulated, sovereign, or air-gapped environment
- they need enterprise packaging, custom integration work, or tailored compliance help
- they already have a real sponsor, workflow, and deployment target in mind

## Related Documents

- [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md)
- [COMMERCIAL_DISCOVERY_CHECKLIST.md](COMMERCIAL_DISCOVERY_CHECKLIST.md)
- [SALES_INTAKE_TEMPLATE.md](SALES_INTAKE_TEMPLATE.md)
- [PRODUCT_TOUR.md](PRODUCT_TOUR.md)
- [LIVE_CUSTOMER_WALKTHROUGH.md](LIVE_CUSTOMER_WALKTHROUGH.md)
- [LIVE_CUSTOMER_WALKTHROUGH_TH.md](LIVE_CUSTOMER_WALKTHROUGH_TH.md)


