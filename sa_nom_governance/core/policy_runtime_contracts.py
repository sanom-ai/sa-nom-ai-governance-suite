from dataclasses import dataclass
from numbers import Real

from sa_nom_governance.core.decision_models import DecisionComputation, DecisionTrace
from sa_nom_governance.core.execution_context import ExecutionContext


@dataclass(slots=True)
class RuntimeContractViolation:
    code: str
    reason: str
    notes: list[str]


class RuntimeContractGuard:
    """Fail-closed contract checks for runtime context and decision output."""

    _ALLOWED_OUTCOMES = {
        'approved',
        'rejected',
        'waiting_human',
        'suspended',
        'escalated',
        'conflicted',
        'out_of_order',
    }

    def request_violation(
        self,
        *,
        requester: object,
        action: object,
        role_id: object,
        payload: object,
        metadata: object,
    ) -> RuntimeContractViolation | None:
        if not isinstance(requester, str) or not requester.strip():
            return RuntimeContractViolation(
                code='requester_invalid',
                reason='Runtime contract violation: requester must be a non-empty string.',
                notes=['Incoming requester is missing or invalid.'],
            )
        if not isinstance(action, str) or not action.strip():
            return RuntimeContractViolation(
                code='action_invalid',
                reason='Runtime contract violation: action must be a non-empty string.',
                notes=['Incoming action is missing or invalid.'],
            )
        if role_id is not None and (not isinstance(role_id, str) or (role_id != '' and not role_id.strip())):
            return RuntimeContractViolation(
                code='role_invalid',
                reason='Runtime contract violation: role_id must be a non-empty string when provided.',
                notes=['Incoming role_id is present but invalid.'],
            )
        if not isinstance(payload, dict):
            return RuntimeContractViolation(
                code='payload_invalid',
                reason='Runtime contract violation: payload must be an object map.',
                notes=['Incoming payload is not a dictionary.'],
            )
        if metadata is not None and not isinstance(metadata, dict):
            return RuntimeContractViolation(
                code='metadata_invalid',
                reason='Runtime contract violation: metadata must be an object map when provided.',
                notes=['Incoming metadata is present but not a dictionary.'],
            )
        return None
    def context_violation(self, context: ExecutionContext) -> RuntimeContractViolation | None:
        if not isinstance(context.requester, str) or not context.requester.strip():
            return RuntimeContractViolation(
                code='requester_invalid',
                reason='Runtime contract violation: requester must be a non-empty string.',
                notes=['Context requester is missing or invalid.'],
            )
        if not isinstance(context.action, str) or not context.action.strip():
            return RuntimeContractViolation(
                code='action_invalid',
                reason='Runtime contract violation: action must be a non-empty string.',
                notes=['Context action is missing or invalid.'],
            )
        if not isinstance(context.role_id, str) or not context.role_id.strip():
            return RuntimeContractViolation(
                code='role_invalid',
                reason='Runtime contract violation: role_id must be a non-empty string.',
                notes=['Context role_id is missing or invalid.'],
            )
        if not isinstance(context.payload, dict):
            return RuntimeContractViolation(
                code='payload_invalid',
                reason='Runtime contract violation: payload must be an object map.',
                notes=['Context payload is not a dictionary.'],
            )
        if not isinstance(context.metadata, dict):
            return RuntimeContractViolation(
                code='metadata_invalid',
                reason='Runtime contract violation: metadata must be an object map.',
                notes=['Context metadata is not a dictionary.'],
            )

        amount = context.payload.get('amount')
        if amount is not None:
            if not isinstance(amount, Real):
                return RuntimeContractViolation(
                    code='amount_type_invalid',
                    reason='Runtime contract violation: payload.amount must be numeric when present.',
                    notes=['payload.amount exists but is not numeric.'],
                )
            if float(amount) < 0:
                return RuntimeContractViolation(
                    code='amount_negative',
                    reason='Runtime contract violation: payload.amount cannot be negative.',
                    notes=['payload.amount is below zero.'],
                )

        return None

    def decision_violation(self, computation: DecisionComputation) -> RuntimeContractViolation | None:
        if computation.outcome not in self._ALLOWED_OUTCOMES:
            return RuntimeContractViolation(
                code='outcome_invalid',
                reason=f"Runtime contract violation: unsupported decision outcome '{computation.outcome}'.",
                notes=['Decision outcome is outside the allowed runtime set.'],
            )

        if not isinstance(computation.policy_basis, str) or not computation.policy_basis.strip():
            return RuntimeContractViolation(
                code='policy_basis_missing',
                reason='Runtime contract violation: policy_basis must be a non-empty string.',
                notes=['Decision policy basis is empty or invalid.'],
            )

        if not computation.trace.source_type or not computation.trace.source_id:
            return RuntimeContractViolation(
                code='trace_invalid',
                reason='Runtime contract violation: decision trace requires source_type and source_id.',
                notes=['Decision trace metadata is incomplete.'],
            )

        return None

    def to_computation(
        self,
        violation: RuntimeContractViolation,
        *,
        phase: str,
    ) -> DecisionComputation:
        return DecisionComputation(
            outcome='escalated',
            reason=violation.reason,
            policy_basis=f'runtime.contract.{phase}',
            trace=DecisionTrace(
                source_type='runtime_contract',
                source_id=violation.code,
                notes=list(violation.notes),
            ),
        )


