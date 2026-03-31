from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sa_nom_governance.core.execution_context import ExecutionContext
from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.utils.persistence import build_line_ledger, build_state_store


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class RecoveryRecord:
    request_id: str
    requester: str
    action: str
    role_id: str
    payload: dict[str, Any]
    metadata: dict[str, Any]
    outcome: str
    policy_basis: str
    reason: str
    status: str
    failure_classification: str
    attempts_used: int
    max_attempts: int
    created_at: str
    updated_at: str
    resumed_by: str | None = None
    resumed_at: str | None = None
    resumed_request_id: str | None = None
    resumed_outcome: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            'request_id': self.request_id,
            'requester': self.requester,
            'action': self.action,
            'role_id': self.role_id,
            'payload': dict(self.payload),
            'metadata': dict(self.metadata),
            'outcome': self.outcome,
            'policy_basis': self.policy_basis,
            'reason': self.reason,
            'status': self.status,
            'failure_classification': self.failure_classification,
            'attempts_used': self.attempts_used,
            'max_attempts': self.max_attempts,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'resumed_by': self.resumed_by,
            'resumed_at': self.resumed_at,
            'resumed_request_id': self.resumed_request_id,
            'resumed_outcome': self.resumed_outcome,
        }


class RuntimeRecoveryStore:
    def __init__(self, config: AppConfig | None, store_path, dead_letter_path) -> None:
        self.store = build_state_store(config, store_path, logical_name='runtime_recovery')
        self.dead_letter_ledger = build_line_ledger(config, dead_letter_path, logical_name='runtime_dead_letter')
        self.records: dict[str, RecoveryRecord] = {}
        self._load()

    def save_failure(
        self,
        context: ExecutionContext,
        *,
        outcome: str,
        policy_basis: str,
        reason: str,
        attempts_used: int,
        max_attempts: int,
        failure_classification: str,
    ) -> RecoveryRecord:
        now = utc_now()
        previous = self.records.get(context.request_id)
        created_at = previous.created_at if previous is not None else now
        record = RecoveryRecord(
            request_id=context.request_id,
            requester=context.requester,
            action=context.action,
            role_id=context.role_id,
            payload=dict(context.payload),
            metadata=dict(context.metadata),
            outcome=outcome,
            policy_basis=policy_basis,
            reason=reason,
            status='dead_letter',
            failure_classification=failure_classification,
            attempts_used=attempts_used,
            max_attempts=max_attempts,
            created_at=created_at,
            updated_at=now,
            resumed_by=previous.resumed_by if previous is not None else None,
            resumed_at=previous.resumed_at if previous is not None else None,
            resumed_request_id=previous.resumed_request_id if previous is not None else None,
            resumed_outcome=previous.resumed_outcome if previous is not None else None,
        )
        self.records[record.request_id] = record
        self.dead_letter_ledger.append(
            {
                'request_id': record.request_id,
                'requester': record.requester,
                'action': record.action,
                'role_id': record.role_id,
                'outcome': record.outcome,
                'policy_basis': record.policy_basis,
                'reason': record.reason,
                'failure_classification': record.failure_classification,
                'attempts_used': record.attempts_used,
                'max_attempts': record.max_attempts,
                'status': record.status,
                'captured_at': now,
            }
        )
        self._save()
        return record

    def mark_resumed(
        self,
        request_id: str,
        *,
        resumed_by: str,
        resumed_request_id: str,
        resumed_outcome: str,
    ) -> RecoveryRecord:
        if request_id not in self.records:
            raise KeyError(f'Recovery record not found: {request_id}')
        record = self.records[request_id]
        record.status = 'resumed'
        record.resumed_by = resumed_by
        record.resumed_at = utc_now()
        record.resumed_request_id = resumed_request_id
        record.resumed_outcome = resumed_outcome
        record.updated_at = record.resumed_at
        self._save()
        return record

    def get_record(self, request_id: str) -> RecoveryRecord:
        if request_id not in self.records:
            raise KeyError(f'Recovery record not found: {request_id}')
        return self.records[request_id]

    def list_records(self, *, status: str | None = None, limit: int | None = None) -> list[dict[str, Any]]:
        items = sorted(self.records.values(), key=lambda item: item.updated_at, reverse=True)
        if status is not None:
            items = [item for item in items if item.status == status]
        if limit is not None:
            items = items[: max(0, limit)]
        return [item.to_dict() for item in items]

    def list_dead_letters(self, *, limit: int | None = None) -> list[dict[str, Any]]:
        records = self.dead_letter_ledger.read_records()
        if limit is None:
            return records
        return records[-max(0, limit) :]

    def summary(self) -> dict[str, Any]:
        status_counts: dict[str, int] = {}
        for item in self.records.values():
            status_counts[item.status] = status_counts.get(item.status, 0) + 1
        return {
            'total_records': len(self.records),
            'status_counts': dict(sorted(status_counts.items())),
            'store': self.store.descriptor().to_dict(),
            'dead_letter_store': self.dead_letter_ledger.descriptor().to_dict(),
            'dead_letter_total': len(self.dead_letter_ledger.read_records()),
        }

    def _load(self) -> None:
        data = self.store.read(default={})
        records = data.get('records', {})
        loaded: dict[str, RecoveryRecord] = {}
        if isinstance(records, dict):
            for request_id, raw in records.items():
                if not isinstance(raw, dict):
                    continue
                loaded[str(request_id)] = RecoveryRecord(
                    request_id=str(raw.get('request_id', request_id)),
                    requester=str(raw.get('requester', '')),
                    action=str(raw.get('action', '')),
                    role_id=str(raw.get('role_id', '')),
                    payload=dict(raw.get('payload', {})) if isinstance(raw.get('payload'), dict) else {},
                    metadata=dict(raw.get('metadata', {})) if isinstance(raw.get('metadata'), dict) else {},
                    outcome=str(raw.get('outcome', '')),
                    policy_basis=str(raw.get('policy_basis', '')),
                    reason=str(raw.get('reason', '')),
                    status=str(raw.get('status', 'dead_letter')),
                    failure_classification=str(raw.get('failure_classification', 'runtime_failure')),
                    attempts_used=int(raw.get('attempts_used', 1)),
                    max_attempts=int(raw.get('max_attempts', 1)),
                    created_at=str(raw.get('created_at', utc_now())),
                    updated_at=str(raw.get('updated_at', utc_now())),
                    resumed_by=str(raw['resumed_by']) if raw.get('resumed_by') is not None else None,
                    resumed_at=str(raw['resumed_at']) if raw.get('resumed_at') is not None else None,
                    resumed_request_id=(
                        str(raw['resumed_request_id']) if raw.get('resumed_request_id') is not None else None
                    ),
                    resumed_outcome=str(raw['resumed_outcome']) if raw.get('resumed_outcome') is not None else None,
                )
        self.records = loaded

    def _save(self) -> None:
        self.store.write(
            {
                'records': {request_id: record.to_dict() for request_id, record in sorted(self.records.items())},
                'updated_at': utc_now(),
            }
        )
