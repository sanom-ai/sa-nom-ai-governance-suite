from unittest.mock import patch

from sa_nom_governance.api.api_engine import build_engine_app
from sa_nom_governance.core.decision_engine import DecisionEngine
from sa_nom_governance.core.execution_context import ExecutionContext
from sa_nom_governance.ptag.ptag_parser import PTAGParser
from sa_nom_governance.ptag.ptag_semantic import SemanticAnalyzer
from sa_nom_governance.utils.config import AppConfig


def build_test_app():
    return build_engine_app(AppConfig(persist_runtime=False))


def build_semantic_document(source: str):
    document = PTAGParser().parse(source)
    return SemanticAnalyzer().analyze(document)


def test_decision_engine_emits_trigger_action_plan_for_global_harmony_context() -> None:
    semantic = build_semantic_document(
        '''
language "PTAG"
module "TRIGGER_RUNTIME"
version "1.0.0"
owner "EXEC_OWNER"

role LEGAL {
  title: "Legal"
}

authority LEGAL {
  allow: review_contract
}

policy CULTURAL_FRICTION_GUARD {
  WHEN action in [review_contract] AND region == "eu" AND audience == "external"
  THEN apply_policy_pack("EU_PRIVACY"), require_approval("LEGAL"), log_evidence("gdpr_guard")
  ELSE approve
}
'''
    )
    context = ExecutionContext(
        requester="tester",
        action="review_contract",
        role_id="LEGAL",
        payload={"resource": "contract", "resource_id": "TR-1", "amount": 1000},
        risk_score=0.2,
        metadata={
            "global_harmony": {
                "region_id": "eu",
                "context": {"audience": "external"},
            }
        },
    )

    result = DecisionEngine().decide(context, semantic)

    assert result.outcome == "waiting_human"
    assert result.policy_basis == "CULTURAL_FRICTION_GUARD"
    assert result.trace.source_id == "CULTURAL_FRICTION_GUARD"
    assert "Human approval requested through LEGAL." in result.trace.notes

    trigger_runtime = context.metadata["ptag_trigger_runtime"]
    assert trigger_runtime["branch"] == "then"
    assert trigger_runtime["requires_approval"] is True
    assert trigger_runtime["approval_role"] == "LEGAL"
    assert trigger_runtime["policy_packs"] == ["EU_PRIVACY"]
    assert trigger_runtime["evidence_tags"] == ["gdpr_guard"]
    assert trigger_runtime["terminal_outcome"] == "waiting_human"


def test_decision_engine_uses_else_branch_for_resonance_fallback() -> None:
    semantic = build_semantic_document(
        '''
language "PTAG"
module "TRIGGER_RUNTIME"
version "1.0.0"
owner "EXEC_OWNER"

role BRAND {
  title: "Brand"
}

authority BRAND {
  allow: send_customer_reply
}

policy BRAND_GUARD {
  WHEN action == send_customer_reply AND resonance_score < 0.85
  THEN approve
  ELSE rewrite_tone("diplomatic"), wait_human
}
'''
    )
    context = ExecutionContext(
        requester="tester",
        action="send_customer_reply",
        role_id="BRAND",
        payload={"resource": "message", "resource_id": "TR-2"},
        metadata={"resonance_score": 0.94},
    )

    result = DecisionEngine().decide(context, semantic)

    assert result.outcome == "waiting_human"
    assert result.policy_basis == "BRAND_GUARD"
    trigger_runtime = context.metadata["ptag_trigger_runtime"]
    assert trigger_runtime["branch"] == "else"
    assert trigger_runtime["tone_profile"] == "diplomatic"
    assert trigger_runtime["terminal_outcome"] == "waiting_human"


