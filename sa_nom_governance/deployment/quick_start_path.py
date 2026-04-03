from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path

from sa_nom_governance.deployment.go_live_readiness import load_smoke_report
from sa_nom_governance.deployment.guided_smoke_test import build_guided_smoke_test
from sa_nom_governance.deployment.runtime_performance_baseline import read_runtime_performance_baseline
from sa_nom_governance.utils.config import AppConfig

DEFAULT_PRIVATE_LANE = 'private_local_ollama'


def _build_quick_start_steps(provider_id: str | None, report: dict[str, object]) -> list[dict[str, object]]:
    selected_provider = str(provider_id or report.get('provider', {}).get('selected_provider') or 'ollama')
    env_example = f'examples/.env.{selected_provider}.example' if selected_provider in {'openai', 'anthropic', 'ollama'} else 'examples/.env.ollama.example'
    runtime_smoke = report.get('runtime_smoke', {})
    smoke_status = 'passed' if isinstance(runtime_smoke, dict) and runtime_smoke.get('passed') else str(runtime_smoke.get('status') or 'pending') if isinstance(runtime_smoke, dict) else 'pending'
    return [
        {
            'step': 1,
            'title': 'Choose the default private lane',
            'action': f'Start with {env_example}. Ollama is the recommended default for private local evaluation.',
        },
        {
            'step': 2,
            'title': 'Run the guided bootstrap',
            'action': 'Run `python scripts/quick_start_path.py` to seed resources, owner registration, access profiles, trusted registry, and first-run validation in one path.',
        },
        {
            'step': 3,
            'title': 'Review generated artifacts',
            'action': 'Inspect the generated quick-start report and the runtime artifacts under `_runtime/` before sharing the environment with others.',
        },
        {
            'step': 4,
            'title': 'Start the local runtime',
            'action': 'Run `python scripts/run_private_server.py --host 127.0.0.1 --port 8080` after the quick-start report passes.',
        },
        {
            'step': 5,
            'title': 'Open the dashboard',
            'action': f'Use the dashboard or API after the smoke status is `{smoke_status}` and the runtime is started.',
        },
    ]


