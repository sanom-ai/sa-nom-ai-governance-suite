from pathlib import Path
from unittest.mock import patch

from sa_nom_governance.api.api_engine import build_engine_app
from sa_nom_governance.studio.role_private_studio_models import PTOSSAssessment, PTOSSIssue
from sa_nom_governance.utils.config import AppConfig


def build_test_app(runtime_dir: Path):
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


def test_operational_readiness_reports_operator_pressure_and_backlogs(tmp_path: Path) -> None:
    app = build_test_app(tmp_path)

    pending = app.request(
        requester="tester",
        role_id="LEGAL",
        action="review_contract",
        payload={"resource": "contract", "resource_id": "OP-001", "amount": 1000000},
        metadata={
            "authority_contract": {"approval_gate": "human_required"},
            "execution_plan": {
                "plan_id": "plan-operational-001",
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

    with patch.object(app.engine, "_process_once", side_effect=ConnectionError("transient network")):
        failed = app.request(
            requester="tester",
            role_id="GOV",
            action="review_audit",
            payload={"resource": "audit", "resource_id": "OP-REC-001"},
            metadata={"runtime_retry_max_attempts": 1},
        )
    assert failed.outcome == "retryable"

    app.human_ask.create_session(
        {
            "role_id": "GOV",
            "prompt": "Approve this governance policy for release.",
            "metadata": {
                "execution_plan": {
                    "plan_id": "plan-operational-002",
                    "step_id": "step-human-review",
                    "previous_step_id": "step-routing",
                },
                "origin_request_id": "req-operational-002",
                "task_packet": {
                    "packet_id": "packet-operational-002",
                    "packet_type": "runtime_step",
                    "source_role": "GOV",
                    "target_role": "EXEC_OWNER",
                    "workflow_id": "plan-operational-002",
                    "step_id": "step-human-review",
                    "packet_status": "prepared",
                },
            },
        },
        requested_by="EXEC_OWNER",
    )

    original_assess_runtime_role = app.human_ask._assess_runtime_role
    app.human_ask._assess_runtime_role = lambda entry: PTOSSAssessment(
        assessment_id="ptoss-operational-clearance",
        generated_at="2026-01-01T00:00:00+00:00",
        mode="PT_OSS_FULL",
        posture="critical",
        readiness_score=20,
        metrics=[],
        blockers=[
            PTOSSIssue(
                category="fragility",
                severity="critical",
                message="Structural fragility is above the safe threshold.",
                blocks_publish=True,
            )
        ],
        recommendations=["Pause runtime use of this hat until fragility is reduced."],
        context={},
    )
    try:
        app.human_ask.create_session(
            {
                "role_id": "GOV",
                "prompt": "Please report the current governance posture and next safe action.",
            },
            requested_by="EXEC_OWNER",
        )
    finally:
        app.human_ask._assess_runtime_role = original_assess_runtime_role

    readiness = app.operational_readiness(limit=20)

    assert readiness["status"] == "attention_required"
    assert readiness["summary"]["blocked_workflow_total"] == 1
    assert readiness["summary"]["human_action_total"] == 0
    assert readiness["summary"]["clearance_total"] == 1
    assert readiness["summary"]["guarded_follow_up_total"] == 1
    assert readiness["summary"]["dead_letter_total"] == 1
    assert set(readiness["action_required"]) == {
        "clearance_review",
        "guarded_follow_up",
        "recovery_resume",
    }
    assert len(readiness["operator_visibility"]["workflow_backlog"]) >= 2
    assert len(readiness["operator_visibility"]["human_decision_inbox"]) >= 2
    assert len(readiness["operator_visibility"]["runtime_recovery_backlog"]) == 1
    assert len(readiness["operator_visibility"]["runtime_dead_letters"]) == 1


def test_operational_readiness_is_ready_when_no_operator_action_is_pending(tmp_path: Path) -> None:
    app = build_test_app(tmp_path)

    result = app.request(
        requester="tester",
        role_id="LEGAL",
        action="review_contract",
        payload={"resource": "contract", "resource_id": "OP-READY-001", "amount": 3000000},
        metadata={
            "execution_plan": {
                "plan_id": "plan-operational-ready-001",
                "step_id": "step-review",
                "intent": "Review governed contract packet",
                "expected_output": "Structured review summary",
                "stop_condition": "summary_ready",
                "step_index": 1,
                "total_steps": 1,
            }
        },
    )

    assert result.outcome == "approved"
    readiness = app.operational_readiness(limit=20)

    assert readiness["status"] == "ready"
    assert readiness["summary"]["workflow_total"] == 1
    assert readiness["summary"]["active_workflow_total"] == 0
    assert readiness["summary"]["action_required_total"] == 0
    assert readiness["action_required"] == []
