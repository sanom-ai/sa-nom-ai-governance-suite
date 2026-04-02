import json
from pathlib import Path
from tempfile import TemporaryDirectory

from sa_nom_governance.deployment.public_release_preflight import run_preflight


def _seed_workspace(root: Path, *, version: str = '0.7.0') -> None:
    (root / '.git').mkdir(parents=True, exist_ok=True)
    (root / '.gitignore').write_text('_runtime/*\n', encoding='utf-8')
    (root / '.dockerignore').write_text('_runtime/\n', encoding='utf-8')
    (root / '_runtime').mkdir(parents=True, exist_ok=True)
    (root / '_runtime' / '.gitkeep').write_text('', encoding='utf-8')
    (root / '_review').mkdir(parents=True, exist_ok=True)
    (root / 'docs' / 'releases').mkdir(parents=True, exist_ok=True)
    (root / 'docs' / 'releases' / f'RELEASE_NOTES_v{version}.md').write_text('# notes\n', encoding='utf-8')
    (root / 'pyproject.toml').write_text(f'[project]\nversion = "{version}"\n', encoding='utf-8')
    (root / '_review' / 'quick_start_doctor.json').write_text(
        json.dumps(
            {
                'status': 'pass',
                'summary': {
                    'checks_total': 10,
                    'required_failed_total': 0,
                    'advisory_failed_total': 0,
                },
            },
            indent=2,
        )
        + '\n',
        encoding='utf-8',
    )



def _write_performance_baseline(root: Path, *, status: str, slowest_metric: str = 'dashboard_snapshot') -> None:
    (root / '_review' / 'runtime_performance_baseline.json').write_text(
        json.dumps(
            {
                'status': status,
                'summary': {
                    'slowest_metric': slowest_metric,
                    'slowest_elapsed_ms': 1337.0,
                    'dashboard_snapshot_elapsed_ms': 1337.0,
                    'health_elapsed_ms': 111.0,
                    'operational_readiness_elapsed_ms': 222.0,
                    'warning_total': 1 if status == 'monitoring' else 0,
                    'critical_total': 1 if status == 'critical' else 0,
                    'failed_total': 1 if status == 'failed' else 0,
                },
            },
            indent=2,
        )
        + '\n',
        encoding='utf-8',
    )



def _find_check(result: dict[str, object], label: str) -> dict[str, str]:
    checks = result.get('checks', []) if isinstance(result.get('checks', []), list) else []
    return next(check for check in checks if isinstance(check, dict) and check.get('label') == label)



def test_public_release_preflight_blocks_on_critical_runtime_performance_posture() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        _seed_workspace(root)
        _write_performance_baseline(root, status='critical')

        result = run_preflight(root=root, git_available=True, pytest_installed=True)

        assert result['status'] == 'BLOCKED'
        check = _find_check(result, 'runtime_performance_guardrail')
        assert check['status'] == 'error'
        assert 'blocking' in check['detail']



def test_public_release_preflight_warns_when_runtime_performance_is_monitoring() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        _seed_workspace(root)
        _write_performance_baseline(root, status='monitoring')

        result = run_preflight(root=root, git_available=True, pytest_installed=True)

        assert result['status'] == 'READY WITH WARNINGS'
        check = _find_check(result, 'runtime_performance_guardrail')
        assert check['status'] == 'warning'
        assert 'warning budget' in check['detail']



def test_public_release_preflight_blocks_when_target_release_notes_are_missing() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        _seed_workspace(root, version='0.7.0')
        _write_performance_baseline(root, status='ready')

        result = run_preflight(root=root, release_version='0.7.1', git_available=True, pytest_installed=True)

        assert result['status'] == 'BLOCKED'
        check = _find_check(result, 'release_notes_target')
        assert check['status'] == 'error'
        assert 'v0.7.1' in check['detail']
