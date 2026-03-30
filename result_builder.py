from dataclasses import asdict, is_dataclass

from api_schemas import DecisionResult
from decision_models import DecisionComputation
from execution_context import ExecutionContext


def build_result(
    context: ExecutionContext,
    computation: DecisionComputation,
    *,
    resource_lock: dict[str, object] | None = None,
    conflict_lock: dict[str, object] | None = None,
) -> DecisionResult:
    human_override = None
    if computation.human_override is not None:
        human_override = asdict(computation.human_override) if is_dataclass(computation.human_override) else computation.human_override

    return DecisionResult(
        requester=context.requester,
        action=context.action,
        active_role=context.role_id,
        outcome=computation.outcome,
        reason=computation.reason,
        risk_score=context.risk_score,
        policy_basis=computation.policy_basis,
        decision_trace=asdict(computation.trace),
        human_override=human_override,
        resource_lock=resource_lock,
        conflict_lock=conflict_lock,
        role_transition=dict(context.role_transition),
        metadata=asdict(context),
    )
