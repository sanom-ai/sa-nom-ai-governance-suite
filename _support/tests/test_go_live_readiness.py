import shutil
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from config import AppConfig
from go_live_readiness import build_go_live_readiness, load_smoke_report, persist_smoke_report


@contextmanager
def workspace_temp_dir():
    source_base = Path(__file__).resolve().parents[2]
    runtime_tmp = source_base / "_runtime" / "tmp_test"
    runtime_tmp.mkdir(parents=True, exist_ok=True)
    temp_path = runtime_tmp / f"go_live_readiness_{uuid4().hex[:8]}"
    temp_path.mkdir(parents=True, exist_ok=True)
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


def test_smoke_report_roundtrip():
    with workspace_temp_dir() as temp_dir:
        config = AppConfig(
            base_dir=temp_dir,
            environment='development',
            api_token='owner-token',
            trusted_registry_signing_key='registry-key',
        )
        report = {
            'generated_at': '2026-03-29T00:00:00+00:00',
            'passed': True,
            'host': '127.0.0.1',
            'port': 8080,
            'checks': [{'code': 'HEALTH', 'status': 'ok', 'message': 'Health endpoint returned ok.'}],
            'errors': 0,
            'warnings': 0,
        }
        persist_smoke_report(config, report)
        loaded = load_smoke_report(config.startup_smoke_report_path)
        assert loaded['present'] is True
        assert loaded['passed'] is True
        assert loaded['status'] == 'passed'
        assert loaded['checks_total'] == 1


def test_smoke_report_missing_file():
    with workspace_temp_dir() as temp_dir:
        config = AppConfig(
            base_dir=temp_dir,
            environment='development',
            api_token='owner-token',
            trusted_registry_signing_key='registry-key',
        )
        loaded = load_smoke_report(config.startup_smoke_report_path)
        assert loaded['present'] is False
        assert loaded['status'] == 'missing'


def test_go_live_readiness_has_no_legacy_advisory_when_audit_is_fully_verified():
    class _AccessControl:
        def health(self):
            return {'plain_file_tokens': 0}

    class _App:
        access_control = _AccessControl()

        def health(self):
            return {
                'trusted_registry': {'signature_trusted': True},
                'audit_integrity': {'status': 'verified'},
            }

    with workspace_temp_dir() as temp_dir:
        config = AppConfig(
            base_dir=temp_dir,
            environment='development',
            api_token='owner-token',
            trusted_registry_signing_key='registry-key',
        )
        assert config.access_profiles_path is not None
        config.access_profiles_path.write_text(
            (
                '[{"profile_id":"operator-one","display_name":"Operator One","role_name":"operator","token_hash":"hash-1","permissions":["dashboard.read","requests.read","request.create","studio.read","studio.create","human_ask.read","human_ask.create","session.manage","retention.manage","audit.manage","ops.manage","studio.publish"]},'
                '{"profile_id":"reviewer-one","display_name":"Reviewer One","role_name":"reviewer","token_hash":"hash-2"},'
                '{"profile_id":"auditor-one","display_name":"Auditor One","role_name":"auditor","token_hash":"hash-3"},'
                '{"profile_id":"viewer-one","display_name":"Viewer One","role_name":"viewer","token_hash":"hash-4"}]'
            ),
            encoding='utf-8',
        )
        persist_smoke_report(config, {'generated_at': '2026-03-29T00:00:00+00:00', 'passed': True, 'checks': [], 'errors': 0, 'warnings': 0})
        review_pack = config.review_dir
        review_pack.mkdir(exist_ok=True)
        (review_pack / 'manifest.json').write_text('{"generated_at":"2026-03-29T00:00:00+00:00","groups":{}}', encoding='utf-8')

        readiness = build_go_live_readiness(config, app=_App())

        assert readiness['status'] == 'ready'
        assert readiness['advisories'] == []


def test_go_live_readiness_becomes_guarded_when_only_advisories_remain():
    class _AccessControl:
        def health(self):
            return {'plain_file_tokens': 0}

    class _App:
        access_control = _AccessControl()

        def health(self):
            return {
                'trusted_registry': {'signature_trusted': True},
                'audit_integrity': {'status': 'verified'},
            }

        def studio_snapshot(self, limit: int = 100):
            return {
                'summary': {
                    'requests_total': 3,
                    'ready_to_publish_total': 1,
                    'structural_guarded_total': 1,
                    'structural_blocked_total': 0,
                    'publication_blocked_total': 0,
                }
            }

    with workspace_temp_dir() as temp_dir:
        config = AppConfig(
            base_dir=temp_dir,
            environment='development',
            api_token='owner-token',
            trusted_registry_signing_key='registry-key',
        )
        assert config.access_profiles_path is not None
        config.access_profiles_path.write_text(
            (
                '[{"profile_id":"operator-one","display_name":"Operator One","role_name":"operator","token_hash":"hash-1"},'
                '{"profile_id":"reviewer-one","display_name":"Reviewer One","role_name":"reviewer","token_hash":"hash-2"}]'
            ),
            encoding='utf-8',
        )
        persist_smoke_report(config, {'generated_at': '2026-03-29T00:00:00+00:00', 'passed': True, 'checks': [], 'errors': 0, 'warnings': 0})
        review_pack = config.review_dir
        review_pack.mkdir(exist_ok=True)
        (review_pack / 'manifest.json').write_text('{"generated_at":"2026-03-29T00:00:00+00:00","groups":{}}', encoding='utf-8')

        readiness = build_go_live_readiness(config, app=_App())

        assert readiness['status'] == 'guarded'
        assert readiness['ready'] is True
        assert readiness['gates']['delegated_privileged_operations'] is False
        assert readiness['gates']['studio_structural_clear'] is False
        assert readiness['privileged_operations']['status'] == 'warning'
        assert readiness['studio_structural']['status'] == 'guarded'
        assert any('owner-only' in advisory or 'guarded drafts' in advisory for advisory in readiness['advisories'])
