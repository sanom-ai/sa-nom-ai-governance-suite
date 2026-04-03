import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from shutil import copy2
from tempfile import TemporaryDirectory

from sa_nom_governance.compliance.trusted_registry import write_trusted_registry_files
from sa_nom_governance.core.execution_context import ExecutionContext
from sa_nom_governance.dashboard.dashboard_data import DashboardSnapshotBuilder
from sa_nom_governance.dashboard.dashboard_server import DashboardService
from sa_nom_governance.deployment.runtime_performance_baseline import export_runtime_performance_baseline
from sa_nom_governance.guards.access_control import AccessControl, AccessProfile
from sa_nom_governance.utils.config import AppConfig


def _base_config(temp_dir: str) -> AppConfig:
    return AppConfig(base_dir=Path(temp_dir), persist_runtime=True, environment='development')


def _build_profile(role_name: str) -> AccessProfile:
    return AccessProfile(
        profile_id=f'{role_name}-test',
        display_name=role_name.title(),
        role_name=role_name,
        permissions=set(AccessControl.DEFAULT_PERMISSIONS[role_name]),
    )


def _seed_invalid_governance_materials(config: AppConfig) -> None:
    fixture_path = Path(__file__).resolve().parent / 'GOV.ptn'
    for role_path in config.roles_dir.glob('*.ptn'):
        role_path.unlink()
    copy2(fixture_path, config.roles_dir / 'GOV.ptn')
    copy2(fixture_path, config.roles_dir / 'BAD.ptn')
    assert config.trusted_registry_manifest_path is not None
    assert config.trusted_registry_cache_path is not None
    write_trusted_registry_files(
        roles_dir=config.roles_dir,
        manifest_path=config.trusted_registry_manifest_path,
        cache_path=config.trusted_registry_cache_path,
        role_ids=['GOV'],
        signing_key=config.trusted_registry_signing_key or 'sanom-dev-registry-key',
        key_id=config.trusted_registry_key_id,
    )


def _seed_notification_targets(config: AppConfig, payload: list[dict[str, object]]) -> None:
    assert config.integration_targets_path is not None
    config.integration_targets_path.parent.mkdir(parents=True, exist_ok=True)
    config.integration_targets_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


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
        assert summary.get('governed_autonomy_status') in {'idle', 'autonomous_inflight', 'human_gated', 'blocked', 'settled', 'unknown'}
        assert isinstance(summary.get('governed_autonomy_action'), str)
        assert isinstance(summary.get('autonomous_inflight_total'), int)
        assert isinstance(summary.get('human_gate_open_total'), int)
        assert isinstance(summary.get('fail_closed_workflow_total'), int)
        assert isinstance(summary.get('work_inbox_open_total'), int)
        assert isinstance(summary.get('work_inbox_attention_total'), int)
        assert isinstance(summary.get('work_inbox_human_required_total'), int)
        assert isinstance(summary.get('work_inbox_blocked_total'), int)
        assert isinstance(summary.get('work_inbox_primary_view'), str)
        assert isinstance(snapshot.get('unified_work_inbox', {}), dict)
        assert first_run.get('status') in {'ready', 'monitoring', 'blocked'}
        assert isinstance(summary.get('first_run_blockers_total'), int)
        assert isinstance(summary.get('first_run_advisories_total'), int)
        assert isinstance(summary.get('first_run_action_items_total'), int)
        assert isinstance(summary.get('first_run_action_required_total'), int)



def test_dashboard_snapshot_exposes_master_data_assignment_and_search_summary() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        snapshot = DashboardSnapshotBuilder(config=config).build()

        master_data = snapshot.get('master_data', {})
        assignment_queue = snapshot.get('assignment_queue', {})
        global_search = snapshot.get('global_search', {})
        summary = snapshot.get('summary', {})
        runtime_health = snapshot.get('runtime_health', {})

        assert isinstance(master_data, dict)
        assert isinstance(assignment_queue, dict)
        assert isinstance(global_search, dict)
        assert isinstance(master_data.get('summary', {}), dict)
        assert isinstance(assignment_queue.get('summary', {}), dict)
        assert isinstance(global_search.get('summary', {}), dict)
        assert isinstance(summary.get('directory_people_total'), int)
        assert isinstance(summary.get('directory_seats_total'), int)
        assert isinstance(summary.get('directory_teams_total'), int)
        assert isinstance(summary.get('assignment_items_total'), int)
        assert isinstance(summary.get('assignment_critical_total'), int)
        assert isinstance(summary.get('assignment_human_required_total'), int)
        assert summary.get('assignment_primary_view') in {'overview', 'requests', 'overrides', 'directory', 'documents', 'actions', 'human_ask', 'studio'}
        assert isinstance(summary.get('search_index_total'), int)
        assert summary.get('search_primary_view') == 'directory'
        assert runtime_health.get('master_data_store', {}).get('status') in {'present', 'missing'}


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



def test_dashboard_snapshot_build_reuses_precomputed_runtime_snapshots() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        builder = DashboardSnapshotBuilder(config=config)
        counters = {
            'health': 0,
            'list_roles': 0,
            'compliance_snapshot': 0,
            'evidence_pack_summary': 0,
        }

        original_health = builder.app.health
        original_list_roles = builder.app.list_roles
        original_compliance_snapshot = builder.app.compliance_snapshot
        original_evidence_pack_summary = builder.app.evidence_pack_summary

        def counted_health(*args, **kwargs):
            counters['health'] += 1
            return original_health(*args, **kwargs)

        def counted_list_roles(*args, **kwargs):
            counters['list_roles'] += 1
            return original_list_roles(*args, **kwargs)

        def counted_compliance_snapshot(*args, **kwargs):
            counters['compliance_snapshot'] += 1
            return original_compliance_snapshot(*args, **kwargs)

        def counted_evidence_pack_summary(*args, **kwargs):
            counters['evidence_pack_summary'] += 1
            return original_evidence_pack_summary(*args, **kwargs)

        builder.app.health = counted_health
        builder.app.list_roles = counted_list_roles
        builder.app.compliance_snapshot = counted_compliance_snapshot
        builder.app.evidence_pack_summary = counted_evidence_pack_summary

        snapshot = builder.build()

        assert snapshot.get('summary', {}).get('operational_readiness_status') in {'ready', 'monitoring', 'attention_required'}
        assert counters['health'] == 1
        assert counters['list_roles'] == 1
        assert counters['compliance_snapshot'] == 1
        assert counters['evidence_pack_summary'] == 1


