from sa_nom_governance.api.api_engine import build_engine_app
from sa_nom_governance.utils.config import AppConfig


def build_test_app():
    return build_engine_app(AppConfig(persist_runtime=False))


def test_execution_plan_rejects_invalid_shape() -> None:
    app = build_test_app()

    result = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'C-PLAN-INVALID-1', 'amount': 1000000},
        metadata={'execution_plan': ['invalid']},
    )

    assert result.outcome == 'escalated'
    assert result.policy_basis == 'runtime.contract.request'
    assert result.decision_trace['source_id'] == 'execution_plan_invalid_type'


def test_execution_plan_rejects_step_index_above_total_steps() -> None:
    app = build_test_app()

    result = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'C-PLAN-INVALID-2', 'amount': 1000000},
        metadata={
            'execution_plan': {
                'plan_id': 'plan-001',
                'step_id': 'step-review',
                'intent': 'Review governed contract package',
                'expected_output': 'Contract review summary',
                'stop_condition': 'summary_ready',
                'step_index': 3,
                'total_steps': 2,
            }
        },
    )

    assert result.outcome == 'escalated'
    assert result.policy_basis == 'runtime.contract.request'
    assert result.decision_trace['source_id'] == 'execution_plan_step_index_out_of_range'


def test_execution_plan_checkpoint_requires_governed_human_path() -> None:
    app = build_test_app()

    result = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'C-PLAN-PREFLIGHT-1', 'amount': 3000000},
        metadata={
            'execution_plan': {
                'plan_id': 'plan-002',
                'step_id': 'step-approve',
                'intent': 'Prepare approval decision bundle',
                'expected_output': 'Approval queue item',
                'stop_condition': 'human_checkpoint',
                'checkpoint_required': True,
            }
        },
    )

    assert result.outcome == 'escalated'
    assert result.policy_basis == 'runtime.contract.preflight'
    assert result.decision_trace['source_id'] == 'execution_plan_checkpoint_unavailable'


def test_execution_plan_metadata_is_emitted_for_active_step() -> None:
    app = build_test_app()

    result = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'C-PLAN-META-1', 'amount': 3000000},
        metadata={
            'execution_plan': {
                'plan_id': 'plan-003',
                'step_id': 'step-review',
                'intent': 'Review contract packet and prepare next step',
                'expected_output': 'Structured review summary',
                'stop_condition': 'summary_ready',
                'step_index': 1,
                'total_steps': 3,
                'allowed_next_steps': ['step-risk', 'step-human-check'],
            }
        },
    )

    assert result.outcome == 'approved'
    execution_plan = result.metadata['metadata']['execution_plan']
    assert execution_plan['plan_id'] == 'plan-003'
    assert execution_plan['step_id'] == 'step-review'
    assert execution_plan['step_index'] == 1
    assert execution_plan['total_steps'] == 3
    assert execution_plan['allowed_next_steps'] == ['step-risk', 'step-human-check']
    assert execution_plan['plan_status'] == 'active_step'


def test_execution_plan_checkpoint_can_align_with_authority_gate() -> None:
    app = build_test_app()

    result = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'C-PLAN-HUMAN-1', 'amount': 1000000},
        metadata={
            'authority_contract': {'approval_gate': 'human_required'},
            'execution_plan': {
                'plan_id': 'plan-004',
                'step_id': 'step-human-check',
                'intent': 'Send prepared approval bundle to human decision queue',
                'expected_output': 'Pending human review item',
                'stop_condition': 'human_checkpoint',
                'step_index': 2,
                'total_steps': 4,
                'checkpoint_required': True,
                'checkpoint_policy_basis_prefix': 'runtime.authority_contract',
            },
        },
    )

    assert result.outcome == 'human_required'
    assert result.policy_basis == 'runtime.authority_contract'
    execution_plan = result.metadata['metadata']['execution_plan']
    assert execution_plan['checkpoint_required'] is True
    assert execution_plan['checkpoint_policy_basis_prefix'] == 'runtime.authority_contract'
