import json
from argparse import ArgumentParser
from dataclasses import asdict, is_dataclass
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from sa_nom_governance.guards.access_control import AccessProfile
from sa_nom_governance.api.api_engine import build_engine_app
from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.dashboard.dashboard_data import DashboardSnapshotBuilder
from sa_nom_governance.deployment.deployment_profile import build_deployment_report, validate_startup_or_raise
from sa_nom_governance.utils.owner_registration import (
    build_owner_registration,
    write_owner_registration,
)


SECURITY_HEADERS = {
    'Cache-Control': 'no-store',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'Referrer-Policy': 'no-referrer',
    'Cross-Origin-Opener-Policy': 'same-origin',
    'Cross-Origin-Resource-Policy': 'same-origin',
    'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
    'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'",
}


def to_jsonable(value):
    if is_dataclass(value):
        return asdict(value)
    return value


class DashboardService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.deployment_report = build_deployment_report(config)
        self.app = build_engine_app(config)
        self.snapshot_builder = DashboardSnapshotBuilder(config=config, app=self.app)
        self.access_control = self.app.access_control
        self.base_dir = Path(config.base_dir)
        self.static_dir = Path(__file__).resolve().parent / 'static'

    def authenticate_result(self, headers):
        return self.access_control.authenticate_result(headers)

    def login_session(self, headers):
        return self.access_control.issue_session_from_headers(headers)

    def logout_session(self, headers):
        return self.access_control.revoke_session_from_headers(headers)

    def dashboard(self, profile: AccessProfile) -> dict[str, object]:
        snapshot = self.snapshot_builder.build()
        if not profile.can('requests.read'):
            snapshot['requests'] = []
        if not profile.can('overrides.read'):
            snapshot['overrides'] = []
        if not profile.can('locks.read'):
            snapshot['locks'] = []
        if not profile.can('audit.read'):
            snapshot['audit'] = []
        if not profile.can('roles.read'):
            snapshot['roles'] = []
        if not profile.can('sessions.read'):
            snapshot['sessions'] = []
        if not profile.can('studio.read'):
            snapshot['role_private_studio'] = {'summary': {}, 'requests': [], 'template': {}, 'examples': []}
        if not profile.can('human_ask.read'):
            snapshot['human_ask'] = {'summary': {}, 'sessions': [], 'callable_directory': {'summary': {}, 'entries': []}}
        if not profile.can('compliance.read'):
            snapshot['compliance'] = {'summary': {}, 'frameworks': [], 'role_mappings': [], 'capabilities': {}}
        if not profile.can('evidence.read'):
            snapshot['evidence_exports'] = {'summary': {}, 'exports': []}
        if not profile.can('integration.read'):
            snapshot['integrations'] = {'summary': {}, 'targets': [], 'deliveries': []}
            snapshot['model_providers'] = {'status': 'hidden', 'providers': []}
        snapshot['session'] = profile.to_public_dict()
        snapshot['available_profiles'] = self.access_control.list_public_profiles()
        snapshot['deployment_profile'] = self.deployment_report.to_dict()
        return snapshot

    def health(self, profile: AccessProfile) -> dict[str, object]:
        return {
            'status': 'ok',
            'environment': self.config.environment,
            'token_gate': 'enabled' if self.access_control.list_public_profiles() else 'disabled',
            'server_host': self.config.server_host,
            'server_port': self.config.server_port,
            'server_public_base_url': self.config.server_public_base_url,
            'runtime': self.snapshot_builder.runtime_health(),
            'retention': self.snapshot_builder.retention_report(),
            'retention_plan': self.snapshot_builder.retention_plan(),
            'go_live_readiness': self.snapshot_builder.go_live_readiness(),
            'access_control': self.access_control.health(),
            'deployment_profile': self.deployment_report.to_dict(),
            'integrations': self.app.integration_snapshot(limit=10),
            'model_providers': self.app.model_provider_snapshot(),
            'human_ask': self.app.human_ask_snapshot(limit=10),
            'session': profile.to_public_dict(),
        }

    def owner_registration(self) -> dict[str, object]:
        return self.snapshot_builder.owner_registration()

    def update_owner_registration(self, payload: dict[str, object], profile: AccessProfile) -> dict[str, object]:
        if self.config.owner_registration_path is None:
            raise ValueError('Owner registration path is not configured.')
        existing = self.config.owner_registration()
        registration = build_owner_registration(payload, existing=existing)
        write_owner_registration(self.config.owner_registration_path, registration, force=True)
        self.config.reload_owner_registration()
        self.app = build_engine_app(self.config)
        self.deployment_report = build_deployment_report(self.config)
        self.access_control = self.app.access_control
        self.snapshot_builder = DashboardSnapshotBuilder(config=self.config, app=self.app)
        self.record_security_event(
            action='owner_registration_updated',
            outcome='updated',
            reason='Runtime registration code updated from dashboard.',
            metadata={
                'updated_by': profile.display_name,
                'registration_code': registration.registration_code,
                'deployment_mode': registration.deployment_mode,
                'organization_name': registration.organization_name,
                'organization_id': registration.organization_id,
                'executive_owner_id': registration.executive_owner_id,
            },
        )
        return self.snapshot_builder.owner_registration()

    def list_requests(self, limit: int = 200):
        return self.snapshot_builder.list_requests(limit=limit)

    def list_overrides(self, status: str | None = None, limit: int = 100):
        return self.snapshot_builder.list_overrides(status=status, limit=limit)

    def list_locks(self, status: str | None = None, limit: int = 100):
        return self.snapshot_builder.list_locks(status=status, limit=limit)

    def list_audit(self, limit: int = 200):
        return self.snapshot_builder.list_audit(limit=limit)

    def audit_integrity(self):
        return self.app.audit_integrity()

    def reseal_audit(self, profile: AccessProfile):
        return self.app.reseal_audit_log(requested_by=profile.display_name)

    def retention(self):
        return {'report': self.app.retention_report(), 'plan': self.app.retention_plan()}

    def operations(self, limit: int = 20):
        return {'summary': self.app.runtime_backup_summary(), 'backups': self.app.list_runtime_backups(limit=limit)}

    def create_backup(self, profile: AccessProfile):
        return self.app.create_runtime_backup(requested_by=profile.display_name)

    def create_usability_proof_bundle(self, profile: AccessProfile, payload: dict[str, object]):
        from sa_nom_governance.deployment.usability_proof_bundle import export_usability_proof_bundle

        run_quick_start = bool(payload.get('run_quick_start', False))
        output_raw = str(payload.get('output_path', '')).strip()
        output_path = Path(output_raw) if output_raw else None
        return export_usability_proof_bundle(
            config=self.config,
            output_path=output_path,
            run_quick_start=run_quick_start,
        )

    def go_live_readiness(self):
        return self.snapshot_builder.go_live_readiness()

    def list_sessions(self, status: str | None = None, limit: int = 100):
        return self.app.list_sessions(status=status)[:limit]

    def revoke_session(self, session_id: str, payload: dict[str, object], profile: AccessProfile):
        reason = str(payload.get('reason') or f'Revoked by {profile.display_name}.')
        return self.app.revoke_session(session_id, reason=reason)

    def list_roles(self):
        return self.snapshot_builder.list_roles()

    def compliance(self):
        return self.app.compliance_snapshot()

    def evidence(self, limit: int = 20):
        return {'summary': self.app.evidence_pack_summary(), 'exports': self.app.list_evidence_packs(limit=limit)}

    def create_evidence_export(self, profile: AccessProfile):
        return self.app.create_evidence_pack(requested_by=profile.display_name)

    def integrations(self, limit: int = 50):
        return self.app.integration_snapshot(limit=limit)

    def model_providers(self):
        return self.app.model_provider_snapshot()

    def probe_model_providers(self, profile: AccessProfile, payload: dict[str, object]):
        provider_id = str(payload.get('provider_id') or '').strip() or None
        return self.app.probe_model_providers(requested_by=profile.display_name, provider_id=provider_id)

    def trigger_integration_test_event(self, profile: AccessProfile, payload: dict[str, object]):
        event_type = str(payload.get('event_type') or 'integration.test.manual')
        return self.app.trigger_integration_test_event(requested_by=profile.display_name, event_type=event_type)

    def list_studio_requests(self, status: str | None = None, limit: int = 100):
        return self.app.list_studio_requests(status=status, limit=limit)

    def studio_snapshot(self, limit: int = 50):
        return self.app.studio_snapshot(limit=limit)

    def human_ask_snapshot(self, limit: int = 50):
        return self.app.human_ask_snapshot(limit=limit)

    def list_human_ask_sessions(self, status: str | None = None, limit: int = 100):
        return self.app.list_human_ask_sessions(status=status, limit=limit)

    def get_human_ask_session(self, session_id: str):
        return self.app.get_human_ask_session(session_id)

    def callable_directory(self, limit: int = 200):
        return self.app.list_callable_directory(limit=limit)

    def create_human_ask_session(self, payload: dict[str, object], profile: AccessProfile):
        return self.app.create_human_ask_session(payload, requested_by=profile.display_name)

    def create_human_ask_studio_record(self, studio_request_id: str, payload: dict[str, object], profile: AccessProfile):
        return self.app.create_human_ask_studio_record(studio_request_id=studio_request_id, payload=payload, requested_by=profile.display_name)

    def get_studio_request(self, request_id: str):
        return self.app.get_studio_request(request_id)

    def create_studio_request(self, payload: dict[str, object], profile: AccessProfile):
        return self.app.create_studio_request(payload, requested_by=profile.display_name)

    def update_studio_request(self, request_id: str, payload: dict[str, object], profile: AccessProfile):
        return self.app.update_studio_request(request_id=request_id, payload=payload, updated_by=profile.display_name)

    def update_studio_request_ptag(self, request_id: str, payload: dict[str, object], profile: AccessProfile):
        return self.app.update_studio_request_ptag(request_id=request_id, ptag_source=str(payload.get('ptag_source') or ''), updated_by=profile.display_name)

    def reset_studio_request_ptag(self, request_id: str, profile: AccessProfile):
        return self.app.reset_studio_request_ptag(request_id=request_id, updated_by=profile.display_name)

    def refresh_studio_request(self, request_id: str):
        return self.app.refresh_studio_request(request_id)

    def restore_studio_request_revision(self, request_id: str, payload: dict[str, object], profile: AccessProfile):
        revision_number = int(payload.get('revision_number') or 0)
        if revision_number <= 0:
            raise ValueError('A positive revision_number is required.')
        return self.app.restore_studio_request_revision(
            request_id=request_id,
            revision_number=revision_number,
            restored_by=str(payload.get('restored_by') or profile.display_name),
        )

    def review_studio_request(self, request_id: str, payload: dict[str, object], profile: AccessProfile):
        return self.app.review_studio_request(request_id=request_id, reviewer=str(payload.get('reviewer') or profile.display_name), decision=str(payload.get('decision') or 'request_changes'), note=str(payload.get('note') or 'Reviewed from dashboard.'))

    def publish_studio_request(self, request_id: str, payload: dict[str, object], profile: AccessProfile):
        return self.app.publish_studio_request(request_id=request_id, published_by=str(payload.get('published_by') or profile.display_name))

    def create_request(self, payload: dict[str, object], profile: AccessProfile):
        requester = str(payload.get('requester') or profile.display_name)
        return to_jsonable(self.app.request(requester=requester, role_id=str(payload.get('role_id', '')), action=str(payload.get('action', '')), payload=payload.get('payload', {}) if isinstance(payload.get('payload', {}), dict) else {}, metadata=payload.get('metadata', {}) if isinstance(payload.get('metadata', {}), dict) else {}))

    def approve_override(self, request_id: str, payload: dict[str, object], profile: AccessProfile):
        return to_jsonable(self.app.approve_override(request_id, resolved_by=str(payload.get('resolved_by') or profile.display_name), note=str(payload.get('note', 'Approved from dashboard.'))))

    def veto_override(self, request_id: str, payload: dict[str, object], profile: AccessProfile):
        return to_jsonable(self.app.veto_override(request_id, resolved_by=str(payload.get('resolved_by') or profile.display_name), note=str(payload.get('note', 'Vetoed from dashboard.'))))

    def enforce_retention(self, payload: dict[str, object]):
        dry_run_raw = payload.get('dry_run', True)
        dry_run = dry_run_raw if isinstance(dry_run_raw, bool) else str(dry_run_raw).strip().lower() not in {'0', 'false', 'no'}
        return self.app.enforce_retention(dry_run=dry_run)

    def record_security_event(self, action: str, outcome: str, reason: str, metadata: dict[str, object]) -> None:
        self.app.engine.audit_logger.record_event(active_role='SECURITY', action=action, outcome=outcome, reason=reason, metadata=metadata)


class DashboardRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, service: DashboardService, **kwargs):
        self.service = service
        super().__init__(*args, directory=str(service.static_dir), **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == '/':
            self.path = '/dashboard_index.html'
            return super().do_GET()
        if parsed.path.startswith('/api/'):
            try:
                return self._handle_api_get(parsed)
            except ValueError as error:
                return self._respond_json(HTTPStatus.BAD_REQUEST, {'error': str(error)})
        return super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith('/api/'):
            try:
                return self._handle_api_post(parsed)
            except ValueError as error:
                return self._respond_json(HTTPStatus.BAD_REQUEST, {'error': str(error)})
        self._respond_json(HTTPStatus.NOT_FOUND, {'error': 'Unknown endpoint.'})

    def end_headers(self) -> None:
        for key, value in SECURITY_HEADERS.items():
            self.send_header(key, value)
        super().end_headers()

    def _handle_api_get(self, parsed) -> None:
        params = parse_qs(parsed.query)
        limit = self._parse_limit(params.get('limit', ['200'])[0])
        status = params.get('status', [None])[0]

        if parsed.path == '/api/dashboard':
            return self._require_and_run('dashboard.read', lambda profile: self._respond_json(HTTPStatus.OK, self.service.dashboard(profile)))
        if parsed.path == '/api/health':
            return self._require_and_run('health.read', lambda profile: self._respond_json(HTTPStatus.OK, self.service.health(profile)))
        if parsed.path == '/api/requests':
            return self._require_and_run('requests.read', lambda profile: self._respond_json(HTTPStatus.OK, {'items': self.service.list_requests(limit=limit), 'session': profile.to_public_dict()}))
        if parsed.path == '/api/overrides':
            return self._require_and_run('overrides.read', lambda profile: self._respond_json(HTTPStatus.OK, {'items': self.service.list_overrides(status=status, limit=limit), 'session': profile.to_public_dict()}))
        if parsed.path == '/api/locks':
            return self._require_and_run('locks.read', lambda profile: self._respond_json(HTTPStatus.OK, {'items': self.service.list_locks(status=status, limit=limit), 'session': profile.to_public_dict()}))
        if parsed.path == '/api/audit':
            return self._require_and_run('audit.read', lambda profile: self._respond_json(HTTPStatus.OK, {'items': self.service.list_audit(limit=limit), 'session': profile.to_public_dict()}))
        if parsed.path == '/api/audit/integrity':
            return self._require_and_run('audit.read', lambda profile: self._respond_json(HTTPStatus.OK, {'integrity': self.service.audit_integrity(), 'session': profile.to_public_dict()}))
        if parsed.path == '/api/retention':
            return self._require_and_run('health.read', lambda profile: self._respond_json(HTTPStatus.OK, {**self.service.retention(), 'session': profile.to_public_dict()}))
        if parsed.path == '/api/operations/backups':
            return self._require_and_run('health.read', lambda profile: self._respond_json(HTTPStatus.OK, {'item': self.service.operations(limit=limit), 'session': profile.to_public_dict()}))
        if parsed.path == '/api/go-live-readiness':
            return self._require_and_run('health.read', lambda profile: self._respond_json(HTTPStatus.OK, {'item': self.service.go_live_readiness(), 'session': profile.to_public_dict()}))
        if parsed.path == '/api/owner-registration':
            return self._require_and_run('health.read', lambda profile: self._respond_json(HTTPStatus.OK, {'item': self.service.owner_registration(), 'session': profile.to_public_dict()}))
        if parsed.path == '/api/sessions':
            return self._require_and_run('sessions.read', lambda profile: self._respond_json(HTTPStatus.OK, {'items': self.service.list_sessions(status=status, limit=limit), 'session': profile.to_public_dict()}))
        if parsed.path == '/api/roles':
            return self._require_and_run('roles.read', lambda profile: self._respond_json(HTTPStatus.OK, {'items': self.service.list_roles(), 'session': profile.to_public_dict()}))
        if parsed.path == '/api/compliance':
            return self._require_and_run('compliance.read', lambda profile: self._respond_json(HTTPStatus.OK, {'item': self.service.compliance(), 'session': profile.to_public_dict()}))
        if parsed.path == '/api/evidence':
            return self._require_and_run('evidence.read', lambda profile: self._respond_json(HTTPStatus.OK, {'item': self.service.evidence(limit=limit), 'session': profile.to_public_dict()}))
        if parsed.path == '/api/integrations':
            return self._require_and_run('integration.read', lambda profile: self._respond_json(HTTPStatus.OK, {'item': self.service.integrations(limit=limit), 'session': profile.to_public_dict()}))
        if parsed.path == '/api/model-providers':
            return self._require_and_run('integration.read', lambda profile: self._respond_json(HTTPStatus.OK, {'item': self.service.model_providers(), 'session': profile.to_public_dict()}))
        if parsed.path == '/api/human-ask':
            return self._require_and_run('human_ask.read', lambda profile: self._respond_json(HTTPStatus.OK, {'item': self.service.human_ask_snapshot(limit=limit), 'session': profile.to_public_dict()}))
        if parsed.path == '/api/human-ask/sessions':
            return self._require_and_run('human_ask.read', lambda profile: self._respond_json(HTTPStatus.OK, {'items': self.service.list_human_ask_sessions(status=status, limit=limit), 'session': profile.to_public_dict()}))
        if parsed.path == '/api/human-ask/callable-directory':
            return self._require_and_run('human_ask.read', lambda profile: self._respond_json(HTTPStatus.OK, {'item': self.service.callable_directory(limit=limit), 'session': profile.to_public_dict()}))
        if parsed.path == '/api/role-private-studio':
            return self._require_and_run('studio.read', lambda profile: self._respond_json(HTTPStatus.OK, {'item': self.service.studio_snapshot(limit=limit), 'session': profile.to_public_dict()}))
        if parsed.path == '/api/role-private-studio/requests':
            return self._require_and_run('studio.read', lambda profile: self._respond_json(HTTPStatus.OK, {'items': self.service.list_studio_requests(status=status, limit=limit), 'session': profile.to_public_dict()}))
        if parsed.path == '/api/session':
            return self._require_and_run('dashboard.read', lambda profile: self._respond_json(HTTPStatus.OK, {'session': profile.to_public_dict(), 'available_profiles': self.service.access_control.list_public_profiles()}))

        parts = [part for part in parsed.path.split('/') if part]
        if len(parts) == 4 and parts[0] == 'api' and parts[1] == 'role-private-studio' and parts[2] == 'requests':
            request_id = unquote(parts[3])
            return self._require_and_run('studio.read', lambda profile: self._respond_json(HTTPStatus.OK, {'item': self.service.get_studio_request(request_id), 'session': profile.to_public_dict()}))
        if len(parts) == 4 and parts[0] == 'api' and parts[1] == 'human-ask' and parts[2] == 'sessions':
            session_id = unquote(parts[3])
            return self._require_and_run('human_ask.read', lambda profile: self._respond_json(HTTPStatus.OK, {'item': self.service.get_human_ask_session(session_id), 'session': profile.to_public_dict()}))

        self._respond_json(HTTPStatus.NOT_FOUND, {'error': 'Unknown API endpoint.'})

    def _handle_api_post(self, parsed) -> None:
        payload = self._read_json_body()
        if parsed.path == '/api/session/login':
            auth_result, session_payload = self.service.login_session(self.headers)
            if not auth_result.authenticated or session_payload is None:
                self.service.record_security_event(action='security_session_issue_denied', outcome='denied', reason=f'Session issuance denied: {auth_result.reason}.', metadata={'path': self.path, 'method': self.command, 'profile_id': auth_result.profile_id, 'auth_method': auth_result.auth_method})
                return self._respond_json(HTTPStatus.UNAUTHORIZED, {'error': 'Unauthorized', 'reason': auth_result.reason})
            self.service.record_security_event(action='security_session_issued', outcome='issued', reason=f'Session issued for profile {auth_result.profile_id}.', metadata={'profile_id': auth_result.profile_id, 'auth_method': auth_result.auth_method, 'session_id': auth_result.session_id})
            return self._respond_json(HTTPStatus.OK, session_payload)
        if parsed.path == '/api/session/logout':
            result = self.service.logout_session(self.headers)
            if not result.get('success'):
                self.service.record_security_event(action='security_session_revoke_denied', outcome='denied', reason=f"Session revoke denied: {result.get('reason', 'unknown')}", metadata={'path': self.path, 'method': self.command})
                return self._respond_json(HTTPStatus.UNAUTHORIZED, {'error': 'Unauthorized', 'reason': result.get('reason', 'unknown_session')})
            self.service.record_security_event(action='security_session_revoked', outcome='revoked', reason='Session revoked from private server API.', metadata=result)
            return self._respond_json(HTTPStatus.OK, result)
        if parsed.path == '/api/request':
            return self._require_and_run('request.create', lambda profile: self._respond_json(HTTPStatus.OK, self.service.create_request(payload, profile)))
        if parsed.path == '/api/retention/enforce':
            return self._require_and_run('retention.manage', lambda profile: self._respond_json(HTTPStatus.OK, {'result': self.service.enforce_retention(payload), 'session': profile.to_public_dict()}))
        if parsed.path == '/api/audit/reseal':
            return self._require_and_run('audit.manage', lambda profile: self._respond_json(HTTPStatus.OK, {'result': self.service.reseal_audit(profile), 'session': profile.to_public_dict()}))
        if parsed.path == '/api/operations/backup':
            return self._require_and_run('ops.manage', lambda profile: self._respond_json(HTTPStatus.OK, {'result': self.service.create_backup(profile), 'session': profile.to_public_dict()}))
        if parsed.path == '/api/operations/usability-proof':
            return self._require_and_run('ops.manage', lambda profile: self._respond_json(HTTPStatus.OK, {'result': self.service.create_usability_proof_bundle(profile, payload), 'session': profile.to_public_dict()}))
        if parsed.path == '/api/evidence/export':
            return self._require_and_run('evidence.export', lambda profile: self._respond_json(HTTPStatus.OK, {'result': self.service.create_evidence_export(profile), 'session': profile.to_public_dict()}))
        if parsed.path == '/api/integrations/test-event':
            return self._require_and_run('integration.manage', lambda profile: self._respond_json(HTTPStatus.OK, {'result': self.service.trigger_integration_test_event(profile, payload), 'session': profile.to_public_dict()}))
        if parsed.path == '/api/model-providers/probe':
            return self._require_and_run('integration.manage', lambda profile: self._respond_json(HTTPStatus.OK, {'result': self.service.probe_model_providers(profile, payload), 'session': profile.to_public_dict()}))
        if parsed.path == '/api/human-ask/sessions':
            return self._require_and_run('human_ask.create', lambda profile: self._respond_json(HTTPStatus.OK, {'item': self.service.create_human_ask_session(payload, profile), 'session': profile.to_public_dict()}))
        if parsed.path == '/api/role-private-studio/requests':
            return self._require_and_run('studio.create', lambda profile: self._respond_json(HTTPStatus.OK, {'item': self.service.create_studio_request(payload, profile), 'session': profile.to_public_dict()}))
        if parsed.path == '/api/owner-registration':
            return self._require_owner_run(lambda profile: self._respond_json(HTTPStatus.OK, {'item': self.service.update_owner_registration(payload, profile), 'session': profile.to_public_dict()}))

        parts = [part for part in parsed.path.split('/') if part]
        if len(parts) == 4 and parts[0] == 'api' and parts[1] == 'sessions' and parts[3] == 'revoke':
            session_id = unquote(parts[2])
            return self._require_and_run('session.manage', lambda profile: self._respond_json(HTTPStatus.OK, {'result': self.service.revoke_session(session_id, payload, profile), 'session': profile.to_public_dict()}))
        if len(parts) == 4 and parts[0] == 'api' and parts[1] == 'overrides':
            request_id = unquote(parts[2])
            if parts[3] == 'approve':
                return self._require_and_run('override.review', lambda profile: self._respond_json(HTTPStatus.OK, self.service.approve_override(request_id, payload, profile)))
            if parts[3] == 'veto':
                return self._require_and_run('override.review', lambda profile: self._respond_json(HTTPStatus.OK, self.service.veto_override(request_id, payload, profile)))
        if len(parts) == 5 and parts[0] == 'api' and parts[1] == 'role-private-studio' and parts[2] == 'requests':
            request_id = unquote(parts[3])
            action = parts[4]
            if action == 'update':
                return self._require_and_run('studio.create', lambda profile: self._respond_json(HTTPStatus.OK, {'item': self.service.update_studio_request(request_id, payload, profile), 'session': profile.to_public_dict()}))
            if action == 'ptag':
                return self._require_and_run('studio.create', lambda profile: self._respond_json(HTTPStatus.OK, {'item': self.service.update_studio_request_ptag(request_id, payload, profile), 'session': profile.to_public_dict()}))
            if action == 'ptag-reset':
                return self._require_and_run('studio.create', lambda profile: self._respond_json(HTTPStatus.OK, {'item': self.service.reset_studio_request_ptag(request_id, profile), 'session': profile.to_public_dict()}))
            if action == 'refresh':
                return self._require_and_run('studio.create', lambda profile: self._respond_json(HTTPStatus.OK, {'item': self.service.refresh_studio_request(request_id), 'session': profile.to_public_dict()}))
            if action == 'restore-revision':
                return self._require_and_run('studio.create', lambda profile: self._respond_json(HTTPStatus.OK, {'item': self.service.restore_studio_request_revision(request_id, payload, profile), 'session': profile.to_public_dict()}))
            if action == 'review':
                return self._require_and_run('studio.review', lambda profile: self._respond_json(HTTPStatus.OK, {'item': self.service.review_studio_request(request_id, payload, profile), 'session': profile.to_public_dict()}))
            if action == 'publish':
                return self._require_and_run('studio.publish', lambda profile: self._respond_json(HTTPStatus.OK, {'item': self.service.publish_studio_request(request_id, payload, profile), 'session': profile.to_public_dict()}))
            if action == 'human-ask-record':
                return self._require_and_run('human_ask.create', lambda profile: self._respond_json(HTTPStatus.OK, {'item': self.service.create_human_ask_studio_record(request_id, payload, profile), 'session': profile.to_public_dict()}))

        self._respond_json(HTTPStatus.NOT_FOUND, {'error': 'Unknown API endpoint.'})

    def _require_and_run(self, permission: str, callback) -> None:
        auth_result = self.service.authenticate_result(self.headers)
        if not auth_result.authenticated or auth_result.profile is None:
            self.service.record_security_event(action='security_auth_denied', outcome='denied', reason=f'Authentication denied: {auth_result.reason}.', metadata={'permission': permission, 'path': self.path, 'method': self.command, 'token_present': auth_result.token_present, 'profile_id': auth_result.profile_id, 'auth_method': auth_result.auth_method, 'session_id': auth_result.session_id})
            return self._respond_json(HTTPStatus.UNAUTHORIZED, {'error': 'Unauthorized', 'reason': auth_result.reason})
        profile = auth_result.profile
        if not self.service.access_control.require(profile, permission):
            self.service.record_security_event(action='security_forbidden', outcome='forbidden', reason=f'Access forbidden for permission {permission}.', metadata={'permission': permission, 'path': self.path, 'method': self.command, 'profile_id': profile.profile_id, 'role_name': profile.role_name, 'auth_method': auth_result.auth_method, 'session_id': auth_result.session_id})
            return self._respond_json(HTTPStatus.FORBIDDEN, {'error': f'Forbidden: missing {permission}', 'session': profile.to_public_dict()})
        callback(profile)

    def _require_owner_run(self, callback) -> None:
        auth_result = self.service.authenticate_result(self.headers)
        if not auth_result.authenticated or auth_result.profile is None:
            self.service.record_security_event(action='security_auth_denied', outcome='denied', reason=f'Authentication denied: {auth_result.reason}.', metadata={'permission': 'owner', 'path': self.path, 'method': self.command, 'token_present': auth_result.token_present, 'profile_id': auth_result.profile_id, 'auth_method': auth_result.auth_method, 'session_id': auth_result.session_id})
            return self._respond_json(HTTPStatus.UNAUTHORIZED, {'error': 'Unauthorized', 'reason': auth_result.reason})
        profile = auth_result.profile
        if profile.role_name != 'owner':
            self.service.record_security_event(action='security_forbidden', outcome='forbidden', reason='Owner-only endpoint denied.', metadata={'permission': 'owner', 'path': self.path, 'method': self.command, 'profile_id': profile.profile_id, 'role_name': profile.role_name, 'auth_method': auth_result.auth_method, 'session_id': auth_result.session_id})
            return self._respond_json(HTTPStatus.FORBIDDEN, {'error': 'Forbidden: owner access required', 'session': profile.to_public_dict()})
        callback(profile)

    def _read_json_body(self) -> dict[str, object]:
        raw_length = self.headers.get('Content-Length', '0')
        try:
            length = int(raw_length)
        except ValueError as error:
            raise ValueError('Content-Length must be a valid integer.') from error
        if length <= 0:
            return {}
        if length > 1024 * 1024:
            raise ValueError('Request body exceeds the 1MB safety limit.')
        raw = self.rfile.read(length).decode('utf-8')
        if not raw.strip():
            return {}
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as error:
            raise ValueError(f'Invalid JSON body: {error.msg}.') from error
        if not isinstance(payload, dict):
            raise ValueError('JSON body must be an object.')
        return payload

    def _parse_limit(self, raw_limit: str, *, default: int = 200, maximum: int = 500) -> int:
        raw = str(raw_limit or '').strip()
        if not raw:
            return default
        try:
            value = int(raw)
        except ValueError as error:
            raise ValueError('limit must be a valid integer.') from error
        if value <= 0:
            raise ValueError('limit must be greater than zero.')
        return min(value, maximum)

    def _respond_json(self, status: HTTPStatus, payload: dict[str, object] | list[object]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def create_handler(service: DashboardService):
    def handler(*args, **kwargs):
        return DashboardRequestHandler(*args, service=service, **kwargs)
    return handler


def create_server(config: AppConfig | None = None, host: str | None = None, port: int | None = None) -> ThreadingHTTPServer:
    app_config = config or AppConfig()
    validate_startup_or_raise(app_config)
    service = DashboardService(app_config)
    server = ThreadingHTTPServer((host or app_config.server_host, port if port is not None else app_config.server_port), create_handler(service))
    server.service = service
    return server


def run_server(config: AppConfig | None = None, host: str | None = None, port: int | None = None) -> None:
    server = create_server(config=config, host=host, port=port)
    resolved_host, resolved_port = server.server_address
    print(f'Dashboard available at http://{resolved_host}:{resolved_port}/dashboard_index.html')
    print('Available access profiles:')
    for profile in server.service.access_control.list_public_profiles():
        print(f"- {profile['display_name']} [{profile['role_name']}] ({profile['status']})")
    print(f'Deployment ready: {server.service.deployment_report.ready}')
    server.serve_forever()


def main() -> None:
    parser = ArgumentParser(description='Serve the SA-NOM AI Governance Suite dashboard and private API.')
    parser.add_argument('--host', default=None)
    parser.add_argument('--port', type=int, default=None)
    parser.add_argument('--token', default=None)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    config = AppConfig()
    if args.token is not None:
        config.api_token = args.token
    report = validate_startup_or_raise(config)
    if args.check_only:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return
    run_server(config=config, host=args.host, port=args.port)


if __name__ == '__main__':
    main()
