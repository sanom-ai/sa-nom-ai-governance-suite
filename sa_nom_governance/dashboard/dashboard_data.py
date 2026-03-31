from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from sa_nom_governance.api.api_engine import EngineApplication, build_engine_app
from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.deployment.deployment_profile import build_deployment_report
from sa_nom_governance.deployment.go_live_readiness import build_go_live_readiness
from sa_nom_governance.utils.registry import RoleRegistry
from sa_nom_governance.compliance.retention_manager import RetentionManager
from sa_nom_governance.ptag.role_loader import RoleLoader


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
        roles = self.list_roles()
        sessions = self.list_sessions()
        retention = self.retention_report()
        retention_plan = self.retention_plan()
        role_private_studio = self.role_private_studio()
        human_ask = self.human_ask()
        go_live_readiness = self.go_live_readiness()
        operational_readiness = self.app.operational_readiness(limit=50)
        operator_decision_lanes = self.build_operator_decision_lanes(operational_readiness)
        operations = self.operations()
        compliance = self.compliance_snapshot()
        evidence_exports = self.evidence_exports()
        integrations = self.integrations()
        model_providers = self.model_providers()
        runtime_alerts = self.runtime_alerts(
            human_ask=human_ask,
            role_private_studio=role_private_studio,
            go_live_readiness=go_live_readiness,
        )

        conflicts = [request for request in requests if request['outcome'] == 'conflicted']
        escalated = [request for request in requests if request['outcome'] in {'escalated', 'waiting_human'}]
        pending_overrides = [item for item in overrides if item['status'] == 'pending']

        return {
            'generated_at': self._utc_now(),
            'product': 'SA-NOM AI Governance Suite',
            'environment': self.config.environment,
            'owner_registration': self.owner_registration(),
            'summary': {
                'requests_total': len(requests),
                'pending_overrides': len(pending_overrides),
                'active_locks': len(locks),
                'conflicts_total': len(conflicts),
                'escalated_total': len(escalated),
                'audit_events': len(audit_entries),
                'studio_requests_total': role_private_studio.get('summary', {}).get('requests_total', 0),
                'studio_ready_to_publish_total': role_private_studio.get('summary', {}).get('ready_to_publish_total', 0),
                'studio_structural_guarded_total': role_private_studio.get('summary', {}).get('structural_guarded_total', 0),
                'studio_structural_blocked_total': role_private_studio.get('summary', {}).get('structural_blocked_total', 0),
                'human_ask_sessions_total': human_ask.get('summary', {}).get('sessions_total', 0),
                'human_ask_callable_total': human_ask.get('summary', {}).get('callable_total', 0),
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
                'operator_human_required_total': sum(
                    1 for lane in operator_decision_lanes if lane.get('disposition') == 'human_required'
                ),
                'operator_blocked_total': sum(
                    1 for lane in operator_decision_lanes if lane.get('disposition') == 'blocked'
                ),
                'backups_total': operations.get('summary', {}).get('backups_total', 0),
                'usability_proof_status': operations.get('usability_proof', {}).get('status', 'missing'),
                'usability_proof_available': bool(operations.get('usability_proof', {}).get('available', False)),
                'frameworks_total': compliance.get('summary', {}).get('frameworks_total', 0),
                'evidence_exports_total': evidence_exports.get('summary', {}).get('exports_total', 0),
                'integration_targets_total': integrations.get('summary', {}).get('targets_total', 0),
                'integration_deliveries_total': integrations.get('summary', {}).get('deliveries_total', 0),
                'integration_failures_total': integrations.get('summary', {}).get('failed_total', 0),
                'integration_outbox_total': integrations.get('summary', {}).get('outbox_total', 0),
                'model_providers_configured_total': model_providers.get('configured_providers', 0),
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
            'operations': operations,
            'compliance': compliance,
            'evidence_exports': evidence_exports,
            'integrations': integrations,
            'model_providers': model_providers,
            'go_live_readiness': go_live_readiness,
            'operational_readiness': operational_readiness,
            'operator_decision_lanes': operator_decision_lanes,
            'runtime_alerts': runtime_alerts,
            'runtime_health': self.runtime_health(roles=roles, go_live_readiness=go_live_readiness),
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
            metadata = entry.get('metadata', {})
            context = metadata.get('context', {})
            if not context or str(entry.get('action', '')).startswith('override_'):
                continue
            consistency = context.get('metadata', {}).get('request_consistency', {})
            role_transition = context.get('role_transition', {}) if isinstance(context.get('role_transition', {}), dict) else {}
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
                    'idempotency_status': consistency.get('idempotency_status', 'none'),
                    'ordering_status': consistency.get('ordering_status', 'none'),
                    'event_stream': consistency.get('event_stream', '-'),
                    'event_sequence': consistency.get('event_sequence', '-'),
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

    def list_audit(self, limit: int = 200) -> list[dict[str, object]]:
        return self.app.list_audit(limit=limit)

    def list_sessions(self, status: str | None = None, limit: int = 100) -> list[dict[str, object]]:
        return self.app.list_sessions(status=status)[:limit]

    def list_roles(self) -> list[dict[str, object]]:
        roles = self.app.list_roles()
        compliance = self.app.compliance_snapshot()
        mapping_index = {item['role_id']: item.get('controls', []) for item in compliance.get('role_mappings', [])}
        for role in roles:
            role['control_refs'] = mapping_index.get(role['role_id'], [])
        return roles

    def role_private_studio(self, limit: int = 50) -> dict[str, object]:
        return self.app.studio_snapshot(limit=limit)

    def human_ask(self, limit: int = 50) -> dict[str, object]:
        return self.app.human_ask_snapshot(limit=limit)

    def operations(self, limit: int = 10) -> dict[str, object]:
        return {
            'summary': self.app.runtime_backup_summary(),
            'backups': self.app.list_runtime_backups(limit=limit),
            'usability_proof': self.usability_proof_summary(),
        }

    def usability_proof_summary(self) -> dict[str, object]:
        from sa_nom_governance.deployment.usability_proof_bundle import read_usability_proof_bundle

        result = read_usability_proof_bundle(config=self.config)
        return {
            'status': result.get('status', 'missing'),
            'available': bool(result.get('available', False)),
            'path': str(result.get('output_path', self.config.review_dir / 'usability_proof_bundle.json')),
            'generated_at': result.get('generated_at'),
            'passed': bool(result.get('passed', False)),
            'milestone': str(result.get('milestone', 'v0.3.0')),
        }

    def retention_report(self) -> dict[str, object]:
        return self.app.retention_report()

    def retention_plan(self) -> dict[str, object]:
        return self.app.retention_plan()

    def go_live_readiness(self) -> dict[str, object]:
        return build_go_live_readiness(self.config, app=self.app)

    def compliance_snapshot(self) -> dict[str, object]:
        return self.app.compliance_snapshot()

    def evidence_exports(self, limit: int = 20) -> dict[str, object]:
        return {
            'summary': self.app.evidence_pack_summary(),
            'exports': self.app.list_evidence_packs(limit=limit),
        }

    def integrations(self, limit: int = 50) -> dict[str, object]:
        return self.app.integration_snapshot(limit=limit)

    def model_providers(self) -> dict[str, object]:
        return self.app.model_provider_snapshot()

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

    def runtime_health(self, roles: list[dict[str, object]] | None = None, go_live_readiness: dict[str, object] | None = None) -> dict[str, object]:
        known_roles = roles if roles is not None else self.list_roles()
        app_health = self.app.health()
        deployment_profile = build_deployment_report(self.config).to_dict()
        readiness = go_live_readiness if go_live_readiness is not None else self.go_live_readiness()
        return {
            'engine_status': app_health.get('status', 'unknown'),
            'owner_registration': self.owner_registration(),
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
            'trusted_registry': app_health.get('trusted_registry', {}),
            'request_consistency': app_health.get('request_consistency', {}),
            'audit_integrity': app_health.get('audit_integrity', {}),
            'access_control': self.access_control.health(),
            'deployment_profile': deployment_profile,
            'go_live_readiness': readiness,
            'privileged_operations': readiness.get('privileged_operations', {}),
            'studio_structural': readiness.get('studio_structural', {}),
            'retention': app_health.get('retention', self.retention_manager.summary()),
            'role_private_studio': app_health.get('role_private_studio', {}),
            'human_ask': app_health.get('human_ask', {}),
            'runtime_backups': app_health.get('runtime_backups', {}),
            'role_hierarchy': app_health.get('role_hierarchy', {}),
            'role_transition_policy': app_health.get('role_transition_policy', {}),
            'persistence_layer': app_health.get('persistence_layer', {}),
            'compliance_frameworks': app_health.get('compliance_frameworks', {}),
            'evidence_exports': app_health.get('evidence_exports', {}),
            'integration_registry': app_health.get('integration_registry', {}),
            'model_providers': app_health.get('model_providers', {}),
            'integration_deliveries': app_health.get('integration_deliveries', {}),
            'coordination_layer': app_health.get('coordination_layer', {}),
            'ptag_modules': len(known_roles),
            'token_gate': 'enabled' if self.config.api_token else 'disabled',
            'legal_hold_file': self._file_health(self.config.legal_hold_path),
        }

    def runtime_alerts(
        self,
        *,
        human_ask: dict[str, object],
        role_private_studio: dict[str, object],
        go_live_readiness: dict[str, object],
        limit: int = 12,
    ) -> list[dict[str, object]]:
        alerts: list[dict[str, object]] = []
        owner_registration = self.owner_registration()
        sessions = human_ask.get('sessions', []) if isinstance(human_ask.get('sessions', []), list) else []
        studio_summary = role_private_studio.get('summary', {}) if isinstance(role_private_studio.get('summary', {}), dict) else {}

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

        structural_guarded_total = int(studio_summary.get('structural_guarded_total', 0) or 0)
        structural_blocked_total = int(studio_summary.get('structural_blocked_total', 0) or 0)
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
