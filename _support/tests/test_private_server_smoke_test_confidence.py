import io
import json
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from sa_nom_governance.deployment import private_server_smoke_test as smoke
from sa_nom_governance.utils.config import AppConfig


class DummyServer:
    def __init__(self) -> None:
        self.server_port = 8765
        self.server_address = ('127.0.0.1', 8765)
        self.shutdown_called = False
        self.closed = False

    def serve_forever(self) -> None:
        return None

    def shutdown(self) -> None:
        self.shutdown_called = True

    def server_close(self) -> None:
        self.closed = True


class DummyThread:
    def __init__(self) -> None:
        self.started = False
        self.joined = False

    def start(self) -> None:
        self.started = True

    def join(self, timeout: int | None = None) -> None:
        self.joined = True


class FakeResponse:
    def __init__(self, status: int, payload: str) -> None:
        self.status = status
        self._payload = payload.encode('utf-8')

    def read(self) -> bytes:
        return self._payload


class FakeConnection:
    def __init__(self, host: str, port: int, timeout: int) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.request_args: tuple | None = None
        self.closed = False
        self._response = FakeResponse(204, '')

    def request(self, method: str, path: str, body=None, headers=None) -> None:
        self.request_args = (method, path, body, headers)

    def getresponse(self) -> FakeResponse:
        return self._response

    def close(self) -> None:
        self.closed = True


def _config(tmp_path: Path) -> AppConfig:
    config = AppConfig(base_dir=tmp_path, persist_runtime=True)
    config.api_token = 'runtime-token'
    return config


def _loop_ok_responses(provider_item: dict[str, object] | None = None) -> list[tuple[int, dict[str, object]]]:
    provider_item = provider_item or {'status': 'ok', 'configured_providers': 0}
    return [
        (200, {'summary': {}}),
        (200, {'status': 'ok'}),
        (200, {'items': []}),
        (200, {'item': {}}),
        (200, {'item': {}}),
        (200, {'item': {}}),
        (200, {'item': {}}),
        (200, {'item': {}}),
        (200, {'item': {}}),
        (200, {'item': provider_item}),
    ]


def _run_smoke_with_responses(tmp_path: Path, responses: list[tuple[int, dict[str, object]]], *, token: str | None = None, persist_report: bool = True, config_token: str | None = 'runtime-token'):
    config = AppConfig(base_dir=tmp_path, persist_runtime=True)
    config.api_token = config_token
    server = DummyServer()
    thread = DummyThread()
    with (
        patch.object(smoke, 'create_server', return_value=server),
        patch.object(smoke.threading, 'Thread', return_value=thread),
        patch.object(smoke.time, 'sleep', return_value=None),
        patch.object(smoke, 'validate_startup_or_raise', return_value=None),
        patch.object(smoke, 'persist_smoke_report') as persist_mock,
        patch.object(smoke, 'request_json', side_effect=responses),
    ):
        result = smoke.run_smoke(config=config, token=token, persist_report=persist_report)
    return result, server, thread, persist_mock


def test_request_json_serializes_payload_and_handles_blank_response() -> None:
    fake_connection = FakeConnection('127.0.0.1', 8080, 10)
    with patch.object(smoke, 'HTTPConnection', return_value=fake_connection):
        status, payload = smoke.request_json('POST', '127.0.0.1', 8080, '/api/test', body={'hello': 'world'}, headers={'X-Test': '1'})

    assert status == 204
    assert payload == {}
    assert fake_connection.closed is True
    assert fake_connection.request_args is not None
    method, path, body, headers = fake_connection.request_args
    assert method == 'POST'
    assert path == '/api/test'
    assert json.loads(body.decode('utf-8')) == {'hello': 'world'}
    assert headers['Content-Type'] == 'application/json'
    assert headers['X-Test'] == '1'


def test_run_smoke_returns_missing_token_error_without_persist_when_disabled(tmp_path: Path) -> None:
    result, server, thread, persist_mock = _run_smoke_with_responses(
        tmp_path,
        responses=[],
        token=None,
        persist_report=False,
        config_token=None,
    )

    assert result['passed'] is False
    assert result['checks'][0]['code'] == 'SMOKE_TOKEN'
    assert persist_mock.called is False
    assert server.shutdown_called is True
    assert thread.joined is True


