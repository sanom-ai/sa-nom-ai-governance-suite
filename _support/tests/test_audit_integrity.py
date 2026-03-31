import json
from pathlib import Path
from tempfile import TemporaryDirectory

from sa_nom_governance.api.api_schemas import DecisionResult
from sa_nom_governance.audit.audit_logger import AuditLogger


def test_audit_log_seals_and_verifies_chain() -> None:
    with TemporaryDirectory() as temp_dir:
        log_path = Path(temp_dir) / "audit.jsonl"
        logger = AuditLogger(log_path=log_path)

        logger.record_event(
            active_role="SYSTEM",
            action="first_event",
            outcome="completed",
            reason="First event in audit chain.",
            metadata={"scope": "test"},
        )
        logger.record_event(
            active_role="SYSTEM",
            action="second_event",
            outcome="completed",
            reason="Second event in audit chain.",
            metadata={"scope": "test"},
        )

        health = logger.health()
        assert health["status"] == "verified"
        assert health["sealed_entries"] == 2

        lines = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert lines[0]["entry_hash"]
        assert lines[1]["prev_hash"] == lines[0]["entry_hash"]


def test_audit_integrity_detects_tampering() -> None:
    with TemporaryDirectory() as temp_dir:
        log_path = Path(temp_dir) / "audit.jsonl"
        logger = AuditLogger(log_path=log_path)
        logger.record_event(
            active_role="SYSTEM",
            action="baseline_event",
            outcome="completed",
            reason="Baseline event before tampering.",
            metadata={"scope": "test"},
        )
        logger.record_event(
            active_role="SYSTEM",
            action="follow_up_event",
            outcome="completed",
            reason="Follow-up event before tampering.",
            metadata={"scope": "test"},
        )

        tampered = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        tampered[0]["reason"] = "Tampered reason"
        log_path.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in tampered) + "\n", encoding="utf-8")

        reloaded = AuditLogger(log_path=log_path)
        health = reloaded.health()
        assert health["status"] == "broken"
        assert health["hash_mismatches"] >= 1 or health["broken_links"] >= 1

def test_audit_reseal_converts_legacy_entries_into_verified_chain() -> None:
    with TemporaryDirectory() as temp_dir:
        log_path = Path(temp_dir) / "audit.jsonl"
        legacy_entries = [
            {
                "timestamp": "2026-03-29T00:00:00+00:00",
                "active_role": "SYSTEM",
                "action": "legacy_event_one",
                "outcome": "completed",
                "reason": "Legacy entry one.",
                "metadata": {"scope": "test"},
            },
            {
                "timestamp": "2026-03-29T00:01:00+00:00",
                "active_role": "SYSTEM",
                "action": "legacy_event_two",
                "outcome": "completed",
                "reason": "Legacy entry two.",
                "metadata": {"scope": "test"},
            },
        ]
        log_path.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in legacy_entries) + "\n", encoding="utf-8")

        logger = AuditLogger(log_path=log_path)
        assert logger.health()["status"] == "legacy_verified"

        result = logger.reseal_legacy_entries()

        assert result["status"] == "resealed"
        assert result["before_integrity"]["legacy_unsealed_entries"] == 2
        assert result["after_integrity"]["status"] == "verified"
        assert result["after_integrity"]["legacy_unsealed_entries"] == 0

        reloaded = AuditLogger(log_path=log_path)
        health = reloaded.health()
        assert health["status"] == "verified"
        assert health["sealed_entries"] == 2


def test_audit_event_contract_is_emitted_for_record_event() -> None:
    with TemporaryDirectory() as temp_dir:
        log_path = Path(temp_dir) / 'audit.jsonl'
        logger = AuditLogger(log_path=log_path)

        logger.record_event(
            active_role='SYSTEM',
            action='contract_probe',
            outcome='completed',
            reason='Validate evidence event contract for plain audit event.',
            metadata={'scope': 'contract_test'},
        )

        latest = logger.list_entries(limit=1)[0]
        evidence_event = latest.metadata['evidence_event']

        assert evidence_event['contract_version'] == 'v0.2.2'
        assert evidence_event['event_kind'] == 'action'
        assert evidence_event['active_role'] == 'SYSTEM'
        assert evidence_event['action'] == 'contract_probe'
        assert evidence_event['outcome'] == 'completed'
        assert evidence_event['requires_human_confirmation'] is False


def test_audit_event_contract_is_emitted_for_decision_result() -> None:
    with TemporaryDirectory() as temp_dir:
        log_path = Path(temp_dir) / 'audit.jsonl'
        logger = AuditLogger(log_path=log_path)

        result = DecisionResult(
            requester='tester',
            action='review_contract',
            active_role='LEGAL',
            outcome='human_required',
            reason='Authority gate requires human confirmation.',
            risk_score=0.7,
            policy_basis='runtime.authority_contract',
            decision_trace={'source_type': 'authority_contract', 'source_id': 'approval_gate'},
            metadata={
                'request_id': 'req-audit-contract-1',
                'metadata': {
                    'authority_gate': {
                        'gate_triggered': True,
                        'outcome': 'human_required',
                        'source_id': 'approval_gate',
                        'reason': 'Request paused for human approval by authority gate.',
                        'requires_human_confirmation': True,
                        'decision_mode': 'ai_prepared_human_confirmed',
                    },
                    'runtime_state_flow': {
                        'current_state': 'awaiting_human_confirmation',
                        'history': [],
                    },
                },
            },
        )

        logger.record(result)

        latest = logger.list_entries(limit=1)[0]
        evidence_event = latest.metadata['evidence_event']

        assert evidence_event['contract_version'] == 'v0.2.2'
        assert evidence_event['event_kind'] == 'authority_gate'
        assert evidence_event['requires_human_confirmation'] is True
        assert isinstance(evidence_event['authority_gate'], dict)
        assert evidence_event['authority_gate']['gate_triggered'] is True
        assert isinstance(evidence_event['runtime_state_flow'], dict)



