from dataclasses import dataclass

from sa_nom_governance.api.api_engine import build_engine_app
from sa_nom_governance.utils.config import AppConfig


def build_test_app():
    return build_engine_app(AppConfig(persist_runtime=False))


@dataclass(slots=True)
class GovernanceRequestCase:
    name: str
    requester: str
    role_id: str
    action: str
    payload: dict[str, object]
    metadata: dict[str, object]
    expected_outcome: str
    expected_policy_basis: str
    expected_trace_source_type: str
    expected_trace_source_id: str


def test_runtime_governance_transition_matrix() -> None:
    app = build_test_app()
    cases = [
        GovernanceRequestCase(
            name='authority_blocked',
            requester='tester',
            role_id='LEGAL',
            action='review_contract',
            payload={'resource': 'contract', 'resource_id': 'C-GOV-MATRIX-1', 'amount': 1000000},
            metadata={'authority_contract': {'approval_gate': 'blocked'}},
            expected_outcome='blocked',
            expected_policy_basis='runtime.authority_contract',
            expected_trace_source_type='authority_contract',
            expected_trace_source_id='approval_gate',
        ),
        GovernanceRequestCase(
            name='authority_human_required',
            requester='tester',
            role_id='LEGAL',
            action='review_contract',
            payload={'resource': 'contract', 'resource_id': 'C-GOV-MATRIX-2', 'amount': 1000000},
            metadata={'authority_contract': {'approval_gate': 'human_required'}},
            expected_outcome='human_required',
            expected_policy_basis='runtime.authority_contract',
            expected_trace_source_type='authority_contract',
            expected_trace_source_id='approval_gate',
        ),
        GovernanceRequestCase(
            name='deep_think_human_gate',
            requester='tester',
            role_id='LEGAL',
            action='review_contract',
            payload={'resource': 'contract', 'resource_id': 'C-GOV-MATRIX-3', 'amount': 1000000},
            metadata={
                'policy_contract': {
                    'reasoning_mode': 'deep_think',
                    'max_reasoning_steps': 12,
                    'requires_human_for_deep_think': True,
                }
            },
            expected_outcome='human_required',
            expected_policy_basis='runtime.reasoning_control',
            expected_trace_source_type='reasoning_control',
            expected_trace_source_id='deep_think_human_gate',
        ),
        GovernanceRequestCase(
            name='policy_preflight_fail_closed',
            requester='tester',
            role_id='LEGAL',
            action='review_contract',
            payload={'resource': 'contract', 'resource_id': 'C-GOV-MATRIX-4', 'amount': 3000000},
            metadata={'policy_contract': {'human_required': {'required': True}}},
            expected_outcome='escalated',
            expected_policy_basis='runtime.contract.preflight',
            expected_trace_source_type='runtime_contract',
            expected_trace_source_id='policy_contract_human_required_unavailable',
        ),
    ]

    for case in cases:
        result = app.request(
            requester=case.requester,
            role_id=case.role_id,
            action=case.action,
            payload=case.payload,
            metadata=case.metadata,
        )

        assert result.outcome == case.expected_outcome, case.name
        assert result.policy_basis == case.expected_policy_basis, case.name
        assert result.decision_trace['source_type'] == case.expected_trace_source_type, case.name
        assert result.decision_trace['source_id'] == case.expected_trace_source_id, case.name


def test_runtime_governance_override_resume_chain_remains_consistent() -> None:
    app = build_test_app()

    pending = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'C-GOV-OVERRIDE-1', 'amount': 1000000},
        metadata={
            'authority_contract': {'approval_gate': 'human_required'},
            'policy_contract': {
                'human_required': {
                    'required': True,
                    'required_policy_basis_prefix': 'runtime.authority_contract',
                },
                'override_path': {
                    'required': True,
                    'required_policy_basis_prefix': 'runtime.authority_contract',
                    'required_approver_role': 'GOV',
                },
            },
        },
    )

    assert pending.outcome == 'human_required'
    assert pending.human_override is not None
    assert pending.human_override['approver_role'] == 'GOV'

    reviewed = app.approve_override(
        pending.human_override['request_id'],
        resolved_by='EXEC_OWNER',
        note='Governed override matrix validation.',
    )

    assert reviewed.execution_result is not None
    execution_result = reviewed.execution_result
    assert execution_result['outcome'] == 'approved'
    assert execution_result['policy_basis'] == 'runtime.authority_contract'
    authority_gate = execution_result['metadata']['metadata']['authority_gate']
    assert authority_gate['source_id'] == 'human_override_resume'
    assert authority_gate['resumed_from_override_request_id'] == pending.human_override['request_id']


def test_runtime_governance_out_of_order_event_sequence_stays_fail_closed() -> None:
    app = build_test_app()

    app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'C-GOV-ORDER-1', 'amount': 3000000},
        metadata={'event_stream': 'contract:C-GOV-ORDER-1', 'event_sequence': 1},
    )
    gap = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'C-GOV-ORDER-1', 'amount': 3000000},
        metadata={'event_stream': 'contract:C-GOV-ORDER-1', 'event_sequence': 3},
    )

    assert gap.outcome == 'out_of_order'
    assert gap.policy_basis == 'runtime.event_order'
    assert gap.decision_trace['source_type'] == 'runtime_event_order'
    assert gap.metadata['metadata']['runtime_state_flow']['current_state'] == 'blocked'
