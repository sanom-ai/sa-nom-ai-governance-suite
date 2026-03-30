from api_engine import build_engine_app
from config import AppConfig


def build_test_app():
    return build_engine_app(AppConfig(persist_runtime=False))


def test_engine_request_returns_decision() -> None:
    app = build_test_app()
    result = app.request(
        requester="tester",
        role_id="GOV",
        action="review_audit",
        payload={},
    )
    assert result.outcome == "approved"
    assert result.decision_trace["source_id"] == "GOV_REVIEW_AUDIT"


def test_engine_request_waits_for_human_when_required() -> None:
    app = build_test_app()
    result = app.request(
        requester="tester",
        role_id="GOV",
        action="approve_group_policy",
        payload={},
    )
    assert result.outcome == "waiting_human"
    assert result.decision_trace["source_type"] == "constraint"
    assert result.human_override is not None
    assert result.human_override["status"] == "pending"
    assert result.human_override["approver_role"] == "EXEC_OWNER"


def test_policy_else_branch_escalates_high_risk_review() -> None:
    app = build_test_app()
    result = app.request(
        requester="tester",
        role_id="GOV",
        action="review_audit",
        payload={"amount": 9000000},
    )
    assert result.outcome == "escalated"
    assert result.policy_basis == "GOV_REVIEW_AUDIT"
    assert "risk_score <= 0.60" in result.decision_trace["failed_conditions"]


def test_amount_condition_controls_legal_review() -> None:
    app = build_test_app()
    result = app.request(
        requester="tester",
        role_id="LEGAL",
        action="review_contract",
        payload={"amount": 3000000},
    )
    assert result.outcome == "approved"
    assert "amount <= 4000000" in result.decision_trace["matched_conditions"]


def test_requester_condition_creates_human_override_state() -> None:
    app = build_test_app()
    result = app.request(
        requester="AUDITOR",
        role_id="GOV",
        action="approve_policy",
        payload={},
    )
    assert result.outcome == "waiting_human"
    assert result.policy_basis == "GOV_APPROVE_POLICY"
    assert result.human_override is not None
    assert result.human_override["required_by"] == "GOV_APPROVE_POLICY"


def test_resource_condition_drives_policy_result() -> None:
    app = build_test_app()
    approved = app.request(
        requester="EXEC_OWNER",
        role_id="GOV",
        action="emergency_stop",
        payload={"resource": "engine"},
    )
    escalated = app.request(
        requester="EXEC_OWNER",
        role_id="LEGAL",
        action="flag_risk",
        payload={"resource": "tenant"},
    )
    assert approved.outcome == "approved"
    assert escalated.outcome == "escalated"


def test_payload_condition_controls_advise_compliance() -> None:
    app = build_test_app()
    approved = app.request(
        requester="tester",
        role_id="LEGAL",
        action="advise_compliance",
        payload={"topic": "standard_review"},
    )
    escalated = app.request(
        requester="tester",
        role_id="LEGAL",
        action="advise_compliance",
        payload={"topic": "urgent_exception"},
    )
    assert approved.outcome == "approved"
    assert escalated.outcome == "escalated"


def test_override_lifecycle_supports_approve_and_veto() -> None:
    app = build_test_app()

    pending = app.request(
        requester="AUDITOR",
        role_id="GOV",
        action="approve_policy",
        payload={},
    )
    pending_id = pending.human_override["request_id"]

    pending_list = app.list_overrides(status="pending")
    assert any(item["request_id"] == pending_id for item in pending_list)

    approved = app.approve_override(pending_id, resolved_by="EXEC_OWNER", note="Approved after manual review.")
    assert approved.status == "approved"
    assert approved.resolved_by == "EXEC_OWNER"
    assert approved.execution_result is not None
    assert approved.execution_result["outcome"] == "approved"

    fetched_approved = app.get_override(pending_id)
    assert fetched_approved["execution_outcome"] == "approved"
    assert fetched_approved["execution_status"] == "completed"

    audit_entries = app.list_audit(limit=5)
    assert any(entry["action"] == "override_approve" for entry in audit_entries)

    second_pending = app.request(
        requester="tester",
        role_id="GOV",
        action="approve_group_policy",
        payload={},
    )
    second_pending_id = second_pending.human_override["request_id"]

    vetoed = app.veto_override(second_pending_id, resolved_by="EXEC_OWNER", note="Rejected during review.")
    assert vetoed.status == "vetoed"
    fetched = app.get_override(second_pending_id)
    assert fetched["status"] == "vetoed"


