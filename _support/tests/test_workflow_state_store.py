from pathlib import Path

from sa_nom_governance.api.api_engine import build_engine_app
from sa_nom_governance.utils.config import AppConfig


def build_persistent_test_app(runtime_dir: Path):
    config = AppConfig(persist_runtime=True)
    runtime_dir.mkdir(parents=True, exist_ok=True)
    config.audit_log_path = runtime_dir / "runtime_audit_log.jsonl"
    config.override_store_path = runtime_dir / "runtime_override_store.json"
    config.lock_store_path = runtime_dir / "runtime_lock_store.json"
    config.consistency_store_path = runtime_dir / "runtime_consistency_store.json"
    config.workflow_state_store_path = runtime_dir / "runtime_workflow_state_store.json"
    return build_engine_app(config)


def test_workflow_state_store_persists_execution_plan_snapshot_across_restart(tmp_path: Path) -> None:
    app = build_persistent_test_app(tmp_path)

    result = app.request(
        requester="tester",
        role_id="LEGAL",
        action="review_contract",
        payload={"resource": "contract", "resource_id": "WF-STATE-1", "amount": 3000000},
        metadata={
            "execution_plan": {
                "plan_id": "plan-state-001",
                "step_id": "step-review",
                "intent": "Review governed contract packet",
                "expected_output": "Structured review summary",
                "stop_condition": "summary_ready",
                "step_index": 1,
                "total_steps": 2,
            }
        },
    )

    assert result.outcome == "approved"
    state = app.get_workflow_state("plan-state-001")
    assert state["workflow_id"] == "plan-state-001"
    assert state["current_state"] == "completed"
    assert state["step_id"] == "step-review"
    assert state["plan_id"] == "plan-state-001"
    assert state["source"] == "runtime_result"
    assert state["revision"] >= 2

    restarted = build_persistent_test_app(tmp_path)
    reloaded = restarted.get_workflow_state("plan-state-001")
    assert reloaded["workflow_id"] == "plan-state-001"
    assert reloaded["request_id"] == state["request_id"]
    assert reloaded["current_state"] == "completed"

    summary = restarted.health()["workflow_state"]
    assert summary["total"] == 1
    assert summary["states"]["completed"] == 1


def test_workflow_state_store_updates_same_plan_after_override_resume(tmp_path: Path) -> None:
    app = build_persistent_test_app(tmp_path)

    pending = app.request(
        requester="tester",
        role_id="LEGAL",
        action="review_contract",
        payload={"resource": "contract", "resource_id": "WF-STATE-2", "amount": 1000000},
        metadata={
            "authority_contract": {"approval_gate": "human_required"},
            "execution_plan": {
                "plan_id": "plan-state-002",
                "step_id": "step-human-check",
                "intent": "Prepare contract approval bundle",
                "expected_output": "Human review package",
                "stop_condition": "human_checkpoint",
                "step_index": 2,
                "total_steps": 4,
                "checkpoint_required": True,
                "checkpoint_policy_basis_prefix": "runtime.authority_contract",
            },
        },
    )

    assert pending.outcome == "human_required"
    before = app.get_workflow_state("plan-state-002")
    assert before["current_state"] == "awaiting_human_confirmation"
    assert before["role_state"] == "paused_for_human"

    review = app.approve_override(pending.human_override["request_id"], resolved_by="EXEC_OWNER", note="Resume workflow test.")
    assert review.status == "approved"
    assert review.execution_result is not None
    assert review.execution_result["outcome"] == "approved"

    after = app.get_workflow_state("plan-state-002")
    assert after["current_state"] == "completed"
    assert after["role_state"] == "completed"
    assert after["source"] == "override_review"
    assert after["revision"] > before["revision"]

    restarted = build_persistent_test_app(tmp_path)
    reloaded = restarted.get_workflow_state("plan-state-002")
    assert reloaded["current_state"] == "completed"
    assert reloaded["source"] == "override_review"
