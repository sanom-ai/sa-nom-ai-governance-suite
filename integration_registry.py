import json
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path


DEFAULT_TARGETS = [
    {
        "target_id": "executive-ledger",
        "name": "Executive Integration Ledger",
        "category": "internal",
        "kind": "webhook",
        "status": "active",
        "delivery_mode": "log_only",
        "endpoint_url": "log://executive-ledger",
        "subscribed_events": [
            "runtime.*",
            "role_private_studio.*",
            "governance.*",
        ],
        "headers": {},
        "description": "Default log-only outbound ledger for enterprise integration events.",
        "verify_tls": True,
        "timeout_seconds": 5,
        "max_attempts": 1,
        "retry_backoff_ms": 0,
        "signing_policy": "none",
    },
    {
        "target_id": "siem-bridge",
        "name": "SIEM Bridge",
        "category": "siem",
        "kind": "webhook",
        "status": "disabled",
        "delivery_mode": "http",
        "endpoint_url": "https://siem.example.local/intake",
        "subscribed_events": [
            "runtime.request.completed",
            "runtime.override.reviewed",
            "governance.evidence.exported",
        ],
        "headers": {},
        "description": "Example outbound target for SIEM export.",
        "verify_tls": True,
        "timeout_seconds": 5,
        "max_attempts": 3,
        "retry_backoff_ms": 250,
        "signing_policy": "hmac_sha256",
    },
    {
        "target_id": "service-desk",
        "name": "Service Desk Bridge",
        "category": "ticketing",
        "kind": "webhook",
        "status": "disabled",
        "delivery_mode": "http",
        "endpoint_url": "https://tickets.example.local/webhook",
        "subscribed_events": [
            "role_private_studio.request.reviewed",
            "role_private_studio.request.published",
        ],
        "headers": {},
        "description": "Example outbound target for Jira or ServiceNow workflows.",
        "verify_tls": True,
        "timeout_seconds": 5,
        "max_attempts": 3,
        "retry_backoff_ms": 250,
        "signing_policy": "hmac_sha256",
    },
]


@dataclass(slots=True)
class IntegrationTarget:
    target_id: str
    name: str
    category: str = "custom"
    kind: str = "webhook"
    status: str = "disabled"
    delivery_mode: str = "log_only"
    endpoint_url: str = ""
    subscribed_events: list[str] = field(default_factory=lambda: ["*"])
    headers: dict[str, str] = field(default_factory=dict)
    description: str = ""
    verify_tls: bool = True
    timeout_seconds: int = 5
    max_attempts: int = 1
    retry_backoff_ms: int = 0
    signing_policy: str = "none"
    secret: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "IntegrationTarget":
        return cls(
            target_id=str(payload.get("target_id") or "").strip(),
            name=str(payload.get("name") or payload.get("target_id") or "").strip(),
            category=str(payload.get("category") or "custom").strip() or "custom",
            kind=str(payload.get("kind") or "webhook").strip() or "webhook",
            status=str(payload.get("status") or "disabled").strip() or "disabled",
            delivery_mode=str(payload.get("delivery_mode") or "log_only").strip() or "log_only",
            endpoint_url=str(payload.get("endpoint_url") or "").strip(),
            subscribed_events=[str(item).strip() for item in payload.get("subscribed_events", ["*"]) if str(item).strip()],
            headers={str(key): str(value) for key, value in dict(payload.get("headers") or {}).items()},
            description=str(payload.get("description") or "").strip(),
            verify_tls=bool(payload.get("verify_tls", True)),
            timeout_seconds=max(1, int(payload.get("timeout_seconds") or 5)),
            max_attempts=max(1, int(payload.get("max_attempts") or 1)),
            retry_backoff_ms=max(0, int(payload.get("retry_backoff_ms") or 0)),
            signing_policy=str(payload.get("signing_policy") or ("hmac_sha256" if payload.get("secret") else "none")).strip() or "none",
            secret=str(payload["secret"]).strip() if payload.get("secret") else None,
        )

    def matches(self, event_type: str) -> bool:
        if self.status != "active":
            return False
        patterns = self.subscribed_events or ["*"]
        return any(fnmatch(event_type, pattern) for pattern in patterns)

    def to_dict(self, *, include_secret: bool = False) -> dict[str, object]:
        data = {
            "target_id": self.target_id,
            "name": self.name,
            "category": self.category,
            "kind": self.kind,
            "status": self.status,
            "delivery_mode": self.delivery_mode,
            "endpoint_url": self.endpoint_url,
            "subscribed_events": list(self.subscribed_events),
            "headers": dict(self.headers),
            "description": self.description,
            "verify_tls": self.verify_tls,
            "timeout_seconds": self.timeout_seconds,
            "max_attempts": self.max_attempts,
            "retry_backoff_ms": self.retry_backoff_ms,
            "signing_policy": self.signing_policy,
        }
        if include_secret and self.secret:
            data["secret"] = self.secret
        return data


class IntegrationRegistry:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self.targets: list[IntegrationTarget] = []
        self.reload()

    def reload(self) -> None:
        payload = DEFAULT_TARGETS
        if self.path is not None and self.path.exists():
            payload = json.loads(self.path.read_text(encoding="utf-8-sig"))
        self.targets = [IntegrationTarget.from_dict(item) for item in payload if isinstance(item, dict) and item.get("target_id")]

    def list_targets(self, *, status: str | None = None) -> list[IntegrationTarget]:
        if status is None:
            return list(self.targets)
        return [target for target in self.targets if target.status == status]

    def matching_targets(self, event_type: str) -> list[IntegrationTarget]:
        return [target for target in self.targets if target.matches(event_type)]

    def categories(self) -> list[str]:
        return sorted({target.category for target in self.targets})

    def health(self) -> dict[str, object]:
        return {
            "status": "configured" if self.targets else "empty",
            "targets_total": len(self.targets),
            "active_targets": sum(1 for target in self.targets if target.status == "active"),
            "disabled_targets": sum(1 for target in self.targets if target.status != "active"),
            "http_targets": sum(1 for target in self.targets if target.delivery_mode == "http"),
            "log_only_targets": sum(1 for target in self.targets if target.delivery_mode == "log_only"),
            "signed_targets": sum(1 for target in self.targets if target.signing_policy != "none"),
            "categories": self.categories(),
            "path": str(self.path) if self.path is not None else None,
        }

    def snapshot(self) -> dict[str, object]:
        return {
            "summary": self.health(),
            "targets": [target.to_dict() for target in self.targets],
        }
