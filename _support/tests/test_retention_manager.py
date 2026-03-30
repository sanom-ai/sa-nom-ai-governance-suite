import json
from pathlib import Path
from tempfile import TemporaryDirectory

from config import AppConfig
from retention_manager import RetentionManager


def test_retention_enforcement_archives_and_purges_expired_audit_records() -> None:
    with TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        config = AppConfig(base_dir=base_dir, persist_runtime=True)
        config.retention_audit_days = 30

        audit_path = config.audit_log_path
        assert audit_path is not None
        audit_path.write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "timestamp": "2020-01-01T00:00:00+00:00",
                            "active_role": "SYSTEM",
                            "action": "legacy_event",
                            "outcome": "completed",
                            "reason": "Expired record.",
                            "metadata": {},
                        },
                        ensure_ascii=False,
                    ),
                    json.dumps(
                        {
                            "timestamp": "2099-01-01T00:00:00+00:00",
                            "active_role": "SYSTEM",
                            "action": "future_event",
                            "outcome": "completed",
                            "reason": "Live record.",
                            "metadata": {},
                        },
                        ensure_ascii=False,
                    ),
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        manager = RetentionManager(config)
        plan = manager.plan()
        assert plan["archive_candidate_total"] == 1

        result = manager.enforce(dry_run=False)
        assert result["archived_total"] == 1
        assert result["purged_total"] == 1

        remaining_lines = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert len(remaining_lines) == 1
        assert remaining_lines[0]["action"] == "future_event"
        assert remaining_lines[0]["entry_hash"]

        archive_files = list((config.retention_archive_dir / "audit_log").glob("*.jsonl"))
        assert len(archive_files) == 1


def test_legal_hold_blocks_override_purge() -> None:
    with TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        config = AppConfig(base_dir=base_dir, persist_runtime=True)
        config.retention_override_days = 30

        hold_path = config.legal_hold_path
        assert hold_path is not None
        hold_path.write_text(
            json.dumps(
                {
                    "datasets": [
                        {"dataset": "override_requests", "active": True, "reason": "Active dispute."}
                    ]
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        override_path = config.override_store_path
        assert override_path is not None
        override_path.write_text(
            json.dumps(
                [
                    {
                        "request_id": "override-1",
                        "origin_request_id": "request-1",
                        "status": "approved",
                        "approver_role": "EXEC_OWNER",
                        "action": "approve_policy",
                        "active_role": "GOV",
                        "required_by": "GOV_APPROVE_POLICY",
                        "reason": "Expired override.",
                        "requester": "tester",
                        "payload_snapshot": {},
                        "created_at": "2020-01-01T00:00:00+00:00",
                    }
                ],
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        manager = RetentionManager(config)
        result = manager.enforce(dry_run=False)
        assert result["blocked_total"] == 1
        stored = json.loads(override_path.read_text(encoding="utf-8"))
        assert len(stored) == 1


def test_session_store_is_included_in_retention_plan() -> None:
    with TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        config = AppConfig(base_dir=base_dir, persist_runtime=True)
        config.retention_session_days = 30

        session_path = config.session_store_path
        assert session_path is not None
        session_path.write_text(
            json.dumps(
                [
                    {
                        "session_id": "session-1",
                        "profile_id": "owner",
                        "display_name": "Executive Owner",
                        "role_name": "owner",
                        "permissions": ["*"],
                        "token_hash": "hash",
                        "status": "revoked",
                        "created_at": "2020-01-01T00:00:00+00:00",
                        "last_seen_at": "2020-01-02T00:00:00+00:00",
                        "expires_at": "2020-01-03T00:00:00+00:00",
                        "idle_expires_at": "2020-01-02T01:00:00+00:00",
                        "auth_method": "access_token",
                        "revoked_at": "2020-01-04T00:00:00+00:00",
                        "revoke_reason": "test"
                    }
                ],
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        manager = RetentionManager(config)
        report = manager.report()
        datasets = {item["dataset"]: item for item in report["datasets"]}
        assert "session_store" in datasets
        assert datasets["session_store"]["expired_candidates"] == 1
