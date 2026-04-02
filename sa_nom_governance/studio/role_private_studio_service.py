import json
from copy import deepcopy
from uuid import uuid4

from sa_nom_governance.audit.audit_logger import AuditLogger
from sa_nom_governance.compliance.trusted_registry import write_trusted_registry_files
from sa_nom_governance.ptag.pt_oss_engine import PTOSSEngine
from sa_nom_governance.studio.role_private_studio_diff import build_revision_delta
from sa_nom_governance.studio.role_private_studio_generator import RolePrivateStudioGenerator
from sa_nom_governance.studio.role_private_studio_models import (
    PublishArtifact,
    ReviewDecision,
    RoleDraftRevision,
    RolePrivateStudioRequest,
    StructuredJD,
    utc_now,
)
from sa_nom_governance.studio.role_private_studio_simulator import RolePrivateStudioSimulator
from sa_nom_governance.studio.role_private_studio_store import RolePrivateStudioStore
from sa_nom_governance.studio.role_private_studio_validator import RolePrivateStudioValidator
from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.utils.owner_identity import is_default_owner_alias
from sa_nom_governance.utils.registry import RoleRegistry

DEFAULT_TEMPLATE = {
    'template_name': 'SA-NOM Role Private Studio JD Template',
    'description': 'Structured authoring template for governed role creation.',
    'language_identity': 'PTAG Governance Language',
    'stages': ['create', 'normalize', 'generate', 'validate', 'simulate', 'review', 'publish'],
    'fields': [
        {'id': 'role_name', 'label': 'Role name', 'type': 'text', 'required': True},
        {'id': 'purpose', 'label': 'Purpose', 'type': 'textarea', 'required': True},
        {'id': 'reporting_line', 'label': 'Reporting line', 'type': 'text', 'required': True},
        {'id': 'business_domain', 'label': 'Business domain', 'type': 'text', 'required': True},
        {'id': 'operating_mode', 'label': 'Operating mode', 'type': 'enum', 'options': ['direct', 'indirect'], 'required': True},
        {'id': 'assigned_user_id', 'label': 'Assigned user id', 'type': 'text', 'required': False},
        {'id': 'executive_owner_id', 'label': 'Executive owner id', 'type': 'text', 'required': False},
        {'id': 'seat_id', 'label': 'Seat id', 'type': 'text', 'required': False},
        {'id': 'responsibilities', 'label': 'Responsibilities', 'type': 'list', 'required': True},
        {'id': 'allowed_actions', 'label': 'Allowed actions', 'type': 'list', 'required': True},
        {'id': 'forbidden_actions', 'label': 'Forbidden actions', 'type': 'list', 'required': False},
        {'id': 'wait_human_actions', 'label': 'Wait-human actions', 'type': 'list', 'required': False},
        {'id': 'handled_resources', 'label': 'Handled resources', 'type': 'list', 'required': False},
        {'id': 'financial_sensitivity', 'label': 'Financial sensitivity', 'type': 'enum', 'options': ['low', 'medium', 'high', 'critical']},
        {'id': 'legal_sensitivity', 'label': 'Legal sensitivity', 'type': 'enum', 'options': ['low', 'medium', 'high', 'critical']},
        {'id': 'compliance_sensitivity', 'label': 'Compliance sensitivity', 'type': 'enum', 'options': ['low', 'medium', 'high', 'critical']},
        {'id': 'sample_scenarios', 'label': 'Sample scenarios', 'type': 'list', 'required': False},
        {'id': 'operator_notes', 'label': 'Operator notes', 'type': 'textarea', 'required': False},
    ],
    'library': [
        {
            'template_id': 'governance_guardian',
            'category': 'governance',
            'label': 'Governance Guardian',
            'summary': 'Governed review role for policies, escalations, and approval routing.',
            'payload': {
                'role_name': 'Governance Guardian',
                'purpose': 'Review sensitive policy and escalation requests before they enter privileged execution.',
                'reporting_line': 'EXEC_OWNER',
                'business_domain': 'governance',
                'operating_mode': 'direct',
                'executive_owner_id': 'EXEC_OWNER',
                'seat_id': 'EXEC-GOV',
                'responsibilities': ['review high-risk policy requests', 'route escalations', 'confirm override boundaries'],
                'allowed_actions': ['review_policy', 'approve_policy', 'escalate_policy'],
                'forbidden_actions': ['delete_runtime_data'],
                'wait_human_actions': ['approve_policy'],
                'handled_resources': ['policy', 'runtime'],
                'financial_sensitivity': 'medium',
                'legal_sensitivity': 'medium',
                'compliance_sensitivity': 'high',
                'sample_scenarios': ['policy review', 'escalation routing'],
                'operator_notes': 'Keeps governance boundaries explicit and review-first.',
            },
        },
        {
            'template_id': 'legal_operator',
            'category': 'legal',
            'label': 'Legal Operator',
            'summary': 'Contract and compliance review role with strict approval boundaries.',
            'payload': {
                'role_name': 'Legal Operator',
                'purpose': 'Review contract and compliance work without granting signing authority.',
                'reporting_line': 'LEGAL',
                'business_domain': 'legal_operations',
                'operating_mode': 'indirect',
                'assigned_user_id': 'LEGAL_MANAGER_01',
                'executive_owner_id': 'EXEC_OWNER',
                'seat_id': 'OPS-LEGAL',
                'responsibilities': ['review contracts', 'flag compliance risk', 'summarize legal concerns'],
                'allowed_actions': ['review_contract', 'flag_risk', 'advise_compliance'],
                'forbidden_actions': ['sign_contract'],
                'wait_human_actions': ['approve_contract_exception'],
                'handled_resources': ['contract'],
                'financial_sensitivity': 'medium',
                'legal_sensitivity': 'high',
                'compliance_sensitivity': 'high',
                'sample_scenarios': ['contract review', 'high-value escalation'],
                'operator_notes': 'Must never sign or finalize contracts.',
            },
        },
        {
            'template_id': 'finance_steward',
            'category': 'finance',
            'label': 'Finance Steward',
            'summary': 'Budget and spend governance role with strong human-review discipline.',
            'payload': {
                'role_name': 'Finance Steward',
                'purpose': 'Review budgets and spending requests while escalating sensitive approvals.',
                'reporting_line': 'GOV',
                'business_domain': 'finance_operations',
                'operating_mode': 'indirect',
                'assigned_user_id': 'FINANCE_MANAGER_01',
                'executive_owner_id': 'EXEC_OWNER',
                'seat_id': 'OPS-FINANCE',
                'responsibilities': ['review spend requests', 'prepare budget summaries', 'flag anomalies'],
                'allowed_actions': ['review_budget', 'prepare_finance_report', 'flag_finance_risk'],
                'forbidden_actions': ['release_funds'],
                'wait_human_actions': ['approve_budget'],
                'handled_resources': ['budget', 'invoice'],
                'financial_sensitivity': 'high',
                'legal_sensitivity': 'medium',
                'compliance_sensitivity': 'high',
                'sample_scenarios': ['monthly budget review', 'high-risk budget escalation'],
                'operator_notes': 'Approvals must stay governed by human finance authority.',
            },
        },
        {
            'template_id': 'ops_coordinator',
            'category': 'operations',
            'label': 'Operations Coordinator',
            'summary': 'Operational routing role for workflow health, tickets, and controlled execution.',
            'payload': {
                'role_name': 'Operations Coordinator',
                'purpose': 'Coordinate daily operations and route risky actions for human attention.',
                'reporting_line': 'GOV',
                'business_domain': 'operations',
                'operating_mode': 'indirect',
                'assigned_user_id': 'OPS_COORDINATOR_01',
                'executive_owner_id': 'EXEC_OWNER',
                'seat_id': 'OPS-COORD',
                'responsibilities': ['route operational work', 'track service health', 'coordinate tickets'],
                'allowed_actions': ['review_runbook', 'coordinate_operation', 'escalate_incident'],
                'forbidden_actions': ['terminate_service'],
                'wait_human_actions': ['emergency_stop'],
                'handled_resources': ['service', 'runbook', 'ticket'],
                'financial_sensitivity': 'low',
                'legal_sensitivity': 'medium',
                'compliance_sensitivity': 'medium',
                'sample_scenarios': ['incident routing', 'runbook review'],
                'operator_notes': 'May coordinate but should not directly terminate production services.',
            },
        },
        {
            'template_id': 'safety_officer',
            'category': 'safety',
            'label': 'Safety Officer',
            'summary': 'Safety-focused role with immediate escalation discipline for high-risk actions.',
            'payload': {
                'role_name': 'Safety Officer',
                'purpose': 'Monitor safety-sensitive domains and force escalation on risky operations.',
                'reporting_line': 'GOV',
                'business_domain': 'product_safety',
                'operating_mode': 'direct',
                'executive_owner_id': 'EXEC_OWNER',
                'seat_id': 'EXEC-SAFETY',
                'responsibilities': ['inspect safety posture', 'escalate risk', 'document safety findings'],
                'allowed_actions': ['review_safety', 'escalate_safety_case', 'advise_compliance'],
                'forbidden_actions': ['suppress_safety_alert'],
                'wait_human_actions': ['approve_safety_exception', 'emergency_stop'],
                'handled_resources': ['safety_case', 'incident'],
                'financial_sensitivity': 'low',
                'legal_sensitivity': 'high',
                'compliance_sensitivity': 'critical',
                'sample_scenarios': ['safety review', 'critical escalation'],
                'operator_notes': 'Safety exceptions should always remain review-heavy.',
            },
        },
    ],
}
DEFAULT_EXAMPLES = [
    {
        'name': 'Contract Review Analyst',
        'role_name': 'Contract Review Analyst',
        'purpose': 'Review contract packets and route risky documents for human attention.',
        'reporting_line': 'LEGAL',
        'business_domain': 'legal_operations',
        'operating_mode': 'indirect',
        'assigned_user_id': 'LEGAL_MANAGER_01',
        'executive_owner_id': 'EXEC_OWNER',
        'seat_id': 'OPS-LEGAL',
        'responsibilities': ['review incoming contracts', 'flag risk', 'summarize compliance points'],
        'allowed_actions': ['review_contract', 'flag_risk', 'advise_compliance'],
        'forbidden_actions': ['sign_contract'],
        'wait_human_actions': [],
        'handled_resources': ['contract'],
        'financial_sensitivity': 'medium',
        'legal_sensitivity': 'high',
        'compliance_sensitivity': 'high',
        'sample_scenarios': ['normal review', 'high-value contract escalation'],
        'operator_notes': 'Should never sign or approve contracts directly.',
    }
]


