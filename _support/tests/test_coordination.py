from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.integrations.coordination import FileWorkQueue, build_enterprise_execution_hook, build_work_queue, redact_secret_url


def test_file_work_queue_round_trip():
    with TemporaryDirectory() as temp_dir:
        queue = build_work_queue(AppConfig(), Path(temp_dir) / "integration_outbox.json", logical_name="integration_outbox")

        job = queue.enqueue("integration_delivery", {"event_type": "runtime.request.completed"})
        queue.mark_processing(job.job_id, worker_id="inline_dispatch")
        queue.mark_completed(job.job_id, result_snapshot={"status": "recorded"})

        rows = queue.list_jobs(limit=10)
        assert len(rows) == 1
        assert rows[0]["status"] == "completed"
        assert queue.summary()["jobs_completed"] == 1


def test_work_queue_marks_redis_as_fallback_when_native_disabled():
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


def test_work_queue_enters_native_redis_mode_when_enabled_and_driver_present():
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


def test_redact_secret_url_masks_password():
    masked = redact_secret_url("redis://default:super-secret@redis.internal:6379/0")
    assert masked == "redis://default:***@redis.internal:6379/0"



def test_build_enterprise_execution_hook_preserves_workflow_correlation():
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
