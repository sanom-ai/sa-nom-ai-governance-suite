import json
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
    config.runtime_evidence_dir = runtime_dir / "runtime_evidence"
    return build_engine_app(config)


def test_workflow_proof_bundle_exports_workflow_human_and_audit_artifacts(tmp_path: Path) -> None:
    app = build_persistent_test_app(tmp_path)

    pending = app.request(
        requester="tester",
        role_id="LEGAL",
        action="review_contract",
        payload={"resource": "contract", "resource_id": "WPF-001", "amount": 1000000},
        metadata={
            "authority_contract": {"approval_gate": "human_required"},
            "execution_plan": {
                "plan_id": "plan-proof-001",
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
                "packet_id": "packet-proof-001",
                "packet_type": "runtime_step",
                "source_role": "LEGAL",
                "target_role": "GOV",
                "workflow_id": "plan-proof-001",
                "step_id": "step-human-check",
                "packet_status": "prepared",
            },
        },
    )
    assert pending.outcome == "human_required"

    app.create_human_ask_session(
        {
            "role_id": "GOV",
            "prompt": "Approve this governance policy for release.",
            "metadata": {
                "execution_plan": {
                    "plan_id": "plan-proof-001",
                    "step_id": "step-human-check",
                    "previous_step_id": "step-routing",
                },
                "origin_request_id": pending.metadata["request_id"],
                "task_packet": {
                    "packet_id": "packet-proof-001",
                    "packet_type": "runtime_step",
                    "source_role": "LEGAL",
                    "target_role": "GOV",
                    "workflow_id": "plan-proof-001",
                    "step_id": "step-human-check",
                    "packet_status": "prepared",
                },
            },
        },
        requested_by="EXEC_OWNER",
    )

    reviewed = app.approve_override(
        pending.human_override["request_id"],
        resolved_by="EXEC_OWNER",
        note="Workflow proof bundle validation.",
    )
    assert reviewed.execution_result is not None

    bundle = app.create_workflow_proof_bundle("plan-proof-001", requested_by="EXEC_OWNER")
    listed = app.list_workflow_proof_bundles(limit=10)

    assert bundle["bundle_type"] == "workflow_proof"
    assert bundle["workflow_id"] == "plan-proof-001"
    assert bundle["human_session_total"] >= 1
    assert bundle["audit_excerpt_total"] >= 1
    assert listed[0]["bundle_id"] == bundle["bundle_id"]
    assert listed[0]["workflow_id"] == "plan-proof-001"

    manifest_path = Path(bundle["export_path"]) / "manifest.json"
    workflow_state_path = Path(bundle["export_path"]) / "artifacts" / "workflow_state.json"
    human_sessions_path = Path(bundle["export_path"]) / "artifacts" / "human_sessions.json"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    workflow_state = json.loads(workflow_state_path.read_text(encoding="utf-8"))
    human_sessions = json.loads(human_sessions_path.read_text(encoding="utf-8"))

    assert manifest["bundle_id"] == bundle["bundle_id"]
    assert manifest["workflow_state"]["current_state"] == "completed"
    assert workflow_state["workflow_id"] == "plan-proof-001"
    assert any(
        session.get("metadata", {}).get("origin_request_id") == pending.metadata["request_id"]
        or session.get("metadata", {}).get("human_decision_inbox", {}).get("execution_plan", {}).get("plan_id") == "plan-proof-001"
        for session in human_sessions
    )


def test_workflow_proof_bundle_captures_recovery_artifacts_for_failed_then_resumed_workflow(tmp_path: Path) -> None:
    app = build_persistent_test_app(tmp_path)

    with patch.object(app.engine, "_process_once", side_effect=TimeoutError("temporary timeout")):
        failed = app.request(
            requester="tester",
            role_id="GOV",
            action="review_audit",
            payload={"resource": "audit", "resource_id": "WPF-REC-001"},
            metadata={
                "runtime_retry_max_attempts": 1,
                "execution_plan": {
                    "plan_id": "plan-proof-recovery-001",
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

    resumed = app.resume_runtime_recovery(failed.metadata["request_id"], resumed_by="EXEC_OWNER")
    assert resumed.outcome == "approved"

    bundle = app.create_workflow_proof_bundle("plan-proof-recovery-001", requested_by="EXEC_OWNER")

    recovery_records_path = Path(bundle["export_path"]) / "artifacts" / "recovery_records.json"
    dead_letters_path = Path(bundle["export_path"]) / "artifacts" / "dead_letters.json"

    recovery_records = json.loads(recovery_records_path.read_text(encoding="utf-8"))
    dead_letters = json.loads(dead_letters_path.read_text(encoding="utf-8"))

    assert bundle["recovery_total"] == 1
    assert bundle["dead_letter_total"] == 1
    assert recovery_records[0]["status"] == "resumed"
    assert recovery_records[0]["resumed_request_id"] == resumed.metadata["request_id"]
    assert dead_letters[0]["request_id"] == failed.metadata["request_id"]
