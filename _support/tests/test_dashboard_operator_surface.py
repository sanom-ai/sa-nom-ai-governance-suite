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
