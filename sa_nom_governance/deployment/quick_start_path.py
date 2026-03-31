from __future__ import annotations

import argparse
import json
from pathlib import Path

from sa_nom_governance.deployment.guided_smoke_test import build_guided_smoke_test
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
    ready = bool(report.get('passed'))
    return {
        'status': 'ready' if ready else 'attention_required',
        'startup_ready': bool(startup.get('ready', False)),
        'runtime_smoke_status': runtime_smoke.get('status', 'unknown'),
        'provider_status': provider.get('status', 'unknown'),
        'recommended_provider': provider.get('recommended_provider'),
        'selected_provider': provider.get('selected_provider'),
    }


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


def main() -> None:
    config = AppConfig()
    parser = argparse.ArgumentParser(description='Run the 5-10 minute quick-start path for a first SA-NOM local evaluation.')
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
    args = parser.parse_args()

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