def test_engine_health_reuses_dispatcher_health_snapshot() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        builder = DashboardSnapshotBuilder(config=config)
        counter = {'dispatcher_health': 0}
        original_dispatcher_health = builder.app.integration_dispatcher.health

        def counted_dispatcher_health(*args, **kwargs):
            counter['dispatcher_health'] += 1
            return original_dispatcher_health(*args, **kwargs)

        builder.app.integration_dispatcher.health = counted_dispatcher_health

        health = builder.app.health()

        assert health.get('status') in {'ok', 'degraded'}
        assert counter['dispatcher_health'] == 1


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
        assert summary.get('runtime_performance_status') == 'missing'
        assert isinstance(summary.get('runtime_performance_dashboard_elapsed_ms'), float)
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

def test_dashboard_snapshot_exposes_runtime_performance_baseline_summary() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        export_runtime_performance_baseline(config=config)
        snapshot = DashboardSnapshotBuilder(config=config).build()

        operations = snapshot.get('operations', {})
        baseline = operations.get('runtime_performance_baseline', {}) if isinstance(operations, dict) else {}
        summary = snapshot.get('summary', {})

        assert baseline.get('available') is True
        assert baseline.get('status') in {'ready', 'monitoring', 'critical', 'failed'}
        assert baseline.get('slowest_metric') in {'health', 'operational_readiness', 'dashboard_snapshot'}
        assert isinstance(baseline.get('dashboard_snapshot_elapsed_ms'), float)
        assert summary.get('runtime_performance_status') == baseline.get('status')
        assert isinstance(summary.get('runtime_performance_dashboard_elapsed_ms'), float)


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
        config.operator_notification_warning_channels = 'dashboard,email,slack,servicenow'
        config.operator_notification_critical_channels = 'dashboard,email,slack,servicenow'
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
        assert notification_center.get('external_channel_total', 0) >= 2
        assert delivery_readiness.get('posture') == 'dashboard_only'
        assert delivery_readiness.get('external_routing_ready') is False
        assert delivery_readiness.get('dispatch_candidates_total', 0) >= 1
        assert delivery_readiness.get('missing_external_channels') == []
        assert set(delivery_readiness.get('inactive_external_channels', [])) == {'slack', 'servicenow'}
        assert 'slack' in delivery_readiness.get('configured_external_channels', [])
        assert 'servicenow' in delivery_readiness.get('configured_external_channels', [])
        assert isinstance(delivery_readiness.get('next_actions'), list)
        pending_notification = next(item for item in notification_center.get('items', []) if item.get('lane_id') == 'pending_overrides')
        assert pending_notification.get('dispatch_ready') is True
        assert pending_notification.get('channels') == ['dashboard', 'email', 'slack', 'servicenow']
        assert pending_notification.get('external_channels') == ['slack', 'servicenow']
        assert any(alert.get('alert_id') == 'operator_queue_pending_overrides' for alert in runtime_alerts)