def test_pending_override_holds_resource_lock_and_blocks_conflicting_request() -> None:
    app = build_test_app()

    pending = app.request(
        requester="AUDITOR",
        role_id="GOV",
        action="approve_policy",
        payload={"resource": "contract", "resource_id": "C-001"},
    )
    assert pending.outcome == "waiting_human"
    assert pending.resource_lock is not None
    assert pending.resource_lock["status"] == "waiting_human"
    assert pending.resource_lock["resource_key"] == "contract:C-001"

    locks = app.list_locks()
    assert any(lock["resource_key"] == "contract:C-001" for lock in locks)

    conflict = app.request(
        requester="tester",
        role_id="LEGAL",
        action="review_contract",
        payload={"resource": "contract", "resource_id": "C-001", "amount": 3000000},
    )
    assert conflict.outcome == "conflicted"
    assert conflict.policy_basis == "runtime.resource_lock"
    assert conflict.conflict_lock is not None
    assert conflict.conflict_lock["resource_key"] == "contract:C-001"


def test_resolving_override_releases_resource_lock() -> None:
    app = build_test_app()

    pending = app.request(
        requester="AUDITOR",
        role_id="GOV",
        action="approve_policy",
        payload={"resource": "contract", "resource_id": "C-002"},
    )
    pending_id = pending.human_override["request_id"]

    approved = app.approve_override(pending_id, resolved_by="EXEC_OWNER", note="Approved lock release test.")
    assert approved.status == "approved"
    assert app.list_locks() == []

    follow_up = app.request(
        requester="tester",
        role_id="LEGAL",
        action="review_contract",
        payload={"resource": "contract", "resource_id": "C-002", "amount": 3000000},
    )
    assert follow_up.outcome == "approved"


def test_idempotent_replay_returns_stored_result() -> None:
    app = build_test_app()

    first = app.request(
        requester="tester",
        role_id="LEGAL",
        action="review_contract",
        payload={"resource": "contract", "resource_id": "C-300", "amount": 3000000},
        metadata={"idempotency_key": "REQ-300"},
    )
    second = app.request(
        requester="tester",
        role_id="LEGAL",
        action="review_contract",
        payload={"resource": "contract", "resource_id": "C-300", "amount": 3000000},
        metadata={"idempotency_key": "REQ-300"},
    )

    assert first.outcome == "approved"
    assert second.outcome == "approved"
    assert second.metadata["request_id"] == first.metadata["request_id"]
    consistency = second.metadata["metadata"]["request_consistency"]
    assert consistency["idempotency_status"] == "replayed"
    assert consistency["original_request_id"] == first.metadata["request_id"]
    audit_entries = app.list_audit(limit=10)
    assert any(entry["action"] == "runtime_idempotent_replay" for entry in audit_entries)


def test_idempotency_conflict_rejects_changed_request() -> None:
    app = build_test_app()

    first = app.request(
        requester="tester",
        role_id="LEGAL",
        action="review_contract",
        payload={"resource": "contract", "resource_id": "C-301", "amount": 3000000},
        metadata={"idempotency_key": "REQ-301"},
    )
    second = app.request(
        requester="tester",
        role_id="LEGAL",
        action="review_contract",
        payload={"resource": "contract", "resource_id": "C-301", "amount": 3500000},
        metadata={"idempotency_key": "REQ-301"},
    )

    assert first.outcome == "approved"
    assert second.outcome == "rejected"
    assert second.policy_basis == "runtime.idempotency"
    assert second.metadata["metadata"]["request_consistency"]["idempotency_status"] == "conflict"


