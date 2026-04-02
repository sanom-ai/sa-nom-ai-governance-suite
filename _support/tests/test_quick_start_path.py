from pathlib import Path
from tempfile import TemporaryDirectory

from sa_nom_governance.deployment.quick_start_path import (
    build_quick_start_doctor,
    build_quick_start_path,
    export_quick_start_doctor,
    read_quick_start_doctor,
)
from sa_nom_governance.utils.config import AppConfig


def _base_config(temp_dir: str) -> AppConfig:
    return AppConfig(base_dir=Path(temp_dir), persist_runtime=True, environment='development')


def test_quick_start_path_defaults_to_private_ollama_lane() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        report = build_quick_start_path(config=config, registration_code='demo-org')

        assert report['passed'] is True
        quick_start = report['quick_start']
        assert quick_start['status'] == 'ready'
        assert quick_start['lane'] == 'private_local_ollama'
        assert quick_start['recommended_env_example'] == 'examples/.env.ollama.example'
        assert quick_start['entry_command'] == 'python scripts/quick_start_path.py'
        assert quick_start['operator_summary']['runtime_smoke_status'] == 'passed'
        assert quick_start['operator_summary']['performance_status'] in {'ready', 'monitoring', 'critical', 'failed'}
        assert quick_start['operator_summary']['performance_slowest_metric'] in {'health', 'operational_readiness', 'dashboard_snapshot'}
        assert quick_start['steps'][1]['action'].startswith('Run `python scripts/quick_start_path.py`')


def test_quick_start_path_surfaces_attention_when_runtime_smoke_is_skipped() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        report = build_quick_start_path(config=config, registration_code='demo-org', skip_runtime_smoke=True)

        assert report['passed'] is False
        assert report['quick_start']['status'] == 'attention_required'
        assert report['quick_start']['operator_summary']['runtime_smoke_status'] == 'skipped'
        assert report['quick_start']['operator_summary']['performance_status'] in {'ready', 'monitoring', 'critical', 'failed'}
        assert 'Runtime smoke test was skipped by request.' in report['next_actions']


def test_quick_start_doctor_fails_when_required_bootstrap_artifacts_are_missing() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        report = build_quick_start_doctor(config=config)

        assert report['status'] == 'fail'
        assert report['summary']['required_failed_total'] >= 1
        assert isinstance(report['next_actions'], list)
        assert report['next_actions']


def test_quick_start_doctor_reports_warn_or_pass_after_quick_start_bootstrap() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        build_quick_start_path(config=config, registration_code='demo-org')
        report = build_quick_start_doctor(config=config)

        assert report['status'] in {'warn', 'pass'}
        assert report['summary']['required_failed_total'] == 0
        assert report['summary']['checks_total'] >= 10
        check_ids = {item['check_id'] for item in report['checks']}
        assert 'runtime_performance_baseline_present' in check_ids
        assert 'runtime_performance_posture_recorded' in check_ids


def test_quick_start_doctor_export_and_read_roundtrip() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        output_path = config.review_dir / 'quick_start_doctor.json'
        exported = export_quick_start_doctor(config=config, output_path=output_path)
        loaded = read_quick_start_doctor(config=config, output_path=output_path)

        assert exported['artifact_path'] == str(output_path)
        assert loaded['available'] is True
        assert loaded['artifact_path'] == str(output_path)
        assert loaded['status'] in {'fail', 'warn', 'pass'}


def test_quick_start_doctor_read_missing_report() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        output_path = config.review_dir / 'doctor_missing.json'
        loaded = read_quick_start_doctor(config=config, output_path=output_path)

        assert loaded['status'] == 'missing'
        assert loaded['available'] is False
        assert loaded['artifact_path'] == str(output_path)
