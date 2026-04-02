from pathlib import Path
from tempfile import TemporaryDirectory

from sa_nom_governance.deployment.runtime_performance_baseline import (
    build_runtime_performance_baseline,
    export_runtime_performance_baseline,
    read_runtime_performance_baseline,
)
from sa_nom_governance.utils.config import AppConfig


def _base_config(temp_dir: str) -> AppConfig:
    return AppConfig(base_dir=Path(temp_dir), persist_runtime=True, environment='development')


def test_runtime_performance_baseline_returns_expected_measurements() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        report = build_runtime_performance_baseline(config=config)

        assert report['status'] in {'ready', 'monitoring', 'critical', 'failed'}
        assert report['iterations'] == 1
        measurements = report.get('measurements', {})
        assert set(measurements.keys()) == {'health', 'operational_readiness', 'dashboard_snapshot'}
        assert report.get('summary', {}).get('measurements_total') == 3
        for metric in measurements.values():
            assert metric.get('status') in {'ready', 'monitoring', 'critical', 'failed'}
            assert isinstance(metric.get('elapsed_ms'), float)
            assert metric.get('elapsed_ms', 0.0) >= 0.0
            assert isinstance(metric.get('samples_ms'), list)
            assert metric.get('samples_ms')



def test_runtime_performance_baseline_export_and_read_roundtrip() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        output_path = config.review_dir / 'runtime_performance_baseline.json'
        exported = export_runtime_performance_baseline(config=config, output_path=output_path)
        loaded = read_runtime_performance_baseline(config=config, output_path=output_path)

        assert exported['output_path'] == str(output_path)
        assert loaded['available'] is True
        assert loaded['output_path'] == str(output_path)
        assert loaded['status'] in {'ready', 'monitoring', 'critical', 'failed'}
        assert isinstance(loaded.get('summary', {}).get('dashboard_snapshot_elapsed_ms'), float)



def test_runtime_performance_baseline_read_missing_report() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        output_path = config.review_dir / 'runtime_performance_missing.json'
        loaded = read_runtime_performance_baseline(config=config, output_path=output_path)

        assert loaded['status'] == 'missing'
        assert loaded['available'] is False
        assert loaded['output_path'] == str(output_path)
