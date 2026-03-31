from unittest.mock import patch
from sa_nom_governance.api.api_engine import build_engine_app
from sa_nom_governance.core.core_engine import HumanRequiredError
from sa_nom_governance.utils.config import AppConfig


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

def test_runtime_contract_rejects_non_object_payload() -> None:
    app = build_test_app()
    result = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload=['invalid_payload_shape'],
    )
    assert result.outcome == 'escalated'
    assert result.policy_basis == 'runtime.contract.request'
    assert result.decision_trace['source_type'] == 'runtime_contract'
    assert result.decision_trace['source_id'] == 'payload_invalid'


def test_runtime_contract_rejects_negative_amount() -> None:
    app = build_test_app()
    result = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'amount': -1, 'resource': 'contract', 'resource_id': 'C-NEGATIVE'},
    )
    assert result.outcome == 'escalated'
    assert result.policy_basis == 'runtime.contract.context'
    assert result.decision_trace['source_type'] == 'runtime_contract'
    assert result.decision_trace['source_id'] == 'amount_negative'




def test_runtime_evidence_trace_is_emitted_and_queryable() -> None:
    app = build_test_app()

    approved = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'C-TRACE-1', 'amount': 3000000},
    )
    waiting = app.request(
        requester='AUDITOR',
        role_id='GOV',
        action='approve_policy',
        payload={'resource': 'contract', 'resource_id': 'C-TRACE-2'},
    )

    assert approved.outcome == 'approved'
    assert waiting.outcome == 'waiting_human'

    traces = app.list_runtime_evidence(limit=10)
    assert len(traces) >= 2
    latest = traces[-1]
    assert latest['request_id'] is not None
    assert latest['trace_source_type'] is not None

    waiting_only = app.list_runtime_evidence(outcome='waiting_human')
    assert any(item['request_id'] == waiting.metadata['request_id'] for item in waiting_only)

    policy_source = app.list_runtime_evidence(source_type='policy')
    assert any(item['trace_source_type'] == 'policy' for item in policy_source)



def test_runtime_reliability_retries_transient_timeout() -> None:
    app = build_test_app()
    original = app.engine._evaluate_context
    attempts = {'count': 0}

    def flaky_eval(context, approved_override=None):
        attempts['count'] += 1
        if attempts['count'] == 1:
            raise TimeoutError('temporary runtime timeout')
        return original(context, approved_override=approved_override)

    with patch.object(app.engine, '_evaluate_context', side_effect=flaky_eval):
        result = app.request(
            requester='tester',
            role_id='LEGAL',
            action='review_contract',
            payload={'resource': 'contract', 'resource_id': 'C-RETRY-1', 'amount': 3000000},
            metadata={'runtime_retry_max_attempts': 2},
        )

    assert attempts['count'] == 2
    assert result.outcome == 'approved'
    reliability = result.metadata['metadata']['runtime_reliability']
    assert reliability['attempts_used'] == 2
    assert reliability['max_attempts'] == 2
    assert reliability['outcome_state'] == 'approved'


def test_runtime_reliability_marks_human_required_signal() -> None:
    app = build_test_app()

    with patch.object(app.engine, '_evaluate_context', side_effect=HumanRequiredError('human approval boundary reached')):
        result = app.request(
            requester='tester',
            role_id='LEGAL',
            action='review_contract',
            payload={'resource': 'contract', 'resource_id': 'C-HUMAN-1', 'amount': 3000000},
            metadata={'runtime_retry_max_attempts': 1},
        )

    assert result.outcome == 'human_required'
    assert result.policy_basis == 'runtime.orchestration.reliability'
    assert result.decision_trace['source_type'] == 'runtime_reliability'
    reliability = result.metadata['metadata']['runtime_reliability']
    assert reliability['outcome_state'] == 'human_required'
    assert reliability['error_type'] == 'HumanRequiredError'


def test_runtime_reliability_marks_unhandled_errors_as_blocked() -> None:
    app = build_test_app()

    with patch.object(app.engine, '_evaluate_context', side_effect=RuntimeError('unexpected crash')):
        result = app.request(
            requester='tester',
            role_id='LEGAL',
            action='review_contract',
            payload={'resource': 'contract', 'resource_id': 'C-BLOCKED-1', 'amount': 3000000},
            metadata={'runtime_retry_max_attempts': 1},
        )

    assert result.outcome == 'blocked'
    assert result.policy_basis == 'runtime.orchestration.reliability'
    assert result.decision_trace['source_id'] == 'RuntimeError'
    reliability = result.metadata['metadata']['runtime_reliability']
    assert reliability['retry_exhausted'] is True
    assert reliability['error_type'] == 'RuntimeError'


