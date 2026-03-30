import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from sa_nom_governance.audit.audit_schemas import AuditEntry


@dataclass(slots=True)
class AuditIntegrityReport:
    status: str
    entries_total: int
    sealed_entries: int
    legacy_unsealed_entries: int
    broken_links: int
    hash_mismatches: int
    sequence_mismatches: int
    first_issue: str | None
    last_hash: str | None
    verified_at: str
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class AuditChain:
    def seal(self, entry: AuditEntry, existing_entries: list[AuditEntry]) -> AuditEntry:
        previous_entry = existing_entries[-1] if existing_entries else None
        previous_sequence = previous_entry.sequence if previous_entry is not None else None
        sequence = previous_sequence + 1 if previous_sequence is not None else len(existing_entries) + 1
        prev_hash = self.entry_digest(previous_entry) if previous_entry is not None else None
        sealed = AuditEntry(
            timestamp=entry.timestamp,
            active_role=entry.active_role,
            action=entry.action,
            outcome=entry.outcome,
            reason=entry.reason,
            metadata=dict(entry.metadata),
            entry_id=entry.entry_id or f"audit-{uuid4().hex}",
            sequence=sequence,
            prev_hash=prev_hash,
        )
        sealed.entry_hash = self.entry_digest(sealed)
        return sealed

    def reseal_entries(self, entries: list[AuditEntry]) -> list[AuditEntry]:
        resealed: list[AuditEntry] = []
        for entry in entries:
            resealed.append(
                self.seal(
                    AuditEntry(
                        timestamp=entry.timestamp,
                        active_role=entry.active_role,
                        action=entry.action,
                        outcome=entry.outcome,
                        reason=entry.reason,
                        metadata=dict(entry.metadata),
                        entry_id=entry.entry_id,
                    ),
                    resealed,
                )
            )
        return resealed

    def entry_digest(self, entry: AuditEntry | None) -> str | None:
        if entry is None:
            return None
        payload = {
            "timestamp": entry.timestamp,
            "active_role": entry.active_role,
            "action": entry.action,
            "outcome": entry.outcome,
            "reason": entry.reason,
            "metadata": entry.metadata,
            "entry_id": entry.entry_id,
            "sequence": entry.sequence,
            "prev_hash": entry.prev_hash,
        }
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def verify(self, entries: list[AuditEntry]) -> AuditIntegrityReport:
        sealed_entries = 0
        legacy_unsealed_entries = 0
        broken_links = 0
        hash_mismatches = 0
        sequence_mismatches = 0
        issues: list[str] = []
        previous_digest: str | None = None
        previous_sequence: int | None = None

        for index, entry in enumerate(entries, start=1):
            has_chain_metadata = any(
                value is not None for value in (entry.entry_id, entry.sequence, entry.prev_hash, entry.entry_hash)
            )
            digest = self.entry_digest(entry)

            if not has_chain_metadata:
                legacy_unsealed_entries += 1
                previous_digest = digest
                continue

            sealed_entries += 1
            if previous_sequence is not None and entry.sequence != previous_sequence + 1:
                sequence_mismatches += 1
                issues.append(
                    f"Sequence mismatch at log position {index}: expected {previous_sequence + 1}, found {entry.sequence}."
                )
            elif previous_sequence is None and (entry.sequence is None or entry.sequence <= 0):
                sequence_mismatches += 1
                issues.append(f"First sealed entry at log position {index} must have a positive sequence number.")

            if entry.prev_hash != previous_digest:
                broken_links += 1
                issues.append(
                    f"Hash link mismatch at log position {index}: expected prev_hash {previous_digest}, found {entry.prev_hash}."
                )

            if entry.entry_hash != digest:
                hash_mismatches += 1
                issues.append(f"Entry hash mismatch at log position {index}.")

            previous_sequence = entry.sequence if entry.sequence is not None else previous_sequence
            previous_digest = digest

        status = "verified"
        if issues:
            status = "broken"
        elif legacy_unsealed_entries:
            status = "legacy_verified"

        return AuditIntegrityReport(
            status=status,
            entries_total=len(entries),
            sealed_entries=sealed_entries,
            legacy_unsealed_entries=legacy_unsealed_entries,
            broken_links=broken_links,
            hash_mismatches=hash_mismatches,
            sequence_mismatches=sequence_mismatches,
            first_issue=issues[0] if issues else None,
            last_hash=previous_digest,
            verified_at=datetime.now(timezone.utc).isoformat(),
            issues=issues,
        )
