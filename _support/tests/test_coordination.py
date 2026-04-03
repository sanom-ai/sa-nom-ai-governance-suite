import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from unittest.mock import patch

import pytest

from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.integrations.coordination import (
    CoordinationSelection,
    FileWorkQueue,
    RedisWorkQueue,
    _hook_string,
    _timestamp_score,
    _utc_now,
    _validate_namespace,
    build_enterprise_execution_hook,
    build_work_queue,
    detect_redis_driver,
    normalize_coordination_backend,
    redact_secret_url,
)


class _FakeRedisClient:
    def __init__(self):
        self.hashes = {}
        self.indices = {}

    def hset(self, key, mapping):
        bucket = self.hashes.setdefault(key, {})
        for field, value in mapping.items():
            bucket[field] = value.encode("utf-8") if isinstance(value, str) else value

    def hget(self, key, field):
        return self.hashes.get(key, {}).get(field)

    def zadd(self, key, mapping):
        bucket = self.indices.setdefault(key, {})
        bucket.update(mapping)

    def zrange(self, key, start, end):
        rows = [name.encode("utf-8") for name, _score in sorted(self.indices.get(key, {}).items(), key=lambda item: item[1])]
        if not rows:
            return []
        size = len(rows)
        start_index = size + start if start < 0 else start
        end_index = size + end if end < 0 else end
        start_index = max(0, start_index)
        end_index = min(size - 1, end_index)
        if start_index > end_index:
            return []
        return rows[start_index : end_index + 1]



def test_file_work_queue_round_trip() -> None:
    with TemporaryDirectory() as temp_dir:
        queue = build_work_queue(AppConfig(), Path(temp_dir) / "integration_outbox.json", logical_name="integration_outbox")

        job = queue.enqueue("integration_delivery", {"event_type": "runtime.request.completed"})
        queue.mark_processing(job.job_id, worker_id="inline_dispatch")
        queue.mark_completed(job.job_id, result_snapshot={"status": "recorded"})

        rows = queue.list_jobs(limit=10)
        assert len(rows) == 1
        assert rows[0]["status"] == "completed"
        assert queue.summary()["jobs_completed"] == 1



