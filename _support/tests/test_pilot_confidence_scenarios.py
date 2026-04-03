from pathlib import Path

from sa_nom_governance.api.api_engine import build_engine_app
from sa_nom_governance.dashboard.dashboard_data import DashboardSnapshotBuilder
from sa_nom_governance.dashboard.dashboard_server import DashboardService
from sa_nom_governance.guards.access_control import AccessControl, AccessProfile
from sa_nom_governance.utils.config import AppConfig


def _build_service(tmp_path: Path, *, persist_runtime: bool = False) -> DashboardService:
    config = AppConfig(
        base_dir=tmp_path,
        persist_runtime=persist_runtime,
        environment="development",
        api_token="owner-token",
        trusted_registry_signing_key="registry-key",
    )
    return DashboardService(config=config)


def _build_persistent_builder(tmp_path: Path) -> DashboardSnapshotBuilder:
    config = AppConfig(persist_runtime=True)
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    config.audit_log_path = runtime_dir / "runtime_audit_log.jsonl"
    config.override_store_path = runtime_dir / "runtime_override_store.json"
    config.lock_store_path = runtime_dir / "runtime_lock_store.json"
    config.consistency_store_path = runtime_dir / "runtime_consistency_store.json"
    config.workflow_state_store_path = runtime_dir / "runtime_workflow_state_store.json"
    config.runtime_recovery_store_path = runtime_dir / "runtime_recovery_store.json"
    config.runtime_dead_letter_path = runtime_dir / "runtime_dead_letter_log.jsonl"
    config.session_store_path = runtime_dir / "runtime_session_store.json"
    config.human_ask_store_path = runtime_dir / "human_ask_store.json"
    config.document_store_path = runtime_dir / "runtime_document_store.json"
    config.action_runtime_store_path = runtime_dir / "runtime_action_store.json"
    config.runtime_evidence_dir = runtime_dir / "runtime_evidence"
    app = build_engine_app(config)
    return DashboardSnapshotBuilder(config=config, app=app)


def _build_profile(
    role_name: str,
    *,
    extra_permissions: set[str] | None = None,
    wildcard: bool = False,
) -> AccessProfile:
    permissions = set(AccessControl.DEFAULT_PERMISSIONS[role_name])
    if extra_permissions:
        permissions.update(extra_permissions)
    if wildcard:
        permissions.add("*")
    return AccessProfile(
        profile_id=f"{role_name}-pilot",
        display_name=role_name.title(),
        role_name=role_name,
        permissions=permissions,
    )


def _linked_case(snapshot: dict[str, object], request_id: str) -> dict[str, object]:
    case_items = snapshot.get("cases", {}).get("items", [])
    return next(item for item in case_items if request_id in item.get("linked_request_ids", []))


def test_governed_document_release_scenario_keeps_request_action_and_document_in_one_case(
    tmp_path: Path,
) -> None:
    service = _build_service(tmp_path, persist_runtime=True)
    owner = _build_profile(
        "owner",
        extra_permissions={"documents.publish", "documents.archive"},
        wildcard=True,
    )
    reviewer = _build_profile("reviewer")

    request_result = service.app.request(
        requester="pilot@example.com",
        role_id="GOV",
        action="approve_policy",
        payload={"resource": "contract", "resource_id": "DOC-REL-001"},
        metadata={
            "execution_plan": {
                "plan_id": "plan-doc-release-001",
                "step_id": "step-release",
            }
        },
    )
    request_id = request_result.metadata["request_id"]

    initial_dashboard = service.dashboard(owner)
    initial_case = _linked_case(initial_dashboard, request_id)

    draft_action = service.create_action(
        {
            "action_type": "draft_document",
            "case_id": initial_case["case_id"],
        },
        owner,
    )
    document_id = draft_action["artifacts"][0]["ref_id"]

    service.submit_document_review(
        document_id,
        {"note": "Ready for governed release."},
        owner,
    )
    service.approve_document(
        document_id,
        {"note": "Approved for publication."},
        reviewer,
    )
    published = service.publish_document(
        document_id,
        {"note": "Published into the governed runtime."},
        owner,
    )

    dashboard = service.dashboard(owner)
    linked_case = _linked_case(dashboard, request_id)
    document_row = next(
        item for item in dashboard.get("documents", {}).get("items", []) if item.get("document_id") == document_id
    )
    action_row = next(
        item for item in dashboard.get("actions", {}).get("items", []) if item.get("action_id") == draft_action["action_id"]
    )
    filtered_documents = service.documents(case_id=linked_case["case_reference"], active_only=True)
    filtered_actions = service.actions(case_id=linked_case["case_id"])
    continuity = linked_case.get("continuity", {}) if isinstance(linked_case.get("continuity", {}), dict) else {}
    work_item_kinds = {
        entry.get("kind") for entry in linked_case.get("work_items", []) if int(entry.get("total", 0) or 0) > 0
    }

    assert published["status"] == "published"
    assert document_row.get("status") == "published"
    assert document_row.get("case_id") == linked_case.get("case_id")
    assert action_row.get("case_id") == linked_case.get("case_id")
    assert draft_action["action_id"] in linked_case.get("linked_action_ids", [])
    assert document_id in linked_case.get("linked_document_ids", [])
    assert {"request", "action", "document"}.issubset(work_item_kinds)
    assert continuity.get("next_view") in {"requests", "documents", "audit", "overrides", "conflicts"}
    assert continuity.get("evidence_posture") == "partial proof"
    assert filtered_documents.get("summary", {}).get("published_total", 0) >= 1
    assert filtered_documents.get("summary", {}).get("case_linked_total", 0) >= 1
    assert any(item.get("document_id") == document_id for item in filtered_documents.get("items", []))
    assert filtered_actions.get("summary", {}).get("document_artifact_total", 0) >= 1
    assert any(item.get("action_id") == draft_action["action_id"] for item in filtered_actions.get("items", []))
    assert dashboard.get("summary", {}).get("documents_published_total", 0) >= 1


