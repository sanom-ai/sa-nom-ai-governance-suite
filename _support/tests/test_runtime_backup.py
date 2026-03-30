import json
from pathlib import Path
from tempfile import TemporaryDirectory

from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.deployment.runtime_backup_manager import RuntimeBackupManager


def test_runtime_backup_copies_runtime_files_and_role_packs() -> None:
    with TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        config = AppConfig(base_dir=base_dir, persist_runtime=True, environment='development', api_token='owner-token', trusted_registry_signing_key='registry-key')

        audit_path = config.audit_log_path
        assert audit_path is not None
        audit_path.write_text(
            json.dumps(
                {
                    'timestamp': '2026-03-29T00:00:00+00:00',
                    'active_role': 'SYSTEM',
                    'action': 'event',
                    'outcome': 'completed',
                    'reason': 'ok',
                    'metadata': {},
                },
                ensure_ascii=False,
            )
            + '\n',
            encoding='utf-8',
        )

        role_path = base_dir / 'OPS.ptn'
        role_path.write_text('role OPS\n  title: Operations\n', encoding='utf-8')

        manager = RuntimeBackupManager(config)
        result = manager.create_backup(requested_by='tester', metadata={'scope': 'unit'})

        assert result['files_total'] >= 2
        assert result['files_present'] >= 2
        assert result['backup_id'].startswith('backup-')

        manifest_path = Path(result['backup_path']) / 'manifest.json'
        assert manifest_path.exists()
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        datasets = {item['dataset']: item for item in manifest['files']}
        assert datasets['audit_log']['present'] is True
        assert datasets['role_pack:OPS.ptn']['present'] is True

        summary = manager.summary()
        assert summary['backups_total'] == 1
        assert summary['latest_backup']['backup_id'] == result['backup_id']


def test_runtime_backup_lists_missing_files_without_failing() -> None:
    with TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        config = AppConfig(base_dir=base_dir, persist_runtime=True, environment='development', api_token='owner-token', trusted_registry_signing_key='registry-key')

        manager = RuntimeBackupManager(config)
        result = manager.create_backup(requested_by='tester')

        assert result['files_missing'] >= 1
        assert result['files_total'] >= result['files_missing']
        listed = manager.list_backups(limit=5)
        assert listed[0]['backup_id'] == result['backup_id']
