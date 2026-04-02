from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Callable

from sa_nom_governance.utils.config import AppConfig

DEFAULT_OUTPUT_NAME = 'runtime_performance_baseline.json'
DEFAULT_BUDGETS_MS: dict[str, dict[str, float]] = {
    'health': {'warning': 250.0, 'critical': 1000.0},
    'operational_readiness': {'warning': 500.0, 'critical': 1500.0},
    'dashboard_snapshot': {'warning': 1200.0, 'critical': 3000.0},
}
STATUS_RANK = {
    'ready': 0,
    'monitoring': 1,
    'critical': 2,
    'failed': 3,
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _elapsed_status(elapsed_ms: float, *, warning_ms: float, critical_ms: float) -> str:
    if elapsed_ms >= critical_ms:
        return 'critical'
    if elapsed_ms >= warning_ms:
        return 'monitoring'
    return 'ready'


def _pick_status(statuses: list[str]) -> str:
    if not statuses:
        return 'ready'
    return max(statuses, key=lambda item: STATUS_RANK.get(item, 0))


def _measure_metric(
    metric_id: str,
    runner: Callable[[], Any],
    summarizer: Callable[[Any], dict[str, object]],
    *,
    warning_ms: float,
    critical_ms: float,
    iterations: int,
) -> dict[str, object]:
    samples_ms: list[float] = []
    sample_statuses: list[str] = []
    last_result: Any = None
    error_message: str | None = None

    for _ in range(max(1, iterations)):
        started = perf_counter()
        try:
            last_result = runner()
        except Exception as exc:  # pragma: no cover - failure path is reported as data
            elapsed_ms = round((perf_counter() - started) * 1000, 3)
            samples_ms.append(elapsed_ms)
            sample_statuses.append('failed')
            error_message = f'{type(exc).__name__}: {exc}'
            break
        elapsed_ms = round((perf_counter() - started) * 1000, 3)
        samples_ms.append(elapsed_ms)
        sample_statuses.append(_elapsed_status(elapsed_ms, warning_ms=warning_ms, critical_ms=critical_ms))

    average_ms = round(sum(samples_ms) / len(samples_ms), 3) if samples_ms else 0.0
    maximum_ms = round(max(samples_ms), 3) if samples_ms else 0.0
    minimum_ms = round(min(samples_ms), 3) if samples_ms else 0.0
    status = _pick_status(sample_statuses)
    result_summary = summarizer(last_result) if error_message is None else {}

    return {
        'metric_id': metric_id,
        'status': status,
        'warning_ms': warning_ms,
        'critical_ms': critical_ms,
        'iterations': max(1, iterations),
        'samples_ms': samples_ms,
        'elapsed_ms': average_ms,
        'minimum_ms': minimum_ms,
        'maximum_ms': maximum_ms,
        'result_summary': result_summary,
        'error': error_message,
    }


def _health_summary(payload: Any) -> dict[str, object]:
    report = payload if isinstance(payload, dict) else {}
    governance_materials = report.get('governance_materials', {}) if isinstance(report.get('governance_materials', {}), dict) else {}
    role_library = report.get('role_library', {}) if isinstance(report.get('role_library', {}), dict) else {}
    return {
        'status': str(report.get('status', 'unknown')),
        'governance_materials_status': str(governance_materials.get('status', 'unknown')),
        'invalid_roles_total': int(role_library.get('roles_invalid_total', 0) or 0),
    }


def _operational_readiness_summary(payload: Any) -> dict[str, object]:
    report = payload if isinstance(payload, dict) else {}
    workflow = report.get('workflow', {}) if isinstance(report.get('workflow', {}), dict) else {}
    governed = report.get('governed_autonomy', {}) if isinstance(report.get('governed_autonomy', {}), dict) else {}
    return {
        'status': str(report.get('status', 'unknown')),
        'workflow_backlog_total': int(workflow.get('backlog_total', 0) or 0),
        'human_gate_open_total': int(governed.get('human_gate_open_total', 0) or 0),
        'recommended_runtime_action': str(governed.get('recommended_runtime_action', 'none')),
    }


def _dashboard_snapshot_summary(payload: Any) -> dict[str, object]:
    report = payload if isinstance(payload, dict) else {}
    summary = report.get('summary', {}) if isinstance(report.get('summary', {}), dict) else {}
    return {
        'operational_readiness_status': str(summary.get('operational_readiness_status', 'unknown')),
        'runtime_alert_total': int(summary.get('runtime_alert_total', 0) or 0),
        'workflow_backlog_total': int(summary.get('workflow_backlog_total', 0) or 0),
        'operator_attention_total': int(summary.get('operator_attention_total', 0) or 0),
    }


def build_runtime_performance_baseline(
    config: AppConfig | None = None,
    *,
    iterations: int = 1,
) -> dict[str, object]:
    from sa_nom_governance.api.api_engine import build_engine_app
    from sa_nom_governance.dashboard.dashboard_data import DashboardSnapshotBuilder

    runtime_config = config or AppConfig()
    runtime_app = build_engine_app(runtime_config)
    dashboard_builder = DashboardSnapshotBuilder(config=runtime_config, app=runtime_app)

    metric_specs = [
        ('health', lambda: runtime_app.health(), _health_summary),
        ('operational_readiness', lambda: runtime_app.operational_readiness(limit=50), _operational_readiness_summary),
        ('dashboard_snapshot', dashboard_builder.build, _dashboard_snapshot_summary),
    ]

    measurements: dict[str, dict[str, object]] = {}
    statuses: list[str] = []
    for metric_id, runner, summarizer in metric_specs:
        budget = DEFAULT_BUDGETS_MS[metric_id]
        measurement = _measure_metric(
            metric_id,
            runner,
            summarizer,
            warning_ms=float(budget['warning']),
            critical_ms=float(budget['critical']),
            iterations=iterations,
        )
        measurements[metric_id] = measurement
        statuses.append(str(measurement.get('status', 'ready')))

    overall_status = _pick_status(statuses)
    warning_total = sum(1 for item in measurements.values() if item.get('status') == 'monitoring')
    critical_total = sum(1 for item in measurements.values() if item.get('status') == 'critical')
    failed_total = sum(1 for item in measurements.values() if item.get('status') == 'failed')
    slowest_metric = max(measurements.values(), key=lambda item: float(item.get('elapsed_ms', 0.0) or 0.0)) if measurements else None

    return {
        'generated_at': _utc_now(),
        'status': overall_status,
        'iterations': max(1, iterations),
        'budgets_ms': DEFAULT_BUDGETS_MS,
        'measurements': measurements,
        'summary': {
            'measurements_total': len(measurements),
            'warning_total': warning_total,
            'critical_total': critical_total,
            'failed_total': failed_total,
            'slowest_metric': str((slowest_metric or {}).get('metric_id', 'unknown')),
            'slowest_elapsed_ms': float((slowest_metric or {}).get('elapsed_ms', 0.0) or 0.0),
            'health_elapsed_ms': float(measurements.get('health', {}).get('elapsed_ms', 0.0) or 0.0),
            'operational_readiness_elapsed_ms': float(measurements.get('operational_readiness', {}).get('elapsed_ms', 0.0) or 0.0),
            'dashboard_snapshot_elapsed_ms': float(measurements.get('dashboard_snapshot', {}).get('elapsed_ms', 0.0) or 0.0),
        },
    }


def read_runtime_performance_baseline(
    config: AppConfig | None = None,
    *,
    output_path: Path | None = None,
) -> dict[str, object]:
    runtime_config = config or AppConfig()
    resolved_output = output_path or (runtime_config.review_dir / DEFAULT_OUTPUT_NAME)

    if not resolved_output.exists():
        return {
            'status': 'missing',
            'available': False,
            'output_path': str(resolved_output),
            'generated_at': None,
            'summary': {
                'measurements_total': 0,
                'warning_total': 0,
                'critical_total': 0,
                'failed_total': 0,
                'slowest_metric': 'unknown',
                'slowest_elapsed_ms': 0.0,
                'health_elapsed_ms': 0.0,
                'operational_readiness_elapsed_ms': 0.0,
                'dashboard_snapshot_elapsed_ms': 0.0,
            },
            'report': None,
        }

    try:
        report = json.loads(resolved_output.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return {
            'status': 'invalid',
            'available': True,
            'output_path': str(resolved_output),
            'generated_at': None,
            'summary': {
                'measurements_total': 0,
                'warning_total': 0,
                'critical_total': 0,
                'failed_total': 0,
                'slowest_metric': 'unknown',
                'slowest_elapsed_ms': 0.0,
                'health_elapsed_ms': 0.0,
                'operational_readiness_elapsed_ms': 0.0,
                'dashboard_snapshot_elapsed_ms': 0.0,
            },
            'report': None,
        }

    return {
        'status': str(report.get('status', 'unknown')),
        'available': True,
        'output_path': str(resolved_output),
        'generated_at': report.get('generated_at'),
        'summary': report.get('summary', {}) if isinstance(report.get('summary', {}), dict) else {},
        'report': report,
    }


def export_runtime_performance_baseline(
    config: AppConfig | None = None,
    *,
    output_path: Path | None = None,
    iterations: int = 1,
) -> dict[str, object]:
    runtime_config = config or AppConfig()
    resolved_output = output_path or (runtime_config.review_dir / DEFAULT_OUTPUT_NAME)
    report = build_runtime_performance_baseline(config=runtime_config, iterations=iterations)
    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    resolved_output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {
        'status': str(report.get('status', 'unknown')),
        'output_path': str(resolved_output),
        'report': report,
    }


def main() -> None:
    config = AppConfig()
    parser = argparse.ArgumentParser(description='Capture a runtime performance baseline for health, readiness, and dashboard build paths.')
    parser.add_argument('--output', default=str(config.review_dir / DEFAULT_OUTPUT_NAME))
    parser.add_argument('--iterations', type=int, default=1)
    args = parser.parse_args()

    result = export_runtime_performance_baseline(
        config=config,
        output_path=Path(args.output),
        iterations=args.iterations,
    )
    print(json.dumps(result.get('report', {}), ensure_ascii=False, indent=2))
    if result.get('status') in {'critical', 'failed'}:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
