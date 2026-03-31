import json
from pathlib import Path
from tempfile import TemporaryDirectory

from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.integrations.integration_registry import IntegrationRegistry
from sa_nom_governance.integrations.webhook_dispatcher import WebhookDispatcher


def test_webhook_dispatcher_records_log_only_and_blocked_http_deliveries():
    with TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        targets_path = base_dir / 'integration_targets.json'
        targets_path.write_text(
            json.dumps(
                [
                    {
                        'target_id': 'ledger',
                        'name': 'Ledger',
                        'status': 'active',
                        'delivery_mode': 'log_only',
                        'subscribed_events': ['runtime.*'],
                    },
                    {
                        'target_id': 'siem',
                        'name': 'SIEM',
                        'status': 'active',
                        'delivery_mode': 'http',
                        'endpoint_url': 'https://siem.example.local/intake',
                        'subscribed_events': ['runtime.*'],
                    },
                ]
            ),
            encoding='utf-8',
        )

        config = AppConfig(base_dir=base_dir)
        config.integration_targets_path = targets_path
        config.integration_delivery_log_path = base_dir / 'runtime_integration_delivery_log.jsonl'
        config.integration_dead_letter_log_path = base_dir / 'runtime_integration_dead_letters.jsonl'
        config.integration_outbox_path = base_dir / 'runtime_integration_outbox.json'
        config.outbound_http_integrations_enabled = False

        registry = IntegrationRegistry(config.integration_targets_path)
        dispatcher = WebhookDispatcher(config, registry)

        result = dispatcher.dispatch_event(
            'runtime.request.completed',
            {'request_id': 'REQ-1', 'outcome': 'approved'},
            source='runtime',
            requested_by='EXEC_OWNER',
        )
        deliveries = dispatcher.list_deliveries(limit=10)
        dead_letters = dispatcher.list_dead_letters(limit=10)
        outbox = dispatcher.list_outbox_jobs(limit=10)

        assert result['targets_matched'] == 2
        assert result['deliveries_total'] == 2
        assert result['failed_total'] == 1
        assert result['dead_lettered_total'] == 1
        assert result['outbox']['jobs_total'] == 2
        assert deliveries[0]['status'] in {'blocked', 'recorded'}
        assert {item['status'] for item in deliveries} == {'recorded', 'blocked'}
        assert dead_letters[0]['target_id'] == 'siem'
        assert dead_letters[0]['final_status'] == 'blocked'
        assert {item['status'] for item in outbox} == {'completed', 'dead_lettered'}


def test_webhook_dispatcher_summary_tracks_latest_delivery():
    with TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        targets_path = base_dir / 'integration_targets.json'
        targets_path.write_text(
            json.dumps(
                [
                    {
                        'target_id': 'ledger',
                        'name': 'Ledger',
                        'status': 'active',
                        'delivery_mode': 'log_only',
                        'subscribed_events': ['*'],
                    }
                ]
            ),
            encoding='utf-8',
        )

        config = AppConfig(base_dir=base_dir)
        config.integration_targets_path = targets_path
        config.integration_delivery_log_path = base_dir / 'runtime_integration_delivery_log.jsonl'
        config.integration_dead_letter_log_path = base_dir / 'runtime_integration_dead_letters.jsonl'
        config.integration_outbox_path = base_dir / 'runtime_integration_outbox.json'

        registry = IntegrationRegistry(config.integration_targets_path)
        dispatcher = WebhookDispatcher(config, registry)
        dispatcher.dispatch_event('role_private_studio.request.published', {'role_id': 'LEGAL'}, source='studio')
        summary = dispatcher.summary()

        assert summary['deliveries_total'] == 1
        assert summary['recorded_total'] == 1
        assert summary['latest_delivery']['event_type'] == 'role_private_studio.request.published'
        assert summary['dead_letters_total'] == 0
        assert summary['outbox_total'] == 1
        assert summary['coordination_backend'] == 'json_queue'



def test_webhook_dispatcher_outbox_job_includes_enterprise_hook_metadata():
    with TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        targets_path = base_dir / 'integration_targets.json'
        targets_path.write_text(
            json.dumps(
                [
                    {
                        'target_id': 'ledger',
                        'name': 'Ledger',
                        'status': 'active',
                        'delivery_mode': 'log_only',
                        'subscribed_events': ['runtime.*'],
                    }
                ]
            ),
            encoding='utf-8',
        )

        config = AppConfig(base_dir=base_dir, environment='production')
        config.integration_targets_path = targets_path
        config.integration_delivery_log_path = base_dir / 'runtime_integration_delivery_log.jsonl'
        config.integration_dead_letter_log_path = base_dir / 'runtime_integration_dead_letters.jsonl'
        config.integration_outbox_path = base_dir / 'runtime_integration_outbox.json'

        registry = IntegrationRegistry(config.integration_targets_path)
        dispatcher = WebhookDispatcher(config, registry)
        dispatcher.dispatch_event(
            'runtime.request.completed',
            {
                'request_id': 'REQ-HOOK-1',
                'outcome': 'approved',
                'workflow_bundle': {
                    'execution_plan': {
                        'plan_id': 'plan-hook-2',
                        'step_id': 'step-delivery',
                        'routing_status': 'handoff_active',
                    },
                    'decision_queue': {
                        'queue_id': 'dq-hook-2',
                        'queue_lane': 'human_review',
                        'queue_state': 'queued_human_review',
                    },
                    'correlation': {
                        'request_id': 'REQ-HOOK-1',
                        'execution_plan_id': 'plan-hook-2',
                        'execution_step_id': 'step-delivery',
                        'decision_queue_id': 'dq-hook-2',
                        'decision_queue_lane': 'human_review',
                    },
                },
            },
            source='runtime',
            requested_by='EXEC_OWNER',
            metadata={'tenant_id': 'SANOM-TH', 'release_version': 'v0.2.5'},
        )

        outbox_job = dispatcher.list_outbox_jobs(limit=1)[0]
        enterprise_hook = outbox_job['metadata']['enterprise_hook']

        assert enterprise_hook['logical_name'] == 'integration_outbox'
        assert enterprise_hook['environment'] == 'production'
        assert enterprise_hook['tenant_id'] == 'SANOM-TH'
        assert enterprise_hook['release_version'] == 'v0.2.5'
        assert enterprise_hook['correlation']['request_id'] == 'REQ-HOOK-1'
        assert enterprise_hook['correlation']['execution_plan_id'] == 'plan-hook-2'
        assert enterprise_hook['correlation']['decision_queue_id'] == 'dq-hook-2'
        assert enterprise_hook['workflow']['routing_status'] == 'handoff_active'
