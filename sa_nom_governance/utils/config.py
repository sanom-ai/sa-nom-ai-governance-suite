import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from sa_nom_governance.utils.owner_identity import (
    DEFAULT_EXECUTIVE_OWNER_ID,
    DEFAULT_OWNER_DISPLAY_NAME,
    DEFAULT_OWNER_NAME,
    is_default_owner_alias,
)
from sa_nom_governance.utils.owner_registration import OwnerRegistration, load_owner_registration

PACKAGE_DIR = Path(__file__).resolve().parents[1]
SOURCE_TREE_ROOT = PACKAGE_DIR.parent
BUNDLED_RESOURCES_SUBDIR = "_bundled_resources"


def bundled_resources_dir() -> Path:
    packaged_dir = PACKAGE_DIR / BUNDLED_RESOURCES_SUBDIR
    if packaged_dir.exists():
        return packaged_dir
    return SOURCE_TREE_ROOT / "resources"


def _package_base_dir() -> Path:
    configured_home = os.getenv("SANOM_HOME", "").strip()
    if configured_home:
        configured_path = Path(configured_home)
        return configured_path if configured_path.is_absolute() else (Path.cwd() / configured_path)
    source_resources_dir = SOURCE_TREE_ROOT / "resources"
    if (SOURCE_TREE_ROOT / "pyproject.toml").exists() and source_resources_dir.exists():
        return SOURCE_TREE_ROOT
    return Path.cwd()


