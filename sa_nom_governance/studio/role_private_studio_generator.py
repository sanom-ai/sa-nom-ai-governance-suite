import re

from sa_nom_governance.studio.role_private_studio_models import NormalizedRoleSpec, StructuredJD


HIGH_RISK_KEYWORDS = ('approve', 'sign', 'delete', 'emergency', 'override', 'terminate', 'suspend', 'stop')
SENSITIVITY_RANK = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
RISK_THRESHOLD = {1: 0.8, 2: 0.6, 3: 0.4, 4: 0.2}


class RolePrivateStudioGenerator:
    def __init__(self, *, owner_name: str = "Executive Owner", default_executive_owner_id: str = "EXEC_OWNER") -> None:
        self.owner_name = str(owner_name).strip() or "Executive Owner"
        self.default_executive_owner_id = str(default_executive_owner_id).strip().upper() or "EXEC_OWNER"

    def normalize(self, structured_jd: StructuredJD) -> NormalizedRoleSpec:
        allowed_actions = _clean_list(structured_jd.allowed_actions)
        forbidden_actions = _clean_list(structured_jd.forbidden_actions)
        explicit_wait_human = _clean_list(structured_jd.wait_human_actions)
        auto_wait_human = [action for action in allowed_actions if _is_high_risk_action(action) and action not in explicit_wait_human]
        wait_human_actions = _clean_list([*explicit_wait_human, *auto_wait_human])

        sensitivity_profile = {
            'financial': _normalize_sensitivity(structured_jd.financial_sensitivity),
            'legal': _normalize_sensitivity(structured_jd.legal_sensitivity),
            'compliance': _normalize_sensitivity(structured_jd.compliance_sensitivity),
        }
        max_rank = max(SENSITIVITY_RANK[value] for value in sensitivity_profile.values())
        role_id = _role_id(structured_jd.role_name)

        ambiguity_notes: list[str] = []
        if not structured_jd.reporting_line.strip():
            ambiguity_notes.append('Reporting line was missing and defaulted to GOV.')
        if not structured_jd.handled_resources:
            ambiguity_notes.append('Handled resources were not provided; generator will use general_resource safeguards.')
        operating_mode = str(structured_jd.operating_mode or 'direct').strip().lower()
        if operating_mode not in {'indirect', 'direct'}:
            operating_mode = 'direct'
            ambiguity_notes.append('Operating mode was invalid and defaulted to direct.')
        assigned_user_id = structured_jd.assigned_user_id.strip()
        executive_owner_id = structured_jd.executive_owner_id.strip() or self.default_executive_owner_id
        seat_id = structured_jd.seat_id.strip()
        if operating_mode == 'indirect' and not assigned_user_id:
            ambiguity_notes.append('Indirect mode was requested without an assigned user id.')
        if operating_mode == 'direct':
            assigned_user_id = ''

        risk_flags: list[str] = []
        if auto_wait_human:
            risk_flags.append(f'Auto safety upgrade applied to high-risk actions: {", ".join(auto_wait_human)}.')

        return NormalizedRoleSpec(
            role_id=role_id,
            title=structured_jd.role_name.strip() or role_id,
            purpose=structured_jd.purpose.strip(),
            reports_to=(structured_jd.reporting_line.strip() or 'GOV'),
            domain=structured_jd.business_domain.strip(),
            operating_mode=operating_mode,
            assigned_user_id=assigned_user_id,
            executive_owner_id=executive_owner_id,
            seat_id=seat_id,
            responsibilities=_clean_list(structured_jd.responsibilities),
            allowed_actions=allowed_actions,
            forbidden_actions=forbidden_actions,
            wait_human_actions=wait_human_actions,
            auto_wait_human_actions=auto_wait_human,
            handled_resources=_clean_list(structured_jd.handled_resources),
            sensitivity_profile=sensitivity_profile,
            risk_threshold=RISK_THRESHOLD[max_rank],
            ambiguity_notes=ambiguity_notes,
            risk_flags=risk_flags,
        )

    def generate(self, spec: NormalizedRoleSpec) -> str:
        default_resource = spec.handled_resources[0] if spec.handled_resources else 'general_resource'
        handled_resources = spec.handled_resources or ['general_resource']
        derived_stratum = 0 if spec.reports_to in {'NONE', self.default_executive_owner_id} else 1
        escalation_to = spec.reports_to if spec.reports_to not in {'NONE', ''} else spec.executive_owner_id
        safety_owner = spec.executive_owner_id if spec.operating_mode == 'direct' else (spec.reports_to or spec.executive_owner_id)
        handled_resource_block = ', '.join(handled_resources)
        lines: list[str] = [
            'language "PTAG"',
            f'module "{spec.role_id}_PRIVATE_STUDIO"',
            'version "1.0.0"',
            f'owner "{self.owner_name}"',
            'context "SA-NOM Role Private Studio"',
            '',
            f'role {spec.role_id} {{',
            f'  title: "{spec.title}"',
            f'  stratum: {derived_stratum}',
            f'  reports_to: {spec.reports_to}',
            f'  escalation_to: {escalation_to}',
            f'  safety_owner: {safety_owner}',
            f'  purpose: "{spec.purpose}"',
            f'  business_domain: "{spec.domain}"',
            f'  operating_mode: {spec.operating_mode}',
            f'  executive_owner_id: {spec.executive_owner_id}',
            *( [f'  assigned_user_id: {spec.assigned_user_id}'] if spec.operating_mode == 'indirect' and spec.assigned_user_id else [] ),
            *( [f'  seat_id: "{spec.seat_id}"'] if spec.seat_id else [] ),
            f'  handled_resources: [{handled_resource_block}]',
            '}',
            '',
            f'authority {spec.role_id} {{',
            f'  allow: {", ".join(spec.allowed_actions)}',
            f'  deny: {", ".join(spec.forbidden_actions)}',
        ]
        for action in spec.wait_human_actions:
            lines.append(f'  require human_override for {action}')
        lines.extend(['}', '', f'constraint {spec.role_id}_BOUNDARY {{'])
        for action in spec.forbidden_actions:
            lines.append(f'  forbid {spec.role_id} to {action}')
        for action in spec.wait_human_actions:
            lines.append(f'  require human_override for {action}')
        if not spec.forbidden_actions and not spec.wait_human_actions:
            lines.append(f'  forbid {spec.role_id} to bypass_ethics')
        lines.append('}')

        for action in spec.allowed_actions:
            policy_id = f'{spec.role_id}_{_policy_token(action)}'
            lines.extend(['', f'policy {policy_id} {{', f'  when action == {action}'])
            if action in spec.wait_human_actions:
                lines.append('  then wait_human')
                lines.append('}')
                continue
            lines.append(f'  and resource == {default_resource}')
            lines.append(f'  and risk_score <= {spec.risk_threshold:.2f}')
            lines.append('  then approve')
            lines.append('  else escalate')
            lines.append('}')
        return '\n'.join(lines) + '\n'


def _clean_list(values: list[str]) -> list[str]:
    seen: set[str] = set()
    items: list[str] = []
    for raw in values:
        token = re.sub(r'[^a-zA-Z0-9_]+', '_', str(raw).strip()).strip('_').lower()
        if not token or token in seen:
            continue
        seen.add(token)
        items.append(token)
    return items


def _normalize_sensitivity(value: str) -> str:
    token = str(value or 'medium').strip().lower()
    return token if token in SENSITIVITY_RANK else 'medium'


def _is_high_risk_action(action: str) -> bool:
    lowered = action.lower()
    return any(keyword in lowered for keyword in HIGH_RISK_KEYWORDS)


def _role_id(role_name: str) -> str:
    token = re.sub(r'[^A-Za-z0-9]+', '_', role_name.strip().upper()).strip('_')
    return token or 'NEW_ROLE'


def _policy_token(action: str) -> str:
    return re.sub(r'[^A-Za-z0-9]+', '_', action.strip().upper()).strip('_') or 'POLICY'