def test_run_smoke_handles_login_failure_and_persists_result(tmp_path: Path) -> None:
    result, _server, _thread, persist_mock = _run_smoke_with_responses(
        tmp_path,
        responses=[(401, {})],
    )

    assert result['passed'] is False
    assert result['checks'][0]['code'] == 'SESSION_LOGIN'
    persist_mock.assert_called_once()


def test_run_smoke_handles_endpoint_loop_failure(tmp_path: Path) -> None:
    responses = [(200, {'session_token': 'session-1'}), (500, {})]
    result, _server, _thread, persist_mock = _run_smoke_with_responses(tmp_path, responses)

    assert result['passed'] is False
    assert result['checks'][-1]['code'] == 'DASHBOARD'
    persist_mock.assert_called_once()


def test_run_smoke_handles_evidence_export_failure(tmp_path: Path) -> None:
    responses = [(200, {'session_token': 'session-1'})] + _loop_ok_responses() + [(500, {})]
    result, _server, _thread, _persist_mock = _run_smoke_with_responses(tmp_path, responses)

    assert result['passed'] is False
    assert result['checks'][-1]['code'] == 'EVIDENCE_EXPORT'


def test_run_smoke_handles_integration_and_provider_failures(tmp_path: Path) -> None:
    integration_failure = [(200, {'session_token': 'session-1'})] + _loop_ok_responses() + [(200, {'result': {}}), (500, {})]
    result, _server, _thread, _persist_mock = _run_smoke_with_responses(tmp_path, integration_failure)
    assert result['checks'][-1]['code'] == 'INTEGRATION_TEST_EVENT'

    provider_failure = [(200, {'session_token': 'session-1'})] + _loop_ok_responses() + [(200, {'result': {}}), (200, {'result': {}}), (500, {})]
    result, _server, _thread, _persist_mock = _run_smoke_with_responses(tmp_path, provider_failure)
    assert result['checks'][-1]['code'] == 'MODEL_PROVIDER_STATUS'

    partial_provider = [(200, {'session_token': 'session-1'})] + _loop_ok_responses({'status': 'partial', 'configured_providers': 1}) + [(200, {'result': {}}), (200, {'result': {}}), (200, {'item': {'status': 'partial', 'configured_providers': 1}})]
    result, _server, _thread, _persist_mock = _run_smoke_with_responses(tmp_path, partial_provider)
    assert result['checks'][-1]['code'] == 'MODEL_PROVIDER_STATUS'

    probe_failure = [(200, {'session_token': 'session-1'})] + _loop_ok_responses({'status': 'ok', 'configured_providers': 1}) + [(200, {'result': {}}), (200, {'result': {}}), (200, {'item': {'status': 'ok', 'configured_providers': 1}}), (500, {})]
    result, _server, _thread, _persist_mock = _run_smoke_with_responses(tmp_path, probe_failure)
    assert result['checks'][-1]['code'] == 'MODEL_PROVIDER_PROBE'


def test_run_smoke_succeeds_with_provider_warning_and_logout_warning(tmp_path: Path) -> None:
    responses = (
        [(200, {'session_token': 'session-1'})]
        + _loop_ok_responses({'status': 'ok', 'configured_providers': 0})
        + [(200, {'result': {}}), (200, {'result': {}}), (200, {'item': {'status': 'ok', 'configured_providers': 0}}), (500, {})]
    )
    result, _server, _thread, persist_mock = _run_smoke_with_responses(tmp_path, responses)

    assert result['passed'] is True
    codes = [check['code'] for check in result['checks']]
    assert 'MODEL_PROVIDER_PROBE' in codes
    assert result['warnings'] >= 2
    persist_mock.assert_called_once()


def test_private_server_smoke_parser_and_main_exit_on_failed_result() -> None:
    parser = smoke.build_parser()
    assert parser.parse_args(['--token', 'abc']).token == 'abc'

    with patch.object(smoke, 'run_smoke', return_value={'passed': False}), patch.object(smoke, 'AppConfig', return_value=object()):
        stream = io.StringIO()
        try:
            with redirect_stdout(stream):
                smoke.main(['--token', 'abc'])
        except SystemExit as exc:
            assert exc.code == 1
        else:
            raise AssertionError('Expected main() to exit non-zero when smoke result is not passed.')
        assert '"passed": false' in stream.getvalue().lower()
