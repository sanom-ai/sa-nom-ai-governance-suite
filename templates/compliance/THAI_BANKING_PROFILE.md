# Thai Banking Compliance Starter Profile

Use this profile as a working template for banking or fintech deployments that need stronger governance, auditability, cyber resilience, and third-party model oversight.

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
