from datetime import datetime, timezone
from uuid import uuid4


_EXCEPTION_OUTCOMES = {'blocked', 'rejected', 'escalated', 'conflicted', 'out_of_order'}


def build_evidence_event_contract(
    *,
    active_role: str,
    action: str,
    outcome: str,
    reason: str,
    metadata: dict[str, object],
) -> dict[str, object]:
    decision_trace = _decision_trace(metadata)
    runtime_metadata = _runtime_metadata(metadata)
    runtime_evidence = _runtime_evidence(metadata)
    authority_gate = _authority_gate(metadata, runtime_metadata)
    state_flow = _state_flow(metadata, runtime_metadata)

    request_id = _request_id(runtime_evidence, metadata)
    policy_basis = _policy_basis(runtime_evidence, metadata)
    trace_source_type = _string_or_none(decision_trace.get('source_type'))
    trace_source_id = _string_or_none(decision_trace.get('source_id'))

    outcome_class = _outcome_class(outcome)
    requires_human_confirmation = _requires_human_confirmation(outcome, authority_gate)
    event_id = f'evt-{uuid4()}'

    exception_trace = _exception_trace(
        outcome=outcome,
        reason=reason,
        policy_basis=policy_basis,
        request_id=request_id,
        trace_source_type=trace_source_type,
        trace_source_id=trace_source_id,
        authority_gate=authority_gate,
        state_flow=state_flow,
        runtime_metadata=runtime_metadata,
    )

    return {
        'event_id': event_id,
        'contract_version': 'v0.2.2',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'event_kind': _event_kind(action=action, outcome=outcome, authority_gate=authority_gate, decision_trace=decision_trace),
        'outcome_class': outcome_class,
        'active_role': active_role,
        'action': action,
        'outcome': outcome,
        'reason': reason,
        'request_id': request_id,
        'policy_basis': policy_basis,
        'trace_source_type': trace_source_type,
        'trace_source_id': trace_source_id,
        'correlation': {
            'request_id': request_id,
            'event_id': event_id,
            'policy_basis': policy_basis,
            'trace_source': {
                'type': trace_source_type,
                'id': trace_source_id,
            },
        },
        'requires_human_confirmation': requires_human_confirmation,
        'has_exception_surface': outcome in {'waiting_human', 'human_required', 'escalated', 'rejected', 'blocked', 'conflicted', 'out_of_order'},
        'authority_gate': authority_gate,
        'runtime_state_flow': state_flow,
        'exception_trace': exception_trace,
    }


def _event_kind(
    *,
    action: str,
    outcome: str,
    authority_gate: dict[str, object] | None,
    decision_trace: dict[str, object],
) -> str:
    if action.startswith('override_'):
        return 'override'
    if outcome in _EXCEPTION_OUTCOMES:
        return 'exception'
    if authority_gate is not None and authority_gate.get('gate_triggered') is True:
        return 'authority_gate'
    if decision_trace:
        return 'decision'
    return 'action'


def _outcome_class(outcome: str) -> str:
    if outcome == 'approved' or outcome == 'completed':
        return 'success'
    if outcome in {'waiting_human', 'human_required'}:
        return 'human_boundary'
    if outcome == 'escalated':
        return 'escalated'
    if outcome in {'blocked', 'rejected', 'conflicted', 'out_of_order'}:
        return 'blocked'
    return 'exception'


def _exception_trace(
    *,
    outcome: str,
    reason: str,
    policy_basis: str | None,
    request_id: str | None,
    trace_source_type: str | None,
    trace_source_id: str | None,
    authority_gate: dict[str, object] | None,
    state_flow: dict[str, object] | None,
    runtime_metadata: dict[str, object],
) -> dict[str, object] | None:
    if outcome not in _EXCEPTION_OUTCOMES:
        return None

    runtime_reliability = runtime_metadata.get('runtime_reliability')
    reliability_snapshot = dict(runtime_reliability) if isinstance(runtime_reliability, dict) else None

    exception_kind = {
        'blocked': 'blocked',
        'rejected': 'rejected',
        'escalated': 'escalated',
        'conflicted': 'conflicted',
        'out_of_order': 'out_of_order',
    }.get(outcome, 'exception')

    return {
        'exception_kind': exception_kind,
        'outcome': outcome,
        'reason': reason,
        'policy_basis': policy_basis,
        'request_id': request_id,
        'trace_source': {
            'type': trace_source_type,
            'id': trace_source_id,
        },
        'authority_gate_triggered': bool(authority_gate.get('gate_triggered')) if isinstance(authority_gate, dict) else False,
        'runtime_state': state_flow.get('current_state') if isinstance(state_flow, dict) else None,
        'runtime_reliability': reliability_snapshot,
    }


def _decision_trace(metadata: dict[str, object]) -> dict[str, object]:
    trace = metadata.get('decision_trace')
    if isinstance(trace, dict):
        return trace
    return {}


def _runtime_metadata(metadata: dict[str, object]) -> dict[str, object]:
    context = metadata.get('context')
    if not isinstance(context, dict):
        return {}
    context_metadata = context.get('metadata')
    if not isinstance(context_metadata, dict):
        return {}
    return context_metadata


def _runtime_evidence(metadata: dict[str, object]) -> dict[str, object]:
    evidence = metadata.get('runtime_evidence')
    if isinstance(evidence, dict):
        return evidence
    return {}


def _authority_gate(metadata: dict[str, object], runtime_metadata: dict[str, object]) -> dict[str, object] | None:
    gate = runtime_metadata.get('authority_gate')
    if isinstance(gate, dict):
        return dict(gate)
    gate = metadata.get('authority_gate')
    if isinstance(gate, dict):
        return dict(gate)
    return None


def _state_flow(metadata: dict[str, object], runtime_metadata: dict[str, object]) -> dict[str, object] | None:
    state_flow = runtime_metadata.get('runtime_state_flow')
    if isinstance(state_flow, dict):
        return dict(state_flow)
    state_flow = metadata.get('runtime_state_flow')
    if isinstance(state_flow, dict):
        return dict(state_flow)
    return None


def _requires_human_confirmation(outcome: str, authority_gate: dict[str, object] | None) -> bool:
    if authority_gate is not None:
        raw = authority_gate.get('requires_human_confirmation')
        if isinstance(raw, bool):
            return raw
    return outcome in {'waiting_human', 'human_required'}


def _request_id(runtime_evidence: dict[str, object], metadata: dict[str, object]) -> str | None:
    request_id = runtime_evidence.get('request_id')
    if isinstance(request_id, str) and request_id:
        return request_id
    context = metadata.get('context')
    if isinstance(context, dict):
        raw = context.get('request_id')
        if isinstance(raw, str) and raw:
            return raw
    return None


def _policy_basis(runtime_evidence: dict[str, object], metadata: dict[str, object]) -> str | None:
    policy_basis = runtime_evidence.get('policy_basis')
    if isinstance(policy_basis, str) and policy_basis:
        return policy_basis
    raw = metadata.get('policy_basis')
    if isinstance(raw, str) and raw:
        return raw
    return None


def _string_or_none(value: object) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None
