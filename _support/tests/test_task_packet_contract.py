from sa_nom_governance.api.api_engine import build_engine_app
from sa_nom_governance.utils.config import AppConfig


def build_test_app():
    return build_engine_app(AppConfig(persist_runtime=False))


def test_task_packet_rejects_unknown_keys() -> None:
    app = build_test_app()

    result = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'PKT-001', 'amount': 1000000},
        metadata={
            'task_packet': {
                'packet_id': 'pkt-001',
                'packet_type': 'runtime_step',
                'source_role': 'LEGAL',
                'target_role': 'LEGAL',
                'workflow_id': 'wf-001',
                'step_id': 'step-1',
                'unsupported_key': 'x',
            }
        },
    )

    assert result.outcome == 'escalated'
    assert result.policy_basis == 'runtime.contract.request'
    assert result.decision_trace['source_id'] == 'task_packet_unknown_keys'


def test_task_packet_metadata_is_emitted_for_execution_plan_step() -> None:
    app = build_test_app()

    result = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'PKT-002', 'amount': 3000000},
        metadata={
            'execution_plan': {
                'plan_id': 'plan-pkt-001',
                'step_id': 'step-review',
                'intent': 'Review governed contract packet',
                'expected_output': 'Structured review summary',
                'stop_condition': 'summary_ready',
                'step_index': 1,
                'total_steps': 2,
            }
        },
    )

    assert result.outcome == 'approved'
    task_packet = result.metadata['metadata']['task_packet']
    assert task_packet['packet_type'] == 'runtime_step'
    assert task_packet['workflow_id'] == 'plan-pkt-001'
    assert task_packet['step_id'] == 'step-review'
    assert task_packet['source_role'] == 'LEGAL'
    assert task_packet['target_role'] == 'LEGAL'
    assert task_packet['packet_status'] == 'prepared'
    assert task_packet['correlation']['request_id'] == result.metadata['request_id']
    assert result.metadata['request_id'] in task_packet['evidence_refs']


def test_task_packet_resume_path_normalizes_contract_shape() -> None:
    app = build_test_app()

    pending = app.request(
        requester='tester',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'PKT-003', 'amount': 1000000},
        metadata={
            'authority_contract': {'approval_gate': 'human_required'},
            'execution_plan': {
                'plan_id': 'plan-pkt-002',
                'step_id': 'step-human-check',
                'intent': 'Prepare contract approval bundle',
                'expected_output': 'Human review package',
                'stop_condition': 'human_checkpoint',
                'step_index': 2,
                'total_steps': 4,
                'checkpoint_required': True,
                'checkpoint_policy_basis_prefix': 'runtime.authority_contract',
            },
            'task_packet': {
                'packet_id': 'pkt-003',
                'packet_type': 'runtime_step',
                'source_role': 'LEGAL',
                'target_role': 'LEGAL',
                'workflow_id': 'plan-pkt-002',
                'step_id': 'step-human-check',
                'correlation': {'request_id': 'placeholder'},
                'evidence_refs': ['seed-ref'],
                'packet_status': 'prepared',
            },
        },
    )

    assert pending.outcome == 'human_required'
    review = app.approve_override(pending.human_override['request_id'], resolved_by='EXEC_OWNER', note='Resume task packet test.')
    assert review.status == 'approved'
    assert review.execution_result is not None
    assert review.execution_result['policy_basis'] != 'runtime.contract.context'
