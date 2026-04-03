import io
import json
import os
from http import HTTPStatus
from types import SimpleNamespace
from urllib.parse import urlparse

import pytest

from sa_nom_governance.dashboard.dashboard_server import DashboardRequestHandler, SECURITY_HEADERS
from sa_nom_governance.guards.access_control import AccessControl, AccessProfile


def _build_profile(role_name: str = 'owner') -> AccessProfile:
    return AccessProfile(
        profile_id=f'{role_name}-test',
        display_name=role_name.title(),
        role_name=role_name,
        permissions=set(AccessControl.DEFAULT_PERMISSIONS.get(role_name, [])),
    )


def _make_handler(service=None):
    handler = DashboardRequestHandler.__new__(DashboardRequestHandler)
    handler.service = service or SimpleNamespace()
    handler.headers = {}
    handler.path = '/api/test'
    handler.command = 'GET'
    handler.wfile = io.BytesIO()
    handler.rfile = io.BytesIO()
    responses = []
    headers = []
    handler.send_response = lambda status: responses.append(status)
    handler.send_header = lambda key, value: headers.append((key, value))
    handler._test_responses = responses
    handler._test_headers = headers
    return handler


def test_parse_limit_validates_and_caps_values() -> None:
    handler = _make_handler()

    assert handler._parse_limit('', default=25, maximum=50) == 25
    assert handler._parse_limit('20', default=25, maximum=50) == 20
    assert handler._parse_limit('200', default=25, maximum=50) == 50

    with pytest.raises(ValueError, match='limit must be a valid integer'):
        handler._parse_limit('abc')
    with pytest.raises(ValueError, match='limit must be greater than zero'):
        handler._parse_limit('0')


def test_read_json_body_validates_length_and_payload_shape() -> None:
    handler = _make_handler()
    handler.headers = {'Content-Length': '7'}
    handler.rfile = io.BytesIO(b'{"a":1}')
    assert handler._read_json_body() == {'a': 1}

    handler.headers = {'Content-Length': 'x'}
    handler.rfile = io.BytesIO()
    with pytest.raises(ValueError, match='Content-Length must be a valid integer'):
        handler._read_json_body()

    handler.headers = {'Content-Length': str(1024 * 1024 + 1)}
    handler.rfile = io.BytesIO(b'{}')
    with pytest.raises(ValueError, match='1MB safety limit'):
        handler._read_json_body()

    handler.headers = {'Content-Length': '4'}
    handler.rfile = io.BytesIO(b'[1] ')
    with pytest.raises(ValueError, match='JSON body must be an object'):
        handler._read_json_body()


def test_respond_json_writes_status_headers_and_body() -> None:
    handler = _make_handler()

    ended = {'value': False}
    handler.end_headers = lambda: ended.__setitem__('value', True)

    handler._respond_json(HTTPStatus.CREATED, {'status': 'ok'})

    assert handler._test_responses == [HTTPStatus.CREATED]
    assert ('Content-Type', 'application/json; charset=utf-8') in handler._test_headers
    assert ended['value'] is True
    assert json.loads(handler.wfile.getvalue().decode('utf-8')) == {'status': 'ok'}


def test_require_and_run_returns_unauthorized_when_authentication_fails() -> None:
    recorded = []
    auth_result = SimpleNamespace(authenticated=False, profile=None, reason='missing_token', token_present=False, profile_id=None, auth_method='none', session_id=None)
    service = SimpleNamespace(
        authenticate_result=lambda headers: auth_result,
        record_security_event=lambda **kwargs: recorded.append(kwargs),
        access_control=SimpleNamespace(require=lambda profile, permission: True),
    )
    handler = _make_handler(service)
    payloads = []
    handler._respond_json = lambda status, payload: payloads.append((status, payload))

    handler._require_and_run('dashboard.read', lambda profile: None)

    assert payloads[0][0] == HTTPStatus.UNAUTHORIZED
    assert payloads[0][1]['reason'] == 'missing_token'
    assert recorded[0]['action'] == 'security_auth_denied'


