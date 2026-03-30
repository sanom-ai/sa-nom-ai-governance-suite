import json
import os
import re
import tempfile
import threading
from importlib import util as importlib_util
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit, urlunsplit

if TYPE_CHECKING:
    from sa_nom_governance.utils.config import AppConfig


SUPPORTED_PERSISTENCE_BACKENDS = {"file", "postgresql"}
POSTGRES_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_STORE_LOCKS: dict[str, threading.RLock] = {}
_STORE_LOCKS_GUARD = threading.Lock()


def _store_lock(path: Path | None, logical_name: str) -> threading.RLock:
    key = f"{logical_name}:{path.resolve()}" if path is not None else logical_name
    with _STORE_LOCKS_GUARD:
        lock = _STORE_LOCKS.get(key)
        if lock is None:
            lock = threading.RLock()
            _STORE_LOCKS[key] = lock
        return lock


def _atomic_write_text(path: Path, content: str, *, encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f"{path.stem}_", suffix=path.suffix, dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding=encoding, newline="") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            try:
                os.remove(temp_name)
            except OSError:
                pass


def normalize_persistence_backend(value: str | None) -> str:
    raw = (value or "file").strip().lower()
    if raw in {"postgres", "postgresql"}:
        return "postgresql"
    return "file"


@dataclass(slots=True)
class PersistenceSelection:
    logical_name: str
    configured_backend: str
    runtime_backend: str
    mode: str
    ready: bool
    driver: str | None = None
    dsn_present: bool = False
    schema: str | None = None
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class PersistenceDescriptor:
    backend: str
    configured_backend: str
    path: str | None
    format: str
    available: bool
    logical_name: str
    mode: str = "native"
    ready: bool = True
    driver: str | None = None
    dsn_present: bool = False
    schema: str | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "backend": self.backend,
            "configured_backend": self.configured_backend,
            "path": self.path,
            "format": self.format,
            "available": self.available,
            "logical_name": self.logical_name,
            "mode": self.mode,
            "ready": self.ready,
            "driver": self.driver,
            "dsn_present": self.dsn_present,
            "schema": self.schema,
            "notes": list(self.notes),
        }


class JsonStateStore:
    backend_name = "json_file"
    data_format = "json"

    def __init__(
        self,
        path: Path | None,
        *,
        logical_name: str = "state_store",
        selection: PersistenceSelection | None = None,
    ) -> None:
        self.path = path
        self.logical_name = logical_name
        self._lock = _store_lock(path, logical_name)
        self.selection = selection or PersistenceSelection(
            logical_name=logical_name,
            configured_backend="file",
            runtime_backend=self.backend_name,
            mode="native",
            ready=True,
        )

    def read(self, default: Any) -> Any:
        if self.path is None or not self.path.exists():
            return default
        with self._lock:
            if not self.path.exists():
                return default
            return json.loads(self.path.read_text(encoding="utf-8-sig"))

    def write(self, payload: Any) -> None:
        if self.path is None:
            return
        serialized = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        with self._lock:
            _atomic_write_text(self.path, serialized, encoding="utf-8")

    def exists(self) -> bool:
        return self.path is not None and self.path.exists()

    def descriptor(self) -> PersistenceDescriptor:
        return PersistenceDescriptor(
            backend=self.selection.runtime_backend,
            configured_backend=self.selection.configured_backend,
            path=str(self.path) if self.path is not None else None,
            format=self.data_format,
            available=self.exists(),
            logical_name=self.logical_name,
            mode=self.selection.mode,
            ready=self.selection.ready,
            driver=self.selection.driver,
            dsn_present=self.selection.dsn_present,
            schema=self.selection.schema,
            notes=list(self.selection.notes),
        )


