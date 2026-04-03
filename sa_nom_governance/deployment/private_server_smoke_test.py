import argparse
import json
import threading
import time
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.dashboard.dashboard_server import create_server
from sa_nom_governance.deployment.deployment_profile import validate_startup_or_raise
from sa_nom_governance.deployment.go_live_readiness import persist_smoke_report


@dataclass(slots=True)
class SmokeCheck:
    code: str
    status: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def request_json(method: str, host: str, port: int, path: str, body: dict | None = None, headers: dict[str, str] | None = None) -> tuple[int, dict[str, object]]:
    connection = HTTPConnection(host, port, timeout=10)
    payload = json.dumps(body or {}).encode('utf-8')
    request_headers = {'Content-Type': 'application/json'}
    if headers:
        request_headers.update(headers)
    connection.request(method, path, body=payload if method != 'GET' else None, headers=request_headers)
    response = connection.getresponse()
    raw = response.read().decode('utf-8')
    connection.close()
    data = json.loads(raw) if raw.strip() else {}
    return response.status, data


def run_smoke(config: AppConfig, token: str | None = None, persist_report: bool = True) -> dict[str, object]:
    validate_startup_or_raise(config)
    host = '127.0.0.1'
    server: ThreadingHTTPServer = create_server(config=config, host=host, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.2)

    checks: list[SmokeCheck] = []
    runtime_token = token or config.api_token

    try:
        if not runtime_token:
            checks.append(SmokeCheck('SMOKE_TOKEN', 'error', 'No API token available for smoke test.'))
            result = _build_result(False, server, checks)
            if persist_report:
                persist_smoke_report(config, result)
            return result

        status, payload = request_json('POST', host, server.server_port, '/api/session/login', headers={'X-SA-NOM-Token': runtime_token})
        if status != 200 or not payload.get('session_token'):
            checks.append(SmokeCheck('SESSION_LOGIN', 'error', f'Login failed with status {status}.'))
            result = _build_result(False, server, checks)
            if persist_report:
                persist_smoke_report(config, result)
            return result
        session_token = str(payload['session_token'])
        checks.append(SmokeCheck('SESSION_LOGIN', 'ok', 'Session login succeeded.'))

        auth_headers = {'X-SA-NOM-Session': session_token}
        for code, path, expected_key, success_message, failure_message in [
            ('DASHBOARD', '/api/dashboard', 'summary', 'Dashboard payload loaded.', 'Dashboard load failed'),
            ('HEALTH', '/api/health', 'status', 'Health endpoint returned ok.', 'Health endpoint failed'),
            ('ROLES', '/api/roles', 'items', 'Roles endpoint returned live PTAG packs.', 'Roles endpoint failed'),
            ('ROLE_PRIVATE_STUDIO', '/api/role-private-studio', 'item', 'Role Private Studio endpoint returned a live snapshot.', 'Role Private Studio endpoint failed'),
            ('OPERATIONS_BACKUPS', '/api/operations/backups', 'item', 'Operations backup endpoint returned runtime backup state.', 'Operations backup endpoint failed'),
            ('GO_LIVE_READINESS', '/api/go-live-readiness', 'item', 'Go-live readiness endpoint returned the current deployment gate.', 'Go-live readiness endpoint failed'),
            ('COMPLIANCE', '/api/compliance', 'item', 'Compliance endpoint returned framework alignment data.', 'Compliance endpoint failed'),
            ('EVIDENCE', '/api/evidence', 'item', 'Evidence endpoint returned auditor export state.', 'Evidence endpoint failed'),
            ('INTEGRATIONS', '/api/integrations', 'item', 'Integration endpoint returned registry and delivery state.', 'Integration endpoint failed'),
            ('MODEL_PROVIDERS', '/api/model-providers', 'item', 'Model provider endpoint returned runtime provider state.', 'Model provider endpoint failed'),
        ]:
            status, data = request_json('GET', host, server.server_port, path, headers=auth_headers)
            if status != 200 or expected_key not in data:
                checks.append(SmokeCheck(code, 'error', f'{failure_message} with status {status}.'))
                result = _build_result(False, server, checks)
                if persist_report:
                    persist_smoke_report(config, result)
                return result
            checks.append(SmokeCheck(code, 'ok', success_message))

        export_status, export_payload = request_json('POST', host, server.server_port, '/api/evidence/export', headers=auth_headers)
        if export_status != 200 or 'result' not in export_payload:
            checks.append(SmokeCheck('EVIDENCE_EXPORT', 'error', f'Evidence export failed with status {export_status}.'))
            result = _build_result(False, server, checks)
            if persist_report:
                persist_smoke_report(config, result)
            return result
        checks.append(SmokeCheck('EVIDENCE_EXPORT', 'ok', 'Evidence export completed.'))

        integration_status, integration_payload = request_json('POST', host, server.server_port, '/api/integrations/test-event', headers=auth_headers)
        if integration_status != 200 or 'result' not in integration_payload:
            checks.append(SmokeCheck('INTEGRATION_TEST_EVENT', 'error', f'Integration test event failed with status {integration_status}.'))
            result = _build_result(False, server, checks)
            if persist_report:
                persist_smoke_report(config, result)
            return result
        checks.append(SmokeCheck('INTEGRATION_TEST_EVENT', 'ok', 'Integration test event dispatched successfully.'))

        provider_status, provider_payload = request_json('GET', host, server.server_port, '/api/model-providers', headers=auth_headers)
        provider_item = provider_payload.get('item', {}) if provider_status == 200 else {}
        if provider_status != 200 or not isinstance(provider_item, dict):
            checks.append(SmokeCheck('MODEL_PROVIDER_STATUS', 'error', f'Model provider status failed with status {provider_status}.'))
            result = _build_result(False, server, checks)
            if persist_report:
                persist_smoke_report(config, result)
            return result
        if provider_item.get('status') == 'partial':
            checks.append(SmokeCheck('MODEL_PROVIDER_STATUS', 'error', 'Model provider configuration is partial.'))
            result = _build_result(False, server, checks)
            if persist_report:
                persist_smoke_report(config, result)
            return result
        configured_providers = int(provider_item.get('configured_providers', 0) or 0)
        if configured_providers > 0:
            probe_status, probe_payload = request_json('POST', host, server.server_port, '/api/model-providers/probe', headers=auth_headers)
            if probe_status != 200 or probe_payload.get('result', {}).get('status') != 'ok':
                checks.append(SmokeCheck('MODEL_PROVIDER_PROBE', 'error', f'Model provider probe failed with status {probe_status}.'))
                result = _build_result(False, server, checks)
                if persist_report:
                    persist_smoke_report(config, result)
                return result
            checks.append(SmokeCheck('MODEL_PROVIDER_PROBE', 'ok', 'Configured model providers responded successfully.'))
        else:
            checks.append(SmokeCheck('MODEL_PROVIDER_PROBE', 'warning', 'No model providers are configured for this runtime.'))

        logout_status, _logout_payload = request_json('POST', host, server.server_port, '/api/session/logout', headers=auth_headers)
        if logout_status != 200:
            checks.append(SmokeCheck('SESSION_LOGOUT', 'warning', f'Session logout returned status {logout_status}.'))
        else:
            checks.append(SmokeCheck('SESSION_LOGOUT', 'ok', 'Session logout succeeded.'))

        result = _build_result(True, server, checks)
        if persist_report:
            persist_smoke_report(config, result)
        return result
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def _build_result(passed: bool, server: ThreadingHTTPServer, checks: list[SmokeCheck]) -> dict[str, object]:
    return {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'passed': passed and not any(check.status == 'error' for check in checks),
        'host': server.server_address[0],
        'port': server.server_address[1],
        'checks': [check.to_dict() for check in checks],
        'errors': sum(1 for check in checks if check.status == 'error'),
        'warnings': sum(1 for check in checks if check.status == 'warning'),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Run a private-server smoke test against a local ephemeral SA-NOM runtime.')
    parser.add_argument('--token', default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    config = AppConfig()
    result = run_smoke(config=config, token=args.token)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
