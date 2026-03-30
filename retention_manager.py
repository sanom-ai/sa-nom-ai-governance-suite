import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from audit_integrity import AuditChain
from audit_schemas import AuditEntry
from config import AppConfig


@dataclass(slots=True)
class DatasetRecord:
    record_id: str
    timestamp: str
    payload: Any
    partition: str = "records"


@dataclass(slots=True)
class RetentionDatasetReport:
    dataset: str
    file_path: str | None
    retention_days: int
    records: int
    expired_candidates: int
    hold_blocked_candidates: int
    legal_hold_active: bool
    oldest_record_at: str | None
    newest_record_at: str | None
    next_expiry_at: str | None
    enforcement_action: str
    archive_path_preview: str | None
    archivable_candidates: int
    purgeable_candidates: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class RetentionExecutionAction:
    dataset: str
    action: str
    source_path: str | None
    archive_path: str | None
    expired_candidates: int
    archived_records: int
    purged_records: int
    blocked_records: int
    legal_hold_active: bool
    notes: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class RetentionExecutionResult:
    executed_at: str
    dry_run: bool
    archive_dir: str
    status: str
    archived_total: int
    purged_total: int
    blocked_total: int
    actions: list[RetentionExecutionAction]

    def to_dict(self) -> dict[str, object]:
        return {
            "executed_at": self.executed_at,
            "dry_run": self.dry_run,
            "archive_dir": self.archive_dir,
            "status": self.status,
            "archived_total": self.archived_total,
            "purged_total": self.purged_total,
            "blocked_total": self.blocked_total,
            "actions": [action.to_dict() for action in self.actions],
        }


