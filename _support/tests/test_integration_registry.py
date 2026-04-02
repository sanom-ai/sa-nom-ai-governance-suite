import json
from pathlib import Path
from tempfile import TemporaryDirectory

from sa_nom_governance.integrations.integration_registry import IntegrationRegistry


def test_integration_registry_matches_wildcard_and_exact_patterns():
    with TemporaryDirectory() as temp_dir:
        registry_path = Path(temp_dir) / 'integration_targets.json'
        registry_path.write_text(
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
                        'target_id': 'tickets',
                        'name': 'Tickets',
                        'status': 'active',
                        'delivery_mode': 'http',
                        'subscribed_events': ['role_private_studio.request.published'],
                    },
                ]
            ),
            encoding='utf-8',
        )

        registry = IntegrationRegistry(registry_path)

        runtime_targets = registry.matching_targets('runtime.request.completed')
        publish_targets = registry.matching_targets('role_private_studio.request.published')

        assert [target.target_id for target in runtime_targets] == ['ledger']
        assert [target.target_id for target in publish_targets] == ['tickets']


def test_integration_registry_health_counts_targets_and_channel_families():
    with TemporaryDirectory() as temp_dir:
        registry_path = Path(temp_dir) / 'integration_targets.json'
        registry_path.write_text(
            json.dumps(
                [
                    {
                        'target_id': 'a',
                        'name': 'A',
                        'status': 'active',
                        'delivery_mode': 'log_only',
                        'platform': 'ledger',
                        'notification_channels': ['dashboard'],
                    },
                    {
                        'target_id': 'b',
                        'name': 'B',
                        'status': 'disabled',
                        'delivery_mode': 'http',
                        'category': 'chatops',
                        'platform': 'slack',
                        'notification_channels': ['slack', 'webhook'],
                    },
                    {
                        'target_id': 'c',
                        'name': 'C',
                        'status': 'active',
                        'delivery_mode': 'http',
                        'category': 'ticketing',
                        'platform': 'jira',
                        'notification_channels': ['jira', 'ticketing', 'webhook'],
                    },
                ]
            ),
            encoding='utf-8',
        )

        registry = IntegrationRegistry(registry_path)
        health = registry.health()

        assert health['targets_total'] == 3
        assert health['active_targets'] == 2
        assert health['http_targets'] == 2
        assert health['log_only_targets'] == 1
        assert health['chatops_targets'] == 1
        assert health['ticketing_targets'] == 1
        assert health['platforms_configured'] == ['jira', 'ledger', 'slack']
        assert health['platforms_active'] == ['jira', 'ledger']
        assert health['notification_channels_configured'] == ['dashboard', 'jira', 'slack', 'ticketing', 'webhook']
        assert health['notification_channels_active'] == ['dashboard', 'jira', 'ticketing', 'webhook']
