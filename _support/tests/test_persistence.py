import json
import shutil
import sys
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType
from unittest.mock import patch
from uuid import uuid4

import pytest

from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.utils.persistence import (
    JsonLineLedger,
    JsonStateStore,
    PersistenceSelection,
    PostgresLineLedger,
    PostgresStateStore,
    _postgres_connection,
    _store_lock,
    _validate_postgres_identifier,
    build_line_ledger,
    build_state_store,
    detect_postgres_driver,
    normalize_persistence_backend,
    redact_postgres_dsn,
)


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


class _FakeCursor:
    def __init__(self, *, row=None, rows=None):
        self.row = row
        self.rows = rows or []
        self.executed = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, query, params=()):
        self.executed.append((query, params))

    def fetchone(self):
        return self.row

    def fetchall(self):
        return self.rows


class _FakeConnection:
    def __init__(self, *, row=None, rows=None):
        self.cursor_obj = _FakeCursor(row=row, rows=rows)
        self.commit_count = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.commit_count += 1


def test_store_lock_reuses_same_key_and_distinguishes_logical_name(tmp_path: Path) -> None:
    path = tmp_path / "state.json"

    first = _store_lock(path, "sessions")
    second = _store_lock(path, "sessions")
    third = _store_lock(path, "audit")
    none_first = _store_lock(None, "sessions")
    none_second = _store_lock(None, "sessions")

    assert first is second
    assert first is not third
    assert none_first is none_second


def test_json_state_store_round_trip() -> None:
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


def test_json_line_ledger_append_and_rewrite() -> None:
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


def test_json_state_store_write_is_atomic_without_temp_artifacts() -> None:
    with workspace_temp_dir() as temp_path:
        path = temp_path / "state.json"
        store = JsonStateStore(path)

        store.write({"status": "first"})
        store.write({"status": "second"})

        assert json.loads(path.read_text(encoding="utf-8")) == {"status": "second"}
        assert list(path.parent.glob("state_*")) == []


def test_normalize_persistence_backend_and_json_defaults(tmp_path: Path) -> None:
    assert normalize_persistence_backend(None) == "file"
    assert normalize_persistence_backend(" postgres ") == "postgresql"
    assert normalize_persistence_backend("PoStGreSQL") == "postgresql"
    assert normalize_persistence_backend("file") == "file"

    state_store = JsonStateStore(None, logical_name="empty")
    line_ledger = JsonLineLedger(None, logical_name="empty")

    assert state_store.read(default={"empty": True}) == {"empty": True}
    assert state_store.exists() is False
    assert state_store.descriptor().path is None
    assert line_ledger.read_records() == []
    assert line_ledger.exists() is False
    assert line_ledger.descriptor().available is False



def test_json_line_ledger_skips_blank_lines_and_missing_path() -> None:
    with workspace_temp_dir() as temp_path:
        path = temp_path / "ledger.jsonl"
        path.write_text('{"event": "one"}\n\n  \n{"event": "two"}\n', encoding="utf-8")

        ledger = JsonLineLedger(path)
        missing = JsonLineLedger(temp_path / "missing.jsonl")

        assert [row["event"] for row in ledger.read_records()] == ["one", "two"]
        assert missing.read_records() == []



def test_state_store_marks_postgresql_as_configured_with_file_fallback() -> None:
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



def test_line_ledger_marks_postgresql_without_dsn_as_fallback_not_ready() -> None:
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



def test_state_store_enters_native_postgresql_mode_when_enabled_and_driver_present() -> None:
    with workspace_temp_dir() as temp_path:
        config = AppConfig()
        config.persistence_backend = "postgresql"
        config.postgres_dsn = "postgresql://sanom:secret@db.internal:5432/sanom"
        config.postgres_schema = "sanom_core"
        config.postgres_native_enabled = True

        with patch("sa_nom_governance.utils.persistence.detect_postgres_driver", return_value="psycopg"):
            store = build_state_store(config, temp_path / "state.json", logical_name="sessions")
            descriptor = store.descriptor()

        assert descriptor.backend == "postgresql_jsonb"
        assert descriptor.configured_backend == "postgresql"
        assert descriptor.mode == "native"
        assert descriptor.ready is True
        assert descriptor.driver == "psycopg"
        assert descriptor.path == "postgresql://sanom:***@db.internal:5432/sanom"



