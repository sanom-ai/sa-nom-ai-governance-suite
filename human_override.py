from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from config import AppConfig
from owner_identity import DEFAULT_EXECUTIVE_OWNER_ID
from execution_context import ExecutionContext
from persistence import build_state_store


@dataclass(slots=True)
class HumanOverrideState:
    request_id: str
    origin_request_id: str
    status: str
    approver_role: str
    action: str
    active_role: str
    required_by: str
    reason: str
    requester: str
    payload_snapshot: dict[str, object]
    context_metadata_snapshot: dict[str, object] = field(default_factory=dict)
    created_at: str = ""
    resolved_at: str | None = None
    resolved_by: str | None = None
    resolution_note: str | None = None
    execution_status: str | None = None
    execution_outcome: str | None = None
    execution_policy_basis: str | None = None
    execution_reason: str | None = None
    executed_at: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "HumanOverrideState":
        return cls(
            request_id=str(data["request_id"]),
            origin_request_id=str(data.get("origin_request_id") or f"legacy-{data['request_id']}"),
            status=str(data["status"]),
            approver_role=str(data["approver_role"]),
            action=str(data["action"]),
            active_role=str(data["active_role"]),
            required_by=str(data["required_by"]),
            reason=str(data["reason"]),
            requester=str(data["requester"]),
            payload_snapshot=data.get("payload_snapshot", {}),
            context_metadata_snapshot=data.get("context_metadata_snapshot", {}),
            created_at=str(data["created_at"]),
            resolved_at=data.get("resolved_at"),
            resolved_by=data.get("resolved_by"),
            resolution_note=data.get("resolution_note"),
            execution_status=data.get("execution_status"),
            execution_outcome=data.get("execution_outcome"),
            execution_policy_basis=data.get("execution_policy_basis"),
            execution_reason=data.get("execution_reason"),
            executed_at=data.get("executed_at"),
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class HumanOverrideGateway:
    def __init__(self, store_path=None, *, config: AppConfig | None = None) -> None:
        self.config = config
        self.store = build_state_store(config, store_path, logical_name="overrides")
        self.store_path = self.store.path
        self._requests: dict[str, HumanOverrideState] = {}
        self._load_existing()

    def requires_human(self, action: str) -> bool:
        guarded_actions = {"approve_group_policy", "emergency_stop", "suspend_role"}
        return action in guarded_actions

    def create_state(self, context: ExecutionContext, required_by: str, reason: str, approver_role: str | None = None) -> HumanOverrideState:
        state = HumanOverrideState(
            request_id=f"override-{uuid4()}",
            origin_request_id=context.request_id,
            status="pending",
            approver_role=approver_role or (
                self.config.executive_owner_id() if self.config is not None else DEFAULT_EXECUTIVE_OWNER_ID
            ),
            action=context.action,
            active_role=context.role_id,
            required_by=required_by,
            reason=reason,
            requester=context.requester,
            payload_snapshot=context.payload.copy(),
            context_metadata_snapshot=dict(context.metadata),
            created_at=self._utc_now(),
        )
        self._requests[state.request_id] = state
        self._persist()
        return state

    def list_requests(self, status: str | None = None) -> list[HumanOverrideState]:
        requests = list(self._requests.values())
        if status is None:
            return requests
        return [request for request in requests if request.status == status]

    def get_request(self, request_id: str) -> HumanOverrideState:
        if request_id not in self._requests:
            raise KeyError(f"Override request not found: {request_id}")
        return self._requests[request_id]

    def approve(self, request_id: str, resolved_by: str, note: str | None = None) -> HumanOverrideState:
        return self._resolve(request_id=request_id, status="approved", resolved_by=resolved_by, note=note)

    def veto(self, request_id: str, resolved_by: str, note: str | None = None) -> HumanOverrideState:
        return self._resolve(request_id=request_id, status="vetoed", resolved_by=resolved_by, note=note)

    def expire(self, request_id: str, note: str | None = None) -> HumanOverrideState:
        return self._resolve(request_id=request_id, status="expired", resolved_by="system", note=note)

    def record_execution(self, request_id: str, outcome: str, policy_basis: str, reason: str) -> HumanOverrideState:
        state = self.get_request(request_id)
        state.execution_status = "completed"
        state.execution_outcome = outcome
        state.execution_policy_basis = policy_basis
        state.execution_reason = reason
        state.executed_at = self._utc_now()
        self._persist()
        return state

    def _resolve(self, request_id: str, status: str, resolved_by: str, note: str | None) -> HumanOverrideState:
        state = self.get_request(request_id)
        if state.status != "pending":
            raise ValueError(f"Override request {request_id} is already resolved with status {state.status}")
        state.status = status
        state.resolved_at = self._utc_now()
        state.resolved_by = resolved_by
        state.resolution_note = note
        self._persist()
        return state

    def _persist(self) -> None:
        snapshot = [state.to_dict() for state in self._requests.values()]
        self.store.write(snapshot)

    def _load_existing(self) -> None:
        data = self.store.read(default=[])
        for item in data:
            state = HumanOverrideState.from_dict(item)
            self._requests[state.request_id] = state

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()
