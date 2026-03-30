from __future__ import annotations

import difflib
from typing import Any

from role_private_studio_models import NormalizedRoleSpec, RoleDraftRevision, SimulationReport, StructuredJD, ValidationReport


FIELD_LABELS = {
    'role_name': 'Role name',
    'purpose': 'Purpose',
    'reporting_line': 'Reporting line',
    'business_domain': 'Business domain',
    'responsibilities': 'Responsibilities',
    'allowed_actions': 'Allowed actions',
    'forbidden_actions': 'Forbidden actions',
    'wait_human_actions': 'Wait-human actions',
    'handled_resources': 'Handled resources',
    'financial_sensitivity': 'Financial sensitivity',
    'legal_sensitivity': 'Legal sensitivity',
    'compliance_sensitivity': 'Compliance sensitivity',
    'sample_scenarios': 'Sample scenarios',
    'operator_notes': 'Operator notes',
    'attachments': 'Attachments',
}
LIST_FIELDS = {
    'responsibilities',
    'allowed_actions',
    'forbidden_actions',
    'wait_human_actions',
    'handled_resources',
    'sample_scenarios',
}


def build_revision_delta(
    previous_revision: RoleDraftRevision | None,
    current_structured_jd: StructuredJD,
    current_normalized_spec: NormalizedRoleSpec | None,
    current_ptag: str,
    validation_report: ValidationReport | None,
    simulation_report: SimulationReport | None,
) -> tuple[dict[str, Any], list[str]]:
    if previous_revision is None:
        diff_summary = {
            'structured_jd': {
                'changed': True,
                'changed_fields': sorted(current_structured_jd.to_dict().keys()),
                'details': {},
            },
            'ptag': _ptag_diff('', current_ptag),
            'validation': _validation_summary(validation_report),
            'simulation': _simulation_summary(simulation_report),
            'normalized_role_id': current_normalized_spec.role_id if current_normalized_spec else '',
        }
        return diff_summary, ['Initial draft generated.']

    previous_jd = previous_revision.structured_jd_snapshot
    structured_diff, change_summary = _structured_jd_diff(previous_jd, current_structured_jd)
    ptag_diff = _ptag_diff(previous_revision.generated_ptag, current_ptag)
    validation_delta, validation_messages = _validation_delta(previous_revision.validation_report, validation_report)
    simulation_delta, simulation_messages = _simulation_delta(previous_revision.simulation_report, simulation_report)

    if ptag_diff['changed']:
        change_summary.append(f"PTAG draft changed by +{ptag_diff['added_lines']} / -{ptag_diff['removed_lines']} lines.")
    change_summary.extend(validation_messages)
    change_summary.extend(simulation_messages)
    if not change_summary:
        change_summary.append('No effective change detected.')

    diff_summary = {
        'structured_jd': structured_diff,
        'ptag': ptag_diff,
        'validation': validation_delta,
        'simulation': simulation_delta,
        'normalized_role_id': current_normalized_spec.role_id if current_normalized_spec else '',
    }
    return diff_summary, change_summary[:12]


def _structured_jd_diff(previous_jd: StructuredJD, current_jd: StructuredJD) -> tuple[dict[str, Any], list[str]]:
    previous = previous_jd.to_dict()
    current = current_jd.to_dict()
    changed_fields: list[str] = []
    details: dict[str, Any] = {}
    summary: list[str] = []

    for field_name, current_value in current.items():
        previous_value = previous.get(field_name)
        if previous_value == current_value:
            continue
        changed_fields.append(field_name)
        label = FIELD_LABELS.get(field_name, field_name.replace('_', ' ').title())
        if field_name in LIST_FIELDS:
            previous_list = [str(item) for item in previous_value or []]
            current_list = [str(item) for item in current_value or []]
            added = [item for item in current_list if item not in previous_list]
            removed = [item for item in previous_list if item not in current_list]
            details[field_name] = {
                'kind': 'list',
                'added': added,
                'removed': removed,
                'previous_count': len(previous_list),
                'current_count': len(current_list),
            }
            summary.append(f'{label} +{len(added)} / -{len(removed)}.')
            continue

        details[field_name] = {
            'kind': 'value',
            'from': previous_value,
            'to': current_value,
        }
        summary.append(f'{label} updated.')

    return {
        'changed': bool(changed_fields),
        'changed_fields': changed_fields,
        'details': details,
    }, summary


def _ptag_diff(previous_text: str, current_text: str) -> dict[str, Any]:
    previous_lines = previous_text.splitlines()
    current_lines = current_text.splitlines()
    diff_lines = list(difflib.unified_diff(previous_lines, current_lines, fromfile='previous', tofile='current', lineterm=''))
    added_lines = [line[1:].strip() for line in diff_lines if line.startswith('+') and not line.startswith('+++')]
    removed_lines = [line[1:].strip() for line in diff_lines if line.startswith('-') and not line.startswith('---')]
    return {
        'changed': previous_text != current_text,
        'previous_line_count': len(previous_lines),
        'current_line_count': len(current_lines),
        'added_lines': len(added_lines),
        'removed_lines': len(removed_lines),
        'added_preview': [line for line in added_lines[:6] if line],
        'removed_preview': [line for line in removed_lines[:6] if line],
    }


def _validation_summary(report: ValidationReport | None) -> dict[str, Any]:
    return {
        'blocked_publish': report.blocked_publish if report else True,
        'critical_count': len(report.critical_findings) if report else 0,
        'warning_count': len(report.warning_findings) if report else 0,
        'coverage_gaps': report.coverage_gaps if report else [],
    }


def _simulation_summary(report: SimulationReport | None) -> dict[str, Any]:
    report_dict = report.to_dict() if report else {}
    return {
        'status': report.status if report else 'not_run',
        'scenario_count': report_dict.get('scenario_count', 0),
        'passed_count': report_dict.get('passed_count', 0),
        'failed_count': report_dict.get('failed_count', 0),
    }


def _validation_delta(previous_report: ValidationReport | None, current_report: ValidationReport | None) -> tuple[dict[str, Any], list[str]]:
    previous_summary = _validation_summary(previous_report)
    current_summary = _validation_summary(current_report)
    messages: list[str] = []

    if previous_report is not None and current_report is not None:
        if previous_report.blocked_publish and not current_report.blocked_publish:
            messages.append('Validation blockers cleared.')
        elif not previous_report.blocked_publish and current_report.blocked_publish:
            messages.append('Validation blockers introduced.')

    return {
        **current_summary,
        'changed': previous_summary != current_summary,
        'previous_blocked_publish': previous_summary['blocked_publish'],
    }, messages


def _simulation_delta(previous_report: SimulationReport | None, current_report: SimulationReport | None) -> tuple[dict[str, Any], list[str]]:
    previous_summary = _simulation_summary(previous_report)
    current_summary = _simulation_summary(current_report)
    messages: list[str] = []

    previous_status = previous_summary['status']
    current_status = current_summary['status']
    if previous_status != current_status:
        messages.append(f'Simulation status changed from {previous_status} to {current_status}.')

    return {
        **current_summary,
        'changed': previous_summary != current_summary,
        'previous_status': previous_status,
    }, messages
