# Thai Banking Compliance Starter Profile

Label: `Starter support`

Use this profile as a working template for banking or fintech deployments that need stronger governance, auditability, cyber resilience, and third-party model oversight.

Legal review required.
Regulator filing not included.

For the broader baseline, read:
- [Compliance Knowledge Baseline](../../docs/COMPLIANCE_KNOWLEDGE_BASELINE.md)
- [ISO 42001 and NIST AI RMF Crosswalk](../../docs/ISO_42001_NIST_CROSSWALK.md)
- [Thai AI Regulatory Gap Map](../../docs/THAI_AI_REGULATORY_GAP_MAP.md)
- [PDPA AI Guideline Map](../../docs/PDPA_AI_GUIDELINE_MAP.md)
- [Local Representative Readiness](../../docs/LOCAL_REPRESENTATIVE_READINESS.md)

## Regulatory Reference Points

- Bank of Thailand Cyber Resilience Framework: https://www.bot.or.th/content/dam/bot/fipcs/documents/FOG/2562/ThaiPDF/25620189.pdf
- Thailand PDPA Government Platform reference: https://gppc.pdpc.or.th/pdpa-course/

## Scope

- Organization: `<bank-or-financial-institution>`
- Environment: `<production / uat / dr>`
- Executive owner: `<name>`
- Security owner: `<name>`
- Compliance owner: `<name>`
- SA-NOM deployment mode: `<private / multi-org>`

## Control Workbook

| Control Area | Required Outcome | SA-NOM Evidence | Local Owner | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| Authority boundaries | Live roles define least-privilege boundaries and governed escalation. | Role packs, trusted registry manifest, role hierarchy snapshot | `<owner>` | `<planned/in-progress/complete>` | `<notes>` |
| Change governance | PTAG publication is signed, reviewed, and auditable. | Trusted registry verification, audit chain, studio publish trail | `<owner>` | `<planned/in-progress/complete>` | `<notes>` |
| Human oversight | Sensitive or high-risk requests stop at a human review boundary. | Human Ask sessions, override records, safety-owner mappings | `<owner>` | `<planned/in-progress/complete>` | `<notes>` |
| Provider risk | Hosted or local model providers are approved, probed, and monitored. | Provider probe report, outbound allowlist, vendor review | `<owner>` | `<planned/in-progress/complete>` | `<notes>` |
| Cyber resilience | Runtime backup, restore, and smoke validation are tested. | Backup summary, smoke report, deployment profile | `<owner>` | `<planned/in-progress/complete>` | `<notes>` |
| Evidence retention | Audit and evidence artifacts are retained and exportable. | Retention plan, evidence export manifest | `<owner>` | `<planned/in-progress/complete>` | `<notes>` |

## Minimum Evidence Pack

- Latest `python -m pytest _support/tests` result
- Latest startup smoke report
- Latest provider probe report
- Latest deployment profile and go-live readiness export
- Latest evidence export manifest
- Trusted registry manifest and signature verification result
- Backup and restore rehearsal summary

## Approval

- Security approval: `<name/date>`
- Compliance approval: `<name/date>`
- Business owner approval: `<name/date>`
