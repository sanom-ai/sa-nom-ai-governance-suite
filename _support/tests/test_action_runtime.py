from pathlib import Path
from tempfile import TemporaryDirectory

from sa_nom_governance.dashboard.dashboard_data import DashboardSnapshotBuilder
from sa_nom_governance.utils.config import AppConfig


def _base_config(temp_dir: str) -> AppConfig:
    return AppConfig(base_dir=Path(temp_dir), persist_runtime=True, environment='development')


def _create_case(builder: DashboardSnapshotBuilder) -> tuple[str, dict[str, object]]:
    request_result = builder.app.request(
        requester='operator@example.com',
        role_id='GOV',
        action='approve_policy',
        payload={'resource': 'contract', 'resource_id': 'C-ACTION-001'},
        metadata={
            'execution_plan': {
                'plan_id': 'plan-action-001',
                'step_id': 'step-runtime',
            }
        },
    )
    request_id = request_result.metadata['request_id']
    snapshot = builder.build()
    case_items = snapshot.get('cases', {}).get('items', [])
    case_item = next(item for item in case_items if request_id in item.get('linked_request_ids', []))
    return request_id, case_item


def test_action_runtime_summarize_case_completes_and_links_into_case_snapshot() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        builder = DashboardSnapshotBuilder(config=config)
        _, case_item = _create_case(builder)

        action = builder.app.create_action(
            {
                'action_type': 'summarize_case',
                'case_id': case_item['case_id'],
                'case_reference': case_item['case_reference'],
            },
            requested_by='EXEC_OWNER',
            case_snapshot=case_item,
        )

        snapshot = builder.build()
        actions_surface = snapshot.get('actions', {})
        action_row = next(item for item in actions_surface.get('items', []) if item.get('action_id') == action['action_id'])
        linked_case = next(item for item in snapshot.get('cases', {}).get('items', []) if item.get('case_id') == case_item['case_id'])
        timeline_types = {entry.get('event_type') for entry in linked_case.get('timeline', [])}
        work_item_kinds = {entry.get('kind') for entry in linked_case.get('work_items', []) if int(entry.get('total', 0) or 0) > 0}

        assert action_row.get('status') == 'completed'
        assert actions_surface.get('summary', {}).get('completed_total', 0) >= 1
        assert action_row.get('case_id') == linked_case.get('case_id')
        assert action['action_id'] in linked_case.get('linked_action_ids', [])
        assert 'action' in timeline_types
        assert 'action' in work_item_kinds
        assert snapshot.get('runtime_health', {}).get('action_runtime_store', {}).get('status') == 'present'


def test_action_runtime_draft_document_and_request_human_preserve_case_reference() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        builder = DashboardSnapshotBuilder(config=config)
        _, case_item = _create_case(builder)

        draft_action = builder.app.create_action(
            {
                'action_type': 'draft_document',
                'case_id': case_item['case_id'],
                'case_reference': case_item['case_reference'],
            },
            requested_by='EXEC_OWNER',
            case_snapshot=case_item,
        )
        human_action = builder.app.create_action(
            {
                'action_type': 'request_human',
                'case_id': case_item['case_id'],
                'case_reference': case_item['case_reference'],
            },
            requested_by='EXEC_OWNER',
            case_snapshot=case_item,
        )

        snapshot = builder.build()
        actions_summary = snapshot.get('actions', {}).get('summary', {})
        documents = snapshot.get('documents', {}).get('items', [])
        sessions = snapshot.get('human_ask', {}).get('sessions', [])
        linked_case = next(item for item in snapshot.get('cases', {}).get('items', []) if item.get('case_id') == case_item['case_id'])
        document_id = draft_action['artifacts'][0]['ref_id']
        session_id = human_action['artifacts'][0]['ref_id']
        document_row = next(item for item in documents if item.get('document_id') == document_id)
        session_row = next(item for item in sessions if item.get('session_id') == session_id)

        assert document_row.get('case_reference') == case_item['case_reference']
        assert session_row.get('case_id') == case_item['case_id']
        assert draft_action['action_id'] in linked_case.get('linked_action_ids', [])
        assert human_action['action_id'] in linked_case.get('linked_action_ids', [])
        assert actions_summary.get('actions_total', 0) >= 2
        assert actions_summary.get('document_artifact_total', 0) >= 1
        assert actions_summary.get('request_human_total', 0) >= 1
        assert actions_summary.get('completed_total', 0) + actions_summary.get('waiting_human_total', 0) >= 2