class RolePrivateStudioService:
    def __init__(self, config: AppConfig, registry: RoleRegistry, audit_logger: AuditLogger | None = None) -> None:
        self.config = config
        self.registry = registry
        self.audit_logger = audit_logger
        self.store = RolePrivateStudioStore(config, config.role_private_studio_store_path)
        self.generator = RolePrivateStudioGenerator(
            owner_name=config.owner_name(),
            default_executive_owner_id=config.executive_owner_id(),
        )
        self.validator = RolePrivateStudioValidator()
        self.simulator = RolePrivateStudioSimulator(config.trusted_registry_signing_key or 'role-private-studio-sim-key')
        bundled_dir = config.bundled_resources_root
        bundled_foundation_path = bundled_dir / 'pt_oss' / 'pt_oss_foundation.json'
        bundled_template_path = bundled_dir / 'studio' / 'role_private_studio_templates.json'
        bundled_examples_path = bundled_dir / 'studio' / 'role_private_studio_examples.json'
        foundation_path = config.pt_oss_foundation_path or (config.base_dir / 'resources' / 'pt_oss' / 'pt_oss_foundation.json')
        legacy_foundation_path = config.base_dir / 'pt_oss_foundation.json'
        if foundation_path.exists():
            effective_foundation_path = foundation_path
        elif legacy_foundation_path.exists():
            effective_foundation_path = legacy_foundation_path
        else:
            effective_foundation_path = bundled_foundation_path
        self.pt_oss_engine = PTOSSEngine(effective_foundation_path)
        self.template_path = config.role_private_studio_template_path or (config.base_dir / 'resources' / 'studio' / 'role_private_studio_templates.json')
        self.examples_path = config.role_private_studio_examples_path or (config.base_dir / 'resources' / 'studio' / 'role_private_studio_examples.json')
        if not self.template_path.exists():
            legacy_template_path = config.base_dir / 'role_private_studio_templates.json'
            self.template_path = legacy_template_path if legacy_template_path.exists() else bundled_template_path
        if not self.examples_path.exists():
            legacy_examples_path = config.base_dir / 'role_private_studio_examples.json'
            self.examples_path = legacy_examples_path if legacy_examples_path.exists() else bundled_examples_path

    def studio_snapshot(self, limit: int = 50) -> dict[str, object]:
        requests = [item.to_dict(compact=True) for item in self.store.list_requests()[:limit]]
        statuses = [item['status'] for item in requests]
        structural_guarded_total = sum(
            1 for item in requests if (item.get('publish_readiness') or {}).get('status') == 'guarded'
        )
        structural_blocked_total = sum(
            1 for item in requests if (item.get('publish_readiness') or {}).get('structural_state') == 'blocked'
        )
        publication_blocked_total = sum(
            1 for item in requests if (item.get('publish_readiness') or {}).get('status') == 'blocked'
        )
        ready_to_publish_total = sum(
            1 for item in requests if (item.get('publish_readiness') or {}).get('status') == 'ready'
        )
        return {
            'summary': {
                'requests_total': len(requests),
                'published_total': sum(1 for item in requests if item.get('publish_artifact')),
                'blocked_total': sum(1 for item in requests if (item.get('validation_report') or {}).get('blocked_publish')),
                'publication_blocked_total': publication_blocked_total,
                'ready_to_publish_total': ready_to_publish_total,
                'structural_guarded_total': structural_guarded_total,
                'structural_blocked_total': structural_blocked_total,
                'review_lane_total': sum(
                    1
                    for item in requests
                    if item.get('status') != 'published'
                    and (item.get('publish_readiness') or {}).get('status') not in {'ready', 'guarded'}
                ),
                'approved_total': sum(1 for item in requests if item.get('status') == 'approved'),
                'changes_requested_total': sum(1 for item in requests if item.get('status') == 'changes_requested'),
                'revisions_total': sum(len(item.get('revisions', [])) for item in requests),
                'template_library_total': len(self.load_template().get('library', [])),
                'statuses': {status: statuses.count(status) for status in sorted(set(statuses))},
            },
            'requests': requests,
            'template': self.load_template(),
            'examples': self.load_examples(),
        }

    def load_template(self) -> dict[str, object]:
        if self.template_path.exists():
            loaded = json.loads(self.template_path.read_text(encoding='utf-8-sig'))
            if 'library' not in loaded:
                loaded['library'] = DEFAULT_TEMPLATE['library']
            return self._apply_owner_defaults_to_template(loaded)
        return self._apply_owner_defaults_to_template(DEFAULT_TEMPLATE)

    def load_examples(self) -> list[dict[str, object]]:
        if self.examples_path.exists():
            return self._apply_owner_defaults_to_examples(json.loads(self.examples_path.read_text(encoding='utf-8-sig')))
        return self._apply_owner_defaults_to_examples(DEFAULT_EXAMPLES)

    def list_requests(self, status: str | None = None, limit: int = 100) -> list[dict[str, object]]:
        return [item.to_dict(compact=True) for item in self.store.list_requests(status=status)[:limit]]

    def get_request(self, request_id: str) -> dict[str, object]:
        return self.store.get_request(request_id).to_dict()

    def create_request(self, payload: dict[str, object], requested_by: str) -> dict[str, object]:
        payload = self._apply_owner_defaults_to_payload(payload)
        request = RolePrivateStudioRequest(
            request_id=f'rps_{uuid4().hex[:12]}',
            requested_by=requested_by,
            created_at=utc_now(),
            updated_at=utc_now(),
            status='draft',
            structured_jd=StructuredJD.from_dict(payload),
            ptag_override_source=str(payload.get('ptag_override_source', '') or ''),
        )
        self.store.save_request(request)
        self._audit('role_private_studio_request_created', 'created', 'Role Private Studio request created.', {'request_id': request.request_id, 'requested_by': requested_by})
        return self._refresh_request_object(request, trigger='create', actor=requested_by)

    def _apply_owner_defaults_to_payload(self, payload: dict[str, object]) -> dict[str, object]:
        executive_owner_id = self.config.executive_owner_id()
        normalized = dict(payload)
        current_owner = str(normalized.get('executive_owner_id', '') or '').strip().upper()
        if is_default_owner_alias(current_owner):
            normalized['executive_owner_id'] = executive_owner_id
        reporting_line = str(normalized.get('reporting_line', '') or '').strip().upper()
        if reporting_line and is_default_owner_alias(reporting_line, include_empty=False):
            normalized['reporting_line'] = executive_owner_id
        return normalized

    def _apply_owner_defaults_to_template(self, template: dict[str, object]) -> dict[str, object]:
        normalized = deepcopy(template)
        library = normalized.get('library', [])
        if isinstance(library, list):
            for item in library:
                if not isinstance(item, dict):
                    continue
                payload = item.get('payload')
                if isinstance(payload, dict):
                    item['payload'] = self._apply_owner_defaults_to_payload(payload)
        return normalized

    def _apply_owner_defaults_to_examples(self, examples: list[dict[str, object]]) -> list[dict[str, object]]:
        normalized: list[dict[str, object]] = []
        for item in examples:
            if isinstance(item, dict):
                normalized.append(self._apply_owner_defaults_to_payload(item))
        return normalized

    def update_request(self, request_id: str, payload: dict[str, object], updated_by: str) -> dict[str, object]:
        request = self.store.get_request(request_id)
        if request.status == 'published':
            raise ValueError('Published Role Private Studio requests may not be updated.')
        merged_payload = request.structured_jd.to_dict()
        for key, value in payload.items():
            if key in merged_payload:
                merged_payload[key] = value
        request.structured_jd = StructuredJD.from_dict(merged_payload)
        if 'ptag_override_source' in payload:
            request.ptag_override_source = str(payload.get('ptag_override_source', '') or '')
        request.updated_at = utc_now()
        self.store.save_request(request)
        self._audit('role_private_studio_request_updated', 'updated', 'Role Private Studio request updated before regeneration.', {'request_id': request.request_id, 'updated_by': updated_by, 'updated_fields': sorted(key for key in payload.keys() if key in merged_payload)})
        return self._refresh_request_object(request, trigger='update', actor=updated_by)

    def refresh_request(self, request_id: str) -> dict[str, object]:
        request = self.store.get_request(request_id)
        return self._refresh_request_object(request, trigger='refresh', actor='system')

    def restore_request_revision(self, request_id: str, revision_number: int, restored_by: str) -> dict[str, object]:
        request = self.store.get_request(request_id)
        if request.status == 'published':
            raise ValueError('Published Role Private Studio requests may not be restored.')
        revision = next((item for item in request.revisions if item.revision_number == revision_number), None)
        if revision is None:
            raise ValueError(f'Role Private Studio revision {revision_number} was not found.')
        request.structured_jd = StructuredJD.from_dict(revision.structured_jd_snapshot.to_dict())
        request.ptag_override_source = revision.generated_ptag if revision.ptag_source_mode == 'manual' else ''
        request.updated_at = utc_now()
        self.store.save_request(request)
        self._audit(
            'role_private_studio_revision_restored',
            'restored',
            'Role Private Studio request restored to a governed prior revision.',
            {
                'request_id': request_id,
                'restored_by': restored_by,
                'restored_revision_number': revision_number,
            },
        )
        return self._refresh_request_object(request, trigger=f'restore_r{revision_number}', actor=restored_by)

    def update_request_ptag(self, request_id: str, ptag_source: str, updated_by: str) -> dict[str, object]:
        request = self.store.get_request(request_id)
        if request.status == 'published':
            raise ValueError('Published Role Private Studio requests may not be edited.')
        request.ptag_override_source = str(ptag_source or '')
        request.updated_at = utc_now()
        self.store.save_request(request)
        self._audit(
            'role_private_studio_ptag_updated',
            'updated',
            'Role Private Studio PTAG draft was edited through the live editor.',
            {
                'request_id': request.request_id,
                'updated_by': updated_by,
                'override_active': bool(request.ptag_override_source),
                'ptag_length': len(request.ptag_override_source),
            },
        )
        return self._refresh_request_object(request, trigger='ptag_edit', actor=updated_by)

    def reset_request_ptag(self, request_id: str, updated_by: str) -> dict[str, object]:
        request = self.store.get_request(request_id)
        if request.status == 'published':
            raise ValueError('Published Role Private Studio requests may not be edited.')
        request.ptag_override_source = ''
        request.updated_at = utc_now()
        self.store.save_request(request)
        self._audit(
            'role_private_studio_ptag_reset',
            'updated',
            'Role Private Studio PTAG override was cleared and reverted to generated mode.',
            {'request_id': request.request_id, 'updated_by': updated_by},
        )
        return self._refresh_request_object(request, trigger='ptag_reset', actor=updated_by)

    def review_request(self, request_id: str, reviewer: str, decision: str, note: str) -> dict[str, object]:
        request = self.store.get_request(request_id)
        current_revision_number = request.revisions[-1].revision_number if request.revisions else 0
        review = ReviewDecision(
            review_id=f'review_{uuid4().hex[:12]}',
            decision=decision,
            reviewer=reviewer,
            note=note,
            created_at=utc_now(),
            revision_number=current_revision_number,
        )
        request.review_history.append(review)
        if decision == 'approve':
            if request.validation_report is None or request.validation_report.blocked_publish:
                raise ValueError('Cannot approve a draft with validation blockers.')
            if request.simulation_report is None or request.simulation_report.status != 'passed':
                raise ValueError('Cannot approve a draft that has not passed simulation.')
            request.status = 'approved'
        elif decision == 'request_changes':
            request.status = 'changes_requested'
        else:
            raise ValueError(f'Unsupported Role Private Studio review decision: {decision}')
        request.updated_at = utc_now()
        self.store.save_request(request)
        self._audit('role_private_studio_reviewed', request.status, f'Role Private Studio request reviewed with decision {decision}.', {'request_id': request_id, 'reviewer': reviewer, 'decision': decision, 'note': note, 'revision_number': current_revision_number})
        return request.to_dict()

    def publish_request(self, request_id: str, published_by: str) -> dict[str, object]:
        request = self.store.get_request(request_id)
        if request.publish_artifact is not None:
            return request.to_dict()
        readiness = request.to_dict(compact=True).get('publish_readiness', {})
        if readiness.get('status') != 'ready':
            blockers = '; '.join(readiness.get('blockers', []))
            raise ValueError(f'Role Private Studio draft is not ready to publish: {blockers}')
        if request.normalized_spec is None:
            raise ValueError('Normalized role specification is missing.')

        role_path = self.config.roles_dir / f'{request.normalized_spec.role_id}.ptn'
        if role_path.exists() and role_path.read_text(encoding='utf-8') != request.generated_ptag:
            raise ValueError(f'Role file already exists for {request.normalized_spec.role_id}; publish is blocked to avoid overwriting an active role pack.')

        role_path.write_text(request.generated_ptag, encoding='utf-8')
        role_ids = sorted(path.stem for path in self.config.roles_dir.glob('*.ptn') if path.stem.lower() != 'core_terms')
        manifest, _cache = write_trusted_registry_files(
            roles_dir=self.config.roles_dir,
            manifest_path=self.config.trusted_registry_manifest_path,
            cache_path=self.config.trusted_registry_cache_path,
            role_ids=role_ids,
            signing_key=self.config.trusted_registry_signing_key or '',
            key_id=self.config.trusted_registry_key_id,
            signed_by=self.config.trusted_registry_signed_by,
        )
        self.registry.reload()
        manifest_entry = manifest['roles'][request.normalized_spec.role_id]
        current_revision_number = request.revisions[-1].revision_number if request.revisions else 0
        request.publish_artifact = PublishArtifact(
            publish_id=f'publish_{uuid4().hex[:12]}',
            role_id=request.normalized_spec.role_id,
            published_by=published_by,
            published_at=utc_now(),
            role_path=str(role_path),
            trusted_sha256=str(manifest_entry['sha256']),
            manifest_key_id=str(manifest['signature']['key_id']),
            manifest_signature_status='verified',
            revision_number=current_revision_number,
        )
        request.status = 'published'
        request.updated_at = utc_now()
        self.store.save_request(request)
        self._audit('role_private_studio_published', 'published', 'Role Private Studio draft published into the trusted registry.', {'request_id': request_id, 'role_id': request.normalized_spec.role_id, 'published_by': published_by, 'role_path': str(role_path), 'trusted_sha256': manifest_entry['sha256'], 'revision_number': current_revision_number})
        return request.to_dict()

    def _refresh_request_object(self, request: RolePrivateStudioRequest, trigger: str, actor: str) -> dict[str, object]:
        if request.status == 'published':
            return request.to_dict()

        previous_revision = request.revisions[-1] if request.revisions else None
        request.normalized_spec = self.generator.normalize(request.structured_jd)
        generated_ptag = self.generator.generate(request.normalized_spec)
        request.system_generated_ptag = generated_ptag
        if request.ptag_override_source.strip():
            request.generated_ptag = request.ptag_override_source
            request.ptag_source_mode = 'manual'
        else:
            request.generated_ptag = generated_ptag
            request.ptag_source_mode = 'generated'
        request.validation_report = self.validator.validate(request)
        request.simulation_report = self.simulator.simulate(request)
        request.pt_oss_assessment = self.pt_oss_engine.assess_role_draft(
            structured_jd=request.structured_jd,
            normalized_spec=request.normalized_spec,
            validation_report=request.validation_report,
            simulation_report=request.simulation_report,
            current_ptag=request.generated_ptag,
            generated_ptag=request.system_generated_ptag,
        )

        if request.validation_report.blocked_publish:
            request.status = 'validation_failed'
        elif request.simulation_report.status != 'passed':
            request.status = 'simulation_failed'
        else:
            request.status = 'in_review'

        diff_summary, change_summary = build_revision_delta(
            previous_revision=previous_revision,
            current_structured_jd=request.structured_jd,
            current_normalized_spec=request.normalized_spec,
            current_ptag=request.generated_ptag,
            validation_report=request.validation_report,
            simulation_report=request.simulation_report,
        )
        revision = RoleDraftRevision(
            revision_id=f'rev_{uuid4().hex[:12]}',
            revision_number=len(request.revisions) + 1,
            trigger=trigger,
            generated_at=utc_now(),
            structured_jd_snapshot=StructuredJD.from_dict(request.structured_jd.to_dict()),
            normalized_spec=request.normalized_spec,
            generated_ptag=request.generated_ptag,
            system_generated_ptag=request.system_generated_ptag,
            ptag_source_mode=request.ptag_source_mode,
            validation_report=request.validation_report,
            simulation_report=request.simulation_report,
            pt_oss_assessment=request.pt_oss_assessment,
            diff_summary=diff_summary,
            change_summary=change_summary,
        )
        request.revisions.append(revision)
        request.updated_at = utc_now()
        self.store.save_request(request)
        self._audit(
            'role_private_studio_refreshed',
            request.status,
            'Role Private Studio request regenerated and revalidated.',
            {
                'request_id': request.request_id,
                'role_id': request.normalized_spec.role_id if request.normalized_spec else None,
                'trigger': trigger,
                'actor': actor,
                'revision_number': revision.revision_number,
                'change_summary': change_summary,
                'pt_oss_posture': request.pt_oss_assessment.posture if request.pt_oss_assessment else None,
                'pt_oss_readiness_score': request.pt_oss_assessment.readiness_score if request.pt_oss_assessment else None,
            },
        )
        return request.to_dict()

    def _audit(self, action: str, outcome: str, reason: str, metadata: dict[str, object]) -> None:
        if self.audit_logger is None:
            return
        self.audit_logger.record_event(active_role='ROLE_PRIVATE_STUDIO', action=action, outcome=outcome, reason=reason, metadata=metadata)