def test_line_ledger_enters_native_postgresql_mode_when_enabled_and_driver_present() -> None:
    with workspace_temp_dir() as temp_path:
        config = AppConfig()
        config.persistence_backend = "postgresql"
        config.postgres_dsn = "postgresql://sanom:secret@db.internal:5432/sanom"
        config.postgres_schema = "sanom_core"
        config.postgres_native_enabled = True

        with patch("sa_nom_governance.utils.persistence.detect_postgres_driver", return_value="psycopg2"):
            ledger = build_line_ledger(config, temp_path / "audit.jsonl", logical_name="audit")
            descriptor = ledger.descriptor()

        assert descriptor.backend == "postgresql_jsonl"
        assert descriptor.configured_backend == "postgresql"
        assert descriptor.mode == "native"
        assert descriptor.ready is True
        assert descriptor.driver == "psycopg2"



def test_postgres_state_store_read_write_descriptor_and_exists() -> None:
    selection = PersistenceSelection(
        logical_name="sessions",
        configured_backend="postgresql",
        runtime_backend="postgresql_jsonb",
        mode="native",
        ready=True,
        driver="psycopg",
        dsn_present=True,
        schema="sanom_core",
        notes=["Native PostgreSQL adapter is selected for this store."],
    )
    store = PostgresStateStore(
        "postgresql://sanom:secret@db.internal:5432/sanom",
        schema="sanom_core",
        logical_name="sessions",
        selection=selection,
    )

    store._ensure_table = lambda: None
    store._fetchone = lambda query, params: ('{"status": "ok"}',)
    assert store.read(default={}) == {"status": "ok"}

    store._fetchone = lambda query, params: ({"status": "ready"},)
    assert store.read(default={}) == {"status": "ready"}

    store._fetchone = lambda query, params: None
    assert store.read(default={"empty": True}) == {"empty": True}

    executed = []
    store._execute = lambda query, params=(): executed.append((query, params))
    store.write({"status": "saved"})
    descriptor = store.descriptor()

    assert any("INSERT INTO" in query for query, _params in executed)
    assert store.exists() is True
    assert descriptor.path == "postgresql://sanom:***@db.internal:5432/sanom"
    assert descriptor.notes == ["Native PostgreSQL adapter is selected for this store."]



def test_postgres_line_ledger_append_read_rewrite_and_descriptor(monkeypatch) -> None:
    selection = PersistenceSelection(
        logical_name="audit",
        configured_backend="postgresql",
        runtime_backend="postgresql_jsonl",
        mode="native",
        ready=True,
        driver="psycopg",
        dsn_present=True,
        schema="sanom_core",
    )
    ledger = PostgresLineLedger(
        "postgresql://sanom:secret@db.internal:5432/sanom",
        schema="sanom_core",
        logical_name="audit",
        selection=selection,
    )

    ledger._ensure_table = lambda: None
    executed = []
    ledger._execute = lambda query, params=(): executed.append((query, params))
    ledger.append({"event": "one"})

    ledger._fetchall = lambda query, params: [('{"event": "one"}',), ({"event": "two"},)]
    assert [row["event"] for row in ledger.read_records()] == ["one", "two"]

    fake_connection = _FakeConnection()
    monkeypatch.setattr("sa_nom_governance.utils.persistence._postgres_connection", lambda dsn, timeout: fake_connection)
    ledger.rewrite([{"event": "rewritten"}])
    descriptor = ledger.descriptor()

    assert any("INSERT INTO" in query for query, _params in executed)
    assert len(fake_connection.cursor_obj.executed) == 2
    assert "DELETE FROM" in fake_connection.cursor_obj.executed[0][0]
    assert "INSERT INTO" in fake_connection.cursor_obj.executed[1][0]
    assert fake_connection.commit_count == 1
    assert descriptor.path == "postgresql://sanom:***@db.internal:5432/sanom"



def test_detect_postgres_driver_prioritizes_and_falls_back(monkeypatch) -> None:
    monkeypatch.setattr(
        "sa_nom_governance.utils.persistence.importlib_util.find_spec",
        lambda name: object() if name == "psycopg" else None,
    )
    assert detect_postgres_driver() == "psycopg"

    monkeypatch.setattr(
        "sa_nom_governance.utils.persistence.importlib_util.find_spec",
        lambda name: object() if name == "psycopg2" else None,
    )
    assert detect_postgres_driver() == "psycopg2"

    monkeypatch.setattr("sa_nom_governance.utils.persistence.importlib_util.find_spec", lambda name: None)
    assert detect_postgres_driver() is None


@pytest.mark.parametrize(("driver_name", "module_name"), [("psycopg", "psycopg"), ("psycopg2", "psycopg2")])
def test_postgres_connection_uses_driver_specific_connector(monkeypatch, driver_name: str, module_name: str) -> None:
    module = ModuleType(module_name)
    module.connect = lambda dsn, connect_timeout: {
        "driver": module_name,
        "dsn": dsn,
        "timeout": connect_timeout,
    }
    monkeypatch.setattr("sa_nom_governance.utils.persistence.detect_postgres_driver", lambda: driver_name)
    monkeypatch.setitem(sys.modules, module_name, module)

    connection = _postgres_connection("postgresql://sanom:secret@db.internal:5432/sanom", 7)

    assert connection["driver"] == module_name
    assert connection["timeout"] == 7



