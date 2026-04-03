import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


class _ReportStub:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def to_dict(self) -> dict[str, object]:
        return dict(self._payload)


def _reload_module(module_name: str):
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


def test_api_main_create_app_uses_config_and_engine_builder(monkeypatch) -> None:
    built_configs: list[object] = []

    class DummyConfig:
        pass

    def fake_app_config() -> DummyConfig:
        return DummyConfig()

    def fake_build_engine_app(config: object) -> dict[str, object]:
        built_configs.append(config)
        return {'kind': 'engine-app', 'config_id': id(config)}

    monkeypatch.setattr('sa_nom_governance.utils.config.AppConfig', fake_app_config)
    monkeypatch.setattr('sa_nom_governance.api.api_engine.build_engine_app', fake_build_engine_app)

    module = _reload_module('sa_nom_governance.api.main')

    assert isinstance(module.config, DummyConfig)
    assert module.app == {'kind': 'engine-app', 'config_id': id(module.config)}
    explicit = DummyConfig()
    assert module.create_app(explicit) == {'kind': 'engine-app', 'config_id': id(explicit)}
    assert built_configs[0] is module.config
    assert built_configs[-1] is explicit


def test_run_private_server_check_only_prints_startup_report(monkeypatch, capsys) -> None:
    module = importlib.import_module('sa_nom_governance.deployment.run_private_server')
    config = SimpleNamespace(api_token='owner-token')
    monkeypatch.setattr(module, 'AppConfig', lambda: config)
    monkeypatch.setattr(module, 'validate_startup_or_raise', lambda resolved: _ReportStub({'ready': True, 'environment': 'development'}))
    monkeypatch.setattr(module, 'run_smoke', lambda **kwargs: {'passed': True})
    monkeypatch.setattr(module, 'run_server', lambda **kwargs: (_ for _ in ()).throw(AssertionError('run_server should not be called')))

    module.main(['--check-only'])

    assert json.loads(capsys.readouterr().out) == {'ready': True, 'environment': 'development'}


def test_run_private_server_smoke_before_serve_exits_when_smoke_fails(monkeypatch, capsys) -> None:
    module = importlib.import_module('sa_nom_governance.deployment.run_private_server')
    config = SimpleNamespace(api_token='owner-token')
    monkeypatch.setattr(module, 'AppConfig', lambda: config)
    monkeypatch.setattr(module, 'validate_startup_or_raise', lambda resolved: _ReportStub({'ready': True}))
    monkeypatch.setattr(module, 'run_smoke', lambda **kwargs: {'passed': False, 'reason': 'probe failed'})
    monkeypatch.setattr(module, 'run_server', lambda **kwargs: (_ for _ in ()).throw(AssertionError('run_server should not be called')))

    with pytest.raises(SystemExit) as exc:
        module.main(['--smoke-before-serve'])

    assert exc.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload['startup_smoke']['passed'] is False


def test_run_private_server_runs_server_with_requested_host_port_and_token(monkeypatch) -> None:
    module = importlib.import_module('sa_nom_governance.deployment.run_private_server')
    config = SimpleNamespace(api_token='owner-token')
    calls: dict[str, object] = {}
    monkeypatch.setattr(module, 'AppConfig', lambda: config)
    monkeypatch.setattr(module, 'validate_startup_or_raise', lambda resolved: _ReportStub({'ready': True}))
    monkeypatch.setattr(module, 'run_smoke', lambda **kwargs: {'passed': True})
    monkeypatch.setattr(module, 'run_server', lambda **kwargs: calls.update(kwargs))

    module.main(['--host', '127.0.0.1', '--port', '8080', '--token', 'fresh-token'])

    assert config.api_token == 'fresh-token'
    assert calls['config'] is config
    assert calls['host'] == '127.0.0.1'
    assert calls['port'] == 8080


