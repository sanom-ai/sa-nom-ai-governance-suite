import json
from pathlib import Path
from tempfile import TemporaryDirectory

from integration_registry import IntegrationRegistry


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


def test_integration_registry_health_counts_targets():
    with TemporaryDirectory() as temp_dir:
        registry_path = Path(temp_dir) / 'integration_targets.json'
        registry_path.write_text(
            json.dumps(
                [
                    {'target_id': 'a', 'name': 'A', 'status': 'active', 'delivery_mode': 'log_only'},
                    {'target_id': 'b', 'name': 'B', 'status': 'disabled', 'delivery_mode': 'http'},
                ]
            ),
            encoding='utf-8',
        )

        registry = IntegrationRegistry(registry_path)
        health = registry.health()

        assert health['targets_total'] == 2
        assert health['active_targets'] == 1
        assert health['http_targets'] == 1
        assert health['log_only_targets'] == 1
