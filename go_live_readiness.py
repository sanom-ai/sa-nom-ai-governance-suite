import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from api_engine import EngineApplication
from config import AppConfig
from deployment_profile import build_deployment_report


def build_go_live_readiness(config: AppConfig, app: "EngineApplication" | None = None) -> dict[str, Any]:
    if app is None:
        from api_engine import build_engine_app
        runtime_app = build_engine_app(config)
    else:
        runtime_app = app
    deployment_report = build_deployment_report(config).to_dict()
    app_health = runtime_app.health()
    access_health = runtime_app.access_control.health()
    smoke_report = load_smoke_report(config.startup_smoke_report_path)
    review_pack = load_review_pack_state(config)
    studio_snapshot = runtime_app.studio_snapshot(limit=100) if hasattr(runtime_app, 'studio_snapshot') else {'summary': {}}
    studio_summary = studio_snapshot.get('summary', {}) if isinstance(studio_snapshot, dict) else {}
    deployment_checks = {
        str(item.get('code', '')): item
        for item in deployment_report.get('checks', [])
        if isinstance(item, dict)
    }
    privileged_check = (
        deployment_checks.get('ACCESS_PROFILES_PRIVILEGED_PERMISSION_COVERAGE')
        or deployment_checks.get('ACCESS_PROFILES_PRIVILEGED_PERMISSION_GAP')
        or deployment_checks.get('ACCESS_PROFILES_MISSING')
        or {}
    )
    privileged_operations = {
        'status': str(privileged_check.get('status', 'unknown')),
        'message': str(privileged_check.get('message', 'Delegated privileged-operation coverage is unavailable.')),
        'delegated': str(privileged_check.get('status', '')) == 'ok',
    }
    studio_structural = {
        'ready_total': int(studio_summary.get('ready_to_publish_total', 0) or 0),
        'guarded_total': int(studio_summary.get('structural_guarded_total', 0) or 0),
        'blocked_total': int(studio_summary.get('structural_blocked_total', 0) or 0),
        'publication_blocked_total': int(studio_summary.get('publication_blocked_total', 0) or 0),
        'requests_total': int(studio_summary.get('requests_total', 0) or 0),
    }
    if studio_structural['blocked_total']:
        studio_structural['status'] = 'blocked'
    elif studio_structural['guarded_total']:
        studio_structural['status'] = 'guarded'
    else:
        studio_structural['status'] = 'clear'

    audit_status = str(app_health.get('audit_integrity', {}).get('status', 'unknown'))
    gates = {
        'deployment_ready': bool(deployment_report.get('ready', False)),
        'trusted_registry_verified': bool(app_health.get('trusted_registry', {}).get('signature_trusted', False)),
        'audit_integrity_verified': audit_status in {'verified', 'legacy_verified'},
        'plain_file_tokens_zero': int(access_health.get('plain_file_tokens', access_health.get('plain_tokens', 0))) == 0,
        'startup_smoke_passed': bool(smoke_report.get('passed', False)),
        'review_pack_present': bool(review_pack.get('present', False)),
        'delegated_privileged_operations': privileged_operations['delegated'],
        'studio_structural_clear': studio_structural['status'] == 'clear',
    }

    blockers: list[str] = []
    advisories: list[str] = []
    if not gates['deployment_ready']:
        blockers.append('Deployment validation is not ready.')
    if not gates['trusted_registry_verified']:
        blockers.append('Trusted registry signature is not verified.')
    if not gates['audit_integrity_verified']:
        blockers.append('Audit integrity is not verified.')
    elif audit_status == 'legacy_verified':
        advisories.append('Audit log contains legacy unsealed entries but the chain is intact.')
    if not gates['plain_file_tokens_zero']:
        blockers.append('Plain access-profile tokens are still present.')
    if not gates['startup_smoke_passed']:
        blockers.append('Startup smoke verification has not passed yet.')
    if not gates['review_pack_present']:
        blockers.append('Review pack manifest is missing.')
    if not privileged_operations['delegated']:
        if str(privileged_operations['status']) == 'error' or config.environment.lower() == 'production':
            blockers.append(privileged_operations['message'])
        else:
            advisories.append(privileged_operations['message'])
    if studio_structural['blocked_total']:
        advisories.append(
            'Role Private Studio still has structurally blocked drafts: '
            f"{studio_structural['blocked_total']} blocked, {studio_structural['guarded_total']} guarded."
        )
    elif studio_structural['guarded_total']:
        advisories.append(
            'Role Private Studio has guarded drafts waiting on PT-OSS mitigation before publication: '
            f"{studio_structural['guarded_total']} guarded."
        )

    ready = not blockers
    status = 'blocked' if blockers else 'guarded' if advisories else 'ready'
    return {
        'status': status,
        'ready': ready,
        'gates': gates,
        'blockers': blockers,
        'advisories': advisories,
        'privileged_operations': privileged_operations,
        'studio_structural': studio_structural,
        'deployment_report': {
            'ready': deployment_report.get('ready', False),
            'errors': deployment_report.get('errors', 0),
            'warnings': deployment_report.get('warnings', 0),
        },
        'smoke_report': smoke_report,
        'review_pack': review_pack,
    }


def load_smoke_report(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {'present': False, 'passed': False, 'status': 'disabled', 'path': None}
    if not path.exists():
        return {'present': False, 'passed': False, 'status': 'missing', 'path': str(path)}
    try:
        data = json.loads(path.read_text(encoding='utf-8-sig'))
    except Exception as error:
        return {'present': True, 'passed': False, 'status': 'invalid', 'path': str(path), 'error': str(error)}
    return {
        'present': True,
        'passed': bool(data.get('passed', False)),
        'status': 'passed' if data.get('passed', False) else 'failed',
        'path': str(path),
        'generated_at': data.get('generated_at'),
        'errors': data.get('errors', 0),
        'warnings': data.get('warnings', 0),
        'checks_total': len(data.get('checks', [])) if isinstance(data.get('checks', []), list) else 0,
    }


def persist_smoke_report(config: AppConfig, result: dict[str, Any]) -> None:
    path = config.startup_smoke_report_path
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def load_review_pack_state(config: AppConfig) -> dict[str, Any]:
    manifest_path = config.review_dir / 'manifest.json'
    if not manifest_path.exists():
        return {'present': False, 'path': str(manifest_path), 'generated_at': None, 'groups': {}}
    try:
        manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
    except Exception as error:
        return {'present': True, 'path': str(manifest_path), 'generated_at': None, 'groups': {}, 'error': str(error)}
    groups = manifest.get('groups', {}) if isinstance(manifest.get('groups', {}), dict) else {}
    return {
        'present': True,
        'path': str(manifest_path),
        'generated_at': manifest.get('generated_at'),
        'groups': {group: len(items) for group, items in groups.items()},
    }