def _build_operator_summary(report: dict[str, object]) -> dict[str, object]:
    startup = report.get('startup', {}) if isinstance(report.get('startup'), dict) else {}
    runtime_smoke = report.get('runtime_smoke', {}) if isinstance(report.get('runtime_smoke'), dict) else {}
    provider = report.get('provider', {}) if isinstance(report.get('provider'), dict) else {}
    performance = report.get('performance_baseline', {}) if isinstance(report.get('performance_baseline'), dict) else {}
    performance_summary = performance.get('summary', {}) if isinstance(performance.get('summary', {}), dict) else {}
    ready = bool(report.get('passed'))
    return {
        'status': 'ready' if ready else 'attention_required',
        'startup_ready': bool(startup.get('ready', False)),
        'runtime_smoke_status': runtime_smoke.get('status', 'unknown'),
        'provider_status': provider.get('status', 'unknown'),
        'recommended_provider': provider.get('recommended_provider'),
        'selected_provider': provider.get('selected_provider'),
        'performance_status': performance.get('status', 'unknown'),
        'performance_slowest_metric': performance_summary.get('slowest_metric', 'unknown'),
        'dashboard_snapshot_elapsed_ms': float(performance_summary.get('dashboard_snapshot_elapsed_ms', 0.0) or 0.0),
    }


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_quick_start_doctor(config: AppConfig | None = None) -> dict[str, object]:
    runtime_config = config or AppConfig()

    def add_check(
        checks: list[dict[str, object]],
        *,
        check_id: str,
        severity: str,
        passed: bool,
        message: str,
        path: Path | None = None,
        next_step: str | None = None,
    ) -> None:
        checks.append(
            {
                'check_id': check_id,
                'severity': severity,
                'status': 'pass' if passed else 'fail',
                'message': message,
                'path': str(path) if path is not None else None,
                'next_step': next_step if not passed else None,
            }
        )

    checks: list[dict[str, object]] = []
    smoke_report = load_smoke_report(runtime_config.startup_smoke_report_path)
    owner_path = runtime_config.effective_owner_registration_path()
    access_profiles_path = runtime_config.effective_access_profiles_path()
    trusted_manifest_path = runtime_config.trusted_registry_manifest_path
    usability_proof_path = runtime_config.review_dir / 'usability_proof_bundle.json'
    runtime_performance_path = runtime_config.review_dir / 'runtime_performance_baseline.json'
    performance_report = read_runtime_performance_baseline(config=runtime_config, output_path=runtime_performance_path)
    quick_start_script = runtime_config.base_dir / 'scripts' / 'quick_start_path.py'
    run_server_script = runtime_config.base_dir / 'scripts' / 'run_private_server.py'
    demo_script = runtime_config.base_dir / 'scripts' / 'nontechnical_demo_path.py'

    add_check(
        checks,
        check_id='api_token_configured',
        severity='required',
        passed=bool(runtime_config.api_token),
        message='API token is configured for runtime access.',
        next_step='Set SANOM_API_TOKEN or use the development default token.',
    )
    add_check(
        checks,
        check_id='owner_registration_present',
        severity='required',
        passed=owner_path is not None and owner_path.exists(),
        message='Owner registration is present.',
        path=owner_path,
        next_step='Run `python scripts/register_owner.py --registration-code <ORG-CODE>`.',
    )
    add_check(
        checks,
        check_id='access_profiles_present',
        severity='required',
        passed=access_profiles_path is not None and access_profiles_path.exists(),
        message='Access profiles file is present.',
        path=access_profiles_path,
        next_step='Run `python scripts/bootstrap_access_profiles.py --force` to create profiles.',
    )
    add_check(
        checks,
        check_id='trusted_registry_manifest_present',
        severity='required',
        passed=trusted_manifest_path is not None and trusted_manifest_path.exists(),
        message='Trusted registry manifest is present.',
        path=trusted_manifest_path,
        next_step='Run `python scripts/trusted_registry_refresh.py --force`.',
    )
    add_check(
        checks,
        check_id='runtime_smoke_passed',
        severity='required',
        passed=bool(smoke_report.get('present')) and str(smoke_report.get('status')) == 'passed',
        message='Startup smoke report is present and passed.',
        path=runtime_config.startup_smoke_report_path,
        next_step='Run `python scripts/guided_smoke_test.py` and ensure smoke status is passed.',
    )

    add_check(
        checks,
        check_id='quick_start_script_present',
        severity='advisory',
        passed=quick_start_script.exists(),
        message='Quick-start script entrypoint is available.',
        path=quick_start_script,
        next_step='Ensure `scripts/quick_start_path.py` exists in this workspace.',
    )
    add_check(
        checks,
        check_id='run_server_script_present',
        severity='advisory',
        passed=run_server_script.exists(),
        message='Runtime server startup script is available.',
        path=run_server_script,
        next_step='Ensure `scripts/run_private_server.py` exists in this workspace.',
    )
    add_check(
        checks,
        check_id='nontechnical_demo_script_present',
        severity='advisory',
        passed=demo_script.exists(),
        message='Non-technical demo script is available.',
        path=demo_script,
        next_step='Add `scripts/nontechnical_demo_path.py` for guided local demo runs.',
    )
    add_check(
        checks,
        check_id='usability_proof_bundle_present',
        severity='advisory',
        passed=usability_proof_path.exists(),
        message='Usability proof bundle artifact is available.',
        path=usability_proof_path,
        next_step='Run `python scripts/usability_proof_bundle.py` to generate the artifact.',
    )
    add_check(
        checks,
        check_id='runtime_performance_baseline_present',
        severity='advisory',
        passed=bool(performance_report.get('available', False)),
        message='Runtime performance baseline artifact is available.',
        path=runtime_performance_path,
        next_step='Run `python scripts/runtime_performance_baseline.py` or rerun `python scripts/guided_smoke_test.py` to capture the baseline.',
    )
    add_check(
        checks,
        check_id='runtime_performance_posture_recorded',
        severity='advisory',
        passed=str(performance_report.get('status', 'missing')) in {'ready', 'monitoring'},
        message='Runtime performance posture is captured without critical or failed hot paths.',
        path=runtime_performance_path,
        next_step='Review the performance baseline and tighten dashboard/health hot paths before heavier automation if posture is critical or failed.',
    )

    required_failed = [item for item in checks if item['severity'] == 'required' and item['status'] == 'fail']
    advisory_failed = [item for item in checks if item['severity'] == 'advisory' and item['status'] == 'fail']
    if required_failed:
        status = 'fail'
    elif advisory_failed:
        status = 'warn'
    else:
        status = 'pass'
    next_actions = [str(item['next_step']) for item in required_failed + advisory_failed if item.get('next_step')]

    return {
        'generated_at': _utc_now(),
        'status': status,
        'summary': {
            'checks_total': len(checks),
            'required_failed_total': len(required_failed),
            'advisory_failed_total': len(advisory_failed),
        },
        'checks': checks,
        'next_actions': next_actions,
    }


def export_quick_start_doctor(
    config: AppConfig | None = None,
    *,
    output_path: Path | None = None,
) -> dict[str, object]:
    runtime_config = config or AppConfig()
    target_path = output_path or (runtime_config.review_dir / 'quick_start_doctor.json')
    target_path.parent.mkdir(parents=True, exist_ok=True)
    report = build_quick_start_doctor(config=runtime_config)
    report['artifact_path'] = str(target_path)
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    target_path.write_text(encoded + '\n', encoding='utf-8')
    return report