class RetentionManager:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.legal_holds = self._load_legal_holds()
        self.audit_chain = AuditChain()

    def report(self) -> dict[str, object]:
        self.legal_holds = self._load_legal_holds()
        datasets = [self._build_dataset_report(*spec) for spec in self._dataset_specs()]
        next_expiries = [item.next_expiry_at for item in datasets if item.next_expiry_at]
        active_holds = [item.dataset for item in datasets if item.legal_hold_active]
        return {
            "generated_at": self._utc_now(),
            "legal_hold_file": str(self.config.legal_hold_path) if self.config.legal_hold_path else None,
            "archive_dir": str(self.config.retention_archive_dir),
            "legal_hold_datasets": active_holds,
            "dataset_count": len(datasets),
            "expired_candidate_total": sum(item.expired_candidates for item in datasets),
            "hold_blocked_total": sum(item.hold_blocked_candidates for item in datasets),
            "archive_candidate_total": sum(item.archivable_candidates for item in datasets),
            "purge_candidate_total": sum(item.purgeable_candidates for item in datasets),
            "next_expiry_at": min(next_expiries) if next_expiries else None,
            "datasets": [item.to_dict() for item in datasets],
        }

    def summary(self) -> dict[str, object]:
        report = self.report()
        planned_actions = sum(1 for item in report["datasets"] if item["enforcement_action"] != "none")
        return {
            "datasets": report["dataset_count"],
            "expired_candidates": report["expired_candidate_total"],
            "archive_candidates": report["archive_candidate_total"],
            "legal_hold_datasets": len(report["legal_hold_datasets"]),
            "next_expiry_at": report["next_expiry_at"] or "-",
            "planned_actions": planned_actions,
            "archive_dir": report["archive_dir"],
        }

    def plan(self) -> dict[str, object]:
        report = self.report()
        return {
            "generated_at": report["generated_at"],
            "archive_dir": report["archive_dir"],
            "status": "ready",
            "archive_candidate_total": report["archive_candidate_total"],
            "purge_candidate_total": report["purge_candidate_total"],
            "blocked_total": report["hold_blocked_total"],
            "actions": [
                {
                    "dataset": item["dataset"],
                    "action": item["enforcement_action"],
                    "expired_candidates": item["expired_candidates"],
                    "archivable_candidates": item["archivable_candidates"],
                    "purgeable_candidates": item["purgeable_candidates"],
                    "blocked_by_hold": item["hold_blocked_candidates"],
                    "archive_path_preview": item["archive_path_preview"],
                }
                for item in report["datasets"]
            ],
        }

    def enforce(self, dry_run: bool = True) -> dict[str, object]:
        self.legal_holds = self._load_legal_holds()
        actions = [self._enforce_dataset(*spec, dry_run=dry_run) for spec in self._dataset_specs()]
        result = RetentionExecutionResult(
            executed_at=self._utc_now(),
            dry_run=dry_run,
            archive_dir=str(self.config.retention_archive_dir),
            status="planned" if dry_run else "completed",
            archived_total=sum(action.archived_records for action in actions),
            purged_total=sum(action.purged_records for action in actions),
            blocked_total=sum(action.blocked_records for action in actions),
            actions=actions,
        )
        return result.to_dict()

    def _dataset_specs(self) -> list[tuple[str, Path | None, int, Callable[[Path | None], list[DatasetRecord]], Callable[[Path | None, list[DatasetRecord]], None], str]]:
        return [
            ("audit_log", self.config.audit_log_path, self.config.retention_audit_days, self._load_audit_records, self._save_audit_records, ".jsonl"),
            ("override_requests", self.config.override_store_path, self.config.retention_override_days, self._load_override_records, self._save_list_records, ".json"),
            ("resource_locks", self.config.lock_store_path, self.config.retention_lock_days, self._load_lock_records, self._save_list_records, ".json"),
            ("request_consistency", self.config.consistency_store_path, self.config.retention_consistency_days, self._load_consistency_records, self._save_consistency_records, ".json"),
            ("session_store", self.config.session_store_path, self.config.retention_session_days, self._load_session_records, self._save_list_records, ".json"),
            ("role_private_studio", self.config.role_private_studio_store_path, self.config.retention_role_private_studio_days, self._load_role_private_studio_records, self._save_role_private_studio_records, ".json"),
            ("human_ask", self.config.human_ask_store_path, self.config.retention_human_ask_days, self._load_human_ask_records, self._save_human_ask_records, ".json"),
        ]

    def _build_dataset_report(
        self,
        dataset: str,
        path: Path | None,
        retention_days: int,
        loader: Callable[[Path | None], list[DatasetRecord]],
        _saver: Callable[[Path | None, list[DatasetRecord]], None],
        extension: str,
    ) -> RetentionDatasetReport:
        records = loader(path)
        cutoff = self._now() - timedelta(days=retention_days)
        parsed = sorted((self._parse_timestamp(record.timestamp), record) for record in records if record.timestamp)
        expired = [record for timestamp, record in parsed if timestamp < cutoff]
        live = [record for timestamp, record in parsed if timestamp >= cutoff]
        legal_hold_active = dataset in self.legal_holds
        archive_preview = str(self._archive_destination(dataset, extension)) if expired and not legal_hold_active else None
        if legal_hold_active and expired:
            enforcement_action = "blocked_by_hold"
        elif expired:
            enforcement_action = "archive_and_purge"
        else:
            enforcement_action = "none"
        next_expiry = None
        if live:
            future_expiries = [self._parse_timestamp(record.timestamp) + timedelta(days=retention_days) for record in live]
            next_expiry = min(future_expiries).isoformat()
        return RetentionDatasetReport(
            dataset=dataset,
            file_path=str(path) if path else None,
            retention_days=retention_days,
            records=len(records),
            expired_candidates=len(expired),
            hold_blocked_candidates=len(expired) if legal_hold_active else 0,
            legal_hold_active=legal_hold_active,
            oldest_record_at=parsed[0][0].isoformat() if parsed else None,
            newest_record_at=parsed[-1][0].isoformat() if parsed else None,
            next_expiry_at=next_expiry,
            enforcement_action=enforcement_action,
            archive_path_preview=archive_preview,
            archivable_candidates=0 if legal_hold_active else len(expired),
            purgeable_candidates=0 if legal_hold_active else len(expired),
        )

    def _enforce_dataset(
        self,
        dataset: str,
        path: Path | None,
        retention_days: int,
        loader: Callable[[Path | None], list[DatasetRecord]],
        saver: Callable[[Path | None, list[DatasetRecord]], None],
        extension: str,
        *,
        dry_run: bool,
    ) -> RetentionExecutionAction:
        records = loader(path)
        if path is None:
            return RetentionExecutionAction(
                dataset=dataset,
                action="disabled",
                source_path=None,
                archive_path=None,
                expired_candidates=0,
                archived_records=0,
                purged_records=0,
                blocked_records=0,
                legal_hold_active=False,
                notes=["Dataset is disabled because no runtime path is configured."],
            )

        cutoff = self._now() - timedelta(days=retention_days)
        expired = [record for record in records if self._parse_timestamp(record.timestamp) < cutoff]
        remaining = [record for record in records if self._parse_timestamp(record.timestamp) >= cutoff]
        legal_hold_active = dataset in self.legal_holds
        archive_path = self._archive_destination(dataset, extension)

        if not expired:
            return RetentionExecutionAction(
                dataset=dataset,
                action="no_action",
                source_path=str(path),
                archive_path=None,
                expired_candidates=0,
                archived_records=0,
                purged_records=0,
                blocked_records=0,
                legal_hold_active=legal_hold_active,
                notes=["No expired records matched the current retention window."],
            )

        if legal_hold_active:
            return RetentionExecutionAction(
                dataset=dataset,
                action="blocked_by_hold",
                source_path=str(path),
                archive_path=None,
                expired_candidates=len(expired),
                archived_records=0,
                purged_records=0,
                blocked_records=len(expired),
                legal_hold_active=True,
                notes=["Legal hold is active for this dataset, so archive and purge operations were skipped."],
            )

        action_name = "archive_and_purge_planned" if dry_run else "archive_and_purge_completed"
        if not dry_run:
            self._write_archive(dataset, archive_path, expired)
            saver(path, remaining)

        return RetentionExecutionAction(
            dataset=dataset,
            action=action_name,
            source_path=str(path),
            archive_path=str(archive_path),
            expired_candidates=len(expired),
            archived_records=len(expired),
            purged_records=len(expired),
            blocked_records=0,
            legal_hold_active=False,
            notes=["Expired records were staged for archive and purge." if dry_run else "Expired records were archived and removed from the active dataset."],
        )

    def _load_audit_records(self, path: Path | None) -> list[DatasetRecord]:
        records: list[DatasetRecord] = []
        if path is None or not path.exists():
            return records
        with path.open("r", encoding="utf-8") as handle:
            for index, raw_line in enumerate(handle, start=1):
                line = raw_line.strip()
                if not line:
                    continue
                item = json.loads(line)
                timestamp = item.get("timestamp")
                if not timestamp:
                    continue
                records.append(DatasetRecord(record_id=f"audit:{index}", timestamp=str(timestamp), payload=item))
        return records

    def _load_override_records(self, path: Path | None) -> list[DatasetRecord]:
        if path is None or not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        records: list[DatasetRecord] = []
        for item in data:
            timestamp = item.get("created_at")
            if not timestamp:
                continue
            records.append(
                DatasetRecord(
                    record_id=str(item.get("request_id", f"override:{len(records) + 1}")),
                    timestamp=str(timestamp),
                    payload=item,
                )
            )
        return records

    def _load_lock_records(self, path: Path | None) -> list[DatasetRecord]:
        if path is None or not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        records: list[DatasetRecord] = []
        for item in data:
            timestamp = item.get("updated_at") or item.get("created_at")
            if not timestamp:
                continue
            records.append(
                DatasetRecord(
                    record_id=str(item.get("lock_id", f"lock:{len(records) + 1}")),
                    timestamp=str(timestamp),
                    payload=item,
                )
            )
        return records

    def _load_consistency_records(self, path: Path | None) -> list[DatasetRecord]:
        if path is None or not path.exists():
            return []
        snapshot = json.loads(path.read_text(encoding="utf-8"))
        records: list[DatasetRecord] = []
        for key, item in snapshot.get("idempotency_records", {}).items():
            timestamp = item.get("updated_at") or item.get("created_at")
            if not timestamp:
                continue
            records.append(
                DatasetRecord(
                    record_id=str(key),
                    timestamp=str(timestamp),
                    payload=item,
                    partition="idempotency_records",
                )
            )
        for key, item in snapshot.get("event_streams", {}).items():
            timestamp = item.get("latest_processed_at")
            if not timestamp:
                continue
            records.append(
                DatasetRecord(
                    record_id=str(key),
                    timestamp=str(timestamp),
                    payload=item,
                    partition="event_streams",
                )
            )
        return records

    def _load_session_records(self, path: Path | None) -> list[DatasetRecord]:
        if path is None or not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        records: list[DatasetRecord] = []
        for item in data:
            timestamp = item.get("revoked_at") or item.get("last_seen_at") or item.get("created_at")
            if not timestamp:
                continue
            records.append(
                DatasetRecord(
                    record_id=str(item.get("session_id", f"session:{len(records) + 1}")),
                    timestamp=str(timestamp),
                    payload=item,
                )
            )
        return records


    def _load_role_private_studio_records(self, path: Path | None) -> list[DatasetRecord]:
        if path is None or not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        records: list[DatasetRecord] = []
        for key, item in data.get("requests", {}).items():
            timestamp = item.get("updated_at") or item.get("created_at")
            if not timestamp:
                continue
            records.append(
                DatasetRecord(
                    record_id=str(key),
                    timestamp=str(timestamp),
                    payload=item,
                )
            )
        return records

    def _load_human_ask_records(self, path: Path | None) -> list[DatasetRecord]:
        if path is None or not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        records: list[DatasetRecord] = []
        for key, item in data.get("sessions", {}).items():
            timestamp = item.get("updated_at") or item.get("created_at")
            if not timestamp:
                continue
            records.append(
                DatasetRecord(
                    record_id=str(key),
                    timestamp=str(timestamp),
                    payload=item,
                )
            )
        return records

    def _save_role_private_studio_records(self, path: Path | None, records: list[DatasetRecord]) -> None:
        if path is None:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        snapshot = {
            "generated_at": self._utc_now(),
            "requests": {record.record_id: record.payload for record in records},
        }
        path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")

    def _save_human_ask_records(self, path: Path | None, records: list[DatasetRecord]) -> None:
        if path is None:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        snapshot = {
            "generated_at": self._utc_now(),
            "sessions": {record.record_id: record.payload for record in records},
        }
        path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")

    def _save_audit_records(self, path: Path | None, records: list[DatasetRecord]) -> None:
        if path is None:
            return
        entries = [AuditEntry.from_dict(record.payload) for record in records]
        resealed = self.audit_chain.reseal_entries(entries)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            for entry in resealed:
                handle.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")

    def _save_list_records(self, path: Path | None, records: list[DatasetRecord]) -> None:
        if path is None:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = [record.payload for record in records]
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _save_consistency_records(self, path: Path | None, records: list[DatasetRecord]) -> None:
        if path is None:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        idempotency_records = {record.record_id: record.payload for record in records if record.partition == "idempotency_records"}
        event_streams = {record.record_id: record.payload for record in records if record.partition == "event_streams"}
        snapshot = {
            "generated_at": self._utc_now(),
            "idempotency_records": idempotency_records,
            "event_streams": event_streams,
        }
        path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")

    def _write_archive(self, dataset: str, archive_path: Path, records: list[DatasetRecord]) -> None:
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        if dataset == "audit_log":
            with archive_path.open("w", encoding="utf-8") as handle:
                for record in records:
                    handle.write(json.dumps(record.payload, ensure_ascii=False) + "\n")
            return

        payload: dict[str, object] = {
            "archived_at": self._utc_now(),
            "dataset": dataset,
            "retention_archive_dir": str(self.config.retention_archive_dir),
        }
        if dataset == "request_consistency":
            payload["idempotency_records"] = {
                record.record_id: record.payload for record in records if record.partition == "idempotency_records"
            }
            payload["event_streams"] = {
                record.record_id: record.payload for record in records if record.partition == "event_streams"
            }
        else:
            payload["items"] = [record.payload for record in records]
        archive_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _archive_destination(self, dataset: str, extension: str) -> Path:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return self.config.retention_archive_dir / dataset / f"{dataset}_{timestamp}{extension}"

    def _load_legal_holds(self) -> set[str]:
        path = self.config.legal_hold_path
        if path is None or not path.exists():
            return set()
        data = json.loads(path.read_text(encoding="utf-8"))
        holds = set()
        for item in data.get("datasets", []):
            if item.get("active") and item.get("dataset"):
                holds.add(str(item["dataset"]))
        return holds

    def _parse_timestamp(self, value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _utc_now(self) -> str:
        return self._now().isoformat()
