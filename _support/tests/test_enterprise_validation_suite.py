from pathlib import Path
from unittest.mock import patch

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
    config.runtime_recovery_store_path = runtime_dir / "runtime_recovery_store.json"
    config.runtime_dead_letter_path = runtime_dir / "runtime_dead_letter_log.jsonl"
    config.human_ask_store_path = runtime_dir / "human_ask_store.json"
    return build_engine_app(config)


def test_enterprise_validation_suite_human_gate_resume_survives_restart(tmp_path: Path) -> None:
    app = build_persistent_test_app(tmp_path)

    pending = app.request(
        requester="tester",
        role_id="LEGAL",
        action="review_contract",
        payload={"resource": "contract", "resource_id": "EVS-HUMAN-001", "amount": 1000000},
        metadata={
            "authority_contract": {"approval_gate": "human_required"},
            "policy_contract": {
                "human_required": {
                    "required": True,
                    "required_policy_basis_prefix": "runtime.authority_contract",
                },
                "override_path": {
                    "required": True,
                    "required_policy_basis_prefix": "runtime.authority_contract",
                    "required_approver_role": "GOV",
                },
            },
            "execution_plan": {
                "plan_id": "plan-evs-human-001",
                "step_id": "step-human-check",
                "intent": "Prepare contract approval bundle",
                "expected_output": "Human review package",
                "stop_condition": "human_checkpoint",
                "step_index": 2,
                "total_steps": 4,
                "checkpoint_required": True,
                "checkpoint_policy_basis_prefix": "runtime.authority_contract",
            },
            "task_packet": {
                "packet_id": "packet-evs-human-001",
                "packet_type": "runtime_step",
                "source_role": "LEGAL",
                "target_role": "GOV",
                "workflow_id": "plan-evs-human-001",
                "step_id": "step-human-check",
                "packet_status": "prepared",
            },
        },
    )

    assert pending.outcome == "human_required"
    assert pending.human_override is not None

    before = app.get_workflow_state("plan-evs-human-001")
    readiness_before = app.operational_readiness(limit=20)

    assert before["current_state"] == "awaiting_human_confirmation"
    assert before["role_state"] == "paused_for_human"
    assert readiness_before["status"] == "monitoring"
    assert readiness_before["summary"]["blocked_workflow_total"] == 1

    reviewed = app.approve_override(
        pending.human_override["request_id"],
        resolved_by="EXEC_OWNER",
        note="Enterprise validation suite human gate resume.",
    )

    assert reviewed.status == "approved"
    assert reviewed.execution_result is not None
    assert reviewed.execution_result["outcome"] == "approved"

    after = app.get_workflow_state("plan-evs-human-001")
    readiness_after = app.operational_readiness(limit=20)

    assert after["current_state"] == "completed"
    assert after["source"] == "override_review"
    assert readiness_after["status"] == "ready"
    assert readiness_after["summary"]["action_required_total"] == 0

    restarted = build_persistent_test_app(tmp_path)
    reloaded = restarted.get_workflow_state("plan-evs-human-001")
    readiness_reloaded = restarted.operational_readiness(limit=20)

    assert reloaded["current_state"] == "completed"
    assert reloaded["request_id"] == after["request_id"]
    assert readiness_reloaded["status"] == "ready"
    assert readiness_reloaded["summary"]["workflow_total"] == 1


def test_enterprise_validation_suite_recovery_resume_survives_restart(tmp_path: Path) -> None:
    app = build_persistent_test_app(tmp_path)

    with patch.object(app.engine, "_process_once", side_effect=TimeoutError("temporary timeout")):
        failed = app.request(
            requester="tester",
            role_id="GOV",
            action="review_audit",
            payload={"resource": "audit", "resource_id": "EVS-REC-001"},
            metadata={
                "runtime_retry_max_attempts": 1,
                "execution_plan": {
                    "plan_id": "plan-evs-recovery-001",
                    "step_id": "step-recovery-check",
                    "intent": "Run governed recovery validation",
                    "expected_output": "Recovery-ready replay path",
                    "stop_condition": "recovery_resolved",
                    "step_index": 1,
                    "total_steps": 2,
                },
            },
        )

    assert failed.outcome == "retryable"

    readiness_before = app.operational_readiness(limit=20)
    recovery_before = app.list_runtime_recovery_records(status="dead_letter", limit=10)

    assert readiness_before["status"] == "attention_required"
    assert readiness_before["summary"]["dead_letter_total"] == 1
    assert readiness_before["summary"]["action_required_total"] == 1
    assert readiness_before["action_required"] == ["recovery_resume"]
    assert len(recovery_before) == 1
    assert recovery_before[0]["request_id"] == failed.metadata["request_id"]

    resumed = app.resume_runtime_recovery(failed.metadata["request_id"], resumed_by="EXEC_OWNER")
    assert resumed.outcome == "approved"

    readiness_after = app.operational_readiness(limit=20)
    recovery_after = app.list_runtime_recovery_records(limit=10)

    assert readiness_after["status"] == "ready"
    assert readiness_after["summary"]["dead_letter_total"] == 0
    assert readiness_after["summary"]["action_required_total"] == 0
    assert recovery_after[0]["status"] == "resumed"
    assert recovery_after[0]["resumed_by"] == "EXEC_OWNER"

    restarted = build_persistent_test_app(tmp_path)
    reloaded_recovery = restarted.list_runtime_recovery_records(limit=10)
    readiness_reloaded = restarted.operational_readiness(limit=20)

    assert reloaded_recovery[0]["status"] == "resumed"
    assert reloaded_recovery[0]["resumed_request_id"] == resumed.metadata["request_id"]
    assert readiness_reloaded["status"] == "ready"
    assert readiness_reloaded["summary"]["recovery_total"] == 1
    assert readiness_reloaded["summary"]["dead_letter_event_total"] == 1
