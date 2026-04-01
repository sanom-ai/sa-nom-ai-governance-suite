from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from sa_nom_governance.core.execution_context import ExecutionContext
from sa_nom_governance.dashboard.dashboard_data import DashboardSnapshotBuilder
from sa_nom_governance.utils.config import AppConfig


def _base_config(temp_dir: str) -> AppConfig:
    return AppConfig(base_dir=Path(temp_dir), persist_runtime=True, environment='development')


def test_dashboard_snapshot_includes_operational_readiness_summary() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        snapshot = DashboardSnapshotBuilder(config=config).build()

        operational = snapshot.get('operational_readiness', {})
        first_run = snapshot.get('first_run_readiness', {})
        summary = snapshot.get('summary', {})

        assert isinstance(operational, dict)
        assert isinstance(first_run, dict)
        assert operational.get('status') in {'ready', 'monitoring', 'attention_required'}
        assert summary.get('operational_readiness_status') == operational.get('status')
        assert isinstance(summary.get('workflow_backlog_total'), int)
        assert isinstance(summary.get('human_inbox_open_total'), int)
        assert isinstance(summary.get('recovery_pending_total'), int)
        assert isinstance(summary.get('dead_letter_total'), int)
        assert first_run.get('status') in {'ready', 'monitoring', 'blocked'}
        assert isinstance(summary.get('first_run_blockers_total'), int)
        assert isinstance(summary.get('first_run_advisories_total'), int)
        assert isinstance(summary.get('first_run_action_items_total'), int)
        assert isinstance(summary.get('first_run_action_required_total'), int)



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
        doctor = operations.get('quick_start_doctor', {}) if isinstance(operations, dict) else {}
        first_run_actions = operations.get('first_run_action_center', {}) if isinstance(operations, dict) else {}
        summary = snapshot.get('summary', {})

        assert proof.get('status') == 'missing'
        assert proof.get('available') is False
        assert summary.get('usability_proof_status') == 'missing'
        assert summary.get('usability_proof_available') is False
        assert summary.get('quick_start_doctor_status') == 'missing'
        assert doctor.get('status') == 'missing'
        assert first_run_actions.get('status') in {'ready', 'monitoring', 'blocked'}
        assert isinstance(first_run_actions.get('items_total'), int)
        assert isinstance(first_run_actions.get('required_total'), int)
        assert isinstance(summary.get('first_run_action_items_total'), int)
        assert isinstance(summary.get('first_run_action_required_total'), int)


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
        doctor = operations.get('quick_start_doctor', {}) if isinstance(operations, dict) else {}
        summary = snapshot.get('summary', {})

        assert proof.get('status') == 'ready'
        assert proof.get('available') is True
        assert proof.get('passed') is True
        assert proof.get('criteria_total') == 2
        assert proof.get('criteria_passed_total') == 1
        assert proof.get('criteria_failed_total') == 1
        assert proof.get('failed_criteria') == ['demo_script_available']
        assert isinstance(proof.get('pass_criteria'), list)
        assert summary.get('usability_proof_status') == 'ready'
        assert summary.get('usability_proof_available') is True
        assert summary.get('usability_proof_criteria_total') == 2
        assert summary.get('usability_proof_criteria_passed_total') == 1
        assert summary.get('usability_proof_criteria_failed_total') == 1

def test_dashboard_snapshot_exposes_unified_operator_alert_policy_and_queue_health() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        config.operator_alert_warning_hours = 12
        config.operator_alert_critical_hours = 48
        config.operator_alert_stale_hours = 720
        config.operator_alert_backlog_warning_total = 2
        config.operator_alert_backlog_critical_total = 4
        config.operator_notification_realert_hours = 2
        config.operator_notification_digest_hours = 12
        config.operator_notification_critical_channels = 'dashboard,email'
        builder = DashboardSnapshotBuilder(config=config)

        context = ExecutionContext(
            request_id='REQ-OPS-1',
            requester='operator@example.com',
            action='approve_group_policy',
            role_id='OPS_REVIEW',
            payload={'resource': 'contract', 'resource_id': 'C-100'},
            metadata={},
        )
        override = builder.app.engine.human_override.create_state(
            context,
            required_by='reviewer@example.com',
            reason='High-risk action requires human review.',
        )
        builder.app.engine.human_override._requests[override.request_id].created_at = (
            datetime.now(timezone.utc) - timedelta(hours=72)
        ).isoformat()
        builder.app.engine.human_override._persist()

        snapshot = builder.build()
        policy = snapshot.get('operator_alert_policy', {})
        queue_health = snapshot.get('operator_queue_health', {})
        notification_center = snapshot.get('operator_notification_center', {})
        delivery_readiness = snapshot.get('operator_notification_delivery_readiness', {})
        runtime_alerts = snapshot.get('runtime_alerts', [])
        summary = snapshot.get('summary', {})

        assert policy.get('aging', {}).get('warning_hours') == 12
        assert policy.get('aging', {}).get('critical_hours') == 48
        assert policy.get('backlog', {}).get('warning_total') == 2
        assert policy.get('notification', {}).get('cadence', {}).get('realert_hours') == 2
        assert policy.get('notification', {}).get('cadence', {}).get('digest_hours') == 12
        assert isinstance(queue_health.get('items'), list)
        pending = next(item for item in queue_health.get('items', []) if item.get('lane_id') == 'pending_overrides')
        assert pending.get('total') == 1
        assert pending.get('status') in {'critical', 'stale'}
        assert pending.get('oldest_age_hours', 0) >= 72
        assert summary.get('operator_attention_total', 0) >= 1
        assert summary.get('operator_critical_total', 0) >= 1
        assert summary.get('operator_notification_candidates_total', 0) >= 1
        assert summary.get('operator_notification_posture') in {'ready', 'dashboard_only', 'pressured', 'degraded', 'disabled'}
        assert summary.get('operator_notification_external_ready') is False
        assert notification_center.get('dispatch_candidates_total', 0) >= 1
        assert notification_center.get('active_channel_total', 0) >= 1
        assert delivery_readiness.get('posture') == 'dashboard_only'
        assert delivery_readiness.get('external_routing_ready') is False
        assert delivery_readiness.get('dispatch_candidates_total', 0) >= 1
        assert isinstance(delivery_readiness.get('next_actions'), list)
        pending_notification = next(item for item in notification_center.get('items', []) if item.get('lane_id') == 'pending_overrides')
        assert pending_notification.get('dispatch_ready') is True
        assert pending_notification.get('channels') == ['dashboard', 'email']
        assert any(alert.get('alert_id') == 'operator_queue_pending_overrides' for alert in runtime_alerts)
