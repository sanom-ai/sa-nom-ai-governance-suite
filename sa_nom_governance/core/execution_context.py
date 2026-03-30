from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ExecutionContext:
    request_id: str = ""
    requester: str = ""
    action: str = ""
    role_id: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    risk_score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    role_transition: dict[str, Any] = field(default_factory=dict)