def test_authority_contract_blocks_request_via_gate() -> None:
    app = build_test_app()

    result = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'C-AUTH-BLOCK-1', 'amount': 1000000},
        metadata={'authority_contract': {'approval_gate': 'blocked'}},
    )

    assert result.outcome == 'blocked'
    assert result.policy_basis == 'runtime.authority_contract'
    assert result.decision_trace['source_type'] == 'authority_contract'
    assert result.decision_trace['source_id'] == 'approval_gate'


def test_authority_contract_requires_human_via_gate() -> None:
    app = build_test_app()

    result = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'C-AUTH-HUMAN-1', 'amount': 1000000},
        metadata={'authority_contract': {'approval_gate': 'human_required'}},
    )

    assert result.outcome == 'human_required'
    assert result.human_override is not None
    assert result.human_override['status'] == 'pending'
    assert result.policy_basis == 'runtime.authority_contract'


def test_authority_contract_invalid_shape_fails_closed() -> None:
    app = build_test_app()

    result = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'C-AUTH-INVALID-1', 'amount': 1000000},
        metadata={'authority_contract': {'approval_gate': 'unknown_gate'}},
    )

    assert result.outcome == 'blocked'
    assert result.policy_basis == 'runtime.authority_contract'
    assert result.decision_trace['source_id'] == 'authority_contract_invalid_gate'


def test_authority_contract_allow_actions_enforced() -> None:
    app = build_test_app()

    result = app.request(
        requester='tester',
        role_id='LEGAL',
        action='flag_risk',
        payload={'resource': 'contract', 'resource_id': 'C-AUTH-ALLOW-1', 'amount': 1000000},
        metadata={'authority_contract': {'allow_actions': ['review_contract']}},
    )

    assert result.outcome == 'blocked'
    assert result.policy_basis == 'runtime.authority_contract'
    assert result.decision_trace['source_id'] == 'allow_actions'


def test_authority_contract_human_required_can_resume_after_override() -> None:
    app = build_test_app()

    pending = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'C-AUTH-RESUME-1', 'amount': 1000000},
        metadata={'authority_contract': {'approval_gate': 'human_required'}},
    )
    assert pending.outcome == 'human_required'
    assert pending.human_override is not None

    reviewed = app.approve_override(
        pending.human_override['request_id'],
        resolved_by='EXEC_OWNER',
        note='Approved authority contract gate.',
    )

    assert reviewed.status == 'approved'
    assert reviewed.execution_result is not None
    assert reviewed.execution_result['outcome'] == 'approved'


def test_runtime_state_flow_completed_for_approved_request() -> None:
    app = build_test_app()

    result = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'C-STATE-APPROVED-1', 'amount': 3000000},
    )

    runtime_flow = result.metadata['metadata']['runtime_state_flow']
    role_lifecycle = result.metadata['metadata']['role_execution_lifecycle']

    assert result.outcome == 'approved'
    assert runtime_flow['current_state'] == 'completed'
    assert any(item['to_state'] == 'received' for item in runtime_flow['history'])
    assert any(item['to_state'] == 'in_progress_ai' for item in runtime_flow['history'])
    assert any(item['to_state'] == 'approved' for item in runtime_flow['history'])
    assert any(item['to_state'] == 'completed' for item in runtime_flow['history'])
    assert role_lifecycle['current_state'] == 'completed'


def test_runtime_state_flow_pauses_for_human_confirmation() -> None:
    app = build_test_app()

    result = app.request(
        requester='tester',
        role_id='GOV',
        action='approve_group_policy',
        payload={'resource': 'contract', 'resource_id': 'C-STATE-HUMAN-1'},
    )

    runtime_flow = result.metadata['metadata']['runtime_state_flow']
    role_lifecycle = result.metadata['metadata']['role_execution_lifecycle']

    assert result.outcome == 'waiting_human'
    assert runtime_flow['current_state'] == 'awaiting_human_confirmation'
    assert role_lifecycle['current_state'] == 'paused_for_human'


