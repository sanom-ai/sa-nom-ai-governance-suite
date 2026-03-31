from datetime import datetime, timezone
from uuid import uuid4


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

    outcome_class = _outcome_class(outcome)
    requires_human_confirmation = _requires_human_confirmation(outcome, authority_gate)

    return {
        'event_id': f'evt-{uuid4()}',
        'contract_version': 'v0.2.2',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'event_kind': _event_kind(action=action, outcome=outcome, authority_gate=authority_gate, decision_trace=decision_trace),
        'outcome_class': outcome_class,
        'active_role': active_role,
        'action': action,
        'outcome': outcome,
        'reason': reason,
        'request_id': _request_id(runtime_evidence, metadata),
        'trace_source_type': decision_trace.get('source_type'),
        'trace_source_id': decision_trace.get('source_id'),
        'requires_human_confirmation': requires_human_confirmation,
        'has_exception_surface': outcome in {'waiting_human', 'human_required', 'escalated', 'rejected', 'blocked'},
        'authority_gate': authority_gate,
        'runtime_state_flow': state_flow,
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
    if outcome in {'blocked', 'rejected', 'escalated', 'conflicted', 'out_of_order'}:
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