class JsonLineLedger:
    backend_name = "json_lines"
    data_format = "jsonl"

    def __init__(
        self,
        path: Path | None,
        *,
        logical_name: str = "line_ledger",
        selection: PersistenceSelection | None = None,
    ) -> None:
        self.path = path
        self.logical_name = logical_name
        self._lock = _store_lock(path, logical_name)
        self.selection = selection or PersistenceSelection(
            logical_name=logical_name,
            configured_backend="file",
            runtime_backend=self.backend_name,
            mode="native",
            ready=True,
        )

    def append(self, payload: dict[str, Any]) -> None:
        if self.path is None:
            return
        serialized = json.dumps(payload, ensure_ascii=False) + "\n"
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(serialized)
                handle.flush()
                os.fsync(handle.fileno())

    def read_records(self) -> list[dict[str, Any]]:
        if self.path is None or not self.path.exists():
            return []
        records: list[dict[str, Any]] = []
        with self._lock:
            if not self.path.exists():
                return []
            with self.path.open("r", encoding="utf-8") as handle:
                for raw_line in handle:
                    line = raw_line.strip()
                    if not line:
                        continue
                    records.append(json.loads(line))
        return records

    def rewrite(self, payloads: list[dict[str, Any]]) -> None:
        if self.path is None:
            return
        serialized = "".join(json.dumps(payload, ensure_ascii=False) + "\n" for payload in payloads)
        with self._lock:
            _atomic_write_text(self.path, serialized, encoding="utf-8")

    def exists(self) -> bool:
        return self.path is not None and self.path.exists()

    def descriptor(self) -> PersistenceDescriptor:
        return PersistenceDescriptor(
            backend=self.selection.runtime_backend,
            configured_backend=self.selection.configured_backend,
            path=str(self.path) if self.path is not None else None,
            format=self.data_format,
            available=self.exists(),
            logical_name=self.logical_name,
            mode=self.selection.mode,
            ready=self.selection.ready,
            driver=self.selection.driver,
            dsn_present=self.selection.dsn_present,
            schema=self.selection.schema,
            notes=list(self.selection.notes),
        )


class PostgresStateStore:
    backend_name = "postgresql_jsonb"
    data_format = "jsonb"
    table_name = "sanom_state_store"

    def __init__(
        self,
        dsn: str,
        *,
        schema: str,
        logical_name: str,
        selection: PersistenceSelection,
        connect_timeout_seconds: int = 5,
    ) -> None:
        self.dsn = dsn
        self.schema = _validate_postgres_identifier(schema)
        self.logical_name = logical_name
        self.selection = selection
        self.connect_timeout_seconds = connect_timeout_seconds
        self.path = redact_postgres_dsn(dsn)

    def read(self, default: Any) -> Any:
        self._ensure_table()
        row = self._fetchone(
            f'SELECT payload FROM "{self.schema}"."{self.table_name}" WHERE logical_name = %s',
            (self.logical_name,),
        )
        if row is None:
            return default
        payload = row[0]
        if isinstance(payload, str):
            return json.loads(payload)
        return payload

    def write(self, payload: Any) -> None:
        self._ensure_table()
        rendered = json.dumps(payload, ensure_ascii=False)
        self._execute(
            f'''
            INSERT INTO "{self.schema}"."{self.table_name}" (logical_name, payload, updated_at)
            VALUES (%s, %s::jsonb, NOW())
            ON CONFLICT (logical_name)
            DO UPDATE SET payload = EXCLUDED.payload, updated_at = NOW()
            ''',
            (self.logical_name, rendered),
        )

    def exists(self) -> bool:
        return True

    def descriptor(self) -> PersistenceDescriptor:
        return PersistenceDescriptor(
            backend=self.selection.runtime_backend,
            configured_backend=self.selection.configured_backend,
            path=self.path,
            format=self.data_format,
            available=True,
            logical_name=self.logical_name,
            mode=self.selection.mode,
            ready=self.selection.ready,
            driver=self.selection.driver,
            dsn_present=self.selection.dsn_present,
            schema=self.selection.schema,
            notes=list(self.selection.notes),
        )

    def _ensure_table(self) -> None:
        self._execute(f'CREATE SCHEMA IF NOT EXISTS "{self.schema}"')
        self._execute(
            f'''
            CREATE TABLE IF NOT EXISTS "{self.schema}"."{self.table_name}" (
                logical_name TEXT PRIMARY KEY,
                payload JSONB NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            '''
        )

    def _execute(self, query: str, params: tuple[Any, ...] = ()) -> None:
        with _postgres_connection(self.dsn, self.connect_timeout_seconds) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
            connection.commit()

    def _fetchone(self, query: str, params: tuple[Any, ...]) -> tuple[Any, ...] | None:
        with _postgres_connection(self.dsn, self.connect_timeout_seconds) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                row = cursor.fetchone()
            connection.commit()
        return row