def test_dashboard_snapshot_exposes_unified_work_inbox_surface() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        builder = DashboardSnapshotBuilder(config=config)

        context = ExecutionContext(
            request_id='REQ-INBOX-1',
            requester='operator@example.com',
            action='approve_group_policy',
            role_id='OPS_REVIEW',
            payload={'resource': 'contract', 'resource_id': 'C-INBOX-1'},
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

        studio_request = builder.app.role_private_studio.create_request(
            {
                'role_name': 'Inbox Publish Candidate',
                'purpose': 'Prepare a publish-ready hat for unified work inbox coverage.',
                'reporting_line': 'LEGAL',
                'business_domain': 'legal_operations',
                'operating_mode': 'indirect',
                'assigned_user_id': 'LEGAL_MANAGER_30',
                'executive_owner_id': 'EXEC_OWNER',
                'seat_id': 'OPS-INBOX-STUDIO',
                'responsibilities': ['review incoming contracts', 'flag risk'],
                'allowed_actions': ['review_contract', 'flag_risk', 'advise_compliance'],
                'forbidden_actions': ['sign_contract'],
                'wait_human_actions': [],
                'handled_resources': ['contract'],
                'financial_sensitivity': 'medium',
                'legal_sensitivity': 'high',
                'compliance_sensitivity': 'high',
            },
            requested_by='EXEC_OWNER',
        )
        builder.app.role_private_studio.review_request(studio_request['request_id'], reviewer='EXEC_OWNER', decision='approve', note='Ready for publish.')

        snapshot = builder.build()
        inbox = snapshot.get('unified_work_inbox', {})
        summary = inbox.get('summary', {}) if isinstance(inbox, dict) else {}
        items = inbox.get('items', []) if isinstance(inbox, dict) else []

        pending_lane = next(item for item in items if item.get('lane_id') == 'pending_overrides')
        studio_lane = next(item for item in items if item.get('lane_id') == 'studio_publish_queue')

        assert summary.get('open_total', 0) >= 2
        assert summary.get('attention_total', 0) >= 1
        assert summary.get('human_required_total', 0) >= 1
        assert summary.get('ready_total', 0) >= 1
        assert summary.get('primary_view') in {'overrides', 'studio', 'overview'}
        assert pending_lane.get('view') == 'overrides'
        assert pending_lane.get('disposition') == 'human_required'
        assert pending_lane.get('total') == 1
        assert pending_lane.get('oldest_age_hours', 0) >= 72
        assert pending_lane.get('sample_references') == [override.request_id]
        assert studio_lane.get('view') == 'studio'
        assert studio_lane.get('disposition') == 'ready'
        assert studio_lane.get('total') >= 1
        assert studio_request['request_id'] in studio_lane.get('sample_references', [])
        assert snapshot.get('summary', {}).get('work_inbox_open_total', 0) >= 2
        assert snapshot.get('summary', {}).get('work_inbox_human_required_total', 0) >= 1
        assert snapshot.get('summary', {}).get('work_inbox_primary_view') == summary.get('primary_view')




def test_dashboard_snapshot_groups_requests_overrides_and_human_ask_into_cases() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        builder = DashboardSnapshotBuilder(config=config)

        request_result = builder.app.request(
            requester='operator@example.com',
            role_id='GOV',
            action='approve_policy',
            payload={'resource': 'contract', 'resource_id': 'C-CASE-001'},
            metadata={
                'execution_plan': {
                    'plan_id': 'plan-case-001',
                    'step_id': 'step-intake',
                }
            },
        )
        request_id = request_result.metadata['request_id']

        context = ExecutionContext(
            request_id=request_id,
            requester='operator@example.com',
            action='approve_policy',
            role_id='GOV',
            payload={'resource': 'contract', 'resource_id': 'C-CASE-001'},
            metadata={
                'origin_request_id': request_id,
                'execution_plan': {
                    'plan_id': 'plan-case-001',
                    'step_id': 'step-human-review',
                },
            },
        )
        override = builder.app.engine.human_override.create_state(
            context,
            required_by='reviewer@example.com',
            reason='High-risk action requires human review.',
        )
        builder.app.engine.human_override._persist()

        session = builder.app.create_human_ask_session(
            {
                'role_id': 'GOV',
                'prompt': 'Summarize the current governed case posture.',
                'metadata': {
                    'origin_request_id': request_id,
                    'execution_plan': {
                        'plan_id': 'plan-case-001',
                        'step_id': 'step-human-review',
                    },
                },
            },
            requested_by='EXEC_OWNER',
        )

        snapshot = builder.build()
        cases_surface = snapshot.get('cases', {})
        case_summary = cases_surface.get('summary', {}) if isinstance(cases_surface, dict) else {}
        case_items = cases_surface.get('items', []) if isinstance(cases_surface, dict) else []

        linked_case = next(item for item in case_items if request_id in item.get('linked_request_ids', []))
        timeline_types = {entry.get('event_type') for entry in linked_case.get('timeline', [])}
        work_item_kinds = {entry.get('kind') for entry in linked_case.get('work_items', []) if int(entry.get('total', 0) or 0) > 0}
        request_row = next(item for item in snapshot.get('requests', []) if item.get('request_id') == request_id)
        override_row = next(item for item in snapshot.get('overrides', []) if item.get('request_id') == override.request_id)
        session_row = next(item for item in snapshot.get('human_ask', {}).get('sessions', []) if item.get('session_id') == session['session_id'])
        audit_row = next(
            item
            for item in snapshot.get('audit', [])
            if (
                item.get('request_id') == request_id
                or (item.get('metadata', {}) if isinstance(item.get('metadata', {}), dict) else {}).get('request_id') == request_id
                or ((item.get('metadata', {}) if isinstance(item.get('metadata', {}), dict) else {}).get('context', {}) if isinstance((item.get('metadata', {}) if isinstance(item.get('metadata', {}), dict) else {}).get('context', {}), dict) else {}).get('request_id') == request_id
            )
        )

        assert case_summary.get('cases_total', 0) >= 1
        assert snapshot.get('summary', {}).get('cases_total', 0) >= 1
        assert case_summary.get('primary_view') in {'overrides', 'requests', 'human_ask', 'audit'}
        assert linked_case.get('status') in {'human_required', 'attention_required', 'active', 'blocked'}
        assert override.request_id in linked_case.get('linked_override_ids', [])
        assert session['session_id'] in linked_case.get('linked_session_ids', [])
        assert 'plan-case-001' in linked_case.get('linked_workflow_ids', [])
        assert request_row.get('case_id') == linked_case.get('case_id')
        assert override_row.get('case_id') == linked_case.get('case_id')
        assert session_row.get('case_id') == linked_case.get('case_id')
        assert audit_row.get('case_id') == linked_case.get('case_id')
        continuity = linked_case.get('continuity', {})

        assert {'request', 'override', 'human_ask', 'audit'}.issubset(timeline_types)
        assert {'request', 'override', 'human_ask', 'audit'}.issubset(work_item_kinds)
        assert continuity.get('next_view') in {'overrides', 'human_ask', 'requests', 'audit', 'conflicts'}
        assert continuity.get('evidence_posture') in {'proof attached', 'partial proof', 'proof starting'}



def test_dashboard_snapshot_surfaces_case_proof_and_follow_up_cues() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        builder = DashboardSnapshotBuilder(config=config)

        pending = builder.app.request(
            requester='operator@example.com',
            role_id='LEGAL',
            action='review_contract',
            payload={'resource': 'contract', 'resource_id': 'CASE-PROOF-001', 'amount': 1000000},
            metadata={
                'authority_contract': {'approval_gate': 'human_required'},
                'execution_plan': {
                    'plan_id': 'plan-case-proof-001',
                    'step_id': 'step-human-check',
                    'intent': 'Prepare proof-aware case review',
                    'expected_output': 'Human review package',
                    'stop_condition': 'human_checkpoint',
                    'step_index': 2,
                    'total_steps': 4,
                    'checkpoint_required': True,
                },
            },
        )
        request_id = pending.metadata['request_id']

        builder.app.create_human_ask_session(
            {
                'role_id': 'GOV',
                'prompt': 'Summarize the proof posture for this governed case.',
                'metadata': {
                    'origin_request_id': request_id,
                    'execution_plan': {
                        'plan_id': 'plan-case-proof-001',
                        'step_id': 'step-human-check',
                    },
                },
            },
            requested_by='EXEC_OWNER',
        )

        builder.app.approve_override(
            pending.human_override['request_id'],
            resolved_by='EXEC_OWNER',
            note='Workflow proof bundle validation.',
        )
        builder.app.create_workflow_proof_bundle('plan-case-proof-001', requested_by='EXEC_OWNER')

        snapshot = builder.build()
        case_items = snapshot.get('cases', {}).get('items', [])
        linked_case = next(item for item in case_items if request_id in item.get('linked_request_ids', []))
        continuity = linked_case.get('continuity', {}) if isinstance(linked_case.get('continuity', {}), dict) else {}
        latest_proof = linked_case.get('latest_proof_event', {}) if isinstance(linked_case.get('latest_proof_event', {}), dict) else {}
        follow_up_views = {entry.get('view') for entry in continuity.get('follow_up_actions', []) if isinstance(entry, dict)}

        assert linked_case.get('workflow_proof_total', 0) >= 1
        assert continuity.get('evidence_posture') == 'proof attached'
        assert latest_proof.get('action') == 'workflow_proof_export'
        assert 'audit' in follow_up_views
        assert continuity.get('next_view') in {'requests', 'audit', 'human_ask'}
def test_dashboard_snapshot_surfaces_case_ids_on_studio_requests() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        builder = DashboardSnapshotBuilder(config=config)

        studio_request = builder.app.role_private_studio.create_request(
            {
                'role_name': 'Case Backbone Studio Analyst',
                'purpose': 'Keep studio authoring linked into the canonical case lane.',
                'reporting_line': 'LEGAL',
                'business_domain': 'case_backbone',
                'operating_mode': 'direct',
                'assigned_user_id': 'LEGAL_MANAGER_CASE',
                'executive_owner_id': 'EXEC_OWNER',
                'seat_id': 'OPS-CASE-STUDIO',
                'responsibilities': ['Prepare governed role updates'],
                'allowed_actions': ['review_contract'],
                'forbidden_actions': ['approve_contract'],
                'wait_human_actions': ['approve_contract'],
                'handled_resources': ['contract'],
                'sample_scenarios': ['Role draft needs linked case visibility'],
            },
            requested_by='EXEC_OWNER',
        )

        snapshot = builder.build()
        studio_rows = snapshot.get('role_private_studio', {}).get('requests', [])
        studio_row = next(item for item in studio_rows if item.get('request_id') == studio_request['request_id'])
        case_items = snapshot.get('cases', {}).get('items', [])
        linked_case = next(item for item in case_items if studio_request['request_id'] in item.get('linked_studio_request_ids', []))
        work_item_kinds = {entry.get('kind') for entry in linked_case.get('work_items', []) if int(entry.get('total', 0) or 0) > 0}

        assert studio_row.get('case_id') == linked_case.get('case_id')
        assert studio_row.get('case_status') == linked_case.get('status')
        assert studio_row.get('case_primary_view') == linked_case.get('primary_view')
        assert 'studio' in work_item_kinds
        assert (linked_case.get('continuity', {}) or {}).get('next_view') in {'studio', 'audit', 'requests'}


def test_dashboard_snapshot_surfaces_ai_actions_in_cases_and_runtime_health() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        builder = DashboardSnapshotBuilder(config=config)

        request_result = builder.app.request(
            requester='operator@example.com',
            role_id='GOV',
            action='approve_policy',
            payload={'resource': 'contract', 'resource_id': 'ACTION-CASE-001'},
            metadata={
                'execution_plan': {
                    'plan_id': 'plan-action-case-001',
                    'step_id': 'step-action-runtime',
                }
            },
        )
        request_id = request_result.metadata['request_id']

        initial_snapshot = builder.build()
        case_item = next(item for item in initial_snapshot.get('cases', {}).get('items', []) if request_id in item.get('linked_request_ids', []))
        action = builder.app.create_action(
            {
                'action_type': 'summarize_case',
                'case_id': case_item['case_id'],
                'case_reference': case_item['case_reference'],
            },
            requested_by='EXEC_OWNER',
            case_snapshot=case_item,
        )

        snapshot = builder.build()
        actions_surface = snapshot.get('actions', {})
        action_row = next(item for item in actions_surface.get('items', []) if item.get('action_id') == action['action_id'])
        linked_case = next(item for item in snapshot.get('cases', {}).get('items', []) if action['action_id'] in item.get('linked_action_ids', []))
        work_item_kinds = {entry.get('kind') for entry in linked_case.get('work_items', []) if int(entry.get('total', 0) or 0) > 0}
        timeline_types = {entry.get('event_type') for entry in linked_case.get('timeline', [])}

        assert actions_surface.get('summary', {}).get('actions_total', 0) >= 1
        assert action_row.get('case_id') == linked_case.get('case_id')
        assert linked_case.get('case_primary_view') == linked_case.get('primary_view') if 'case_primary_view' in linked_case else True
        assert 'action' in work_item_kinds
        assert 'action' in timeline_types
        assert snapshot.get('runtime_health', {}).get('action_runtime_store', {}).get('status') == 'present'


def test_dashboard_snapshot_surfaces_governed_documents_in_cases_and_runtime_health() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        builder = DashboardSnapshotBuilder(config=config)

        pending = builder.app.request(
            requester='operator@example.com',
            role_id='LEGAL',
            action='review_contract',
            payload={'resource': 'contract', 'resource_id': 'DOC-CASE-001', 'amount': 250000},
        )
        request_id = pending.metadata['request_id']

        document = builder.document_center.create_document(
            {
                'document_class': 'policy',
                'title': 'Case-linked Policy Memo',
                'content': 'This governed document is linked to a live runtime case.',
                'case_id': f'request:{request_id}',
                'owner_id': 'LEGAL_OWNER',
                'approver_id': 'EXEC_OWNER',
                'retention_code': 'POL-RET-001',
                'business_domain': 'contract_governance',
                'tags': ['policy', 'case'],
                'metadata': {'source': 'dashboard_operator_surface'},
            },
            created_by='EXEC_OWNER',
        )
        builder.document_center.submit_review(document['document_id'], submitted_by='EXEC_OWNER', note='Submit document for review.')
        builder.document_center.approve_document(document['document_id'], approved_by='EXEC_OWNER', note='Approve document for publication.')
        builder.document_center.publish_document(document['document_id'], published_by='EXEC_OWNER', note='Publish linked document.')

        snapshot = builder.build()
        documents_surface = snapshot.get('documents', {})
        document_summary = documents_surface.get('summary', {}) if isinstance(documents_surface, dict) else {}
        document_items = documents_surface.get('items', []) if isinstance(documents_surface, dict) else []
        document_row = next(item for item in document_items if item.get('document_id') == document['document_id'])
        linked_case = next(item for item in snapshot.get('cases', {}).get('items', []) if document['document_id'] in item.get('linked_document_ids', []))
        timeline_types = {entry.get('event_type') for entry in linked_case.get('timeline', [])}
        work_item_kinds = {entry.get('kind') for entry in linked_case.get('work_items', []) if int(entry.get('total', 0) or 0) > 0}
        runtime_health = snapshot.get('runtime_health', {})

        assert document_summary.get('documents_total', 0) >= 1
        assert document_summary.get('published_total', 0) >= 1
        assert document_summary.get('case_linked_total', 0) >= 1
        assert snapshot.get('summary', {}).get('documents_total', 0) >= 1
        assert snapshot.get('summary', {}).get('documents_published_total', 0) >= 1
        assert document_row.get('case_reference') == f'request:{request_id}'
        assert document_row.get('case_id') == linked_case.get('case_id')
        assert runtime_health.get('document_store', {}).get('status') == 'present'
        assert runtime_health.get('document_center', {}).get('published_total', 0) >= 1
        assert 'document' in timeline_types
        assert 'document' in work_item_kinds
        assert linked_case.get('primary_view') in {'requests', 'documents', 'audit', 'overrides'}
        assert (linked_case.get('continuity', {}) or {}).get('next_view') in {'requests', 'documents', 'audit', 'overrides', 'conflicts'}


def test_dashboard_snapshot_surfaces_document_review_and_publish_work_lanes() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        builder = DashboardSnapshotBuilder(config=config)

        builder.document_center.create_document(
            {
                'document_class': 'procedure',
                'title': 'Draft Document Work Lane',
                'content': 'This draft should stay in the document review queue.',
                'owner_id': 'OPS_OWNER',
                'approver_id': 'EXEC_OWNER',
                'retention_code': 'PROC-RET-001',
                'business_domain': 'operations',
            },
            created_by='EXEC_OWNER',
        )

        approved = builder.document_center.create_document(
            {
                'document_class': 'policy',
                'title': 'Approved Document Work Lane',
                'content': 'This approved document should surface in the publish queue.',
                'owner_id': 'LEGAL_OWNER',
                'approver_id': 'EXEC_OWNER',
                'retention_code': 'POL-RET-002',
                'business_domain': 'policy_operations',
            },
            created_by='EXEC_OWNER',
        )
        builder.document_center.submit_review(approved['document_id'], submitted_by='EXEC_OWNER', note='Submit approved lane document.')
        builder.document_center.approve_document(approved['document_id'], approved_by='EXEC_OWNER', note='Ready for publish queue.')

        snapshot = builder.build()
        inbox = snapshot.get('unified_work_inbox', {})
        items = inbox.get('items', []) if isinstance(inbox, dict) else []

        review_lane = next(item for item in items if item.get('lane_id') == 'document_review_queue')
        publish_lane = next(item for item in items if item.get('lane_id') == 'document_publish_queue')

        assert review_lane.get('view') == 'documents'
        assert review_lane.get('disposition') == 'monitoring'
        assert review_lane.get('total', 0) >= 1
        assert publish_lane.get('view') == 'documents'
        assert publish_lane.get('disposition') == 'ready'
        assert publish_lane.get('total', 0) >= 1
        assert any(str(ref).startswith('POL-') for ref in publish_lane.get('sample_references', []))
        assert snapshot.get('summary', {}).get('work_inbox_open_total', 0) >= 2


def test_dashboard_notification_delivery_readiness_turns_ready_for_active_external_channels() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        config.outbound_http_integrations_enabled = True
        config.operator_notification_warning_channels = 'dashboard,slack,jira'
        config.operator_notification_critical_channels = 'dashboard,slack,jira'
        _seed_notification_targets(
            config,
            [
                {
                    'target_id': 'executive-ledger',
                    'name': 'Executive Integration Ledger',
                    'status': 'active',
                    'delivery_mode': 'log_only',
                    'platform': 'ledger',
                    'notification_channels': ['dashboard'],
                    'subscribed_events': ['runtime.*'],
                },
                {
                    'target_id': 'slack-bridge',
                    'name': 'Slack Alert Bridge',
                    'category': 'chatops',
                    'platform': 'slack',
                    'status': 'active',
                    'delivery_mode': 'http',
                    'endpoint_url': 'https://hooks.slack.example.local/services/test',
                    'notification_channels': ['slack', 'webhook'],
                    'subscribed_events': ['runtime.*'],
                },
                {
                    'target_id': 'jira-service-desk',
                    'name': 'Jira Service Desk Bridge',
                    'category': 'ticketing',
                    'platform': 'jira',
                    'status': 'active',
                    'delivery_mode': 'http',
                    'endpoint_url': 'https://jira.example.local/rest/api/2/issue',
                    'notification_channels': ['jira', 'ticketing', 'webhook'],
                    'subscribed_events': ['runtime.*'],
                },
            ],
        )
        builder = DashboardSnapshotBuilder(config=config)

        context = ExecutionContext(
            request_id='REQ-OPS-2',
            requester='operator@example.com',
            action='approve_group_policy',
            role_id='OPS_REVIEW',
            payload={'resource': 'contract', 'resource_id': 'C-101'},
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
        delivery_readiness = snapshot.get('operator_notification_delivery_readiness', {})
        notification_center = snapshot.get('operator_notification_center', {})

        assert delivery_readiness.get('posture') == 'ready'
        assert delivery_readiness.get('external_routing_ready') is True
        assert set(delivery_readiness.get('requested_external_channels', [])) == {'jira', 'slack'}
        assert set(delivery_readiness.get('active_external_channels', [])) >= {'jira', 'slack'}
        assert delivery_readiness.get('missing_external_channels') == []
        assert delivery_readiness.get('inactive_external_channels') == []
        pending_notification = next(item for item in notification_center.get('items', []) if item.get('lane_id') == 'pending_overrides')
        assert pending_notification.get('external_channels') == ['slack', 'jira']


def test_engine_health_surfaces_invalid_governance_materials() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        _seed_invalid_governance_materials(config)
        builder = DashboardSnapshotBuilder(config=config)

        roles = builder.app.list_roles()
        invalid_role = next(role for role in roles if role.get('role_id') == 'BAD')
        health = builder.app.health()
        invalid_hierarchy = next(item for item in health.get('role_hierarchy', {}).get('invalid_entries', []) if item.get('role_id') == 'BAD')
        invalid_role_health = next(item for item in health.get('role_library', {}).get('invalid_roles', []) if item.get('role_id') == 'BAD')

        assert invalid_role.get('status') == 'invalid'
        assert invalid_role.get('load_error', {}).get('stage') == 'load'
        assert invalid_role.get('load_error', {}).get('error_type') == 'TrustedRegistryError'
        assert health.get('status') == 'degraded'
        assert health.get('governance_materials', {}).get('status') == 'degraded'
        assert health.get('role_library', {}).get('roles_total') == 2
        assert health.get('role_library', {}).get('roles_ready_total') == 1
        assert health.get('role_library', {}).get('roles_invalid_total') == 1
        assert invalid_role_health.get('load_error', {}).get('stage') == 'load'
        assert health.get('role_hierarchy', {}).get('roles_total') == 1
        assert health.get('role_hierarchy', {}).get('invalid_entries_total') == 1
        assert invalid_hierarchy.get('error_type') == 'TrustedRegistryError'


def test_dashboard_snapshot_exposes_invalid_governance_material_counts() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        _seed_invalid_governance_materials(config)
        snapshot = DashboardSnapshotBuilder(config=config).build()

        summary = snapshot.get('summary', {})
        runtime_health = snapshot.get('runtime_health', {})
        role_library = runtime_health.get('role_library', {}) if isinstance(runtime_health.get('role_library', {}), dict) else {}
        governance_materials = runtime_health.get('governance_materials', {}) if isinstance(runtime_health.get('governance_materials', {}), dict) else {}
        invalid_role = next(role for role in snapshot.get('roles', []) if role.get('role_id') == 'BAD')

        assert runtime_health.get('engine_status') == 'degraded'
        assert governance_materials.get('status') == 'degraded'
        assert role_library.get('roles_invalid_total') == 1
        assert summary.get('governance_materials_status') == 'degraded'
        assert summary.get('invalid_roles_total') == 1
        assert summary.get('invalid_hierarchy_entries_total') == 1
        assert invalid_role.get('status') == 'invalid'
        assert invalid_role.get('load_error', {}).get('stage') == 'load'



def test_dashboard_snapshot_surfaces_human_ask_confidence_and_freshness_signals() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        builder = DashboardSnapshotBuilder(config=config)
        original_confidence_score = builder.app.human_ask._confidence_score
        builder.app.human_ask._confidence_score = lambda prompt, entry, risk_score: min(0.99, builder.app.human_ask.confidence_threshold + 0.02)
        try:
            session = builder.app.create_human_ask_session(
                {
                    'role_id': 'GOV',
                    'prompt': 'Summarize the current governance posture.',
                },
                requested_by='EXEC_OWNER',
            )
        finally:
            builder.app.human_ask._confidence_score = original_confidence_score

        stored = builder.app.human_ask.store.get_session(session['session_id'])
        stored.updated_at = (
            datetime.now(timezone.utc) - timedelta(hours=builder.app.human_ask.freshness_stale_hours + 4)
        ).isoformat()
        builder.app.human_ask.store.save_session(stored)

        snapshot = builder.build()
        human_ask_summary = snapshot.get('human_ask', {}).get('summary', {})
        summary = snapshot.get('summary', {})
        runtime_alerts = snapshot.get('runtime_alerts', [])

        assert human_ask_summary.get('guarded_confidence_total', 0) >= 1
        assert human_ask_summary.get('stale_total', 0) >= 1
        assert human_ask_summary.get('guarded_follow_up_posture_total', 0) >= 1
        assert summary.get('human_ask_guarded_confidence_total', 0) >= 1
        assert summary.get('human_ask_stale_total', 0) >= 1
        assert any(alert.get('alert_id') == 'human_ask_guarded_confidence' for alert in runtime_alerts)
        assert any(alert.get('alert_id') == 'human_ask_stale_follow_up' for alert in runtime_alerts)



def test_dashboard_snapshot_surfaces_role_private_studio_revision_and_publish_signals() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        builder = DashboardSnapshotBuilder(config=config)

        def studio_payload(role_name: str, seat_id: str, assigned_user_id: str) -> dict[str, object]:
            return {
                'role_name': role_name,
                'purpose': 'Review governed publication posture before trusted release.',
                'reporting_line': 'LEGAL',
                'business_domain': 'legal_operations',
                'operating_mode': 'indirect',
                'assigned_user_id': assigned_user_id,
                'executive_owner_id': 'EXEC_OWNER',
                'seat_id': seat_id,
                'responsibilities': ['review incoming contracts', 'flag risk'],
                'allowed_actions': ['review_contract', 'flag_risk', 'advise_compliance'],
                'forbidden_actions': ['sign_contract'],
                'wait_human_actions': [],
                'handled_resources': ['contract'],
                'financial_sensitivity': 'medium',
                'legal_sensitivity': 'high',
                'compliance_sensitivity': 'high',
            }

        ready_request = builder.app.role_private_studio.create_request(studio_payload('Publisher Ready Dashboard Analyst', 'OPS-DASH-READY', 'LEGAL_MANAGER_11'), requested_by='EXEC_OWNER')
        builder.app.role_private_studio.review_request(ready_request['request_id'], reviewer='EXEC_OWNER', decision='approve', note='Ready for publish.')

        manual_request = builder.app.role_private_studio.create_request(studio_payload('Manual Dashboard Analyst', 'OPS-DASH-MANUAL', 'LEGAL_MANAGER_12'), requested_by='EXEC_OWNER')
        builder.app.role_private_studio.update_request_ptag(
            manual_request['request_id'],
            manual_request['generated_ptag'].replace('context "SA-NOM Role Private Studio"', 'context "SA-NOM Role Private Studio Manual"'),
            updated_by='EXEC_OWNER',
        )

        restored_request = builder.app.role_private_studio.create_request(studio_payload('Restored Dashboard Analyst', 'OPS-DASH-RESTORE', 'LEGAL_MANAGER_13'), requested_by='EXEC_OWNER')
        builder.app.role_private_studio.update_request(
            restored_request['request_id'],
            {'purpose': 'Review restored dashboard draft before trusted publication.'},
            updated_by='EXEC_OWNER',
        )
        builder.app.role_private_studio.restore_request_revision(restored_request['request_id'], 1, restored_by='EXEC_OWNER')

        published_request = builder.app.role_private_studio.create_request(studio_payload('Published Dashboard Analyst', 'OPS-DASH-PUBLISHED', 'LEGAL_MANAGER_14'), requested_by='EXEC_OWNER')
        builder.app.role_private_studio.review_request(published_request['request_id'], reviewer='EXEC_OWNER', decision='approve', note='Approved for publish.')
        builder.app.role_private_studio.publish_request(published_request['request_id'], published_by='EXEC_OWNER')

        snapshot = builder.build()
        studio_summary = snapshot.get('role_private_studio', {}).get('summary', {})
        summary = snapshot.get('summary', {})
        runtime_alerts = snapshot.get('runtime_alerts', [])

        assert studio_summary.get('manual_override_total', 0) >= 1
        assert studio_summary.get('restored_request_total', 0) >= 1
        assert studio_summary.get('publisher_ready_total', 0) >= 1
        assert studio_summary.get('published_registry_verified_total', 0) >= 1
        assert studio_summary.get('published_live_hash_verified_total', 0) >= 1
        assert studio_summary.get('published_current_revision_total', 0) >= 1
        assert studio_summary.get('trusted_live_total', 0) >= 1
        assert studio_summary.get('trust_attention_total', 0) == 0
        assert summary.get('studio_manual_override_total', 0) >= 1
        assert summary.get('studio_restored_request_total', 0) >= 1
        assert summary.get('studio_publisher_ready_total', 0) >= 1
        assert summary.get('studio_registry_verified_total', 0) >= 1
        assert summary.get('studio_live_hash_verified_total', 0) >= 1
        assert summary.get('studio_trusted_live_total', 0) >= 1
        assert summary.get('studio_trust_attention_total', 0) == 0
        assert any(alert.get('alert_id') == 'studio_revision_governance' for alert in runtime_alerts)



def test_dashboard_snapshot_surfaces_structural_and_guardrail_operator_proof() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        builder = DashboardSnapshotBuilder(config=config)

        builder.app.role_private_studio.create_request(
            {
                'role_name': 'Public Sector Fragility Analyst',
                'purpose': 'Review public-sector structural pressure before trusted release.',
                'reporting_line': '',
                'business_domain': 'government_policy_operations',
                'operating_mode': 'direct',
                'assigned_user_id': '',
                'executive_owner_id': 'EXEC_OWNER',
                'seat_id': 'OPS-PUBLIC-FRAGILE',
                'responsibilities': ['review incoming policy packets'],
                'allowed_actions': ['review_contract', 'approve_contract_exception', 'advise_compliance', 'approve_policy', 'escalate_policy'],
                'forbidden_actions': ['sign_contract'],
                'wait_human_actions': [],
                'handled_resources': [],
                'financial_sensitivity': 'high',
                'legal_sensitivity': 'high',
                'compliance_sensitivity': 'critical',
            },
            requested_by='EXEC_OWNER',
        )

        pending = builder.app.request(
            requester='AUDITOR',
            role_id='GOV',
            action='approve_policy',
            payload={'resource': 'contract', 'resource_id': 'C-GUARD-1'},
        )
        conflict = builder.app.request(
            requester='tester',
            role_id='LEGAL',
            action='review_contract',
            payload={'resource': 'contract', 'resource_id': 'C-GUARD-1', 'amount': 3000000},
        )
        blocked = builder.app.request(
            requester='tester',
            role_id='LEGAL',
            action='review_contract',
            payload={'resource': 'contract', 'resource_id': 'C-GUARD-2', 'amount': 1000000},
            metadata={'authority_contract': {'approval_gate': 'blocked'}},
        )

        snapshot = builder.build()
        studio_summary = snapshot.get('role_private_studio', {}).get('summary', {})
        guardrail_summary = snapshot.get('guardrail_surface', {}).get('summary', {})
        summary = snapshot.get('summary', {})
        requests = snapshot.get('requests', [])
        runtime_alerts = snapshot.get('runtime_alerts', [])

        assert studio_summary.get('pt_oss_public_sector_mode_total', 0) >= 1
        assert studio_summary.get('pt_oss_elevated_total', 0) >= 1
        assert studio_summary.get('pt_oss_high_risk_metric_total', 0) >= 1
        assert studio_summary.get('structural_guarded_total', 0) >= 1
        assert summary.get('studio_pt_oss_public_sector_total', 0) >= 1
        assert summary.get('studio_pt_oss_elevated_total', 0) >= 1
        assert summary.get('studio_pt_oss_high_risk_metric_total', 0) >= 1
        assert summary.get('studio_structural_guarded_total', 0) >= 1
        assert summary.get('guardrail_posture') == 'attention_required'
        assert summary.get('authority_guard_human_required_total', 0) >= 1
        assert summary.get('authority_guard_blocked_total', 0) >= 1
        assert summary.get('resource_lock_conflict_total', 0) >= 1
        assert guardrail_summary.get('authority_guard_total', 0) >= 2

        pending_request = next(item for item in requests if item.get('request_id') == pending.metadata['request_id'])
        conflict_request = next(item for item in requests if item.get('request_id') == conflict.metadata['request_id'])
        blocked_request = next(item for item in requests if item.get('request_id') == blocked.metadata['request_id'])

        assert pending_request.get('authority_gate_triggered') is False
        assert pending_request.get('human_override_request_id')
        assert pending_request.get('resource_lock_status') == 'waiting_human'
        assert conflict_request.get('conflict_lock_key') == 'contract:C-GUARD-1'
        assert blocked_request.get('authority_gate_triggered') is True
        assert blocked_request.get('authority_gate_outcome') == 'blocked'

        assert any(alert.get('alert_id') == 'studio_structural_pressure' for alert in runtime_alerts)
        assert any(alert.get('alert_id') == 'authority_guard_attention' for alert in runtime_alerts)
        assert any(alert.get('alert_id') == 'resource_lock_pressure' for alert in runtime_alerts)


def test_dashboard_snapshot_surfaces_evidence_attention_and_registry_drift() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        builder = DashboardSnapshotBuilder(config=config)

        payload = {
            'role_name': 'Trust Drift Dashboard Analyst',
            'purpose': 'Review trusted publication drift visibility.',
            'reporting_line': 'LEGAL',
            'business_domain': 'legal_operations',
            'operating_mode': 'indirect',
            'assigned_user_id': 'LEGAL_MANAGER_20',
            'executive_owner_id': 'EXEC_OWNER',
            'seat_id': 'OPS-DASH-TRUST',
            'responsibilities': ['review incoming contracts', 'flag risk'],
            'allowed_actions': ['review_contract', 'flag_risk', 'advise_compliance'],
            'forbidden_actions': ['sign_contract'],
            'wait_human_actions': [],
            'handled_resources': ['contract'],
            'financial_sensitivity': 'medium',
            'legal_sensitivity': 'high',
            'compliance_sensitivity': 'high',
        }

        created = builder.app.role_private_studio.create_request(payload, requested_by='EXEC_OWNER')
        builder.app.role_private_studio.review_request(created['request_id'], reviewer='EXEC_OWNER', decision='approve', note='Approved for publish.')
        published = builder.app.role_private_studio.publish_request(created['request_id'], published_by='EXEC_OWNER')
        role_path = Path(published['publish_artifact']['role_path'])
        role_path.write_text(role_path.read_text(encoding='utf-8') + '\n# trust drift\n', encoding='utf-8')
        builder.app.create_evidence_pack(requested_by='EXEC_OWNER')

        snapshot = builder.build()
        studio_summary = snapshot.get('role_private_studio', {}).get('summary', {})
        evidence_summary = snapshot.get('evidence_exports', {}).get('summary', {})
        summary = snapshot.get('summary', {})
        runtime_alerts = snapshot.get('runtime_alerts', [])

        assert studio_summary.get('trust_attention_total', 0) >= 1
        assert studio_summary.get('published_live_hash_verified_total', 0) == 0
        assert summary.get('studio_trust_attention_total', 0) >= 1
        assert summary.get('studio_live_hash_verified_total', 0) == 0
        assert evidence_summary.get('attention_total', 0) >= 1
        assert evidence_summary.get('trusted_role_mismatch_total', 0) >= 1
        assert evidence_summary.get('posture') == 'attention_required'
        assert summary.get('evidence_posture') == 'attention_required'
        assert summary.get('evidence_attention_total', 0) >= 1
        assert summary.get('evidence_trusted_role_mismatch_total', 0) >= 1
        assert any(alert.get('alert_id') == 'studio_trusted_registry_drift' for alert in runtime_alerts)
        assert any(alert.get('alert_id') == 'evidence_export_attention' for alert in runtime_alerts)


def test_dashboard_snapshot_exposes_command_surface_summary() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        snapshot = DashboardSnapshotBuilder(config=config).build()

        surface = snapshot.get('command_surface', {})
        posture = surface.get('posture_summary', {}) if isinstance(surface.get('posture_summary', {}), dict) else {}
        quick_links = surface.get('quick_links', []) if isinstance(surface.get('quick_links', []), list) else []

        assert surface.get('organization_name')
        assert posture.get('operating_mode') == 'Governance-first'
        assert posture.get('operating_status') in {'stable', 'guarded'}
        assert isinstance(posture.get('ai_actions_running'), int)
        assert isinstance(posture.get('attention_items_total'), int)
        assert isinstance(surface.get('next_actions', []), list)
        assert isinstance(surface.get('ai_activity_feed', []), list)
        assert isinstance(surface.get('department_quick_access', []), list)
        assert [item.get('view') for item in quick_links] == ['requests', 'cases', 'documents', 'actions']



def test_command_surface_prioritizes_active_department_quick_access_for_compact_surfaces() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        builder = DashboardSnapshotBuilder(config=config)

        surface = builder.command_surface(
            assignment_queue={
                'items': [
                    {'team_label': 'Operations', 'status': 'human_required', 'priority': 'critical', 'age_hours': 12},
                    {'team_label': 'Operations', 'status': 'blocked', 'priority': 'high', 'age_hours': 4},
                    {'team_label': 'Finance', 'status': 'in_progress', 'priority': 'high', 'age_hours': 8},
                    {'team_label': 'Vendor Risk', 'status': 'human_required', 'priority': 'critical', 'age_hours': 6},
                    {'team_label': 'HR', 'status': 'queued', 'priority': 'medium', 'age_hours': 1},
                ],
                'summary': {},
            },
            master_data={
                'summary': {'organization_name': 'Tawan Company'},
                'teams': [
                    {'team_id': 'finance', 'label': 'Finance', 'member_ids': ['P1', 'P2'], 'seat_ids': ['S1', 'S2']},
                    {'team_id': 'hr', 'label': 'HR', 'member_ids': ['P3'], 'seat_ids': ['S3']},
                    {'team_id': 'legal', 'label': 'Legal', 'member_ids': ['P4'], 'seat_ids': ['S4']},
                    {'team_id': 'operations', 'label': 'Operations', 'member_ids': ['P5', 'P6', 'P7'], 'seat_ids': ['S5', 'S6']},
                    {'team_id': 'it', 'label': 'IT', 'member_ids': ['P8'], 'seat_ids': ['S7']},
                    {'team_id': 'audit', 'label': 'Audit', 'member_ids': ['P9'], 'seat_ids': ['S8']},
                    {'team_id': 'procurement', 'label': 'Procurement', 'member_ids': ['P10'], 'seat_ids': ['S9']},
                ],
            },
            actions={'items': [], 'summary': {}},
            evidence_exports={'summary': {}},
            runtime_health={'audit_integrity': {}},
            go_live_readiness={'status': 'ready'},
            operator_queue_health={'items': []},
            owner_registration={'organization_name': 'Tawan Company'},
        )

        quick_access = surface.get('department_quick_access', [])

        assert len(quick_access) == 6
        assert [item.get('label') for item in quick_access[:4]] == ['Operations', 'Vendor Risk', 'Finance', 'HR']
        assert next(item for item in quick_access if item.get('label') == 'Vendor Risk').get('assignment_total') == 1


def test_dashboard_service_marks_control_room_access_for_founder_admin_and_it_roles() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        service = DashboardService(config=config)

        owner_payload = service.dashboard(_build_profile('owner'))
        admin_payload = service.dashboard(AccessProfile(
            profile_id='admin-test',
            display_name='Admin',
            role_name='admin',
            permissions={'*'},
        ))
        it_payload = service.dashboard(AccessProfile(
            profile_id='it-test',
            display_name='IT',
            role_name='it',
            permissions={'ops.manage', 'health.read', 'audit.read'},
        ))
        operator_payload = service.dashboard(_build_profile('operator'))
        auditor_payload = service.dashboard(_build_profile('auditor'))

        assert owner_payload['session']['control_room_access'] is True
        assert owner_payload['session']['setup_assistant_access'] is True
        assert owner_payload['session']['persona'] == 'founder'
        assert admin_payload['session']['control_room_access'] is True
        assert admin_payload['session']['setup_assistant_access'] is True
        assert admin_payload['session']['persona'] == 'admin'
        assert it_payload['session']['control_room_access'] is True
        assert it_payload['session']['setup_assistant_access'] is True
        assert it_payload['session']['persona'] == 'admin'
        assert operator_payload['session']['control_room_access'] is False
        assert operator_payload['session']['setup_assistant_access'] is False
        assert operator_payload['session']['persona'] == 'operator'
        assert auditor_payload['session']['control_room_access'] is False
        assert auditor_payload['session']['setup_assistant_access'] is False
        assert auditor_payload['session']['persona'] == 'executive'
        assert owner_payload['session']['private_runtime_mode'] == 'private_first'
        assert owner_payload['session']['tablet_focus_title'] == 'Organization command'
        assert owner_payload['session']['tablet_primary_views'][0] == 'overview'
        assert owner_payload['session']['tablet_lane_emphasis']['requests']['rank'] == 'primary'
        assert admin_payload['session']['tablet_focus_title'] == 'Runtime stability and governance pressure'
        assert admin_payload['session']['tablet_primary_views'][0] == 'overview'
        assert admin_payload['session']['tablet_lane_emphasis']['actions']['rank'] == 'primary'
        assert operator_payload['session']['tablet_focus_title'] == 'Assignments and governed follow-through'
        assert operator_payload['session']['tablet_primary_views'][0] == 'requests'
        assert operator_payload['session']['tablet_lane_emphasis']['requests']['label'] == 'Start here'
        assert auditor_payload['session']['tablet_focus_title'] == 'Department direction'
        assert auditor_payload['session']['session_ttl_minutes'] == config.session_ttl_minutes
        assert auditor_payload['session']['session_idle_timeout_minutes'] == config.session_idle_timeout_minutes
        assert auditor_payload['session']['session_continuity_status'] == 'standby'
        assert auditor_payload['session']['session_continuity_action'] == 'reconnect_session'


def test_dashboard_service_surfaces_private_session_continuity_for_active_sessions() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        service = DashboardService(config=config)
        profile = _build_profile('operator')
        state, _token = service.access_control.session_manager.issue(profile, auth_method='access_token')

        payload = service.dashboard(profile)
        session = payload['session']

        assert session['session_status'] == 'active'
        assert session['active_session_count'] >= 1
        assert session['session_created_at'] == state.created_at
        assert session['session_last_seen_at'] == state.last_seen_at
        assert session['session_expires_at'] == state.expires_at
        assert session['session_idle_expires_at'] == state.idle_expires_at
        assert session['session_auth_method'] == 'access_token'
        assert session['session_continuity_status'] == 'ready'
        assert session['session_continuity_action'] == 'monitor'


def test_dashboard_service_marks_private_session_as_renewable_when_idle_window_is_short() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        service = DashboardService(config=config)
        profile = _build_profile('operator')
        state, _token = service.access_control.session_manager.issue(profile, auth_method='access_token')

        hot_session = service.access_control.session_manager._sessions[state.session_id]
        now = datetime.now(timezone.utc)
        hot_session.last_seen_at = now.isoformat()
        hot_session.idle_expires_at = (now + timedelta(seconds=90)).isoformat()
        hot_session.expires_at = (now + timedelta(minutes=40)).isoformat()
        service.access_control.session_manager._persist()

        payload = service.dashboard(profile)
        session = payload['session']

        assert session['session_status'] == 'active'
        assert session['session_continuity_status'] == 'idle_lock_soon'
        assert session['session_continuity_action'] == 'renew_session'
        assert session['session_continuity_tone'] == 'warning'
        assert int(session['session_idle_remaining_seconds']) <= 120
        assert int(session['session_signed_remaining_seconds']) > 0


def test_dashboard_service_operations_include_runtime_performance_baseline() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        service = DashboardService(config=config)

        operations = service.operations(limit=5)

        assert isinstance(operations, dict)
        assert 'runtime_performance_baseline' in operations
        baseline = operations.get('runtime_performance_baseline', {})
        assert isinstance(baseline, dict)
        assert baseline.get('status') in {'missing', 'ready', 'warning', 'critical'}
        assert isinstance(baseline.get('available'), bool)
