from pathlib import Path

from sa_nom_governance.deployment.nontechnical_demo_path import build_nontechnical_demo_path
from sa_nom_governance.utils.config import AppConfig


def test_nontechnical_demo_path_returns_operator_ready_shape(tmp_path: Path) -> None:
    config = AppConfig(base_dir=tmp_path, persist_runtime=True, environment='development')

    report = build_nontechnical_demo_path(config=config)

    assert report['audience'] == 'non_technical_operator'
    assert report['status'] in {'ready', 'monitoring', 'attention_required'}
    assert isinstance(report.get('demo_script', []), list)
    assert isinstance(report.get('talking_points', []), list)
    assert isinstance(report.get('next_actions', []), list)
    assert report.get('first_run', {}).get('summary', {}).get('action_required_total') == len(report.get('next_actions', []))


def test_nontechnical_demo_path_can_wrap_quick_start_run(tmp_path: Path) -> None:
    config = AppConfig(base_dir=tmp_path, persist_runtime=True, environment='development')

    report = build_nontechnical_demo_path(
        config=config,
        run_quick_start=True,
        quick_start_options={'skip_runtime_smoke': True},
    )

    assert report['quick_start_executed'] is True
    assert isinstance(report.get('quick_start_report', {}), dict)
    assert report['quick_start_report'].get('quick_start', {}).get('entry_command') == 'python scripts/quick_start_path.py'
