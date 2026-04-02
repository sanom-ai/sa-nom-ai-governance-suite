from dataclasses import asdict

from sa_nom_governance.audit.auditor_evidence_pack import AuditorEvidencePackBuilder
from sa_nom_governance.compliance.compliance_registry import ComplianceFrameworkRegistry
from sa_nom_governance.compliance.retention_manager import RetentionManager
from sa_nom_governance.core.core_engine import CoreEngine
from sa_nom_governance.deployment.go_live_readiness import build_go_live_readiness
from sa_nom_governance.deployment.runtime_backup_manager import RuntimeBackupManager
from sa_nom_governance.guards.access_control import AccessControl
from sa_nom_governance.human_ask.human_ask_service import HumanAskService
from sa_nom_governance.integrations.integration_registry import IntegrationRegistry
from sa_nom_governance.integrations.model_provider_registry import ModelProviderRegistry
from sa_nom_governance.integrations.webhook_dispatcher import WebhookDispatcher
from sa_nom_governance.ptag.role_loader import RoleLoader
from sa_nom_governance.studio.role_private_studio_service import RolePrivateStudioService
from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.utils.registry import RoleRegistry


class EngineApplication:
    def __init__(
        self,
        engine: CoreEngine,
        loader: RoleLoader,
        registry: RoleRegistry,
        retention_manager: RetentionManager,
        access_control: AccessControl,
        role_private_studio: RolePrivateStudioService,
        human_ask: HumanAskService,
        backup_manager: RuntimeBackupManager,
        compliance_registry: ComplianceFrameworkRegistry,
        evidence_builder: AuditorEvidencePackBuilder,
        integration_registry: IntegrationRegistry,
        model_provider_registry: ModelProviderRegistry,
        integration_dispatcher: WebhookDispatcher,
    ) -> None:
        self.engine = engine
        self.loader = loader
        self.registry = registry
        self.retention_manager = retention_manager
        self.access_control = access_control
        self.role_private_studio = role_private_studio
        self.human_ask = human_ask
        self.backup_manager = backup_manager
        self.compliance_registry = compliance_registry
        self.evidence_builder = evidence_builder
        self.integration_registry = integration_registry
        self.model_provider_registry = model_provider_registry
        self.integration_dispatcher = integration_dispatcher

    def _base_health(self, roles: list[dict[str, object]] | None = None) -> dict[str, object]:
        trusted_registry_health = self.registry.trusted_registry.health()
        consistency_health = self.engine.request_consistency.health()
        audit_integrity = self.engine.audit_logger.health()
        retention_summary = self.retention_manager.summary()
        studio_summary = self.role_private_studio.studio_snapshot(limit=20).get('summary', {})
        human_ask_summary = self.human_ask.human_ask_snapshot(limit=20).get('summary', {})
        backup_summary = self.backup_manager.summary()
        known_roles = roles if roles is not None else self.list_roles()
        invalid_roles = [role for role in known_roles if role.get('status') == 'invalid']
        hierarchy_summary = self.engine.hierarchy_registry.health()
        governance_materials = {
            'status': 'degraded' if invalid_roles or int(hierarchy_summary.get('invalid_entries_total', 0) or 0) > 0 else 'ready',
            'invalid_roles_total': len(invalid_roles),
            'invalid_roles': [
                {
                    'role_id': role.get('role_id'),
                    'title': role.get('title'),
                    'load_error': role.get('load_error', {}),
                }
                for role in invalid_roles
            ],
            'invalid_hierarchy_entries_total': int(hierarchy_summary.get('invalid_entries_total', 0) or 0),
            'invalid_hierarchy_entries': hierarchy_summary.get('invalid_entries', []),
        }
        store_descriptors = {
            'audit': self.engine.audit_logger.ledger.descriptor().to_dict(),
            'overrides': self.engine.human_override.store.descriptor().to_dict(),
            'locks': self.engine.lock_manager.store.descriptor().to_dict(),
            'consistency': self.engine.request_consistency.store.descriptor().to_dict(),
            'sessions': self.access_control.session_manager.store.descriptor().to_dict(),
            'role_private_studio': self.role_private_studio.store.store.descriptor().to_dict(),
            'human_ask': self.human_ask.store.store.descriptor().to_dict(),
            'workflow_state': self.engine.workflow_state_store.store.descriptor().to_dict(),
            'runtime_recovery': self.engine.runtime_recovery_store.store.descriptor().to_dict(),
            'runtime_dead_letters': self.engine.runtime_recovery_store.dead_letter_ledger.descriptor().to_dict(),
            'integration_deliveries': self.integration_dispatcher.ledger.descriptor().to_dict(),
            'integration_dead_letters': self.integration_dispatcher.dead_letter_ledger.descriptor().to_dict(),
        }
        configured_backends = sorted({str(item.get('configured_backend', item.get('backend', 'file'))) for item in store_descriptors.values()})
        runtime_backends = sorted({str(item.get('backend', 'unknown')) for item in store_descriptors.values()})
        fallback_stores = sorted(name for name, item in store_descriptors.items() if item.get('mode') == 'fallback')
        native_stores = sorted(name for name, item in store_descriptors.items() if item.get('mode') == 'native' and item.get('configured_backend') == 'postgresql')
        configured_drivers = sorted({str(item.get('driver')) for item in store_descriptors.values() if item.get('driver')})
        if native_stores:
            persistence_status = 'postgresql_native'
        elif fallback_stores and 'postgresql' in configured_backends:
            persistence_status = 'postgresql_ready_fallback'
        else:
            persistence_status = 'abstracted'

        persistence_summary = {
            'status': persistence_status,
            'configured_backends': configured_backends,
            'runtime_backends': runtime_backends,
            'configured_drivers': configured_drivers,
            'fallback_stores': fallback_stores,
            'native_stores': native_stores,
            'postgresql_requested': 'postgresql' in configured_backends,
            'postgresql_native_ready': not fallback_stores and 'postgresql' in configured_backends,
            'stores': store_descriptors,
        }

        status = 'ok'
        if (
            not trusted_registry_health.get('signature_trusted', False)
            or audit_integrity.get('status') == 'broken'
            or governance_materials.get('status') == 'degraded'
        ):
            status = 'degraded'

        return {
            'status': status,
            'trusted_registry': trusted_registry_health,
            'request_consistency': consistency_health,
            'audit_integrity': audit_integrity,
            'retention': retention_summary,
            'role_private_studio': studio_summary,
            'human_ask': human_ask_summary,
            'runtime_backups': backup_summary,
            'role_hierarchy': hierarchy_summary,
            'governance_materials': governance_materials,
            'role_transition_policy': self.engine.role_transition_policy.health(),
            'persistence_layer': persistence_summary,
            'integration_registry': self.integration_registry.health(),
            'model_providers': self.model_provider_registry.health(),
            'integration_deliveries': self.integration_dispatcher.health(),
            'coordination_layer': self.integration_dispatcher.health().get('coordination', {}),
            'workflow_state': self.engine.workflow_state_store.summary(),
            'runtime_recovery': self.engine.runtime_recovery_store.summary(),
            'role_library': {
                'roles_total': len(known_roles),
                'roles_ready_total': sum(1 for role in known_roles if role.get('status') != 'invalid'),
                'roles_invalid_total': len(invalid_roles),
                'trusted_verified': sum(1 for role in known_roles if role.get('trusted_manifest_signature_status') == 'verified'),
                'invalid_roles': governance_materials.get('invalid_roles', []),
            },
        }

    def health(self) -> dict[str, object]:
        roles = self.list_roles()
        base = self._base_health(roles=roles)
        access_health = self.access_control.health()
        evidence_summary = self.evidence_builder.summary()
        compliance_snapshot = self.compliance_registry.build_snapshot(
            runtime_health=base,
            access_control_health=access_health,
            roles=roles,
            evidence_summary=evidence_summary,
        )
        return {
            **base,
            'compliance_frameworks': compliance_snapshot['summary'],
            'evidence_exports': evidence_summary,
        }

    def operational_readiness(self, *, limit: int = 50) -> dict[str, object]:
        def inbox_state(item: dict[str, object]) -> str:
            inbox = item.get('human_decision_inbox')
            if isinstance(inbox, dict):
                return str(inbox.get('inbox_state', 'autonomy_ready'))
            return 'autonomy_ready'

        health = self.health()
        workflow_items = self.list_workflow_states(limit=limit)
        recovery_items = self.list_runtime_recovery_records(limit=limit)
        dead_letters = self.list_runtime_dead_letters(limit=limit)
        inbox_items = self.list_human_decision_inbox(limit=limit)

        blocked_workflows = [
            item
            for item in workflow_items
            if str(item.get('current_state', '')) in {'blocked', 'awaiting_human_confirmation'}
        ]
        active_workflows = [
            item
            for item in workflow_items
            if str(item.get('current_state', '')) not in {'completed', 'rejected'}
        ]
        dead_letter_records = [item for item in recovery_items if str(item.get('status', '')) == 'dead_letter']
        human_action_items = [item for item in inbox_items if inbox_state(item) == 'human_action_required']
        clearance_items = [item for item in inbox_items if inbox_state(item) == 'clearance_required']
        guarded_items = [item for item in inbox_items if inbox_state(item) == 'guarded_follow_up']

        status = 'ready'
        if dead_letter_records or clearance_items:
            status = 'attention_required'
        elif human_action_items or guarded_items or blocked_workflows:
            status = 'monitoring'

        action_required: list[str] = []
        if clearance_items:
            action_required.append('clearance_review')
        if human_action_items:
            action_required.append('human_decision')
        if dead_letter_records:
            action_required.append('recovery_resume')
        if guarded_items:
            action_required.append('guarded_follow_up')

        return {
            'status': status,
            'summary': {
                'workflow_total': len(workflow_items),
                'active_workflow_total': len(active_workflows),
                'blocked_workflow_total': len(blocked_workflows),
                'human_inbox_total': len(inbox_items),
                'human_action_total': len(human_action_items),
                'clearance_total': len(clearance_items),
                'guarded_follow_up_total': len(guarded_items),
                'recovery_total': len(recovery_items),
                'dead_letter_total': len(dead_letter_records),
                'dead_letter_event_total': len(dead_letters),
                'action_required_total': len(action_required),
            },
            'action_required': action_required,
            'health': {
                'status': health.get('status', 'unknown'),
                'persistence_layer': health.get('persistence_layer', {}),
                'workflow_state': health.get('workflow_state', {}),
                'runtime_recovery': health.get('runtime_recovery', {}),
                'human_ask': health.get('human_ask', {}),
            },
            'operator_visibility': {
                'workflow_backlog': workflow_items,
                'human_decision_inbox': inbox_items,
                'runtime_recovery_backlog': recovery_items,
                'runtime_dead_letters': dead_letters,
            },
        }

    def request(self, requester: str, role_id: str | None, action: str, payload: dict, metadata: dict | None = None):
        result = self.engine.process(requester=requester, role_id=role_id, action=action, payload=payload, metadata=metadata)
        self._dispatch_integration_event(
            'runtime.request.completed',
            payload={
                'requester': requester,
                'action': action,
                'requested_role': role_id,
                'active_role': result.active_role,
                'outcome': result.outcome,
                'reason': result.reason,
                'policy_basis': result.policy_basis,
                'risk_score': result.risk_score,
                'role_transition': result.role_transition or {},
                'resource_lock': result.resource_lock,
                'human_override': result.human_override,
            },
            source='runtime',
            requested_by=requester,
            metadata={'request_id': result.metadata.get('request_id'), 'business_domain': result.metadata.get('business_domain')},
        )
        return result

    def list_workflow_states(self, current_state: str | None = None, limit: int | None = None) -> list[dict[str, object]]:
        return self.engine.list_workflow_states(current_state=current_state, limit=limit)

    def get_workflow_state(self, workflow_id: str) -> dict[str, object]:
        return self.engine.get_workflow_state(workflow_id)

    def list_runtime_recovery_records(
        self,
        *,
        status: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, object]]:
        return self.engine.list_runtime_recovery_records(status=status, limit=limit)

    def list_runtime_dead_letters(self, *, limit: int | None = None) -> list[dict[str, object]]:
        return self.engine.list_runtime_dead_letters(limit=limit)

    def resume_runtime_recovery(self, request_id: str, resumed_by: str):
        return self.engine.resume_runtime_recovery(request_id, resumed_by)

    def list_overrides(self, status: str | None = None) -> list[dict[str, object]]:
        return self.engine.list_override_requests(status=status)

    def get_override(self, request_id: str) -> dict[str, object]:
        return self.engine.get_override_request(request_id)

    def approve_override(self, request_id: str, resolved_by: str, note: str | None = None):
        result = self.engine.review_override(request_id=request_id, resolved_by=resolved_by, decision='approve', note=note)
        self._dispatch_integration_event(
            'runtime.override.reviewed',
            payload={
                'request_id': result.request_id,
                'decision': 'approve',
                'status': result.status,
                'resolved_by': result.resolved_by,
                'active_role': result.active_role,
                'action': result.action,
                'required_by': result.required_by,
                'execution_result': result.execution_result,
            },
            source='runtime',
            requested_by=resolved_by,
        )
        return result

    def veto_override(self, request_id: str, resolved_by: str, note: str | None = None):
        result = self.engine.review_override(request_id=request_id, resolved_by=resolved_by, decision='veto', note=note)
        self._dispatch_integration_event(
            'runtime.override.reviewed',
            payload={
                'request_id': result.request_id,
                'decision': 'veto',
                'status': result.status,
                'resolved_by': result.resolved_by,
                'active_role': result.active_role,
                'action': result.action,
                'required_by': result.required_by,
            },
            source='runtime',
            requested_by=resolved_by,
        )
        return result

    def list_locks(self, status: str | None = None) -> list[dict[str, object]]:
        return self.engine.list_lock_states(status=status)

    def list_audit(self, limit: int | None = None) -> list[dict[str, object]]:
        return self.engine.list_audit_entries(limit=limit)

    def list_runtime_evidence(
        self,
        *,
        limit: int | None = None,
        outcome: str | None = None,
        source_type: str | None = None,
    ) -> list[dict[str, object]]:
        return self.engine.list_runtime_evidence(
            limit=limit,
            outcome=outcome,
            source_type=source_type,
        )
    def list_runtime_backups(self, limit: int = 20) -> list[dict[str, object]]:
        return self.backup_manager.list_backups(limit=limit)

    def runtime_backup_summary(self) -> dict[str, object]:
        return self.backup_manager.summary()

    def create_runtime_backup(self, requested_by: str) -> dict[str, object]:
        result = self.backup_manager.create_backup(
            requested_by=requested_by,
            metadata={
                'runtime_status': self.health().get('status', 'unknown'),
                'audit_integrity': self.audit_integrity(),
                'trusted_registry': self.registry.trusted_registry.health(),
            },
        )
        self.engine.audit_logger.record_event(
            active_role='SYSTEM',
            action='runtime_backup',
            outcome='completed',
            reason='Operational runtime backup created for private server recovery.',
            metadata={
                'requested_by': requested_by,
                'backup_id': result['backup_id'],
                'backup_path': result['backup_path'],
                'files_present': result['files_present'],
                'files_missing': result['files_missing'],
                'bytes_total': result['bytes_total'],
            },
        )
        self._dispatch_integration_event(
            'runtime.backup.created',
            payload={
                'backup_id': result['backup_id'],
                'backup_path': result['backup_path'],
                'bytes_total': result['bytes_total'],
                'files_present': result['files_present'],
                'files_missing': result['files_missing'],
            },
            source='operations',
            requested_by=requested_by,
        )
        return result

    @staticmethod
    def _role_load_error(
        role_id: str,
        path: object,
        *,
        stage: str,
        exc: Exception | None = None,
        message: str | None = None,
    ) -> dict[str, object]:
        detail = message or (str(exc) if exc is not None else f'Role {role_id} could not be loaded.')
        error_type = type(exc).__name__ if exc is not None else 'GovernanceMaterialError'
        return {
            'role_id': role_id,
            'source_path': str(path),
            'stage': stage,
            'error_type': error_type,
            'message': detail,
        }

    def _invalid_role_record(
        self,
        role_id: str,
        path: object,
        *,
        stage: str,
        exc: Exception | None = None,
        message: str | None = None,
        validation_issues: list[object] | None = None,
        headers: dict[str, object] | None = None,
    ) -> dict[str, object]:
        role_error = self._role_load_error(role_id, path, stage=stage, exc=exc, message=message)
        header_values = headers or {}
        return {
            'role_id': role_id,
            'title': role_id,
            'purpose': '',
            'stratum': None,
            'reports_to': None,
            'escalation_to': None,
            'safety_owner': None,
            'business_domain': None,
            'handled_resources': [],
            'allow': [],
            'deny': [],
            'requires': {},
            'validation_issues': [asdict(issue) for issue in (validation_issues or [])],
            'policies': [],
            'constraints': [],
            'trusted_source_origin': header_values.get('trusted_source_origin', 'unavailable'),
            'trusted_sha256': header_values.get('trusted_sha256'),
            'trusted_manifest_signature_status': header_values.get('trusted_manifest_signature_status') or 'error',
            'trusted_manifest_key_id': header_values.get('trusted_manifest_key_id'),
            'status': 'invalid',
            'source_path': str(path),
            'load_error': role_error,
        }

    @staticmethod
    def _compiled_role_record(role_id: str, path: object, document) -> dict[str, object]:
        role = document.roles.get(role_id)
        authority = document.authorities.get(role_id)
        return {
            'role_id': role_id,
            'title': role.fields.get('title') if role else role_id,
            'purpose': role.fields.get('purpose') if role else '',
            'stratum': role.fields.get('stratum') if role else None,
            'reports_to': role.fields.get('reports_to') if role else None,
            'escalation_to': role.fields.get('escalation_to') if role else None,
            'safety_owner': role.fields.get('safety_owner') if role else None,
            'business_domain': role.fields.get('business_domain') if role else None,
            'handled_resources': role.fields.get('handled_resources') if role else [],
            'allow': sorted(authority.allow) if authority else [],
            'deny': sorted(authority.deny) if authority else [],
            'requires': authority.require if authority else {},
            'validation_issues': [asdict(issue) for issue in document.validation_issues],
            'policies': sorted(document.policies.keys()),
            'constraints': sorted(document.constraints.keys()),
            'trusted_source_origin': document.headers.get('trusted_source_origin', 'unknown'),
            'trusted_sha256': document.headers.get('trusted_sha256'),
            'trusted_manifest_signature_status': document.headers.get('trusted_manifest_signature_status'),
            'trusted_manifest_key_id': document.headers.get('trusted_manifest_key_id'),
            'status': 'ready',
            'source_path': str(path),
            'load_error': None,
        }

    def list_roles(self) -> list[dict[str, object]]:
        roles: list[dict[str, object]] = []
        for path in sorted(self.registry.roles_dir.glob('*.ptn')):
            role_id = path.stem
            if role_id.lower() == 'core_terms':
                continue
            try:
                document = self.loader.load(role_id)
            except Exception as exc:
                roles.append(self._invalid_role_record(role_id, path, stage='load', exc=exc))
                continue
            role = document.roles.get(role_id)
            authority = document.authorities.get(role_id)
            if role is None or authority is None:
                roles.append(
                    self._invalid_role_record(
                        role_id,
                        path,
                        stage='semantic',
                        message=f'Role {role_id} is missing a compiled role or authority block.',
                        validation_issues=document.validation_issues,
                        headers=document.headers,
                    )
                )
                continue
            roles.append(self._compiled_role_record(role_id, path, document))
        return roles

    def audit_integrity(self) -> dict[str, object]:
        return self.engine.audit_logger.health()

    def reseal_audit_log(self, requested_by: str) -> dict[str, object]:
        result = self.engine.audit_logger.reseal_legacy_entries()
        if result['status'] == 'resealed':
            self.engine.audit_logger.record_event(
                active_role='SYSTEM',
                action='audit_reseal',
                outcome='completed',
                reason='Legacy audit entries were resealed into a fully chained log.',
                metadata={
                    'requested_by': requested_by,
                    'before_integrity': result['before_integrity'],
                    'after_integrity': result['after_integrity'],
                },
            )
        result['final_integrity'] = self.engine.audit_logger.health()
        return result

    def retention_report(self) -> dict[str, object]:
        return self.retention_manager.report()

    def retention_plan(self) -> dict[str, object]:
        return self.retention_manager.plan()

    def enforce_retention(self, dry_run: bool = True) -> dict[str, object]:
        result = self.retention_manager.enforce(dry_run=dry_run)
        if not dry_run:
            self.engine.audit_logger.reload()
        self.engine.audit_logger.record_event(active_role='SYSTEM', action='retention_dry_run' if dry_run else 'retention_enforce', outcome=result['status'], reason='Retention lifecycle processed through the enterprise runtime.', metadata={'dry_run': dry_run, 'archived_total': result['archived_total'], 'purged_total': result['purged_total'], 'blocked_total': result['blocked_total'], 'actions': result['actions']})
        return result

    def list_sessions(self, status: str | None = None) -> list[dict[str, object]]:
        return self.access_control.list_sessions(status=status)

    def revoke_session(self, session_id: str, reason: str = 'admin_revoke') -> dict[str, object]:
        return self.access_control.revoke_session(session_id, reason=reason)

    def studio_snapshot(self, limit: int = 50) -> dict[str, object]:
        return self.role_private_studio.studio_snapshot(limit=limit)

    def list_studio_requests(self, status: str | None = None, limit: int = 100) -> list[dict[str, object]]:
        return self.role_private_studio.list_requests(status=status, limit=limit)

    def get_studio_request(self, request_id: str) -> dict[str, object]:
        return self.role_private_studio.get_request(request_id)

    def create_studio_request(self, payload: dict[str, object], requested_by: str) -> dict[str, object]:
        result = self.role_private_studio.create_request(payload, requested_by=requested_by)
        self._dispatch_integration_event(
            'role_private_studio.request.created',
            payload={
                'request_id': result.get('request_id'),
                'status': result.get('status'),
                'requested_by': requested_by,
                'role_name': result.get('structured_jd', {}).get('role_name'),
                'role_id': result.get('summary', {}).get('role_id'),
                'business_domain': result.get('structured_jd', {}).get('business_domain'),
            },
            source='role_private_studio',
            requested_by=requested_by,
        )
        return result

    def update_studio_request(self, request_id: str, payload: dict[str, object], updated_by: str) -> dict[str, object]:
        return self.role_private_studio.update_request(request_id=request_id, payload=payload, updated_by=updated_by)

    def update_studio_request_ptag(self, request_id: str, ptag_source: str, updated_by: str) -> dict[str, object]:
        return self.role_private_studio.update_request_ptag(request_id=request_id, ptag_source=ptag_source, updated_by=updated_by)

    def reset_studio_request_ptag(self, request_id: str, updated_by: str) -> dict[str, object]:
        return self.role_private_studio.reset_request_ptag(request_id=request_id, updated_by=updated_by)

    def refresh_studio_request(self, request_id: str) -> dict[str, object]:
        return self.role_private_studio.refresh_request(request_id)

    def restore_studio_request_revision(self, request_id: str, revision_number: int, restored_by: str) -> dict[str, object]:
        result = self.role_private_studio.restore_request_revision(
            request_id=request_id,
            revision_number=revision_number,
            restored_by=restored_by,
        )
        self._dispatch_integration_event(
            'role_private_studio.request.restored',
            payload={
                'request_id': result.get('request_id'),
                'status': result.get('status'),
                'restored_by': restored_by,
                'revision_number': revision_number,
                'role_id': result.get('summary', {}).get('role_id'),
            },
            source='role_private_studio',
            requested_by=restored_by,
        )
        return result

    def review_studio_request(self, request_id: str, reviewer: str, decision: str, note: str) -> dict[str, object]:
        result = self.role_private_studio.review_request(request_id=request_id, reviewer=reviewer, decision=decision, note=note)
        self._dispatch_integration_event(
            'role_private_studio.request.reviewed',
            payload={
                'request_id': result.get('request_id'),
                'status': result.get('status'),
                'decision': decision,
                'reviewer': reviewer,
                'role_id': result.get('summary', {}).get('role_id'),
                'publish_readiness': result.get('publish_readiness', {}),
            },
            source='role_private_studio',
            requested_by=reviewer,
        )
        return result

    def publish_studio_request(self, request_id: str, published_by: str) -> dict[str, object]:
        result = self.role_private_studio.publish_request(request_id=request_id, published_by=published_by)
        self.engine.hierarchy_registry.reload()
        self.engine.role_transition_policy.reload()
        self._dispatch_integration_event(
            'role_private_studio.request.published',
            payload={
                'request_id': result.get('request_id'),
                'status': result.get('status'),
                'published_by': published_by,
                'role_id': result.get('publish_artifact', {}).get('role_id'),
                'publish_artifact': result.get('publish_artifact', {}),
            },
            source='role_private_studio',
            requested_by=published_by,
        )
        return result

    def human_ask_snapshot(self, limit: int = 50) -> dict[str, object]:
        return self.human_ask.human_ask_snapshot(limit=limit)

    def list_human_ask_sessions(self, status: str | None = None, limit: int = 100) -> list[dict[str, object]]:
        return self.human_ask.list_sessions(status=status, limit=limit)

    def list_human_decision_inbox(
        self,
        inbox_state: str | None = None,
        queue_lane: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, object]]:
        return self.human_ask.list_human_decision_inbox(
            inbox_state=inbox_state,
            queue_lane=queue_lane,
            limit=limit,
        )

    def get_human_ask_session(self, session_id: str) -> dict[str, object]:
        return self.human_ask.get_session(session_id)

    def list_callable_directory(self, limit: int = 200) -> dict[str, object]:
        return self.human_ask.callable_directory(limit=limit)

    def create_human_ask_session(self, payload: dict[str, object], requested_by: str) -> dict[str, object]:
        result = self.human_ask.create_session(payload, requested_by=requested_by)
        self._dispatch_integration_event(
            'human_ask.session.created',
            payload={
                'session_id': result.get('session_id'),
                'status': result.get('status'),
                'mode': result.get('mode'),
                'requested_by': requested_by,
                'participant': result.get('participant', {}),
                'decision_summary': result.get('decision_summary', {}),
            },
            source='human_ask',
            requested_by=requested_by,
        )
        if (result.get('decision_summary', {}) or {}).get('escalated'):
            self._dispatch_integration_event(
                'human_ask.session.escalated',
                payload={
                    'session_id': result.get('session_id'),
                    'status': result.get('status'),
                    'requested_by': requested_by,
                    'participant': result.get('participant', {}),
                    'decision_summary': result.get('decision_summary', {}),
                },
                source='human_ask',
                requested_by=requested_by,
            )
        return result

    def create_human_ask_studio_record(self, studio_request_id: str, payload: dict[str, object], requested_by: str) -> dict[str, object]:
        result = self.human_ask.create_studio_record_request(studio_request_id, payload, requested_by=requested_by)
        self._dispatch_integration_event(
            'human_ask.session.created',
            payload={
                'session_id': result.get('session_id'),
                'status': result.get('status'),
                'mode': result.get('mode'),
                'requested_by': requested_by,
                'participant': result.get('participant', {}),
                'decision_summary': result.get('decision_summary', {}),
            },
            source='human_ask',
            requested_by=requested_by,
            metadata={'studio_request_id': studio_request_id},
        )
        self._dispatch_integration_event(
            'human_ask.session.recorded_from_studio',
            payload={
                'session_id': result.get('session_id'),
                'studio_request_id': studio_request_id,
                'status': result.get('status'),
                'participant': result.get('participant', {}),
                'decision_summary': result.get('decision_summary', {}),
            },
            source='human_ask',
            requested_by=requested_by,
            metadata={'studio_request_id': studio_request_id},
        )
        return result

    def compliance_snapshot(self) -> dict[str, object]:
        roles = self.list_roles()
        base = self._base_health(roles=roles)
        return self.compliance_registry.build_snapshot(
            runtime_health=base,
            access_control_health=self.access_control.health(),
            roles=roles,
            evidence_summary=self.evidence_builder.summary(),
        )

    def list_evidence_packs(self, limit: int = 20) -> list[dict[str, object]]:
        return self.evidence_builder.list_packs(limit=limit)

    def list_workflow_proof_bundles(self, limit: int = 20) -> list[dict[str, object]]:
        return self.evidence_builder.list_workflow_proof_bundles(limit=limit)

    def evidence_pack_summary(self) -> dict[str, object]:
        return self.evidence_builder.summary()

    def create_workflow_proof_bundle(self, workflow_id: str, requested_by: str, *, limit: int = 400) -> dict[str, object]:
        workflow_state = self.get_workflow_state(workflow_id)
        request_id = str(workflow_state.get('request_id', ''))

        recovery_records = [
            item
            for item in self.list_runtime_recovery_records(limit=limit)
            if self._workflow_matches_runtime_record(workflow_id, request_id, item)
        ]
        related_request_ids = {request_id}
        for item in recovery_records:
            related_request_ids.add(str(item.get('request_id', '')))
            resumed_request_id = item.get('resumed_request_id')
            if resumed_request_id is not None:
                related_request_ids.add(str(resumed_request_id))
        dead_letters = [
            item
            for item in self.list_runtime_dead_letters(limit=limit)
            if str(item.get('request_id', '')) in related_request_ids
        ]
        human_sessions = [
            session.to_dict()
            for session in self.human_ask.store.list_sessions()
            if self._workflow_matches_human_session(workflow_id, request_id, session.to_dict())
        ]
        audit_entries = [
            entry
            for entry in self.list_audit(limit=limit)
            if self._workflow_matches_audit_entry(workflow_id, request_id, entry)
        ]

        result = self.evidence_builder.create_workflow_proof_bundle(
            requested_by=requested_by,
            workflow_id=workflow_id,
            workflow_state=workflow_state,
            operational_readiness=self.operational_readiness(limit=50),
            recovery_records=recovery_records,
            dead_letters=dead_letters,
            human_sessions=human_sessions,
            audit_entries=audit_entries,
        )
        self.engine.audit_logger.record_event(
            active_role='SYSTEM',
            action='workflow_proof_export',
            outcome='completed',
            reason='Workflow proof bundle exported from the enterprise runtime.',
            metadata={
                'requested_by': requested_by,
                'workflow_id': workflow_id,
                'bundle_id': result['bundle_id'],
                'export_path': result['export_path'],
                'artifact_total': result['artifact_total'],
            },
        )
        return result

    def create_evidence_pack(self, requested_by: str) -> dict[str, object]:
        roles = self.list_roles()
        base = self._base_health(roles=roles)
        access_health = self.access_control.health()
        compliance_snapshot = self.compliance_registry.build_snapshot(
            runtime_health=base,
            access_control_health=access_health,
            roles=roles,
            evidence_summary=self.evidence_builder.summary(),
        )
        result = self.evidence_builder.create_pack(
            requested_by=requested_by,
            runtime_health=base,
            access_control_health=access_health,
            compliance_snapshot=compliance_snapshot,
            roles=roles,
            audit_entries=self.list_audit(limit=400),
            retention_report=self.retention_report(),
            go_live_readiness=build_go_live_readiness(self.retention_manager.config, app=self),
            operations={
                'summary': self.runtime_backup_summary(),
                'backups': self.list_runtime_backups(limit=10),
            },
            studio_summary=self.studio_snapshot(limit=20).get('summary', {}),
        )
        self.engine.audit_logger.record_event(
            active_role='SYSTEM',
            action='evidence_export',
            outcome='completed',
            reason='Auditor evidence pack exported from the enterprise runtime.',
            metadata={
                'requested_by': requested_by,
                'pack_id': result['pack_id'],
                'export_path': result['export_path'],
                'artifact_total': result['artifact_total'],
                'file_total': result['file_total'],
            },
        )
        self._dispatch_integration_event(
            'governance.evidence.exported',
            payload={
                'pack_id': result['pack_id'],
                'export_path': result['export_path'],
                'artifact_total': result['artifact_total'],
                'file_total': result['file_total'],
            },
            source='governance',
            requested_by=requested_by,
        )
        return result

    def integration_snapshot(self, limit: int = 50) -> dict[str, object]:
        return {
            'summary': {
                **self.integration_registry.health(),
                **self.integration_dispatcher.summary(),
            },
            'targets': self.integration_registry.snapshot().get('targets', []),
            'outbox': self.integration_dispatcher.list_outbox_jobs(limit=limit),
            'deliveries': self.integration_dispatcher.list_deliveries(limit=limit),
            'dead_letters': self.integration_dispatcher.list_dead_letters(limit=limit),
            'coordination': self.integration_dispatcher.health().get('coordination', {}),
        }

    def model_provider_snapshot(self) -> dict[str, object]:
        return self.model_provider_registry.health()

    def probe_model_providers(self, requested_by: str, provider_id: str | None = None) -> dict[str, object]:
        result = self.model_provider_registry.probe(provider_id=provider_id)
        outcome = 'completed' if result.get('failed_providers', 0) == 0 else 'partial'
        self.engine.audit_logger.record_event(
            active_role='INTEGRATION',
            action='model_provider_probe',
            outcome=outcome,
            reason='Configured model providers were probed for runtime readiness.',
            metadata={
                'requested_by': requested_by,
                'provider_id': provider_id,
                'probe_result': result,
            },
        )
        return result

    def trigger_integration_test_event(self, requested_by: str, event_type: str = 'integration.test.manual') -> dict[str, object]:
        return self._dispatch_integration_event(
            event_type,
            payload={
                'message': 'Manual integration test event generated from the private dashboard.',
                'requested_by': requested_by,
                'runtime_status': self.health().get('status', 'unknown'),
            },
            source='integration_console',
            requested_by=requested_by,
        )

    def _workflow_matches_runtime_record(self, workflow_id: str, request_id: str, record: dict[str, object]) -> bool:
        if str(record.get('request_id', '')) == request_id:
            return True
        metadata = record.get('metadata', {})
        if isinstance(metadata, dict):
            execution_plan = metadata.get('execution_plan', {})
            if isinstance(execution_plan, dict) and str(execution_plan.get('plan_id', '')) == workflow_id:
                return True
        return False

    def _workflow_matches_human_session(self, workflow_id: str, request_id: str, session: dict[str, object]) -> bool:
        metadata = session.get('metadata', {})
        if not isinstance(metadata, dict):
            return False
        if str(metadata.get('origin_request_id', '')) == request_id:
            return True
        execution_plan = metadata.get('execution_plan', {})
        if isinstance(execution_plan, dict) and str(execution_plan.get('plan_id', '')) == workflow_id:
            return True
        inbox = metadata.get('human_decision_inbox', {})
        if isinstance(inbox, dict):
            plan = inbox.get('execution_plan', {})
            if isinstance(plan, dict) and str(plan.get('plan_id', '')) == workflow_id:
                return True
        return False

    def _workflow_matches_audit_entry(self, workflow_id: str, request_id: str, entry: dict[str, object]) -> bool:
        payload = str(entry)
        return workflow_id in payload or request_id in payload

    def _dispatch_integration_event(
        self,
        event_type: str,
        payload: dict[str, object],
        *,
        source: str,
        requested_by: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> dict[str, object]:
        result = self.integration_dispatcher.dispatch_event(
            event_type,
            payload,
            source=source,
            requested_by=requested_by,
            metadata=metadata,
        )
        outcome = 'completed' if result['failed_total'] == 0 else 'partial'
        self.engine.audit_logger.record_event(
            active_role='INTEGRATION',
            action='integration_dispatch',
            outcome=outcome,
            reason=f"Outbound integration event {event_type} dispatched to {result['targets_matched']} target(s).",
            metadata={
                'event_type': event_type,
                'source': source,
                'requested_by': requested_by,
                'dispatch_result': result,
            },
        )
        return result



def build_engine_app(config: AppConfig) -> EngineApplication:
    registry = RoleRegistry(config.roles_dir, manifest_path=config.trusted_registry_manifest_path, cache_path=config.trusted_registry_cache_path, signing_key=config.trusted_registry_signing_key, signature_required=config.trusted_registry_signature_required)
    loader = RoleLoader(registry)
    engine = CoreEngine(loader, config=config, audit_log_path=config.audit_log_path, override_store_path=config.override_store_path, lock_store_path=config.lock_store_path, consistency_store_path=config.consistency_store_path, workflow_state_store_path=config.workflow_state_store_path, runtime_recovery_store_path=config.runtime_recovery_store_path, runtime_dead_letter_path=config.runtime_dead_letter_path)
    retention_manager = RetentionManager(config)
    access_control = AccessControl(config)
    role_private_studio = RolePrivateStudioService(config=config, registry=registry, audit_logger=engine.audit_logger)
    human_ask = HumanAskService(config=config, engine=engine, registry=registry, role_private_studio=role_private_studio, audit_logger=engine.audit_logger)
    backup_manager = RuntimeBackupManager(config)
    compliance_registry = ComplianceFrameworkRegistry(config.compliance_frameworks_path)
    evidence_builder = AuditorEvidencePackBuilder(config)
    integration_registry = IntegrationRegistry(config.integration_targets_path)
    model_provider_registry = ModelProviderRegistry(config)
    integration_dispatcher = WebhookDispatcher(config, integration_registry)
    return EngineApplication(engine, loader=loader, registry=registry, retention_manager=retention_manager, access_control=access_control, role_private_studio=role_private_studio, human_ask=human_ask, backup_manager=backup_manager, compliance_registry=compliance_registry, evidence_builder=evidence_builder, integration_registry=integration_registry, model_provider_registry=model_provider_registry, integration_dispatcher=integration_dispatcher)

