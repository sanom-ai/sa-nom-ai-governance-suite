# ISO 42001 And NIST AI RMF Crosswalk

This note gives a public-facing crosswalk between SA-NOM's current governance posture and two important AI governance references:

- ISO/IEC 42001:2023
- NIST AI Risk Management Framework

This is a starter crosswalk, not a conformity statement.

## Why This Document Exists

Buyers, compliance teams, and regulators often ask whether an AI governance platform can be understood through recognized standards language.

SA-NOM already aligns with many governance ideas these frameworks care about, but the repo has not yet mapped them directly enough for regulated conversations.

## Crosswalk Table

| Area | SA-NOM Baseline | Standards Reading | Current Position |
| --- | --- | --- | --- |
| AI role definition and bounded responsibility | Governed role packs, Role Private Studio, organization-defined governed hats | Governance structure, accountable scope, defined AI system roles | Included baseline |
| Human involvement | Human Ask, override, escalation boundaries | Human oversight and accountability controls | Included baseline |
| Auditability and evidence | Audit chain, evidence-oriented execution, response and scenario artifacts | Traceability, reviewability, documented controls | Included baseline |
| Risk-aware operational routing | Authority guard, escalation, review-and-escalation patterns | Risk treatment and control operation | Included baseline |
| Deployment and runtime readiness | Startup checks, smoke tests, deployment guides | Operational control readiness and implementation discipline | Included baseline |
| Standards-specific policy mapping | Cross-reference from SA-NOM artifacts into clause-level or function-level expectations | Formal framework mapping and implementation planning | Partial mapping |
| Organization-wide AI management system | Named AI management system structure, policy owners, management review cadence | ISO/IEC 42001 management-system maturity | Legal review required |
| Formal risk inventory and control register mapped to the standards | Cross-functional governance story and examples | Standardized risk register and control ownership | Partial mapping |
| Supplier and third-party AI governance | Procurement, supplier-risk, and regulator-response lanes | Third-party oversight and lifecycle governance | Included baseline, but still partial for full standards coverage |
| Formal conformity or certification path | Not provided by the public repo | Certification or audited conformity outcomes | Regulator filing not included |

## What SA-NOM Already Does Well

SA-NOM already supports several fundamentals that matter in both frameworks:
- explicit role and authority boundaries
- human oversight and escalation
- evidence retention
- operational readiness checks
- governance-oriented workflow design
- cross-functional control stories

These strengths make SA-NOM a strong starting platform for organizations that want to operationalize governed AI, not only document policies on paper.

## Where The Gaps Still Matter

The main gaps are not in the idea of governance. They are in the formal mapping layer:
- clause-by-clause or function-by-function traceability
- named accountable owners in the customer organization
- management-system operating cadence
- documented control evidence tied to a specific legal or standards program
- regulated-industry completion work

That is why this crosswalk should be read as a baseline map, not a conformity claim.

## Recommended Next Step For Regulated Teams

Regulated teams should use SA-NOM in this order:

1. Use SA-NOM to establish governed AI workflow and evidence posture
2. Map those workflows into the organization's own standards program
3. Validate gaps with legal, compliance, risk, and audit owners
4. Tailor evidence, controls, and review cadence before treating the result as standards-aligned delivery

## Summary

SA-NOM aligns well with the operational spirit of ISO/IEC 42001 and NIST AI RMF.

The public repo still needs:
- deeper formal mappings
- organization-specific control ownership
- legal and compliance tailoring

So the correct public claim is:

SA-NOM supports AI governance readiness and can anchor standards-oriented work, but the public repo alone should not be presented as completed ISO/IEC 42001 conformity or NIST AI RMF completion.