class PostgresLineLedger:
    backend_name = "postgresql_jsonl"
    data_format = "jsonb_rows"
    table_name = "sanom_line_ledger"

    def __init__(
        self,
        dsn: str,
        *,
        schema: str,
        logical_name: str,
        selection: PersistenceSelection,
        connect_timeout_seconds: int = 5,
    ) -> None:
        self.dsn = dsn
        self.schema = _validate_postgres_identifier(schema)
        self.logical_name = logical_name
        self.selection = selection
        self.connect_timeout_seconds = connect_timeout_seconds
        self.path = redact_postgres_dsn(dsn)

    def append(self, payload: dict[str, Any]) -> None:
        self._ensure_table()
        rendered = json.dumps(payload, ensure_ascii=False)
        self._execute(
            f'''
            INSERT INTO "{self.schema}"."{self.table_name}" (logical_name, payload, created_at)
            VALUES (%s, %s::jsonb, NOW())
            ''',
            (self.logical_name, rendered),
        )

    def read_records(self) -> list[dict[str, Any]]:
        self._ensure_table()
        rows = self._fetchall(
            f'''
            SELECT payload
            FROM "{self.schema}"."{self.table_name}"
            WHERE logical_name = %s
            ORDER BY entry_id ASC
            ''',
            (self.logical_name,),
        )
        records: list[dict[str, Any]] = []
        for row in rows:
            payload = row[0]
            records.append(json.loads(payload) if isinstance(payload, str) else payload)
        return records

    def rewrite(self, payloads: list[dict[str, Any]]) -> None:
        self._ensure_table()
        with _postgres_connection(self.dsn, self.connect_timeout_seconds) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f'DELETE FROM "{self.schema}"."{self.table_name}" WHERE logical_name = %s',
                    (self.logical_name,),
                )
                for payload in payloads:
                    cursor.execute(
                        f'''
                        INSERT INTO "{self.schema}"."{self.table_name}" (logical_name, payload, created_at)
                        VALUES (%s, %s::jsonb, NOW())
                        ''',
                        (self.logical_name, json.dumps(payload, ensure_ascii=False)),
                    )
            connection.commit()

    def exists(self) -> bool:
        return True

    def descriptor(self) -> PersistenceDescriptor:
        return PersistenceDescriptor(
            backend=self.selection.runtime_backend,
            configured_backend=self.selection.configured_backend,
            path=self.path,
            format=self.data_format,
            available=True,
            logical_name=self.logical_name,
            mode=self.selection.mode,
            ready=self.selection.ready,
            driver=self.selection.driver,
            dsn_present=self.selection.dsn_present,
            schema=self.selection.schema,
            notes=list(self.selection.notes),
        )

    def _ensure_table(self) -> None:
        self._execute(f'CREATE SCHEMA IF NOT EXISTS "{self.schema}"')
        self._execute(
            f'''
            CREATE TABLE IF NOT EXISTS "{self.schema}"."{self.table_name}" (
                entry_id BIGSERIAL PRIMARY KEY,
                logical_name TEXT NOT NULL,
                payload JSONB NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            '''
        )

    def _execute(self, query: str, params: tuple[Any, ...] = ()) -> None:
        with _postgres_connection(self.dsn, self.connect_timeout_seconds) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
            connection.commit()

    def _fetchall(self, query: str, params: tuple[Any, ...]) -> list[tuple[Any, ...]]:
        with _postgres_connection(self.dsn, self.connect_timeout_seconds) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
            connection.commit()
        return list(rows)


