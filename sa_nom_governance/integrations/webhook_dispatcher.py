import hashlib
import hmac
import json
import ssl
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4

from sa_nom_governance.integrations.coordination import build_work_queue
from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.integrations.integration_registry import IntegrationRegistry, IntegrationTarget
from sa_nom_governance.utils.persistence import build_line_ledger


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class DeliveryRecord:
    delivery_id: str
    event_id: str
    event_type: str
    target_id: str
    target_name: str
    category: str
    delivery_mode: str
    status: str
    attempted_at: str
    source: str
    requested_by: str | None
    destination: str
    payload_digest: str
    reason: str
    duration_ms: int
    attempt_number: int
    max_attempts: int
    signing_policy: str
    queue_job_id: str | None = None
    response_code: int | None = None
    response_excerpt: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "DeliveryRecord":
        return cls(
            delivery_id=str(payload.get("delivery_id") or ""),
            event_id=str(payload.get("event_id") or ""),
            event_type=str(payload.get("event_type") or ""),
            target_id=str(payload.get("target_id") or ""),
            target_name=str(payload.get("target_name") or ""),
            category=str(payload.get("category") or "custom"),
            delivery_mode=str(payload.get("delivery_mode") or "log_only"),
            status=str(payload.get("status") or "unknown"),
            attempted_at=str(payload.get("attempted_at") or ""),
            source=str(payload.get("source") or "system"),
            requested_by=str(payload["requested_by"]) if payload.get("requested_by") else None,
            destination=str(payload.get("destination") or ""),
            payload_digest=str(payload.get("payload_digest") or ""),
            reason=str(payload.get("reason") or ""),
            duration_ms=int(payload.get("duration_ms") or 0),
            attempt_number=max(1, int(payload.get("attempt_number") or 1)),
            max_attempts=max(1, int(payload.get("max_attempts") or 1)),
            signing_policy=str(payload.get("signing_policy") or "none"),
            queue_job_id=str(payload["queue_job_id"]) if payload.get("queue_job_id") else None,
            response_code=int(payload["response_code"]) if payload.get("response_code") is not None else None,
            response_excerpt=str(payload["response_excerpt"]) if payload.get("response_excerpt") is not None else None,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "delivery_id": self.delivery_id,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "target_id": self.target_id,
            "target_name": self.target_name,
            "category": self.category,
            "delivery_mode": self.delivery_mode,
            "status": self.status,
            "attempted_at": self.attempted_at,
            "source": self.source,
            "requested_by": self.requested_by,
            "destination": self.destination,
            "payload_digest": self.payload_digest,
            "reason": self.reason,
            "duration_ms": self.duration_ms,
            "attempt_number": self.attempt_number,
            "max_attempts": self.max_attempts,
            "signing_policy": self.signing_policy,
            "queue_job_id": self.queue_job_id,
            "response_code": self.response_code,
            "response_excerpt": self.response_excerpt,
        }


@dataclass(slots=True)
class DeadLetterRecord:
    dead_letter_id: str
    event_id: str
    event_type: str
    target_id: str
    target_name: str
    category: str
    source: str
    requested_by: str | None
    destination: str
    payload_digest: str
    final_status: str
    attempts_used: int
    max_attempts: int
    signing_policy: str
    dead_lettered_at: str
    reason: str
    queue_job_id: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "DeadLetterRecord":
        return cls(
            dead_letter_id=str(payload.get("dead_letter_id") or ""),
            event_id=str(payload.get("event_id") or ""),
            event_type=str(payload.get("event_type") or ""),
            target_id=str(payload.get("target_id") or ""),
            target_name=str(payload.get("target_name") or ""),
            category=str(payload.get("category") or "custom"),
            source=str(payload.get("source") or "system"),
            requested_by=str(payload["requested_by"]) if payload.get("requested_by") else None,
            destination=str(payload.get("destination") or ""),
            payload_digest=str(payload.get("payload_digest") or ""),
            final_status=str(payload.get("final_status") or "failed"),
            attempts_used=max(1, int(payload.get("attempts_used") or 1)),
            max_attempts=max(1, int(payload.get("max_attempts") or 1)),
            signing_policy=str(payload.get("signing_policy") or "none"),
            dead_lettered_at=str(payload.get("dead_lettered_at") or ""),
            reason=str(payload.get("reason") or ""),
            queue_job_id=str(payload["queue_job_id"]) if payload.get("queue_job_id") else None,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "dead_letter_id": self.dead_letter_id,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "target_id": self.target_id,
            "target_name": self.target_name,
            "category": self.category,
            "source": self.source,
            "requested_by": self.requested_by,
            "destination": self.destination,
            "payload_digest": self.payload_digest,
            "final_status": self.final_status,
            "attempts_used": self.attempts_used,
            "max_attempts": self.max_attempts,
            "signing_policy": self.signing_policy,
            "dead_lettered_at": self.dead_lettered_at,
            "reason": self.reason,
            "queue_job_id": self.queue_job_id,
        }


