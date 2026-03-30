import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from sa_nom_governance.compliance.trusted_registry import write_trusted_registry_files
from sa_nom_governance.guards.bootstrap_access_profiles import build_profiles
from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.utils.owner_registration import (
    build_owner_registration,
    load_owner_registration,
    normalize_registration_code,
    write_owner_registration,
)

BUNDLED_RESOURCES_DIR = Path(__file__).resolve().parents[2] / 'resources'


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, object] | list[object]:
    return json.loads(path.read_text(encoding='utf-8-sig'))


def dedupe_actions(actions: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for action in actions:
        text = str(action).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        unique.append(text)
    return unique


def ensure_public_resources(config: AppConfig, *, force: bool = False) -> dict[str, object]:
    source_root = BUNDLED_RESOURCES_DIR.resolve()
    target_root = config.resources_dir.resolve()
    if source_root == target_root:
        return {
            'status': 'ok',
            'action': 'bundled',
            'resources_dir': str(target_root),
            'copied_files': 0,
            'files': [],
        }

    copied: list[str] = []
    for source_path in sorted(path for path in source_root.rglob('*') if path.is_file()):
        relative_path = source_path.relative_to(source_root)
        target_path = target_root / relative_path
        if force or not target_path.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)
            copied.append(relative_path.as_posix())

    return {
        'status': 'ok',
        'action': 'seeded' if copied else 'existing',
        'resources_dir': str(target_root),
        'copied_files': len(copied),
        'files': copied,
    }


def ensure_owner_registration(config: AppConfig, *, registration_code: str, force: bool = False) -> dict[str, object]:
    path = config.owner_registration_path
    if path is None:
        raise ValueError('Owner registration path is not configured.')

    existed = path.exists()
    if existed and not force:
        registration = load_owner_registration(path)
        action = 'existing'
    else:
        registration = build_owner_registration({
            'registration_code': normalize_registration_code(registration_code),
            'deployment_mode': 'private',
        })
        write_owner_registration(path, registration, force=force)
        action = 'updated' if existed else 'created'

    if registration is None:
        raise ValueError(f'Owner registration could not be loaded from {path}.')
    config.reload_owner_registration()
    return {
        'status': 'ok',
        'action': action,
        'path': str(path),
        'organization_name': registration.organization_name,
        'organization_id': registration.organization_id,
        'executive_owner_id': registration.executive_owner_id,
        'trusted_registry_signed_by': registration.trusted_registry_signed_by,
    }