def _build_selection(
    config: "AppConfig | None",
    *,
    logical_name: str,
    file_runtime_backend: str,
    native_runtime_backend: str,
) -> PersistenceSelection:
    if config is None:
        return PersistenceSelection(
            logical_name=logical_name,
            configured_backend="file",
            runtime_backend=file_runtime_backend,
            mode="native",
            ready=True,
        )

    configured_backend = normalize_persistence_backend(getattr(config, "persistence_backend", "file"))
    if configured_backend == "file":
        return PersistenceSelection(
            logical_name=logical_name,
            configured_backend="file",
            runtime_backend=file_runtime_backend,
            mode="native",
            ready=True,
        )

    postgres_dsn = getattr(config, "postgres_dsn", None)
    postgres_schema = getattr(config, "postgres_schema", "public")
    postgres_native_enabled = bool(getattr(config, "postgres_native_enabled", False))
    driver_name = detect_postgres_driver()
    notes = [
        "PostgreSQL backend requested for enterprise scale.",
    ]
    if not postgres_dsn:
        notes.append("SANOM_POSTGRES_DSN is not configured yet.")
    if not postgres_native_enabled:
        notes.append("SANOM_POSTGRES_NATIVE_ENABLED is disabled, so runtime stays on the file adapter.")
    if driver_name is None:
        notes.append("No supported PostgreSQL driver is available yet. Install psycopg or psycopg2 to enable native mode.")

    if postgres_dsn and postgres_native_enabled and driver_name is not None:
        notes.append("Native PostgreSQL adapter is selected for this store.")
        return PersistenceSelection(
            logical_name=logical_name,
            configured_backend="postgresql",
            runtime_backend=native_runtime_backend,
            mode="native",
            ready=True,
            driver=driver_name,
            dsn_present=True,
            schema=postgres_schema,
            notes=notes,
        )

    return PersistenceSelection(
        logical_name=logical_name,
        configured_backend="postgresql",
        runtime_backend=file_runtime_backend,
        mode="fallback",
        ready=False,
        driver=driver_name,
        dsn_present=bool(postgres_dsn),
        schema=postgres_schema,
        notes=notes,
    )


def build_state_store(config: "AppConfig | None", path: Path | None, *, logical_name: str):
    selection = _build_selection(
        config,
        logical_name=logical_name,
        file_runtime_backend=JsonStateStore.backend_name,
        native_runtime_backend=PostgresStateStore.backend_name,
    )
    if selection.configured_backend == "postgresql" and selection.mode == "native" and config is not None and config.postgres_dsn:
        return PostgresStateStore(
            config.postgres_dsn,
            schema=config.postgres_schema,
            logical_name=logical_name,
            selection=selection,
            connect_timeout_seconds=config.postgres_connect_timeout_seconds,
        )
    return JsonStateStore(
        path,
        logical_name=logical_name,
        selection=selection,
    )


def build_line_ledger(config: "AppConfig | None", path: Path | None, *, logical_name: str):
    selection = _build_selection(
        config,
        logical_name=logical_name,
        file_runtime_backend=JsonLineLedger.backend_name,
        native_runtime_backend=PostgresLineLedger.backend_name,
    )
    if selection.configured_backend == "postgresql" and selection.mode == "native" and config is not None and config.postgres_dsn:
        return PostgresLineLedger(
            config.postgres_dsn,
            schema=config.postgres_schema,
            logical_name=logical_name,
            selection=selection,
            connect_timeout_seconds=config.postgres_connect_timeout_seconds,
        )
    return JsonLineLedger(
        path,
        logical_name=logical_name,
        selection=selection,
    )


def detect_postgres_driver() -> str | None:
    if importlib_util.find_spec("psycopg") is not None:
        return "psycopg"
    if importlib_util.find_spec("psycopg2") is not None:
        return "psycopg2"
    return None


def redact_postgres_dsn(dsn: str) -> str:
    split = urlsplit(dsn)
    if not split.scheme or not split.netloc:
        return "postgresql://configured"
    username = split.username or ""
    password = split.password
    hostname = split.hostname or ""
    port = f":{split.port}" if split.port else ""
    if username:
        userinfo = username
        if password is not None:
            userinfo += ":***"
        netloc = f"{userinfo}@{hostname}{port}"
    else:
        netloc = f"{hostname}{port}"
    return urlunsplit((split.scheme, netloc, split.path, split.query, split.fragment))


def _validate_postgres_identifier(value: str) -> str:
    if not POSTGRES_IDENTIFIER_RE.match(value):
        raise ValueError(f"Invalid PostgreSQL identifier: {value}")
    return value


def _postgres_connection(dsn: str, connect_timeout_seconds: int):
    driver = detect_postgres_driver()
    if driver == "psycopg":
        import psycopg  # type: ignore

        return psycopg.connect(dsn, connect_timeout=connect_timeout_seconds)
    if driver == "psycopg2":
        import psycopg2  # type: ignore

        return psycopg2.connect(dsn, connect_timeout=connect_timeout_seconds)
    raise RuntimeError("No supported PostgreSQL driver is installed. Install psycopg or psycopg2.")
