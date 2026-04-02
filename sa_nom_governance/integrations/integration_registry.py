import json
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path


DEFAULT_TARGETS = [
    {
        "target_id": "executive-ledger",
        "name": "Executive Integration Ledger",
        "category": "internal",
        "platform": "ledger",
        "kind": "webhook",
        "status": "active",
        "delivery_mode": "log_only",
        "endpoint_url": "log://executive-ledger",
        "subscribed_events": [
            "runtime.*",
            "role_private_studio.*",
            "governance.*",
        ],
        "notification_channels": ["dashboard"],
        "capability_tags": ["internal_ledger", "evidence"],
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
        "platform": "siem",
        "kind": "webhook",
        "status": "disabled",
        "delivery_mode": "http",
        "endpoint_url": "https://siem.example.local/intake",
        "subscribed_events": [
            "runtime.request.completed",
            "runtime.override.reviewed",
            "governance.evidence.exported",
        ],
        "notification_channels": ["siem", "webhook"],
        "capability_tags": ["security_ops", "alert_export"],
        "headers": {},
        "description": "Example outbound target for SIEM export.",
        "verify_tls": True,
        "timeout_seconds": 5,
        "max_attempts": 3,
        "retry_backoff_ms": 250,
        "signing_policy": "hmac_sha256",
    },
    {
        "target_id": "slack-bridge",
        "name": "Slack Alert Bridge",
        "category": "chatops",
        "platform": "slack",
        "kind": "webhook",
        "status": "disabled",
        "delivery_mode": "http",
        "endpoint_url": "https://hooks.slack.com/services/example",
        "subscribed_events": [
            "runtime.override.created",
            "runtime.recovery.required",
            "governance.notification.*",
        ],
        "notification_channels": ["slack", "webhook"],
        "capability_tags": ["chatops", "operator_alerting"],
        "headers": {},
        "description": "Example outbound target for Slack operator alerts.",
        "verify_tls": True,
        "timeout_seconds": 5,
        "max_attempts": 3,
        "retry_backoff_ms": 250,
        "signing_policy": "hmac_sha256",
    },
    {
        "target_id": "teams-bridge",
        "name": "Teams Alert Bridge",
        "category": "chatops",
        "platform": "teams",
        "kind": "webhook",
        "status": "disabled",
        "delivery_mode": "http",
        "endpoint_url": "https://outlook.office.com/webhook/example",
        "subscribed_events": [
            "runtime.override.created",
            "runtime.recovery.required",
            "governance.notification.*",
        ],
        "notification_channels": ["teams", "webhook"],
        "capability_tags": ["chatops", "operator_alerting"],
        "headers": {},
        "description": "Example outbound target for Microsoft Teams operator alerts.",
        "verify_tls": True,
        "timeout_seconds": 5,
        "max_attempts": 3,
        "retry_backoff_ms": 250,
        "signing_policy": "hmac_sha256",
    },
    {
        "target_id": "jira-service-desk",
        "name": "Jira Service Desk Bridge",
        "category": "ticketing",
        "platform": "jira",
        "kind": "webhook",
        "status": "disabled",
        "delivery_mode": "http",
        "endpoint_url": "https://jira.example.local/rest/api/2/issue",
        "subscribed_events": [
            "role_private_studio.request.reviewed",
            "role_private_studio.request.published",
            "runtime.recovery.required",
        ],
        "notification_channels": ["jira", "ticketing", "webhook"],
        "capability_tags": ["ticketing", "workflow_handoff"],
        "headers": {},
        "description": "Example outbound target for Jira ticketing workflows.",
        "verify_tls": True,
        "timeout_seconds": 5,
        "max_attempts": 3,
        "retry_backoff_ms": 250,
        "signing_policy": "hmac_sha256",
    },
    {
        "target_id": "servicenow-service-desk",
        "name": "ServiceNow Bridge",
        "category": "ticketing",
        "platform": "servicenow",
        "kind": "webhook",
        "status": "disabled",
        "delivery_mode": "http",
        "endpoint_url": "https://servicenow.example.local/api/now/table/incident",
        "subscribed_events": [
            "role_private_studio.request.reviewed",
            "role_private_studio.request.published",
            "runtime.recovery.required",
        ],
        "notification_channels": ["servicenow", "ticketing", "webhook"],
        "capability_tags": ["ticketing", "workflow_handoff"],
        "headers": {},
        "description": "Example outbound target for ServiceNow ticketing workflows.",
        "verify_tls": True,
        "timeout_seconds": 5,
        "max_attempts": 3,
        "retry_backoff_ms": 250,
        "signing_policy": "hmac_sha256",
    },
    {
        "target_id": "custom-webhook",
        "name": "Custom Webhook Bridge",
        "category": "custom",
        "platform": "custom_webhook",
        "kind": "webhook",
        "status": "disabled",
        "delivery_mode": "http",
        "endpoint_url": "https://example.local/sanom/webhook",
        "subscribed_events": ["*"],
        "notification_channels": ["webhook"],
        "capability_tags": ["custom", "extensibility"],
        "headers": {},
        "description": "Example outbound target for custom governed integrations.",
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
    platform: str = "custom"
    kind: str = "webhook"
    status: str = "disabled"
    delivery_mode: str = "log_only"
    endpoint_url: str = ""
    subscribed_events: list[str] = field(default_factory=lambda: ["*"])
    notification_channels: list[str] = field(default_factory=list)
    capability_tags: list[str] = field(default_factory=list)
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
        delivery_mode = str(payload.get("delivery_mode") or "log_only").strip() or "log_only"
        category = str(payload.get("category") or "custom").strip() or "custom"
        platform = str(payload.get("platform") or category or "custom").strip() or "custom"
        notification_channels = payload.get("notification_channels")
        capability_tags = payload.get("capability_tags")
        if not isinstance(notification_channels, list):
            notification_channels = cls._default_notification_channels(category=category, platform=platform, delivery_mode=delivery_mode)
        if not isinstance(capability_tags, list):
            capability_tags = cls._default_capability_tags(category=category, platform=platform, delivery_mode=delivery_mode)
        return cls(
            target_id=str(payload.get("target_id") or "").strip(),
            name=str(payload.get("name") or payload.get("target_id") or "").strip(),
            category=category,
            platform=platform,
            kind=str(payload.get("kind") or "webhook").strip() or "webhook",
            status=str(payload.get("status") or "disabled").strip() or "disabled",
            delivery_mode=delivery_mode,
            endpoint_url=str(payload.get("endpoint_url") or "").strip(),
            subscribed_events=[str(item).strip() for item in payload.get("subscribed_events", ["*"]) if str(item).strip()],
            notification_channels=[str(item).strip() for item in notification_channels if str(item).strip()],
            capability_tags=[str(item).strip() for item in capability_tags if str(item).strip()],
            headers={str(key): str(value) for key, value in dict(payload.get("headers") or {}).items()},
            description=str(payload.get("description") or "").strip(),
            verify_tls=bool(payload.get("verify_tls", True)),
            timeout_seconds=max(1, int(payload.get("timeout_seconds") or 5)),
            max_attempts=max(1, int(payload.get("max_attempts") or 1)),
            retry_backoff_ms=max(0, int(payload.get("retry_backoff_ms") or 0)),
            signing_policy=str(payload.get("signing_policy") or ("hmac_sha256" if payload.get("secret") else "none")).strip() or "none",
            secret=str(payload["secret"]).strip() if payload.get("secret") else None,
        )

    @staticmethod
    def _default_notification_channels(*, category: str, platform: str, delivery_mode: str) -> list[str]:
        if delivery_mode == "log_only":
            return ["dashboard"]
        defaults = {
            "siem": ["siem", "webhook"],
            "slack": ["slack", "webhook"],
            "teams": ["teams", "webhook"],
            "jira": ["jira", "ticketing", "webhook"],
            "servicenow": ["servicenow", "ticketing", "webhook"],
            "ticketing": ["ticketing", "webhook"],
        }
        return list(defaults.get(platform, defaults.get(category, ["webhook"])))

    @staticmethod
    def _default_capability_tags(*, category: str, platform: str, delivery_mode: str) -> list[str]:
        tags = [category, platform]
        if delivery_mode == "http":
            tags.append("http_delivery")
        if delivery_mode == "log_only":
            tags.append("log_only")
        return [tag for tag in tags if tag and tag != "custom"] or ["custom"]

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
            "platform": self.platform,
            "kind": self.kind,
            "status": self.status,
            "delivery_mode": self.delivery_mode,
            "endpoint_url": self.endpoint_url,
            "subscribed_events": list(self.subscribed_events),
            "notification_channels": list(self.notification_channels),
            "capability_tags": list(self.capability_tags),
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

    def platforms(self, *, active_only: bool = False) -> list[str]:
        return sorted({target.platform for target in self.targets if target.platform and (not active_only or target.status == "active")})

    def notification_channels(self, *, active_only: bool = False) -> list[str]:
        channels = {
            channel
            for target in self.targets
            if not active_only or target.status == "active"
            for channel in target.notification_channels
            if channel
        }
        return sorted(channels)

    def health(self) -> dict[str, object]:
        return {
            "status": "configured" if self.targets else "empty",
            "targets_total": len(self.targets),
            "active_targets": sum(1 for target in self.targets if target.status == "active"),
            "disabled_targets": sum(1 for target in self.targets if target.status != "active"),
            "http_targets": sum(1 for target in self.targets if target.delivery_mode == "http"),
            "log_only_targets": sum(1 for target in self.targets if target.delivery_mode == "log_only"),
            "signed_targets": sum(1 for target in self.targets if target.signing_policy != "none"),
            "chatops_targets": sum(1 for target in self.targets if target.category == "chatops"),
            "ticketing_targets": sum(1 for target in self.targets if target.category == "ticketing"),
            "siem_targets": sum(1 for target in self.targets if target.category == "siem"),
            "categories": self.categories(),
            "platforms_configured": self.platforms(),
            "platforms_active": self.platforms(active_only=True),
            "notification_channels_configured": self.notification_channels(),
            "notification_channels_active": self.notification_channels(active_only=True),
            "path": str(self.path) if self.path is not None else None,
        }

    def snapshot(self) -> dict[str, object]:
        return {
            "summary": self.health(),
            "targets": [target.to_dict() for target in self.targets],
        }
