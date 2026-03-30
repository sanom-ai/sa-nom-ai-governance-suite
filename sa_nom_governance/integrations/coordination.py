import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from importlib import util as importlib_util
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

if TYPE_CHECKING:
    from sa_nom_governance.utils.config import AppConfig


SUPPORTED_COORDINATION_BACKENDS = {"file", "redis"}
REDIS_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9:_-]+$")


def normalize_coordination_backend(value: str | None) -> str:
    raw = (value or "file").strip().lower()
    if raw == "redis":
        return "redis"
    return "file"


@dataclass(slots=True)
class CoordinationSelection:
    logical_name: str
    configured_backend: str
    runtime_backend: str
    mode: str
    ready: bool
    driver: str | None = None
    endpoint_present: bool = False
    namespace: str | None = None
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CoordinationDescriptor:
    backend: str
    configured_backend: str
    logical_name: str
    mode: str
    ready: bool
    available: bool
    path: str | None = None
    driver: str | None = None
    endpoint_present: bool = False
    namespace: str | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "backend": self.backend,
            "configured_backend": self.configured_backend,
            "logical_name": self.logical_name,
            "mode": self.mode,
            "ready": self.ready,
            "available": self.available,
            "path": self.path,
            "driver": self.driver,
            "endpoint_present": self.endpoint_present,
            "namespace": self.namespace,
            "notes": list(self.notes),
        }


