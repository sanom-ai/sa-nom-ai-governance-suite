import json
from pathlib import Path
from tempfile import TemporaryDirectory

from sa_nom_governance.compliance.retention_manager import DatasetRecord, RetentionManager
from sa_nom_governance.utils.config import AppConfig


VALID_AUDIT_PAYLOAD = {
    "timestamp": "2020-01-01T00:00:00+00:00",
    "active_role": "SYSTEM",
    "action": "retention_check",
    "outcome": "completed",
    "reason": "Coverage exercise.",
    "metadata": {},
}


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
                    json.dumps(VALID_AUDIT_PAYLOAD, ensure_ascii=False),
                    json.dumps(
                        {
                            **VALID_AUDIT_PAYLOAD,
                            "timestamp": "2099-01-01T00:00:00+00:00",
                            "action": "future_event",
                            "reason": "Live record.",
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


def test_report_summary_and_blocked_hold_surface_next_expiry() -> None:
    with TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        config = AppConfig(base_dir=base_dir, persist_runtime=True)
        config.retention_override_days = 30

        hold_path = config.legal_hold_path
        assert hold_path is not None
        hold_path.write_text(
            json.dumps({"datasets": [{"dataset": "override_requests", "active": True}]}, ensure_ascii=False),
            encoding="utf-8",
        )

        override_path = config.override_store_path
        assert override_path is not None
        override_path.write_text(
            json.dumps(
                [{"request_id": "override-1", "created_at": "2020-01-01T00:00:00+00:00"}],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        human_ask_path = config.human_ask_store_path
        assert human_ask_path is not None
        human_ask_path.write_text(
            json.dumps(
                {"sessions": {"human-1": {"updated_at": "2099-01-01T00:00:00+00:00", "summary": "live"}}},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        manager = RetentionManager(config)
        report = manager.report()
        datasets = {item["dataset"]: item for item in report["datasets"]}

        assert "override_requests" in report["legal_hold_datasets"]
        assert datasets["override_requests"]["enforcement_action"] == "blocked_by_hold"
        assert datasets["override_requests"]["archive_path_preview"] is None
        assert datasets["override_requests"]["hold_blocked_candidates"] == 1
        assert report["next_expiry_at"] is not None

        summary = manager.summary()
        assert summary["planned_actions"] >= 1
        assert summary["legal_hold_datasets"] == 1
        assert summary["next_expiry_at"] != "-"


def test_private_enforce_dataset_covers_disabled_and_no_action_branches() -> None:
    with TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        config = AppConfig(base_dir=base_dir, persist_runtime=True)
        manager = RetentionManager(config)

        disabled = manager._enforce_dataset(
            "custom",
            None,
            30,
            lambda _path: [],
            lambda _path, _records: None,
            ".json",
            dry_run=False,
        )
        assert disabled.action == "disabled"
        assert disabled.source_path is None

        live_path = base_dir / "live.json"
        live_path.write_text("[]", encoding="utf-8")
        live_record = DatasetRecord(
            record_id="live-1",
            timestamp="2099-01-01T00:00:00+00:00",
            payload={"record_id": "live-1"},
        )
        no_action = manager._enforce_dataset(
            "custom",
            live_path,
            30,
            lambda _path: [live_record],
            lambda _path, _records: (_path, _records),
            ".json",
            dry_run=False,
        )
        assert no_action.action == "no_action"
        assert no_action.expired_candidates == 0
        assert no_action.archive_path is None


def test_loaders_and_savers_cover_runtime_variants() -> None:
    with TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        config = AppConfig(base_dir=base_dir, persist_runtime=True)
        manager = RetentionManager(config)

        audit_path = base_dir / "audit.jsonl"
        audit_path.write_text(
            "\n".join(
                [
                    "",
                    json.dumps({"action": "missing_timestamp"}, ensure_ascii=False),
                    json.dumps(VALID_AUDIT_PAYLOAD, ensure_ascii=False),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        audit_records = manager._load_audit_records(audit_path)
        assert [record.record_id for record in audit_records] == ["audit:3"]

        override_path = base_dir / "override.json"
        override_path.write_text(
            json.dumps(
                [
                    {"request_id": "override-skip"},
                    {"created_at": "2020-01-01T00:00:00+00:00"},
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        override_records = manager._load_override_records(override_path)
        assert [record.record_id for record in override_records] == ["override:1"]

        lock_path = base_dir / "locks.json"
        lock_path.write_text(
            json.dumps(
                [
                    {"lock_id": "lock-skip"},
                    {"created_at": "2020-01-01T00:00:00+00:00"},
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        lock_records = manager._load_lock_records(lock_path)
        assert [record.record_id for record in lock_records] == ["lock:1"]

        consistency_path = base_dir / "consistency.json"
        consistency_path.write_text(
            json.dumps(
                {
                    "idempotency_records": {
                        "skip-idempotency": {"status": "skip"},
                        "ok-idempotency": {"created_at": "2020-01-01T00:00:00+00:00"},
                    },
                    "event_streams": {
                        "skip-stream": {"status": "skip"},
                        "ok-stream": {"latest_processed_at": "2020-01-02T00:00:00+00:00"},
                    },
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        consistency_records = manager._load_consistency_records(consistency_path)
        assert {(record.record_id, record.partition) for record in consistency_records} == {
            ("ok-idempotency", "idempotency_records"),
            ("ok-stream", "event_streams"),
        }

        session_path = base_dir / "sessions.json"
        session_path.write_text(
            json.dumps(
                [
                    {"session_id": "session-skip"},
                    {"created_at": "2020-01-03T00:00:00+00:00"},
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        session_records = manager._load_session_records(session_path)
        assert [record.record_id for record in session_records] == ["session:1"]

        studio_path = base_dir / "studio.json"
        studio_path.write_text(
            json.dumps(
                {
                    "requests": {
                        "skip": {"name": "skip"},
                        "draft-1": {"created_at": "2020-01-04T00:00:00+00:00", "name": "draft"},
                    }
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        studio_records = manager._load_role_private_studio_records(studio_path)
        assert [record.record_id for record in studio_records] == ["draft-1"]

        human_ask_path = base_dir / "human_ask.json"
        human_ask_path.write_text(
            json.dumps(
                {
                    "sessions": {
                        "skip": {"summary": "skip"},
                        "human-1": {"updated_at": "2020-01-05T00:00:00+00:00", "summary": "ok"},
                    }
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        human_ask_records = manager._load_human_ask_records(human_ask_path)
        assert [record.record_id for record in human_ask_records] == ["human-1"]

        studio_save_path = base_dir / "saved_studio.json"
        manager._save_role_private_studio_records(
            studio_save_path,
            [DatasetRecord("draft-1", "2020-01-01T00:00:00+00:00", {"name": "draft"})],
        )
        assert json.loads(studio_save_path.read_text(encoding="utf-8"))["requests"]["draft-1"]["name"] == "draft"

        human_save_path = base_dir / "saved_human.json"
        manager._save_human_ask_records(
            human_save_path,
            [DatasetRecord("human-1", "2020-01-01T00:00:00+00:00", {"summary": "ok"})],
        )
        assert json.loads(human_save_path.read_text(encoding="utf-8"))["sessions"]["human-1"]["summary"] == "ok"

        audit_save_path = base_dir / "saved_audit.jsonl"
        manager._save_audit_records(
            audit_save_path,
            [DatasetRecord("audit-1", "2020-01-01T00:00:00+00:00", VALID_AUDIT_PAYLOAD)],
        )
        saved_audit = [json.loads(line) for line in audit_save_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert saved_audit[0]["entry_hash"]

        list_save_path = base_dir / "saved_list.json"
        manager._save_list_records(
            list_save_path,
            [DatasetRecord("item-1", "2020-01-01T00:00:00+00:00", {"value": 1})],
        )
        assert json.loads(list_save_path.read_text(encoding="utf-8")) == [{"value": 1}]

        consistency_save_path = base_dir / "saved_consistency.json"
        manager._save_consistency_records(
            consistency_save_path,
            [
                DatasetRecord("idem-1", "2020-01-01T00:00:00+00:00", {"value": 1}, partition="idempotency_records"),
                DatasetRecord("stream-1", "2020-01-02T00:00:00+00:00", {"value": 2}, partition="event_streams"),
            ],
        )
        saved_consistency = json.loads(consistency_save_path.read_text(encoding="utf-8"))
        assert saved_consistency["idempotency_records"]["idem-1"]["value"] == 1
        assert saved_consistency["event_streams"]["stream-1"]["value"] == 2

        manager._save_role_private_studio_records(None, [])
        manager._save_human_ask_records(None, [])
        manager._save_audit_records(None, [])
        manager._save_list_records(None, [])
        manager._save_consistency_records(None, [])


def test_archive_writer_legal_holds_and_time_helpers_cover_remaining_paths() -> None:
    with TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        config = AppConfig(base_dir=base_dir, persist_runtime=True)
        manager = RetentionManager(config)

        audit_archive = base_dir / "archive" / "audit.jsonl"
        manager._write_archive(
            "audit_log",
            audit_archive,
            [DatasetRecord("audit-1", "2020-01-01T00:00:00+00:00", VALID_AUDIT_PAYLOAD)],
        )
        assert audit_archive.read_text(encoding="utf-8").strip().startswith("{")

        consistency_archive = base_dir / "archive" / "consistency.json"
        manager._write_archive(
            "request_consistency",
            consistency_archive,
            [
                DatasetRecord("idem-1", "2020-01-01T00:00:00+00:00", {"value": 1}, partition="idempotency_records"),
                DatasetRecord("stream-1", "2020-01-02T00:00:00+00:00", {"value": 2}, partition="event_streams"),
            ],
        )
        consistency_payload = json.loads(consistency_archive.read_text(encoding="utf-8"))
        assert consistency_payload["idempotency_records"]["idem-1"]["value"] == 1
        assert consistency_payload["event_streams"]["stream-1"]["value"] == 2

        generic_archive = base_dir / "archive" / "human_ask.json"
        manager._write_archive(
            "human_ask",
            generic_archive,
            [DatasetRecord("human-1", "2020-01-05T00:00:00+00:00", {"summary": "ok"})],
        )
        assert json.loads(generic_archive.read_text(encoding="utf-8"))["items"][0]["summary"] == "ok"

        hold_path = config.legal_hold_path
        assert hold_path is not None
        hold_path.write_text(
            json.dumps(
                {
                    "datasets": [
                        {"dataset": "override_requests", "active": True},
                        {"dataset": "session_store", "active": False},
                        {"active": True},
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        assert manager._load_legal_holds() == {"override_requests"}

        archive_path = manager._archive_destination("audit_log", ".jsonl")
        assert archive_path.parent.name == "audit_log"
        assert archive_path.name.endswith(".jsonl")

        parsed = manager._parse_timestamp("2026-01-01T00:00:00Z")
        assert parsed.tzinfo is not None
        assert "T" in manager._utc_now()
