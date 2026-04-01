from sa_nom_governance.api.api_engine import build_engine_app
from sa_nom_governance.utils.config import AppConfig


def build_test_app():
    return build_engine_app(AppConfig(persist_runtime=False))


def test_runtime_attaches_global_harmony_signal_for_low_risk_request() -> None:
    app = build_test_app()

    result = app.request(
        requester="operator.tawan",
        role_id="LEGAL",
        action="review_contract",
        payload={"resource": "contract", "resource_id": "GH-RT-1", "amount": 1000000},
        metadata={
            "global_harmony": {
                "region_id": "thailand",
                "selected_by": "operator.tawan",
                "rationale": "Internal ASEAN pilot alignment for low-risk review.",
                "context": {
                    "audience": "internal",
                    "channel": "internal",
                    "sensitivity": "normal",
                    "tone": "neutral",
                    "requires_approval": False,
                },
                "draft_text": "Internal coordination update.",
            }
        },
    )

    assert result.outcome == "approved"
    harmony = result.metadata["metadata"]["global_harmony_runtime"]
    assert harmony["mode"] == "requested_region_preview"
    assert harmony["selection_intent"]["action"] == "direct_switch"
    assert harmony["evaluation"]["status"] == "aligned"
    assert harmony["evaluation"]["resonance_band"] == "high"


def test_runtime_waits_for_human_when_global_harmony_requires_approval() -> None:
    app = build_test_app()

    result = app.request(
        requester="operator.tawan",
        role_id="LEGAL",
        action="review_contract",
        payload={"resource": "contract", "resource_id": "GH-RT-2", "amount": 1000000},
        metadata={
            "global_harmony": {
                "region_id": "thailand",
                "selected_by": "operator.tawan",
                "rationale": "Customer-facing ASEAN pilot alignment requiring review.",
                "context": {
                    "audience": "customer",
                    "channel": "public",
                    "sensitivity": "high",
                    "tone": "aggressive",
                    "requires_approval": False,
                },
                "draft_text": "Aggressive escalation message to a customer.",
            }
        },
    )

    assert result.outcome == "waiting_human"
    assert result.policy_basis == "runtime.global_harmony.selection"
    assert result.decision_trace["source_type"] == "global_harmony"
    assert result.human_override is not None
    harmony = result.metadata["metadata"]["global_harmony_runtime"]
    assert harmony["selection_intent"]["action"] == "require_approval"
    assert harmony["evaluation"]["status"] == "escalated"
    assert harmony["evaluation"]["resonance_band"] == "low"


def test_runtime_keeps_active_region_alignment_signal_in_metadata() -> None:
    app = build_test_app()

    result = app.request(
        requester="operator.tawan",
        role_id="LEGAL",
        action="review_contract",
        payload={"resource": "contract", "resource_id": "GH-RT-3", "amount": 1000000},
        metadata={
            "global_harmony": {
                "context": {
                    "audience": "customer",
                    "channel": "public",
                    "sensitivity": "regulated",
                    "tone": "neutral",
                    "explanation_visible": False,
                    "requires_approval": True,
                },
                "draft_text": "Provide a policy explanation to a customer.",
            }
        },
    )

    assert result.outcome == "approved"
    harmony = result.metadata["metadata"]["global_harmony_runtime"]
    assert harmony["mode"] == "active_runtime"
    assert harmony["region_id"] == "eu"
    assert harmony["evaluation"]["status"] == "guarded"
    assert harmony["evaluation"]["resonance_band"] == "moderate"
    concern_codes = {item["code"] for item in harmony["evaluation"]["concerns"]}
    assert "EXPLANATION_GAP" in concern_codes