def test_require_and_run_returns_forbidden_without_permission() -> None:
    profile = _build_profile('operator')
    recorded = []
    auth_result = SimpleNamespace(authenticated=True, profile=profile, reason='ok', token_present=True, profile_id=profile.profile_id, auth_method='session', session_id='sess-1')
    service = SimpleNamespace(
        authenticate_result=lambda headers: auth_result,
        record_security_event=lambda **kwargs: recorded.append(kwargs),
        access_control=SimpleNamespace(require=lambda profile, permission: False),
    )
    handler = _make_handler(service)
    payloads = []
    handler._respond_json = lambda status, payload: payloads.append((status, payload))

    handler._require_and_run('dashboard.read', lambda profile: None)

    assert payloads[0][0] == HTTPStatus.FORBIDDEN
    assert 'missing dashboard.read' in payloads[0][1]['error']
    assert recorded[0]['action'] == 'security_forbidden'


def test_require_and_run_calls_callback_when_permission_is_granted() -> None:
    profile = _build_profile('owner')
    auth_result = SimpleNamespace(authenticated=True, profile=profile, reason='ok', token_present=True, profile_id=profile.profile_id, auth_method='session', session_id='sess-1')
    service = SimpleNamespace(
        authenticate_result=lambda headers: auth_result,
        record_security_event=lambda **kwargs: None,
        access_control=SimpleNamespace(require=lambda profile, permission: True),
    )
    handler = _make_handler(service)
    seen = []

    handler._require_and_run('dashboard.read', lambda profile: seen.append(profile.profile_id))

    assert seen == [profile.profile_id]


def test_require_owner_run_enforces_owner_role() -> None:
    profile = _build_profile('operator')
    auth_result = SimpleNamespace(authenticated=True, profile=profile, reason='ok', token_present=True, profile_id=profile.profile_id, auth_method='session', session_id='sess-1')
    recorded = []
    service = SimpleNamespace(
        authenticate_result=lambda headers: auth_result,
        record_security_event=lambda **kwargs: recorded.append(kwargs),
    )
    handler = _make_handler(service)
    payloads = []
    handler._respond_json = lambda status, payload: payloads.append((status, payload))

    handler._require_owner_run(lambda profile: None)

    assert payloads[0][0] == HTTPStatus.FORBIDDEN
    assert payloads[0][1]['error'] == 'Forbidden: owner access required'
    assert recorded[0]['action'] == 'security_forbidden'


def test_handle_api_get_documents_passes_filters_to_service() -> None:
    profile = _build_profile('owner')
    captured = {}
    service = SimpleNamespace(
        documents=lambda **kwargs: captured.update(kwargs) or {'summary': {}, 'items': []},
    )
    handler = _make_handler(service)
    responses = []
    handler._respond_json = lambda status, payload: responses.append((status, payload))

    def require_and_run(permission, callback):
        assert permission == 'documents.read'
        callback(profile)

    handler._require_and_run = require_and_run
    handler._session_public = lambda profile: {'profile_id': profile.profile_id}

    handler._handle_api_get(urlparse('/api/documents?limit=25&query=legal&status=published&document_class=POLICY&case_id=CASE-9&active_only=true'))

    assert captured == {
        'limit': 25,
        'query': 'legal',
        'status': 'published',
        'document_class': 'POLICY',
        'case_id': 'CASE-9',
        'active_only': True,
    }
    assert responses[0][0] == HTTPStatus.OK
    assert responses[0][1]['session']['profile_id'] == profile.profile_id


def test_handle_api_post_session_login_denial_returns_unauthorized() -> None:
    auth_result = SimpleNamespace(authenticated=False, profile=None, reason='bad_token', profile_id=None, auth_method='access_token', session_id=None)
    service = SimpleNamespace(
        login_session=lambda headers: (auth_result, None),
        record_security_event=lambda **kwargs: None,
    )
    handler = _make_handler(service)
    payloads = []
    handler._read_json_body = lambda: {}
    handler._respond_json = lambda status, payload: payloads.append((status, payload))

    handler._handle_api_post(urlparse('/api/session/login'))

    assert payloads[0][0] == HTTPStatus.UNAUTHORIZED
    assert payloads[0][1]['reason'] == 'bad_token'


