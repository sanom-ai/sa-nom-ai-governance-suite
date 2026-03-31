from dataclasses import dataclass
from typing import Any

from sa_nom_governance.core.decision_models import DecisionComputation, DecisionTrace
from sa_nom_governance.core.execution_context import ExecutionContext
from sa_nom_governance.guards.human_override import HumanOverrideState
from sa_nom_governance.ptag.ptag_semantic import SemanticDocument


@dataclass(slots=True)
class PolicyEvaluation:
    applicable: bool
    matched: bool
    outcome: str | None = None
    matched_conditions: list[str] | None = None
    failed_conditions: list[str] | None = None


class DecisionEngine:
    """Evaluates PTAG constraints and policies for the flat dev runtime."""

    COMPARISON_OPERATORS = (">=", "<=", "==", "!=", ">", "<")

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
            evaluation = self._evaluate_policy(policy.body, context)
            if evaluation.outcome is not None:
                if evaluation.outcome == "waiting_human" and override_active:
                    return DecisionComputation(
                        outcome="approved",
                        reason=f"Action resumed after human override approval for policy {policy.policy_id}.",
                        policy_basis=policy.policy_id,
                        trace=DecisionTrace(
                            source_type="human_override_resume",
                            source_id=approved_override.request_id if approved_override else policy.policy_id,
                            matched_conditions=evaluation.matched_conditions or [],
                            failed_conditions=evaluation.failed_conditions or [],
                            notes=["Human override approval resumed execution.", f"Original policy source: {policy.policy_id}."],
                        ),
                        human_override=approved_override,
                    )
                return DecisionComputation(
                    outcome=evaluation.outcome,
                    reason=f"Decision resolved by policy {policy.policy_id}.",
                    policy_basis=policy.policy_id,
                    trace=DecisionTrace(
                        source_type="policy",
                        source_id=policy.policy_id,
                        matched_conditions=evaluation.matched_conditions or [],
                        failed_conditions=evaluation.failed_conditions or [],
                        notes=["Policy evaluation completed."],
                    ),
                )

        return DecisionComputation(
            outcome="escalated",
            reason="No matching PTAG policy found; request escalated by fail-closed default.",
            policy_basis=f"{context.role_id}.fail_closed",
            trace=DecisionTrace(
                source_type="default",
                source_id=f"{context.role_id}.fail_closed",
                notes=["No applicable policy produced a result.", "Fail-closed default applied."],
            ),
        )

    def _override_is_active(self, context: ExecutionContext, approved_override: HumanOverrideState | None) -> bool:
        if approved_override is None:
            return False
        return (
            approved_override.status == "approved"
            and approved_override.active_role == context.role_id
            and approved_override.action == context.action
        )

    def _evaluate_policy(self, lines: list[str], context: ExecutionContext) -> PolicyEvaluation:
        conditions: list[str] = []
        then_token: str | None = None
        else_token: str | None = None

        for line in lines:
            if line.startswith("when "):
                conditions.append(line.removeprefix("when ").strip())
            elif line.startswith("and "):
                conditions.append(line.removeprefix("and ").strip())
            elif line.startswith("then "):
                then_token = line.removeprefix("then ").strip()
            elif line.startswith("else "):
                else_token = line.removeprefix("else ").strip()

        if not conditions or then_token is None:
            return PolicyEvaluation(applicable=False, matched=False, outcome=None)

        action_conditions = [condition for condition in conditions if condition.startswith("action ")]
        non_action_conditions = [condition for condition in conditions if not condition.startswith("action ")]

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
            return PolicyEvaluation(
                applicable=True,
                matched=True,
                outcome=self._normalize_outcome(then_token),
                matched_conditions=matched_conditions,
                failed_conditions=failed_conditions,
            )

        if else_token is not None:
            return PolicyEvaluation(
                applicable=True,
                matched=False,
                outcome=self._normalize_outcome(else_token),
                matched_conditions=matched_conditions,
                failed_conditions=failed_conditions,
            )

        return PolicyEvaluation(
            applicable=True,
            matched=False,
            outcome=None,
            matched_conditions=matched_conditions,
            failed_conditions=failed_conditions,
        )

    def _evaluate_condition(self, condition: str, context: ExecutionContext) -> bool:
        for operator in self.COMPARISON_OPERATORS:
            if operator in condition:
                left, right = condition.split(operator, 1)
                actual = self._resolve_operand(left.strip(), context)
                expected = self._coerce_literal(right.strip())
                return self._compare(actual, expected, operator)
        return False

    def _resolve_operand(self, operand: str, context: ExecutionContext) -> Any | None:
        if operand == "action":
            return context.action
        if operand == "requester":
            return context.requester
        if operand == "risk_score":
            return context.risk_score
        if operand == "amount":
            return context.payload.get("amount")
        if operand == "resource":
            return context.payload.get("resource")
        if operand.startswith("payload."):
            key = operand.split(".", 1)[1]
            return context.payload.get(key)
        return None

    def _coerce_literal(self, value: str) -> Any:
        stripped = value.strip()
        if stripped.startswith('"') and stripped.endswith('"'):
            return stripped[1:-1]
        if stripped.lower() == "true":
            return True
        if stripped.lower() == "false":
            return False
        try:
            if "." in stripped:
                return float(stripped)
            return int(stripped)
        except ValueError:
            return stripped

    def _compare(self, actual: Any, expected: Any, operator: str) -> bool:
        if actual is None:
            return False
        if operator == "==":
            return bool(actual == expected)
        if operator == "!=":
            return bool(actual != expected)

        try:
            actual_num = float(actual)
            expected_num = float(expected)
        except (TypeError, ValueError):
            return False

        if operator == ">=":
            return actual_num >= expected_num
        if operator == "<=":
            return actual_num <= expected_num
        if operator == ">":
            return actual_num > expected_num
        if operator == "<":
            return actual_num < expected_num
        return False

    def _matches_forbid(self, line: str, action: str) -> bool:
        if not line.startswith("forbid "):
            return False
        return line.endswith(f"to {action}")

    def _matches_require(self, line: str, action: str) -> bool:
        if not line.startswith("require "):
            return False
        return line.endswith(f"for {action}")

    def _normalize_outcome(self, token: str) -> str:
        mapping = {
            "approve": "approved",
            "reject": "rejected",
            "wait_human": "waiting_human",
            "suspend": "suspended",
            "escalate": "escalated",
        }
        return mapping.get(token, token)
