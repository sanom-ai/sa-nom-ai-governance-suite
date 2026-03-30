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
| PTAG parsing and validation | Included in the public baseline as the policy and role-governance language layer used to define roles, authority boundaries, constraints, and policy logic in a structured, reviewable way. PTAG is a proprietary framework developed by the creator and integrated into SA-NOM as a foundational governance layer. | Tailored policy modeling support, assisted role design, and organization-specific PTAG authoring patterns. | Gives teams a structured way to define governed AI roles instead of relying on prompt-only behavior. |
| Private Rule Studio and Private Rule Positions | Included in the public baseline. Teams can upload their own JD inputs, start from starter JD/rule/hat materials, and create organization-specific `Private Rule Positions` without artificial rule-count limits. | Tailored rule design workshops, industry-specific starter libraries, publication governance support, and rollout-specific operating models. | This is how SA-NOM supports custom hats that only make sense inside one organization, not only standard role templates. |
| Role Private Studio | Included in the public baseline with role-authoring workflows, history, and publication flow. | Assisted template design, publication workflow extensions, and guided operating models for enterprise teams. | Helps teams move from job descriptions, Private Rule Positions, and role intent into governed AI roles faster. |
| Governed Document Center | Concept surfaced in the public product story as the controlled document system for creating, organizing, approving, publishing, and retaining policies, standards, procedures, forms, templates, and records under role-based authority and audit-ready governance. The preferred design is a single governed base template shaped by rules for document class, lifecycle, authority, numbering, release behavior, approval routing, numbering/metadata standards, and Human Ask reporting and retention/records governance. | Tailored document models, controlled-template libraries, rollout design, records-governance support, and organization-specific approval workflows. | Extends SA-NOM from governed AI roles into governed document work, where AI handles routine document activity and humans step in only for approvals, exceptions, waivers, and higher-risk control decisions. |