def test_runtime_human_override_uses_trigger_approval_role() -> None:
    app = build_test_app()
    semantic = build_semantic_document(
        '''
language "PTAG"
module "TRIGGER_RUNTIME"
version "1.0.0"
owner "EXEC_OWNER"

role LEGAL {
  title: "Legal"
}

authority LEGAL {
  allow: review_contract
}

policy REVIEW_GATE {
  WHEN action == review_contract AND audience == "external"
  THEN require_approval("LEGAL"), log_evidence("external_review_gate")
  ELSE approve
}
'''
    )

    with patch.object(app.engine.role_loader, "load", return_value=semantic):
        pending = app.request(
            requester="operator.tawan",
            role_id="LEGAL",
            action="review_contract",
            payload={"resource": "contract", "resource_id": "TR-3", "amount": 1000000},
            metadata={"audience": "external"},
        )

        assert pending.outcome == "waiting_human"
        assert pending.human_override is not None
        assert pending.human_override["approver_role"] == "LEGAL"
        trigger_runtime = pending.metadata["metadata"]["ptag_trigger_runtime"]
        assert trigger_runtime["approval_role"] == "LEGAL"
        assert trigger_runtime["evidence_tags"] == ["external_review_gate"]
        policy_runtime = pending.metadata["metadata"]["policy_runtime"]
        assert policy_runtime["approval_role"] == "LEGAL"
        assert policy_runtime["evidence_tags"] == ["external_review_gate"]

        reviewed = app.approve_override(
            pending.human_override["request_id"],
            resolved_by="LEGAL",
            note="Approved trigger runtime test.",
        )

    assert reviewed.execution_result is not None
    execution_result = reviewed.execution_result
    assert execution_result["outcome"] == "approved"
    resume_runtime = execution_result["metadata"]["metadata"]["ptag_trigger_runtime"]
    assert resume_runtime["approval_role"] == "LEGAL"
    assert resume_runtime["terminal_outcome"] == "approved"


def test_runtime_materializes_trigger_effects_into_metadata_and_audit_evidence() -> None:
    app = build_test_app()
    semantic = build_semantic_document(
        '''
language "PTAG"
module "TRIGGER_RUNTIME"
version "1.0.0"
owner "EXEC_OWNER"

role LEGAL {
  title: "Legal"
}

authority LEGAL {
  allow: review_contract
}

policy REVIEW_CONTEXT_PACK {
  WHEN action == review_contract AND region == "eu" AND audience == "external"
  THEN apply_policy_pack("EU_PRIVACY"), rewrite_tone("diplomatic"), log_evidence("gdpr_guard"), approve
  ELSE escalate
}
'''
    )

    with patch.object(app.engine.role_loader, "load", return_value=semantic):
        result = app.request(
            requester="operator.tawan",
            role_id="LEGAL",
            action="review_contract",
            payload={"resource": "contract", "resource_id": "TR-4", "amount": 1000000},
            metadata={
                "region": "eu",
                "audience": "external",
                "global_harmony": {
                    "context": {
                        "audience": "external",
                        "channel": "customer",
                        "sensitivity": "normal",
                        "tone": "neutral",
                    },
                    "draft_text": "Initial contract response.",
                },
            },
        )

    assert result.outcome == "approved"
    metadata = result.metadata["metadata"]
    policy_runtime = metadata["policy_runtime"]
    output_guidance = metadata["output_guidance"]
    harmony_runtime = metadata["global_harmony_runtime"]

    assert policy_runtime["source_policy_id"] == "REVIEW_CONTEXT_PACK"
    assert policy_runtime["active_policy_packs"] == ["EU_PRIVACY"]
    assert policy_runtime["evidence_tags"] == ["gdpr_guard"]
    assert output_guidance["tone_profile"] == "diplomatic"
    assert metadata["runtime_evidence_tags"] == ["gdpr_guard"]
    assert harmony_runtime["trigger_runtime"]["policy_packs"] == ["EU_PRIVACY"]
    assert harmony_runtime["trigger_runtime"]["tone_profile"] == "diplomatic"

    evidence = app.list_runtime_evidence(limit=1)[-1]
    assert evidence["trigger_policy_id"] == "REVIEW_CONTEXT_PACK"
    assert evidence["trigger_policy_packs"] == ["EU_PRIVACY"]
    assert evidence["trigger_evidence_tags"] == ["gdpr_guard"]
    assert evidence["trigger_tone_profile"] == "diplomatic"
