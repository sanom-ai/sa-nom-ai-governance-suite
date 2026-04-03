import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from sa_nom_governance.deployment import public_release_preflight as preflight
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


def test_preflight_helpers_cover_invalid_missing_and_warning_states() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        assert preflight._project_version(root) is None

        invalid_json_path = root / 'invalid.json'
        invalid_json_path.write_text('{broken', encoding='utf-8')
        assert preflight._load_json(invalid_json_path) is None

        list_json_path = root / 'list.json'
        list_json_path.write_text(json.dumps(['not', 'a', 'dict']), encoding='utf-8')
        assert preflight._load_json(list_json_path) is None

        review_dir = root / '_review'
        review_dir.mkdir(parents=True, exist_ok=True)
        (review_dir / 'quick_start_doctor.json').write_text('{broken', encoding='utf-8')
        quick_start = preflight._load_quick_start_doctor(root)
        assert quick_start['status'] == 'invalid'

        baseline = preflight._load_runtime_performance_baseline(root)
        assert baseline['status'] == 'missing'

        assert preflight._evaluate_checks([{'status': 'warning'}]) == 'READY WITH WARNINGS'
        assert preflight._evaluate_checks([{'status': 'ok'}]) == 'READY'


def test_public_release_preflight_uses_release_catalog_and_surfaces_mixed_warnings() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        _seed_workspace(root)
        (root / 'pyproject.toml').unlink()
        (root / '.env.local').write_text('TOKEN=secret\n', encoding='utf-8')
        (root / '_review' / 'quick_start_doctor.json').write_text(
            json.dumps({'status': 'warn', 'summary': {'advisory_failed_total': 2}}, indent=2),
            encoding='utf-8',
        )
        (root / '_review' / 'runtime_performance_baseline.json').write_text('{broken', encoding='utf-8')

        result = run_preflight(root=root, git_available=False, pytest_installed=False)

        assert result['status'] == 'READY WITH WARNINGS'
        assert _find_check(result, 'git_installed')['status'] == 'warning'
        assert _find_check(result, 'pytest_installed')['status'] == 'warning'
        assert _find_check(result, 'release_notes_catalog')['status'] == 'ok'
        assert _find_check(result, 'private_env_files')['status'] == 'warning'
        assert _find_check(result, 'quick_start_doctor_posture')['status'] == 'warning'
        assert _find_check(result, 'runtime_performance_guardrail')['status'] == 'warning'


def test_public_release_preflight_main_prints_json_and_text_modes() -> None:
    ok_result = {'status': 'READY', 'checks': [], 'release_version': None}
    with patch.object(preflight, 'run_preflight', return_value=ok_result), patch.object(sys, 'argv', ['preflight', '--json']):
        stream = io.StringIO()
        with redirect_stdout(stream):
            assert preflight.main() == 0
        assert '"status": "READY"' in stream.getvalue()

    blocked_result = {
        'status': 'BLOCKED',
        'checks': [{'status': 'error', 'label': 'release_notes_target', 'detail': 'missing notes'}],
        'release_version': '0.7.9',
    }
    with patch.object(preflight, 'run_preflight', return_value=blocked_result), patch.object(sys, 'argv', ['preflight', '--release-version', '0.7.9']):
        stream = io.StringIO()
        with redirect_stdout(stream):
            assert preflight.main() == 1
        text = stream.getvalue()
        assert 'Target release version: v0.7.9' in text
        assert 'Preflight result: BLOCKED' in text
