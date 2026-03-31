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
        'human_required',
        'retryable',
        'blocked',
        'suspended',
        'escalated',
        'conflicted',
        'out_of_order',
    }
    _POLICY_CONTRACT_KEYS = {
        'required_role',
        'allowed_roles',
        'allowed_actions',
        'required_payload_fields',
        'allowed_outcomes',
        'required_policy_basis_prefix',
        'required_trace_sources',
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
        if isinstance(metadata, dict):
            policy_contract_violation = self._policy_contract_shape_violation(metadata.get('policy_contract'))
            if policy_contract_violation is not None:
                return policy_contract_violation
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

        policy_contract = context.metadata.get('policy_contract')
        shape_violation = self._policy_contract_shape_violation(policy_contract)
        if shape_violation is not None:
            return shape_violation

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

        boundary_violation = self._policy_contract_context_boundary_violation(context, policy_contract)
        if boundary_violation is not None:
            return boundary_violation

        return None

    def decision_violation(
        self,
        computation: DecisionComputation,
        *,
        context: ExecutionContext | None = None,
    ) -> RuntimeContractViolation | None:
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

        policy_contract = context.metadata.get('policy_contract') if context is not None else None
        boundary_violation = self._policy_contract_decision_boundary_violation(computation, policy_contract)
        if boundary_violation is not None:
            return boundary_violation

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

    def _policy_contract_shape_violation(self, policy_contract: object) -> RuntimeContractViolation | None:
        if policy_contract is None:
            return None
        if not isinstance(policy_contract, dict):
            return RuntimeContractViolation(
                code='policy_contract_invalid_type',
                reason='Runtime contract violation: metadata.policy_contract must be an object map when provided.',
                notes=['metadata.policy_contract is present but not a dictionary.'],
            )
        unknown_keys = sorted(key for key in policy_contract if key not in self._POLICY_CONTRACT_KEYS)
        if unknown_keys:
            return RuntimeContractViolation(
                code='policy_contract_unknown_keys',
                reason='Runtime contract violation: metadata.policy_contract contains unsupported keys.',
                notes=[f"unsupported keys: {', '.join(unknown_keys)}"],
            )
        if 'required_role' in policy_contract:
            required_role = policy_contract['required_role']
            if not isinstance(required_role, str) or not required_role.strip():
                return RuntimeContractViolation(
                    code='policy_contract_required_role_invalid',
                    reason='Runtime contract violation: policy_contract.required_role must be a non-empty string.',
                    notes=['metadata.policy_contract.required_role is invalid.'],
                )
        if 'required_policy_basis_prefix' in policy_contract:
            prefix = policy_contract['required_policy_basis_prefix']
            if not isinstance(prefix, str) or not prefix.strip():
                return RuntimeContractViolation(
                    code='policy_contract_policy_prefix_invalid',
                    reason='Runtime contract violation: policy_contract.required_policy_basis_prefix must be a non-empty string.',
                    notes=['metadata.policy_contract.required_policy_basis_prefix is invalid.'],
                )
        for key in (
            'allowed_roles',
            'allowed_actions',
            'required_payload_fields',
            'allowed_outcomes',
            'required_trace_sources',
        ):
            if key in policy_contract and not self._string_list(policy_contract[key]):
                return RuntimeContractViolation(
                    code=f'policy_contract_{key}_invalid',
                    reason=f'Runtime contract violation: policy_contract.{key} must be a list of non-empty strings.',
                    notes=[f'metadata.policy_contract.{key} has invalid shape.'],
                )
        return None

    def _policy_contract_context_boundary_violation(
        self,
        context: ExecutionContext,
        policy_contract: object,
    ) -> RuntimeContractViolation | None:
        if not isinstance(policy_contract, dict):
            return None

        required_role = policy_contract.get('required_role')
        if isinstance(required_role, str) and context.role_id != required_role:
            return RuntimeContractViolation(
                code='policy_contract_required_role_mismatch',
                reason=f"Runtime contract violation: role_id '{context.role_id}' does not match required role '{required_role}'.",
                notes=['Request role is outside policy contract required_role boundary.'],
            )

        allowed_roles = policy_contract.get('allowed_roles')
        if isinstance(allowed_roles, list) and context.role_id not in allowed_roles:
            return RuntimeContractViolation(
                code='policy_contract_role_outside_allowlist',
                reason=f"Runtime contract violation: role_id '{context.role_id}' is outside policy contract allowed_roles.",
                notes=['Request role is outside allowed_roles boundary.'],
            )

        allowed_actions = policy_contract.get('allowed_actions')
        if isinstance(allowed_actions, list) and context.action not in allowed_actions:
            return RuntimeContractViolation(
                code='policy_contract_action_outside_allowlist',
                reason=f"Runtime contract violation: action '{context.action}' is outside policy contract allowed_actions.",
                notes=['Request action is outside allowed_actions boundary.'],
            )

        required_payload_fields = policy_contract.get('required_payload_fields')
        if isinstance(required_payload_fields, list):
            missing_fields = [field for field in required_payload_fields if field not in context.payload]
            if missing_fields:
                return RuntimeContractViolation(
                    code='policy_contract_missing_payload_fields',
                    reason='Runtime contract violation: required payload fields are missing for policy contract.',
                    notes=[f"missing fields: {', '.join(missing_fields)}"],
                )

        return None

    def _policy_contract_decision_boundary_violation(
        self,
        computation: DecisionComputation,
        policy_contract: object,
    ) -> RuntimeContractViolation | None:
        if not isinstance(policy_contract, dict):
            return None

        allowed_outcomes = policy_contract.get('allowed_outcomes')
        if isinstance(allowed_outcomes, list) and computation.outcome not in allowed_outcomes:
            return RuntimeContractViolation(
                code='policy_contract_outcome_outside_allowlist',
                reason=f"Runtime contract violation: outcome '{computation.outcome}' is outside policy contract allowed_outcomes.",
                notes=['Decision outcome is outside allowed_outcomes boundary.'],
            )

        required_prefix = policy_contract.get('required_policy_basis_prefix')
        if isinstance(required_prefix, str) and not computation.policy_basis.startswith(required_prefix):
            return RuntimeContractViolation(
                code='policy_contract_policy_basis_prefix_mismatch',
                reason='Runtime contract violation: decision policy_basis does not match required policy basis prefix.',
                notes=[f"required prefix: {required_prefix}", f"actual policy_basis: {computation.policy_basis}"],
            )

        required_trace_sources = policy_contract.get('required_trace_sources')
        if isinstance(required_trace_sources, list) and computation.trace.source_type not in required_trace_sources:
            return RuntimeContractViolation(
                code='policy_contract_trace_source_outside_allowlist',
                reason=f"Runtime contract violation: trace source_type '{computation.trace.source_type}' is outside policy contract required_trace_sources.",
                notes=['Decision trace source_type is outside required_trace_sources boundary.'],
            )

        return None

    def _string_list(self, value: object) -> bool:
        if not isinstance(value, list):
            return False
        return all(isinstance(item, str) and item.strip() for item in value)
