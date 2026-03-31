from pathlib import Path
from tempfile import TemporaryDirectory

from sa_nom_governance.dashboard.dashboard_data import DashboardSnapshotBuilder
from sa_nom_governance.utils.config import AppConfig


def _base_config(temp_dir: str) -> AppConfig:
    return AppConfig(base_dir=Path(temp_dir), persist_runtime=True, environment='development')


def test_dashboard_snapshot_includes_operational_readiness_summary() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        snapshot = DashboardSnapshotBuilder(config=config).build()

        operational = snapshot.get('operational_readiness', {})
        summary = snapshot.get('summary', {})

        assert isinstance(operational, dict)
        assert operational.get('status') in {'ready', 'monitoring', 'attention_required'}
        assert summary.get('operational_readiness_status') == operational.get('status')
        assert isinstance(summary.get('workflow_backlog_total'), int)
        assert isinstance(summary.get('human_inbox_open_total'), int)
        assert isinstance(summary.get('recovery_pending_total'), int)
        assert isinstance(summary.get('dead_letter_total'), int)



def test_build_operator_decision_lanes_maps_human_required_and_blocked_paths() -> None:
    lanes = DashboardSnapshotBuilder.build_operator_decision_lanes(
        {
            'action_required': ['clearance_review', 'human_decision', 'recovery_resume', 'guarded_follow_up'],
        }
    )

    lane_ids = [lane['lane_id'] for lane in lanes]
    assert lane_ids == ['clearance_review', 'human_decision', 'recovery_resume', 'guarded_follow_up']
    assert lanes[0]['disposition'] == 'human_required'
    assert lanes[2]['disposition'] == 'blocked'


def test_build_operator_decision_lanes_falls_back_to_autonomy_ready() -> None:
    lanes = DashboardSnapshotBuilder.build_operator_decision_lanes({'action_required': []})

    assert len(lanes) == 1
    assert lanes[0]['lane_id'] == 'autonomy_ready'
    assert lanes[0]['disposition'] == 'autonomy_ready'



def test_dashboard_snapshot_exposes_missing_usability_proof_status() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        snapshot = DashboardSnapshotBuilder(config=config).build()

        operations = snapshot.get('operations', {})
        proof = operations.get('usability_proof', {}) if isinstance(operations, dict) else {}
        summary = snapshot.get('summary', {})

        assert proof.get('status') == 'missing'
        assert proof.get('available') is False
        assert summary.get('usability_proof_status') == 'missing'
        assert summary.get('usability_proof_available') is False


def test_dashboard_snapshot_reads_latest_usability_proof_status() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        config.review_dir.mkdir(parents=True, exist_ok=True)
        proof_path = config.review_dir / 'usability_proof_bundle.json'
        proof_path.write_text(
            '{"milestone":"v0.3.0","status":"ready","passed":true,"generated_at":"2026-04-01T00:00:00+00:00","pass_criteria":[{"criterion":"quick_start_path_exists","passed":true},{"criterion":"demo_script_available","passed":false}]}\n',
            encoding='utf-8',
        )

        snapshot = DashboardSnapshotBuilder(config=config).build()
        operations = snapshot.get('operations', {})
        proof = operations.get('usability_proof', {}) if isinstance(operations, dict) else {}
        summary = snapshot.get('summary', {})

        assert proof.get('status') == 'ready'
        assert proof.get('available') is True
        assert proof.get('passed') is True
        assert proof.get('criteria_total') == 2
        assert proof.get('criteria_passed_total') == 1
        assert isinstance(proof.get('pass_criteria'), list)
        assert summary.get('usability_proof_status') == 'ready'
        assert summary.get('usability_proof_available') is True
        assert summary.get('usability_proof_criteria_total') == 2
        assert summary.get('usability_proof_criteria_passed_total') == 1
