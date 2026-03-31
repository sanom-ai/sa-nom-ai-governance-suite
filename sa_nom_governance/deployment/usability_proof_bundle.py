from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from sa_nom_governance.dashboard.dashboard_data import DashboardSnapshotBuilder
from sa_nom_governance.deployment.nontechnical_demo_path import build_nontechnical_demo_path
from sa_nom_governance.deployment.quick_start_path import build_quick_start_path
from sa_nom_governance.utils.config import AppConfig


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _quick_start_summary(report: dict[str, object]) -> dict[str, object]:
    quick_start = report.get('quick_start', {}) if isinstance(report.get('quick_start'), dict) else {}
    summary = quick_start.get('operator_summary', {}) if isinstance(quick_start.get('operator_summary'), dict) else {}
    return {
        'status': quick_start.get('status', 'unknown'),
        'lane': quick_start.get('lane', 'unknown'),
        'entry_command': quick_start.get('entry_command', 'python scripts/quick_start_path.py'),
        'runtime_smoke_status': summary.get('runtime_smoke_status', 'unknown'),
        'provider_status': summary.get('provider_status', 'unknown'),
        'next_actions_total': len(report.get('next_actions', [])) if isinstance(report.get('next_actions', []), list) else 0,
    }


def _demo_summary(report: dict[str, object]) -> dict[str, object]:
    first_run = report.get('first_run', {}) if isinstance(report.get('first_run'), dict) else {}
    first_run_summary = first_run.get('summary', {}) if isinstance(first_run.get('summary'), dict) else {}
    return {
        'status': report.get('status', 'unknown'),
        'audience': report.get('audience', 'non_technical_operator'),
        'next_actions_total': len(report.get('next_actions', [])) if isinstance(report.get('next_actions', []), list) else 0,
        'talking_points_total': len(report.get('talking_points', [])) if isinstance(report.get('talking_points', []), list) else 0,
        'first_run_action_required_total': first_run_summary.get('action_required_total', 0),
    }


def _dashboard_summary(snapshot: dict[str, object]) -> dict[str, object]:
    summary = snapshot.get('summary', {}) if isinstance(snapshot.get('summary'), dict) else {}
    lanes = snapshot.get('operator_decision_lanes', []) if isinstance(snapshot.get('operator_decision_lanes', []), list) else []
    return {
        'operational_readiness_status': summary.get('operational_readiness_status', 'unknown'),
        'runtime_alert_total': summary.get('runtime_alert_total', 0),
        'human_required_total': summary.get('operator_human_required_total', 0),
        'blocked_total': summary.get('operator_blocked_total', 0),
        'workflow_backlog_total': summary.get('workflow_backlog_total', 0),
        'human_inbox_open_total': summary.get('human_inbox_open_total', 0),
        'recovery_pending_total': summary.get('recovery_pending_total', 0),
        'decision_lanes_total': len(lanes),
    }


def build_usability_proof_bundle(
    config: AppConfig | None = None,
    *,
    run_quick_start: bool = False,
    quick_start_options: dict[str, object] | None = None,
) -> dict[str, object]:
    runtime_config = config or AppConfig()
    quick_start_options = quick_start_options or {}

    if run_quick_start:
        quick_start_report = build_quick_start_path(runtime_config, **quick_start_options)
    else:
        quick_start_report = build_quick_start_path(runtime_config, skip_runtime_smoke=True, **quick_start_options)

    demo_report = build_nontechnical_demo_path(config=runtime_config)
    dashboard_snapshot = DashboardSnapshotBuilder(config=runtime_config).build()

    quick_start_summary = _quick_start_summary(quick_start_report)
    demo_summary = _demo_summary(demo_report)
    dashboard_operator_summary = _dashboard_summary(dashboard_snapshot)

    pass_criteria = [
        {
            'criterion': 'quick_start_path_exists',
            'passed': quick_start_summary.get('entry_command') == 'python scripts/quick_start_path.py',
        },
        {
            'criterion': 'demo_script_available',
            'passed': len(demo_report.get('demo_script', [])) > 0 if isinstance(demo_report.get('demo_script', []), list) else False,
        },
        {
            'criterion': 'dashboard_operator_lanes_available',
            'passed': dashboard_operator_summary.get('decision_lanes_total', 0) > 0,
        },
        {
            'criterion': 'human_boundary_visibility_available',
            'passed': 'human_required_total' in dashboard_operator_summary and 'blocked_total' in dashboard_operator_summary,
        },
    ]

    passed = all(bool(item.get('passed')) for item in pass_criteria)
    return {
        'generated_at': _utc_now(),
        'milestone': 'v0.3.0',
        'status': 'ready' if passed else 'attention_required',
        'passed': passed,
        'proof': {
            'quick_start_validation': quick_start_summary,
            'nontechnical_demo': demo_summary,
            'dashboard_operator_surface': dashboard_operator_summary,
        },
        'pass_criteria': pass_criteria,
        'next_actions': demo_report.get('next_actions', []),
        'artifacts': {
            'quick_start_report_generated': bool(quick_start_report),
            'nontechnical_demo_generated': True,
            'dashboard_snapshot_generated': True,
        },
    }


def main() -> None:
    config = AppConfig()
    parser = argparse.ArgumentParser(description='Build a v0.3.0 usability proof bundle from quick-start, demo, and dashboard surfaces.')
    parser.add_argument('--run-quick-start', action='store_true', help='Run the full quick_start_path, including runtime smoke, before collecting proof.')
    parser.add_argument('--output', default=str(config.review_dir / 'usability_proof_bundle.json'))
    args = parser.parse_args()

    report = build_usability_proof_bundle(
        config=config,
        run_quick_start=args.run_quick_start,
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    output_path.write_text(encoded + '\n', encoding='utf-8')
    print(encoded)

    if not report.get('passed', False):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
