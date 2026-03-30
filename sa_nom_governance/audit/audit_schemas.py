from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class AuditEntry:
    timestamp: str
    active_role: str
    action: str
    outcome: str
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)
    entry_id: str | None = None
    sequence: int | None = None
    prev_hash: str | None = None
    entry_hash: str | None = None

    @classmethod
    def create(
        cls,
        active_role: str,
        action: str,
        outcome: str,
        reason: str,
        metadata: dict[str, Any],
        *,
        entry_id: str | None = None,
        sequence: int | None = None,
        prev_hash: str | None = None,
        entry_hash: str | None = None,
    ) -> "AuditEntry":
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            active_role=active_role,
            action=action,
            outcome=outcome,
            reason=reason,
            metadata=metadata,
            entry_id=entry_id,
            sequence=sequence,
            prev_hash=prev_hash,
            entry_hash=entry_hash,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuditEntry":
        return cls(
            timestamp=str(data["timestamp"]),
            active_role=str(data["active_role"]),
            action=str(data["action"]),
            outcome=str(data["outcome"]),
            reason=str(data["reason"]),
            metadata=data.get("metadata", {}),
            entry_id=str(data["entry_id"]) if data.get("entry_id") else None,
            sequence=int(data["sequence"]) if data.get("sequence") is not None else None,
            prev_hash=str(data["prev_hash"]) if data.get("prev_hash") else None,
            entry_hash=str(data["entry_hash"]) if data.get("entry_hash") else None,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
