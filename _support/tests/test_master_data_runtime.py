import json
from pathlib import Path
from tempfile import TemporaryDirectory

from sa_nom_governance.guards.access_control import AccessControl
from sa_nom_governance.master_data.master_data_service import MasterDataService
from sa_nom_governance.utils.config import AppConfig


def _config(temp_dir: str) -> AppConfig:
    return AppConfig(base_dir=Path(temp_dir), persist_runtime=True, environment='development')


def test_master_data_service_builds_registry_assignment_queue_and_search_index() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _config(temp_dir)
        access_control = AccessControl(config)
        service = MasterDataService(config=config, access_control=access_control)

        roles = [
            {
                'role_id': 'LEGAL',
                'title': 'Legal AI',
                'business_domain': 'legal',
                'status': 'published',
                'purpose': 'Review governed contracts',
            }
        ]
        requests = [
            {
                'request_id': 'REQ-001',
                'requester': 'owner',
                'action': 'review_contract',
                'active_role': 'LEGAL',
                'resource': 'contract',
                'case_id': 'CASE-001',
                'created_at': '2026-04-03T00:00:00+00:00',
                'outcome': 'waiting_human',
            }
        ]
        overrides = [
            {
                'request_id': 'REQ-001',
                'origin_request_id': 'REQ-001',
                'status': 'pending',
                'approver_role': 'GOV_OWNER',
                'requester': 'owner',
                'case_id': 'CASE-001',
                'created_at': '2026-04-03T01:00:00+00:00',
            }
        ]
        human_ask = {
            'sessions': [
                {
                    'session_id': 'ASK-001',
                    'status': 'waiting_human',
                    'requested_by': 'owner',
                    'case_id': 'CASE-001',
                    'created_at': '2026-04-03T02:00:00+00:00',
                    'summary': {
                        'participant': 'Legal AI',
                        'prompt': 'Summarize the latest contract risk posture.',
                    },
                }
            ]
        }
        role_private_studio = {
            'requests': [
                {
                    'request_id': 'STUDIO-001',
                    'title': 'Contract reviewer update',
                    'status': 'in_review',
                    'requested_by': 'owner',
                    'case_id': 'CASE-001',
                    'created_at': '2026-04-03T03:00:00+00:00',
                }
            ]
        }
        documents = {
            'items': [
                {
                    'document_id': 'DOC-001',
                    'document_number': 'CTR-001',
                    'title': 'Contract Review Memo',
                    'status': 'in_review',
                    'owner_id': 'owner',
                    'approver_id': 'GOV_OWNER',
                    'document_class': 'legal_review',
                    'business_domain': 'legal',
                    'case_id': 'CASE-001',
                    'created_at': '2026-04-03T04:00:00+00:00',
                }
            ]
        }
        actions = {
            'items': [
                {
                    'action_id': 'ACT-001',
                    'action_type': 'summarize_case',
                    'label': 'Summarize contract case',
                    'status': 'waiting_human',
                    'requested_by': 'owner',
                    'case_id': 'CASE-001',
                    'created_at': '2026-04-03T05:00:00+00:00',
                    'next_action': 'Review the generated summary before sending it onward.',
                    'output_summary': 'Generated a first draft summary for the contract case.',
                }
            ],
            'summary': {'actions_total': 1},
        }
        cases = {
            'items': [
                {
                    'case_id': 'CASE-001',
                    'title': 'Contract review exception',
                    'summary': 'A governed contract review moved into human oversight.',
                    'case_reference': 'CASE-001',
                    'primary_view': 'overrides',
                    'status': 'human_required',
                }
            ]
        }
        owner_registration = {
            'organization_id': 'sanom-org',
            'organization_name': 'SA-NOM Organization',
            'owner_id': 'owner',
        }
        unified_work_inbox = {
            'items': [
                {
                    'lane_id': 'lane-overrides',
                    'title': 'Override queue',
                    'status': 'critical',
                    'view': 'overrides',
                    'operator_action': 'Clear the pending human decision queue.',
                }
            ]
        }
        evidence_exports = {
            'exports': [
                {
                    'pack_id': 'PACK-001',
                    'status': 'ready',
                    'posture': 'tamper_evident',
                    'requested_by': 'owner',
                }
            ]
        }
        sessions = [
            {
                'session_id': 'SESSION-001',
                'display_name': 'Owner session',
                'role_name': 'owner',
                'status': 'active',
                'profile_id': 'owner',
            }
        ]

        master_data = service.master_data_snapshot(
            roles=roles,
            requests=requests,
            overrides=overrides,
            human_ask=human_ask,
            role_private_studio=role_private_studio,
            documents=documents,
            actions=actions,
            cases=cases,
            owner_registration=owner_registration,
        )
        assignment_queue = service.assignment_queue_snapshot(
            master_data=master_data,
            overrides=overrides,
            human_ask=human_ask,
            role_private_studio=role_private_studio,
            documents=documents,
            actions=actions,
            unified_work_inbox=unified_work_inbox,
        )
        search = service.global_search_snapshot(
            master_data=master_data,
            assignment_queue=assignment_queue,
            cases=cases,
            requests=requests,
            documents=documents,
            actions=actions,
            human_ask=human_ask,
            roles=roles,
            evidence_exports=evidence_exports,
            sessions=sessions,
            role_private_studio=role_private_studio,
        )

        assert master_data['summary']['people_total'] >= 1
        assert master_data['summary']['teams_total'] >= 1
        assert master_data['summary']['search_ready'] is True
        assert config.master_data_store_path is not None
        assert config.master_data_store_path.exists()
        persisted = json.loads(config.master_data_store_path.read_text(encoding='utf-8'))
        assert persisted['organization']['organization_id'] == 'sanom-org'

        assert assignment_queue['summary']['items_total'] >= 4
        assert assignment_queue['summary']['human_required_total'] >= 1
        assert any(item['kind'] == 'override' for item in assignment_queue['items'])
        assert any(item['kind'] == 'action' for item in assignment_queue['items'])

        assert search['summary']['indexed_total'] >= 8
        kinds = {item['kind'] for item in search['items']}
        assert {'person', 'assignment', 'case', 'document', 'action', 'role'}.issubset(kinds)