def ensure_access_profiles(
    config: AppConfig,
    *,
    days_valid: int,
    rotate_days: int,
    force: bool = False,
) -> dict[str, object]:
    access_profiles_path = config.access_profiles_path
    if access_profiles_path is None:
        raise ValueError('Access profiles path is not configured.')

    tokens_path = config.runtime_dir / 'generated_access_tokens.json'
    existed = access_profiles_path.exists()
    if existed and not force:
        profiles_payload = load_json(access_profiles_path)
        profiles_total = len(profiles_payload) if isinstance(profiles_payload, list) else 0
        action = 'existing'
    else:
        profiles_payload, token_bundle = build_profiles(days_valid=days_valid, rotate_days=rotate_days)
        access_profiles_path.write_text(json.dumps(profiles_payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        tokens_path.write_text(json.dumps(token_bundle, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        profiles_total = len(profiles_payload)
        action = 'updated' if existed else 'created'

    return {
        'status': 'ok',
        'action': action,
        'path': str(access_profiles_path),
        'tokens_output_path': str(tokens_path),
        'profiles_total': profiles_total,
        'token_export_status': 'present' if tokens_path.exists() else 'missing',
    }


def registry_refresh_reasons(
    config: AppConfig,
    *,
    role_ids: list[str],
    force: bool,
    resources_action: str,
    owner_action: str,
) -> list[str]:
    reasons: list[str] = []
    manifest_path = config.trusted_registry_manifest_path
    cache_path = config.trusted_registry_cache_path

    if force:
        reasons.append('forced refresh requested')
    if resources_action == 'seeded':
        reasons.append('public resources were seeded')
    if manifest_path is None or not manifest_path.exists():
        reasons.append('trusted registry manifest is missing')
    if cache_path is None or not cache_path.exists():
        reasons.append('trusted registry cache is missing')
    if reasons or manifest_path is None or not manifest_path.exists():
        return reasons

    manifest = load_json(manifest_path)
    manifest_roles = manifest.get('roles', {}) if isinstance(manifest.get('roles', {}), dict) else {}
    manifest_role_ids = sorted(str(role_id) for role_id in manifest_roles.keys())
    if manifest_role_ids != role_ids:
        reasons.append('trusted registry role set is out of sync with bundled PTAG packs')
    return reasons


def ensure_trusted_registry(
    config: AppConfig,
    *,
    force: bool = False,
    resources_action: str,
    owner_action: str,
) -> dict[str, object]:
    manifest_path = config.trusted_registry_manifest_path
    cache_path = config.trusted_registry_cache_path
    if manifest_path is None or cache_path is None:
        raise ValueError('Trusted registry paths are not configured.')

    role_ids = sorted(path.stem for path in config.roles_dir.glob('*.ptn') if path.stem.lower() != 'core_terms')
    reasons = registry_refresh_reasons(
        config,
        role_ids=role_ids,
        force=force,
        resources_action=resources_action,
        owner_action=owner_action,
    )

    if reasons:
        manifest, _cache = write_trusted_registry_files(
            roles_dir=config.roles_dir,
            manifest_path=manifest_path,
            cache_path=cache_path,
            role_ids=role_ids,
            signing_key=config.trusted_registry_signing_key or '',
            key_id=config.trusted_registry_key_id,
            signed_by=config.trusted_registry_signed_by or config.executive_owner_id(),
        )
        action = 'refreshed'
        role_total = len(manifest.get('roles', {}))
    else:
        manifest = load_json(manifest_path)
        role_total = len(manifest.get('roles', {})) if isinstance(manifest.get('roles', {}), dict) else 0
        action = 'existing'

    return {
        'status': 'ok',
        'action': action,
        'reasons': reasons,
        'manifest_path': str(manifest_path),
        'cache_path': str(cache_path),
        'roles_total': role_total,
        'role_ids': role_ids,
    }

from sa_nom_governance.deployment.deployment_profile import build_deployment_report
from sa_nom_governance.deployment.private_server_smoke_test import run_smoke
from sa_nom_governance.deployment.provider_demo_flow import build_provider_demo_flow


def build_next_actions(report: dict[str, object]) -> list[str]:
    actions: list[str] = []
    startup = report.get('startup', {})
    provider = report.get('provider', {})
    runtime_smoke = report.get('runtime_smoke', {})

    if isinstance(startup, dict) and not startup.get('ready', False):
        failing_checks = [
            str(check.get('message', 'Startup validation failed.'))
            for check in startup.get('checks', [])
            if isinstance(check, dict) and check.get('status') == 'error'
        ]
        actions.extend(failing_checks[:3])
        actions.append('Fix the startup errors above, then rerun `python scripts/guided_smoke_test.py --registration-code DEMO-ORG`.')

    if isinstance(provider, dict):
        recommended_provider = str(provider.get('recommended_provider') or '').strip()
        if recommended_provider == 'ollama':
            actions.append('For the default private demo lane, copy `examples/.env.ollama.example`, set `SANOM_OLLAMA_MODEL`, then run `python scripts/provider_demo_flow.py --provider ollama --probe` when Ollama is available.')
            actions.append('OpenAI and Claude remain optional hosted evaluation lanes via `examples/.env.openai.example` and `examples/.env.claude.example`.')
        elif recommended_provider:
            actions.append(f'Set `SANOM_MODEL_PROVIDER_DEFAULT={recommended_provider}` before running a live provider probe.')

    if isinstance(runtime_smoke, dict) and runtime_smoke.get('status') == 'skipped' and runtime_smoke.get('reason'):
        actions.append(str(runtime_smoke['reason']))
    elif isinstance(runtime_smoke, dict) and runtime_smoke.get('passed'):
        actions.append('Start the local runtime with `python scripts/run_private_server.py --host 127.0.0.1 --port 8080` when you are ready to inspect the dashboard or API.')

    return dedupe_actions(actions)


def guided_smoke_passed(report: dict[str, object]) -> bool:
    startup = report.get('startup', {})
    runtime_smoke = report.get('runtime_smoke', {})
    provider = report.get('provider', {})
    if not isinstance(startup, dict) or not startup.get('ready', False):
        return False
    if not isinstance(runtime_smoke, dict) or not runtime_smoke.get('passed', False):
        return False
    if report.get('provider_probe_requested'):
        probe = provider.get('probe') if isinstance(provider, dict) else None
        return isinstance(probe, dict) and probe.get('status') == 'ok'
    return True


def build_guided_smoke_test(
    config: AppConfig | None = None,
    *,
    registration_code: str = 'DEMO-ORG',
    provider_id: str | None = None,
    probe_provider: bool = False,
    skip_runtime_smoke: bool = False,
    force_seed_resources: bool = False,
    force_owner: bool = False,
    force_access_profiles: bool = False,
    force_refresh_registry: bool = False,
    days_valid: int = 365,
    rotate_days: int = 180,
) -> dict[str, object]:
    runtime_config = config or AppConfig()
    resources_step = ensure_public_resources(runtime_config, force=force_seed_resources)
    owner_step = ensure_owner_registration(runtime_config, registration_code=registration_code, force=force_owner)
    access_step = ensure_access_profiles(runtime_config, days_valid=days_valid, rotate_days=rotate_days, force=force_access_profiles)
    registry_step = ensure_trusted_registry(
        runtime_config,
        force=force_refresh_registry,
        resources_action=str(resources_step.get('action', '')),
        owner_action=str(owner_step.get('action', '')),
    )
    startup_report = build_deployment_report(runtime_config).to_dict()
    provider_report = build_provider_demo_flow(runtime_config, provider_id=provider_id, probe=probe_provider)

    if skip_runtime_smoke:
        runtime_smoke: dict[str, object] = {'status': 'skipped', 'passed': startup_report.get('ready', False), 'reason': 'Runtime smoke test was skipped by request.'}
    elif not startup_report.get('ready', False):
        runtime_smoke = {'status': 'skipped', 'passed': False, 'reason': 'Startup readiness is not ready, so the runtime smoke test was not attempted.'}
    else:
        smoke_result = run_smoke(runtime_config)
        runtime_smoke = {'status': 'passed' if smoke_result.get('passed', False) else 'failed', **smoke_result}

    report = {
        'generated_at': utc_now(),
        'registration_code': normalize_registration_code(registration_code),
        'provider_probe_requested': probe_provider,
        'provider_requested': provider_id,
        'steps': {
            'public_resources': resources_step,
            'owner_registration': owner_step,
            'access_profiles': access_step,
            'trusted_registry': registry_step,
        },
        'startup': startup_report,
        'provider': provider_report,
        'runtime_smoke': runtime_smoke,
        'artifacts': {
            'owner_registration': str(runtime_config.owner_registration_path) if runtime_config.owner_registration_path else None,
            'access_profiles': str(runtime_config.access_profiles_path) if runtime_config.access_profiles_path else None,
            'access_tokens': str(runtime_config.runtime_dir / 'generated_access_tokens.json'),
            'trusted_registry_manifest': str(runtime_config.trusted_registry_manifest_path) if runtime_config.trusted_registry_manifest_path else None,
            'trusted_registry_cache': str(runtime_config.trusted_registry_cache_path) if runtime_config.trusted_registry_cache_path else None,
            'runtime_smoke_report': str(runtime_config.startup_smoke_report_path) if runtime_config.startup_smoke_report_path else None,
        },
    }
    report['next_actions'] = build_next_actions(report)
    report['passed'] = guided_smoke_passed(report)
    return report


def main() -> None:
    config = AppConfig()
    parser = argparse.ArgumentParser(description='Prepare a first-run guided smoke-test report for the SA-NOM community baseline.')
    parser.add_argument('--registration-code', default='DEMO-ORG')
    parser.add_argument('--provider', default=None, help='Optional provider lane to target explicitly: ollama, openai, or anthropic.')
    parser.add_argument('--probe', action='store_true', help='Probe the selected provider lane after building the guided smoke-test report.')
    parser.add_argument('--skip-runtime-smoke', action='store_true', help='Skip the end-to-end runtime smoke step.')
    parser.add_argument('--days-valid', type=int, default=365)
    parser.add_argument('--rotate-days', type=int, default=180)
    parser.add_argument('--force-seed-resources', action='store_true')
    parser.add_argument('--force-owner', action='store_true')
    parser.add_argument('--force-access-profiles', action='store_true')
    parser.add_argument('--force-refresh-registry', action='store_true')
    parser.add_argument('--output', default=str(config.review_dir / 'guided_smoke_test.json'))
    args = parser.parse_args()

    report = build_guided_smoke_test(
        config=config,
        registration_code=args.registration_code,
        provider_id=args.provider,
        probe_provider=args.probe,
        skip_runtime_smoke=args.skip_runtime_smoke,
        force_seed_resources=args.force_seed_resources,
        force_owner=args.force_owner,
        force_access_profiles=args.force_access_profiles,
        force_refresh_registry=args.force_refresh_registry,
        days_valid=args.days_valid,
        rotate_days=args.rotate_days,
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report['artifacts']['guided_report'] = str(output_path)
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    output_path.write_text(encoded + '\n', encoding='utf-8')
    print(encoded)
    if not report['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
