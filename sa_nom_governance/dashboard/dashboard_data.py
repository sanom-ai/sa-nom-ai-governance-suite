from datetime import datetime, timezone
from math import ceil
from pathlib import Path

from sa_nom_governance.api.api_engine import EngineApplication, build_engine_app
from sa_nom_governance.compliance.retention_manager import RetentionManager
from sa_nom_governance.deployment.deployment_profile import build_deployment_report
from sa_nom_governance.deployment.go_live_readiness import build_go_live_readiness
from sa_nom_governance.ptag.role_loader import RoleLoader
from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.utils.registry import RoleRegistry


class DashboardSnapshotBuilder:
    def __init__(self, config: AppConfig | None = None, app: EngineApplication | None = None, registry: RoleRegistry | None = None, loader: RoleLoader | None = None) -> None:
        self.config = config or AppConfig()
        self.app = app or build_engine_app(self.config)
        self.registry = registry or RoleRegistry(self.config.roles_dir, manifest_path=self.config.trusted_registry_manifest_path, cache_path=self.config.trusted_registry_cache_path, signing_key=self.config.trusted_registry_signing_key, signature_required=self.config.trusted_registry_signature_required)
        self.loader = loader or RoleLoader(self.registry)
        self.retention_manager = RetentionManager(self.config)
        self.access_control = self.app.access_control

    def build(self) -> dict[str, object]:
        audit_entries = self.list_audit(limit=200)
        overrides = self.list_overrides()
        locks = self.list_locks()
        requests = self.list_requests(audit_entries=audit_entries, limit=200)
        guardrail_surface = self.guardrail_surface(requests=requests, overrides=overrides, locks=locks)
        raw_roles = self.app.list_roles()
        access_control_health = self.access_control.health()
        evidence_summary = self.app.evidence_pack_summary()
        app_health = self.app.health(
            roles=raw_roles,
            access_control_health=access_control_health,
            evidence_summary=evidence_summary,
        )
        compliance = self.compliance_snapshot(
            roles=raw_roles,
            runtime_health=app_health,
            access_control_health=access_control_health,
            evidence_summary=evidence_summary,
        )
        roles = self.list_roles(roles=raw_roles, compliance_snapshot=compliance)
        sessions = self.list_sessions()
        retention = self.retention_report()
        retention_plan = self.retention_plan()
        role_private_studio = self.role_private_studio()
        human_ask = self.human_ask()
        owner_registration = self.owner_registration()
        deployment_profile = build_deployment_report(self.config).to_dict()
        go_live_readiness = self.go_live_readiness(
            app_health=app_health,
            access_control_health=access_control_health,
            studio_snapshot=role_private_studio,
            deployment_report=deployment_profile,
        )
        operational_readiness = self.app.operational_readiness(limit=50, health=app_health)
        operator_decision_lanes = self.build_operator_decision_lanes(operational_readiness)
        operations = self.operations()
        first_run_readiness = self.first_run_readiness(
            owner_registration=owner_registration,
            go_live_readiness=go_live_readiness,
            operational_readiness=operational_readiness,
            operations=operations,
        )
        operations['first_run_action_center'] = self.first_run_action_center(
            first_run_readiness=first_run_readiness,
            go_live_readiness=go_live_readiness,
            operations=operations,
        )
        evidence_exports = self.evidence_exports(summary=evidence_summary)
        integrations = self.integrations()
        model_providers = self.model_providers(health=app_health.get('model_providers', {}))
        operator_alert_policy = self.config.operator_alert_policy()
        operator_queue_health = self.operator_queue_health(
            overrides=overrides,
            human_ask=human_ask,
            operational_readiness=operational_readiness,
            policy=operator_alert_policy,
        )
        unified_work_inbox = self.unified_work_inbox(
            overrides=overrides,
            human_ask=human_ask,
            role_private_studio=role_private_studio,
            operational_readiness=operational_readiness,
            operator_queue_health=operator_queue_health,
            operator_decision_lanes=operator_decision_lanes,
        )
        cases = self.case_backbone(
            requests=requests,
            overrides=overrides,
            human_ask=human_ask,
            role_private_studio=role_private_studio,
            audit_entries=audit_entries,
        )
        self._attach_case_refs(
            requests=requests,
            overrides=overrides,
            human_ask=human_ask,
            role_private_studio=role_private_studio,
            cases=cases,
        )
        operator_notification_center = self.operator_notification_center(
            queue_health=operator_queue_health,
            policy=operator_alert_policy,
        )
        operator_notification_delivery_readiness = self.operator_notification_delivery_readiness(
            notification_center=operator_notification_center,
            integrations=integrations,
        )
        runtime_alerts = self.runtime_alerts(
            human_ask=human_ask,
            role_private_studio=role_private_studio,
            evidence_exports=evidence_exports,
            go_live_readiness=go_live_readiness,
            operational_readiness=operational_readiness,
            operator_queue_health=operator_queue_health,
            operator_notification_center=operator_notification_center,
            guardrail_surface=guardrail_surface,
        )
        runtime_health = self.runtime_health(
            roles=roles,
            go_live_readiness=go_live_readiness,
            owner_registration=owner_registration,
            app_health=app_health,
            access_control_health=access_control_health,
            deployment_profile=deployment_profile,
        )
        governance_materials = runtime_health.get('governance_materials', {}) if isinstance(runtime_health.get('governance_materials', {}), dict) else {}
        role_library = runtime_health.get('role_library', {}) if isinstance(runtime_health.get('role_library', {}), dict) else {}
        role_hierarchy = runtime_health.get('role_hierarchy', {}) if isinstance(runtime_health.get('role_hierarchy', {}), dict) else {}
        studio_summary = role_private_studio.get('summary', {}) if isinstance(role_private_studio.get('summary', {}), dict) else {}
        guardrail_summary = guardrail_surface.get('summary', {}) if isinstance(guardrail_surface.get('summary', {}), dict) else {}

        conflicts = [request for request in requests if request['outcome'] == 'conflicted']
        escalated = [request for request in requests if request['outcome'] in {'escalated', 'waiting_human'}]
        pending_overrides = [item for item in overrides if item['status'] == 'pending']

        return {
            'generated_at': self._utc_now(),
            'product': 'SA-NOM AI Governance Suite',
            'environment': self.config.environment,
            'owner_registration': owner_registration,
            'summary': {
                'requests_total': len(requests),
                'pending_overrides': len(pending_overrides),
                'active_locks': len(locks),
                'conflicts_total': len(conflicts),
                'escalated_total': len(escalated),
                'audit_events': len(audit_entries),
                'studio_requests_total': studio_summary.get('requests_total', 0),
                'studio_ready_to_publish_total': studio_summary.get('ready_to_publish_total', 0),
                'studio_publisher_ready_total': int(studio_summary.get('publisher_ready_total', 0) or 0),
                'studio_manual_override_total': int(studio_summary.get('manual_override_total', 0) or 0),
                'studio_restored_request_total': int(studio_summary.get('restored_request_total', 0) or 0),
                'studio_registry_verified_total': int(studio_summary.get('published_registry_verified_total', 0) or 0),
                'studio_live_hash_verified_total': int(studio_summary.get('published_live_hash_verified_total', 0) or 0),
                'studio_trusted_live_total': int(studio_summary.get('trusted_live_total', 0) or 0),
                'studio_trust_attention_total': int(studio_summary.get('trust_attention_total', 0) or 0),
                'studio_published_current_revision_total': int(studio_summary.get('published_current_revision_total', 0) or 0),
                'studio_revision_drift_total': int(studio_summary.get('revision_drift_total', 0) or 0),
                'studio_structural_guarded_total': int(studio_summary.get('structural_guarded_total', 0) or 0),
                'studio_structural_blocked_total': int(studio_summary.get('structural_blocked_total', 0) or 0),
                'studio_structural_ready_total': int(studio_summary.get('structural_ready_total', 0) or 0),
                'studio_structural_review_total': int(studio_summary.get('structural_review_total', 0) or 0),
                'studio_pt_oss_watch_total': int(studio_summary.get('pt_oss_watch_total', 0) or 0),
                'studio_pt_oss_elevated_total': int(studio_summary.get('pt_oss_elevated_total', 0) or 0),
                'studio_pt_oss_healthy_total': int(studio_summary.get('pt_oss_healthy_total', 0) or 0),
                'studio_pt_oss_critical_total': int(studio_summary.get('pt_oss_critical_total', 0) or 0),
                'studio_pt_oss_public_sector_total': int(studio_summary.get('pt_oss_public_sector_mode_total', 0) or 0),
                'studio_pt_oss_blocking_issue_total': int(studio_summary.get('pt_oss_blocking_issue_total', 0) or 0),
                'studio_pt_oss_high_risk_metric_total': int(studio_summary.get('pt_oss_high_risk_metric_total', 0) or 0),
                'human_ask_sessions_total': human_ask.get('summary', {}).get('sessions_total', 0),
                'human_ask_callable_total': human_ask.get('summary', {}).get('callable_total', 0),
                'human_ask_low_confidence_total': int(human_ask.get('summary', {}).get('low_confidence_total', 0) or 0),
                'human_ask_guarded_confidence_total': int(human_ask.get('summary', {}).get('guarded_confidence_total', 0) or 0),
                'human_ask_stale_total': int(human_ask.get('summary', {}).get('stale_total', 0) or 0),
                'human_ask_human_gated_total': int(human_ask.get('summary', {}).get('human_gated_posture_total', 0) or 0),
                'go_live_status': go_live_readiness.get('status', 'blocked'),
                'privileged_operations_status': go_live_readiness.get('privileged_operations', {}).get('status', 'unknown'),
                'runtime_alert_total': len(runtime_alerts),
                'runtime_alert_critical_total': sum(
                    1 for item in runtime_alerts if item.get('tone') == 'danger'
                ),
                'operational_readiness_status': operational_readiness.get('status', 'unknown'),
                'workflow_backlog_total': operational_readiness.get('workflow', {}).get('backlog_total', 0),
                'human_inbox_open_total': operational_readiness.get('human_inbox', {}).get('open_total', 0),
                'recovery_pending_total': operational_readiness.get('runtime_recovery', {}).get('pending_total', 0),
                'dead_letter_total': operational_readiness.get('runtime_recovery', {}).get('dead_letter_total', 0),
                'governed_autonomy_status': str(operational_readiness.get('governed_autonomy', {}).get('status', 'unknown')),
                'governed_autonomy_action': str(operational_readiness.get('governed_autonomy', {}).get('recommended_runtime_action', 'none')),
                'autonomous_inflight_total': int(operational_readiness.get('governed_autonomy', {}).get('autonomous_inflight_total', 0) or 0),
                'human_gate_open_total': int(operational_readiness.get('governed_autonomy', {}).get('human_gate_open_total', 0) or 0),
                'fail_closed_workflow_total': int(operational_readiness.get('governed_autonomy', {}).get('fail_closed_total', 0) or 0),
                'guardrail_posture': str(guardrail_surface.get('posture', 'unknown')),
                'authority_guard_total': int(guardrail_summary.get('authority_guard_total', 0) or 0),
                'authority_guard_human_required_total': int(guardrail_summary.get('authority_guard_human_required_total', 0) or 0),
                'authority_guard_blocked_total': int(guardrail_summary.get('authority_guard_blocked_total', 0) or 0),
                'authority_guard_resumed_total': int(guardrail_summary.get('authority_guard_resumed_total', 0) or 0),
                'resource_lock_active_total': int(guardrail_summary.get('resource_lock_active_total', 0) or 0),
                'resource_lock_waiting_total': int(guardrail_summary.get('resource_lock_waiting_total', 0) or 0),
                'resource_lock_conflict_total': int(guardrail_summary.get('resource_lock_conflict_total', 0) or 0),
                'operator_human_required_total': sum(
                    1 for lane in operator_decision_lanes if lane.get('disposition') == 'human_required'
                ),
                'operator_blocked_total': sum(
                    1 for lane in operator_decision_lanes if lane.get('disposition') == 'blocked'
                ),
                'backups_total': operations.get('summary', {}).get('backups_total', 0),
                'usability_proof_status': operations.get('usability_proof', {}).get('status', 'missing'),
                'usability_proof_available': bool(operations.get('usability_proof', {}).get('available', False)),
                'usability_proof_criteria_total': int(operations.get('usability_proof', {}).get('criteria_total', 0) or 0),
                'usability_proof_criteria_passed_total': int(operations.get('usability_proof', {}).get('criteria_passed_total', 0) or 0),
                'usability_proof_criteria_failed_total': int(operations.get('usability_proof', {}).get('criteria_failed_total', 0) or 0),
                'quick_start_doctor_status': str(operations.get('quick_start_doctor', {}).get('status', 'missing')),
                'runtime_performance_status': str(operations.get('runtime_performance_baseline', {}).get('status', 'missing')),
                'runtime_performance_dashboard_elapsed_ms': float((operations.get('runtime_performance_baseline', {}) or {}).get('dashboard_snapshot_elapsed_ms', 0.0) or 0.0),
                'first_run_readiness_status': str(first_run_readiness.get('status', 'blocked')),
                'first_run_blockers_total': int(first_run_readiness.get('blockers_total', 0) or 0),
                'first_run_advisories_total': int(first_run_readiness.get('advisories_total', 0) or 0),
                'first_run_action_items_total': int((operations.get('first_run_action_center', {}) or {}).get('items_total', 0) or 0),
                'first_run_action_required_total': int((operations.get('first_run_action_center', {}) or {}).get('required_total', 0) or 0),
                'frameworks_total': compliance.get('summary', {}).get('frameworks_total', 0),
                'evidence_exports_total': evidence_exports.get('summary', {}).get('exports_total', 0),
                'workflow_proof_total': int(evidence_exports.get('summary', {}).get('workflow_proof_total', 0) or 0),
                'evidence_posture': str(evidence_exports.get('summary', {}).get('posture', 'missing')),
                'evidence_attention_total': int(evidence_exports.get('summary', {}).get('attention_total', 0) or 0),
                'evidence_tamper_evident_total': int(evidence_exports.get('summary', {}).get('tamper_evident_total', 0) or 0),
                'evidence_trusted_role_mismatch_total': int(evidence_exports.get('summary', {}).get('trusted_role_mismatch_total', 0) or 0),
                'integration_targets_total': integrations.get('summary', {}).get('targets_total', 0),
                'integration_deliveries_total': integrations.get('summary', {}).get('deliveries_total', 0),
                'integration_failures_total': integrations.get('summary', {}).get('failed_total', 0),
                'integration_outbox_total': integrations.get('summary', {}).get('outbox_total', 0),
                'model_providers_configured_total': model_providers.get('configured_providers', 0),
                'operator_attention_total': sum(1 for item in operator_queue_health.get('items', []) if item.get('status') in {'warning', 'critical', 'stale'}),
                'operator_critical_total': sum(1 for item in operator_queue_health.get('items', []) if item.get('status') in {'critical', 'stale'}),
                'work_inbox_open_total': int((unified_work_inbox.get('summary', {}) or {}).get('open_total', 0) or 0),
                'work_inbox_attention_total': int((unified_work_inbox.get('summary', {}) or {}).get('attention_total', 0) or 0),
                'work_inbox_human_required_total': int((unified_work_inbox.get('summary', {}) or {}).get('human_required_total', 0) or 0),
                'work_inbox_blocked_total': int((unified_work_inbox.get('summary', {}) or {}).get('blocked_total', 0) or 0),
                'work_inbox_primary_view': str((unified_work_inbox.get('summary', {}) or {}).get('primary_view', 'overview')),
                'cases_total': int((cases.get('summary', {}) or {}).get('cases_total', 0) or 0),
                'cases_attention_total': int((cases.get('summary', {}) or {}).get('attention_total', 0) or 0),
                'cases_human_required_total': int((cases.get('summary', {}) or {}).get('human_required_total', 0) or 0),
                'cases_blocked_total': int((cases.get('summary', {}) or {}).get('blocked_total', 0) or 0),
                'cases_primary_view': str((cases.get('summary', {}) or {}).get('primary_view', 'overview')),
                'operator_notification_candidates_total': int(operator_notification_center.get('dispatch_candidates_total', 0) or 0),
                'operator_notification_channels_total': int(operator_notification_center.get('active_channel_total', 0) or 0),
                'operator_notification_posture': str(operator_notification_delivery_readiness.get('posture', 'unknown')),
                'operator_notification_external_ready': bool(operator_notification_delivery_readiness.get('external_routing_ready', False)),
                'governance_materials_status': str(governance_materials.get('status', 'unknown')),
                'invalid_roles_total': int(role_library.get('roles_invalid_total', 0) or 0),
                'invalid_hierarchy_entries_total': int(role_hierarchy.get('invalid_entries_total', 0) or 0),
            },
            'requests': requests[:50],
            'overrides': overrides[:50],
            'locks': locks[:50],
            'audit': audit_entries[:100],
            'roles': roles,
            'sessions': sessions[:100],
            'retention': retention,
            'retention_plan': retention_plan,
            'role_private_studio': role_private_studio,
            'human_ask': human_ask,
            'cases': cases,
            'operations': operations,
            'compliance': compliance,
            'evidence_exports': evidence_exports,
            'guardrail_surface': guardrail_surface,
            'integrations': integrations,
            'model_providers': model_providers,
            'operator_alert_policy': operator_alert_policy,
            'operator_queue_health': operator_queue_health,
            'unified_work_inbox': unified_work_inbox,
            'operator_notification_center': operator_notification_center,
            'operator_notification_delivery_readiness': operator_notification_delivery_readiness,
            'go_live_readiness': go_live_readiness,
            'operational_readiness': operational_readiness,
            'first_run_readiness': first_run_readiness,
            'operator_decision_lanes': operator_decision_lanes,
            'runtime_alerts': runtime_alerts,
            'runtime_health': runtime_health,
        }

    @staticmethod
    def build_operator_decision_lanes(operational_readiness: dict[str, object]) -> list[dict[str, object]]:
        actions = operational_readiness.get('action_required', [])
        action_list = [str(item) for item in actions if str(item)]
        action_set = set(action_list)

        lane_map = {
            'clearance_review': {
                'lane_id': 'clearance_review',
                'disposition': 'human_required',
                'priority': 1,
                'title': 'Clearance review required',
                'operator_action': 'Review clearance-bound decisions before runtime continues.',
                'default_view': 'human_ask',
                'governance_outcome': 'AI remains paused until a human grants or denies clearance.',
            },
            'human_decision': {
                'lane_id': 'human_decision',
                'disposition': 'human_required',
                'priority': 2,
                'title': 'Human decision required',
                'operator_action': 'Decide on queued human-only boundaries in the inbox.',
                'default_view': 'human_ask',
                'governance_outcome': 'AI resumes only after the decision is recorded.',
            },
            'recovery_resume': {
                'lane_id': 'recovery_resume',
                'disposition': 'blocked',
                'priority': 3,
                'title': 'Recovery resume required',
                'operator_action': 'Inspect failed/dead-letter recovery records and resume safely.',
                'default_view': 'conflicts',
                'governance_outcome': 'Runtime remains fail-closed on the affected path until recovered.',
            },
            'guarded_follow_up': {
                'lane_id': 'guarded_follow_up',
                'disposition': 'monitoring',
                'priority': 4,
                'title': 'Guarded follow-up pending',
                'operator_action': 'Review guarded follow-ups and confirm acceptable risk posture.',
                'default_view': 'overview',
                'governance_outcome': 'AI can continue within constraints while follow-up remains visible.',
            },
        }

        lanes = [lane_map[action] for action in action_list if action in lane_map]
        if not lanes:
            lanes.append(
                {
                    'lane_id': 'autonomy_ready',
                    'disposition': 'autonomy_ready',
                    'priority': 99,
                    'title': 'Autonomy ready',
                    'operator_action': 'No immediate human gate is open; continue governed execution.',
                    'default_view': 'overview',
                    'governance_outcome': 'AI continues inside policy contracts without human interruption.',
                }
            )

        # Keep any unknown runtime actions visible instead of silently dropping them.
        for action in sorted(action_set - set(lane_map.keys())):
            lanes.append(
                {
                    'lane_id': action,
                    'disposition': 'blocked',
                    'priority': 5,
                    'title': f'Unknown action: {action}',
                    'operator_action': 'Review runtime posture before continuing; this action is not mapped yet.',
                    'default_view': 'health',
                    'governance_outcome': 'Fail-closed posture: unknown action requires explicit human review.',
                }
            )

        lanes.sort(key=lambda item: (int(item.get('priority', 99)), str(item.get('lane_id', ''))))
        return lanes

    def list_requests(self, audit_entries: list[dict[str, object]] | None = None, limit: int = 200) -> list[dict[str, object]]:
        entries = audit_entries if audit_entries is not None else self.list_audit(limit=max(limit * 3, 100))
        requests: list[dict[str, object]] = []
        for entry in entries:
            metadata = entry.get('metadata', {}) if isinstance(entry.get('metadata', {}), dict) else {}
            context = metadata.get('context', {}) if isinstance(metadata.get('context', {}), dict) else {}
            if not context or str(entry.get('action', '')).startswith('override_'):
                continue
            context_metadata = context.get('metadata', {}) if isinstance(context.get('metadata', {}), dict) else {}
            consistency = context_metadata.get('request_consistency', {}) if isinstance(context_metadata.get('request_consistency', {}), dict) else {}
            role_transition = context.get('role_transition', {}) if isinstance(context.get('role_transition', {}), dict) else {}
            authority_gate = context_metadata.get('authority_gate', {}) if isinstance(context_metadata.get('authority_gate', {}), dict) else {}
            resource_lock = metadata.get('resource_lock', {}) if isinstance(metadata.get('resource_lock', {}), dict) else {}
            if not resource_lock:
                resource_lock = context_metadata.get('resource_lock', {}) if isinstance(context_metadata.get('resource_lock', {}), dict) else {}
            conflict_lock = metadata.get('conflict_lock', {}) if isinstance(metadata.get('conflict_lock', {}), dict) else {}
            if not conflict_lock:
                conflict_lock = context_metadata.get('conflict_lock', {}) if isinstance(context_metadata.get('conflict_lock', {}), dict) else {}
            human_override = metadata.get('human_override', {}) if isinstance(metadata.get('human_override', {}), dict) else {}
            if not human_override:
                human_override = context_metadata.get('human_override', {}) if isinstance(context_metadata.get('human_override', {}), dict) else {}
            authority_gate_triggered = bool(authority_gate.get('gate_triggered', False))
            requests.append(
                {
                    'request_id': context.get('request_id', 'unknown'),
                    'timestamp': entry.get('timestamp'),
                    'requester': context.get('requester', 'unknown'),
                    'active_role': entry.get('active_role'),
                    'action': entry.get('action'),
                    'outcome': entry.get('outcome'),
                    'reason': entry.get('reason'),
                    'policy_basis': metadata.get('decision_trace', {}).get('source_id'),
                    'risk_score': context.get('risk_score', 0.0),
                    'resource': self._resource_label(context.get('payload', {})),
                    'decision_trace': metadata.get('decision_trace', {}),
                    'authority_gate_triggered': authority_gate_triggered,
                    'authority_gate_outcome': str(authority_gate.get('outcome', 'passthrough' if not authority_gate_triggered else 'unknown')),
                    'authority_gate_source_id': authority_gate.get('source_id'),
                    'authority_gate_reason': authority_gate.get('reason'),
                    'authority_gate_requires_human_confirmation': bool(authority_gate.get('requires_human_confirmation', False)),
                    'authority_gate_decision_mode': str(authority_gate.get('decision_mode', 'policy_fallback') or 'policy_fallback'),
                    'authority_gate_resume_request_id': authority_gate.get('resumed_from_override_request_id'),
                    'resource_lock_status': resource_lock.get('status'),
                    'resource_lock_key': resource_lock.get('resource_key'),
                    'resource_lock_owner_request_id': resource_lock.get('owner_request_id'),
                    'conflict_lock_status': conflict_lock.get('status'),
                    'conflict_lock_key': conflict_lock.get('resource_key'),
                    'conflict_lock_owner_request_id': conflict_lock.get('owner_request_id'),
                    'human_override_request_id': human_override.get('request_id'),
                    'human_override_status': human_override.get('status'),
                    'human_override_approver_role': human_override.get('approver_role'),
                    'idempotency_status': consistency.get('idempotency_status', 'none'),
                    'ordering_status': consistency.get('ordering_status', 'none'),
                    'event_stream': consistency.get('event_stream', '-'),
                    'event_sequence': consistency.get('event_sequence', '-'),
                    'workflow_id': str(
                        (
                            context_metadata.get('execution_plan', {})
                            if isinstance(context_metadata.get('execution_plan', {}), dict)
                            else {}
                        ).get('plan_id', '')
                    ),
                    'previous_role': role_transition.get('previous_role'),
                    'new_role': role_transition.get('new_role'),
                    'requested_role': role_transition.get('requested_role'),
                    'activation_source': role_transition.get('activation_source'),
                    'switch_reason': role_transition.get('switch_reason'),
                    'escalated_to': role_transition.get('escalated_to'),
                    'transition_rule_id': role_transition.get('transition_rule_id'),
                    'transition_disposition': role_transition.get('transition_disposition'),
                }
            )
        return requests[:limit]

    def list_overrides(self, status: str | None = None, limit: int = 100) -> list[dict[str, object]]:
        return self.app.list_overrides(status=status)[:limit]

    def list_locks(self, status: str | None = None, limit: int = 100) -> list[dict[str, object]]:
        return self.app.list_locks(status=status)[:limit]

    def guardrail_surface(
        self,
        *,
        requests: list[dict[str, object]],
        overrides: list[dict[str, object]],
        locks: list[dict[str, object]],
        limit: int = 25,
    ) -> dict[str, object]:
        authority_guarded = [
            item
            for item in requests
            if bool(item.get('authority_gate_triggered', False)) or bool(item.get('human_override_request_id'))
        ]
        authority_human_required = [
            item
            for item in requests
            if bool(item.get('authority_gate_requires_human_confirmation', False))
            or bool(item.get('human_override_request_id'))
            or str(item.get('outcome', '')) in {'waiting_human', 'human_required'}
        ]
        authority_blocked = [
            item
            for item in authority_guarded
            if str(item.get('authority_gate_outcome', '')) == 'blocked'
            or str(item.get('outcome', '')) == 'blocked'
        ]
        authority_resumed = [item for item in authority_guarded if str(item.get('authority_gate_source_id', '')) == 'human_override_resume']
        waiting_locks = [item for item in locks if str(item.get('status', '')) == 'waiting_human']
        active_locks = [item for item in locks if str(item.get('status', '')) == 'active']
        conflict_requests = [item for item in requests if item.get('conflict_lock_key') not in {None, ''}]
        if authority_blocked or conflict_requests:
            posture = 'attention_required'
        elif authority_human_required or waiting_locks or active_locks or overrides:
            posture = 'governed'
        else:
            posture = 'ready'
        items: list[dict[str, object]] = []
        if authority_human_required:
            latest = authority_human_required[0]
            items.append(
                {
                    'lane_id': 'authority_human_confirmation',
                    'status': 'warning',
                    'title': 'Authority guard is holding requests for human confirmation',
                    'detail': latest.get('reason') or latest.get('authority_gate_reason') or 'Authority gate requires review.',
                    'request_total': len(authority_human_required),
                    'view': 'requests',
                }
            )
        if authority_blocked:
            latest = authority_blocked[0]
            items.append(
                {
                    'lane_id': 'authority_blocked',
                    'status': 'critical',
                    'title': 'Authority guard blocked governed requests',
                    'detail': latest.get('reason') or latest.get('authority_gate_reason') or 'Authority contract blocked execution.',
                    'request_total': len(authority_blocked),
                    'view': 'requests',
                }
            )
        if conflict_requests or waiting_locks:
            latest_conflict = conflict_requests[0] if conflict_requests else None
            latest_lock = waiting_locks[0] if waiting_locks else (active_locks[0] if active_locks else {})
            items.append(
                {
                    'lane_id': 'resource_lock_contention',
                    'status': 'critical' if conflict_requests else 'warning',
                    'title': 'Resource lock is actively governing concurrent access',
                    'detail': (
                        latest_conflict.get('conflict_lock_key')
                        if latest_conflict is not None
                        else latest_lock.get('resource_key')
                        or 'Governed resource lock is active.'
                    ),
                    'request_total': len(conflict_requests),
                    'waiting_lock_total': len(waiting_locks),
                    'view': 'requests',
                }
            )
        return {
            'posture': posture,
            'summary': {
                'posture': posture,
                'authority_guard_total': len(authority_guarded),
                'authority_guard_human_required_total': len(authority_human_required),
                'authority_guard_blocked_total': len(authority_blocked),
                'authority_guard_resumed_total': len(authority_resumed),
                'resource_lock_active_total': len(active_locks),
                'resource_lock_waiting_total': len(waiting_locks),
                'resource_lock_conflict_total': len(conflict_requests),
                'pending_override_total': sum(1 for item in overrides if str(item.get('status', '')) == 'pending'),
            },
            'items': items[:limit],
            'authority_requests': authority_guarded[:limit],
            'conflicted_requests': conflict_requests[:limit],
            'locks': locks[:limit],
        }

    def list_audit(self, limit: int = 200) -> list[dict[str, object]]:
        return self.app.list_audit(limit=limit)

    def list_sessions(self, status: str | None = None, limit: int = 100) -> list[dict[str, object]]:
        return self.app.list_sessions(status=status)[:limit]

    def list_roles(
        self,
        roles: list[dict[str, object]] | None = None,
        compliance_snapshot: dict[str, object] | None = None,
    ) -> list[dict[str, object]]:
        known_roles = [dict(role) for role in (roles if roles is not None else self.app.list_roles())]
        compliance = compliance_snapshot if compliance_snapshot is not None else self.app.compliance_snapshot(roles=known_roles)
        mapping_index = {item['role_id']: item.get('controls', []) for item in compliance.get('role_mappings', [])}
        for role in known_roles:
            role['control_refs'] = mapping_index.get(role['role_id'], [])
        return known_roles

    def role_private_studio(self, limit: int = 50) -> dict[str, object]:
        return self.app.studio_snapshot(limit=limit)

    def human_ask(self, limit: int = 50) -> dict[str, object]:
        return self.app.human_ask_snapshot(limit=limit)


    def case_backbone(
        self,
        *,
        requests: list[dict[str, object]],
        overrides: list[dict[str, object]],
        human_ask: dict[str, object],
        role_private_studio: dict[str, object],
        audit_entries: list[dict[str, object]],
        limit: int = 40,
    ) -> dict[str, object]:
        sessions = human_ask.get('sessions', []) if isinstance(human_ask.get('sessions', []), list) else []
        studio_requests = role_private_studio.get('requests', []) if isinstance(role_private_studio.get('requests', []), list) else []
        alias_to_case: dict[str, str] = {}
        cases: dict[str, dict[str, object]] = {}

        def case_shell(case_key: str) -> dict[str, object]:
            return {
                'case_key': case_key,
                'aliases': set(),
                'linked_request_ids': set(),
                'linked_override_ids': set(),
                'linked_session_ids': set(),
                'linked_workflow_ids': set(),
                'linked_studio_request_ids': set(),
                'timeline': [],
                'opened_at': None,
                'updated_at': None,
                'pending_override_total': 0,
                'waiting_human_total': 0,
                'blocked_total': 0,
                'attention_total': 0,
                'active_total': 0,
                'audit_event_total': 0,
            }

        def merge_case(target: dict[str, object], source: dict[str, object]) -> None:
            for field in [
                'aliases',
                'linked_request_ids',
                'linked_override_ids',
                'linked_session_ids',
                'linked_workflow_ids',
                'linked_studio_request_ids',
            ]:
                target[field].update(source[field])
            target['timeline'].extend(source['timeline'])
            for field in ['pending_override_total', 'waiting_human_total', 'blocked_total', 'attention_total', 'active_total', 'audit_event_total']:
                target[field] += int(source.get(field, 0) or 0)
            opened_at = [value for value in [target.get('opened_at'), source.get('opened_at')] if value]
            updated_at = [value for value in [target.get('updated_at'), source.get('updated_at')] if value]
            target['opened_at'] = min(opened_at) if opened_at else None
            target['updated_at'] = max(updated_at) if updated_at else None

        def ensure_case(aliases: list[str]) -> tuple[str, dict[str, object]]:
            normalized = [alias for alias in aliases if alias]
            existing_keys: list[str] = []
            for alias in normalized:
                case_key = alias_to_case.get(alias)
                if case_key and case_key not in existing_keys:
                    existing_keys.append(case_key)
            if not existing_keys:
                case_key = normalized[0] if normalized else f'synthetic:{len(cases) + 1}'
                cases[case_key] = case_shell(case_key)
            else:
                case_key = existing_keys[0]
                if case_key not in cases:
                    cases[case_key] = case_shell(case_key)
                for duplicate in existing_keys[1:]:
                    if duplicate == case_key or duplicate not in cases:
                        continue
                    merge_case(cases[case_key], cases.pop(duplicate))
                    for alias, mapped in list(alias_to_case.items()):
                        if mapped == duplicate:
                            alias_to_case[alias] = case_key
            case = cases[case_key]
            for alias in normalized:
                alias_to_case[alias] = case_key
                case['aliases'].add(alias)
            return case_key, case

        def touch_case(case: dict[str, object], *, timestamp: object, event: dict[str, object], request_id: str = '', override_id: str = '', session_id: str = '', workflow_id: str = '', studio_request_id: str = '', pending_override: bool = False, waiting_human: bool = False, blocked: bool = False, attention: bool = False, active: bool = False, audit_event: bool = False) -> None:
            stamp = str(timestamp or '').strip()
            if stamp:
                case['opened_at'] = min([value for value in [case.get('opened_at'), stamp] if value]) if case.get('opened_at') else stamp
                case['updated_at'] = max([value for value in [case.get('updated_at'), stamp] if value]) if case.get('updated_at') else stamp
            if request_id:
                case['linked_request_ids'].add(request_id)
            if override_id:
                case['linked_override_ids'].add(override_id)
            if session_id:
                case['linked_session_ids'].add(session_id)
            if workflow_id:
                case['linked_workflow_ids'].add(workflow_id)
            if studio_request_id:
                case['linked_studio_request_ids'].add(studio_request_id)
            if pending_override:
                case['pending_override_total'] += 1
            if waiting_human:
                case['waiting_human_total'] += 1
            if blocked:
                case['blocked_total'] += 1
            if attention:
                case['attention_total'] += 1
            if active:
                case['active_total'] += 1
            if audit_event:
                case['audit_event_total'] += 1
            case['timeline'].append(event)

        for item in requests:
            request_id = str(item.get('request_id', '') or '').strip()
            workflow_id = str(item.get('workflow_id', '') or '').strip()
            override_id = str(item.get('human_override_request_id', '') or '').strip()
            aliases = []
            if request_id:
                aliases.append(f'request:{request_id}')
            if workflow_id:
                aliases.append(f'workflow:{workflow_id}')
            if override_id:
                aliases.append(f'override:{override_id}')
            _, case = ensure_case(aliases)
            outcome = str(item.get('outcome', 'unknown') or 'unknown')
            touch_case(
                case,
                timestamp=item.get('timestamp'),
                request_id=request_id,
                workflow_id=workflow_id,
                override_id=override_id,
                blocked=outcome in {'blocked', 'conflicted'} or str(item.get('authority_gate_outcome', '')) == 'blocked',
                waiting_human=outcome in {'waiting_human', 'human_required'} or bool(item.get('human_override_request_id')),
                attention=outcome in {'escalated', 'waiting_human', 'human_required'} or bool(item.get('authority_gate_triggered')),
                active=True,
                event={
                    'timestamp': item.get('timestamp'),
                    'event_type': 'request',
                    'status': outcome,
                    'view': 'requests',
                    'reference': request_id or workflow_id or '-',
                    'title': f"{str(item.get('action', 'request') or 'request')} request",
                    'detail': str(item.get('reason') or item.get('switch_reason') or item.get('resource') or 'Governed request recorded in the runtime ledger.'),
                },
            )

        for item in overrides:
            override_id = str(item.get('request_id', '') or '').strip()
            origin_request_id = str(item.get('origin_request_id', item.get('request_id', '')) or '').strip()
            workflow_id = str(item.get('workflow_id', '') or '').strip()
            aliases = []
            if override_id:
                aliases.append(f'override:{override_id}')
            if origin_request_id:
                aliases.append(f'request:{origin_request_id}')
            if workflow_id:
                aliases.append(f'workflow:{workflow_id}')
            _, case = ensure_case(aliases)
            status = str(item.get('status', 'unknown') or 'unknown')
            touch_case(
                case,
                timestamp=item.get('resolved_at') or item.get('created_at'),
                request_id=origin_request_id,
                override_id=override_id,
                workflow_id=workflow_id,
                pending_override=status == 'pending',
                waiting_human=status == 'pending',
                blocked=status == 'vetoed',
                attention=status in {'pending', 'vetoed'},
                active=True,
                event={
                    'timestamp': item.get('resolved_at') or item.get('created_at'),
                    'event_type': 'override',
                    'status': status,
                    'view': 'overrides',
                    'reference': override_id or origin_request_id or '-',
                    'title': 'Human override decision',
                    'detail': str(item.get('reason') or item.get('required_by') or 'Human boundary state changed.'),
                },
            )

        for item in sessions:
            metadata = item.get('metadata', {}) if isinstance(item.get('metadata', {}), dict) else {}
            decision_summary = item.get('decision_summary', {}) if isinstance(item.get('decision_summary', {}), dict) else {}
            participant = item.get('participant', {}) if isinstance(item.get('participant', {}), dict) else {}
            summary = item.get('summary', {}) if isinstance(item.get('summary', {}), dict) else {}
            inbox = metadata.get('human_decision_inbox', {}) if isinstance(metadata.get('human_decision_inbox', {}), dict) else {}
            execution_plan = metadata.get('execution_plan', {}) if isinstance(metadata.get('execution_plan', {}), dict) else {}
            if not execution_plan:
                execution_plan = inbox.get('execution_plan', {}) if isinstance(inbox.get('execution_plan', {}), dict) else {}
            session_id = str(item.get('session_id', '') or '').strip()
            origin_request_id = str(metadata.get('origin_request_id', metadata.get('request_id', '')) or '').strip()
            workflow_id = str(execution_plan.get('plan_id', summary.get('queue_execution_plan_id', '')) or '').strip()
            studio_request_id = str(metadata.get('studio_request_id', '') or '').strip()
            aliases = []
            if session_id:
                aliases.append(f'session:{session_id}')
            if origin_request_id:
                aliases.append(f'request:{origin_request_id}')
            if workflow_id:
                aliases.append(f'workflow:{workflow_id}')
            if studio_request_id:
                aliases.append(f'studio:{studio_request_id}')
            _, case = ensure_case(aliases)
            status = str(item.get('status', 'unknown') or 'unknown')
            scope_status = str((decision_summary.get('metadata', {}) if isinstance(decision_summary.get('metadata', {}), dict) else {}).get('scope_status', ''))
            posture = str(summary.get('governed_reporting_posture', '') or '')
            touch_case(
                case,
                timestamp=item.get('updated_at') or item.get('created_at'),
                request_id=origin_request_id,
                session_id=session_id,
                workflow_id=workflow_id,
                studio_request_id=studio_request_id,
                waiting_human=status in {'waiting_human', 'escalated'} or scope_status == 'human_only_boundary',
                attention=status in {'waiting_human', 'escalated'} or posture in {'guarded_follow_up', 'human_gated'} or summary.get('confidence_band') == 'guarded',
                active=True,
                event={
                    'timestamp': item.get('updated_at') or item.get('created_at'),
                    'event_type': 'human_ask',
                    'status': status,
                    'view': 'human_ask',
                    'reference': session_id or origin_request_id or workflow_id or '-',
                    'title': 'Human Ask record',
                    'detail': str(participant.get('display_name') or participant.get('role_id') or item.get('mode') or 'Governed record captured.'),
                },
            )

        for item in studio_requests:
            studio_request_id = str(item.get('request_id', '') or '').strip()
            aliases = [f'studio:{studio_request_id}'] if studio_request_id else []
            _, case = ensure_case(aliases)
            status = str(item.get('status', 'unknown') or 'unknown')
            structured_jd = item.get('structured_jd', {}) if isinstance(item.get('structured_jd', {}), dict) else {}
            publish_readiness = item.get('publish_readiness', {}) if isinstance(item.get('publish_readiness', {}), dict) else {}
            touch_case(
                case,
                timestamp=item.get('updated_at') or item.get('created_at'),
                studio_request_id=studio_request_id,
                attention=status in {'changes_requested'} or str(publish_readiness.get('status', '')) in {'guarded', 'blocked'},
                active=True,
                event={
                    'timestamp': item.get('updated_at') or item.get('created_at'),
                    'event_type': 'studio',
                    'status': status,
                    'view': 'studio',
                    'reference': studio_request_id or '-',
                    'title': 'Role Private Studio request',
                    'detail': str(structured_jd.get('role_name') or structured_jd.get('purpose') or 'Governed role authoring activity recorded.'),
                },
            )

        for entry in audit_entries:
            metadata = entry.get('metadata', {}) if isinstance(entry.get('metadata', {}), dict) else {}
            context = metadata.get('context', {}) if isinstance(metadata.get('context', {}), dict) else {}
            context_metadata = context.get('metadata', {}) if isinstance(context.get('metadata', {}), dict) else {}
            runtime_evidence = metadata.get('runtime_evidence', {}) if isinstance(metadata.get('runtime_evidence', {}), dict) else {}
            workflow_bundle = runtime_evidence.get('workflow_bundle_summary', {}) if isinstance(runtime_evidence.get('workflow_bundle_summary', {}), dict) else {}
            execution_plan = context_metadata.get('execution_plan', {}) if isinstance(context_metadata.get('execution_plan', {}), dict) else {}
            human_override = metadata.get('human_override', {}) if isinstance(metadata.get('human_override', {}), dict) else {}
            request_id = str(entry.get('request_id') or context.get('request_id') or metadata.get('request_id') or '').strip()
            workflow_id = str(workflow_bundle.get('execution_plan_id') or execution_plan.get('plan_id') or metadata.get('workflow_id') or '').strip()
            override_id = str(human_override.get('request_id', '') or '').strip()
            studio_request_id = str(metadata.get('studio_request_id', '') or '').strip()
            aliases = []
            if request_id:
                aliases.append(f'request:{request_id}')
            if workflow_id:
                aliases.append(f'workflow:{workflow_id}')
            if override_id:
                aliases.append(f'override:{override_id}')
            if studio_request_id:
                aliases.append(f'studio:{studio_request_id}')
            if not aliases:
                continue
            _, case = ensure_case(aliases)
            action = str(entry.get('action', 'audit_event') or 'audit_event')
            outcome = str(entry.get('outcome', 'recorded') or 'recorded')
            touch_case(
                case,
                timestamp=entry.get('timestamp'),
                request_id=request_id,
                override_id=override_id,
                workflow_id=workflow_id,
                studio_request_id=studio_request_id,
                attention=action in {'evidence_export', 'workflow_proof_export'} and outcome != 'completed',
                audit_event=True,
                event={
                    'timestamp': entry.get('timestamp'),
                    'event_type': 'audit',
                    'status': outcome,
                    'view': 'audit',
                    'reference': request_id or workflow_id or studio_request_id or '-',
                    'title': f'{action} audit event',
                    'detail': str(entry.get('reason') or metadata.get('requested_by') or 'Audit event recorded.'),
                },
            )

        items: list[dict[str, object]] = []
        for case in cases.values():
            timeline = sorted(
                case['timeline'],
                key=lambda item: (str(item.get('timestamp', '') or ''), str(item.get('reference', '') or '')),
                reverse=True,
            )
            if case['blocked_total'] > 0:
                status = 'blocked'
            elif case['pending_override_total'] > 0 or case['waiting_human_total'] > 0:
                status = 'human_required'
            elif case['attention_total'] > 0:
                status = 'attention_required'
            elif case['active_total'] > 0:
                status = 'active'
            else:
                status = 'monitoring'
            if case['pending_override_total'] > 0:
                primary_view = 'overrides'
            elif case['blocked_total'] > 0:
                primary_view = 'conflicts'
            elif case['linked_request_ids']:
                primary_view = 'requests'
            elif case['linked_studio_request_ids']:
                primary_view = 'studio'
            elif case['linked_session_ids']:
                primary_view = 'human_ask'
            else:
                primary_view = 'audit'
            display_id = self._case_display_id(case['case_key'])
            title = (
                next(iter(sorted(case['linked_request_ids'])), '')
                or next(iter(sorted(case['linked_studio_request_ids'])), '')
                or next(iter(sorted(case['linked_session_ids'])), '')
                or display_id
            )
            items.append(
                {
                    'case_id': display_id,
                    'status': status,
                    'primary_view': primary_view,
                    'title': title,
                    'opened_at': case.get('opened_at'),
                    'updated_at': case.get('updated_at'),
                    'linked_request_ids': sorted(case['linked_request_ids']),
                    'linked_override_ids': sorted(case['linked_override_ids']),
                    'linked_session_ids': sorted(case['linked_session_ids']),
                    'linked_workflow_ids': sorted(case['linked_workflow_ids']),
                    'linked_studio_request_ids': sorted(case['linked_studio_request_ids']),
                    'audit_event_total': int(case.get('audit_event_total', 0) or 0),
                    'timeline_total': len(timeline),
                    'timeline': timeline[:6],
                    'summary': {
                        'pending_override_total': int(case.get('pending_override_total', 0) or 0),
                        'waiting_human_total': int(case.get('waiting_human_total', 0) or 0),
                        'blocked_total': int(case.get('blocked_total', 0) or 0),
                        'attention_total': int(case.get('attention_total', 0) or 0),
                    },
                }
            )

        priority = {
            'blocked': 0,
            'human_required': 1,
            'attention_required': 2,
            'active': 3,
            'monitoring': 4,
        }
        items.sort(key=lambda item: (priority.get(str(item.get('status', 'monitoring')), 5), str(item.get('updated_at', '') or ''), str(item.get('case_id', ''))), reverse=False)
        attention_total = sum(1 for item in items if str(item.get('status', '')) in {'blocked', 'human_required', 'attention_required'})
        human_required_total = sum(1 for item in items if str(item.get('status', '')) == 'human_required')
        blocked_total = sum(1 for item in items if str(item.get('status', '')) == 'blocked')
        primary_view = items[0].get('primary_view', 'overview') if items else 'overview'
        return {
            'summary': {
                'cases_total': len(items),
                'attention_total': attention_total,
                'human_required_total': human_required_total,
                'blocked_total': blocked_total,
                'primary_view': primary_view,
            },
            'items': items[:limit],
        }

    @staticmethod
    def _attach_case_refs(
        *,
        requests: list[dict[str, object]],
        overrides: list[dict[str, object]],
        human_ask: dict[str, object],
        role_private_studio: dict[str, object],
        cases: dict[str, object],
    ) -> None:
        case_items = cases.get('items', []) if isinstance(cases.get('items', []), list) else []
        request_refs: dict[str, dict[str, str]] = {}
        override_refs: dict[str, dict[str, str]] = {}
        session_refs: dict[str, dict[str, str]] = {}
        workflow_refs: dict[str, dict[str, str]] = {}
        studio_refs: dict[str, dict[str, str]] = {}

        def payload(item: dict[str, object]) -> dict[str, str]:
            return {
                'case_id': str(item.get('case_id', '') or ''),
                'case_status': str(item.get('status', 'monitoring') or 'monitoring'),
                'case_primary_view': str(item.get('primary_view', 'overview') or 'overview'),
            }

        for item in case_items:
            ref = payload(item)
            if not ref['case_id']:
                continue
            for request_id in item.get('linked_request_ids', []) if isinstance(item.get('linked_request_ids', []), list) else []:
                request_refs[str(request_id)] = ref
            for override_id in item.get('linked_override_ids', []) if isinstance(item.get('linked_override_ids', []), list) else []:
                override_refs[str(override_id)] = ref
            for session_id in item.get('linked_session_ids', []) if isinstance(item.get('linked_session_ids', []), list) else []:
                session_refs[str(session_id)] = ref
            for workflow_id in item.get('linked_workflow_ids', []) if isinstance(item.get('linked_workflow_ids', []), list) else []:
                workflow_refs[str(workflow_id)] = ref
            for studio_request_id in item.get('linked_studio_request_ids', []) if isinstance(item.get('linked_studio_request_ids', []), list) else []:
                studio_refs[str(studio_request_id)] = ref

        for item in requests:
            request_id = str(item.get('request_id', '') or '').strip()
            workflow_id = str(item.get('workflow_id', '') or '').strip()
            override_id = str(item.get('human_override_request_id', '') or '').strip()
            ref = request_refs.get(request_id) or workflow_refs.get(workflow_id) or override_refs.get(override_id)
            if ref:
                item.update(ref)

        for item in overrides:
            override_id = str(item.get('request_id', '') or '').strip()
            origin_request_id = str(item.get('origin_request_id', item.get('request_id', '')) or '').strip()
            workflow_id = str(item.get('workflow_id', '') or '').strip()
            ref = override_refs.get(override_id) or request_refs.get(origin_request_id) or workflow_refs.get(workflow_id)
            if ref:
                item.update(ref)

        sessions = human_ask.get('sessions', []) if isinstance(human_ask.get('sessions', []), list) else []
        for item in sessions:
            metadata = item.get('metadata', {}) if isinstance(item.get('metadata', {}), dict) else {}
            summary = item.get('summary', {}) if isinstance(item.get('summary', {}), dict) else {}
            inbox = metadata.get('human_decision_inbox', {}) if isinstance(metadata.get('human_decision_inbox', {}), dict) else {}
            execution_plan = metadata.get('execution_plan', {}) if isinstance(metadata.get('execution_plan', {}), dict) else {}
            if not execution_plan:
                execution_plan = inbox.get('execution_plan', {}) if isinstance(inbox.get('execution_plan', {}), dict) else {}
            session_id = str(item.get('session_id', '') or '').strip()
            origin_request_id = str(metadata.get('origin_request_id', metadata.get('request_id', '')) or '').strip()
            workflow_id = str(execution_plan.get('plan_id', summary.get('queue_execution_plan_id', '')) or '').strip()
            studio_request_id = str(metadata.get('studio_request_id', '') or '').strip()
            ref = session_refs.get(session_id) or request_refs.get(origin_request_id) or workflow_refs.get(workflow_id) or studio_refs.get(studio_request_id)
            if ref:
                item.update(ref)

        studio_requests = role_private_studio.get('requests', []) if isinstance(role_private_studio.get('requests', []), list) else []
        for item in studio_requests:
            request_id = str(item.get('request_id', '') or '').strip()
            ref = studio_refs.get(request_id)
            if ref:
                item.update(ref)


    @staticmethod
    def _case_display_id(case_key: str) -> str:
        prefix, _, value = str(case_key).partition(':')
        cleaned = value or case_key
        if prefix == 'request':
            return f'CASE-REQ-{cleaned}'
        if prefix == 'workflow':
            return f'CASE-WF-{cleaned}'
        if prefix == 'override':
            return f'CASE-OVR-{cleaned}'
        if prefix == 'session':
            return f'CASE-ASK-{cleaned}'
        if prefix == 'studio':
            return f'CASE-STUDIO-{cleaned}'
        return f'CASE-{cleaned}'

    def operations(self, limit: int = 10) -> dict[str, object]:
        return {
            'summary': self.app.runtime_backup_summary(),
            'backups': self.app.list_runtime_backups(limit=limit),
            'usability_proof': self.usability_proof_summary(),
            'quick_start_doctor': self.quick_start_doctor_summary(),
            'runtime_performance_baseline': self.runtime_performance_baseline_summary(),
        }

    def first_run_readiness(
        self,
        *,
        owner_registration: dict[str, object],
        go_live_readiness: dict[str, object],
        operational_readiness: dict[str, object],
        operations: dict[str, object],
    ) -> dict[str, object]:
        proof = operations.get('usability_proof', {}) if isinstance(operations.get('usability_proof'), dict) else {}
        smoke_report = go_live_readiness.get('smoke_report', {}) if isinstance(go_live_readiness.get('smoke_report'), dict) else {}
        quick_start_report_path = self.config.review_dir / 'quick_start_path.json'
        demo_script_path = self.config.base_dir / 'scripts' / 'nontechnical_demo_path.py'
        checks: list[dict[str, object]] = [
            {
                'check_id': 'owner_registration',
                'title': 'Owner registration is present',
                'passed': bool(owner_registration.get('registered', False)),
                'required': True,
                'view': 'health',
                'detail': str(owner_registration.get('path') or 'Owner registration record is missing.'),
            },
            {
                'check_id': 'go_live_gate',
                'title': 'Go-live gate is ready',
                'passed': bool(go_live_readiness.get('ready', False)),
                'required': True,
                'view': 'health',
                'detail': f"Go-live status is {go_live_readiness.get('status', 'blocked')}.",
            },
            {
                'check_id': 'runtime_smoke',
                'title': 'Runtime smoke report is passed',
                'passed': str(smoke_report.get('status', 'missing')) == 'passed',
                'required': True,
                'view': 'health',
                'detail': f"Smoke status is {smoke_report.get('status', 'missing')}.",
            },
            {
                'check_id': 'operational_visibility',
                'title': 'Operational readiness surface is live',
                'passed': str(operational_readiness.get('status', 'unknown')) in {'ready', 'monitoring'},
                'required': True,
                'view': 'overview',
                'detail': f"Operational readiness is {operational_readiness.get('status', 'unknown')}.",
            },
            {
                'check_id': 'quick_start_report',
                'title': 'Quick-start report artifact exists',
                'passed': quick_start_report_path.exists(),
                'required': False,
                'view': 'health',
                'detail': str(quick_start_report_path),
            },
            {
                'check_id': 'usability_proof',
                'title': 'Usability proof bundle is available',
                'passed': bool(proof.get('available', False)),
                'required': False,
                'view': 'overview',
                'detail': f"Proof status is {proof.get('status', 'missing')}.",
            },
            {
                'check_id': 'demo_script',
                'title': 'Non-technical demo script is available',
                'passed': demo_script_path.exists(),
                'required': False,
                'view': 'overview',
                'detail': str(demo_script_path),
            },
        ]
        blockers = [item for item in checks if bool(item.get('required')) and not bool(item.get('passed'))]
        advisories = [item for item in checks if not bool(item.get('required')) and not bool(item.get('passed'))]
        if blockers:
            status = 'blocked'
        elif advisories:
            status = 'monitoring'
        else:
            status = 'ready'
        return {
            'status': status,
            'checks': checks,
            'blockers_total': len(blockers),
            'advisories_total': len(advisories),
            'ready': not blockers,
            'recommended_view': str((blockers[0] if blockers else advisories[0]).get('view', 'overview')) if (blockers or advisories) else 'overview',
        }

    def quick_start_doctor_summary(self) -> dict[str, object]:
        from sa_nom_governance.deployment.quick_start_path import read_quick_start_doctor

        result = read_quick_start_doctor(config=self.config)
        summary = result.get('summary', {}) if isinstance(result.get('summary'), dict) else {}
        return {
            'status': str(result.get('status', 'missing')),
            'available': bool(result.get('available', False)),
            'artifact_path': str(result.get('artifact_path', self.config.review_dir / 'quick_start_doctor.json')),
            'generated_at': result.get('generated_at'),
            'checks_total': int(summary.get('checks_total', 0) or 0),
            'required_failed_total': int(summary.get('required_failed_total', 0) or 0),
            'advisory_failed_total': int(summary.get('advisory_failed_total', 0) or 0),
            'next_actions': result.get('next_actions', []) if isinstance(result.get('next_actions'), list) else [],
        }

    def runtime_performance_baseline_summary(self) -> dict[str, object]:
        from sa_nom_governance.deployment.runtime_performance_baseline import read_runtime_performance_baseline

        result = read_runtime_performance_baseline(config=self.config)
        summary = result.get('summary', {}) if isinstance(result.get('summary'), dict) else {}
        return {
            'status': str(result.get('status', 'missing')),
            'available': bool(result.get('available', False)),
            'artifact_path': str(result.get('output_path', self.config.review_dir / 'runtime_performance_baseline.json')),
            'generated_at': result.get('generated_at'),
            'slowest_metric': str(summary.get('slowest_metric', 'unknown')),
            'slowest_elapsed_ms': float(summary.get('slowest_elapsed_ms', 0.0) or 0.0),
            'health_elapsed_ms': float(summary.get('health_elapsed_ms', 0.0) or 0.0),
            'operational_readiness_elapsed_ms': float(summary.get('operational_readiness_elapsed_ms', 0.0) or 0.0),
            'dashboard_snapshot_elapsed_ms': float(summary.get('dashboard_snapshot_elapsed_ms', 0.0) or 0.0),
            'warning_total': int(summary.get('warning_total', 0) or 0),
            'critical_total': int(summary.get('critical_total', 0) or 0),
            'failed_total': int(summary.get('failed_total', 0) or 0),
        }

    def first_run_action_center(
        self,
        *,
        first_run_readiness: dict[str, object],
        go_live_readiness: dict[str, object],
        operations: dict[str, object],
    ) -> dict[str, object]:
        checks = first_run_readiness.get('checks', []) if isinstance(first_run_readiness.get('checks'), list) else []
        items: list[dict[str, object]] = []

        action_map = {
            'owner_registration': {
                'ops_action': None,
                'recommendation': 'Register the runtime ownership identity before first-run handoff.',
            },
            'go_live_gate': {
                'ops_action': 'quick-start-doctor',
                'recommendation': 'Run quick-start doctor and clear required blockers before go-live.',
            },
            'runtime_smoke': {
                'ops_action': 'quick-start-doctor',
                'recommendation': 'Run quick-start doctor to refresh startup smoke posture.',
            },
            'operational_visibility': {
                'ops_action': 'quick-start-doctor',
                'recommendation': 'Refresh doctor status so operational visibility is current.',
            },
            'quick_start_report': {
                'ops_action': 'quick-start-doctor',
                'recommendation': 'Generate quick-start doctor report so first-run artifacts are visible.',
            },
            'usability_proof': {
                'ops_action': 'usability-proof',
                'recommendation': 'Generate usability proof bundle for first-run evidence coverage.',
            },
            'demo_script': {
                'ops_action': None,
                'recommendation': 'Add non-technical demo script to complete first-run handoff flow.',
            },
        }

        for check in checks:
            if bool(check.get('passed')):
                continue
            check_id = str(check.get('check_id', 'unknown'))
            mapping = action_map.get(check_id, {'ops_action': None, 'recommendation': 'Review this first-run gate before continuing.'})
            items.append(
                {
                    'action_id': check_id,
                    'title': str(check.get('title', check_id.replace('_', ' '))),
                    'severity': 'required' if bool(check.get('required')) else 'advisory',
                    'view': str(check.get('view', 'overview')),
                    'detail': str(check.get('detail', '-')),
                    'ops_action': mapping.get('ops_action'),
                    'recommendation': str(mapping.get('recommendation', 'Review this gate before continuing.')),
                }
            )

        doctor = operations.get('quick_start_doctor', {}) if isinstance(operations.get('quick_start_doctor'), dict) else {}
        doctor_status = str(doctor.get('status', 'missing'))
        if doctor_status in {'missing', 'invalid'}:
            items.append(
                {
                    'action_id': 'quick_start_doctor_refresh',
                    'title': 'Quick-start doctor artifact is missing or invalid',
                    'severity': 'required',
                    'view': 'health',
                    'detail': str(doctor.get('artifact_path', self.config.review_dir / 'quick_start_doctor.json')),
                    'ops_action': 'quick-start-doctor',
                    'recommendation': 'Run quick-start doctor so runtime posture is machine-readable.',
                }
            )

        proof = operations.get('usability_proof', {}) if isinstance(operations.get('usability_proof'), dict) else {}
        if not bool(proof.get('available', False)):
            items.append(
                {
                    'action_id': 'usability_proof_refresh',
                    'title': 'Usability proof bundle is not available yet',
                    'severity': 'advisory',
                    'view': 'overview',
                    'detail': str(proof.get('path', self.config.review_dir / 'usability_proof_bundle.json')),
                    'ops_action': 'usability-proof',
                    'recommendation': 'Generate the usability proof bundle for first-run evidence and demo readiness.',
                }
            )

        deduped: list[dict[str, object]] = []
        seen: set[str] = set()
        for item in items:
            action_id = str(item.get('action_id', ''))
            if action_id in seen:
                continue
            seen.add(action_id)
            deduped.append(item)

        deduped.sort(key=lambda item: (0 if item.get('severity') == 'required' else 1, str(item.get('action_id', ''))))
        required_total = sum(1 for item in deduped if item.get('severity') == 'required')

        return {
            'status': str(first_run_readiness.get('status', go_live_readiness.get('status', 'blocked'))),
            'ready': bool(first_run_readiness.get('ready', False)) and required_total == 0,
            'items_total': len(deduped),
            'required_total': required_total,
            'recommended_action': str((deduped[0] if deduped else {}).get('ops_action') or 'none'),
            'items': deduped[:10],
        }


    def usability_proof_summary(self) -> dict[str, object]:
        from sa_nom_governance.deployment.usability_proof_bundle import read_usability_proof_bundle

        result = read_usability_proof_bundle(config=self.config)
        report = result.get('report') if isinstance(result.get('report'), dict) else {}
        pass_criteria = report.get('pass_criteria', []) if isinstance(report.get('pass_criteria'), list) else []
        criteria_rows: list[dict[str, object]] = []
        for item in pass_criteria:
            if not isinstance(item, dict):
                continue
            criteria_rows.append(
                {
                    'criterion': str(item.get('criterion', 'criterion')),
                    'passed': bool(item.get('passed', False)),
                }
            )
        failed_criteria = [str(row.get('criterion', 'criterion')) for row in criteria_rows if not row.get('passed')]
        return {
            'status': result.get('status', 'missing'),
            'available': bool(result.get('available', False)),
            'path': str(result.get('output_path', self.config.review_dir / 'usability_proof_bundle.json')),
            'generated_at': result.get('generated_at'),
            'passed': bool(result.get('passed', False)),
            'milestone': str(result.get('milestone', 'v0.3.0')),
            'criteria_total': len(criteria_rows),
            'criteria_passed_total': sum(1 for row in criteria_rows if row.get('passed')),
            'criteria_failed_total': len(failed_criteria),
            'failed_criteria': failed_criteria,
            'pass_criteria': criteria_rows,
        }

    def retention_report(self) -> dict[str, object]:
        return self.app.retention_report()

    def retention_plan(self) -> dict[str, object]:
        return self.app.retention_plan()

    def go_live_readiness(
        self,
        *,
        app_health: dict[str, object] | None = None,
        access_control_health: dict[str, object] | None = None,
        studio_snapshot: dict[str, object] | None = None,
        deployment_report: dict[str, object] | None = None,
    ) -> dict[str, object]:
        return build_go_live_readiness(
            self.config,
            app=self.app,
            app_health=app_health,
            access_health=access_control_health,
            studio_snapshot=studio_snapshot,
            deployment_report=deployment_report,
        )

    def compliance_snapshot(
        self,
        *,
        roles: list[dict[str, object]] | None = None,
        runtime_health: dict[str, object] | None = None,
        access_control_health: dict[str, object] | None = None,
        evidence_summary: dict[str, object] | None = None,
    ) -> dict[str, object]:
        return self.app.compliance_snapshot(
            roles=roles,
            runtime_health=runtime_health,
            access_control_health=access_control_health,
            evidence_summary=evidence_summary,
        )

    def evidence_exports(self, limit: int = 20, summary: dict[str, object] | None = None) -> dict[str, object]:
        return {
            'summary': summary if summary is not None else self.app.evidence_pack_summary(),
            'exports': self.app.list_evidence_packs(limit=limit),
            'workflow_proofs': self.app.list_workflow_proof_bundles(limit=limit),
        }

    def integrations(self, limit: int = 50) -> dict[str, object]:
        return self.app.integration_snapshot(limit=limit)

    def model_providers(self, health: dict[str, object] | None = None) -> dict[str, object]:
        return self.app.model_provider_snapshot(health=health)

    def owner_registration(self) -> dict[str, object]:
        registration = self.config.owner_registration()
        if registration is None:
            return {
                'registered': False,
                'path': str(self.config.effective_owner_registration_path()) if self.config.effective_owner_registration_path() else None,
            }
        return {
            'registered': True,
            'path': str(self.config.effective_owner_registration_path()) if self.config.effective_owner_registration_path() else None,
            'registration_code': registration.registration_code,
            'deployment_mode': registration.deployment_mode,
            'organization_name': registration.organization_name,
            'organization_id': registration.organization_id,
            'owner_name': registration.owner_name,
            'owner_display_name': registration.owner_display_name,
            'executive_owner_id': registration.executive_owner_id,
            'trusted_registry_signed_by': registration.trusted_registry_signed_by,
            'registered_at': registration.registered_at,
        }

    def runtime_health(
        self,
        roles: list[dict[str, object]] | None = None,
        go_live_readiness: dict[str, object] | None = None,
        *,
        owner_registration: dict[str, object] | None = None,
        app_health: dict[str, object] | None = None,
        access_control_health: dict[str, object] | None = None,
        deployment_profile: dict[str, object] | None = None,
    ) -> dict[str, object]:
        known_roles = roles if roles is not None else self.list_roles()
        cached_health = app_health if app_health is not None else self.app.health(roles=known_roles)
        readiness = (
            go_live_readiness
            if go_live_readiness is not None
            else self.go_live_readiness(
                app_health=cached_health,
                access_control_health=access_control_health,
                deployment_report=deployment_profile,
            )
        )
        registration = owner_registration if owner_registration is not None else self.owner_registration()
        access_health = access_control_health if access_control_health is not None else self.access_control.health()
        deployment = deployment_profile if deployment_profile is not None else build_deployment_report(self.config).to_dict()
        return {
            'engine_status': cached_health.get('status', 'unknown'),
            'owner_registration': registration,
            'audit_store': self._file_health(self.config.audit_log_path),
            'override_store': self._file_health(self.config.override_store_path),
            'lock_store': self._file_health(self.config.lock_store_path),
            'consistency_store': self._file_health(self.config.consistency_store_path),
            'session_store': self._file_health(self.config.session_store_path),
            'role_private_studio_store': self._file_health(self.config.role_private_studio_store_path),
            'human_ask_store': self._file_health(self.config.human_ask_store_path),
            'startup_smoke_report': self._file_health(self.config.startup_smoke_report_path),
            'retention_archive_dir': self._file_health(self.config.retention_archive_dir),
            'runtime_backup_dir': self._file_health(self.config.runtime_backup_dir),
            'runtime_evidence_dir': self._file_health(self.config.runtime_evidence_dir),
            'trusted_registry_manifest': self._file_health(self.config.trusted_registry_manifest_path),
            'trusted_registry_cache': self._file_health(self.config.trusted_registry_cache_path),
            'role_transition_matrix': self._file_health(self.config.role_transition_matrix_path),
            'compliance_frameworks_catalog': self._file_health(self.config.compliance_frameworks_path),
            'integration_targets_catalog': self._file_health(self.config.integration_targets_path),
            'integration_delivery_log': self._file_health(self.config.integration_delivery_log_path),
            'integration_dead_letter_log': self._file_health(self.config.integration_dead_letter_log_path),
            'integration_outbox_store': self._file_health(self.config.integration_outbox_path),
            'trusted_registry': cached_health.get('trusted_registry', {}),
            'request_consistency': cached_health.get('request_consistency', {}),
            'audit_integrity': cached_health.get('audit_integrity', {}),
            'access_control': access_health,
            'deployment_profile': deployment,
            'go_live_readiness': readiness,
            'privileged_operations': readiness.get('privileged_operations', {}),
            'studio_structural': readiness.get('studio_structural', {}),
            'retention': cached_health.get('retention', self.retention_manager.summary()),
            'role_private_studio': cached_health.get('role_private_studio', {}),
            'human_ask': cached_health.get('human_ask', {}),
            'runtime_backups': cached_health.get('runtime_backups', {}),
            'role_library': cached_health.get('role_library', {}),
            'role_hierarchy': cached_health.get('role_hierarchy', {}),
            'governance_materials': cached_health.get('governance_materials', {}),
            'role_transition_policy': cached_health.get('role_transition_policy', {}),
            'persistence_layer': cached_health.get('persistence_layer', {}),
            'compliance_frameworks': cached_health.get('compliance_frameworks', {}),
            'evidence_exports': cached_health.get('evidence_exports', {}),
            'integration_registry': cached_health.get('integration_registry', {}),
            'model_providers': cached_health.get('model_providers', {}),
            'integration_deliveries': cached_health.get('integration_deliveries', {}),
            'coordination_layer': cached_health.get('coordination_layer', {}),
            'ptag_modules': len(known_roles),
            'token_gate': 'enabled' if self.config.api_token else 'disabled',
            'legal_hold_file': self._file_health(self.config.legal_hold_path),
        }

    def operator_queue_health(
        self,
        *,
        overrides: list[dict[str, object]],
        human_ask: dict[str, object],
        operational_readiness: dict[str, object],
        policy: dict[str, object],
    ) -> dict[str, object]:
        visibility = operational_readiness.get('operator_visibility', {}) if isinstance(operational_readiness.get('operator_visibility', {}), dict) else {}
        sessions = human_ask.get('sessions', []) if isinstance(human_ask.get('sessions', []), list) else []
        warning_hours = int(((policy.get('aging') or {}).get('warning_hours')) or 24)
        critical_hours = int(((policy.get('aging') or {}).get('critical_hours')) or warning_hours)
        stale_hours = int(((policy.get('aging') or {}).get('stale_hours')) or critical_hours)
        backlog_warning_total = int(((policy.get('backlog') or {}).get('warning_total')) or 3)
        backlog_critical_total = int(((policy.get('backlog') or {}).get('critical_total')) or backlog_warning_total)

        pending_overrides = [item for item in overrides if str(item.get('status', '')) == 'pending']
        waiting_sessions = [item for item in sessions if str(item.get('status', '')) in {'waiting_human', 'escalated'}]
        blocked_workflows = [
            item for item in (visibility.get('workflow_backlog', []) if isinstance(visibility.get('workflow_backlog', []), list) else [])
            if str(item.get('current_state', '')) in {'blocked', 'awaiting_human_confirmation'}
        ]
        recovery_backlog = visibility.get('runtime_recovery_backlog', []) if isinstance(visibility.get('runtime_recovery_backlog', []), list) else []
        dead_letters = visibility.get('runtime_dead_letters', []) if isinstance(visibility.get('runtime_dead_letters', []), list) else []

        def build_item(lane_id: str, title: str, view: str, rows: list[dict[str, object]], *, timestamp_fields: list[str], reference_fields: list[str]) -> dict[str, object]:
            total = len(rows)
            oldest_record = self._oldest_record(rows, timestamp_fields)
            oldest_hours = self._age_hours(oldest_record, timestamp_fields) if oldest_record is not None else 0
            status = self._operator_queue_status(
                total=total,
                oldest_hours=oldest_hours,
                warning_hours=warning_hours,
                critical_hours=critical_hours,
                stale_hours=stale_hours,
                backlog_warning_total=backlog_warning_total,
                backlog_critical_total=backlog_critical_total,
            )
            return {
                'lane_id': lane_id,
                'title': title,
                'view': view,
                'total': total,
                'oldest_age_hours': oldest_hours,
                'status': status,
                'oldest_reference': self._first_present(oldest_record or {}, reference_fields),
            }

        items = [
            build_item('pending_overrides', 'Pending overrides', 'overrides', pending_overrides, timestamp_fields=['created_at'], reference_fields=['request_id', 'origin_request_id']),
            build_item('waiting_human_sessions', 'Waiting Human Ask sessions', 'human_ask', waiting_sessions, timestamp_fields=['updated_at', 'created_at'], reference_fields=['session_id']),
            build_item('blocked_workflows', 'Blocked workflows', 'requests', blocked_workflows, timestamp_fields=['updated_at'], reference_fields=['workflow_id', 'request_id']),
            build_item('recovery_backlog', 'Recovery backlog', 'conflicts', recovery_backlog, timestamp_fields=['updated_at', 'created_at'], reference_fields=['request_id']),
            build_item('dead_letters', 'Dead letters', 'conflicts', dead_letters, timestamp_fields=['captured_at', 'updated_at', 'created_at'], reference_fields=['request_id', 'event_id']),
        ]
        items.sort(key=lambda item: (0 if item['status'] in {'stale', 'critical'} else 1 if item['status'] == 'warning' else 2, -item['total'], -item['oldest_age_hours']))
        return {
            'policy': policy,
            'items': items,
            'attention_total': sum(1 for item in items if item.get('status') in {'warning', 'critical', 'stale'}),
            'critical_total': sum(1 for item in items if item.get('status') in {'critical', 'stale'}),
        }


    def unified_work_inbox(
        self,
        *,
        overrides: list[dict[str, object]],
        human_ask: dict[str, object],
        role_private_studio: dict[str, object],
        operational_readiness: dict[str, object],
        operator_queue_health: dict[str, object],
        operator_decision_lanes: list[dict[str, object]],
    ) -> dict[str, object]:
        visibility = operational_readiness.get('operator_visibility', {}) if isinstance(operational_readiness.get('operator_visibility', {}), dict) else {}
        queue_items = operator_queue_health.get('items', []) if isinstance(operator_queue_health.get('items', []), list) else []
        queue_map = {str(item.get('lane_id', '')): item for item in queue_items if str(item.get('lane_id', ''))}
        studio_requests = role_private_studio.get('requests', []) if isinstance(role_private_studio.get('requests', []), list) else []
        sessions = human_ask.get('sessions', []) if isinstance(human_ask.get('sessions', []), list) else []

        pending_overrides = [item for item in overrides if str(item.get('status', '')) == 'pending']
        inbox_items = visibility.get('human_decision_inbox', []) if isinstance(visibility.get('human_decision_inbox', []), list) else []
        blocked_workflows = [
            item
            for item in (visibility.get('workflow_backlog', []) if isinstance(visibility.get('workflow_backlog', []), list) else [])
            if str(item.get('current_state', '')) in {'blocked', 'awaiting_human_confirmation', 'closed_with_exception'}
        ]
        recovery_backlog = visibility.get('runtime_recovery_backlog', []) if isinstance(visibility.get('runtime_recovery_backlog', []), list) else []
        dead_letters = visibility.get('runtime_dead_letters', []) if isinstance(visibility.get('runtime_dead_letters', []), list) else []

        structural_review = [item for item in studio_requests if str((item.get('publish_readiness') or {}).get('status', '')) == 'guarded']
        publish_ready = [
            item
            for item in studio_requests
            if str((item.get('publish_readiness') or {}).get('status', '')) == 'ready' or str(item.get('status', '')) == 'approved'
        ]
        review_queue = [
            item
            for item in studio_requests
            if str(item.get('status', '')) != 'published' and item not in publish_ready and item not in structural_review
        ]

        lane_configs: dict[str, dict[str, object]] = {
            'pending_overrides': {
                'title': 'Pending override approvals',
                'view': 'overrides',
                'disposition': 'human_required',
                'next_step': 'Approve or veto the next override packet before execution resumes.',
                'operator_note': 'Human override decisions are the last explicit boundary before the runtime continues.',
                'reference_fields': ['request_id', 'origin_request_id'],
            },
            'human_decision_inbox': {
                'title': 'Human decision inbox',
                'view': 'human_ask',
                'disposition': 'human_required',
                'next_step': 'Review the next governed report or clearance record waiting for a human decision.',
                'operator_note': 'These records already crossed a real human boundary inside Human Ask.',
                'reference_fields': ['session_id', 'request_id', 'workflow_id'],
            },
            'blocked_workflows': {
                'title': 'Blocked workflows',
                'view': 'requests',
                'disposition': 'blocked',
                'next_step': 'Inspect the blocked workflow and route it to the correct governed lane.',
                'operator_note': 'Blocked workflows mean the Director cannot keep moving autonomously on that path.',
                'reference_fields': ['workflow_id', 'request_id'],
            },
            'recovery_backlog': {
                'title': 'Recovery backlog',
                'view': 'conflicts',
                'disposition': 'blocked',
                'next_step': 'Resume retryable runtime recovery items or fail them closed with evidence.',
                'operator_note': 'Recovery backlog is where retryable runtime failures wait for deliberate handling.',
                'reference_fields': ['request_id', 'resumed_request_id'],
            },
            'dead_letters': {
                'title': 'Dead letters',
                'view': 'conflicts',
                'disposition': 'blocked',
                'next_step': 'Review dead-letter events and decide whether they should be retried or retired.',
                'operator_note': 'Dead letters are the fail-closed end of the runtime recovery path.',
                'reference_fields': ['request_id', 'event_id'],
            },
            'studio_review_queue': {
                'title': 'Studio review queue',
                'view': 'studio',
                'disposition': 'monitoring',
                'next_step': 'Review the next hat draft that still needs governance feedback or approval.',
                'operator_note': 'Treat the Studio queue like a promotion pipeline, not a draft pile.',
                'reference_fields': ['request_id'],
            },
            'studio_structural_review': {
                'title': 'Studio structural review',
                'view': 'studio',
                'disposition': 'monitoring',
                'next_step': 'Resolve PT-OSS structural pressure before trusting the next publish candidate.',
                'operator_note': 'These hats are governed but not structurally calm enough for trusted release yet.',
                'reference_fields': ['request_id'],
            },
            'studio_publish_queue': {
                'title': 'Studio publish-ready lane',
                'view': 'studio',
                'disposition': 'ready',
                'next_step': 'Run the final trust check, then publish only from the ready lane.',
                'operator_note': 'Publish-ready hats are the cleanest place to expand AI workforce safely.',
                'reference_fields': ['request_id'],
            },
        }

        def tone_for(status: str, disposition: str) -> str:
            if status in {'critical', 'stale'}:
                return 'danger'
            if status == 'warning':
                return 'warning'
            if disposition == 'ready':
                return 'success'
            return 'accent'

        def sample_refs(rows: list[dict[str, object]], reference_fields: list[str], limit: int = 3) -> list[str]:
            refs: list[str] = []
            seen: set[str] = set()
            for row in rows:
                ref = self._first_present(row, reference_fields)
                if ref in (None, ''):
                    continue
                value = str(ref)
                if value in seen:
                    continue
                seen.add(value)
                refs.append(value)
                if len(refs) >= limit:
                    break
            return refs

        lane_rows: dict[str, list[dict[str, object]]] = {
            'pending_overrides': pending_overrides,
            'human_decision_inbox': inbox_items,
            'blocked_workflows': blocked_workflows,
            'recovery_backlog': recovery_backlog,
            'dead_letters': dead_letters,
            'studio_review_queue': review_queue,
            'studio_structural_review': structural_review,
            'studio_publish_queue': publish_ready,
        }

        items: list[dict[str, object]] = []
        for lane_id, rows in lane_rows.items():
            if not rows:
                continue
            config = lane_configs[lane_id]
            queue_item = queue_map.get(lane_id, {})
            status = str(queue_item.get('status', 'monitoring'))
            oldest_hours = int(queue_item.get('oldest_age_hours', 0) or 0)
            if oldest_hours <= 0:
                oldest_record = self._oldest_record(rows, ['updated_at', 'created_at', 'captured_at', 'timestamp'])
                oldest_hours = self._age_hours(oldest_record, ['updated_at', 'created_at', 'captured_at', 'timestamp'])
            refs = sample_refs(rows, config['reference_fields'])
            items.append(
                {
                    'lane_id': lane_id,
                    'title': str(config['title']),
                    'view': str(config['view']),
                    'disposition': str(config['disposition']),
                    'status': status,
                    'tone': tone_for(status, str(config['disposition'])),
                    'total': len(rows),
                    'oldest_age_hours': oldest_hours,
                    'oldest_reference': queue_item.get('oldest_reference') or (refs[0] if refs else '-'),
                    'next_step': str(config['next_step']),
                    'operator_note': str(config['operator_note']),
                    'sample_references': refs,
                    'action_label': f"Open {str(config['view']).replace('_', ' ').title()}",
                }
            )

        action_to_lane = {
            'clearance_review': 'human_decision_inbox',
            'human_decision': 'human_decision_inbox',
            'recovery_resume': 'recovery_backlog',
            'guarded_follow_up': 'human_decision_inbox',
        }
        action_rank = {
            'clearance_review': 1,
            'human_decision': 2,
            'recovery_resume': 3,
            'guarded_follow_up': 4,
        }
        lane_priority = {lane_id: 50 for lane_id in lane_rows.keys()}
        for lane in operator_decision_lanes:
            lane_id = action_to_lane.get(str(lane.get('lane_id', '')) )
            if not lane_id:
                continue
            lane_priority[lane_id] = min(lane_priority.get(lane_id, 50), action_rank.get(str(lane.get('lane_id', '')), 50))

        items.sort(
            key=lambda item: (
                0 if item.get('tone') == 'danger' else 1 if item.get('tone') == 'warning' else 2 if item.get('disposition') == 'human_required' else 3 if item.get('disposition') == 'blocked' else 4,
                lane_priority.get(str(item.get('lane_id', '')), 50),
                -int(item.get('total', 0) or 0),
                -int(item.get('oldest_age_hours', 0) or 0),
            )
        )

        if not items:
            items.append(
                {
                    'lane_id': 'autonomy_ready',
                    'title': 'Autonomy ready',
                    'view': 'overview',
                    'disposition': 'ready',
                    'status': 'ready',
                    'tone': 'success',
                    'total': 0,
                    'oldest_age_hours': 0,
                    'oldest_reference': '-',
                    'next_step': 'No immediate human work is open; continue governed execution.',
                    'operator_note': 'The Director can keep moving because no explicit human work queue is open right now.',
                    'sample_references': [],
                    'action_label': 'Open Overview',
                }
            )

        primary = items[0]
        return {
            'summary': {
                'open_total': sum(int(item.get('total', 0) or 0) for item in items),
                'attention_total': sum(1 for item in items if item.get('tone') in {'warning', 'danger'}),
                'human_required_total': sum(int(item.get('total', 0) or 0) for item in items if item.get('disposition') == 'human_required'),
                'blocked_total': sum(int(item.get('total', 0) or 0) for item in items if item.get('disposition') == 'blocked'),
                'monitoring_total': sum(int(item.get('total', 0) or 0) for item in items if item.get('disposition') == 'monitoring'),
                'ready_total': sum(int(item.get('total', 0) or 0) for item in items if item.get('disposition') == 'ready'),
                'lane_total': len(items),
                'primary_lane_id': primary.get('lane_id', 'overview'),
                'primary_title': primary.get('title', 'Autonomy ready'),
                'primary_view': primary.get('view', 'overview'),
                'primary_next_step': primary.get('next_step', 'Continue governed execution.'),
            },
            'items': items[:8],
        }

    def operator_notification_center(
        self,
        *,
        queue_health: dict[str, object],
        policy: dict[str, object],
    ) -> dict[str, object]:
        notification = policy.get('notification', {}) if isinstance(policy.get('notification', {}), dict) else {}
        severity_channels = notification.get('severity_channels', {}) if isinstance(notification.get('severity_channels', {}), dict) else {}
        cadence = notification.get('cadence', {}) if isinstance(notification.get('cadence', {}), dict) else {}
        enabled = bool(notification.get('enabled', True))
        default_channels = [str(item) for item in notification.get('default_channels', []) if str(item)] if isinstance(notification.get('default_channels', []), list) else ['dashboard']

        severity_rank = {'warning': 1, 'critical': 2, 'stale': 3}
        items: list[dict[str, object]] = []
        channel_totals: dict[str, int] = {}

        for item in queue_health.get('items', []) if isinstance(queue_health.get('items', []), list) else []:
            status = str(item.get('status', 'ready'))
            if status not in {'warning', 'critical', 'stale'}:
                continue
            channels = severity_channels.get(status, default_channels)
            channels = [str(channel) for channel in channels if str(channel)] if isinstance(channels, list) else default_channels
            normalized_channels = self._normalize_notification_channels(channels)
            for channel in normalized_channels:
                channel_totals[channel] = channel_totals.get(channel, 0) + 1
            items.append(
                {
                    'lane_id': item.get('lane_id'),
                    'title': item.get('title'),
                    'view': item.get('view'),
                    'total': int(item.get('total', 0) or 0),
                    'status': status,
                    'severity': status,
                    'oldest_age_hours': int(item.get('oldest_age_hours', 0) or 0),
                    'oldest_reference': item.get('oldest_reference'),
                    'channels': normalized_channels,
                    'internal_channels': [channel for channel in normalized_channels if self._notification_channel_scope(channel) == 'internal'],
                    'external_channels': [channel for channel in normalized_channels if self._notification_channel_scope(channel) == 'external'],
                    'dispatch_ready': enabled and bool(normalized_channels),
                }
            )

        items.sort(key=lambda item: (-severity_rank.get(str(item.get('severity', 'warning')), 0), -int(item.get('oldest_age_hours', 0) or 0), -int(item.get('total', 0) or 0)))
        highest_severity = 'ready'
        if items:
            highest_severity = max((str(item.get('severity', 'warning')) for item in items), key=lambda level: severity_rank.get(level, 0))

        channels = [
            {
                'channel': channel,
                'active_total': total,
                'scope': self._notification_channel_scope(channel),
                'family': self._notification_channel_family(channel),
            }
            for channel, total in sorted(channel_totals.items(), key=lambda entry: (-entry[1], entry[0]))
        ]

        return {
            'policy': policy,
            'enabled': enabled,
            'cadence': cadence,
            'items': items,
            'channels': channels,
            'active_channel_total': len(channels),
            'internal_channel_total': sum(1 for item in channels if item.get('scope') == 'internal'),
            'external_channel_total': sum(1 for item in channels if item.get('scope') == 'external'),
            'dispatch_candidates_total': len(items),
            'dispatch_ready_total': sum(1 for item in items if item.get('dispatch_ready')),
            'highest_severity': highest_severity,
        }

    def operator_notification_delivery_readiness(
        self,
        *,
        notification_center: dict[str, object],
        integrations: dict[str, object],
    ) -> dict[str, object]:
        summary = integrations.get('summary', {}) if isinstance(integrations.get('summary', {}), dict) else {}
        failed_total = int(summary.get('failed_total', 0) or 0)
        outbox_total = int(summary.get('outbox_total', 0) or 0)
        active_targets = int(summary.get('active_targets', 0) or 0)
        http_enabled = bool(summary.get('http_enabled', False))
        deliveries_total = int(summary.get('deliveries_total', 0) or 0)
        dispatch_candidates_total = int(notification_center.get('dispatch_candidates_total', 0) or 0)
        enabled = bool(notification_center.get('enabled', True))

        configured_external_channels = sorted(
            channel
            for channel in summary.get('notification_channels_configured', [])
            if self._notification_channel_scope(str(channel)) == 'external'
        )
        active_external_channels = sorted(
            channel
            for channel in summary.get('notification_channels_active', [])
            if self._notification_channel_scope(str(channel)) == 'external'
        )
        requested_external_channels = sorted(
            item.get('channel')
            for item in notification_center.get('channels', []) if isinstance(item, dict)
            if self._notification_channel_scope(str(item.get('channel', ''))) == 'external'
        )
        missing_external_channels = [channel for channel in requested_external_channels if channel not in configured_external_channels]
        inactive_external_channels = [channel for channel in requested_external_channels if channel in configured_external_channels and channel not in active_external_channels]
        external_routing_ready = bool(requested_external_channels) and http_enabled and not missing_external_channels and not inactive_external_channels

        if not enabled:
            posture = 'disabled'
        elif failed_total > 0:
            posture = 'degraded'
        elif outbox_total > 0:
            posture = 'pressured'
        elif requested_external_channels and external_routing_ready:
            posture = 'ready'
        elif dispatch_candidates_total <= 0:
            posture = 'ready'
        else:
            posture = 'dashboard_only'

        next_actions: list[dict[str, str]] = []
        if not enabled:
            next_actions.append({'label': 'Immediate action', 'detail': 'Re-enable operator notifications or maintain strict manual dashboard review until routing is restored.'})
        if requested_external_channels and not http_enabled:
            next_actions.append({'label': 'Enable HTTP', 'detail': 'Turn on outbound HTTP integrations before expecting external operator delivery.'})
        if missing_external_channels:
            next_actions.append({'label': 'Add channel targets', 'detail': f"Configure explicit integration targets for: {', '.join(missing_external_channels)}."})
        if inactive_external_channels:
            next_actions.append({'label': 'Activate configured routes', 'detail': f"The following external channels are configured but not active: {', '.join(inactive_external_channels)}."})
        if http_enabled and requested_external_channels and active_targets <= 0:
            next_actions.append({'label': 'Add active target', 'detail': 'Configure at least one active HTTP integration target so alerts can leave the dashboard.'})
        if failed_total > 0:
            next_actions.append({'label': 'Review failed deliveries', 'detail': 'Inspect failed deliveries and dead letters before trusting external routing.'})
        if outbox_total > 0:
            next_actions.append({'label': 'Reduce queue pressure', 'detail': 'Work through queued outbox jobs and coordination pressure to avoid delayed notifications.'})
        if not next_actions:
            next_actions.append({'label': 'Current posture', 'detail': 'Notification delivery is aligned with the current operator routing plan.'})

        return {
            'posture': posture,
            'notifications_enabled': enabled,
            'dispatch_candidates_total': dispatch_candidates_total,
            'external_routing_ready': external_routing_ready,
            'http_enabled': http_enabled,
            'active_targets': active_targets,
            'deliveries_total': deliveries_total,
            'failed_total': failed_total,
            'outbox_total': outbox_total,
            'highest_severity': str(notification_center.get('highest_severity', 'ready')),
            'configured_external_channels': configured_external_channels,
            'active_external_channels': active_external_channels,
            'requested_external_channels': requested_external_channels,
            'missing_external_channels': missing_external_channels,
            'inactive_external_channels': inactive_external_channels,
            'platforms_configured': [str(item) for item in summary.get('platforms_configured', []) if str(item)],
            'platforms_active': [str(item) for item in summary.get('platforms_active', []) if str(item)],
            'next_actions': next_actions,
        }

    @staticmethod
    def _normalize_notification_channels(channels: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for channel in channels:
            value = str(channel).strip().lower()
            if not value or value in seen:
                continue
            seen.add(value)
            normalized.append(value)
        return normalized or ['dashboard']

    @staticmethod
    def _notification_channel_scope(channel: str) -> str:
        return 'internal' if str(channel).strip().lower() in {'dashboard', 'email'} else 'external'

    @staticmethod
    def _notification_channel_family(channel: str) -> str:
        value = str(channel).strip().lower()
        if value in {'jira', 'servicenow'}:
            return 'ticketing'
        if value in {'slack', 'teams'}:
            return 'chatops'
        return value or 'unknown'

    def runtime_alerts(
        self,
        *,
        human_ask: dict[str, object],
        role_private_studio: dict[str, object],
        evidence_exports: dict[str, object],
        go_live_readiness: dict[str, object],
        operational_readiness: dict[str, object],
        operator_queue_health: dict[str, object],
        operator_notification_center: dict[str, object],
        guardrail_surface: dict[str, object],
        limit: int = 12,
    ) -> list[dict[str, object]]:
        alerts: list[dict[str, object]] = []
        owner_registration = self.owner_registration()
        sessions = human_ask.get('sessions', []) if isinstance(human_ask.get('sessions', []), list) else []
        studio_summary = role_private_studio.get('summary', {}) if isinstance(role_private_studio.get('summary', {}), dict) else {}
        evidence_summary = evidence_exports.get('summary', {}) if isinstance(evidence_exports.get('summary', {}), dict) else {}
        guardrail_summary = guardrail_surface.get('summary', {}) if isinstance(guardrail_surface.get('summary', {}), dict) else {}

        if not owner_registration.get('registered'):
            alerts.append(
                {
                    'alert_id': 'owner_registration_missing',
                    'tone': 'danger',
                    'eyebrow': 'Onboarding gate',
                    'title': 'Executive owner registration is still missing',
                    'message': 'Register the organization before treating this runtime as a production-ready private or multi-org deployment.',
                    'view': 'health',
                    'action_label': 'Open Runtime Health',
                    'badge': 'registration required',
                    'timestamp': self._utc_now(),
                    'details': {
                        'expected_path': owner_registration.get('path') or '-',
                    },
                }
            )
        elif owner_registration.get('deployment_mode') == 'multi':
            alerts.append(
                {
                    'alert_id': 'owner_registration_multi_mode',
                    'tone': 'accent',
                    'eyebrow': 'Deployment mode',
                    'title': 'Runtime is registered for multi-org governance',
                    'message': 'This runtime is marked multi-org. Keep identity, seat assignment, and visibility boundaries strict as you expand beyond single-organization private use.',
                    'view': 'health',
                    'action_label': 'Review owner registration',
                    'badge': 'multi mode',
                    'timestamp': owner_registration.get('registered_at') or self._utc_now(),
                    'details': {
                        'organization': owner_registration.get('organization_name') or '-',
                        'organization_id': owner_registration.get('organization_id') or '-',
                    },
                }
            )

        out_of_scope_sessions = [
            session
            for session in sessions
            if ((session.get('decision_summary') or {}).get('metadata', {}) or {}).get('scope_status') == 'out_of_scope'
        ]
        human_boundary_sessions = [
            session
            for session in sessions
            if session.get('status') == 'waiting_human'
            or (((session.get('decision_summary') or {}).get('metadata', {}) or {}).get('scope_status') == 'human_only_boundary')
        ]
        guarded_confidence_sessions = [
            session
            for session in sessions
            if ((session.get('summary') or {}).get('confidence_band') == 'guarded')
            and ((session.get('summary') or {}).get('governed_reporting_posture') in {'autonomy_ready', 'guarded_follow_up'})
        ]
        stale_follow_up_sessions = [
            session
            for session in sessions
            if ((session.get('summary') or {}).get('freshness_status') == 'stale')
            and ((session.get('summary') or {}).get('governed_reporting_posture') != 'autonomy_ready')
        ]
        blocked_sessions = [session for session in sessions if session.get('status') == 'blocked']

        if out_of_scope_sessions:
            latest = out_of_scope_sessions[0]
            alerts.append(
                {
                    'alert_id': 'human_ask_out_of_scope',
                    'tone': 'danger',
                    'eyebrow': 'Scope boundary',
                    'title': 'AI stopped because a request moved outside the loaded JD scope',
                    'message': 'The Director refused to continue automation beyond the approved role boundary.',
                    'view': 'human_ask',
                    'action_label': 'Open Human Ask',
                    'badge': f'{len(out_of_scope_sessions)} out of scope',
                    'timestamp': latest.get('updated_at') or latest.get('created_at') or self._utc_now(),
                    'details': {
                        'records_total': len(out_of_scope_sessions),
                        'latest_participant': ((latest.get('participant') or {}).get('display_name') or (latest.get('summary') or {}).get('participant') or '-'),
                        'latest_session_id': latest.get('session_id', '-'),
                    },
                }
            )

        if human_boundary_sessions:
            latest = human_boundary_sessions[0]
            alerts.append(
                {
                    'alert_id': 'human_ask_human_boundary',
                    'tone': 'warning',
                    'eyebrow': 'Human boundary',
                    'title': 'AI paused at a reserved human decision boundary',
                    'message': 'Automation stopped at the intended handoff line because the request reached a human-only or sensitive decision point.',
                    'view': 'human_ask',
                    'action_label': 'Review records',
                    'badge': f'{len(human_boundary_sessions)} waiting',
                    'timestamp': latest.get('updated_at') or latest.get('created_at') or self._utc_now(),
                    'details': {
                        'records_total': len(human_boundary_sessions),
                        'latest_participant': ((latest.get('participant') or {}).get('display_name') or (latest.get('summary') or {}).get('participant') or '-'),
                        'latest_session_id': latest.get('session_id', '-'),
                    },
                }
            )

        if guarded_confidence_sessions:
            latest = guarded_confidence_sessions[0]
            alerts.append(
                {
                    'alert_id': 'human_ask_guarded_confidence',
                    'tone': 'warning',
                    'eyebrow': 'Confidence guard',
                    'title': 'Human Ask confidence is near the escalation threshold',
                    'message': 'The Director kept the reporting lane governed, but confidence is close enough to the configured threshold that operators should review the follow-up posture before treating it as fully settled.',
                    'view': 'human_ask',
                    'action_label': 'Review governed reports',
                    'badge': f"{len(guarded_confidence_sessions)} guarded",
                    'timestamp': latest.get('updated_at') or latest.get('created_at') or self._utc_now(),
                    'details': {
                        'records_total': len(guarded_confidence_sessions),
                        'latest_participant': ((latest.get('participant') or {}).get('display_name') or (latest.get('summary') or {}).get('participant') or '-'),
                        'latest_session_id': latest.get('session_id', '-'),
                        'confidence_threshold': float((latest.get('summary') or {}).get('confidence_threshold', 0.0) or 0.0),
                    },
                }
            )

        if stale_follow_up_sessions:
            latest = stale_follow_up_sessions[0]
            oldest_age_hours = max(int((session.get('summary') or {}).get('freshness_age_hours', 0) or 0) for session in stale_follow_up_sessions)
            posture_set = {str((session.get('summary') or {}).get('governed_reporting_posture', 'autonomy_ready')) for session in stale_follow_up_sessions}
            alerts.append(
                {
                    'alert_id': 'human_ask_stale_follow_up',
                    'tone': 'danger' if posture_set & {'human_gated', 'blocked'} else 'warning',
                    'eyebrow': 'Freshness posture',
                    'title': 'Human Ask follow-up records have gone stale',
                    'message': 'Some governed reporting records are now outside the freshness window and should be refreshed or resolved before operators rely on them as current status.',
                    'view': 'human_ask',
                    'action_label': 'Refresh governed reports',
                    'badge': f"{len(stale_follow_up_sessions)} stale",
                    'timestamp': latest.get('updated_at') or latest.get('created_at') or self._utc_now(),
                    'details': {
                        'records_total': len(stale_follow_up_sessions),
                        'latest_participant': ((latest.get('participant') or {}).get('display_name') or (latest.get('summary') or {}).get('participant') or '-'),
                        'latest_session_id': latest.get('session_id', '-'),
                        'oldest_age_hours': oldest_age_hours,
                    },
                }
            )

        if blocked_sessions:
            latest = blocked_sessions[0]
            alerts.append(
                {
                    'alert_id': 'human_ask_blocked_lane',
                    'tone': 'warning',
                    'eyebrow': 'Callable lane',
                    'title': 'AI could not continue because the callable or structural lane is blocked',
                    'message': 'A report record was created, but the Director could not proceed because structural posture or callable availability stopped execution.',
                    'view': 'human_ask',
                    'action_label': 'Inspect blocked records',
                    'badge': f'{len(blocked_sessions)} blocked',
                    'timestamp': latest.get('updated_at') or latest.get('created_at') or self._utc_now(),
                    'details': {
                        'records_total': len(blocked_sessions),
                        'latest_participant': ((latest.get('participant') or {}).get('display_name') or (latest.get('summary') or {}).get('participant') or '-'),
                        'latest_session_id': latest.get('session_id', '-'),
                    },
                }
            )

        manual_override_total = int(studio_summary.get('manual_override_total', 0) or 0)
        restored_request_total = int(studio_summary.get('restored_request_total', 0) or 0)
        publisher_ready_total = int(studio_summary.get('publisher_ready_total', 0) or 0)
        structural_guarded_total = int(studio_summary.get('structural_guarded_total', 0) or 0)
        structural_blocked_total = int(studio_summary.get('structural_blocked_total', 0) or 0)
        structural_ready_total = int(studio_summary.get('structural_ready_total', 0) or 0)
        pt_oss_critical_total = int(studio_summary.get('pt_oss_critical_total', 0) or 0)
        pt_oss_public_sector_total = int(studio_summary.get('pt_oss_public_sector_mode_total', 0) or 0)
        authority_human_required_total = int(guardrail_summary.get('authority_guard_human_required_total', 0) or 0)
        authority_blocked_total = int(guardrail_summary.get('authority_guard_blocked_total', 0) or 0)
        resource_lock_waiting_total = int(guardrail_summary.get('resource_lock_waiting_total', 0) or 0)
        resource_lock_conflict_total = int(guardrail_summary.get('resource_lock_conflict_total', 0) or 0)
        if manual_override_total or restored_request_total:
            alerts.append(
                {
                    'alert_id': 'studio_revision_governance',
                    'tone': 'warning',
                    'eyebrow': 'Studio revision governance',
                    'title': 'Role Private Studio has drafts with manual or restored revision state',
                    'message': 'Some studio drafts carry manual PTAG edits or restored revisions. Keep review and publication checks explicit before treating them as ready for trusted release.',
                    'view': 'studio',
                    'action_label': 'Open Studio',
                    'badge': f"{manual_override_total + restored_request_total} drafts",
                    'timestamp': self._utc_now(),
                    'details': {
                        'manual_override_total': manual_override_total,
                        'restored_request_total': restored_request_total,
                        'publisher_ready_total': publisher_ready_total,
                    },
                }
            )
        if structural_guarded_total or structural_blocked_total:
            tone = 'danger' if structural_blocked_total else 'warning'
            alerts.append(
                {
                    'alert_id': 'studio_structural_pressure',
                    'tone': tone,
                    'eyebrow': 'Studio structural review',
                    'title': 'Role Private Studio still has drafts under PT-OSS pressure',
                    'message': 'Some hats are not ready for trusted publication because structural resilience or fragility concerns are still active.',
                    'view': 'studio',
                    'action_label': 'Open Studio',
                    'badge': f'{structural_guarded_total + structural_blocked_total} drafts',
                    'timestamp': self._utc_now(),
                    'details': {
                        'guarded_total': structural_guarded_total,
                        'blocked_total': structural_blocked_total,
                        'ready_total': int(studio_summary.get('ready_to_publish_total', 0) or 0),
                        'structural_ready_total': structural_ready_total,
                        'pt_oss_critical_total': pt_oss_critical_total,
                        'pt_oss_public_sector_total': pt_oss_public_sector_total,
                    },
                }
            )

        if authority_human_required_total or authority_blocked_total:
            alerts.append(
                {
                    'alert_id': 'authority_guard_attention',
                    'tone': 'danger' if authority_blocked_total else 'warning',
                    'eyebrow': 'Authority guard',
                    'title': 'Authority Guard is actively holding governed requests',
                    'message': 'Some requests were blocked or paused for human confirmation because authority boundaries were triggered as designed.',
                    'view': 'requests',
                    'action_label': 'Review governed requests',
                    'badge': f"{authority_human_required_total + authority_blocked_total} requests",
                    'timestamp': self._utc_now(),
                    'details': {
                        'authority_human_required_total': authority_human_required_total,
                        'authority_blocked_total': authority_blocked_total,
                        'resource_lock_waiting_total': resource_lock_waiting_total,
                    },
                }
            )

        if resource_lock_waiting_total or resource_lock_conflict_total:
            alerts.append(
                {
                    'alert_id': 'resource_lock_pressure',
                    'tone': 'danger' if resource_lock_conflict_total else 'warning',
                    'eyebrow': 'Resource lock',
                    'title': 'Resource Lock is governing live contention or held approvals',
                    'message': 'Concurrent access to governed resources is currently serialized by lock state, conflict detection, or pending human review.',
                    'view': 'requests',
                    'action_label': 'Review lock state',
                    'badge': f"{resource_lock_waiting_total + resource_lock_conflict_total} signals",
                    'timestamp': self._utc_now(),
                    'details': {
                        'resource_lock_waiting_total': resource_lock_waiting_total,
                        'resource_lock_conflict_total': resource_lock_conflict_total,
                        'authority_guard_human_required_total': authority_human_required_total,
                    },
                }
            )

        trust_attention_total = int(studio_summary.get('trust_attention_total', 0) or 0)
        published_total = int(studio_summary.get('published_total', 0) or 0)
        published_live_hash_verified_total = int(studio_summary.get('published_live_hash_verified_total', 0) or 0)
        published_current_revision_total = int(studio_summary.get('published_current_revision_total', 0) or 0)
        if trust_attention_total:
            alerts.append(
                {
                    'alert_id': 'studio_trusted_registry_drift',
                    'tone': 'danger',
                    'eyebrow': 'Trusted publication drift',
                    'title': 'Published studio roles have drifted from their trusted registry contract',
                    'message': 'One or more published role packs no longer match the trusted live hash, signature posture, or approved revision contract. Review them before treating the role library as fully trusted.',
                    'view': 'studio',
                    'action_label': 'Review published roles',
                    'badge': f'{trust_attention_total} roles',
                    'timestamp': self._utc_now(),
                    'details': {
                        'published_total': published_total,
                        'published_live_hash_verified_total': published_live_hash_verified_total,
                        'published_current_revision_total': published_current_revision_total,
                    },
                }
            )

        evidence_attention_total = int(evidence_summary.get('attention_total', 0) or 0)
        trusted_role_mismatch_total = int(evidence_summary.get('trusted_role_mismatch_total', 0) or 0)
        latest_export = evidence_summary.get('latest_export', {}) if isinstance(evidence_summary.get('latest_export', {}), dict) else {}
        if evidence_attention_total:
            alerts.append(
                {
                    'alert_id': 'evidence_export_attention',
                    'tone': 'danger',
                    'eyebrow': 'Evidence integrity posture',
                    'title': 'Recent evidence exports captured audit or trust attention signals',
                    'message': 'The latest evidence pack shows integrity attention, so exported proof should be reviewed before it is treated as a clean auditor-ready bundle.',
                    'view': 'health',
                    'action_label': 'Open Evidence Exports',
                    'badge': f'{evidence_attention_total} exports',
                    'timestamp': str(latest_export.get('created_at') or self._utc_now()),
                    'details': {
                        'latest_pack_id': latest_export.get('pack_id') or '-',
                        'audit_chain_status': latest_export.get('audit_chain_status') or 'unknown',
                        'trusted_registry_signature_status': latest_export.get('trusted_registry_signature_status') or 'unknown',
                        'trusted_role_mismatch_total': trusted_role_mismatch_total,
                    },
                }
            )

        for item in operator_queue_health.get('items', []):
            if item.get('total', 0) <= 0 or item.get('status') == 'ready':
                continue
            age_hours = float(item.get('oldest_age_hours', 0) or 0)
            alerts.append(
                {
                    'alert_id': f"operator_queue_{item.get('lane_id')}",
                    'tone': 'danger' if item.get('status') in {'critical', 'stale'} else 'warning',
                    'eyebrow': 'Operator queue health',
                    'title': f"{item.get('title')} need attention",
                    'message': f"The oldest item in this lane has been waiting about {ceil(age_hours)} hours, so the runtime should not leave it unattended.",
                    'view': item.get('view', 'overview'),
                    'action_label': 'Open queue',
                    'badge': f"{item.get('total', 0)} queued",
                    'timestamp': self._utc_now(),
                    'details': {
                        'status': item.get('status', 'warning'),
                        'oldest_age_hours': ceil(age_hours),
                        'oldest_reference': item.get('oldest_reference') or '-',
                    },
                }
            )

        backlog_total = int((operational_readiness.get('summary', {}) or {}).get('active_workflow_total', 0) or 0)
        backlog_policy = (operator_queue_health.get('policy', {}) or {}).get('backlog', {}) if isinstance(operator_queue_health.get('policy', {}), dict) else {}
        backlog_warning_total = int(backlog_policy.get('warning_total', 3) or 3)
        backlog_critical_total = int(backlog_policy.get('critical_total', backlog_warning_total) or backlog_warning_total)
        if backlog_total >= backlog_warning_total:
            alerts.append(
                {
                    'alert_id': 'operator_workflow_backlog_pressure',
                    'tone': 'danger' if backlog_total >= backlog_critical_total else 'warning',
                    'eyebrow': 'Workflow accumulation',
                    'title': 'Live workflow backlog is accumulating beyond the operator threshold',
                    'message': 'The runtime has enough active governed work in flight that operator review should confirm the queues are not silently aging behind the scenes.',
                    'view': 'requests',
                    'action_label': 'Open Requests',
                    'badge': f'{backlog_total} active',
                    'timestamp': self._utc_now(),
                    'details': {
                        'warning_total': backlog_warning_total,
                        'critical_total': backlog_critical_total,
                        'human_inbox_open': int((operational_readiness.get('summary', {}) or {}).get('human_inbox_total', 0) or 0),
                    },
                }
            )

        if go_live_readiness.get('status') in {'guarded', 'blocked'}:
            alerts.append(
                {
                    'alert_id': 'go_live_pressure',
                    'tone': 'danger' if go_live_readiness.get('status') == 'blocked' else 'warning',
                    'eyebrow': 'Go-live posture',
                    'title': 'Production posture still needs attention',
                    'message': 'The current private-server deployment gate is not fully clear, so readiness should be reviewed before calling the runtime production-ready.',
                    'view': 'health',
                    'action_label': 'Open Health',
                    'badge': str(go_live_readiness.get('status', 'blocked')),
                    'timestamp': self._utc_now(),
                    'details': {
                        'blockers': len(go_live_readiness.get('blockers', []) or []),
                        'advisories': len(go_live_readiness.get('advisories', []) or []),
                        'privileged_ops': (go_live_readiness.get('privileged_operations', {}) or {}).get('status', 'unknown'),
                    },
                }
            )

        alerts.sort(key=lambda item: (0 if item.get('tone') == 'danger' else 1, item.get('timestamp', '')), reverse=False)
        return alerts[:limit]

    def _operator_queue_status(
        self,
        *,
        total: int,
        oldest_hours: int,
        warning_hours: int,
        critical_hours: int,
        stale_hours: int,
        backlog_warning_total: int,
        backlog_critical_total: int,
    ) -> str:
        if total <= 0:
            return 'ready'
        if oldest_hours >= stale_hours:
            return 'stale'
        if total >= backlog_critical_total or oldest_hours >= critical_hours:
            return 'critical'
        if total >= backlog_warning_total or oldest_hours >= warning_hours:
            return 'warning'
        return 'monitoring'

    def _oldest_record(self, rows: list[dict[str, object]], timestamp_fields: list[str]) -> dict[str, object] | None:
        if not rows:
            return None
        dated = [row for row in rows if self._parse_timestamp(self._first_present(row, timestamp_fields)) is not None]
        if not dated:
            return rows[0]
        return min(dated, key=lambda row: self._parse_timestamp(self._first_present(row, timestamp_fields)) or datetime.now(timezone.utc))

    def _age_hours(self, row: dict[str, object] | None, timestamp_fields: list[str]) -> int:
        if row is None:
            return 0
        timestamp = self._parse_timestamp(self._first_present(row, timestamp_fields))
        if timestamp is None:
            return 0
        return max(0, int((datetime.now(timezone.utc) - timestamp).total_seconds() // 3600))

    def _first_present(self, row: dict[str, object], fields: list[str]) -> str | None:
        for field in fields:
            value = row.get(field)
            if value not in (None, ''):
                return str(value)
        return None

    def _parse_timestamp(self, value: str | None) -> datetime | None:
        if value in (None, ''):
            return None
        try:
            return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        except ValueError:
            return None

    def _resource_label(self, payload: dict[str, object]) -> str:
        resource = payload.get('resource')
        if resource in (None, ''):
            return '-'
        resource_id = payload.get('resource_id') or payload.get('target_id') or payload.get('contract_id') or payload.get('id')
        return str(resource) if resource_id in (None, '') else f'{resource}:{resource_id}'

    def _file_health(self, path: Path | None) -> dict[str, object]:
        if path is None:
            return {'status': 'disabled', 'path': None, 'bytes': 0}
        return {'status': 'present' if path.exists() else 'missing', 'path': str(path), 'bytes': path.stat().st_size if path.exists() else 0}

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


def build_dashboard_snapshot() -> dict[str, object]:
    return DashboardSnapshotBuilder().build()