def test_runtime_backup_main_prints_backup_result(monkeypatch, capsys) -> None:
    module = importlib.import_module('sa_nom_governance.deployment.runtime_backup')
    marker_app = SimpleNamespace(create_runtime_backup=lambda requested_by: {'backup_id': 'backup-001', 'requested_by': requested_by})
    monkeypatch.setattr(module, 'AppConfig', lambda: SimpleNamespace())
    monkeypatch.setattr(module, 'build_engine_app', lambda config: marker_app)

    module.main(['--requested-by', 'TAWAN'])

    assert json.loads(capsys.readouterr().out) == {'backup_id': 'backup-001', 'requested_by': 'TAWAN'}


def test_audit_reseal_main_prints_reseal_result(monkeypatch, capsys) -> None:
    module = importlib.import_module('sa_nom_governance.audit.audit_reseal')
    marker_app = SimpleNamespace(reseal_audit_log=lambda requested_by: {'resealed': True, 'requested_by': requested_by})
    monkeypatch.setattr(module, 'AppConfig', lambda: SimpleNamespace())
    monkeypatch.setattr(module, 'build_engine_app', lambda config: marker_app)

    module.main(['--requested-by', 'OPS'])

    assert json.loads(capsys.readouterr().out) == {'resealed': True, 'requested_by': 'OPS'}


