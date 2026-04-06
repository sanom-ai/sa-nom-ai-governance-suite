from pathlib import Path

from _bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()



PTAG_SAMPLE = """
language "PTAG"
role SAFETY_ANALYST {
  title: "Safety Analyst"
  reports_to: GOV
  escalation_to: GOV
  safety_owner: GOV
}
""".strip()


def _build_sample_assessment():
    from sa_nom_governance.ptag.pt_oss_engine import PTOSSEngine
    from sa_nom_governance.studio.role_private_studio_models import (
        NormalizedRoleSpec,
        StructuredJD,
    )

    foundation_path = Path(__file__).resolve().parents[1] / "resources" / "pt_oss" / "pt_oss_foundation.json"
    engine = PTOSSEngine(foundation_path)
    structured_jd = StructuredJD(
        role_name="Safety Analyst",
        purpose="Review safety-sensitive operational changes.",
        reporting_line="GOV",
        business_domain="product_safety",
        responsibilities=["review incidents", "flag unsafe changes"],
        allowed_actions=["review_incident", "flag_safety_risk"],
        handled_resources=["runtime", "policy"],
        financial_sensitivity="medium",
        legal_sensitivity="high",
        compliance_sensitivity="high",
    )
    normalized = NormalizedRoleSpec(
        role_id="SAFETY_ANALYST",
        title="Safety Analyst",
        purpose=structured_jd.purpose,
        reports_to="GOV",
        domain="product_safety",
        responsibilities=structured_jd.responsibilities,
        allowed_actions=structured_jd.allowed_actions,
        wait_human_actions=["approve_safety_exception"],
        handled_resources=structured_jd.handled_resources,
        sensitivity_profile={
            "financial": structured_jd.financial_sensitivity,
            "legal": structured_jd.legal_sensitivity,
            "compliance": structured_jd.compliance_sensitivity,
        },
    )
    return engine.assess_role_draft(
        structured_jd=structured_jd,
        normalized_spec=normalized,
        validation_report=None,
        simulation_report=None,
        current_ptag=PTAG_SAMPLE,
        generated_ptag=PTAG_SAMPLE,
    )


def build_markdown_summary() -> str:
    assessment = _build_sample_assessment()
    lines = [
        "## PT-OSS Advisory",
        f"- mode: `{assessment.mode}`",
        f"- posture: `{assessment.posture}`",
        f"- readiness_score: `{assessment.readiness_score}`",
        f"- blockers: `{len(assessment.blockers)}`",
    ]

    top_metrics = sorted(assessment.metrics, key=lambda item: item.value, reverse=True)[:3]
    lines.append("- top_metrics:")
    for metric in top_metrics:
        lines.append(f"  - `{metric.metric_id}` = `{metric.value}` ({metric.risk_level})")

    if assessment.blockers:
        lines.append("- blocker_messages:")
        for blocker in assessment.blockers[:3]:
            lines.append(f"  - {blocker.message}")

    return "\n".join(lines)


def main() -> int:
    print(build_markdown_summary())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

