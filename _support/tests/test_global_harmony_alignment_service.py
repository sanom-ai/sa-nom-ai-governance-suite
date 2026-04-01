from pathlib import Path

import pytest

from sa_nom_governance.alignment.alignment_service import GlobalHarmonyAlignmentService



def test_alignment_service_initializes_with_active_selection() -> None:
    service = GlobalHarmonyAlignmentService(Path("resources/alignment"))

    snapshot = service.build_runtime_snapshot()

    assert snapshot["active_selection"]["region_id"] == "eu"
    assert snapshot["active_selection"]["source"] == "catalog-default"
    assert snapshot["safe_claim"]
    assert snapshot["available_regions"]
    assert snapshot["switch_policy"]["requires_named_actor"] is True
    assert "evaluation" not in snapshot



def test_alignment_service_can_switch_active_region() -> None:
    service = GlobalHarmonyAlignmentService(Path("resources/alignment"))

    selection = service.select_region(
        "thailand",
        selected_by="operator.tawan",
        rationale="Customer-facing ASEAN pilot alignment.",
    )
    snapshot = service.build_runtime_snapshot()

    assert selection.region_id == "thailand"
    assert snapshot["active_selection"]["region_id"] == "thailand"
    assert snapshot["active_selection"]["selected_by"] == "operator.tawan"
    assert snapshot["active_selection"]["rationale"] == "Customer-facing ASEAN pilot alignment."



def test_alignment_service_rejects_switch_without_meaningful_rationale() -> None:
    service = GlobalHarmonyAlignmentService(Path("resources/alignment"))

    with pytest.raises(ValueError):
        service.select_region("thailand", selected_by="operator.tawan", rationale="too short")



def test_alignment_service_builds_runtime_evaluation_snapshot() -> None:
    service = GlobalHarmonyAlignmentService(Path("resources/alignment"))
    service.select_region(
        "usa",
        selected_by="operator.tawan",
        rationale="Accountability-first evaluation path.",
    )

    snapshot = service.build_runtime_snapshot(
        context={
            "audience": "customer",
            "channel": "public",
            "sensitivity": "regulated",
            "tone": "neutral",
            "owner_visible": False,
            "explanation_visible": True,
            "requires_approval": True,
        },
        draft_text="Provide a transparent policy explanation to the customer.",
    )

    assert snapshot["evaluation"]["status"] == "guarded"
    assert snapshot["evaluation"]["human_review_required"] is True
    concern_codes = {item["code"] for item in snapshot["evaluation"]["concerns"]}
    assert "OWNER_NOT_VISIBLE" in concern_codes
    assert snapshot["safe_claim"]
    assert snapshot["notes"]
