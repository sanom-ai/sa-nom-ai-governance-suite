import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from sa_nom_governance.api.api_engine import build_engine_app
from sa_nom_governance.deployment.quick_start_path import build_quick_start_path
from sa_nom_governance.deployment.go_live_readiness import build_go_live_readiness
from sa_nom_governance.utils.config import AppConfig


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_actions(actions: list[dict[str, object]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for item in actions:
        normalized.append(
            {
                'code': str(item.get('code', 'next_step')),
                'title': str(item.get('title', 'Next action')),
                'command': str(item.get('command', '-')),
            }
        )
    return normalized


def _build_talking_points(status: str, actions: list[dict[str, str]]) -> list[str]:
    points = [
        'SA-NOM is running as a governed AI operations runtime, not a free-form chatbot surface.',
        'AI handles operational flow inside policy boundaries while human decisions stay explicit on sensitive paths.',
    ]
    if status == 'ready':
        points.append('Runtime posture is demo-ready with no first-run blockers.')
    elif status == 'monitoring':
        points.append('Runtime posture is usable, but there are monitored queues that should be watched during the demo.')
    else:
        points.append('Runtime posture still has attention-required setup items before a clean demo run.')
    if actions:
        points.append('The operator can clear remaining actions directly using the generated command list.')
    return points


def _build_demo_script(status: str, actions: list[dict[str, str]]) -> list[dict[str, object]]:
    script = [
        {
            'step': 1,
            'title': 'Position the runtime in plain language',
            'operator_line': 'This system lets AI run real work inside governed boundaries, with explicit human authority where needed.',
        },
        {
            'step': 2,
            'title': 'Show first-run posture',
            'operator_line': f"Current first-run status is '{status}'.",
        },
        {
            'step': 3,
            'title': 'Open the operator surface',
            'operator_line': 'Use the Overview panel to show go-live, operational readiness, and first-run action counts.',
        },
    ]
    if actions:
        script.append(
            {
                'step': 4,
                'title': 'Walk through action-required list',
                'operator_line': 'Show remaining setup actions and how each command closes a real runtime gap.',
                'actions': actions,
            }
        )
    else:
        script.append(
            {
                'step': 4,
                'title': 'Run live governed example',
                'operator_line': 'With no pending setup actions, proceed to a live governed request and show auditability in the same session.',
                'actions': [],
            }
        )
    return script




def _fallback_first_run_flow(app, config: AppConfig) -> dict[str, object]:
    operational = app.operational_readiness(limit=50)
    provider = app.model_provider_snapshot()
    go_live = build_go_live_readiness(config, app=app)

    owner_path = config.effective_owner_registration_path()
    access_path = config.effective_access_profiles_path()
    registry_manifest_path = config.trusted_registry_manifest_path

    owner_ready = bool(owner_path and owner_path.exists())
    access_ready = bool(access_path and access_path.exists())
    registry_ready = bool(registry_manifest_path and registry_manifest_path.exists())

    actions: list[dict[str, object]] = []
    if not owner_ready:
        actions.append(
            {
                'code': 'owner_registration',
                'title': 'Register owner identity',
                'command': 'python scripts/register_owner.py --registration-code DEMO-ORG',
            }
        )
    if not access_ready:
        actions.append(
            {
                'code': 'access_profiles',
                'title': 'Generate delegated access profiles',
                'command': 'python scripts/bootstrap_access_profiles.py --output _runtime/access_profiles.json --tokens-output _runtime/generated_access_tokens.json',
            }
        )
    if not registry_ready:
        actions.append(
            {
                'code': 'trusted_registry',
                'title': 'Refresh trusted registry artifacts',
                'command': 'python scripts/trusted_registry_refresh.py',
            }
        )
    if str(provider.get('status', 'unknown')) in {'disabled', 'partial'}:
        actions.append(
            {
                'code': 'provider_probe',
                'title': 'Probe default provider lane',
                'command': 'python scripts/provider_demo_flow.py --provider ollama --probe',
            }
        )

    if owner_ready and access_ready and registry_ready and str(operational.get('status', 'unknown')) == 'ready':
        status = 'ready'
    elif owner_ready and access_ready and registry_ready:
        status = 'monitoring'
    else:
        status = 'attention_required'

    return {
        'status': status,
        'summary': {
            'go_live_status': str(go_live.get('status', 'unknown')),
            'operational_readiness_status': str(operational.get('status', 'unknown')),
            'provider_status': str(provider.get('status', 'unknown')),
            'action_required_total': len(actions),
        },
        'action_required': actions,
        'operator_visibility': {
            'workflow_backlog_total': int((operational.get('summary', {}) or {}).get('active_workflow_total', 0) or 0),
            'human_inbox_open_total': int((operational.get('summary', {}) or {}).get('human_inbox_total', 0) or 0),
            'recovery_pending_total': int((operational.get('summary', {}) or {}).get('recovery_total', 0) or 0),
            'dead_letter_total': int((operational.get('summary', {}) or {}).get('dead_letter_total', 0) or 0),
        },
    }

def build_nontechnical_demo_path(
    config: AppConfig | None = None,
    *,
    run_quick_start: bool = False,
    quick_start_options: dict[str, object] | None = None,
) -> dict[str, object]:
    runtime_config = config or AppConfig()
    app = build_engine_app(runtime_config)

    quick_start_report: dict[str, object] | None = None
    if run_quick_start:
        options = dict(quick_start_options or {})
        quick_start_report = build_quick_start_path(runtime_config, **options)

    first_run = app.first_run_flow() if hasattr(app, 'first_run_flow') else _fallback_first_run_flow(app, runtime_config)
    status = str(first_run.get('status', 'unknown'))
    actions = _normalize_actions(first_run.get('action_required', []))

    return {
        'generated_at': _utc_now(),
        'status': status,
        'audience': 'non_technical_operator',
        'first_run': first_run,
        'demo_script': _build_demo_script(status, actions),
        'talking_points': _build_talking_points(status, actions),
        'next_actions': actions,
        'quick_start_executed': run_quick_start,
        'quick_start_report': quick_start_report,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description='Build a non-technical first-run demo path from live SA-NOM runtime posture.')
    parser.add_argument('--run-quick-start', action='store_true', help='Run quick_start_path before generating the non-technical demo report.')
    parser.add_argument('--quick-start-skip-runtime-smoke', action='store_true', help='If quick start is executed, skip runtime smoke during that run.')
    parser.add_argument('--output', default=None, help='Optional path to write the JSON report.')
    args = parser.parse_args()

    quick_start_options: dict[str, object] | None = None
    if args.run_quick_start:
        quick_start_options = {
            'skip_runtime_smoke': args.quick_start_skip_runtime_smoke,
        }

    report = build_nontechnical_demo_path(
        run_quick_start=args.run_quick_start,
        quick_start_options=quick_start_options,
    )

    output_path = Path(args.output) if args.output else Path(AppConfig().review_dir / 'nontechnical_demo_path.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    output_path.write_text(encoded + '\n', encoding='utf-8')
    print(encoded)


if __name__ == '__main__':
    main()