@dataclass(slots=True)
class QueueJob:
    job_id: str
    channel: str
    status: str
    payload: dict[str, object]
    metadata: dict[str, object]
    created_at: str
    updated_at: str
    attempts: int = 0
    worker_id: str | None = None
    last_error: str | None = None
    completed_at: str | None = None
    result_snapshot: dict[str, object] | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "QueueJob":
        return cls(
            job_id=str(payload.get("job_id") or ""),
            channel=str(payload.get("channel") or "default"),
            status=str(payload.get("status") or "enqueued"),
            payload=dict(payload.get("payload") or {}),
            metadata=dict(payload.get("metadata") or {}),
            created_at=str(payload.get("created_at") or ""),
            updated_at=str(payload.get("updated_at") or ""),
            attempts=max(0, int(payload.get("attempts") or 0)),
            worker_id=str(payload["worker_id"]) if payload.get("worker_id") else None,
            last_error=str(payload["last_error"]) if payload.get("last_error") else None,
            completed_at=str(payload["completed_at"]) if payload.get("completed_at") else None,
            result_snapshot=dict(payload.get("result_snapshot") or {}) if payload.get("result_snapshot") else None,
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class FileWorkQueue:
    backend_name = "json_queue"

    def __init__(self, path: Path | None, *, logical_name: str, selection: CoordinationSelection) -> None:
        self.path = path
        self.logical_name = logical_name
        self.selection = selection
        self._jobs: dict[str, QueueJob] = {}
        self._load()

    def enqueue(self, channel: str, payload: dict[str, object], metadata: dict[str, object] | None = None) -> QueueJob:
        now = _utc_now()
        job = QueueJob(
            job_id=f"job_{uuid4().hex[:12]}",
            channel=channel,
            status="enqueued",
            payload=dict(payload),
            metadata=dict(metadata or {}),
            created_at=now,
            updated_at=now,
        )
        self._jobs[job.job_id] = job
        self._save()
        return job

    def mark_processing(self, job_id: str, *, worker_id: str | None = None) -> QueueJob:
        job = self.get(job_id)
        job.status = "processing"
        job.worker_id = worker_id
        job.attempts += 1
        job.updated_at = _utc_now()
        self._save()
        return job

    def mark_completed(self, job_id: str, *, result_snapshot: dict[str, object] | None = None) -> QueueJob:
        job = self.get(job_id)
        job.status = "completed"
        job.updated_at = _utc_now()
        job.completed_at = job.updated_at
        job.result_snapshot = result_snapshot
        self._save()
        return job

    def mark_failed(
        self,
        job_id: str,
        *,
        error: str,
        dead_lettered: bool = False,
        result_snapshot: dict[str, object] | None = None,
    ) -> QueueJob:
        job = self.get(job_id)
        job.status = "dead_lettered" if dead_lettered else "failed"
        job.updated_at = _utc_now()
        job.completed_at = job.updated_at
        job.last_error = error
        job.result_snapshot = result_snapshot
        self._save()
        return job

    def list_jobs(self, *, limit: int = 100, status: str | None = None) -> list[dict[str, object]]:
        jobs = sorted(self._jobs.values(), key=lambda item: item.created_at)
        if status is not None:
            jobs = [job for job in jobs if job.status == status]
        return [job.to_dict() for job in jobs[-limit:]][::-1]

    def get(self, job_id: str) -> QueueJob:
        if job_id not in self._jobs:
            raise KeyError(f"Queue job not found: {job_id}")
        return self._jobs[job_id]

    def summary(self) -> dict[str, object]:
        latest = sorted(self._jobs.values(), key=lambda item: item.updated_at)[-1].to_dict() if self._jobs else None
        return {
            "status": "active" if self._jobs else "idle",
            "jobs_total": len(self._jobs),
            "jobs_enqueued": sum(1 for job in self._jobs.values() if job.status == "enqueued"),
            "jobs_processing": sum(1 for job in self._jobs.values() if job.status == "processing"),
            "jobs_completed": sum(1 for job in self._jobs.values() if job.status == "completed"),
            "jobs_failed": sum(1 for job in self._jobs.values() if job.status == "failed"),
            "jobs_dead_lettered": sum(1 for job in self._jobs.values() if job.status == "dead_lettered"),
            "latest_job": latest,
            "backend": self.selection.runtime_backend,
            "mode": self.selection.mode,
            "path": str(self.path) if self.path is not None else None,
        }

    def descriptor(self) -> CoordinationDescriptor:
        return CoordinationDescriptor(
            backend=self.selection.runtime_backend,
            configured_backend=self.selection.configured_backend,
            logical_name=self.logical_name,
            mode=self.selection.mode,
            ready=self.selection.ready,
            available=True,
            path=str(self.path) if self.path is not None else None,
            driver=self.selection.driver,
            endpoint_present=self.selection.endpoint_present,
            namespace=self.selection.namespace,
            notes=list(self.selection.notes),
        )

    def _load(self) -> None:
        if self.path is None or not self.path.exists():
            return
        snapshot = json.loads(self.path.read_text(encoding="utf-8-sig"))
        self._jobs = {
            job_id: QueueJob.from_dict(item)
            for job_id, item in dict(snapshot.get("jobs") or {}).items()
        }

    def _save(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_at": _utc_now(),
            "jobs": {job_id: job.to_dict() for job_id, job in sorted(self._jobs.items())},
        }
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class RedisWorkQueue:
    backend_name = "redis_queue"

    def __init__(
        self,
        url: str,
        *,
        logical_name: str,
        selection: CoordinationSelection,
        namespace: str,
        connect_timeout_seconds: int = 5,
    ) -> None:
        self.url = url
        self.logical_name = logical_name
        self.selection = selection
        self.namespace = _validate_namespace(namespace)
        self.connect_timeout_seconds = connect_timeout_seconds
        self.path = redact_secret_url(url)

    def enqueue(self, channel: str, payload: dict[str, object], metadata: dict[str, object] | None = None) -> QueueJob:
        job = QueueJob(
            job_id=f"job_{uuid4().hex[:12]}",
            channel=channel,
            status="enqueued",
            payload=dict(payload),
            metadata=dict(metadata or {}),
            created_at=_utc_now(),
            updated_at=_utc_now(),
        )
        client = self._client()
        key = self._job_key(job.job_id)
        client.hset(key, mapping={"payload": json.dumps(job.to_dict(), ensure_ascii=False)})
        client.zadd(self._index_key(), {job.job_id: _timestamp_score(job.created_at)})
        return job

    def mark_processing(self, job_id: str, *, worker_id: str | None = None) -> QueueJob:
        job = self.get(job_id)
        job.status = "processing"
        job.worker_id = worker_id
        job.attempts += 1
        job.updated_at = _utc_now()
        self._save(job)
        return job

    def mark_completed(self, job_id: str, *, result_snapshot: dict[str, object] | None = None) -> QueueJob:
        job = self.get(job_id)
        job.status = "completed"
        job.updated_at = _utc_now()
        job.completed_at = job.updated_at
        job.result_snapshot = result_snapshot
        self._save(job)
        return job

    def mark_failed(
        self,
        job_id: str,
        *,
        error: str,
        dead_lettered: bool = False,
        result_snapshot: dict[str, object] | None = None,
    ) -> QueueJob:
        job = self.get(job_id)
        job.status = "dead_lettered" if dead_lettered else "failed"
        job.updated_at = _utc_now()
        job.completed_at = job.updated_at
        job.last_error = error
        job.result_snapshot = result_snapshot
        self._save(job)
        return job

    def list_jobs(self, *, limit: int = 100, status: str | None = None) -> list[dict[str, object]]:
        client = self._client()
        job_ids = [job_id.decode("utf-8") if isinstance(job_id, bytes) else str(job_id) for job_id in client.zrange(self._index_key(), -limit, -1)]
        rows: list[dict[str, object]] = []
        for job_id in reversed(job_ids):
            job = self.get(job_id)
            if status is None or job.status == status:
                rows.append(job.to_dict())
        return rows

    def get(self, job_id: str) -> QueueJob:
        client = self._client()
        raw = client.hget(self._job_key(job_id), "payload")
        if raw is None:
            raise KeyError(f"Queue job not found: {job_id}")
        payload = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        return QueueJob.from_dict(json.loads(payload))

    def summary(self) -> dict[str, object]:
        jobs = [QueueJob.from_dict(item) for item in self.list_jobs(limit=500)]
        latest = jobs[0].to_dict() if jobs else None
        return {
            "status": "active" if jobs else "idle",
            "jobs_total": len(jobs),
            "jobs_enqueued": sum(1 for job in jobs if job.status == "enqueued"),
            "jobs_processing": sum(1 for job in jobs if job.status == "processing"),
            "jobs_completed": sum(1 for job in jobs if job.status == "completed"),
            "jobs_failed": sum(1 for job in jobs if job.status == "failed"),
            "jobs_dead_lettered": sum(1 for job in jobs if job.status == "dead_lettered"),
            "latest_job": latest,
            "backend": self.selection.runtime_backend,
            "mode": self.selection.mode,
            "path": self.path,
        }

    def descriptor(self) -> CoordinationDescriptor:
        return CoordinationDescriptor(
            backend=self.selection.runtime_backend,
            configured_backend=self.selection.configured_backend,
            logical_name=self.logical_name,
            mode=self.selection.mode,
            ready=self.selection.ready,
            available=True,
            path=self.path,
            driver=self.selection.driver,
            endpoint_present=self.selection.endpoint_present,
            namespace=self.selection.namespace,
            notes=list(self.selection.notes),
        )

    def _save(self, job: QueueJob) -> None:
        client = self._client()
        client.hset(self._job_key(job.job_id), mapping={"payload": json.dumps(job.to_dict(), ensure_ascii=False)})
        client.zadd(self._index_key(), {job.job_id: _timestamp_score(job.updated_at)})

    def _client(self):
        driver = detect_redis_driver()
        if driver == "redis":
            import redis  # type: ignore

            return redis.Redis.from_url(self.url, socket_connect_timeout=self.connect_timeout_seconds, decode_responses=False)
        raise RuntimeError("No supported Redis driver is installed. Install redis to enable native coordination.")

    def _job_key(self, job_id: str) -> str:
        return f"{self.namespace}:{self.logical_name}:job:{job_id}"

    def _index_key(self) -> str:
        return f"{self.namespace}:{self.logical_name}:index"


def build_work_queue(config: "AppConfig | None", path: Path | None, *, logical_name: str):
    selection = _build_selection(config, logical_name=logical_name)
    if selection.configured_backend == "redis" and selection.mode == "native" and config is not None and config.redis_url:
        return RedisWorkQueue(
            config.redis_url,
            logical_name=logical_name,
            selection=selection,
            namespace=config.redis_queue_namespace,
            connect_timeout_seconds=config.redis_connect_timeout_seconds,
        )
    return FileWorkQueue(path, logical_name=logical_name, selection=selection)


def detect_redis_driver() -> str | None:
    if importlib_util.find_spec("redis") is not None:
        return "redis"
    return None


def redact_secret_url(url: str) -> str:
    split = urlsplit(url)
    if not split.scheme or not split.netloc:
        return "redis://configured"
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


def _build_selection(config: "AppConfig | None", *, logical_name: str) -> CoordinationSelection:
    if config is None:
        return CoordinationSelection(
            logical_name=logical_name,
            configured_backend="file",
            runtime_backend=FileWorkQueue.backend_name,
            mode="native",
            ready=True,
        )

    configured_backend = normalize_coordination_backend(getattr(config, "coordination_backend", "file"))
    if configured_backend == "file":
        return CoordinationSelection(
            logical_name=logical_name,
            configured_backend="file",
            runtime_backend=FileWorkQueue.backend_name,
            mode="native",
            ready=True,
        )

    redis_url = getattr(config, "redis_url", None)
    redis_native_enabled = bool(getattr(config, "redis_native_enabled", False))
    redis_namespace = getattr(config, "redis_queue_namespace", "sanom")
    driver_name = detect_redis_driver()
    notes = [
        "Redis coordination backend requested for enterprise scale.",
    ]
    if not redis_url:
        notes.append("SANOM_REDIS_URL is not configured yet.")
    if not redis_native_enabled:
        notes.append("SANOM_REDIS_NATIVE_ENABLED is disabled, so runtime stays on the file queue.")
    if driver_name is None:
        notes.append("No supported Redis driver is available yet. Install redis to enable native coordination.")

    if redis_url and redis_native_enabled and driver_name is not None:
        notes.append("Native Redis queue adapter is selected for this coordination layer.")
        return CoordinationSelection(
            logical_name=logical_name,
            configured_backend="redis",
            runtime_backend=RedisWorkQueue.backend_name,
            mode="native",
            ready=True,
            driver=driver_name,
            endpoint_present=True,
            namespace=redis_namespace,
            notes=notes,
        )

    return CoordinationSelection(
        logical_name=logical_name,
        configured_backend="redis",
        runtime_backend=FileWorkQueue.backend_name,
        mode="fallback",
        ready=False,
        driver=driver_name,
        endpoint_present=bool(redis_url),
        namespace=redis_namespace,
        notes=notes,
    )


def _validate_namespace(value: str) -> str:
    if not REDIS_IDENTIFIER_RE.match(value):
        raise ValueError(f"Invalid Redis namespace: {value}")
    return value


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _timestamp_score(value: str) -> float:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
