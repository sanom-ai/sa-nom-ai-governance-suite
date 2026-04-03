import io
import json
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