def test_runtime_state_flow_marks_blocked_terminal() -> None:
    app = build_test_app()

    result = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'C-STATE-BLOCK-1', 'amount': 1000000},
        metadata={'authority_contract': {'approval_gate': 'blocked'}},
    )

    runtime_flow = result.metadata['metadata']['runtime_state_flow']
    role_lifecycle = result.metadata['metadata']['role_execution_lifecycle']

    assert result.outcome == 'blocked'
    assert runtime_flow['current_state'] == 'blocked'
    assert role_lifecycle['current_state'] == 'stopped'


def test_runtime_state_flow_resumes_after_override_approval() -> None:
    app = build_test_app()

    pending = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'C-STATE-RESUME-1', 'amount': 1000000},
        metadata={'authority_contract': {'approval_gate': 'human_required'}},
    )
    reviewed = app.approve_override(
        pending.human_override['request_id'],
        resolved_by='EXEC_OWNER',
        note='Resume runtime after authority decision.',
    )

    execution_result = reviewed.execution_result
    assert execution_result is not None

    runtime_flow = execution_result['metadata']['metadata']['runtime_state_flow']
    role_lifecycle = execution_result['metadata']['metadata']['role_execution_lifecycle']

    assert execution_result['outcome'] == 'approved'
    assert runtime_flow['current_state'] == 'completed'
    assert any(item['to_state'] == 'in_progress_ai' and item['event'] == 'ai_execution_resumed' for item in runtime_flow['history'])
    assert any(item['to_state'] == 'resumed' for item in role_lifecycle['history'])
    assert role_lifecycle['current_state'] == 'completed'


def test_authority_gate_metadata_emitted_for_blocked_gate() -> None:
    app = build_test_app()

    result = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'C-AUTH-META-BLOCK-1', 'amount': 1000000},
        metadata={'authority_contract': {'approval_gate': 'blocked'}},
    )

    authority_gate = result.metadata['metadata']['authority_gate']
    assert result.outcome == 'blocked'
    assert authority_gate['gate_triggered'] is True
    assert authority_gate['source_id'] == 'approval_gate'
    assert authority_gate['decision_mode'] == 'ai_autonomous'
    assert authority_gate['requires_human_confirmation'] is False


def test_authority_gate_metadata_marks_human_confirm_required() -> None:
    app = build_test_app()

    result = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'C-AUTH-META-HUMAN-1', 'amount': 1000000},
        metadata={'authority_contract': {'approval_gate': 'human_required'}},
    )

    authority_gate = result.metadata['metadata']['authority_gate']
    assert result.outcome == 'human_required'
    assert authority_gate['gate_triggered'] is True
    assert authority_gate['source_id'] == 'approval_gate'
    assert authority_gate['decision_mode'] == 'ai_prepared_human_confirmed'
    assert authority_gate['requires_human_confirmation'] is True


def test_authority_gate_metadata_passthrough_when_no_contract() -> None:
    app = build_test_app()

    result = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'C-AUTH-META-PASS-1', 'amount': 3000000},
    )

    authority_gate = result.metadata['metadata']['authority_gate']
    assert result.outcome == 'approved'
    assert authority_gate['gate_triggered'] is False
    assert authority_gate['decision_mode'] == 'policy_fallback'


def test_authority_gate_metadata_records_resume_request_id() -> None:
    app = build_test_app()

    pending = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'C-AUTH-META-RESUME-1', 'amount': 1000000},
        metadata={'authority_contract': {'approval_gate': 'human_required'}},
    )
    reviewed = app.approve_override(
        pending.human_override['request_id'],
        resolved_by='EXEC_OWNER',
        note='Approve authority gate metadata resume.',
    )

    execution_result = reviewed.execution_result
    assert execution_result is not None

    authority_gate = execution_result['metadata']['metadata']['authority_gate']
    assert execution_result['outcome'] == 'approved'
    assert authority_gate['gate_triggered'] is True
    assert authority_gate['source_id'] == 'human_override_resume'
    assert authority_gate['resumed_from_override_request_id'] == pending.human_override['request_id']

def test_policy_contract_rejects_unknown_contract_keys() -> None:
    app = build_test_app()

    result = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'C-PC-SHAPE-1', 'amount': 1000000},
        metadata={'policy_contract': {'unsupported_key': 'x'}},
    )

    assert result.outcome == 'escalated'
    assert result.policy_basis == 'runtime.contract.request'
    assert result.decision_trace['source_id'] == 'policy_contract_unknown_keys'


