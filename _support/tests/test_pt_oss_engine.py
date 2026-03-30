from pathlib import Path

from sa_nom_governance.ptag.pt_oss_engine import PTOSSEngine
from sa_nom_governance.studio.role_private_studio_models import NormalizedRoleSpec, StructuredJD


def test_pt_oss_engine_assesses_role_draft() -> None:
    engine = PTOSSEngine(Path(__file__).resolve().parents[2] / "resources" / "pt_oss" / "pt_oss_foundation.json")
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
    ptag = """
language "PTAG"
role SAFETY_ANALYST {
  title: "Safety Analyst"
  reports_to: GOV
  escalation_to: GOV
  safety_owner: GOV
}
"""
    assessment = engine.assess_role_draft(
        structured_jd=structured_jd,
        normalized_spec=normalized,
        validation_report=None,
        simulation_report=None,
        current_ptag=ptag,
        generated_ptag=ptag,
    )

    assert assessment.mode in {"PT_OSS_FULL", "PT_OSS_FULL_CAL_TH", "PT_OSS_LITE"}
    assert assessment.metrics
    assert assessment.readiness_score >= 0
    assert any(metric.metric_id == "HOIS" for metric in assessment.metrics)
