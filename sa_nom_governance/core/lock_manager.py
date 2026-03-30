from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from uuid import uuid4

from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.core.execution_context import ExecutionContext
from sa_nom_governance.utils.persistence import build_state_store


RESOURCE_ID_KEYS = ("resource_id", "target_id", "contract_id", "tenant_id", "entity_id", "record_id", "id")


@dataclass(slots=True)
class ResourceLockState:
    lock_id: str
    resource_key: str
    resource_type: str
    resource_id: str
    owner_request_id: str
    requester: str
    active_role: str
    action: str
    status: str
    created_at: str
    updated_at: str

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "ResourceLockState":
        return cls(
            lock_id=data["lock_id"],
            resource_key=data["resource_key"],
            resource_type=data["resource_type"],
            resource_id=data["resource_id"],
            owner_request_id=data["owner_request_id"],
            requester=data["requester"],
            active_role=data["active_role"],
            action=data["action"],
            status=data["status"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class ResourceConflictError(Exception):
    def __init__(self, requested_key: str, existing_lock: ResourceLockState) -> None:
        super().__init__(f"Resource lock conflict on {requested_key}")
        self.requested_key = requested_key
        self.existing_lock = existing_lock


class ResourceLockManager:
    def __init__(self, store_path=None, *, config: AppConfig | None = None) -> None:
        self.store = build_state_store(config, store_path, logical_name="locks")
        self.store_path = self.store.path
        self._locks: dict[str, ResourceLockState] = {}
        self._load_existing()

    def acquire(self, context: ExecutionContext) -> ResourceLockState | None:
        derived = self.derive_resource(context.payload)
        if derived is None:
            return None

        resource_key, resource_type, resource_id = derived
        existing = self._locks.get(resource_key)
        if existing is not None:
            if existing.owner_request_id == context.request_id:
                return existing
            raise ResourceConflictError(resource_key, existing)

        now = self._utc_now()
        state = ResourceLockState(
            lock_id=f"lock-{uuid4()}",
            resource_key=resource_key,
            resource_type=resource_type,
            resource_id=resource_id,
            owner_request_id=context.request_id,
            requester=context.requester,
            active_role=context.role_id,
            action=context.action,
            status="active",
            created_at=now,
            updated_at=now,
        )
        self._locks[resource_key] = state
        self._persist()
        return state

    def derive_resource(self, payload: dict[str, object]) -> tuple[str, str, str] | None:
        resource_type = payload.get("resource")
        if resource_type in (None, ""):
            return None

        resource_id = None
        for key in RESOURCE_ID_KEYS:
            value = payload.get(key)
            if value not in (None, ""):
                resource_id = str(value)
                break
        if resource_id is None:
            resource_id = "shared"

        resource_type_str = str(resource_type)
        return f"{resource_type_str}:{resource_id}", resource_type_str, resource_id

    def mark_waiting(self, request_id: str) -> ResourceLockState | None:
        state = self.get_by_request(request_id)
        if state is None:
            return None
        state.status = "waiting_human"
        state.updated_at = self._utc_now()
        self._persist()
        return state

    def mark_active(self, request_id: str) -> ResourceLockState | None:
        state = self.get_by_request(request_id)
        if state is None:
            return None
        state.status = "active"
        state.updated_at = self._utc_now()
        self._persist()
        return state

    def get_by_request(self, request_id: str) -> ResourceLockState | None:
        for state in self._locks.values():
            if state.owner_request_id == request_id:
                return state
        return None

    def list_locks(self, status: str | None = None) -> list[ResourceLockState]:
        locks = list(self._locks.values())
        if status is None:
            return locks
        return [lock for lock in locks if lock.status == status]

    def release_by_request(self, request_id: str) -> ResourceLockState | None:
        for resource_key, state in list(self._locks.items()):
            if state.owner_request_id == request_id:
                del self._locks[resource_key]
                self._persist()
                return state
        return None

    def _persist(self) -> None:
        snapshot = [state.to_dict() for state in self._locks.values()]
        self.store.write(snapshot)

    def _load_existing(self) -> None:
        data = self.store.read(default=[])
        for item in data:
            state = ResourceLockState.from_dict(item)
            self._locks[state.resource_key] = state

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()
