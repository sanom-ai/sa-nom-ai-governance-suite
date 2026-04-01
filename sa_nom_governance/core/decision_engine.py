from dataclasses import dataclass
from typing import Any

from sa_nom_governance.core.decision_models import DecisionComputation, DecisionTrace
from sa_nom_governance.core.execution_context import ExecutionContext
from sa_nom_governance.core.trigger_action_registry import TriggerActionRegistry
from sa_nom_governance.guards.human_override import HumanOverrideState
from sa_nom_governance.ptag.ptag_semantic import PolicyDefinition, SemanticDocument


@dataclass(slots=True)
class PolicyEvaluation:
    applicable: bool
    matched: bool
    outcome: str | None = None
    matched_conditions: list[str] | None = None
    failed_conditions: list[str] | None = None
    action_plan: dict[str, Any] | None = None


class DecisionEngine:
    """Evaluates PTAG constraints and policies for the flat dev runtime."""

    COMPARISON_OPERATORS = (">=", "<=", "==", "!=", ">", "<")

    def __init__(self, *, trigger_actions: TriggerActionRegistry | None = None) -> None:
        self.trigger_actions = trigger_actions or TriggerActionRegistry()

    def decide(
        self,
        context: ExecutionContext,
        role_document: SemanticDocument,
        approved_override: HumanOverrideState | None = None,
    ) -> DecisionComputation:
        override_active = self._override_is_active(context, approved_override)

        for constraint in role_document.constraints.values():
            for line in constraint.body:
                if self._matches_forbid(line, context.action):
                    return DecisionComputation(
                        outcome="rejected",
                        reason=f"Action blocked by constraint {constraint.constraint_id}.",
                        policy_basis=constraint.constraint_id,
                        trace=DecisionTrace(
                            source_type="constraint",
                            source_id=constraint.constraint_id,
                            matched_conditions=[line],
                            notes=["Constraint forbid rule applied."],
                        ),
                    )
                if self._matches_require(line, context.action):
                    if override_active:
                        continue
                    return DecisionComputation(
                        outcome="waiting_human",
                        reason=f"Action requires human override by constraint {constraint.constraint_id}.",
                        policy_basis=constraint.constraint_id,
                        trace=DecisionTrace(
                            source_type="constraint",
                            source_id=constraint.constraint_id,
                            matched_conditions=[line],
                            notes=["Constraint require rule applied."],
                        ),
                    )

        for policy in role_document.policies.values():
            evaluation = self._evaluate_policy(policy, context, override_active=override_active)
            if evaluation.action_plan is not None:
                context.metadata['ptag_trigger_runtime'] = dict(evaluation.action_plan)
            if evaluation.outcome is not None:
                if evaluation.outcome == 'waiting_human' and override_active:
                    resume_reason = f"Action resumed after human override approval for policy {policy.policy_id}."
                    if evaluation.action_plan is not None and evaluation.action_plan.get('requires_approval'):
                        resume_reason = f"Action resumed after trigger approval for policy {policy.policy_id}."
                    return DecisionComputation(
                        outcome='approved',
                        reason=resume_reason,
                        policy_basis=policy.policy_id,
                        trace=DecisionTrace(
                            source_type='human_override_resume',
                            source_id=approved_override.request_id if approved_override else policy.policy_id,
                            matched_conditions=evaluation.matched_conditions or [],
                            failed_conditions=evaluation.failed_conditions or [],
                            notes=[
                                'Human override approval resumed execution.',
                                f'Original policy source: {policy.policy_id}.',
                            ],
                        ),
                        human_override=approved_override,
                    )
                reason = f"Decision resolved by policy {policy.policy_id}."
                if evaluation.action_plan is not None:
                    branch = str(evaluation.action_plan.get('branch', '')).strip()
                    if branch:
                        reason = f"Decision resolved by policy {policy.policy_id} via {branch.upper()} branch."
                return DecisionComputation(
                    outcome=evaluation.outcome,
                    reason=reason,
                    policy_basis=policy.policy_id,
                    trace=DecisionTrace(
                        source_type='policy',
                        source_id=policy.policy_id,
                        matched_conditions=evaluation.matched_conditions or [],
                        failed_conditions=evaluation.failed_conditions or [],
                        notes=self.trigger_actions.build_policy_notes(evaluation.action_plan),
                    ),
                )

        return DecisionComputation(
            outcome='escalated',
            reason='No matching PTAG policy found; request escalated by fail-closed default.',
            policy_basis=f'{context.role_id}.fail_closed',
            trace=DecisionTrace(
                source_type='default',
                source_id=f'{context.role_id}.fail_closed',
                notes=['No applicable policy produced a result.', 'Fail-closed default applied.'],
            ),
        )

    def _override_is_active(self, context: ExecutionContext, approved_override: HumanOverrideState | None) -> bool:
        if approved_override is None:
            return False
        return (
            approved_override.status == 'approved'
            and approved_override.active_role == context.role_id
            and approved_override.action == context.action
        )

    def _evaluate_policy(
        self,
        policy: PolicyDefinition,
        context: ExecutionContext,
        *,
        override_active: bool,
    ) -> PolicyEvaluation:
        conditions = list(policy.conditions)
        if not conditions or not policy.then_actions:
            return PolicyEvaluation(applicable=False, matched=False, outcome=None)

        action_conditions = [condition for condition in conditions if condition.lower().startswith('action ')]
        non_action_conditions = [condition for condition in conditions if not condition.lower().startswith('action ')]

        matched_conditions: list[str] = []
        failed_conditions: list[str] = []

        for condition in action_conditions:
            if self._evaluate_condition(condition, context):
                matched_conditions.append(condition)
            else:
                failed_conditions.append(condition)

        if action_conditions and failed_conditions:
            return PolicyEvaluation(
                applicable=False,
                matched=False,
                outcome=None,
                matched_conditions=matched_conditions,
                failed_conditions=failed_conditions,
            )

        for condition in non_action_conditions:
            if self._evaluate_condition(condition, context):
                matched_conditions.append(condition)
            else:
                failed_conditions.append(condition)

        if not failed_conditions:
            action_plan = self.trigger_actions.build_action_plan(
                policy.policy_id,
                branch='then',
                action_tokens=policy.then_actions,
                override_active=override_active,
            )
            action_plan['matched_conditions'] = list(matched_conditions)
            action_plan['failed_conditions'] = list(failed_conditions)
            return PolicyEvaluation(
                applicable=True,
                matched=True,
                outcome=action_plan.get('terminal_outcome'),
                matched_conditions=matched_conditions,
                failed_conditions=failed_conditions,
                action_plan=action_plan,
            )

        if policy.else_actions:
            action_plan = self.trigger_actions.build_action_plan(
                policy.policy_id,
                branch='else',
                action_tokens=policy.else_actions,
                override_active=override_active,
            )
            action_plan['matched_conditions'] = list(matched_conditions)
            action_plan['failed_conditions'] = list(failed_conditions)
            return PolicyEvaluation(
                applicable=True,
                matched=False,
                outcome=action_plan.get('terminal_outcome'),
                matched_conditions=matched_conditions,
                failed_conditions=failed_conditions,
                action_plan=action_plan,
            )

        return PolicyEvaluation(
            applicable=True,
            matched=False,
            outcome=None,
            matched_conditions=matched_conditions,
            failed_conditions=failed_conditions,
        )

    def _evaluate_condition(self, condition: str, context: ExecutionContext) -> bool:
        membership = self._evaluate_membership_condition(condition, context)
        if membership is not None:
            return membership
        for operator in self.COMPARISON_OPERATORS:
            if operator in condition:
                left, right = condition.split(operator, 1)
                actual = self._resolve_operand(left.strip(), context)
                expected = self._coerce_literal(right.strip())
                return self._compare(actual, expected, operator)
        return False

    def _evaluate_membership_condition(self, condition: str, context: ExecutionContext) -> bool | None:
        marker = ' in '
        lower_condition = condition.lower()
        if marker not in lower_condition:
            return None
        index = lower_condition.find(marker)
        left = condition[:index].strip()
        right = condition[index + len(marker):].strip()
        if not (right.startswith('[') and right.endswith(']')):
            return None
        actual = self._resolve_operand(left, context)
        if actual is None:
            return False
        choices = [self._coerce_literal(item) for item in self._split_top_level_csv(right[1:-1].strip())]
        return actual in choices

    def _resolve_operand(self, operand: str, context: ExecutionContext) -> Any | None:
        if operand == 'action':
            return context.action
        if operand == 'requester':
            return context.requester
        if operand == 'risk_score':
            return context.risk_score
        if operand in {'region', 'audience', 'channel', 'sensitivity', 'tone', 'resonance_score'}:
            return self._resolve_context_signal(operand, context)
        if operand == 'amount':
            return context.payload.get('amount')
        if operand == 'resource':
            return context.payload.get('resource')
        if operand.startswith('payload.'):
            key = operand.split('.', 1)[1]
            return context.payload.get(key)
        if operand.startswith('metadata.'):
            key = operand.split('.', 1)[1]
            return self._resolve_nested_mapping(context.metadata, key)
        return None

    def _resolve_context_signal(self, operand: str, context: ExecutionContext) -> Any | None:
        direct_value = context.metadata.get(operand)
        if direct_value is not None:
            return direct_value

        harmony_payload = context.metadata.get('global_harmony')
        if isinstance(harmony_payload, dict):
            if operand == 'region':
                region_value = harmony_payload.get('region_id')
                if region_value is not None:
                    return region_value
            harmony_context = harmony_payload.get('context')
            if isinstance(harmony_context, dict):
                signal_value = harmony_context.get(operand)
                if signal_value is not None:
                    return signal_value

        runtime_payload = context.metadata.get('global_harmony_runtime')
        if isinstance(runtime_payload, dict):
            if operand == 'region':
                region_value = runtime_payload.get('region_id')
                if region_value is not None:
                    return region_value
            normalized_context = self._resolve_nested_mapping(runtime_payload, 'evaluation.normalized_context')
            if isinstance(normalized_context, dict):
                signal_value = normalized_context.get(operand)
                if signal_value is not None:
                    return signal_value
            if operand == 'resonance_score':
                resonance = self._resolve_nested_mapping(runtime_payload, 'evaluation.resonance_score')
                if resonance is not None:
                    return resonance
        return None

    def _resolve_nested_mapping(self, mapping: dict[str, Any], path: str) -> Any | None:
        current: Any = mapping
        for key in path.split('.'):
            if not isinstance(current, dict) or key not in current:
                return None
            current = current[key]
        return current

    def _coerce_literal(self, value: str) -> Any:
        stripped = value.strip()
        if stripped.startswith('"') and stripped.endswith('"'):
            return stripped[1:-1]
        if stripped.lower() == 'true':
            return True
        if stripped.lower() == 'false':
            return False
        try:
            if '.' in stripped:
                return float(stripped)
            return int(stripped)
        except ValueError:
            return stripped

    def _compare(self, actual: Any, expected: Any, operator: str) -> bool:
        if actual is None:
            return False
        if operator == '==':
            return bool(actual == expected)
        if operator == '!=':
            return bool(actual != expected)

        try:
            actual_num = float(actual)
            expected_num = float(expected)
        except (TypeError, ValueError):
            return False

        if operator == '>=':
            return actual_num >= expected_num
        if operator == '<=':
            return actual_num <= expected_num
        if operator == '>':
            return actual_num > expected_num
        if operator == '<':
            return actual_num < expected_num
        return False

    def _matches_forbid(self, line: str, action: str) -> bool:
        if not line.startswith('forbid '):
            return False
        return line.endswith(f'to {action}')

    def _matches_require(self, line: str, action: str) -> bool:
        if not line.startswith('require '):
            return False
        return line.endswith(f'for {action}')

    def _split_top_level_csv(self, value: str) -> list[str]:
        parts: list[str] = []
        current: list[str] = []
        quote_char: str | None = None
        depth = 0

        for char in value:
            if quote_char is not None:
                current.append(char)
                if char == quote_char:
                    quote_char = None
                continue

            if char in {'"', "'"}:
                quote_char = char
                current.append(char)
                continue

            if char in '([{':
                depth += 1
                current.append(char)
                continue

            if char in ')]}':
                depth = max(0, depth - 1)
                current.append(char)
                continue

            if char == ',' and depth == 0:
                part = ''.join(current).strip()
                if part:
                    parts.append(part)
                current = []
                continue

            current.append(char)

        part = ''.join(current).strip()
        if part:
            parts.append(part)
        return parts