def test_operational_exception_scenario_preserves_human_handoff_and_proof_continuity(
    tmp_path: Path,
) -> None:
    builder = _build_persistent_builder(tmp_path)

    pending = builder.app.request(
        requester="pilot@example.com",
        role_id="LEGAL",
        action="review_contract",
        payload={"resource": "contract", "resource_id": "OPS-EXC-001", "amount": 2500000},
        metadata={
            "authority_contract": {"approval_gate": "human_required"},
            "execution_plan": {
                "plan_id": "plan-ops-exception-001",
                "step_id": "step-human-check",
                "intent": "Resolve a governed operational exception",
                "expected_output": "Human-reviewed exception path",
                "stop_condition": "human_checkpoint",
                "step_index": 2,
                "total_steps": 4,
            },
        },
    )
    request_id = pending.metadata["request_id"]

    pre_resolution = builder.build()
    pre_case = _linked_case(pre_resolution, request_id)
    assert pre_case.get("status") in {"human_required", "attention_required", "active", "blocked"}
    assert (pre_case.get("continuity", {}) or {}).get("next_view") in {
        "overrides",
        "human_ask",
        "requests",
        "audit",
        "conflicts",
    }

    session = builder.app.create_human_ask_session(
        {
            "role_id": "GOV",
            "prompt": "Review the governed exception path and confirm the safe next move.",
            "metadata": {
                "origin_request_id": request_id,
                "execution_plan": {
                    "plan_id": "plan-ops-exception-001",
                    "step_id": "step-human-check",
                },
            },
        },
        requested_by="EXEC_OWNER",
    )
    builder.app.approve_override(
        pending.human_override["request_id"],
        resolved_by="EXEC_OWNER",
        note="Human boundary reviewed for pilot confidence scenario.",
    )
    proof_bundle = builder.app.create_workflow_proof_bundle(
        "plan-ops-exception-001",
        requested_by="EXEC_OWNER",
    )

    snapshot = builder.build()
    linked_case = _linked_case(snapshot, request_id)
    continuity = linked_case.get("continuity", {}) if isinstance(linked_case.get("continuity", {}), dict) else {}
    latest_proof = linked_case.get("latest_proof_event", {}) if isinstance(linked_case.get("latest_proof_event", {}), dict) else {}
    follow_up_views = {item.get("view") for item in continuity.get("follow_up_actions", []) if isinstance(item, dict)}
    work_item_kinds = {
        entry.get("kind") for entry in linked_case.get("work_items", []) if int(entry.get("total", 0) or 0) > 0
    }
    human_sessions = snapshot.get("human_ask", {}).get("sessions", [])
    session_row = next(item for item in human_sessions if item.get("session_id") == session["session_id"])
    audit_actions = {str(item.get("action") or "") for item in snapshot.get("audit", [])}
    evidence_summary = snapshot.get("evidence_exports", {}).get("summary", {})

    assert pending.human_override["request_id"] in linked_case.get("linked_override_ids", [])
    assert session["session_id"] in linked_case.get("linked_session_ids", [])
    assert session_row.get("case_id") == linked_case.get("case_id")
    assert linked_case.get("workflow_proof_total", 0) >= 1
    assert continuity.get("evidence_posture") == "proof attached"
    assert latest_proof.get("action") == "workflow_proof_export"
    assert "audit" in follow_up_views
    assert {"request", "override", "human_ask", "audit"}.issubset(work_item_kinds)
    assert evidence_summary.get("workflow_proof_total", 0) >= 1
    assert proof_bundle["workflow_id"] == "plan-ops-exception-001"
    assert "workflow_proof_export" in audit_actions