def test_policy_contract_enforces_context_boundaries() -> None:
    app = build_test_app()

    result = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'C-PC-CONTEXT-1', 'amount': 1000000},
        metadata={
            'policy_contract': {
                'allowed_roles': ['GOV'],
                'allowed_actions': ['approve_policy'],
                'required_payload_fields': ['contract_id'],
            }
        },
    )

    assert result.outcome == 'escalated'
    assert result.policy_basis == 'runtime.contract.context'
    assert result.decision_trace['source_id'] == 'policy_contract_role_outside_allowlist'


def test_policy_contract_enforces_allowed_outcomes() -> None:
    app = build_test_app()

    result = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'C-PC-OUTCOME-1', 'amount': 3000000},
        metadata={'policy_contract': {'allowed_outcomes': ['blocked']}},
    )

    assert result.outcome == 'escalated'
    assert result.policy_basis == 'runtime.contract.decision'
    assert result.decision_trace['source_id'] == 'policy_contract_outcome_outside_allowlist'


def test_policy_contract_enforces_policy_basis_prefix() -> None:
    app = build_test_app()

    result = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'C-PC-POLICY-1', 'amount': 3000000},
        metadata={'policy_contract': {'required_policy_basis_prefix': 'runtime.authority_contract'}},
    )

    assert result.outcome == 'escalated'
    assert result.policy_basis == 'runtime.contract.decision'
    assert result.decision_trace['source_id'] == 'policy_contract_policy_basis_prefix_mismatch'

def test_policy_contract_rejects_invalid_reasoning_mode() -> None:
    app = build_test_app()

    result = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'C-RC-INVALID-MODE-1', 'amount': 1000000},
        metadata={'policy_contract': {'reasoning_mode': 'ultra_think'}},
    )

    assert result.outcome == 'escalated'
    assert result.policy_basis == 'runtime.contract.request'
    assert result.decision_trace['source_id'] == 'policy_contract_reasoning_mode_invalid'


def test_policy_contract_rejects_invalid_reasoning_budget() -> None:
    app = build_test_app()

    result = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'C-RC-INVALID-BUDGET-1', 'amount': 1000000},
        metadata={'policy_contract': {'reasoning_mode': 'think', 'max_reasoning_steps': 0}},
    )

    assert result.outcome == 'escalated'
    assert result.policy_basis == 'runtime.contract.request'
    assert result.decision_trace['source_id'] == 'policy_contract_max_reasoning_steps_invalid'


def test_deep_think_requires_human_confirmation_when_contract_demands_it() -> None:
    app = build_test_app()

    result = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'C-RC-DEEP-1', 'amount': 1000000},
        metadata={
            'policy_contract': {
                'reasoning_mode': 'deep_think',
                'max_reasoning_steps': 12,
                'max_runtime_ms': 1500,
                'requires_human_for_deep_think': True,
            }
        },
    )

    assert result.outcome == 'human_required'
    assert result.policy_basis == 'runtime.reasoning_control'
    assert result.decision_trace['source_type'] == 'reasoning_control'
    assert result.decision_trace['source_id'] == 'deep_think_human_gate'
    assert result.human_override is not None
    reasoning_control = result.metadata['metadata']['reasoning_control']
    assert reasoning_control['reasoning_mode'] == 'deep_think'
    assert reasoning_control['max_reasoning_steps'] == 12
    assert reasoning_control['max_runtime_ms'] == 1500
    assert reasoning_control['requires_human_confirmation'] is True


def test_think_mode_emits_reasoning_control_metadata_without_blocking() -> None:
    app = build_test_app()

    result = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'C-RC-THINK-1', 'amount': 3000000},
        metadata={
            'policy_contract': {
                'reasoning_mode': 'think',
                'max_reasoning_steps': 6,
                'max_runtime_ms': 900,
            }
        },
    )

    assert result.outcome == 'approved'
    reasoning_control = result.metadata['metadata']['reasoning_control']
    assert reasoning_control['reasoning_mode'] == 'think'
    assert reasoning_control['max_reasoning_steps'] == 6
    assert reasoning_control['max_runtime_ms'] == 900
    assert reasoning_control['requires_human_confirmation'] is False