def read_quick_start_doctor(
    config: AppConfig | None = None,
    *,
    output_path: Path | None = None,
) -> dict[str, object]:
    runtime_config = config or AppConfig()
    target_path = output_path or (runtime_config.review_dir / 'quick_start_doctor.json')
    if not target_path.exists():
        return {
            'status': 'missing',
            'available': False,
            'artifact_path': str(target_path),
            'generated_at': None,
            'summary': {
                'checks_total': 0,
                'required_failed_total': 0,
                'advisory_failed_total': 0,
            },
            'checks': [],
            'next_actions': [],
        }
    try:
        payload = json.loads(target_path.read_text(encoding='utf-8'))
    except json.JSONDecodeError:
        return {
            'status': 'invalid',
            'available': False,
            'artifact_path': str(target_path),
            'generated_at': None,
            'summary': {
                'checks_total': 0,
                'required_failed_total': 0,
                'advisory_failed_total': 0,
            },
            'checks': [],
            'next_actions': ['Regenerate doctor report: python scripts/quick_start_path.py --doctor'],
        }
    if not isinstance(payload, dict):
        payload = {}
    payload.setdefault('status', 'invalid')
    payload['available'] = True
    payload['artifact_path'] = str(target_path)
    payload.setdefault('generated_at', None)
    payload.setdefault('summary', {'checks_total': 0, 'required_failed_total': 0, 'advisory_failed_total': 0})
    payload.setdefault('checks', [])
    payload.setdefault('next_actions', [])
    return payload


def build_quick_start_path(
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
    guided = build_guided_smoke_test(
        config=runtime_config,
        registration_code=registration_code,
        provider_id=provider_id,
        probe_provider=probe_provider,
        skip_runtime_smoke=skip_runtime_smoke,
        force_seed_resources=force_seed_resources,
        force_owner=force_owner,
        force_access_profiles=force_access_profiles,
        force_refresh_registry=force_refresh_registry,
        days_valid=days_valid,
        rotate_days=rotate_days,
    )
    selected_provider = str(provider_id or guided.get('provider', {}).get('selected_provider') or 'ollama')
    env_example = f'examples/.env.{selected_provider}.example' if selected_provider in {'openai', 'anthropic', 'ollama'} else 'examples/.env.ollama.example'
    runtime_smoke = guided.get('runtime_smoke', {}) if isinstance(guided.get('runtime_smoke'), dict) else {}
    quick_start_passed = bool(guided.get('passed', False)) and runtime_smoke.get('status') != 'skipped'
    quick_start = {
        'status': 'ready' if quick_start_passed else 'attention_required',
        'lane': DEFAULT_PRIVATE_LANE if selected_provider == 'ollama' else f'provider_{selected_provider}',
        'target_persona': 'operator_first_run',
        'time_to_first_run_minutes': '5-10',
        'entry_command': 'python scripts/quick_start_path.py',
        'recommended_env_example': env_example,
        'dashboard_url': f"http://{runtime_config.server_host}:{runtime_config.server_port}/",
        'start_runtime_command': 'python scripts/run_private_server.py --host 127.0.0.1 --port 8080',
        'steps': _build_quick_start_steps(provider_id, guided),
        'operator_summary': _build_operator_summary(guided),
    }
    report = {
        'generated_at': guided['generated_at'],
        'quick_start': quick_start,
        'guided_report': guided,
        'next_actions': guided.get('next_actions', []),
        'passed': quick_start_passed,
    }
    return report


def build_parser(config: AppConfig) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Run the 5-10 minute quick-start path for a first SA-NOM local evaluation.')
    parser.add_argument('--doctor', action='store_true', help='Run quick-start preflight doctor checks and print pass/warn/fail status.')
    parser.add_argument('--doctor-output', default=str(config.review_dir / 'quick_start_doctor.json'))
    parser.add_argument('--registration-code', default='DEMO-ORG')
    parser.add_argument('--provider', default=None, help='Optional provider lane to target explicitly: ollama, openai, or anthropic.')
    parser.add_argument('--probe', action='store_true', help='Probe the selected provider lane after bootstrapping the quick-start path.')
    parser.add_argument('--skip-runtime-smoke', action='store_true', help='Skip the end-to-end runtime smoke step.')
    parser.add_argument('--days-valid', type=int, default=365)
    parser.add_argument('--rotate-days', type=int, default=180)
    parser.add_argument('--force-seed-resources', action='store_true')
    parser.add_argument('--force-owner', action='store_true')
    parser.add_argument('--force-access-profiles', action='store_true')
    parser.add_argument('--force-refresh-registry', action='store_true')
    parser.add_argument('--output', default=str(config.review_dir / 'quick_start_path.json'))
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    config = AppConfig()
    args = build_parser(config).parse_args(list(argv) if argv is not None else None)

    if args.doctor:
        report = export_quick_start_doctor(config=config, output_path=Path(args.doctor_output))
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if report['status'] == 'fail':
            raise SystemExit(1)
        return

    report = build_quick_start_path(
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
    report['artifact_path'] = str(output_path)
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    output_path.write_text(encoded + '\n', encoding='utf-8')
    print(encoded)

    if not report['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
