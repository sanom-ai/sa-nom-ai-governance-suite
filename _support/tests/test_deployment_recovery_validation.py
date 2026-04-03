import importlib
import json
from types import SimpleNamespace

import pytest


class _FakeServer:
    def __init__(self, port: int = 8765) -> None:
        self.server_port = port
        self.server_address = ('127.0.0.1', port)
        self.shutdown_called = False
        self.closed = False

    def serve_forever(self) -> None:
        return

    def shutdown(self) -> None:
        self.shutdown_called = True

    def server_close(self) -> None:
        self.closed = True


def test_private_server_smoke_reports_missing_token_and_persists(monkeypatch) -> None:
    module = importlib.import_module('sa_nom_governance.deployment.private_server_smoke_test')
    fake_server = _FakeServer()
    persisted: dict[str, object] = {}

    monkeypatch.setattr(module, 'validate_startup_or_raise', lambda config: None)
    monkeypatch.setattr(module, 'create_server', lambda **kwargs: fake_server)
    monkeypatch.setattr(module.time, 'sleep', lambda seconds: None)
    monkeypatch.setattr(module, 'persist_smoke_report', lambda config, result: persisted.update({'result': result}))

    result = module.run_smoke(config=SimpleNamespace(api_token=None), persist_report=True)

    assert result['passed'] is False
    assert result['errors'] == 1
    assert result['checks'][0]['code'] == 'SMOKE_TOKEN'
    assert persisted['result']['checks'][0]['code'] == 'SMOKE_TOKEN'
    assert fake_server.shutdown_called is True
    assert fake_server.closed is True


def test_private_server_smoke_warns_when_no_model_provider_is_configured(monkeypatch) -> None:
    module = importlib.import_module('sa_nom_governance.deployment.private_server_smoke_test')
    fake_server = _FakeServer()

    monkeypatch.setattr(module, 'validate_startup_or_raise', lambda config: None)
    monkeypatch.setattr(module, 'create_server', lambda **kwargs: fake_server)
    monkeypatch.setattr(module.time, 'sleep', lambda seconds: None)

    def fake_request_json(method, host, port, path, body=None, headers=None):
        if path == '/api/session/login':
            return 200, {'session_token': 'session-001'}
        if path in {
            '/api/dashboard',
            '/api/health',
            '/api/roles',
            '/api/role-private-studio',
            '/api/operations/backups',
            '/api/go-live-readiness',
            '/api/compliance',
            '/api/evidence',
            '/api/integrations',
            '/api/model-providers',
        }:
            payload_map = {
                '/api/dashboard': {'summary': {}},
                '/api/health': {'status': 'ok'},
                '/api/roles': {'items': []},
                '/api/role-private-studio': {'item': {}},
                '/api/operations/backups': {'item': {}},
                '/api/go-live-readiness': {'item': {}},
                '/api/compliance': {'item': {}},
                '/api/evidence': {'item': {}},
                '/api/integrations': {'item': {}},
                '/api/model-providers': {'item': {'status': 'ok', 'configured_providers': 0}},
            }
            return 200, payload_map[path]
        if path == '/api/evidence/export':
            return 200, {'result': {'status': 'ok'}}
        if path == '/api/integrations/test-event':
            return 200, {'result': {'status': 'ok'}}
        if path == '/api/session/logout':
            return 200, {}
        raise AssertionError(f'unexpected request: {method} {path}')

    monkeypatch.setattr(module, 'request_json', fake_request_json)

    result = module.run_smoke(config=SimpleNamespace(api_token='owner-token'), persist_report=False)

    assert result['passed'] is True
    assert result['warnings'] == 1
    warning_codes = [item['code'] for item in result['checks'] if item['status'] == 'warning']
    assert warning_codes == ['MODEL_PROVIDER_PROBE']


def test_private_server_smoke_main_exits_when_smoke_fails(monkeypatch, capsys) -> None:
    module = importlib.import_module('sa_nom_governance.deployment.private_server_smoke_test')
    monkeypatch.setattr(module, 'AppConfig', lambda: SimpleNamespace())
    monkeypatch.setattr(module, 'run_smoke', lambda **kwargs: {'passed': False, 'errors': 1})

    with pytest.raises(SystemExit) as exc:
        module.main(['--token', 'owner-token'])

    assert exc.value.code == 1
    assert json.loads(capsys.readouterr().out)['errors'] == 1


def test_guided_smoke_test_main_writes_report_and_exits_on_failure(monkeypatch, tmp_path, capsys) -> None:
    module = importlib.import_module('sa_nom_governance.deployment.guided_smoke_test')
    monkeypatch.setattr(module, 'AppConfig', lambda: SimpleNamespace(review_dir=tmp_path))
    monkeypatch.setattr(module, 'build_guided_smoke_test', lambda **kwargs: {'passed': False, 'generated_at': '2026-04-04T00:00:00+00:00', 'artifacts': {}})

    output_path = tmp_path / 'guided.json'
    with pytest.raises(SystemExit) as exc:
        module.main(['--output', str(output_path)])

    assert exc.value.code == 1
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert payload['artifacts']['guided_report'] == str(output_path)
    assert json.loads(capsys.readouterr().out)['passed'] is False


def test_quick_start_path_main_doctor_exits_on_fail(monkeypatch, tmp_path, capsys) -> None:
    module = importlib.import_module('sa_nom_governance.deployment.quick_start_path')
    monkeypatch.setattr(module, 'AppConfig', lambda: SimpleNamespace(review_dir=tmp_path))
    monkeypatch.setattr(module, 'export_quick_start_doctor', lambda **kwargs: {'status': 'fail', 'artifact_path': str(tmp_path / 'doctor.json')})

    with pytest.raises(SystemExit) as exc:
        module.main(['--doctor', '--doctor-output', str(tmp_path / 'doctor.json')])

    assert exc.value.code == 1
    assert json.loads(capsys.readouterr().out)['status'] == 'fail'


def test_quick_start_path_read_invalid_doctor_report(tmp_path) -> None:
    module = importlib.import_module('sa_nom_governance.deployment.quick_start_path')
    output_path = tmp_path / 'quick_start_doctor.json'
    output_path.write_text('{invalid json', encoding='utf-8')

    loaded = module.read_quick_start_doctor(config=SimpleNamespace(review_dir=tmp_path), output_path=output_path)

    assert loaded['status'] == 'invalid'
    assert loaded['available'] is False
    assert loaded['next_actions'] == ['Regenerate doctor report: python scripts/quick_start_path.py --doctor']


def test_runtime_backup_manager_lists_invalid_manifest(tmp_path) -> None:
    from sa_nom_governance.deployment.runtime_backup_manager import RuntimeBackupManager
    from sa_nom_governance.utils.config import AppConfig

    config = AppConfig(base_dir=tmp_path, persist_runtime=True, environment='development', api_token='owner-token', trusted_registry_signing_key='registry-key')
    invalid_dir = config.runtime_backup_dir / 'backup-invalid'
    invalid_dir.mkdir(parents=True, exist_ok=True)
    (invalid_dir / 'manifest.json').write_text('{invalid json', encoding='utf-8')

    listed = RuntimeBackupManager(config).list_backups(limit=5)

    assert listed[0]['backup_id'] == 'backup-invalid'
    assert listed[0]['status'] == 'invalid_manifest'
    assert listed[0]['error']
