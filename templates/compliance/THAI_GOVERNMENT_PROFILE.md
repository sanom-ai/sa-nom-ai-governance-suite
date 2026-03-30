# Thai Government Compliance Starter Profile

Use this profile as a working template for Thai government or public-sector deployments that need private hosting, audit evidence, data handling discipline, and public-sector security review.

## Regulatory Reference Points

- Digital Government Development Agency security and testing posture: https://www.dga.or.th/en/citizenportal/
- Thailand PDPA Government Platform reference: https://gppc.pdpc.or.th/pdpa-course/

## Scope

- Agency / department: `<agency-name>`
- Environment: `<production / staging / air-gapped>`
- Executive owner: `<name>`
- Information-security owner: `<name>`
- Data protection owner: `<name>`
- SA-NOM deployment mode: `<private / multi-org>`

## Control Workbook

| Control Area | Required Outcome | SA-NOM Evidence | Local Owner | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| Data governance | Sensitive workflows are bound to approved roles and review paths. | Role packs, Human Ask records, retention policy | `<owner>` | `<planned/in-progress/complete>` | `<notes>` |
| Publication control | Role and policy changes are signed, reviewed, and traceable. | Trusted registry, audit chain, studio publish record | `<owner>` | `<planned/in-progress/complete>` | `<notes>` |
| Platform security | Deployment path has startup validation, security headers, backup continuity, and cluster hardening. | Deployment profile, smoke report, security audit checklist | `<owner>` | `<planned/in-progress/complete>` | `<notes>` |
| Provider governance | External or local LLM endpoints are approved, probed, and bounded by policy. | Provider probe report, configuration snapshot, egress review | `<owner>` | `<planned/in-progress/complete>` | `<notes>` |
| Evidence export | Agency reviewers can export evidence for internal audit or incident review. | Evidence export manifest, audit health, retention report | `<owner>` | `<planned/in-progress/complete>` | `<notes>` |
| Recovery continuity | Runtime state can be restored without losing critical governance evidence. | Backup summary, restore rehearsal notes | `<owner>` | `<planned/in-progress/complete>` | `<notes>` |

## Minimum Evidence Pack

- Latest startup smoke report
- Latest provider probe report
- Latest deployment profile
- Latest evidence export manifest
- Access-control health snapshot
- Backup and restore rehearsal summary
- Security audit checklist with sign-off

## Approval

- Information security approval: `<name/date>`
- Data protection approval: `<name/date>`
- Agency business owner approval: `<name/date>`