def test_handle_api_post_non_api_route_returns_not_found() -> None:
    handler = _make_handler(SimpleNamespace())
    payloads = []
    handler._respond_json = lambda status, payload: payloads.append((status, payload))
    handler.path = '/outside'

    handler.do_POST()

    assert payloads[0][0] == HTTPStatus.NOT_FOUND
    assert payloads[0][1]['error'] == 'Unknown endpoint.'


def test_do_get_maps_home_and_control_room_to_dashboard_shell(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr('http.server.SimpleHTTPRequestHandler.do_GET', lambda self: calls.append(self.path))

    home_handler = _make_handler(SimpleNamespace())
    home_handler.path = '/home'
    home_handler.do_GET()

    control_handler = _make_handler(SimpleNamespace())
    control_handler.path = '/governance/control-room'
    control_handler.do_GET()

    assert calls == ['/dashboard_index.html', '/dashboard_index.html']


def test_end_headers_adds_security_headers(monkeypatch) -> None:
    captured = []
    monkeypatch.setattr('http.server.SimpleHTTPRequestHandler.end_headers', lambda self: captured.append('ended'))
    handler = _make_handler(SimpleNamespace())
    handler.send_header = lambda key, value: captured.append((key, value))

    handler.end_headers()

    header_pairs = [item for item in captured if isinstance(item, tuple)]
    assert ('Cache-Control', SECURITY_HEADERS['Cache-Control']) in header_pairs
    assert captured[-1] == 'ended'


def test_create_server_wires_service_and_validate_startup(monkeypatch) -> None:
    import sa_nom_governance.dashboard.dashboard_server as module

    config = SimpleNamespace(server_host='127.0.0.1', server_port=8181)
    created = {}

    monkeypatch.setattr(module, 'validate_startup_or_raise', lambda app_config: created.setdefault('validated', app_config))
    monkeypatch.setattr(module, 'DashboardService', lambda app_config: SimpleNamespace(config=app_config))

    class DummyServer:
        def __init__(self, address, handler):
            self.server_address = address
            self.handler = handler

    monkeypatch.setattr(module, 'ThreadingHTTPServer', DummyServer)

    server = module.create_server(config=config, host='0.0.0.0', port=9090)

    assert created['validated'] is config
    assert server.server_address == ('0.0.0.0', 9090)
    assert server.service.config is config


def test_run_server_prints_runtime_summary(monkeypatch, capsys) -> None:
    import sa_nom_governance.dashboard.dashboard_server as module

    profiles = [
        {'display_name': 'Owner', 'role_name': 'owner', 'status': 'active'},
        {'display_name': 'Operator', 'role_name': 'operator', 'status': 'active'},
    ]

    class DummyServer:
        def __init__(self):
            self.server_address = ('127.0.0.1', 8080)
            self.service = SimpleNamespace(
                access_control=SimpleNamespace(list_public_profiles=lambda: profiles),
                deployment_report=SimpleNamespace(ready=True),
            )

        def serve_forever(self):
            print('serve_forever_called')

    monkeypatch.setattr(module, 'create_server', lambda **kwargs: DummyServer())

    module.run_server(config=SimpleNamespace(), host='127.0.0.1', port=8080)

    output = capsys.readouterr().out
    assert 'Dashboard available at http://127.0.0.1:8080/dashboard_index.html' in output
    assert '- Owner [owner] (active)' in output
    assert 'Deployment ready: True' in output
    assert 'serve_forever_called' in output


def test_dashboard_server_main_check_only_prints_report(monkeypatch, capsys) -> None:
    import sa_nom_governance.dashboard.dashboard_server as module

    report = SimpleNamespace(to_dict=lambda: {'ready': True, 'environment': 'development'})
    config = SimpleNamespace(api_token='old-token')

    monkeypatch.setattr(module, 'AppConfig', lambda: config)
    monkeypatch.setattr(module, 'validate_startup_or_raise', lambda resolved: report)
    monkeypatch.setattr(module, 'run_server', lambda **kwargs: (_ for _ in ()).throw(AssertionError('run_server should not be called')))

    module.main(['--check-only', '--token', 'fresh-token'])

    assert config.api_token == 'fresh-token'
    assert json.loads(capsys.readouterr().out) == {'ready': True, 'environment': 'development'}

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path



def _build_real_service(tmp_path: Path):
    from sa_nom_governance.dashboard.dashboard_server import DashboardService
    from sa_nom_governance.utils.config import AppConfig

    config = AppConfig(
        base_dir=tmp_path,
        persist_runtime=True,
        environment='development',
        api_token='owner-token',
        trusted_registry_signing_key='registry-key',
    )
    return DashboardService(config=config)



def _build_custom_profile(role_name: str, permissions: set[str]) -> AccessProfile:
    return AccessProfile(
        profile_id=f'{role_name}-custom',
        display_name=role_name.title(),
        role_name=role_name,
        permissions=permissions,
    )



def test_to_jsonable_and_dashboard_service_access_helpers(tmp_path: Path) -> None:
    from sa_nom_governance.dashboard.dashboard_server import to_jsonable

    @dataclass
    class SamplePayload:
        value: int

    service = _build_real_service(tmp_path)
    wildcard_profile = _build_custom_profile('operator', {'*'})
    delegated_profile = _build_custom_profile('operator', {'ops.manage', 'health.read', 'audit.read'})
    setup_profile = _build_custom_profile('operator', {'ops.manage'})

    assert to_jsonable(SamplePayload(7)) == {'value': 7}
    assert to_jsonable('plain') == 'plain'
    assert service._control_room_access(_build_profile('owner')) is True
    assert service._control_room_access(wildcard_profile) is True
    assert service._control_room_access(delegated_profile) is True
    assert service._control_room_access(_build_profile('viewer')) is False
    assert service._setup_assistant_access(_build_profile('owner')) is True
    assert service._setup_assistant_access(wildcard_profile) is True
    assert service._setup_assistant_access(setup_profile) is True
    assert service._setup_assistant_access(_build_profile('viewer')) is False



def test_dashboard_service_tablet_focus_parse_time_and_session_continuity_states(tmp_path: Path) -> None:
    service = _build_real_service(tmp_path)
    now = datetime.now(timezone.utc)

    assert service._tablet_focus_profile('founder')['tablet_focus_title'] == 'Organization command'
    assert service._tablet_focus_profile('admin')['tablet_focus_title'] == 'Runtime stability and governance pressure'
    assert service._tablet_focus_profile('operator')['tablet_focus_title'] == 'Assignments and governed follow-through'
    assert service._tablet_focus_profile('executive')['tablet_focus_title'] == 'Department direction'
    assert service._parse_time('') is None
    assert service._parse_time('not-a-date') is None
    assert service._parse_time(now.isoformat()) is not None

    standby = service._session_continuity_profile({})
    reconnect = service._session_continuity_profile(
        {
            'status': 'inactive',
            'expires_at': (now - timedelta(minutes=1)).isoformat(),
            'idle_expires_at': (now - timedelta(minutes=1)).isoformat(),
        }
    )
    idle_lock = service._session_continuity_profile(
        {
            'status': 'active',
            'expires_at': (now + timedelta(minutes=20)).isoformat(),
            'idle_expires_at': (now + timedelta(seconds=90)).isoformat(),
        }
    )
    renew_soon = service._session_continuity_profile(
        {
            'status': 'active',
            'expires_at': (now + timedelta(minutes=10)).isoformat(),
            'idle_expires_at': (now + timedelta(minutes=4)).isoformat(),
        }
    )
    ready = service._session_continuity_profile(
        {
            'status': 'active',
            'expires_at': (now + timedelta(minutes=40)).isoformat(),
            'idle_expires_at': (now + timedelta(minutes=20)).isoformat(),
        }
    )

    assert standby['session_continuity_status'] == 'standby'
    assert reconnect['session_continuity_status'] == 'reconnect_now'
    assert idle_lock['session_continuity_status'] == 'idle_lock_soon'
    assert renew_soon['session_continuity_status'] == 'renew_soon'
    assert ready['session_continuity_status'] == 'ready'



def test_dashboard_service_dashboard_hides_advanced_surfaces_without_permissions(tmp_path: Path) -> None:
    service = _build_real_service(tmp_path)
    profile = _build_custom_profile('viewer', {'dashboard.read'})

    snapshot = service.dashboard(profile)

    assert snapshot['requests'] == []
    assert snapshot['overrides'] == []
    assert snapshot['locks'] == []
    assert snapshot['audit'] == []
    assert snapshot['roles'] == []
    assert snapshot['sessions'] == []
    assert snapshot['role_private_studio']['requests'] == []
    assert snapshot['human_ask']['sessions'] == []
    assert snapshot['documents']['items'] == []
    assert snapshot['actions']['items'] == []
    assert snapshot['compliance']['frameworks'] == []
    assert snapshot['evidence_exports']['exports'] == []
    assert snapshot['integrations']['targets'] == []
    assert snapshot['model_providers']['status'] == 'hidden'
    assert snapshot['session']['persona'] == 'executive'
    assert isinstance(snapshot['available_profiles'], list)
    assert isinstance(snapshot['deployment_profile'], dict)



def test_dashboard_service_session_public_uses_live_session_details(tmp_path: Path) -> None:
    service = _build_real_service(tmp_path)
    profile = _build_profile('operator')
    now = datetime.now(timezone.utc)
    active_session = {
        'profile_id': profile.profile_id,
        'status': 'active',
        'created_at': now.isoformat(),
        'last_seen_at': now.isoformat(),
        'expires_at': (now + timedelta(minutes=30)).isoformat(),
        'idle_expires_at': (now + timedelta(minutes=12)).isoformat(),
        'auth_method': 'session',
    }
    service.access_control.list_sessions = lambda status='active': [active_session]

    payload = service._session_public(profile)

    assert payload['persona'] == 'operator'
    assert payload['active_session_count'] == 1
    assert payload['session_status'] == 'active'
    assert payload['session_continuity_status'] == 'ready'
    assert payload['tablet_focus_title'] == 'Assignments and governed follow-through'



def test_dashboard_service_passthrough_runtime_methods_return_operator_shapes(tmp_path: Path, monkeypatch) -> None:
    service = _build_real_service(tmp_path)
    owner = _build_profile('owner')
    service.record_security_event = lambda **kwargs: None
    monkeypatch.setattr(os, 'startfile', lambda path: None, raising=False)

    service.create_request(
        {
            'requester': 'tester@example.com',
            'role_id': 'GOV',
            'action': 'approve_policy',
            'payload': {'resource': 'contract', 'resource_id': 'REQ-1'},
        },
        owner,
    )
    backup = service.create_backup(owner)
    evidence = service.create_evidence_export(owner)
    operations = service.operations(limit=5)
    health = service.health(owner)
    registration = service.owner_registration()
    retention = service.retention()
    open_result = service.open_operator_path({'path': '_runtime'}, owner)

    assert 'backup_id' in backup and 'backup_path' in backup and backup['files_total'] >= backup['files_present']
    assert 'bundle_id' in evidence and 'posture' in evidence and 'tamper_evident' in evidence
    assert isinstance(operations['backups'], list)
    assert 'first_run_action_center' in operations
    assert health['status'] == 'ok'
    assert 'registered' in registration
    assert 'report' in retention and 'plan' in retention
    assert open_result['status'] == 'opened'


@pytest.mark.parametrize(
    ('path', 'permission', 'service_name', 'response_key', 'expected_value'),
    [
        ('/api/health', 'health.read', 'health', 'status', 'ok'),
        ('/api/requests?limit=3', 'requests.read', 'list_requests', 'items', ['req']),
        ('/api/overrides?status=open&limit=2', 'overrides.read', 'list_overrides', 'items', ['ovr']),
        ('/api/locks?status=active&limit=2', 'locks.read', 'list_locks', 'items', ['lock']),
        ('/api/audit', 'audit.read', 'list_audit', 'items', ['audit']),
        ('/api/audit/integrity', 'audit.read', 'audit_integrity', 'integrity', {'ok': True}),
        ('/api/retention', 'health.read', 'retention', 'report', {'state': 'ok'}),
        ('/api/operations/backups', 'health.read', 'operations', 'item', {'summary': {}}),
        ('/api/operations/usability-proof', 'health.read', 'get_usability_proof_bundle', 'item', {'status': 'ready'}),
        ('/api/operations/quick-start-doctor', 'health.read', 'get_quick_start_doctor', 'item', {'status': 'ready'}),
        ('/api/operations/first-run-action-center', 'health.read', 'get_first_run_action_center', 'item', {'items': []}),
        ('/api/go-live-readiness', 'health.read', 'go_live_readiness', 'item', {'ready': True}),
        ('/api/owner-registration', 'health.read', 'owner_registration', 'item', {'registered': True}),
        ('/api/sessions?status=active&limit=2', 'sessions.read', 'list_sessions', 'items', ['session']),
        ('/api/roles', 'roles.read', 'list_roles', 'items', ['role']),
        ('/api/compliance', 'compliance.read', 'compliance', 'item', {'frameworks': []}),
        ('/api/evidence', 'evidence.read', 'evidence', 'item', {'exports': []}),
        ('/api/integrations', 'integration.read', 'integrations', 'item', {'targets': []}),
        ('/api/model-providers', 'integration.read', 'model_providers', 'item', {'providers': []}),
        ('/api/human-ask', 'human_ask.read', 'human_ask_snapshot', 'item', {'sessions': []}),
        ('/api/human-ask/sessions?status=active', 'human_ask.read', 'list_human_ask_sessions', 'items', ['session']),
        ('/api/human-ask/callable-directory', 'human_ask.read', 'callable_directory', 'item', {'entries': []}),
        ('/api/role-private-studio', 'studio.read', 'studio_snapshot', 'item', {'requests': []}),
        ('/api/role-private-studio/requests?status=draft', 'studio.read', 'list_studio_requests', 'items', ['studio']),
    ],
)
def test_handle_api_get_covers_main_surfaces(path, permission, service_name, response_key, expected_value) -> None:
    profile = _build_profile('owner')
    service = SimpleNamespace(access_control=SimpleNamespace(list_public_profiles=lambda: [{'profile_id': profile.profile_id}]))
    if service_name == 'retention':
        setattr(service, service_name, lambda *args, **kwargs: {'report': {'state': 'ok'}, 'plan': {'items': []}})
    elif service_name == 'health':
        setattr(service, service_name, lambda *args, **kwargs: {'status': 'ok'})
    else:
        setattr(service, service_name, lambda *args, **kwargs: expected_value)
    handler = _make_handler(service)
    handler._session_public = lambda profile: {'profile_id': profile.profile_id}
    payloads = []
    handler._respond_json = lambda status, payload: payloads.append((status, payload))
    handler._require_and_run = lambda required, callback: (required == permission) and callback(profile)

    handler._handle_api_get(urlparse(path))

    assert payloads[0][0] == HTTPStatus.OK
    assert response_key in payloads[0][1]



def test_handle_api_get_covers_detail_and_session_routes() -> None:
    profile = _build_profile('owner')
    service = SimpleNamespace(
        get_studio_request=lambda request_id: {'request_id': request_id},
        get_human_ask_session=lambda session_id: {'session_id': session_id},
        get_action=lambda action_id: {'action_id': action_id},
        access_control=SimpleNamespace(list_public_profiles=lambda: [{'profile_id': profile.profile_id}]),
    )
    handler = _make_handler(service)
    handler._session_public = lambda profile: {'profile_id': profile.profile_id}
    payloads = []
    handler._respond_json = lambda status, payload: payloads.append((status, payload))
    handler._require_and_run = lambda permission, callback: callback(profile)

    handler._handle_api_get(urlparse('/api/role-private-studio/requests/REQ-1'))
    handler._handle_api_get(urlparse('/api/human-ask/sessions/SESSION-9'))
    handler._handle_api_get(urlparse('/api/actions/ACT-7'))
    handler._handle_api_get(urlparse('/api/session'))
    handler._handle_api_get(urlparse('/api/unknown'))

    assert payloads[0][1]['item']['request_id'] == 'REQ-1'
    assert payloads[1][1]['item']['session_id'] == 'SESSION-9'
    assert payloads[2][1]['item']['action_id'] == 'ACT-7'
    assert payloads[3][1]['session']['profile_id'] == profile.profile_id
    assert payloads[4][0] == HTTPStatus.NOT_FOUND



def test_handle_api_post_session_logout_success_and_denial() -> None:
    service = SimpleNamespace(
        logout_session=lambda headers: {'success': False, 'reason': 'missing_session'},
        record_security_event=lambda **kwargs: None,
    )
    handler = _make_handler(service)
    handler._read_json_body = lambda: {}
    payloads = []
    handler._respond_json = lambda status, payload: payloads.append((status, payload))

    handler._handle_api_post(urlparse('/api/session/logout'))

    service.logout_session = lambda headers: {'success': True, 'session_id': 'sess-1'}
    handler._handle_api_post(urlparse('/api/session/logout'))

    assert payloads[0][0] == HTTPStatus.UNAUTHORIZED
    assert payloads[1][0] == HTTPStatus.OK
    assert payloads[1][1]['session_id'] == 'sess-1'


@pytest.mark.parametrize(
    ('path', 'permission', 'service_name', 'response_key'),
    [
        ('/api/request', 'request.create', 'create_request', None),
        ('/api/documents', 'documents.create', 'create_document', 'item'),
        ('/api/actions', 'actions.create', 'create_action', 'item'),
        ('/api/retention/enforce', 'retention.manage', 'enforce_retention', 'result'),
        ('/api/audit/reseal', 'audit.manage', 'reseal_audit', 'result'),
        ('/api/operations/backup', 'ops.manage', 'create_backup', 'result'),
        ('/api/operations/usability-proof', 'ops.manage', 'create_usability_proof_bundle', 'result'),
        ('/api/operations/quick-start-doctor', 'ops.manage', 'run_quick_start_doctor', 'result'),
        ('/api/operations/first-run-action-center', 'ops.manage', 'run_first_run_action_center', 'result'),
        ('/api/evidence/export', 'evidence.export', 'create_evidence_export', 'result'),
        ('/api/integrations/test-event', 'integration.manage', 'trigger_integration_test_event', 'result'),
        ('/api/model-providers/probe', 'integration.manage', 'probe_model_providers', 'result'),
        ('/api/human-ask/sessions', 'human_ask.create', 'create_human_ask_session', 'item'),
        ('/api/role-private-studio/requests', 'studio.create', 'create_studio_request', 'item'),
        ('/api/operator/open-path', 'dashboard.read', 'open_operator_path', 'result'),
    ],
)
def test_handle_api_post_covers_main_mutation_routes(path, permission, service_name, response_key) -> None:
    profile = _build_profile('owner')
    payload = {'note': 'x'}
    service = SimpleNamespace()
    setattr(service, service_name, lambda *args, **kwargs: {'status': 'ok', 'service_name': service_name})
    handler = _make_handler(service)
    handler._read_json_body = lambda: payload
    payloads = []
    handler._respond_json = lambda status, response: payloads.append((status, response))
    handler._require_and_run = lambda required, callback: (required == permission) and callback(profile)

    handler._handle_api_post(urlparse(path))

    assert payloads[0][0] == HTTPStatus.OK
    if response_key is None:
        assert payloads[0][1]['service_name'] == service_name
    else:
        assert payloads[0][1][response_key]['service_name'] == service_name



def test_handle_api_post_owner_registration_uses_owner_gate() -> None:
    profile = _build_profile('owner')
    service = SimpleNamespace(update_owner_registration=lambda payload, profile: {'registered': True})
    handler = _make_handler(service)
    handler._read_json_body = lambda: {'registration_code': 'REG-1'}
    payloads = []
    handler._respond_json = lambda status, response: payloads.append((status, response))
    handler._require_owner_run = lambda callback: callback(profile)

    handler._handle_api_post(urlparse('/api/owner-registration'))

    assert payloads[0][0] == HTTPStatus.OK
    assert payloads[0][1]['item']['registered'] is True


@pytest.mark.parametrize(
    ('path', 'permission', 'service_name', 'response_key'),
    [
        ('/api/sessions/SESS-1/revoke', 'session.manage', 'revoke_session', 'result'),
        ('/api/overrides/OVR-1/approve', 'override.review', 'approve_override', None),
        ('/api/overrides/OVR-1/veto', 'override.review', 'veto_override', None),
        ('/api/documents/DOC-1/update', 'documents.create', 'update_document', 'item'),
        ('/api/documents/DOC-1/submit-review', 'documents.create', 'submit_document_review', 'item'),
        ('/api/documents/DOC-1/approve', 'documents.review', 'approve_document', 'item'),
        ('/api/documents/DOC-1/publish', 'documents.publish', 'publish_document', 'item'),
        ('/api/documents/DOC-1/archive', 'documents.archive', 'archive_document', 'item'),
        ('/api/actions/ACT-1/execute', 'actions.execute', 'execute_action', 'item'),
        ('/api/role-private-studio/requests/REQ-1/update', 'studio.create', 'update_studio_request', 'item'),
        ('/api/role-private-studio/requests/REQ-1/ptag', 'studio.create', 'update_studio_request_ptag', 'item'),
        ('/api/role-private-studio/requests/REQ-1/ptag-reset', 'studio.create', 'reset_studio_request_ptag', 'item'),
        ('/api/role-private-studio/requests/REQ-1/refresh', 'studio.create', 'refresh_studio_request', 'item'),
        ('/api/role-private-studio/requests/REQ-1/restore-revision', 'studio.create', 'restore_studio_request_revision', 'item'),
        ('/api/role-private-studio/requests/REQ-1/review', 'studio.review', 'review_studio_request', 'item'),
        ('/api/role-private-studio/requests/REQ-1/publish', 'studio.publish', 'publish_studio_request', 'item'),
        ('/api/role-private-studio/requests/REQ-1/human-ask-record', 'human_ask.create', 'create_human_ask_studio_record', 'item'),
    ],
)
def test_handle_api_post_covers_detail_mutation_routes(path, permission, service_name, response_key) -> None:
    profile = _build_profile('owner')
    payload = {'note': 'x', 'revision_number': 2}
    service = SimpleNamespace()
    setattr(service, service_name, lambda *args, **kwargs: {'status': 'ok', 'service_name': service_name})
    handler = _make_handler(service)
    handler._read_json_body = lambda: payload
    payloads = []
    handler._respond_json = lambda status, response: payloads.append((status, response))
    handler._require_and_run = lambda required, callback: (required == permission) and callback(profile)

    handler._handle_api_post(urlparse(path))

    assert payloads[0][0] == HTTPStatus.OK
    if response_key is None:
        assert payloads[0][1]['service_name'] == service_name
    else:
        assert payloads[0][1][response_key]['service_name'] == service_name



def test_handle_api_post_unknown_api_endpoint_returns_not_found() -> None:
    handler = _make_handler(SimpleNamespace())
    handler._read_json_body = lambda: {}
    payloads = []
    handler._respond_json = lambda status, response: payloads.append((status, response))

    handler._handle_api_post(urlparse('/api/unknown'))

    assert payloads[0][0] == HTTPStatus.NOT_FOUND



def test_read_json_body_accepts_zero_length_and_invalid_json() -> None:
    handler = _make_handler()

    handler.headers = {'Content-Length': '0'}
    handler.rfile = io.BytesIO()
    assert handler._read_json_body() == {}

    handler.headers = {'Content-Length': '3'}
    handler.rfile = io.BytesIO(b'   ')
    assert handler._read_json_body() == {}

    handler.headers = {'Content-Length': '5'}
    handler.rfile = io.BytesIO(b'{bad}')
    with pytest.raises(ValueError, match='Invalid JSON body'):
        handler._read_json_body()



def test_dashboard_server_main_without_check_only_runs_server(monkeypatch) -> None:
    import sa_nom_governance.dashboard.dashboard_server as module

    config = SimpleNamespace(api_token='seed-token')
    called = {}

    monkeypatch.setattr(module, 'AppConfig', lambda: config)
    monkeypatch.setattr(module, 'validate_startup_or_raise', lambda resolved: SimpleNamespace(to_dict=lambda: {'ready': True}))
    monkeypatch.setattr(module, 'run_server', lambda **kwargs: called.update(kwargs))

    module.main(['--host', '0.0.0.0', '--port', '9090', '--token', 'fresh-token'])

    assert config.api_token == 'fresh-token'
    assert called['config'] is config
    assert called['host'] == '0.0.0.0'
    assert called['port'] == 9090

