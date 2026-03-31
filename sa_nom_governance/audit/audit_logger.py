from datetime import datetime, timezone
from pathlib import Path

from sa_nom_governance.api.api_schemas import DecisionResult
from sa_nom_governance.audit.audit_integrity import AuditChain
from sa_nom_governance.audit.audit_schemas import AuditEntry
from sa_nom_governance.audit.event_contract import build_evidence_event_contract
from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.utils.persistence import build_line_ledger


class AuditLogger:
    def __init__(self, log_path: Path | None = None, *, config: AppConfig | None = None) -> None:
        self.ledger = build_line_ledger(config, log_path, logical_name='audit')
        self.log_path = self.ledger.path
        self.entries: list[AuditEntry] = []
        self.chain = AuditChain()
        self._load_existing()

    def record(self, result: DecisionResult) -> None:
        metadata = {
            'context': result.metadata,
            'decision_trace': result.decision_trace,
            'human_override': result.human_override,
            'resource_lock': result.resource_lock,
            'conflict_lock': result.conflict_lock,
            'runtime_evidence': self._build_runtime_evidence(result),
        }
        self._append_entry(
            AuditEntry.create(
                active_role=result.active_role,
                action=result.action,
                outcome=result.outcome,
                reason=result.reason,
                metadata=self._with_event_contract(
                    active_role=result.active_role,
                    action=result.action,
                    outcome=result.outcome,
                    reason=result.reason,
                    metadata=metadata,
                ),
            )
        )

    def record_event(self, active_role: str, action: str, outcome: str, reason: str, metadata: dict[str, object]) -> None:
        self._append_entry(
            AuditEntry.create(
                active_role=active_role,
                action=action,
                outcome=outcome,
                reason=reason,
                metadata=self._with_event_contract(
                    active_role=active_role,
                    action=action,
                    outcome=outcome,
                    reason=reason,
                    metadata=metadata,
                ),
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

    def list_runtime_evidence(
        self,
        *,
        limit: int | None = None,
        outcome: str | None = None,
        source_type: str | None = None,
    ) -> list[dict[str, object]]:
        evidence_rows: list[dict[str, object]] = []
        for entry in self.entries:
            runtime_evidence = entry.metadata.get('runtime_evidence')
            if not isinstance(runtime_evidence, dict):
                continue
            if outcome is not None and runtime_evidence.get('outcome') != outcome:
                continue
            if source_type is not None and runtime_evidence.get('trace_source_type') != source_type:
                continue
            evidence_rows.append(runtime_evidence)

        if limit is None:
            return evidence_rows
        return evidence_rows[-limit:]

    def verify_integrity(self) -> dict[str, object]:
        return self.chain.verify(self.entries).to_dict()

    def health(self) -> dict[str, object]:
        return {
            **self.verify_integrity(),
            'persistence_backend': self.ledger.descriptor().backend,
        }

    def reload(self) -> None:
        self.entries = []
        self._load_existing()

    def reseal_legacy_entries(self) -> dict[str, object]:
        before = self.verify_integrity()
        if before['status'] == 'broken':
            return {
                'status': 'blocked',
                'resealed': False,
                'reason': 'broken_chain',
                'before_integrity': before,
                'after_integrity': before,
            }
        if before['status'] == 'verified':
            return {
                'status': 'noop',
                'resealed': False,
                'reason': 'already_verified',
                'before_integrity': before,
                'after_integrity': before,
            }

        self.entries = self.chain.reseal_entries(self.entries)
        self._write_entries()
        after = self.verify_integrity()
        return {
            'status': 'resealed',
            'resealed': True,
            'reason': 'legacy_entries_resealed',
            'before_integrity': before,
            'after_integrity': after,
        }

    def _build_runtime_evidence(self, result: DecisionResult) -> dict[str, object]:
        decision_trace = result.decision_trace if isinstance(result.decision_trace, dict) else {}
        metadata = result.metadata if isinstance(result.metadata, dict) else {}
        runtime_metadata = metadata.get('metadata') if isinstance(metadata.get('metadata'), dict) else {}
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'request_id': metadata.get('request_id'),
            'requester': result.requester,
            'action': result.action,
            'active_role': result.active_role,
            'outcome': result.outcome,
            'policy_basis': result.policy_basis,
            'trace_source_type': decision_trace.get('source_type'),
            'trace_source_id': decision_trace.get('source_id'),
            'has_human_override': bool(result.human_override),
            'has_exception_surface': result.outcome in {'waiting_human', 'human_required', 'escalated', 'rejected', 'blocked', 'conflicted', 'out_of_order'},
            'authority_gate_triggered': bool(runtime_metadata.get('authority_gate', {}).get('gate_triggered')) if isinstance(runtime_metadata.get('authority_gate'), dict) else False,
            'runtime_state': runtime_metadata.get('runtime_state_flow', {}).get('current_state') if isinstance(runtime_metadata.get('runtime_state_flow'), dict) else None,
            'exception_kind': self._exception_kind(result.outcome),
            'authority_decision': self._authority_decision_evidence(result, runtime_metadata, decision_trace),
        }

    def _exception_kind(self, outcome: str) -> str | None:
        mapping = {
            'blocked': 'blocked',
            'rejected': 'rejected',
            'escalated': 'escalated',
            'conflicted': 'conflicted',
            'out_of_order': 'out_of_order',
        }
        return mapping.get(outcome)

    def _authority_decision_evidence(
        self,
        result: DecisionResult,
        runtime_metadata: dict[str, object],
        decision_trace: dict[str, object],
    ) -> dict[str, object]:
        authority_gate = runtime_metadata.get('authority_gate') if isinstance(runtime_metadata.get('authority_gate'), dict) else {}
        return {
            'outcome': result.outcome,
            'policy_basis': result.policy_basis,
            'trace_source_type': decision_trace.get('source_type'),
            'trace_source_id': decision_trace.get('source_id'),
            'gate_triggered': authority_gate.get('gate_triggered') is True,
            'decision_mode': authority_gate.get('decision_mode'),
            'requires_human_confirmation': authority_gate.get('requires_human_confirmation') if isinstance(authority_gate.get('requires_human_confirmation'), bool) else result.outcome in {'waiting_human', 'human_required'},
        }
    def _with_event_contract(
        self,
        *,
        active_role: str,
        action: str,
        outcome: str,
        reason: str,
        metadata: dict[str, object],
    ) -> dict[str, object]:
        payload = dict(metadata)
        payload['evidence_event'] = build_evidence_event_contract(
            active_role=active_role,
            action=action,
            outcome=outcome,
            reason=reason,
            metadata=payload,
        )
        return payload

    def _append_entry(self, entry: AuditEntry) -> None:
        sealed_entry = self.chain.seal(entry, self.entries)
        self.entries.append(sealed_entry)
        self.ledger.append(sealed_entry.to_dict())

    def _write_entries(self) -> None:
        self.ledger.rewrite([entry.to_dict() for entry in self.entries])

    def _load_existing(self) -> None:
        for item in self.ledger.read_records():
            self.entries.append(AuditEntry.from_dict(item))



