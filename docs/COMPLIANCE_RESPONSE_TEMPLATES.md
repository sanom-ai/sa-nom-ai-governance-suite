# Compliance Response Templates

This document provides starter answer patterns for a future compliance-aware AI layer in SA-NOM.

These are response templates, not final legal answers.

Each template is designed to stay within the `v0.1.7` baseline and avoid overclaiming regulator-ready status.

## How To Use These Templates

Each answer should do four things:
1. say what SA-NOM already supports
2. say what remains partial or outside the public repo
3. point to the right baseline document
4. say when legal, privacy, compliance, or regulator review is still required

## 1. "Is SA-NOM compliant with ISO/IEC 42001?"

Recommended answer pattern:

`SA-NOM supports many governance practices that align with ISO/IEC 42001, such as bounded roles, human oversight, auditability, and evidence-oriented workflows. The public repo should still be treated as a starter governance baseline and partial mapping, not as a completed ISO/IEC 42001 conformity statement. Formal alignment and any certification-facing work still require organization-specific control mapping and review.`

Follow with:
- [ISO 42001 and NIST AI RMF Crosswalk](ISO_42001_NIST_CROSSWALK.md)
- [Compliance Knowledge Baseline](COMPLIANCE_KNOWLEDGE_BASELINE.md)

## 2. "Can I use SA-NOM for PDPA and AI privacy compliance right away?"

Recommended answer pattern:

`SA-NOM helps with governance, evidence, human oversight, and private deployment posture, which are useful for privacy-aware AI operations. The public repo should not be presented as completed PDPA compliance on its own. Privacy analysis, lawful basis review, sensitive-data handling, and organization-specific privacy controls still require legal and privacy review.`

Follow with:
- [PDPA AI Guideline Map](PDPA_AI_GUIDELINE_MAP.md)
- [Compliance Knowledge Baseline](COMPLIANCE_KNOWLEDGE_BASELINE.md)

## 3. "If a foreign company uses SA-NOM in Thailand, does that solve local representative requirements?"

Recommended answer pattern:

`No. SA-NOM can support governance readiness, evidence posture, and regulator-response discipline, but it does not by itself create a local legal entity, local legal representative, or formal local accountability structure. This question should be treated as a legal-structure and deployment-readiness issue that still requires local legal review.`

Follow with:
- [Local Representative Readiness](LOCAL_REPRESENTATIVE_READINESS.md)
- [Thai AI Regulatory Gap Map](THAI_AI_REGULATORY_GAP_MAP.md)

## 4. "Can I send these templates directly to a regulator or auditor?"

Recommended answer pattern:

`The public templates are starter support for internal governance and control planning. They are not a completed filing pack, not a regulator-approved document set, and not a substitute for legal or compliance sign-off. They can help teams prepare evidence and structure the work, but final submission material still needs review and tailoring.`

Follow with:
- [Compliance Knowledge Baseline](COMPLIANCE_KNOWLEDGE_BASELINE.md)
- `templates/compliance/README.md`

## 5. "Is SA-NOM already compliant with Thailand AI regulation?"

Recommended answer pattern:

`SA-NOM supports governed AI operations, evidence discipline, and workflow readiness, which are strong internal-governance foundations. The public repo should still not be presented as automatically compliant with Thailand-specific AI obligations. Thailand-facing readiness depends on standards mapping depth, privacy review, local legal accountability, sector-specific interpretation, and possible regulator-facing tailoring.`

Follow with:
- [Thai AI Regulatory Gap Map](THAI_AI_REGULATORY_GAP_MAP.md)
- [Compliance Knowledge Baseline](COMPLIANCE_KNOWLEDGE_BASELINE.md)

## 6. "What should the AI say when it is unsure?"

Recommended answer pattern:

`This area goes beyond the current public baseline. SA-NOM can support the workflow and evidence posture, but a legal, privacy, compliance, or regulator review is still required before treating this as completed compliance.`

## Required Closing Patterns

When the skill layer answers compliance-adjacent questions, it should prefer closers like:
- `This is a starter baseline, not a final compliance filing.`
- `This area still requires legal or compliance review.`
- `The public repo should not be presented as regulator-ready on this point.`
- `SA-NOM supports the workflow and evidence posture, but formal completion may remain outside the software.`

## Patterns To Avoid

Do not answer with language like:
- `Yes, SA-NOM is compliant.`
- `You can submit this directly to the regulator.`
- `Self-hosting solves the legal requirement.`
- `The template is enough by itself.`
- `This guarantees ISO/IEC 42001 conformity.`

## Summary

These templates are meant to make the future AI layer:
- safer
- more honest
- more consistent
- easier to trust in regulated conversations
