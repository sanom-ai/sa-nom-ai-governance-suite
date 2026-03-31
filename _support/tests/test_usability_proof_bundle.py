from pathlib import Path

from sa_nom_governance.deployment.usability_proof_bundle import build_usability_proof_bundle, export_usability_proof_bundle
from sa_nom_governance.utils.config import AppConfig


def test_usability_proof_bundle_returns_expected_shape(tmp_path: Path) -> None:
    config = AppConfig(base_dir=tmp_path, persist_runtime=True, environment='development')

    report = build_usability_proof_bundle(config=config)

    assert report['milestone'] == 'v0.3.0'
    assert report['status'] in {'ready', 'attention_required'}
    assert isinstance(report.get('proof', {}), dict)
    assert isinstance(report.get('pass_criteria', []), list)
    assert report.get('proof', {}).get('quick_start_validation', {}).get('entry_command') == 'python scripts/quick_start_path.py'
    assert report.get('proof', {}).get('dashboard_operator_surface', {}).get('decision_lanes_total', 0) >= 1


def test_usability_proof_bundle_can_run_full_quick_start(tmp_path: Path) -> None:
    config = AppConfig(base_dir=tmp_path, persist_runtime=True, environment='development')

    report = build_usability_proof_bundle(config=config, run_quick_start=True, quick_start_options={'skip_runtime_smoke': True})

    assert isinstance(report.get('artifacts', {}), dict)
    assert report.get('artifacts', {}).get('quick_start_report_generated') is True
    assert isinstance(report.get('next_actions', []), list)



def test_export_usability_proof_bundle_writes_output(tmp_path: Path) -> None:
    config = AppConfig(base_dir=tmp_path, persist_runtime=True, environment='development')
    output_path = tmp_path / '_review' / 'usability_proof_bundle_from_test.json'

    result = export_usability_proof_bundle(config=config, output_path=output_path)

    assert result['output_path'] == str(output_path)
    assert output_path.exists() is True
    assert isinstance(result.get('report', {}), dict)
    assert result.get('report', {}).get('milestone') == 'v0.3.0'