def test_trusted_registry_refresh_collects_role_ids_and_prints_summary(monkeypatch, tmp_path, capsys) -> None:
    module = importlib.import_module('sa_nom_governance.compliance.trusted_registry_refresh')
    roles_dir = tmp_path / 'roles'
    roles_dir.mkdir()
    for name in ['ALPHA.ptn', 'BETA.ptn', 'core_terms.ptn']:
        (roles_dir / name).write_text('role', encoding='utf-8')
    manifest_path = tmp_path / 'manifest.json'
    cache_path = tmp_path / 'cache.json'
    config = SimpleNamespace(
        roles_dir=roles_dir,
        trusted_registry_manifest_path=manifest_path,
        trusted_registry_cache_path=cache_path,
        trusted_registry_signing_key='registry-key',
        trusted_registry_key_id='kid-001',
        trusted_registry_signed_by='TAWAN',
    )
    captured: dict[str, object] = {}

    def fake_write_trusted_registry_files(**kwargs):
        captured.update(kwargs)
        return (
            {'roles': {'ALPHA': {}, 'BETA': {}}, 'signature': {'key_id': 'kid-001'}},
            {'entries': [{'role_id': 'ALPHA'}, {'role_id': 'BETA'}]},
        )

    monkeypatch.setattr(module, 'AppConfig', lambda: config)
    monkeypatch.setattr(module, 'write_trusted_registry_files', fake_write_trusted_registry_files)

    module.main()

    lines = [line.strip() for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert captured['role_ids'] == ['ALPHA', 'BETA']
    assert lines[0] == str(manifest_path)
    assert lines[1] == str(cache_path)
    assert lines[2] == "['ALPHA', 'BETA']"
    assert lines[3] == 'kid-001'
    assert lines[4] == '2'


def test_provider_smoke_test_uses_default_prompt_and_requested_provider(monkeypatch, capsys) -> None:
    module = importlib.import_module('sa_nom_governance.deployment.provider_smoke_test')
    captured: dict[str, object] = {}

    class DummyRegistry:
        def __init__(self, config: object) -> None:
            captured['config'] = config

        def probe(self, provider_id=None, prompt=None):
            captured['provider_id'] = provider_id
            captured['prompt'] = prompt
            return {'status': 'ok', 'provider_id': provider_id, 'prompt': prompt}

    monkeypatch.setattr(module, 'AppConfig', lambda: object())
    monkeypatch.setattr(module, 'ModelProviderRegistry', DummyRegistry)
    monkeypatch.setattr(module, 'DEFAULT_PROBE_PROMPT', 'DEFAULT PROBE')

    module.main(['--provider', 'openai'])

    assert captured['provider_id'] == 'openai'
    assert captured['prompt'] == 'DEFAULT PROBE'
    assert json.loads(capsys.readouterr().out)['status'] == 'ok'


def test_provider_smoke_test_requires_configured_provider_when_requested(monkeypatch, capsys) -> None:
    module = importlib.import_module('sa_nom_governance.deployment.provider_smoke_test')

    class DisabledRegistry:
        def __init__(self, config: object) -> None:
            self.config = config

        def probe(self, provider_id=None, prompt=None):
            return {'status': 'disabled', 'provider_id': provider_id}

    monkeypatch.setattr(module, 'AppConfig', lambda: object())
    monkeypatch.setattr(module, 'ModelProviderRegistry', DisabledRegistry)

    with pytest.raises(SystemExit) as exc:
        module.main(['--require-configured'])

    assert exc.value.code == 1
    assert json.loads(capsys.readouterr().out)['status'] == 'disabled'


def test_access_profile_hash_main_prints_hashed_token(monkeypatch, capsys) -> None:
    module = importlib.import_module('sa_nom_governance.guards.access_profile_hash')
    monkeypatch.setattr(module, 'hash_token', lambda token: f'hash::{token}')

    module.main(['secret-token'])

    assert capsys.readouterr().out.strip() == 'hash::secret-token'


def test_access_profile_rotate_updates_profile_file(monkeypatch, tmp_path, capsys) -> None:
    module = importlib.import_module('sa_nom_governance.guards.access_profile_rotate')
    profiles_path = tmp_path / 'access_profiles.json'
    profiles_path.write_text(
        json.dumps([
            {
                'profile_id': 'owner',
                'token_hash': 'old-hash',
                'previous_token_hashes': ['older-hash'],
                'token': 'plaintext-should-be-removed',
            }
        ], ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    monkeypatch.setattr(module, 'AppConfig', lambda: SimpleNamespace(access_profiles_path=profiles_path))
    monkeypatch.setattr(module, 'hash_token', lambda token: f'hash::{token}')

    module.main(['owner', 'fresh-token', '--keep-previous', '1'])

    payload = json.loads(capsys.readouterr().out)
    data = json.loads(profiles_path.read_text(encoding='utf-8'))
    assert payload['updated'] is True
    assert payload['previous_token_hashes'] == 1
    assert data[0]['token_hash'] == 'hash::fresh-token'
    assert data[0]['previous_token_hashes'] == ['old-hash']
    assert 'token' not in data[0]
    assert data[0]['not_before']
    assert data[0]['rotate_after']


def test_access_profile_rotate_raises_for_missing_profile(monkeypatch, tmp_path) -> None:
    module = importlib.import_module('sa_nom_governance.guards.access_profile_rotate')
    profiles_path = tmp_path / 'access_profiles.json'
    profiles_path.write_text(json.dumps([{'profile_id': 'owner'}], ensure_ascii=False), encoding='utf-8')
    monkeypatch.setattr(module, 'AppConfig', lambda: SimpleNamespace(access_profiles_path=profiles_path))

    with pytest.raises(SystemExit, match='profile not found: missing'):
        module.main(['missing', 'fresh-token'])


def test_register_owner_main_writes_owner_registration(monkeypatch, tmp_path, capsys) -> None:
    module = importlib.import_module('sa_nom_governance.utils.register_owner')
    monkeypatch.setattr(module, 'AppConfig', lambda: SimpleNamespace(runtime_dir=tmp_path))
    output_path = tmp_path / 'owner_registration.json'

    module.main(['--registration-code', 'tower-hq-01', '--output', str(output_path)])

    payload = json.loads(capsys.readouterr().out)
    assert output_path.exists()
    assert payload['owner_registration_path'] == str(output_path.resolve())
    assert payload['registration_code'] == 'TOWER-HQ-01'
    assert payload['organization_id'] == 'TOWER_HQ_01'