def test_postgres_connection_raises_when_driver_missing(monkeypatch) -> None:
    monkeypatch.setattr("sa_nom_governance.utils.persistence.detect_postgres_driver", lambda: None)

    with pytest.raises(RuntimeError, match="No supported PostgreSQL driver"):
        _postgres_connection("postgresql://sanom:secret@db.internal:5432/sanom", 5)



def test_redact_postgres_dsn_masks_password() -> None:
    masked = redact_postgres_dsn("postgresql://sanom:super-secret@db.internal:5432/sanom")
    assert masked == "postgresql://sanom:***@db.internal:5432/sanom"



def test_redact_postgres_dsn_handles_missing_credentials_and_invalid_values() -> None:
    assert redact_postgres_dsn("postgresql://db.internal:5432/sanom") == "postgresql://db.internal:5432/sanom"
    assert redact_postgres_dsn("invalid-dsn") == "postgresql://configured"



def test_validate_postgres_identifier_accepts_safe_names_and_rejects_invalid() -> None:
    assert _validate_postgres_identifier("sanom_core") == "sanom_core"
    with pytest.raises(ValueError, match="Invalid PostgreSQL identifier"):
        _validate_postgres_identifier("sanom-core")

class _DisappearingPath:
    def __init__(self) -> None:
        self.exists_calls = 0

    def exists(self) -> bool:
        self.exists_calls += 1
        return self.exists_calls == 1

    def read_text(self, encoding: str = 'utf-8') -> str:
        raise AssertionError('read_text should not be called when the file disappears inside the lock')

    def open(self, mode: str = 'r', encoding: str = 'utf-8'):
        raise AssertionError('open should not be called when the file disappears inside the lock')


def test_file_readers_return_defaults_when_path_disappears_inside_lock() -> None:
    state_store = JsonStateStore(None, logical_name='state')
    state_store.path = _DisappearingPath()
    assert state_store.read(default={'missing': True}) == {'missing': True}

    ledger = JsonLineLedger(None, logical_name='ledger')
    ledger.path = _DisappearingPath()
    assert ledger.read_records() == []


def test_postgres_internal_helpers_cover_table_setup_and_fetch_paths(monkeypatch) -> None:
    state_selection = PersistenceSelection(
        logical_name='sessions',
        configured_backend='postgresql',
        runtime_backend='postgresql_jsonb',
        mode='native',
        ready=True,
        driver='psycopg',
        dsn_present=True,
        schema='sanom_core',
    )
    state_store = PostgresStateStore(
        'postgresql://sanom:secret@db.internal:5432/sanom',
        schema='sanom_core',
        logical_name='sessions',
        selection=state_selection,
    )

    ledger_selection = PersistenceSelection(
        logical_name='audit',
        configured_backend='postgresql',
        runtime_backend='postgresql_jsonl',
        mode='native',
        ready=True,
        driver='psycopg',
        dsn_present=True,
        schema='sanom_core',
    )
    ledger = PostgresLineLedger(
        'postgresql://sanom:secret@db.internal:5432/sanom',
        schema='sanom_core',
        logical_name='audit',
        selection=ledger_selection,
    )

    fake_connection = _FakeConnection(row=('{"status": "stored"}',), rows=[('{"event": "stored"}',)])
    monkeypatch.setattr('sa_nom_governance.utils.persistence._postgres_connection', lambda dsn, timeout: fake_connection)

    state_store._ensure_table()
    state_store._execute('SELECT 1', ('state',))
    assert state_store._fetchone('SELECT 2', ('state',)) == ('{"status": "stored"}',)

    ledger._ensure_table()
    ledger._execute('SELECT 3', ('ledger',))
    assert ledger._fetchall('SELECT 4', ('ledger',)) == [('{"event": "stored"}',)]
    assert ledger.exists() is True

    executed_queries = [query for query, _params in fake_connection.cursor_obj.executed]
    assert any('CREATE SCHEMA IF NOT EXISTS' in query for query in executed_queries)
    assert any('CREATE TABLE IF NOT EXISTS "sanom_core"."sanom_state_store"' in query for query in executed_queries)
    assert any('CREATE TABLE IF NOT EXISTS "sanom_core"."sanom_line_ledger"' in query for query in executed_queries)
    assert 'SELECT 1' in executed_queries
    assert 'SELECT 2' in executed_queries
    assert 'SELECT 3' in executed_queries
    assert 'SELECT 4' in executed_queries

