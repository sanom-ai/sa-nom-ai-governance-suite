from sa_nom_governance.api.api_engine import build_engine_app
from sa_nom_governance.utils.config import AppConfig


def build_test_app():
    return build_engine_app(AppConfig(persist_runtime=False))


def test_execution_plan_rejects_invalid_handoff_flag_shape() -> None:
    app = build_test_app()

    result = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'amount': 3000000},
        metadata={
            'execution_plan': {
                'plan_id': 'plan-routing-001',
                'step_id': 'step-legal-review',
                'intent': 'Review contract packet after governed routing',
                'expected_output': 'Structured legal review summary',
                'stop_condition': 'summary_ready',
                'handoff_required': 'yes',
            }
        },
    )

    assert result.outcome == 'escalated'
    assert result.policy_basis == 'runtime.contract.request'
    assert result.decision_trace['source_id'] == 'execution_plan_handoff_required_invalid'


def test_execution_plan_rejects_previous_step_outside_allowlist() -> None:
    app = build_test_app()

    result = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'amount': 3000000},
        metadata={
            'current_role': 'GOV',
            'execution_plan': {
                'plan_id': 'plan-routing-002',
                'step_id': 'step-legal-review',
                'intent': 'Continue governed contract workflow',
                'expected_output': 'Legal review handoff package',
                'stop_condition': 'review_ready',
                'previous_step_id': 'step-unexpected',
                'allowed_previous_steps': ['step-intake', 'step-risk-triage'],
                'handoff_required': True,
                'handoff_from_role': 'GOV',
                'handoff_target_role': 'LEGAL',
            },
        },
    )

    assert result.outcome == 'escalated'
    assert result.policy_basis == 'runtime.contract.preflight'
    assert result.decision_trace['source_id'] == 'execution_plan_previous_step_outside_allowlist'


def test_execution_plan_handoff_requires_previous_role_context() -> None:
    app = build_test_app()

    result = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'amount': 3000000},
        metadata={
            'execution_plan': {
                'plan_id': 'plan-routing-003',
                'step_id': 'step-legal-review',
                'intent': 'Run routed legal review step',
                'expected_output': 'Legal review summary',
                'stop_condition': 'review_ready',
                'previous_step_id': 'step-intake',
                'allowed_previous_steps': ['step-intake'],
                'handoff_required': True,
                'handoff_from_role': 'GOV',
                'handoff_target_role': 'LEGAL',
            },
        },
    )

    assert result.outcome == 'escalated'
    assert result.policy_basis == 'runtime.contract.preflight'
    assert result.decision_trace['source_id'] == 'execution_plan_handoff_context_missing'


def test_execution_plan_handoff_target_must_match_active_role() -> None:
    app = build_test_app()

    result = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'amount': 3000000},
        metadata={
            'current_role': 'GOV',
            'execution_plan': {
                'plan_id': 'plan-routing-004',
                'step_id': 'step-legal-review',
                'intent': 'Route contract packet to governed reviewer',
                'expected_output': 'Prepared legal review packet',
                'stop_condition': 'review_ready',
                'previous_step_id': 'step-intake',
                'allowed_previous_steps': ['step-intake'],
                'handoff_required': True,
                'handoff_from_role': 'GOV',
                'handoff_target_role': 'FINANCE',
            },
        },
    )

    assert result.outcome == 'escalated'
    assert result.policy_basis == 'runtime.contract.preflight'
    assert result.decision_trace['source_id'] == 'execution_plan_handoff_target_role_mismatch'


def test_execution_plan_handoff_metadata_is_emitted_for_routed_step() -> None:
    app = build_test_app()

    result = app.request(
        requester='tester',
        role_id='AUTO',
        action='review_contract',
        payload={
            'amount': 3000000,
            'resource': 'contract',
            'business_domain': 'legal_operations',
        },
        metadata={
            'current_role': 'GOV',
            'execution_plan': {
                'plan_id': 'plan-routing-005',
                'step_id': 'step-legal-review',
                'intent': 'Handoff governed intake packet to legal review role',
                'expected_output': 'Legal review summary',
                'stop_condition': 'review_ready',
                'step_index': 2,
                'total_steps': 4,
                'previous_step_id': 'step-intake',
                'allowed_previous_steps': ['step-intake'],
                'allowed_next_steps': ['step-human-check', 'step-risk-summary'],
                'handoff_required': True,
                'handoff_from_role': 'GOV',
                'handoff_target_role': 'LEGAL',
            },
        },
    )

    assert result.outcome == 'approved'
    assert result.active_role == 'LEGAL'
    assert result.role_transition['previous_role'] == 'GOV'
    assert result.role_transition['new_role'] == 'LEGAL'
    execution_plan = result.metadata['metadata']['execution_plan']
    assert execution_plan['previous_step_id'] == 'step-intake'
    assert execution_plan['allowed_previous_steps'] == ['step-intake']
    assert execution_plan['handoff_required'] is True
    assert execution_plan['handoff_from_role'] == 'GOV'
    assert execution_plan['handoff_target_role'] == 'LEGAL'
    assert execution_plan['active_role'] == 'LEGAL'
    assert execution_plan['routing_status'] == 'handoff_active'
    assert execution_plan['plan_status'] == 'handoff_active'