def test_event_ordering_requires_monotonic_sequences() -> None:
    app = build_test_app()

    first = app.request(
        requester="tester",
        role_id="LEGAL",
        action="review_contract",
        payload={"resource": "contract", "resource_id": "C-400", "amount": 3000000},
        metadata={"event_stream": "contract:C-400", "event_sequence": 1},
    )
    gap = app.request(
        requester="tester",
        role_id="LEGAL",
        action="review_contract",
        payload={"resource": "contract", "resource_id": "C-400", "amount": 3000000},
        metadata={"event_stream": "contract:C-400", "event_sequence": 3},
    )
    second = app.request(
        requester="tester",
        role_id="LEGAL",
        action="review_contract",
        payload={"resource": "contract", "resource_id": "C-400", "amount": 3000000},
        metadata={"event_stream": "contract:C-400", "event_sequence": 2},
    )
    stale = app.request(
        requester="tester",
        role_id="LEGAL",
        action="review_contract",
        payload={"resource": "contract", "resource_id": "C-400", "amount": 3000000},
        metadata={"event_stream": "contract:C-400", "event_sequence": 2},
    )

    assert first.outcome == "approved"
    assert gap.outcome == "out_of_order"
    assert gap.policy_basis == "runtime.event_order"
    assert gap.metadata["metadata"]["request_consistency"]["ordering_status"] == "gap"
    assert second.outcome == "approved"
    assert second.metadata["metadata"]["request_consistency"]["ordering_status"] == "accepted"
    assert stale.outcome == "out_of_order"
    assert stale.metadata["metadata"]["request_consistency"]["ordering_status"] == "stale"


def test_idempotency_store_updates_after_override_approval() -> None:
    app = build_test_app()

    pending = app.request(
        requester="AUDITOR",
        role_id="GOV",
        action="approve_policy",
        payload={"resource": "contract", "resource_id": "C-500"},
        metadata={"idempotency_key": "REQ-500"},
    )
    pending_id = pending.human_override["request_id"]
    approved = app.approve_override(pending_id, resolved_by="EXEC_OWNER", note="Approved from idempotency test.")
    replay = app.request(
        requester="AUDITOR",
        role_id="GOV",
        action="approve_policy",
        payload={"resource": "contract", "resource_id": "C-500"},
        metadata={"idempotency_key": "REQ-500"},
    )

    assert approved.status == "approved"
    assert replay.outcome == "approved"
    assert replay.metadata["metadata"]["request_consistency"]["idempotency_status"] == "replayed"


def test_auto_role_activation_selects_legal_for_contract_review() -> None:
    app = build_test_app()
    result = app.request(
        requester="tester",
        role_id="",
        action="review_contract",
        payload={"resource": "contract", "amount": 3000000},
    )
    assert result.outcome == "approved"
    assert result.active_role == "LEGAL"
    assert result.role_transition is not None
    assert result.role_transition["activation_source"] == "context_router"
    assert result.role_transition["new_role"] == "LEGAL"


def test_hierarchy_safety_escalation_records_role_switch_audit() -> None:
    app = build_test_app()
    result = app.request(
        requester="tester",
        role_id="",
        action="review_contract",
        payload={"resource": "product_safety", "amount": 3000000, "business_domain": "product_safety"},
        metadata={"current_role": "GOV"},
    )
    assert result.outcome == "waiting_human"
    assert result.active_role == "LEGAL"
    assert result.human_override is not None
    assert result.human_override["approver_role"] == "GOV"
    assert result.role_transition is not None
    assert result.role_transition["previous_role"] == "GOV"
    assert result.role_transition["new_role"] == "LEGAL"

    audit_actions = [entry["action"] for entry in app.list_audit(limit=10)]
    assert "role_switch" in audit_actions
    assert "role_escalation" in audit_actions


def test_role_activation_fails_closed_when_no_candidate_exists() -> None:
    app = build_test_app()
    result = app.request(
        requester="tester",
        role_id="",
        action="unknown_action",
        payload={},
    )
    assert result.outcome == "escalated"
    assert result.policy_basis == "runtime.role_activation"
    assert result.decision_trace["source_id"] == "no_candidate_role"
    assert result.role_transition is not None
    assert result.role_transition["new_role"] == "UNRESOLVED"
