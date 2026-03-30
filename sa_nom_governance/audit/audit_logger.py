from pathlib import Path

from sa_nom_governance.api.api_schemas import DecisionResult
from sa_nom_governance.audit.audit_integrity import AuditChain
from sa_nom_governance.audit.audit_schemas import AuditEntry
from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.utils.persistence import build_line_ledger


class AuditLogger:
    def __init__(self, log_path: Path | None = None, *, config: AppConfig | None = None) -> None:
        self.ledger = build_line_ledger(config, log_path, logical_name="audit")
        self.log_path = self.ledger.path
        self.entries: list[AuditEntry] = []
        self.chain = AuditChain()
        self._load_existing()

    def record(self, result: DecisionResult) -> None:
        metadata = {
            "context": result.metadata,
            "decision_trace": result.decision_trace,
            "human_override": result.human_override,
            "resource_lock": result.resource_lock,
            "conflict_lock": result.conflict_lock,
        }
        self._append_entry(
            AuditEntry.create(
                active_role=result.active_role,
                action=result.action,
                outcome=result.outcome,
                reason=result.reason,
                metadata=metadata,
            )
        )

    def record_event(self, active_role: str, action: str, outcome: str, reason: str, metadata: dict[str, object]) -> None:
        self._append_entry(
            AuditEntry.create(
                active_role=active_role,
                action=action,
                outcome=outcome,
                reason=reason,
                metadata=metadata,
            )
        )

    def record_override_event(self, active_role: str, action: str, outcome: str, reason: str, metadata: dict[str, object]) -> None:
        self.record_event(
            active_role=active_role,
            action=action,
            outcome=outcome,
            reason=reason,
            metadata=metadata,
        )

    def list_entries(self, limit: int | None = None) -> list[AuditEntry]:
        if limit is None:
            return list(self.entries)
        return self.entries[-limit:]

    def verify_integrity(self) -> dict[str, object]:
        return self.chain.verify(self.entries).to_dict()

    def health(self) -> dict[str, object]:
        return {
            **self.verify_integrity(),
            "persistence_backend": self.ledger.descriptor().backend,
        }

    def reload(self) -> None:
        self.entries = []
        self._load_existing()

    def reseal_legacy_entries(self) -> dict[str, object]:
        before = self.verify_integrity()
        if before["status"] == "broken":
            return {
                "status": "blocked",
                "resealed": False,
                "reason": "broken_chain",
                "before_integrity": before,
                "after_integrity": before,
            }
        if before["status"] == "verified":
            return {
                "status": "noop",
                "resealed": False,
                "reason": "already_verified",
                "before_integrity": before,
                "after_integrity": before,
            }

        self.entries = self.chain.reseal_entries(self.entries)
        self._write_entries()
        after = self.verify_integrity()
        return {
            "status": "resealed",
            "resealed": True,
            "reason": "legacy_entries_resealed",
            "before_integrity": before,
            "after_integrity": after,
        }

    def _append_entry(self, entry: AuditEntry) -> None:
        sealed_entry = self.chain.seal(entry, self.entries)
        self.entries.append(sealed_entry)
        self.ledger.append(sealed_entry.to_dict())

    def _write_entries(self) -> None:
        self.ledger.rewrite([entry.to_dict() for entry in self.entries])

    def _load_existing(self) -> None:
        for item in self.ledger.read_records():
            self.entries.append(AuditEntry.from_dict(item))
