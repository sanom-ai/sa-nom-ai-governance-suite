from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class EngineRequest:
    requester: str
    role_id: str | None
    action: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DecisionResult:
    requester: str
    action: str
    active_role: str
    outcome: str
    reason: str
    risk_score: float
    policy_basis: str | None = None
    decision_trace: dict[str, Any] = field(default_factory=dict)
    human_override: dict[str, Any] | None = None
    resource_lock: dict[str, Any] | None = None
    conflict_lock: dict[str, Any] | None = None
    role_transition: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class OverrideReviewResult:
    request_id: str
    status: str
    resolved_by: str | None = None
    resolution_note: str | None = None
    active_role: str | None = None
    action: str | None = None
    required_by: str | None = None
    execution_result: dict[str, Any] | None = None
