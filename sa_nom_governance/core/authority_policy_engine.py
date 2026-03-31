from dataclasses import dataclass
from numbers import Real

from sa_nom_governance.core.decision_models import DecisionComputation, DecisionTrace
from sa_nom_governance.core.execution_context import ExecutionContext


@dataclass(slots=True)
class AuthorityContractViolation:
    code: str
    reason: str
    notes: list[str]


class AuthorityPolicyEngine:
    """Evaluates machine-readable authority contracts from request metadata."""

    _VALID_APPROVAL_GATES = {'ai_allowed', 'human_required', 'blocked'}

    def contract_violation(self, context: ExecutionContext) -> AuthorityContractViolation | None:
        contract = context.metadata.get('authority_contract')
        if contract is None:
            return None
        if not isinstance(contract, dict):
            return AuthorityContractViolation(
                code='authority_contract_invalid_type',
                reason='Authority contract must be an object map when provided.',
                notes=['metadata.authority_contract is not a dictionary.'],
            )

        approval_gate = contract.get('approval_gate')
        if approval_gate is not None and approval_gate not in self._VALID_APPROVAL_GATES:
            return AuthorityContractViolation(
                code='authority_contract_invalid_gate',
                reason=f"Unsupported authority approval gate '{approval_gate}'.",
                notes=['approval_gate must be ai_allowed, human_required, or blocked.'],
            )

        for key in ('allow_actions', 'block_actions', 'require_human_actions'):
            if key in contract and not self._string_list(contract[key]):
                return AuthorityContractViolation(
                    code=f'authority_contract_invalid_{key}',
                    reason=f'Authority contract field {key} must be a list of strings when provided.',
                    notes=[f'metadata.authority_contract.{key} has invalid shape.'],
                )

        if 'max_risk_score' in contract:
            max_risk_score = contract['max_risk_score']
            if not isinstance(max_risk_score, Real):
                return AuthorityContractViolation(
                    code='authority_contract_invalid_max_risk_score',
                    reason='Authority contract max_risk_score must be numeric when provided.',
                    notes=['metadata.authority_contract.max_risk_score is not numeric.'],
                )

        return None

    def evaluate(self, context: ExecutionContext) -> DecisionComputation | None:
        contract = context.metadata.get('authority_contract')
        if not isinstance(contract, dict):
            return None

        decision = self._evaluate_gate(context, contract)
        if decision is not None:
            return decision

        if self._matches_action(contract.get('block_actions'), context.action):
            return self._blocked(context, source='block_actions', reason='Action blocked by authority contract.')

        if self._matches_action(contract.get('require_human_actions'), context.action):
            return self._human_required(context, source='require_human_actions', reason='Action requires human approval by authority contract.')

        if self._has_allow_actions(contract) and not self._matches_action(contract.get('allow_actions'), context.action):
            return self._blocked(context, source='allow_actions', reason='Action is outside authority contract allow_actions.')

        max_risk_score = contract.get('max_risk_score')
        if isinstance(max_risk_score, Real) and context.risk_score > float(max_risk_score):
            return self._human_required(
                context,
                source='max_risk_score',
                reason=f"Risk score {context.risk_score:.4f} exceeds authority contract max_risk_score {float(max_risk_score):.4f}.",
            )

        return None

    def to_computation(self, violation: AuthorityContractViolation) -> DecisionComputation:
        return DecisionComputation(
            outcome='blocked',
            reason=violation.reason,
            policy_basis='runtime.authority_contract',
            trace=DecisionTrace(
                source_type='authority_contract',
                source_id=violation.code,
                notes=list(violation.notes),
            ),
        )

    def _evaluate_gate(self, context: ExecutionContext, contract: dict[str, object]) -> DecisionComputation | None:
        approval_gate = contract.get('approval_gate')
        if approval_gate == 'blocked':
            return self._blocked(
                context,
                source='approval_gate',
                reason='Request blocked by authority approval gate.',
            )
        if approval_gate == 'human_required':
            return self._human_required(
                context,
                source='approval_gate',
                reason='Request paused for human approval by authority gate.',
            )
        return None

    def _blocked(self, context: ExecutionContext, *, source: str, reason: str) -> DecisionComputation:
        return DecisionComputation(
            outcome='blocked',
            reason=reason,
            policy_basis='runtime.authority_contract',
            trace=DecisionTrace(
                source_type='authority_contract',
                source_id=source,
                notes=[f'role={context.role_id}', f'action={context.action}'],
            ),
        )

    def _human_required(self, context: ExecutionContext, *, source: str, reason: str) -> DecisionComputation:
        return DecisionComputation(
            outcome='human_required',
            reason=reason,
            policy_basis='runtime.authority_contract',
            trace=DecisionTrace(
                source_type='authority_contract',
                source_id=source,
                notes=[f'role={context.role_id}', f'action={context.action}'],
            ),
        )

    def _has_allow_actions(self, contract: dict[str, object]) -> bool:
        allow_actions = contract.get('allow_actions')
        return isinstance(allow_actions, list) and len(allow_actions) > 0

    def _matches_action(self, actions: object, action: str) -> bool:
        if not isinstance(actions, list):
            return False
        normalized = [item for item in actions if isinstance(item, str)]
        return action in normalized

    def _string_list(self, value: object) -> bool:
        if not isinstance(value, list):
            return False
        return all(isinstance(item, str) and item.strip() for item in value)