class WebhookDispatcher:
    def __init__(self, config: AppConfig, registry: IntegrationRegistry) -> None:
        self.config = config
        self.registry = registry
        self.ledger = build_line_ledger(config, config.integration_delivery_log_path, logical_name="integration_deliveries")
        self.dead_letter_ledger = build_line_ledger(config, config.integration_dead_letter_log_path, logical_name="integration_dead_letters")
        self.outbox = build_work_queue(config, config.integration_outbox_path, logical_name="integration_outbox")
        self.log_path = self.ledger.path
        self.dead_letter_path = self.dead_letter_ledger.path
        self.outbox_path = getattr(self.outbox, "path", None)
        self.records: list[DeliveryRecord] = []
        self.dead_letters: list[DeadLetterRecord] = []
        self._load_existing()

    def dispatch_event(
        self,
        event_type: str,
        payload: dict[str, object],
        *,
        source: str,
        requested_by: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> dict[str, object]:
        event_id = f"evt_{uuid4().hex[:12]}"
        envelope = {
            "event_id": event_id,
            "event_type": event_type,
            "occurred_at": utc_now(),
            "source": source,
            "requested_by": requested_by,
            "metadata": metadata or {},
            "payload": payload,
        }
        payload_bytes = json.dumps(envelope, ensure_ascii=False, sort_keys=True).encode("utf-8")
        payload_digest = hashlib.sha256(payload_bytes).hexdigest()

        targets = self.registry.matching_targets(event_type)
        deliveries: list[DeliveryRecord] = []
        dead_letters: list[DeadLetterRecord] = []
        for target in targets:
            outbox_job = self.outbox.enqueue(
                "integration_delivery",
                {
                    "event_id": event_id,
                    "event_type": event_type,
                    "target_id": target.target_id,
                    "target_name": target.name,
                    "delivery_mode": target.delivery_mode,
                    "source": source,
                    "requested_by": requested_by,
                },
                metadata={
                    "category": target.category,
                    "endpoint_url": target.endpoint_url,
                },
            )
            self.outbox.mark_processing(outbox_job.job_id, worker_id="inline_dispatch")
            target_deliveries, target_dead_letter = self._deliver(target, envelope, payload_bytes, payload_digest, queue_job_id=outbox_job.job_id)
            deliveries.extend(target_deliveries)
            if target_dead_letter is not None:
                dead_letters.append(target_dead_letter)
                self.outbox.mark_failed(
                    outbox_job.job_id,
                    error=target_dead_letter.reason,
                    dead_lettered=True,
                    result_snapshot=target_dead_letter.to_dict(),
                )
            elif any(item.status in {"failed", "blocked", "retrying"} for item in target_deliveries):
                terminal = target_deliveries[-1]
                self.outbox.mark_failed(
                    outbox_job.job_id,
                    error=terminal.reason,
                    dead_lettered=False,
                    result_snapshot=terminal.to_dict(),
                )
            else:
                self.outbox.mark_completed(
                    outbox_job.job_id,
                    result_snapshot=target_deliveries[-1].to_dict() if target_deliveries else None,
                )

        return {
            "event_id": event_id,
            "event_type": event_type,
            "targets_matched": len(targets),
            "deliveries_total": len(deliveries),
            "recorded_total": sum(1 for item in deliveries if item.status in {"recorded", "sent"}),
            "failed_total": sum(1 for item in deliveries if item.status in {"failed", "blocked", "retrying"}),
            "dead_lettered_total": len(dead_letters),
            "retry_attempts_total": sum(1 for item in deliveries if item.attempt_number > 1 or item.status == "retrying"),
            "outbox": self.outbox.summary(),
            "deliveries": [item.to_dict() for item in deliveries],
            "dead_letters": [item.to_dict() for item in dead_letters],
        }

    def list_deliveries(self, *, limit: int = 100, status: str | None = None) -> list[dict[str, object]]:
        records = self.records if status is None else [record for record in self.records if record.status == status]
        return [record.to_dict() for record in records[-limit:]][::-1]

    def list_dead_letters(self, *, limit: int = 100) -> list[dict[str, object]]:
        return [record.to_dict() for record in self.dead_letters[-limit:]][::-1]

    def list_outbox_jobs(self, *, limit: int = 100, status: str | None = None) -> list[dict[str, object]]:
        return self.outbox.list_jobs(limit=limit, status=status)

    def summary(self) -> dict[str, object]:
        latest = self.records[-1].to_dict() if self.records else None
        latest_dead_letter = self.dead_letters[-1].to_dict() if self.dead_letters else None
        outbox_summary = self.outbox.summary()
        return {
            "status": "active" if self.records else "idle",
            "deliveries_total": len(self.records),
            "failed_total": sum(1 for record in self.records if record.status in {"failed", "blocked", "retrying"}),
            "recorded_total": sum(1 for record in self.records if record.status in {"recorded", "sent"}),
            "retry_records_total": sum(1 for record in self.records if record.attempt_number > 1 or record.status == "retrying"),
            "dead_letters_total": len(self.dead_letters),
            "last_delivery_at": latest.get("attempted_at") if latest else None,
            "latest_delivery": latest,
            "latest_dead_letter": latest_dead_letter,
            "http_enabled": self.config.outbound_http_integrations_enabled,
            "log_path": str(self.log_path) if self.log_path is not None else None,
            "dead_letter_path": str(self.dead_letter_path) if self.dead_letter_path is not None else None,
            "persistence_backend": self.ledger.descriptor().backend,
            "coordination_backend": outbox_summary.get("backend"),
            "coordination_mode": outbox_summary.get("mode"),
            "outbox_total": outbox_summary.get("jobs_total", 0),
            "outbox_enqueued": outbox_summary.get("jobs_enqueued", 0),
            "outbox_processing": outbox_summary.get("jobs_processing", 0),
            "outbox_completed": outbox_summary.get("jobs_completed", 0),
            "outbox_failed": outbox_summary.get("jobs_failed", 0),
            "outbox_dead_lettered": outbox_summary.get("jobs_dead_lettered", 0),
            "latest_outbox_job": outbox_summary.get("latest_job"),
        }

    def health(self) -> dict[str, object]:
        return {
            **self.summary(),
            "configured_targets": self.registry.health().get("targets_total", 0),
            "active_targets": self.registry.health().get("active_targets", 0),
            "coordination": self.outbox.descriptor().to_dict(),
        }

    def _deliver(
        self,
        target: IntegrationTarget,
        envelope: dict[str, object],
        payload_bytes: bytes,
        payload_digest: str,
        *,
        queue_job_id: str | None = None,
    ) -> tuple[list[DeliveryRecord], DeadLetterRecord | None]:
        destination = target.endpoint_url or f"{target.delivery_mode}:{target.target_id}"
        max_attempts = max(1, target.max_attempts or self.config.integration_default_max_attempts)
        signing_policy = target.signing_policy or "none"

        if target.delivery_mode == "log_only":
            record = DeliveryRecord(
                delivery_id=f"dlv_{uuid4().hex[:12]}",
                event_id=str(envelope["event_id"]),
                event_type=str(envelope["event_type"]),
                target_id=target.target_id,
                target_name=target.name,
                category=target.category,
                delivery_mode=target.delivery_mode,
                status="recorded",
                attempted_at=utc_now(),
                source=str(envelope["source"]),
                requested_by=str(envelope["requested_by"]) if envelope.get("requested_by") else None,
                destination=destination,
                payload_digest=payload_digest,
                reason="Recorded in the outbound integration ledger (log-only mode).",
                duration_ms=0,
                attempt_number=1,
                max_attempts=1,
                signing_policy=signing_policy,
                queue_job_id=queue_job_id,
            )
            self._append_record(record)
            return [record], None

        if not self.config.outbound_http_integrations_enabled:
            record = self._build_terminal_record(
                target=target,
                envelope=envelope,
                payload_digest=payload_digest,
                destination=destination,
                status="blocked",
                reason="Outbound HTTP integrations are disabled in the current runtime.",
                attempt_number=1,
                max_attempts=max_attempts,
                signing_policy=signing_policy,
                duration_ms=0,
                queue_job_id=queue_job_id,
            )
            self._append_record(record)
            dead_letter = self._append_dead_letter(record)
            return [record], dead_letter

        if signing_policy == "hmac_sha256" and not target.secret:
            record = self._build_terminal_record(
                target=target,
                envelope=envelope,
                payload_digest=payload_digest,
                destination=destination,
                status="blocked",
                reason="Target requires HMAC signing but no secret is configured.",
                attempt_number=1,
                max_attempts=max_attempts,
                signing_policy=signing_policy,
                duration_ms=0,
                queue_job_id=queue_job_id,
            )
            self._append_record(record)
            dead_letter = self._append_dead_letter(record)
            return [record], dead_letter

        deliveries: list[DeliveryRecord] = []
        for attempt in range(1, max_attempts + 1):
            record = self._attempt_http_delivery(
                target=target,
                envelope=envelope,
                payload_bytes=payload_bytes,
                payload_digest=payload_digest,
                destination=destination,
                attempt_number=attempt,
                max_attempts=max_attempts,
                signing_policy=signing_policy,
                queue_job_id=queue_job_id,
            )
            deliveries.append(record)
            self._append_record(record)

            if record.status == "sent":
                return deliveries, None

            if attempt < max_attempts and target.retry_backoff_ms > 0:
                time.sleep(target.retry_backoff_ms / 1000.0)

        dead_letter = self._append_dead_letter(deliveries[-1])
        return deliveries, dead_letter

    def _attempt_http_delivery(
        self,
        *,
        target: IntegrationTarget,
        envelope: dict[str, object],
        payload_bytes: bytes,
        payload_digest: str,
        destination: str,
        attempt_number: int,
        max_attempts: int,
        signing_policy: str,
        queue_job_id: str | None,
    ) -> DeliveryRecord:
        started = perf_counter()
        attempted_at = utc_now()
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "SA-NOM-AI-Director/1.0",
            **target.headers,
        }
        if signing_policy == "hmac_sha256" and target.secret:
            signature = hmac.new(target.secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
            headers["X-SA-NOM-Signature"] = f"sha256={signature}"

        request = urllib.request.Request(
            url=target.endpoint_url,
            data=payload_bytes,
            headers=headers,
            method="POST",
        )
        try:
            context = None
            if not target.verify_tls and target.endpoint_url.lower().startswith("https://"):
                context = ssl._create_unverified_context()
            with urllib.request.urlopen(
                request,
                timeout=target.timeout_seconds or self.config.integration_delivery_timeout_seconds,
                context=context,
            ) as response:
                response_body = response.read(256).decode("utf-8", errors="replace")
                return DeliveryRecord(
                    delivery_id=f"dlv_{uuid4().hex[:12]}",
                    event_id=str(envelope["event_id"]),
                    event_type=str(envelope["event_type"]),
                    target_id=target.target_id,
                    target_name=target.name,
                    category=target.category,
                    delivery_mode=target.delivery_mode,
                    status="sent",
                    attempted_at=attempted_at,
                    source=str(envelope["source"]),
                    requested_by=str(envelope["requested_by"]) if envelope.get("requested_by") else None,
                    destination=destination,
                    payload_digest=payload_digest,
                    reason="HTTP delivery completed.",
                    duration_ms=int((perf_counter() - started) * 1000),
                    attempt_number=attempt_number,
                    max_attempts=max_attempts,
                    signing_policy=signing_policy,
                    queue_job_id=queue_job_id,
                    response_code=int(getattr(response, "status", 200)),
                    response_excerpt=response_body,
                )
        except (urllib.error.URLError, TimeoutError, ValueError) as error:
            status = "retrying" if attempt_number < max_attempts else "failed"
            return DeliveryRecord(
                delivery_id=f"dlv_{uuid4().hex[:12]}",
                event_id=str(envelope["event_id"]),
                event_type=str(envelope["event_type"]),
                target_id=target.target_id,
                target_name=target.name,
                category=target.category,
                delivery_mode=target.delivery_mode,
                status=status,
                attempted_at=attempted_at,
                source=str(envelope["source"]),
                requested_by=str(envelope["requested_by"]) if envelope.get("requested_by") else None,
                destination=destination,
                payload_digest=payload_digest,
                reason=str(error),
                duration_ms=int((perf_counter() - started) * 1000),
                attempt_number=attempt_number,
                max_attempts=max_attempts,
                signing_policy=signing_policy,
                queue_job_id=queue_job_id,
                response_excerpt=str(error),
            )

    def _build_terminal_record(
        self,
        *,
        target: IntegrationTarget,
        envelope: dict[str, object],
        payload_digest: str,
        destination: str,
        status: str,
        reason: str,
        attempt_number: int,
        max_attempts: int,
        signing_policy: str,
        duration_ms: int,
        queue_job_id: str | None = None,
    ) -> DeliveryRecord:
        return DeliveryRecord(
            delivery_id=f"dlv_{uuid4().hex[:12]}",
            event_id=str(envelope["event_id"]),
            event_type=str(envelope["event_type"]),
            target_id=target.target_id,
            target_name=target.name,
            category=target.category,
            delivery_mode=target.delivery_mode,
            status=status,
            attempted_at=utc_now(),
            source=str(envelope["source"]),
            requested_by=str(envelope["requested_by"]) if envelope.get("requested_by") else None,
            destination=destination,
            payload_digest=payload_digest,
            reason=reason,
            duration_ms=duration_ms,
            attempt_number=attempt_number,
            max_attempts=max_attempts,
            signing_policy=signing_policy,
            queue_job_id=queue_job_id,
        )

    def _append_record(self, record: DeliveryRecord) -> None:
        self.records.append(record)
        self.ledger.append(record.to_dict())

    def _append_dead_letter(self, record: DeliveryRecord) -> DeadLetterRecord:
        dead_letter = DeadLetterRecord(
            dead_letter_id=f"dead_{uuid4().hex[:12]}",
            event_id=record.event_id,
            event_type=record.event_type,
            target_id=record.target_id,
            target_name=record.target_name,
            category=record.category,
            source=record.source,
            requested_by=record.requested_by,
            destination=record.destination,
            payload_digest=record.payload_digest,
            final_status=record.status,
            attempts_used=record.attempt_number,
            max_attempts=record.max_attempts,
            signing_policy=record.signing_policy,
            dead_lettered_at=utc_now(),
            reason=record.reason,
            queue_job_id=record.queue_job_id,
        )
        self.dead_letters.append(dead_letter)
        self.dead_letter_ledger.append(dead_letter.to_dict())
        return dead_letter

    def _load_existing(self) -> None:
        for item in self.ledger.read_records():
            self.records.append(DeliveryRecord.from_dict(item))
        for item in self.dead_letter_ledger.read_records():
            self.dead_letters.append(DeadLetterRecord.from_dict(item))
