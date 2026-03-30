import json
import shutil
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from config import AppConfig
from persistence import JsonLineLedger, JsonStateStore, build_line_ledger, build_state_store, redact_postgres_dsn


@contextmanager
def workspace_temp_dir():
    source_base = Path(__file__).resolve().parents[2]
    runtime_tmp = source_base / "_runtime" / "tmp_test"
    runtime_tmp.mkdir(parents=True, exist_ok=True)
    temp_path = runtime_tmp / f"persistence_{uuid4().hex[:8]}"
    temp_path.mkdir(parents=True, exist_ok=True)
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


def test_json_state_store_round_trip():
    with workspace_temp_dir() as temp_path:
        path = temp_path / "state.json"
        store = JsonStateStore(path)
        payload = {"status": "ok", "items": [1, 2, 3]}

        store.write(payload)
        loaded = store.read(default={})
        descriptor = store.descriptor()

        assert loaded == payload
        assert descriptor.backend == "json_file"
        assert descriptor.configured_backend == "file"
        assert descriptor.mode == "native"


def test_json_line_ledger_append_and_rewrite():
    with workspace_temp_dir() as temp_path:
        path = temp_path / "ledger.jsonl"
        ledger = JsonLineLedger(path)

        ledger.append({"event": "one"})
        ledger.append({"event": "two"})
        assert [row["event"] for row in ledger.read_records()] == ["one", "two"]

        ledger.rewrite([{"event": "rewritten"}])
        descriptor = ledger.descriptor()
        assert [row["event"] for row in ledger.read_records()] == ["rewritten"]
        assert descriptor.backend == "json_lines"
        assert descriptor.configured_backend == "file"
        assert descriptor.mode == "native"


def test_json_state_store_write_is_atomic_without_temp_artifacts():
    with workspace_temp_dir() as temp_path:
        path = temp_path / "state.json"
        store = JsonStateStore(path)

        store.write({"status": "first"})
        store.write({"status": "second"})

        assert json.loads(path.read_text(encoding="utf-8")) == {"status": "second"}
        assert list(path.parent.glob("state_*")) == []


def test_state_store_marks_postgresql_as_configured_with_file_fallback():
    with workspace_temp_dir() as temp_path:
        config = AppConfig()
        config.persistence_backend = "postgresql"
        config.postgres_dsn = "postgresql://sanom:secret@localhost:5432/sanom"
        config.postgres_schema = "sanom_core"
        config.postgres_native_enabled = False

        store = build_state_store(config, temp_path / "state.json", logical_name="sessions")
        descriptor = store.descriptor()

        assert descriptor.backend == "json_file"
        assert descriptor.configured_backend == "postgresql"
        assert descriptor.mode == "fallback"
        assert descriptor.ready is False
        assert descriptor.dsn_present is True
        assert descriptor.schema == "sanom_core"


def test_line_ledger_marks_postgresql_without_dsn_as_fallback_not_ready():
    with workspace_temp_dir() as temp_path:
        config = AppConfig()
        config.persistence_backend = "postgresql"
        config.postgres_dsn = None

        ledger = build_line_ledger(config, temp_path / "audit.jsonl", logical_name="audit")
        descriptor = ledger.descriptor()

        assert descriptor.backend == "json_lines"
        assert descriptor.configured_backend == "postgresql"
        assert descriptor.mode == "fallback"
        assert descriptor.ready is False
        assert descriptor.dsn_present is False


def test_state_store_enters_native_postgresql_mode_when_enabled_and_driver_present():
    with workspace_temp_dir() as temp_path:
        config = AppConfig()
        config.persistence_backend = "postgresql"
        config.postgres_dsn = "postgresql://sanom:secret@db.internal:5432/sanom"
        config.postgres_schema = "sanom_core"
        config.postgres_native_enabled = True

        with patch("persistence.detect_postgres_driver", return_value="psycopg"):
            store = build_state_store(config, temp_path / "state.json", logical_name="sessions")
            descriptor = store.descriptor()

        assert descriptor.backend == "postgresql_jsonb"
        assert descriptor.configured_backend == "postgresql"
        assert descriptor.mode == "native"
        assert descriptor.ready is True
        assert descriptor.driver == "psycopg"
        assert descriptor.path == "postgresql://sanom:***@db.internal:5432/sanom"


def test_redact_postgres_dsn_masks_password():
    masked = redact_postgres_dsn("postgresql://sanom:super-secret@db.internal:5432/sanom")
    assert masked == "postgresql://sanom:***@db.internal:5432/sanom"
