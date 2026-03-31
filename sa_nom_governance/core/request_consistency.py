import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from sa_nom_governance.api.api_schemas import DecisionResult
from sa_nom_governance.core.execution_context import ExecutionContext
from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.utils.persistence import build_state_store


@dataclass(slots=True)
class IdempotencyRecord:
    key: str
    fingerprint: str
    request_id: str
    status: str
    created_at: str
    updated_at: str
    result: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IdempotencyRecord":
        return cls(
            key=str(data["key"]),
            fingerprint=str(data["fingerprint"]),
            request_id=str(data["request_id"]),
            status=str(data["status"]),
            created_at=str(data["created_at"]),
            updated_at=str(data["updated_at"]),
            result=data.get("result"),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EventStreamState:
    stream_key: str
    latest_sequence: int
    latest_request_id: str
    latest_processed_at: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EventStreamState":
        return cls(
            stream_key=str(data["stream_key"]),
            latest_sequence=int(data["latest_sequence"]),
            latest_request_id=str(data["latest_request_id"]),
            latest_processed_at=str(data["latest_processed_at"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class IdempotencyReplay(Exception):
    def __init__(self, result: DecisionResult, audit_metadata: dict[str, Any]) -> None:
        super().__init__("Request replayed from idempotency store.")
        self.result = result
        self.audit_metadata = audit_metadata


class RequestConsistencyError(Exception):
    def __init__(
        self,
        *,
        outcome: str,
        reason: str,
        policy_basis: str,
        source_type: str,
        source_id: str,
        notes: list[str],
        consistency_status: str,
    ) -> None:
        super().__init__(reason)
        self.outcome = outcome
        self.reason = reason
        self.policy_basis = policy_basis
        self.source_type = source_type
        self.source_id = source_id
        self.notes = notes
        self.consistency_status = consistency_status


class RequestConsistencyManager:
    def __init__(self, store_path=None, *, config: AppConfig | None = None) -> None:
        self.store = build_state_store(config, store_path, logical_name="request_consistency")
        self.store_path = self.store.path
        self._idempotency_records: dict[str, IdempotencyRecord] = {}
        self._event_streams: dict[str, EventStreamState] = {}
        self._load_existing()

    def prepare(self, context: ExecutionContext) -> None:
        metadata = context.metadata.setdefault("request_consistency", {})
        metadata.setdefault("idempotency_status", "none")
        metadata.setdefault("ordering_status", "none")

        key = self._idempotency_key(context)
        event_stream = self._event_stream(context)
        try:
            event_sequence = self._event_sequence(context)
        except ValueError as error:
            metadata["ordering_status"] = "invalid"
            raise RequestConsistencyError(
                outcome="rejected",
                reason="Event sequence must be an integer when event ordering is provided.",
                policy_basis="runtime.event_order",
                source_type="runtime_event_order",
                source_id=event_stream or "unknown_stream",
                notes=["The request metadata contains a non-integer event sequence value.", str(error)],
                consistency_status="invalid",
            ) from error
        fingerprint = self._fingerprint(context) if key else None

        if key:
            metadata["idempotency_key"] = key
            metadata["request_fingerprint"] = fingerprint
            existing = self._idempotency_records.get(key)
            if existing is not None:
                if existing.fingerprint != fingerprint:
                    metadata["idempotency_status"] = "conflict"
                    raise RequestConsistencyError(
                        outcome="rejected",
                        reason=f"Idempotency key {key} was already used for a different request fingerprint.",
                        policy_basis="runtime.idempotency",
                        source_type="runtime_idempotency",
                        source_id=key,
                        notes=[
                            "Incoming request fingerprint does not match the stored idempotent request.",
                            f"Original request id: {existing.request_id}.",
                        ],
                        consistency_status="conflict",
                    )
                if existing.status == "completed" and existing.result is not None:
                    metadata["idempotency_status"] = "replayed"
                    metadata["original_request_id"] = existing.request_id
                    raise IdempotencyReplay(
                        result=self._build_replayed_result(context, existing),
                        audit_metadata={
                            "replay_request_id": context.request_id,
                            "original_request_id": existing.request_id,
                            "idempotency_key": key,
                            "event_stream": event_stream,
                            "event_sequence": event_sequence,
                        },
                    )
                metadata["idempotency_status"] = "pending_conflict"
                raise RequestConsistencyError(
                    outcome="rejected",
                    reason=f"Idempotency key {key} is already reserved by an in-progress request.",
                    policy_basis="runtime.idempotency",
                    source_type="runtime_idempotency",
                    source_id=key,
                    notes=[
                        "An earlier request with the same idempotency key is still pending.",
                        f"In-progress request id: {existing.request_id}.",
                    ],
                    consistency_status="pending_conflict",
                )

        if event_stream is not None:
            metadata["event_stream"] = event_stream
        if event_sequence is not None:
            metadata["event_sequence"] = event_sequence

        if event_stream is not None and event_sequence is not None:
            stream_state = self._event_streams.get(event_stream)
            if stream_state is not None:
                metadata["last_seen_sequence"] = stream_state.latest_sequence
                if event_sequence <= stream_state.latest_sequence:
                    metadata["ordering_status"] = "stale"
                    raise RequestConsistencyError(
                        outcome="out_of_order",
                        reason=f"Event sequence {event_sequence} is stale for stream {event_stream}; latest processed sequence is {stream_state.latest_sequence}.",
                        policy_basis="runtime.event_order",
                        source_type="runtime_event_order",
                        source_id=event_stream,
                        notes=[
                            "Incoming event sequence is not newer than the latest processed sequence.",
                            f"Latest processed request id: {stream_state.latest_request_id}.",
                        ],
                        consistency_status="stale",
                    )
                if event_sequence > stream_state.latest_sequence + 1:
                    metadata["ordering_status"] = "gap"
                    raise RequestConsistencyError(
                        outcome="out_of_order",
                        reason=f"Event sequence gap detected for stream {event_stream}; expected at most {stream_state.latest_sequence + 1} but received {event_sequence}.",
                        policy_basis="runtime.event_order",
                        source_type="runtime_event_order",
                        source_id=event_stream,
                        notes=[
                            "The event stream has a sequence gap and cannot be processed safely.",
                            f"Latest processed request id: {stream_state.latest_request_id}.",
                        ],
                        consistency_status="gap",
                    )
            metadata["ordering_status"] = "accepted"

        if key:
            self._idempotency_records[key] = IdempotencyRecord(
                key=key,
                fingerprint=str(fingerprint),
                request_id=context.request_id,
                status="pending",
                created_at=self._utc_now(),
                updated_at=self._utc_now(),
            )
            metadata["idempotency_status"] = "accepted"
            self._persist()

    def complete(self, context: ExecutionContext, result: DecisionResult) -> None:
        metadata = context.metadata.get("request_consistency", {})
        key = metadata.get("idempotency_key")
        if isinstance(key, str) and key in self._idempotency_records:
            record = self._idempotency_records[key]
            record.status = "completed"
            record.updated_at = self._utc_now()
            record.result = asdict(result)

        event_stream = metadata.get("event_stream")
        event_sequence = metadata.get("event_sequence")
        ordering_status = metadata.get("ordering_status")
        if isinstance(event_stream, str) and isinstance(event_sequence, int) and ordering_status == "accepted":
            self._event_streams[event_stream] = EventStreamState(
                stream_key=event_stream,
                latest_sequence=event_sequence,
                latest_request_id=context.request_id,
                latest_processed_at=self._utc_now(),
            )

        self._persist()

    def abort(self, context: ExecutionContext) -> None:
        metadata = context.metadata.get("request_consistency", {})
        key = metadata.get("idempotency_key")
        if not isinstance(key, str):
            return
        record = self._idempotency_records.get(key)
        if record is None:
            return
        if record.status == "pending" and record.request_id == context.request_id:
            del self._idempotency_records[key]
            self._persist()

    def health(self) -> dict[str, Any]:
        completed = sum(1 for record in self._idempotency_records.values() if record.status == "completed")
        pending = sum(1 for record in self._idempotency_records.values() if record.status == "pending")
        return {
            "idempotency_records": len(self._idempotency_records),
            "completed_records": completed,
            "pending_records": pending,
            "event_streams": len(self._event_streams),
            "persistence_backend": self.store.descriptor().backend,
        }

    def _build_replayed_result(self, context: ExecutionContext, record: IdempotencyRecord) -> DecisionResult:
        result_dict = json.loads(json.dumps(record.result))
        context_payload = result_dict.setdefault("metadata", {})
        context_metadata = context_payload.setdefault("metadata", {})
        request_consistency = context_metadata.setdefault("request_consistency", {})
        request_consistency["idempotency_status"] = "replayed"
        request_consistency["idempotency_key"] = record.key
        request_consistency["original_request_id"] = record.request_id
        request_consistency["replay_request_id"] = context.request_id
        request_consistency["replayed_at"] = self._utc_now()

        trace = result_dict.setdefault("decision_trace", {})
        notes = trace.setdefault("notes", [])
        notes.append("Result served from idempotency replay store.")
        return DecisionResult(**result_dict)

    def _idempotency_key(self, context: ExecutionContext) -> str | None:
        value = context.metadata.get("idempotency_key")
        if value in (None, ""):
            return None
        return str(value)

    def _event_stream(self, context: ExecutionContext) -> str | None:
        value = context.metadata.get("event_stream")
        if value in (None, ""):
            return None
        return str(value)

    def _event_sequence(self, context: ExecutionContext) -> int | None:
        value = context.metadata.get("event_sequence")
        if value in (None, ""):
            return None
        return int(value)

    def _fingerprint(self, context: ExecutionContext) -> str:
        payload = {
            "requester": context.requester,
            "role_id": context.role_id,
            "action": context.action,
            "payload": context.payload,
            "event_stream": self._event_stream(context),
            "event_sequence": self._event_sequence(context),
        }
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def _persist(self) -> None:
        snapshot = {
            "generated_at": self._utc_now(),
            "idempotency_records": {key: record.to_dict() for key, record in self._idempotency_records.items()},
            "event_streams": {key: state.to_dict() for key, state in self._event_streams.items()},
        }
        self.store.write(snapshot)

    def _load_existing(self) -> None:
        snapshot = self.store.read(default={})
        for key, item in snapshot.get("idempotency_records", {}).items():
            self._idempotency_records[key] = IdempotencyRecord.from_dict(item)
        for key, item in snapshot.get("event_streams", {}).items():
            self._event_streams[key] = EventStreamState.from_dict(item)

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()