def test_file_work_queue_load_mark_failed_and_missing_job() -> None:
    with TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "integration_outbox.json"
        path.write_text(
            json.dumps(
                {
                    "generated_at": _utc_now(),
                    "jobs": {
                        "job_1": {
                            "job_id": "job_1",
                            "channel": "integration_delivery",
                            "status": "enqueued",
                            "payload": {"event_type": "runtime.request.completed"},
                            "metadata": {},
                            "created_at": _utc_now(),
                            "updated_at": _utc_now(),
                        }
                    },
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        queue = FileWorkQueue(
            path,
            logical_name="integration_outbox",
            selection=CoordinationSelection(
                logical_name="integration_outbox",
                configured_backend="file",
                runtime_backend="json_queue",
                mode="native",
                ready=True,
            ),
        )

        queue.mark_processing("job_1", worker_id="worker-1")
        queue.mark_failed("job_1", error="delivery failed", dead_lettered=True, result_snapshot={"status": "failed"})
        rows = queue.list_jobs(limit=10, status="dead_lettered")
        summary = queue.summary()
        descriptor = queue.descriptor()

        assert rows[0]["status"] == "dead_lettered"
        assert summary["jobs_dead_lettered"] == 1
        assert descriptor.available is True
        with pytest.raises(KeyError, match="Queue job not found"):
            queue.get("missing-job")



def test_file_work_queue_supports_runtime_only_when_path_missing() -> None:
    queue = FileWorkQueue(
        None,
        logical_name="integration_outbox",
        selection=CoordinationSelection(
            logical_name="integration_outbox",
            configured_backend="file",
            runtime_backend="json_queue",
            mode="native",
            ready=True,
        ),
    )

    job = queue.enqueue("integration_delivery", {"event_type": "runtime.request.completed"})

    assert queue.get(job.job_id).channel == "integration_delivery"
    assert queue.descriptor().path is None



def test_work_queue_marks_redis_as_fallback_when_native_disabled() -> None:
    with TemporaryDirectory() as temp_dir:
        config = AppConfig()
        config.coordination_backend = "redis"
        config.redis_url = "redis://default:secret@redis.internal:6379/0"
        config.redis_native_enabled = False

        queue = build_work_queue(config, Path(temp_dir) / "integration_outbox.json", logical_name="integration_outbox")
        descriptor = queue.descriptor()

        assert isinstance(queue, FileWorkQueue)
        assert descriptor.configured_backend == "redis"
        assert descriptor.backend == "json_queue"
        assert descriptor.mode == "fallback"
        assert descriptor.ready is False



def test_work_queue_enters_native_redis_mode_when_enabled_and_driver_present() -> None:
    with TemporaryDirectory() as temp_dir:
        config = AppConfig()
        config.coordination_backend = "redis"
        config.redis_url = "redis://default:secret@redis.internal:6379/0"
        config.redis_native_enabled = True
        config.redis_queue_namespace = "sanom_core"

        with patch("sa_nom_governance.integrations.coordination.detect_redis_driver", return_value="redis"):
            queue = build_work_queue(config, Path(temp_dir) / "integration_outbox.json", logical_name="integration_outbox")
            descriptor = queue.descriptor()

        assert descriptor.configured_backend == "redis"
        assert descriptor.backend == "redis_queue"
        assert descriptor.mode == "native"
        assert descriptor.ready is True
        assert descriptor.namespace == "sanom_core"
        assert descriptor.path == "redis://default:***@redis.internal:6379/0"



def test_redis_work_queue_round_trip_and_summary(monkeypatch) -> None:
    queue = RedisWorkQueue(
        "redis://default:secret@redis.internal:6379/0",
        logical_name="integration_outbox",
        selection=CoordinationSelection(
            logical_name="integration_outbox",
            configured_backend="redis",
            runtime_backend="redis_queue",
            mode="native",
            ready=True,
            driver="redis",
            endpoint_present=True,
            namespace="sanom_core",
        ),
        namespace="sanom_core",
    )
    client = _FakeRedisClient()
    monkeypatch.setattr(queue, "_client", lambda: client)

    first = queue.enqueue("integration_delivery", {"event_type": "runtime.request.completed"}, {"trace_id": "trace-1"})
    second = queue.enqueue("integration_delivery", {"event_type": "runtime.request.failed"})
    queue.mark_processing(first.job_id, worker_id="worker-1")
    queue.mark_completed(first.job_id, result_snapshot={"status": "recorded"})
    queue.mark_failed(second.job_id, error="dispatch failed", dead_lettered=True, result_snapshot={"status": "dead_lettered"})

    rows = queue.list_jobs(limit=10)
    dead_letters = queue.list_jobs(limit=10, status="dead_lettered")
    summary = queue.summary()
    descriptor = queue.descriptor()

    assert rows[0]["job_id"] in {first.job_id, second.job_id}
    assert dead_letters[0]["job_id"] == second.job_id
    assert summary["jobs_total"] == 2
    assert summary["jobs_completed"] == 1
    assert summary["jobs_dead_lettered"] == 1
    assert descriptor.namespace == "sanom_core"
    assert queue._job_key(first.job_id).startswith("sanom_core:integration_outbox:job:")
    assert queue._index_key() == "sanom_core:integration_outbox:index"



def test_redis_work_queue_client_and_error_paths(monkeypatch) -> None:
    queue = RedisWorkQueue(
        "redis://default:secret@redis.internal:6379/0",
        logical_name="integration_outbox",
        selection=CoordinationSelection(
            logical_name="integration_outbox",
            configured_backend="redis",
            runtime_backend="redis_queue",
            mode="native",
            ready=True,
            driver="redis",
            endpoint_present=True,
            namespace="sanom_core",
        ),
        namespace="sanom_core",
    )
    module = ModuleType("redis")

    class _RedisFactory:
        @staticmethod
        def from_url(url, socket_connect_timeout, decode_responses):
            return {
                "url": url,
                "timeout": socket_connect_timeout,
                "decode_responses": decode_responses,
            }

    module.Redis = _RedisFactory
    monkeypatch.setattr("sa_nom_governance.integrations.coordination.detect_redis_driver", lambda: "redis")
    monkeypatch.setitem(sys.modules, "redis", module)

    client = queue._client()

    assert client["timeout"] == 5
    assert client["decode_responses"] is False

    empty_client = _FakeRedisClient()
    monkeypatch.setattr(queue, "_client", lambda: empty_client)
    with pytest.raises(KeyError, match="Queue job not found"):
        queue.get("missing-job")

    monkeypatch.setattr("sa_nom_governance.integrations.coordination.detect_redis_driver", lambda: None)
    with pytest.raises(RuntimeError, match="No supported Redis driver"):
        RedisWorkQueue(
            "redis://default:secret@redis.internal:6379/0",
            logical_name="integration_outbox",
            selection=CoordinationSelection(
                logical_name="integration_outbox",
                configured_backend="redis",
                runtime_backend="redis_queue",
                mode="native",
                ready=True,
            ),
            namespace="sanom_core",
        )._client()



def test_normalize_coordination_backend_and_build_work_queue_defaults() -> None:
    with TemporaryDirectory() as temp_dir:
        queue = build_work_queue(None, Path(temp_dir) / "integration_outbox.json", logical_name="integration_outbox")

    assert normalize_coordination_backend(None) == "file"
    assert normalize_coordination_backend(" redis ") == "redis"
    assert normalize_coordination_backend("anything") == "file"
    assert isinstance(queue, FileWorkQueue)



def test_detect_redis_driver_and_redact_secret_url_helpers(monkeypatch) -> None:
    monkeypatch.setattr(
        "sa_nom_governance.integrations.coordination.importlib_util.find_spec",
        lambda name: object() if name == "redis" else None,
    )
    assert detect_redis_driver() == "redis"

    monkeypatch.setattr("sa_nom_governance.integrations.coordination.importlib_util.find_spec", lambda name: None)
    assert detect_redis_driver() is None

    assert redact_secret_url("redis://default:super-secret@redis.internal:6379/0") == "redis://default:***@redis.internal:6379/0"
    assert redact_secret_url("redis://redis.internal:6379/0") == "redis://redis.internal:6379/0"
    assert redact_secret_url("not-a-url") == "redis://configured"



def test_build_enterprise_execution_hook_preserves_workflow_correlation() -> None:
    config = AppConfig(environment="production")

    hook = build_enterprise_execution_hook(
        config,
        logical_name="integration_outbox",
        channel="integration_delivery",
        payload={
            "event_id": "evt-hook-1",
            "request_id": "req-hook-1",
        },
        metadata={
            "tenant_id": "SANOM-TH",
            "release_version": "v0.2.5",
            "workflow_bundle": {
                "execution_plan": {
                    "plan_id": "plan-hook-1",
                    "step_id": "step-enterprise-delivery",
                    "routing_status": "handoff_active",
                    "plan_status": "handoff_active",
                },
                "decision_queue": {
                    "queue_id": "dq-hook-1",
                    "queue_lane": "human_review",
                    "queue_state": "queued_human_review",
                    "queue_owner": "EXEC_OWNER",
                },
                "correlation": {
                    "request_id": "req-hook-1",
                    "event_id": "evt-hook-1",
                    "execution_plan_id": "plan-hook-1",
                    "execution_step_id": "step-enterprise-delivery",
                    "decision_queue_id": "dq-hook-1",
                    "decision_queue_lane": "human_review",
                },
            },
        },
    )

    assert hook["logical_name"] == "integration_outbox"
    assert hook["channel"] == "integration_delivery"
    assert hook["environment"] == "production"
    assert hook["tenant_id"] == "SANOM-TH"
    assert hook["release_version"] == "v0.2.5"
    assert hook["correlation"]["event_id"] == "evt-hook-1"
    assert hook["correlation"]["request_id"] == "req-hook-1"
    assert hook["correlation"]["execution_plan_id"] == "plan-hook-1"
    assert hook["correlation"]["decision_queue_id"] == "dq-hook-1"
    assert hook["workflow"]["routing_status"] == "handoff_active"
    assert hook["workflow"]["queue_state"] == "queued_human_review"



def test_build_enterprise_execution_hook_uses_defaults_and_fallback_fields() -> None:
    config = AppConfig(environment="development")
    config.coordination_backend = "redis"

    hook = build_enterprise_execution_hook(
        config,
        logical_name="integration_outbox",
        channel="integration_delivery",
        payload={"request_id": "req-hook-2"},
        metadata={
            "release_tag": "v0.7.9",
            "workflow_bundle": {
                "routing": {"routing_status": "queued"},
            },
        },
    )

    assert hook["coordination_backend"] == "redis"
    assert hook["release_version"] == "v0.7.9"
    assert hook["correlation"]["request_id"] == "req-hook-2"
    assert hook["workflow"]["routing_status"] == "queued"
    assert hook["tenant_id"] == config.executive_owner_id()



def test_hook_string_timestamp_and_namespace_helpers() -> None:
    timestamp = _utc_now()

    assert _hook_string(None, "", " value ") == " value "
    assert _timestamp_score(timestamp) > 0
    assert _validate_namespace("sanom:core-1") == "sanom:core-1"
    with pytest.raises(ValueError, match="Invalid Redis namespace"):
        _validate_namespace("bad namespace")
