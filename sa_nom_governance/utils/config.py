import os
from dataclasses import dataclass, field
from pathlib import Path

from sa_nom_governance.utils.owner_identity import (
    DEFAULT_EXECUTIVE_OWNER_ID,
    DEFAULT_OWNER_DISPLAY_NAME,
    DEFAULT_OWNER_NAME,
    is_default_owner_alias,
)
from sa_nom_governance.utils.owner_registration import OwnerRegistration, load_owner_registration


@dataclass(slots=True)
class AppConfig:
    app_name: str = "SA-NOM AI Governance Suite"
    environment: str = field(default_factory=lambda: os.getenv("SANOM_ENV", "development"))
    base_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parents[2])
    resources_dir: Path = field(init=False)
    config_resources_dir: Path = field(init=False)
    pt_oss_resources_dir: Path = field(init=False)
    studio_resources_dir: Path = field(init=False)
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
    session_store_path: Path | None = field(init=False, default=None)
    role_private_studio_store_path: Path | None = field(init=False, default=None)
    human_ask_store_path: Path | None = field(init=False, default=None)
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
        self.resources_dir = self.base_dir / "resources"
        self.config_resources_dir = self.resources_dir / "config"
        self.pt_oss_resources_dir = self.resources_dir / "pt_oss"
        self.studio_resources_dir = self.resources_dir / "studio"
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
            self.session_store_path = self.runtime_dir / "runtime_session_store.json"
            self.role_private_studio_store_path = self.runtime_dir / "runtime_role_private_studio_store.json"
            self.human_ask_store_path = self.runtime_dir / "runtime_human_ask_store.json"
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

    def executive_owner_id(self) -> str:
        registration = self.owner_registration()
        return registration.executive_owner_id if registration is not None else DEFAULT_EXECUTIVE_OWNER_ID
