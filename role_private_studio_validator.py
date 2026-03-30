from uuid import uuid4

from ptag_parser import PTAGParser
from ptag_semantic import SemanticAnalyzer
from ptag_validator import PTAGValidator
from role_private_studio_models import RolePrivateStudioRequest, ValidationFinding, ValidationReport, utc_now


class RolePrivateStudioValidator:
    REQUIRED_FIELDS = {
        'role_name': 'Role name is required.',
        'purpose': 'Role purpose is required.',
        'business_domain': 'Business domain is required.',
    }

    def __init__(self) -> None:
        self.parser = PTAGParser()
        self.validator = PTAGValidator()
        self.semantic = SemanticAnalyzer()

    def validate(self, request: RolePrivateStudioRequest) -> ValidationReport:
        findings: list[ValidationFinding] = []
        structured = request.structured_jd
        normalized = request.normalized_spec

        for field_name, message in self.REQUIRED_FIELDS.items():
            if not str(getattr(structured, field_name, '')).strip():
                findings.append(ValidationFinding(severity='critical', code=f'MISSING_{field_name.upper()}', message=message))

        if not structured.allowed_actions:
            findings.append(ValidationFinding(severity='critical', code='MISSING_ALLOWED_ACTIONS', message='At least one allowed action is required.'))
        if not structured.handled_resources:
            findings.append(ValidationFinding(severity='warning', code='MISSING_HANDLED_RESOURCES', message='Handled resources are empty; runtime policies will use general_resource safeguards.'))
        operating_mode = str(structured.operating_mode or 'direct').strip().lower()
        if operating_mode not in {'indirect', 'direct'}:
            findings.append(ValidationFinding(severity='critical', code='INVALID_OPERATING_MODE', message='Operating mode must be either indirect or direct.'))
        if operating_mode == 'indirect' and not str(structured.assigned_user_id or '').strip():
            findings.append(ValidationFinding(severity='critical', code='INDIRECT_REQUIRES_ASSIGNED_USER', message='Indirect hats must declare an assigned user id.'))
        if operating_mode == 'direct' and str(structured.assigned_user_id or '').strip():
            findings.append(ValidationFinding(severity='warning', code='DIRECT_IGNORES_ASSIGNED_USER', message='Assigned user id is ignored for direct hats because executive ownership is authoritative.'))
        if normalized and normalized.auto_wait_human_actions:
            findings.append(ValidationFinding(severity='warning', code='AUTO_SAFETY_UPGRADE', message=f'High-risk powers were auto-mapped to human override: {", ".join(normalized.auto_wait_human_actions)}.', role_id=normalized.role_id))

        syntax_passed = False
        semantic_passed = False
        coverage_gaps: list[str] = []

        try:
            parsed = self.parser.parse(request.generated_ptag)
            self.validator.validate(parsed)
            syntax_passed = True
            semantic = self.semantic.analyze(parsed)
            semantic_passed = True
            if normalized and normalized.role_id and normalized.role_id not in semantic.roles:
                findings.append(
                    ValidationFinding(
                        severity='critical',
                        code='PTAG_ROLE_ID_MISMATCH',
                        message=f'PTAG source does not define the expected role id {normalized.role_id}.',
                        role_id=normalized.role_id,
                    )
                )
            for issue in self.validator.validate_semantic(semantic):
                findings.append(ValidationFinding(severity='warning' if issue.severity != 'critical' else 'critical', code=issue.code, message=issue.message, role_id=issue.role_id, action=issue.action))
                if issue.code == 'POLICY_COVERAGE_GAP':
                    coverage_gaps.append(issue.message)
        except Exception as error:
            findings.append(ValidationFinding(severity='critical', code='PTAG_VALIDATION_ERROR', message=str(error), role_id=normalized.role_id if normalized else None))

        blocked_publish = (not syntax_passed) or (not semantic_passed) or any(item.severity == 'critical' for item in findings)
        return ValidationReport(
            report_id=f'vr_{uuid4().hex[:12]}',
            syntax_passed=syntax_passed,
            semantic_passed=semantic_passed,
            blocked_publish=blocked_publish,
            generated_at=utc_now(),
            findings=findings,
            coverage_gaps=coverage_gaps,
        )