@dataclass(slots=True)
class AppConfig:
    app_name: str = "SA-NOM AI Governance Suite"
    environment: str = field(default_factory=lambda: os.getenv("SANOM_ENV", "development"))
    base_dir: Path = field(default_factory=_package_base_dir)
    bundled_resources_root: Path = field(init=False)
    resources_dir: Path = field(init=False)
    config_resources_dir: Path = field(init=False)
    pt_oss_resources_dir: Path = field(init=False)
    studio_resources_dir: Path = field(init=False)
    alignment_resources_dir: Path = field(init=False)
    alignment_default_region: str = field(default_factory=lambda: os.getenv("SANOM_ALIGNMENT_DEFAULT_REGION", "eu").strip())
    persist_runtime: bool = True
    api_token: str | None = field(default_factory=lambda: os.getenv("SANOM_API_TOKEN"))
    server_host: str = field(default_factory=lambda: os.getenv("SANOM_SERVER_HOST", "127.0.0.1"))
    server_port: int = field(default_factory=lambda: int(os.getenv("SANOM_SERVER_PORT", "8080")))
    server_public_base_url: str | None = field(default_factory=lambda: os.getenv("SANOM_SERVER_PUBLIC_BASE_URL"))
    strict_startup_validation: bool = field(default_factory=lambda: os.getenv("SANOM_STRICT_STARTUP_VALIDATION", "auto").strip().lower() in {"1", "true", "yes", "auto"})
    access_profiles_require_hashes: bool = field(default_factory=lambda: os.getenv("SANOM_ACCESS_PROFILES_REQUIRE_HASHES", "true").strip().lower() not in {"0", "false", "no"})
    session_ttl_minutes: int = field(default_factory=lambda: int(os.getenv("SANOM_SESSION_TTL_MINUTES", "720")))
    session_idle_timeout_minutes: int = field(default_factory=lambda: int(os.getenv("SANOM_SESSION_IDLE_TIMEOUT_MINUTES", "60")))
    trusted_registry_signing_key: str | None = field(default_factory=lambda: os.getenv("SANOM_TRUSTED_REGISTRY_KEY"))
    trusted_registry_key_id: str = field(default_factory=lambda: os.getenv("SANOM_TRUSTED_REGISTRY_KEY_ID", "SANOM_DEV_REGISTRY"))
    trusted_registry_signed_by: str | None = field(default_factory=lambda: os.getenv("SANOM_TRUSTED_REGISTRY_SIGNED_BY"))
    trusted_registry_signature_required: bool = field(default_factory=lambda: os.getenv("SANOM_TRUSTED_REGISTRY_REQUIRE_SIGNATURE", "true").strip().lower() not in {"0", "false", "no"})
    retention_audit_days: int = field(default_factory=lambda: int(os.getenv("SANOM_RETENTION_AUDIT_DAYS", "2555")))
    retention_override_days: int = field(default_factory=lambda: int(os.getenv("SANOM_RETENTION_OVERRIDE_DAYS", "2555")))
    retention_lock_days: int = field(default_factory=lambda: int(os.getenv("SANOM_RETENTION_LOCK_DAYS", "30")))
    retention_consistency_days: int = field(default_factory=lambda: int(os.getenv("SANOM_RETENTION_CONSISTENCY_DAYS", "365")))
    retention_session_days: int = field(default_factory=lambda: int(os.getenv("SANOM_RETENTION_SESSION_DAYS", "90")))
    retention_role_private_studio_days: int = field(default_factory=lambda: int(os.getenv("SANOM_RETENTION_ROLE_PRIVATE_STUDIO_DAYS", "2555")))
    retention_human_ask_days: int = field(default_factory=lambda: int(os.getenv("SANOM_RETENTION_HUMAN_ASK_DAYS", "365")))
    human_ask_confidence_threshold: float = field(default_factory=lambda: max(0.05, min(float(os.getenv("SANOM_HUMAN_ASK_CONFIDENCE_THRESHOLD", "0.72")), 0.99)))
    human_ask_freshness_warning_hours: int = field(default_factory=lambda: max(1, int(os.getenv("SANOM_HUMAN_ASK_FRESHNESS_WARNING_HOURS", "24"))))
    human_ask_freshness_stale_hours: int = field(default_factory=lambda: max(1, int(os.getenv("SANOM_HUMAN_ASK_FRESHNESS_STALE_HOURS", "168"))))
    operator_alert_warning_hours: int = field(default_factory=lambda: max(1, int(os.getenv("SANOM_OPERATOR_ALERT_WARNING_HOURS", "24"))))
    operator_alert_critical_hours: int = field(default_factory=lambda: max(1, int(os.getenv("SANOM_OPERATOR_ALERT_CRITICAL_HOURS", "168"))))
    operator_alert_stale_hours: int = field(default_factory=lambda: max(1, int(os.getenv("SANOM_OPERATOR_ALERT_STALE_HOURS", "720"))))
    operator_alert_backlog_warning_total: int = field(default_factory=lambda: max(1, int(os.getenv("SANOM_OPERATOR_ALERT_BACKLOG_WARNING_TOTAL", "3"))))
    operator_alert_backlog_critical_total: int = field(default_factory=lambda: max(1, int(os.getenv("SANOM_OPERATOR_ALERT_BACKLOG_CRITICAL_TOTAL", "10"))))
    operator_notifications_enabled: bool = field(default_factory=lambda: os.getenv("SANOM_OPERATOR_NOTIFICATIONS_ENABLED", "true").strip().lower() not in {"0", "false", "no"})
    operator_notification_channels: str = field(default_factory=lambda: os.getenv("SANOM_OPERATOR_NOTIFICATION_CHANNELS", "dashboard,email,webhook").strip())
    operator_notification_warning_channels: str = field(default_factory=lambda: os.getenv("SANOM_OPERATOR_NOTIFICATION_WARNING_CHANNELS", "dashboard").strip())
    operator_notification_critical_channels: str = field(default_factory=lambda: os.getenv("SANOM_OPERATOR_NOTIFICATION_CRITICAL_CHANNELS", "dashboard,email").strip())
    operator_notification_stale_channels: str = field(default_factory=lambda: os.getenv("SANOM_OPERATOR_NOTIFICATION_STALE_CHANNELS", "dashboard,email,webhook").strip())
    operator_notification_digest_hours: int = field(default_factory=lambda: max(1, int(os.getenv("SANOM_OPERATOR_NOTIFICATION_DIGEST_HOURS", "24"))))
    operator_notification_realert_hours: int = field(default_factory=lambda: max(1, int(os.getenv("SANOM_OPERATOR_NOTIFICATION_REALERT_HOURS", "4"))))
    persistence_backend: str = field(default_factory=lambda: os.getenv("SANOM_PERSISTENCE_BACKEND", "file").strip().lower())
    postgres_dsn: str | None = field(default_factory=lambda: os.getenv("SANOM_POSTGRES_DSN"))
    postgres_schema: str = field(default_factory=lambda: os.getenv("SANOM_POSTGRES_SCHEMA", "public"))
    postgres_native_enabled: bool = field(default_factory=lambda: os.getenv("SANOM_POSTGRES_NATIVE_ENABLED", "false").strip().lower() in {"1", "true", "yes"})
    postgres_connect_timeout_seconds: int = field(default_factory=lambda: max(1, int(os.getenv("SANOM_POSTGRES_CONNECT_TIMEOUT_SECONDS", "5"))))
    coordination_backend: str = field(default_factory=lambda: os.getenv("SANOM_COORDINATION_BACKEND", "file").strip().lower())
    redis_url: str | None = field(default_factory=lambda: os.getenv("SANOM_REDIS_URL"))
    redis_native_enabled: bool = field(default_factory=lambda: os.getenv("SANOM_REDIS_NATIVE_ENABLED", "false").strip().lower() in {"1", "true", "yes"})
    redis_queue_namespace: str = field(default_factory=lambda: os.getenv("SANOM_REDIS_QUEUE_NAMESPACE", "sanom"))
    redis_connect_timeout_seconds: int = field(default_factory=lambda: max(1, int(os.getenv("SANOM_REDIS_CONNECT_TIMEOUT_SECONDS", "5"))))
    outbound_http_integrations_enabled: bool = field(default_factory=lambda: os.getenv("SANOM_OUTBOUND_HTTP_INTEGRATIONS_ENABLED", "false").strip().lower() in {"1", "true", "yes"})
    integration_delivery_timeout_seconds: int = field(default_factory=lambda: int(os.getenv("SANOM_INTEGRATION_DELIVERY_TIMEOUT_SECONDS", "5")))
    integration_default_max_attempts: int = field(default_factory=lambda: max(1, int(os.getenv("SANOM_INTEGRATION_DEFAULT_MAX_ATTEMPTS", "3"))))
    integration_retry_backoff_ms: int = field(default_factory=lambda: max(0, int(os.getenv("SANOM_INTEGRATION_RETRY_BACKOFF_MS", "250"))))
    default_model_provider: str | None = field(default_factory=lambda: os.getenv("SANOM_MODEL_PROVIDER_DEFAULT"))
    model_provider_timeout_seconds: int = field(default_factory=lambda: max(1, int(os.getenv("SANOM_MODEL_PROVIDER_TIMEOUT_SECONDS", "15"))))
    openai_api_key: str | None = field(default_factory=lambda: os.getenv("SANOM_OPENAI_API_KEY"))
    openai_base_url: str = field(default_factory=lambda: os.getenv("SANOM_OPENAI_BASE_URL", "https://api.openai.com/v1").strip())
    openai_model: str = field(default_factory=lambda: os.getenv("SANOM_OPENAI_MODEL", "").strip())
    anthropic_api_key: str | None = field(default_factory=lambda: os.getenv("SANOM_ANTHROPIC_API_KEY"))
    anthropic_base_url: str = field(default_factory=lambda: os.getenv("SANOM_ANTHROPIC_BASE_URL", "https://api.anthropic.com").strip())
    anthropic_version: str = field(default_factory=lambda: os.getenv("SANOM_ANTHROPIC_VERSION", "2023-06-01").strip())
    anthropic_model: str = field(default_factory=lambda: os.getenv("SANOM_ANTHROPIC_MODEL", "").strip())
    ollama_base_url: str = field(default_factory=lambda: os.getenv("SANOM_OLLAMA_BASE_URL", "http://localhost:11434").strip())
    ollama_model: str = field(default_factory=lambda: os.getenv("SANOM_OLLAMA_MODEL", "").strip())
    runtime_dir: Path = field(init=False)
    support_dir: Path = field(init=False)
    review_dir: Path = field(init=False)
    owner_registration_path: Path | None = field(init=False, default=None)
    pt_oss_foundation_path: Path | None = field(init=False, default=None)
    role_private_studio_template_path: Path | None = field(init=False, default=None)
    role_private_studio_examples_path: Path | None = field(init=False, default=None)
    access_profiles_path: Path | None = field(init=False, default=None)
    trusted_registry_manifest_path: Path | None = field(init=False, default=None)
    trusted_registry_cache_path: Path | None = field(init=False, default=None)
    role_transition_matrix_path: Path | None = field(init=False, default=None)
    compliance_frameworks_path: Path | None = field(init=False, default=None)
    integration_targets_path: Path | None = field(init=False, default=None)
    roles_dir: Path = field(init=False)
    dictionaries_dir: Path = field(init=False)
    audit_log_path: Path | None = field(init=False, default=None)
    override_store_path: Path | None = field(init=False, default=None)
    lock_store_path: Path | None = field(init=False, default=None)
    consistency_store_path: Path | None = field(init=False, default=None)
    workflow_state_store_path: Path | None = field(init=False, default=None)
    runtime_recovery_store_path: Path | None = field(init=False, default=None)
    runtime_dead_letter_path: Path | None = field(init=False, default=None)
    session_store_path: Path | None = field(init=False, default=None)
    role_private_studio_store_path: Path | None = field(init=False, default=None)
    human_ask_store_path: Path | None = field(init=False, default=None)
    document_store_path: Path | None = field(init=False, default=None)
    action_runtime_store_path: Path | None = field(init=False, default=None)
    startup_smoke_report_path: Path | None = field(init=False, default=None)
    legal_hold_path: Path | None = field(init=False, default=None)
    integration_delivery_log_path: Path | None = field(init=False, default=None)
    integration_dead_letter_log_path: Path | None = field(init=False, default=None)
    integration_outbox_path: Path | None = field(init=False, default=None)
    retention_archive_dir: Path = field(init=False)
    runtime_backup_dir: Path = field(init=False)
    runtime_evidence_dir: Path = field(init=False)
    _owner_registration_cache: OwnerRegistration | None = field(init=False, default=None)
    _owner_registration_loaded: bool = field(init=False, default=False)

    def __post_init__(self) -> None:
        self.bundled_resources_root = bundled_resources_dir()
        self.resources_dir = self.base_dir / "resources"
        self.config_resources_dir = self.resources_dir / "config"
        self.pt_oss_resources_dir = self.resources_dir / "pt_oss"
        self.studio_resources_dir = self.resources_dir / "studio"
        alignment_dir = os.getenv("SANOM_ALIGNMENT_RESOURCES_DIR")
        if alignment_dir:
            alignment_path = Path(alignment_dir)
            self.alignment_resources_dir = alignment_path if alignment_path.is_absolute() else self.base_dir / alignment_path
        else:
            self.alignment_resources_dir = self.resources_dir / "alignment"
        self.alignment_default_region = self.alignment_default_region.strip() or "eu"
        self.roles_dir = self.resources_dir / "roles"
        self.dictionaries_dir = self.roles_dir
        self.runtime_dir = self.base_dir / "_runtime"
        self.support_dir = self.base_dir / "_support"
        self.review_dir = self.base_dir / "_review"
        self.resources_dir.mkdir(parents=True, exist_ok=True)
        self.config_resources_dir.mkdir(parents=True, exist_ok=True)
        self.pt_oss_resources_dir.mkdir(parents=True, exist_ok=True)
        self.studio_resources_dir.mkdir(parents=True, exist_ok=True)
        self.roles_dir.mkdir(parents=True, exist_ok=True)
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.support_dir.mkdir(parents=True, exist_ok=True)
        self.review_dir.mkdir(parents=True, exist_ok=True)
        self._seed_public_resources_from_bundle()
        self.owner_registration_path = self.runtime_dir / "owner_registration.json"
        self.access_profiles_path = self.runtime_dir / "access_profiles.json"
        self.pt_oss_foundation_path = self.pt_oss_resources_dir / "pt_oss_foundation.json"
        self.role_private_studio_template_path = self.studio_resources_dir / "role_private_studio_templates.json"
        self.role_private_studio_examples_path = self.studio_resources_dir / "role_private_studio_examples.json"
        self.trusted_registry_manifest_path = self.config_resources_dir / "trusted_registry_manifest.json"
        self.trusted_registry_cache_path = self.runtime_dir / "trusted_registry_cache.json"
        self.role_transition_matrix_path = self.config_resources_dir / "role_transition_matrix.json"
        self.compliance_frameworks_path = self.config_resources_dir / "compliance_frameworks.json"
        self.integration_targets_path = self.config_resources_dir / "integration_targets.json"
        self.legal_hold_path = self.runtime_dir / "runtime_legal_holds.json"

        archive_dir = os.getenv("SANOM_RETENTION_ARCHIVE_DIR")
        if archive_dir:
            archive_path = Path(archive_dir)
            self.retention_archive_dir = archive_path if archive_path.is_absolute() else self.base_dir / archive_path
        else:
            self.retention_archive_dir = self.runtime_dir / "runtime_archive"

        self.runtime_backup_dir = self.runtime_dir / "runtime_backups"
        self.runtime_evidence_dir = self.runtime_dir / "runtime_evidence_packs"

        if self.persist_runtime:
            self.audit_log_path = self.runtime_dir / "runtime_audit_log.jsonl"
            self.override_store_path = self.runtime_dir / "runtime_override_store.json"
            self.lock_store_path = self.runtime_dir / "runtime_lock_store.json"
            self.consistency_store_path = self.runtime_dir / "runtime_consistency_store.json"
            self.workflow_state_store_path = self.runtime_dir / "runtime_workflow_state_store.json"
            self.runtime_recovery_store_path = self.runtime_dir / "runtime_recovery_store.json"
            self.runtime_dead_letter_path = self.runtime_dir / "runtime_dead_letter_log.jsonl"
            self.session_store_path = self.runtime_dir / "runtime_session_store.json"
            self.role_private_studio_store_path = self.runtime_dir / "runtime_role_private_studio_store.json"
            self.human_ask_store_path = self.runtime_dir / "runtime_human_ask_store.json"
            self.document_store_path = self.runtime_dir / "runtime_document_store.json"
            self.action_runtime_store_path = self.runtime_dir / "runtime_action_store.json"
            self.startup_smoke_report_path = self.runtime_dir / "runtime_startup_smoke.json"
            self.integration_delivery_log_path = self.runtime_dir / "runtime_integration_delivery_log.jsonl"
            self.integration_dead_letter_log_path = self.runtime_dir / "runtime_integration_dead_letters.jsonl"
            self.integration_outbox_path = self.runtime_dir / "runtime_integration_outbox.json"
        if self.api_token is None and self.environment == "development":
            self.api_token = "sanom-dev-token"
        if self.trusted_registry_signing_key is None and self.environment == "development":
            self.trusted_registry_signing_key = "sanom-dev-registry-key"
        if not self.trusted_registry_signed_by:
            registration = self.owner_registration()
            self.trusted_registry_signed_by = (
                registration.trusted_registry_signed_by if registration is not None else DEFAULT_EXECUTIVE_OWNER_ID
            )
        if os.getenv("SANOM_STRICT_STARTUP_VALIDATION", "auto").strip().lower() == "auto":
            self.strict_startup_validation = self.environment != "development"

    def _seed_public_resources_from_bundle(self) -> None:
        source_root = self.bundled_resources_root
        if not source_root.exists():
            return
        try:
            if source_root.resolve() == self.resources_dir.resolve():
                return
        except OSError:
            pass
        for source_path in sorted(path for path in source_root.rglob("*") if path.is_file()):
            relative_path = source_path.relative_to(source_root)
            target_path = self.resources_dir / relative_path
            if target_path.exists():
                continue
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)

    def effective_access_profiles_path(self) -> Path | None:
        if self.access_profiles_path is not None and self.access_profiles_path.exists():
            return self.access_profiles_path
        legacy_path = self.base_dir / "access_profiles.json"
        if legacy_path.exists():
            return legacy_path
        return self.access_profiles_path

    def effective_owner_registration_path(self) -> Path | None:
        if self.owner_registration_path is not None and self.owner_registration_path.exists():
            return self.owner_registration_path
        legacy_path = self.base_dir / "owner_registration.json"
        if legacy_path.exists():
            return legacy_path
        return self.owner_registration_path

    def owner_registration(self) -> OwnerRegistration | None:
        path = self.effective_owner_registration_path()
        should_reload = (
            not self._owner_registration_loaded
            or (self._owner_registration_cache is None and path is not None and path.exists())
        )
        if should_reload:
            self._owner_registration_cache = load_owner_registration(path)
            self._owner_registration_loaded = True
            if self._owner_registration_cache is not None and is_default_owner_alias(
                self.trusted_registry_signed_by
            ):
                self.trusted_registry_signed_by = self._owner_registration_cache.trusted_registry_signed_by
        return self._owner_registration_cache

    def reload_owner_registration(self) -> OwnerRegistration | None:
        self._owner_registration_loaded = False
        self._owner_registration_cache = None
        return self.owner_registration()

    def organization_name(self) -> str | None:
        registration = self.owner_registration()
        return registration.organization_name if registration is not None else None

    def organization_id(self) -> str | None:
        registration = self.owner_registration()
        return registration.organization_id if registration is not None else None

    def deployment_mode(self) -> str:
        registration = self.owner_registration()
        return registration.deployment_mode if registration is not None else "private"

    def owner_name(self) -> str:
        registration = self.owner_registration()
        return registration.owner_name if registration is not None else DEFAULT_OWNER_NAME

    def owner_display_name(self) -> str:
        registration = self.owner_registration()
        return registration.owner_display_name if registration is not None else DEFAULT_OWNER_DISPLAY_NAME

    def operator_alert_policy(self) -> dict[str, object]:
        warning_hours = max(1, int(self.operator_alert_warning_hours))
        critical_hours = max(warning_hours, int(self.operator_alert_critical_hours))
        stale_hours = max(critical_hours, int(self.operator_alert_stale_hours))
        backlog_warning_total = max(1, int(self.operator_alert_backlog_warning_total))
        backlog_critical_total = max(backlog_warning_total, int(self.operator_alert_backlog_critical_total))

        def _split_channels(value: str) -> list[str]:
            channels = [item.strip().lower() for item in str(value or '').split(',') if item.strip()]
            return channels or ['dashboard']

        default_channels = _split_channels(self.operator_notification_channels)
        warning_channels = _split_channels(self.operator_notification_warning_channels)
        critical_channels = _split_channels(self.operator_notification_critical_channels)
        stale_channels = _split_channels(self.operator_notification_stale_channels)

        return {
            "aging": {
                "warning_hours": warning_hours,
                "critical_hours": critical_hours,
                "stale_hours": stale_hours,
            },
            "backlog": {
                "warning_total": backlog_warning_total,
                "critical_total": backlog_critical_total,
            },
            "applies_to": [
                "pending_overrides",
                "waiting_human_sessions",
                "blocked_workflows",
                "recovery_backlog",
                "dead_letters",
            ],
            "notification": {
                "enabled": bool(self.operator_notifications_enabled),
                "default_channels": default_channels,
                "severity_channels": {
                    "warning": warning_channels,
                    "critical": critical_channels,
                    "stale": stale_channels,
                },
                "cadence": {
                    "digest_hours": max(1, int(self.operator_notification_digest_hours)),
                    "realert_hours": max(1, int(self.operator_notification_realert_hours)),
                },
            },
        }

    def executive_owner_id(self) -> str:
        registration = self.owner_registration()
        return registration.executive_owner_id if registration is not None else DEFAULT_EXECUTIVE_OWNER_ID
