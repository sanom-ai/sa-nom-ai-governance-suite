from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class StructuredJD:
    role_name: str = ''
    purpose: str = ''
    reporting_line: str = 'GOV'
    business_domain: str = ''
    operating_mode: str = 'direct'
    assigned_user_id: str = ''
    executive_owner_id: str = 'EXEC_OWNER'
    seat_id: str = ''
    responsibilities: list[str] = field(default_factory=list)
    allowed_actions: list[str] = field(default_factory=list)
    forbidden_actions: list[str] = field(default_factory=list)
    wait_human_actions: list[str] = field(default_factory=list)
    handled_resources: list[str] = field(default_factory=list)
    financial_sensitivity: str = 'medium'
    legal_sensitivity: str = 'medium'
    compliance_sensitivity: str = 'medium'
    sample_scenarios: list[str] = field(default_factory=list)
    operator_notes: str = ''
    attachments: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'StructuredJD':
        return cls(
            role_name=str(data.get('role_name', '')),
            purpose=str(data.get('purpose', '')),
            reporting_line=str(data.get('reporting_line', 'GOV') or 'GOV'),
            business_domain=str(data.get('business_domain', '')),
            operating_mode=str(data.get('operating_mode', 'direct') or 'direct'),
            assigned_user_id=str(data.get('assigned_user_id', '')),
            executive_owner_id=str(data.get('executive_owner_id', 'EXEC_OWNER') or 'EXEC_OWNER'),
            seat_id=str(data.get('seat_id', '')),
            responsibilities=[str(item) for item in data.get('responsibilities', []) if str(item).strip()],
            allowed_actions=[str(item) for item in data.get('allowed_actions', []) if str(item).strip()],
            forbidden_actions=[str(item) for item in data.get('forbidden_actions', []) if str(item).strip()],
            wait_human_actions=[str(item) for item in data.get('wait_human_actions', []) if str(item).strip()],
            handled_resources=[str(item) for item in data.get('handled_resources', []) if str(item).strip()],
            financial_sensitivity=str(data.get('financial_sensitivity', 'medium') or 'medium'),
            legal_sensitivity=str(data.get('legal_sensitivity', 'medium') or 'medium'),
            compliance_sensitivity=str(data.get('compliance_sensitivity', 'medium') or 'medium'),
            sample_scenarios=[str(item) for item in data.get('sample_scenarios', []) if str(item).strip()],
            operator_notes=str(data.get('operator_notes', '')),
            attachments=[item for item in data.get('attachments', []) if isinstance(item, dict)],
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class NormalizedRoleSpec:
    role_id: str
    title: str
    purpose: str
    reports_to: str
    domain: str
    operating_mode: str = 'direct'
    assigned_user_id: str = ''
    executive_owner_id: str = 'EXEC_OWNER'
    seat_id: str = ''
    responsibilities: list[str] = field(default_factory=list)
    allowed_actions: list[str] = field(default_factory=list)
    forbidden_actions: list[str] = field(default_factory=list)
    wait_human_actions: list[str] = field(default_factory=list)
    auto_wait_human_actions: list[str] = field(default_factory=list)
    handled_resources: list[str] = field(default_factory=list)
    sensitivity_profile: dict[str, str] = field(default_factory=dict)
    risk_threshold: float = 0.6
    ambiguity_notes: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> 'NormalizedRoleSpec | None':
        if not data:
            return None
        return cls(
            role_id=str(data.get('role_id', '')),
            title=str(data.get('title', '')),
            purpose=str(data.get('purpose', '')),
            reports_to=str(data.get('reports_to', 'GOV') or 'GOV'),
            domain=str(data.get('domain', '')),
            operating_mode=str(data.get('operating_mode', 'direct') or 'direct'),
            assigned_user_id=str(data.get('assigned_user_id', '')),
            executive_owner_id=str(data.get('executive_owner_id', 'EXEC_OWNER') or 'EXEC_OWNER'),
            seat_id=str(data.get('seat_id', '')),
            responsibilities=[str(item) for item in data.get('responsibilities', [])],
            allowed_actions=[str(item) for item in data.get('allowed_actions', [])],
            forbidden_actions=[str(item) for item in data.get('forbidden_actions', [])],
            wait_human_actions=[str(item) for item in data.get('wait_human_actions', [])],
            auto_wait_human_actions=[str(item) for item in data.get('auto_wait_human_actions', [])],
            handled_resources=[str(item) for item in data.get('handled_resources', [])],
            sensitivity_profile={str(key): str(value) for key, value in data.get('sensitivity_profile', {}).items()},
            risk_threshold=float(data.get('risk_threshold', 0.6)),
            ambiguity_notes=[str(item) for item in data.get('ambiguity_notes', [])],
            risk_flags=[str(item) for item in data.get('risk_flags', [])],
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ValidationFinding:
    severity: str
    code: str
    message: str
    role_id: str | None = None
    action: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'ValidationFinding':
        return cls(
            severity=str(data.get('severity', 'warning')),
            code=str(data.get('code', 'UNKNOWN')),
            message=str(data.get('message', '')),
            role_id=str(data.get('role_id')) if data.get('role_id') is not None else None,
            action=str(data.get('action')) if data.get('action') is not None else None,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ValidationReport:
    report_id: str
    syntax_passed: bool
    semantic_passed: bool
    blocked_publish: bool
    generated_at: str
    findings: list[ValidationFinding] = field(default_factory=list)
    coverage_gaps: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> 'ValidationReport | None':
        if not data:
            return None
        return cls(
            report_id=str(data.get('report_id', '')),
            syntax_passed=bool(data.get('syntax_passed', False)),
            semantic_passed=bool(data.get('semantic_passed', False)),
            blocked_publish=bool(data.get('blocked_publish', True)),
            generated_at=str(data.get('generated_at', utc_now())),
            findings=[ValidationFinding.from_dict(item) for item in data.get('findings', [])],
            coverage_gaps=[str(item) for item in data.get('coverage_gaps', [])],
        )

    @property
    def critical_findings(self) -> list[ValidationFinding]:
        return [finding for finding in self.findings if finding.severity == 'critical']

    @property
    def warning_findings(self) -> list[ValidationFinding]:
        return [finding for finding in self.findings if finding.severity != 'critical']

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload['critical_findings'] = [item.to_dict() for item in self.critical_findings]
        payload['warning_findings'] = [item.to_dict() for item in self.warning_findings]
        return payload


@dataclass(slots=True)
class SimulationScenarioResult:
    scenario_id: str
    category: str
    expected_outcome: str
    observed_outcome: str
    passed: bool
    policy_basis: str | None = None
    reason: str = ''
    failed_conditions: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    input_request: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'SimulationScenarioResult':
        return cls(
            scenario_id=str(data.get('scenario_id', '')),
            category=str(data.get('category', '')),
            expected_outcome=str(data.get('expected_outcome', '')),
            observed_outcome=str(data.get('observed_outcome', '')),
            passed=bool(data.get('passed', False)),
            policy_basis=str(data.get('policy_basis')) if data.get('policy_basis') else None,
            reason=str(data.get('reason', '')),
            failed_conditions=[str(item) for item in data.get('failed_conditions', [])],
            notes=[str(item) for item in data.get('notes', [])],
            input_request=data.get('input_request', {}) if isinstance(data.get('input_request', {}), dict) else {},
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SimulationReport:
    report_id: str
    generated_at: str
    scenario_results: list[SimulationScenarioResult] = field(default_factory=list)
    status: str = 'not_run'

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> 'SimulationReport | None':
        if not data:
            return None
        return cls(
            report_id=str(data.get('report_id', '')),
            generated_at=str(data.get('generated_at', utc_now())),
            scenario_results=[SimulationScenarioResult.from_dict(item) for item in data.get('scenario_results', [])],
            status=str(data.get('status', 'not_run')),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload['scenario_count'] = len(self.scenario_results)
        payload['passed_count'] = sum(1 for item in self.scenario_results if item.passed)
        payload['failed_count'] = sum(1 for item in self.scenario_results if not item.passed)
        payload['escalated_count'] = sum(1 for item in self.scenario_results if item.observed_outcome == 'escalated')
        payload['waiting_human_count'] = sum(1 for item in self.scenario_results if item.observed_outcome == 'waiting_human')
        payload['conflicted_count'] = sum(1 for item in self.scenario_results if item.observed_outcome == 'conflicted')
        return payload


@dataclass(slots=True)
class PTOSSMetricScore:
    metric_id: str
    name: str
    value: float
    unit: str
    label: str
    risk_level: str
    default_action: str
    rationale: str = ''

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'PTOSSMetricScore':
        return cls(
            metric_id=str(data.get('metric_id', '')),
            name=str(data.get('name', '')),
            value=float(data.get('value', 0)),
            unit=str(data.get('unit', '')),
            label=str(data.get('label', '')),
            risk_level=str(data.get('risk_level', 'unknown')),
            default_action=str(data.get('default_action', 'review')),
            rationale=str(data.get('rationale', '')),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PTOSSIssue:
    category: str
    severity: str
    message: str
    blocks_publish: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'PTOSSIssue':
        return cls(
            category=str(data.get('category', 'structural_intelligence')),
            severity=str(data.get('severity', 'warning')),
            message=str(data.get('message', '')),
            blocks_publish=bool(data.get('blocks_publish', False)),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PTOSSAssessment:
    assessment_id: str
    generated_at: str
    mode: str
    posture: str
    readiness_score: int
    metrics: list[PTOSSMetricScore] = field(default_factory=list)
    blockers: list[PTOSSIssue] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> 'PTOSSAssessment | None':
        if not data:
            return None
        return cls(
            assessment_id=str(data.get('assessment_id', '')),
            generated_at=str(data.get('generated_at', utc_now())),
            mode=str(data.get('mode', 'PT_OSS_FULL')),
            posture=str(data.get('posture', 'watch')),
            readiness_score=int(data.get('readiness_score', 0)),
            metrics=[PTOSSMetricScore.from_dict(item) for item in data.get('metrics', [])],
            blockers=[PTOSSIssue.from_dict(item) for item in data.get('blockers', [])],
            recommendations=[str(item) for item in data.get('recommendations', [])],
            context=data.get('context', {}) if isinstance(data.get('context', {}), dict) else {},
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload['critical_blocker_count'] = sum(1 for item in self.blockers if item.severity == 'critical')
        payload['blocking_issue_count'] = sum(1 for item in self.blockers if item.blocks_publish)
        payload['metric_count'] = len(self.metrics)
        return payload


@dataclass(slots=True)
class ReviewDecision:
    review_id: str
    decision: str
    reviewer: str
    note: str
    created_at: str
    revision_number: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'ReviewDecision':
        return cls(
            review_id=str(data.get('review_id', '')),
            decision=str(data.get('decision', '')),
            reviewer=str(data.get('reviewer', '')),
            note=str(data.get('note', '')),
            created_at=str(data.get('created_at', utc_now())),
            revision_number=int(data.get('revision_number', 0)),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PublishArtifact:
    publish_id: str
    role_id: str
    published_by: str
    published_at: str
    role_path: str
    trusted_sha256: str
    manifest_key_id: str
    manifest_signature_status: str
    revision_number: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> 'PublishArtifact | None':
        if not data:
            return None
        return cls(
            publish_id=str(data.get('publish_id', '')),
            role_id=str(data.get('role_id', '')),
            published_by=str(data.get('published_by', '')),
            published_at=str(data.get('published_at', utc_now())),
            role_path=str(data.get('role_path', '')),
            trusted_sha256=str(data.get('trusted_sha256', '')),
            manifest_key_id=str(data.get('manifest_key_id', '')),
            manifest_signature_status=str(data.get('manifest_signature_status', 'unknown')),
            revision_number=int(data.get('revision_number', 0)),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RoleDraftRevision:
    revision_id: str
    revision_number: int
    trigger: str
    generated_at: str
    structured_jd_snapshot: StructuredJD
    normalized_spec: NormalizedRoleSpec | None = None
    generated_ptag: str = ''
    system_generated_ptag: str = ''
    ptag_source_mode: str = 'generated'
    validation_report: ValidationReport | None = None
    simulation_report: SimulationReport | None = None
    pt_oss_assessment: PTOSSAssessment | None = None
    diff_summary: dict[str, Any] = field(default_factory=dict)
    change_summary: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'RoleDraftRevision':
        return cls(
            revision_id=str(data.get('revision_id', '')),
            revision_number=int(data.get('revision_number', 0)),
            trigger=str(data.get('trigger', 'refresh')),
            generated_at=str(data.get('generated_at', utc_now())),
            structured_jd_snapshot=StructuredJD.from_dict(data.get('structured_jd_snapshot', {})),
            normalized_spec=NormalizedRoleSpec.from_dict(data.get('normalized_spec')),
            generated_ptag=str(data.get('generated_ptag', '')),
            system_generated_ptag=str(data.get('system_generated_ptag', data.get('generated_ptag', ''))),
            ptag_source_mode=str(data.get('ptag_source_mode', 'generated') or 'generated'),
            validation_report=ValidationReport.from_dict(data.get('validation_report')),
            simulation_report=SimulationReport.from_dict(data.get('simulation_report')),
            pt_oss_assessment=PTOSSAssessment.from_dict(data.get('pt_oss_assessment')),
            diff_summary=data.get('diff_summary', {}) if isinstance(data.get('diff_summary', {}), dict) else {},
            change_summary=[str(item) for item in data.get('change_summary', [])],
        )

    def to_dict(self, include_source: bool = True) -> dict[str, Any]:
        payload = {
            'revision_id': self.revision_id,
            'revision_number': self.revision_number,
            'trigger': self.trigger,
            'generated_at': self.generated_at,
            'structured_jd_snapshot': self.structured_jd_snapshot.to_dict(),
            'normalized_spec': self.normalized_spec.to_dict() if self.normalized_spec else None,
            'system_generated_ptag': self.system_generated_ptag,
            'ptag_source_mode': self.ptag_source_mode,
            'validation_report': self.validation_report.to_dict() if self.validation_report else None,
            'simulation_report': self.simulation_report.to_dict() if self.simulation_report else None,
            'pt_oss_assessment': self.pt_oss_assessment.to_dict() if self.pt_oss_assessment else None,
            'diff_summary': self.diff_summary,
            'change_summary': self.change_summary,
        }
        if include_source:
            payload['generated_ptag'] = self.generated_ptag
        return payload


@dataclass(slots=True)
class RolePrivateStudioRequest:
    request_id: str
    requested_by: str
    created_at: str
    updated_at: str
    status: str
    structured_jd: StructuredJD
    normalized_spec: NormalizedRoleSpec | None = None
    generated_ptag: str = ''
    system_generated_ptag: str = ''
    ptag_override_source: str = ''
    ptag_source_mode: str = 'generated'
    validation_report: ValidationReport | None = None
    simulation_report: SimulationReport | None = None
    pt_oss_assessment: PTOSSAssessment | None = None
    review_history: list[ReviewDecision] = field(default_factory=list)
    revisions: list[RoleDraftRevision] = field(default_factory=list)
    publish_artifact: PublishArtifact | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'RolePrivateStudioRequest':
        return cls(
            request_id=str(data.get('request_id', '')),
            requested_by=str(data.get('requested_by', '')),
            created_at=str(data.get('created_at', utc_now())),
            updated_at=str(data.get('updated_at', utc_now())),
            status=str(data.get('status', 'draft')),
            structured_jd=StructuredJD.from_dict(data.get('structured_jd', {})),
            normalized_spec=NormalizedRoleSpec.from_dict(data.get('normalized_spec')),
            generated_ptag=str(data.get('generated_ptag', '')),
            system_generated_ptag=str(data.get('system_generated_ptag', data.get('generated_ptag', ''))),
            ptag_override_source=str(data.get('ptag_override_source', '')),
            ptag_source_mode=str(data.get('ptag_source_mode', 'generated') or 'generated'),
            validation_report=ValidationReport.from_dict(data.get('validation_report')),
            simulation_report=SimulationReport.from_dict(data.get('simulation_report')),
            pt_oss_assessment=PTOSSAssessment.from_dict(data.get('pt_oss_assessment')),
            review_history=[ReviewDecision.from_dict(item) for item in data.get('review_history', [])],
            revisions=[RoleDraftRevision.from_dict(item) for item in data.get('revisions', [])],
            publish_artifact=PublishArtifact.from_dict(data.get('publish_artifact')),
        )

    def to_dict(self, compact: bool = False) -> dict[str, Any]:
        latest_revision = self.revisions[-1] if self.revisions else None
        previous_revision = self.revisions[-2] if len(self.revisions) > 1 else None
        coverage_summary = _build_coverage_summary(
            normalized_spec=self.normalized_spec,
            validation_report=self.validation_report,
            simulation_report=self.simulation_report,
            current_ptag=self.generated_ptag,
            generated_ptag=self.system_generated_ptag,
        )
        publish_readiness = _build_publish_readiness(
            status=self.status,
            validation_report=self.validation_report,
            simulation_report=self.simulation_report,
            review_history=self.review_history,
            publish_artifact=self.publish_artifact,
            normalized_spec=self.normalized_spec,
            revisions=self.revisions,
            current_ptag=self.generated_ptag,
            generated_ptag=self.system_generated_ptag,
            coverage_summary=coverage_summary,
            pt_oss_assessment=self.pt_oss_assessment,
        )
        payload = {
            'request_id': self.request_id,
            'requested_by': self.requested_by,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'status': self.status,
            'structured_jd': self.structured_jd.to_dict(),
            'normalized_spec': self.normalized_spec.to_dict() if self.normalized_spec else None,
            'generated_ptag': self.generated_ptag,
            'system_generated_ptag': self.system_generated_ptag,
            'ptag_override_source': self.ptag_override_source,
            'ptag_source_mode': self.ptag_source_mode,
            'validation_report': self.validation_report.to_dict() if self.validation_report else None,
            'simulation_report': self.simulation_report.to_dict() if self.simulation_report else None,
            'pt_oss_assessment': self.pt_oss_assessment.to_dict() if self.pt_oss_assessment else None,
            'review_history': [item.to_dict() for item in self.review_history],
            'revisions': [item.to_dict(include_source=not compact) for item in self.revisions],
            'publish_artifact': self.publish_artifact.to_dict() if self.publish_artifact else None,
            'coverage_summary': coverage_summary,
            'publish_readiness': publish_readiness,
            'publication_workflow': _build_publication_workflow(
                status=self.status,
                review_history=self.review_history,
                publish_artifact=self.publish_artifact,
                publish_readiness=publish_readiness,
                current_revision_number=latest_revision.revision_number if latest_revision else 0,
            ),
        }
        payload['summary'] = {
            'role_id': self.normalized_spec.role_id if self.normalized_spec else '',
            'role_name': self.structured_jd.role_name,
            'operating_mode': self.normalized_spec.operating_mode if self.normalized_spec else self.structured_jd.operating_mode,
            'assigned_user_id': self.normalized_spec.assigned_user_id if self.normalized_spec else self.structured_jd.assigned_user_id,
            'executive_owner_id': self.normalized_spec.executive_owner_id if self.normalized_spec else self.structured_jd.executive_owner_id,
            'seat_id': self.normalized_spec.seat_id if self.normalized_spec else self.structured_jd.seat_id,
            'validation_blocked': self.validation_report.blocked_publish if self.validation_report else True,
            'simulation_status': self.simulation_report.status if self.simulation_report else 'not_run',
            'review_count': len(self.review_history),
            'published': self.publish_artifact is not None,
            'current_revision': latest_revision.revision_number if latest_revision else 0,
            'ptag_source_mode': self.ptag_source_mode,
            'ptag_override_present': bool(self.ptag_override_source.strip()),
            'pt_oss_posture': self.pt_oss_assessment.posture if self.pt_oss_assessment else 'unknown',
            'pt_oss_readiness_score': self.pt_oss_assessment.readiness_score if self.pt_oss_assessment else 0,
            'readiness_score': publish_readiness.get('readiness_score', 0),
            'blocker_total': len(publish_readiness.get('blockers', [])),
            'latest_diff': latest_revision.diff_summary if latest_revision else {},
            'latest_change_summary': latest_revision.change_summary if latest_revision else [],
            'approved_for_current_revision': publish_readiness['gates'].get('review', False),
            'latest_review_decision': self.review_history[-1].decision if self.review_history else None,
            'review_timeline': _build_review_timeline(self.review_history),
            'simulation_history': _build_simulation_history(self.revisions),
            'editor_compare': _build_editor_compare(
                current_ptag=self.generated_ptag,
                generated_ptag=self.system_generated_ptag,
                ptag_source_mode=self.ptag_source_mode,
            ),
            'revision_compare': {
                'current_revision_number': latest_revision.revision_number if latest_revision else 0,
                'previous_revision_number': previous_revision.revision_number if previous_revision else 0,
                'current_trigger': latest_revision.trigger if latest_revision else None,
                'previous_trigger': previous_revision.trigger if previous_revision else None,
                'current_generated_at': latest_revision.generated_at if latest_revision else None,
                'previous_generated_at': previous_revision.generated_at if previous_revision else None,
                'current_structured_jd': latest_revision.structured_jd_snapshot.to_dict() if latest_revision else None,
                'previous_structured_jd': previous_revision.structured_jd_snapshot.to_dict() if previous_revision else None,
                'current_generated_ptag': latest_revision.generated_ptag if latest_revision else '',
                'current_system_generated_ptag': latest_revision.system_generated_ptag if latest_revision else '',
                'previous_generated_ptag': previous_revision.generated_ptag if previous_revision else '',
                'previous_system_generated_ptag': previous_revision.system_generated_ptag if previous_revision else '',
                'current_change_summary': latest_revision.change_summary if latest_revision else [],
                'previous_change_summary': previous_revision.change_summary if previous_revision else [],
            },
        }
        return payload


def _build_publish_readiness(
    status: str,
    validation_report: ValidationReport | None,
    simulation_report: SimulationReport | None,
    review_history: list[ReviewDecision],
    publish_artifact: PublishArtifact | None,
    normalized_spec: NormalizedRoleSpec | None,
    revisions: list[RoleDraftRevision],
    current_ptag: str,
    generated_ptag: str,
    coverage_summary: dict[str, Any],
    pt_oss_assessment: PTOSSAssessment | None,
) -> dict[str, Any]:
    blocker_entries: list[dict[str, str]] = []
    current_revision_number = revisions[-1].revision_number if revisions else 0
    approved_for_current_revision = any(item.decision == 'approve' and item.revision_number == current_revision_number for item in review_history)
    if current_revision_number and not any(item.revision_number for item in review_history):
        approved_for_current_revision = approved_for_current_revision or any(item.decision == 'approve' for item in review_history)

    if normalized_spec is None:
        blocker_entries.append({'category': 'structure', 'severity': 'critical', 'message': 'Normalized role specification is missing.'})
    if validation_report is None:
        blocker_entries.append({'category': 'validation', 'severity': 'critical', 'message': 'Validation report is missing.'})
    elif validation_report.blocked_publish:
        blocker_entries.extend(
            {'category': 'validation', 'severity': finding.severity, 'message': finding.message}
            for finding in validation_report.critical_findings
        )
    if simulation_report is None:
        blocker_entries.append({'category': 'simulation', 'severity': 'critical', 'message': 'Simulation report is missing.'})
    elif simulation_report.status != 'passed':
        blocker_entries.append({'category': 'simulation', 'severity': 'critical', 'message': f'Simulation status is {simulation_report.status}.'})
    if status not in {'approved', 'published'}:
        blocker_entries.append({'category': 'review', 'severity': 'warning', 'message': 'Draft is not approved for publish.'})
    if not approved_for_current_revision:
        blocker_entries.append({'category': 'review', 'severity': 'critical', 'message': 'The current revision has not been approved yet.'})
    structural_gate = False
    structural_state = 'blocked'
    structural_gate_reason = ''
    advisory_entries: list[dict[str, str]] = []
    if pt_oss_assessment is None:
        blocker_entries.append({'category': 'structural_intelligence', 'severity': 'warning', 'message': 'PT-OSS structural assessment is missing.'})
    else:
        structural_state, structural_gate_reason = _resolve_structural_state(pt_oss_assessment)
        structural_gate = structural_state == 'ready'
        for blocker in pt_oss_assessment.blockers:
            if blocker.blocks_publish:
                blocker_entries.append({'category': blocker.category, 'severity': blocker.severity, 'message': blocker.message})
        if structural_state == 'guarded':
            advisory_entries.append({
                'category': 'structural_intelligence',
                'severity': 'warning',
                'message': structural_gate_reason,
            })
    if publish_artifact is not None:
        blocker_entries = []
        advisory_entries = []
        structural_state = 'published'
        structural_gate_reason = 'Role pack is already published into the trusted registry.'

    blockers = [entry['message'] for entry in blocker_entries]
    blocker_groups = _group_blockers(blocker_entries)
    advisories = [entry['message'] for entry in advisory_entries]
    advisory_groups = _group_blockers(advisory_entries)

    gates = {
        'validation': bool(validation_report is not None and not validation_report.blocked_publish),
        'simulation': bool(simulation_report is not None and simulation_report.status == 'passed'),
        'review': approved_for_current_revision,
        'publish_state': status in {'approved', 'published'},
        'trusted_registry': publish_artifact is not None or status == 'approved',
        'structural_intelligence': structural_gate or publish_artifact is not None,
        'current_revision': current_revision_number,
    }
    readiness_score = _build_readiness_score(gates=gates, blocker_entries=blocker_entries, coverage_summary=coverage_summary, pt_oss_assessment=pt_oss_assessment)
    status = 'published' if publish_artifact is not None else ('blocked' if blockers else ('guarded' if structural_state == 'guarded' else 'ready'))
    return {
        'ready': publish_artifact is not None or (not blockers and structural_state == 'ready'),
        'status': status,
        'blockers': blockers,
        'blocker_groups': blocker_groups,
        'advisories': advisories,
        'advisory_groups': advisory_groups,
        'severity_counts': _count_blocker_severities(blocker_entries),
        'readiness_score': readiness_score,
        'coverage_summary': coverage_summary,
        'pt_oss_summary': pt_oss_assessment.to_dict() if pt_oss_assessment else None,
        'structural_state': structural_state,
        'structural_gate_reason': structural_gate_reason,
        'gates': gates,
        'role_path_preview': f"{normalized_spec.role_id}.ptn" if normalized_spec else None,
        'editor_compare': _build_editor_compare(current_ptag=current_ptag, generated_ptag=generated_ptag, ptag_source_mode='manual' if current_ptag != generated_ptag and generated_ptag else 'generated'),
    }


def _build_publication_workflow(status: str, review_history: list[ReviewDecision], publish_artifact: PublishArtifact | None, publish_readiness: dict[str, Any], current_revision_number: int) -> dict[str, Any]:
    latest_review = review_history[-1] if review_history else None
    current_revision_review = next(
        (item for item in reversed(review_history) if item.revision_number == current_revision_number),
        latest_review,
    )
    review_state = 'approved' if publish_readiness['gates'].get('review') else (
        'changes_requested' if status == 'changes_requested' else 'awaiting_review'
    )
    publication_state = 'published' if publish_artifact is not None else (
        'publisher_ready'
        if status == 'approved' and publish_readiness['status'] == 'ready'
        else ('structural_review' if publish_readiness['status'] == 'guarded' else ('blocked' if publish_readiness['status'] == 'blocked' else 'in_progress'))
    )
    stages = [
        {'id': 'authoring', 'label': 'Authoring', 'status': 'complete'},
        {'id': 'validation', 'label': 'Validation', 'status': 'complete' if publish_readiness['gates'].get('validation') else 'blocked'},
        {'id': 'simulation', 'label': 'Simulation', 'status': 'complete' if publish_readiness['gates'].get('simulation') else 'blocked'},
        {'id': 'structural', 'label': 'PT-OSS Structural Gate', 'status': 'complete' if publish_readiness.get('structural_state') in {'ready', 'published'} else ('guarded' if publish_readiness.get('structural_state') == 'guarded' else 'blocked')},
        {'id': 'review', 'label': 'Review Approval', 'status': review_state},
        {'id': 'publication', 'label': 'Publication', 'status': publication_state},
    ]
    return {
        'status': publication_state,
        'current_revision_number': current_revision_number,
        'latest_review_decision': current_revision_review.decision if current_revision_review else None,
        'latest_reviewer': current_revision_review.reviewer if current_revision_review else None,
        'latest_review_note': current_revision_review.note if current_revision_review else None,
        'latest_review_at': current_revision_review.created_at if current_revision_review else None,
        'published_at': publish_artifact.published_at if publish_artifact else None,
        'published_by': publish_artifact.published_by if publish_artifact else None,
        'review_timeline': _build_review_timeline(review_history),
        'stages': stages,
    }


def _build_coverage_summary(
    normalized_spec: NormalizedRoleSpec | None,
    validation_report: ValidationReport | None,
    simulation_report: SimulationReport | None,
    current_ptag: str,
    generated_ptag: str,
) -> dict[str, Any]:
    allowed_actions = normalized_spec.allowed_actions if normalized_spec else []
    coverage_gaps = validation_report.coverage_gaps if validation_report else []
    covered_actions = max(len(allowed_actions) - len(coverage_gaps), 0)
    hierarchy_ready = bool(
        normalized_spec
        and normalized_spec.reports_to
        and 'reports_to:' in current_ptag
        and 'escalation_to:' in current_ptag
        and 'safety_owner:' in current_ptag
    )
    escalation_actions = normalized_spec.wait_human_actions if normalized_spec else []
    safety_ready = bool(
        normalized_spec
        and 'safety_owner:' in current_ptag
        and (
            escalation_actions
            or not normalized_spec.auto_wait_human_actions
            or any('require human_override' in current_ptag for _action in normalized_spec.auto_wait_human_actions)
        )
    )
    simulation_payload = simulation_report.to_dict() if simulation_report else {}
    categories = sorted({item.category for item in simulation_report.scenario_results}) if simulation_report else []
    manual_delta = _line_delta(generated_ptag, current_ptag) if current_ptag or generated_ptag else {'added': 0, 'removed': 0}
    return {
        'policy': {
            'status': 'ready' if allowed_actions and not coverage_gaps else ('warning' if allowed_actions else 'blocked'),
            'covered_actions': covered_actions,
            'total_actions': len(allowed_actions),
            'gaps': coverage_gaps,
        },
        'hierarchy': {
            'status': 'ready' if hierarchy_ready else 'warning',
            'reports_to': normalized_spec.reports_to if normalized_spec else '',
            'escalation_defined': 'escalation_to:' in current_ptag,
            'safety_owner_defined': 'safety_owner:' in current_ptag,
        },
        'escalation': {
            'status': 'ready' if safety_ready else 'warning',
            'wait_human_actions': escalation_actions,
            'auto_wait_human_actions': normalized_spec.auto_wait_human_actions if normalized_spec else [],
        },
        'simulation': {
            'status': simulation_report.status if simulation_report else 'not_run',
            'categories': categories,
            'scenario_count': simulation_payload.get('scenario_count', 0),
            'failed_count': simulation_payload.get('failed_count', 0),
        },
        'editor': {
            'status': 'manual_override' if current_ptag != generated_ptag and generated_ptag else 'generated',
            'current_line_count': _line_count(current_ptag),
            'generated_line_count': _line_count(generated_ptag),
            'manual_delta': manual_delta,
        },
    }


def _build_editor_compare(current_ptag: str, generated_ptag: str, ptag_source_mode: str) -> dict[str, Any]:
    delta = _line_delta(generated_ptag, current_ptag)
    return {
        'mode': ptag_source_mode,
        'current_line_count': _line_count(current_ptag),
        'generated_line_count': _line_count(generated_ptag),
        'added_lines': delta['added'],
        'removed_lines': delta['removed'],
        'manual_override_active': bool(generated_ptag and current_ptag != generated_ptag),
    }


def _build_review_timeline(review_history: list[ReviewDecision]) -> list[dict[str, Any]]:
    return [
        {
            'review_id': item.review_id,
            'decision': item.decision,
            'reviewer': item.reviewer,
            'note': item.note,
            'created_at': item.created_at,
            'revision_number': item.revision_number,
        }
        for item in sorted(review_history, key=lambda review: review.created_at, reverse=True)
    ]


def _build_simulation_history(revisions: list[RoleDraftRevision]) -> list[dict[str, Any]]:
    history: list[dict[str, Any]] = []
    for revision in sorted(revisions, key=lambda item: item.revision_number, reverse=True):
        report = revision.simulation_report
        report_payload = report.to_dict() if report else {}
        history.append(
            {
                'revision_number': revision.revision_number,
                'trigger': revision.trigger,
                'generated_at': revision.generated_at,
                'status': report.status if report else 'not_run',
                'scenario_count': report_payload.get('scenario_count', 0),
                'passed_count': report_payload.get('passed_count', 0),
                'failed_count': report_payload.get('failed_count', 0),
                'escalated_count': report_payload.get('escalated_count', 0),
                'waiting_human_count': report_payload.get('waiting_human_count', 0),
            }
        )
    return history


def _group_blockers(entries: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    groups: dict[str, list[dict[str, str]]] = {}
    for entry in entries:
        groups.setdefault(entry['category'], []).append(entry)
    return groups


def _count_blocker_severities(entries: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in entries:
        counts[entry['severity']] = counts.get(entry['severity'], 0) + 1
    return counts


def _build_readiness_score(gates: dict[str, Any], blocker_entries: list[dict[str, str]], coverage_summary: dict[str, Any], pt_oss_assessment: PTOSSAssessment | None) -> int:
    score = 0
    if gates.get('validation'):
        score += 25
    if gates.get('simulation'):
        score += 25
    if gates.get('review'):
        score += 20
    if gates.get('structural_intelligence'):
        score += 10
    if coverage_summary.get('policy', {}).get('status') == 'ready':
        score += 10
    if coverage_summary.get('hierarchy', {}).get('status') == 'ready':
        score += 10
    if coverage_summary.get('escalation', {}).get('status') == 'ready':
        score += 10
    penalty = sum(8 if entry['severity'] == 'critical' else 4 for entry in blocker_entries)
    score = max(0, min(100, score - penalty))
    if pt_oss_assessment is None:
        return score
    return max(0, min(100, int(round((score * 0.75) + (pt_oss_assessment.readiness_score * 0.25)))))


def _resolve_structural_state(pt_oss_assessment: PTOSSAssessment) -> tuple[str, str]:
    if any(item.blocks_publish for item in pt_oss_assessment.blockers):
        return 'blocked', 'PT-OSS is blocking publication because structural issues are still above the safe threshold.'
    posture = (pt_oss_assessment.posture or 'unknown').lower()
    readiness_score = int(pt_oss_assessment.readiness_score or 0)
    if posture in {'elevated', 'fragile'} or readiness_score < 68:
        return 'guarded', 'PT-OSS requires structural mitigation before publication can move from guarded posture to ready.'
    if (posture == 'watch' and readiness_score < 76) or readiness_score < 72:
        return 'guarded', 'PT-OSS is holding this draft in guarded structural review until resilience signals strengthen.'
    return 'ready', 'PT-OSS structural posture is ready for governed publication.'


def _line_count(source: str) -> int:
    if not source:
        return 0
    return len(str(source).splitlines())


def _line_delta(previous: str, current: str) -> dict[str, int]:
    previous_lines = str(previous or '').splitlines()
    current_lines = str(current or '').splitlines()
    previous_set = set(previous_lines)
    current_set = set(current_lines)
    return {
        'added': len([line for line in current_lines if line not in previous_set]),
        'removed': len([line for line in previous_lines if line not in current_set]),
    }


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
