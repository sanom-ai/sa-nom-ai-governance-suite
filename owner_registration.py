import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_owner_id(value: str) -> str:
    token = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in str(value).strip().upper())
    token = token.strip("_")
    return token or "EXEC_OWNER"


def normalize_organization_id(value: str) -> str:
    token = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in str(value).strip().upper())
    token = token.strip("_")
    return token or "ORG"


def normalize_registration_code(value: str) -> str:
    token = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "-" for ch in str(value).strip().upper())
    token = token.strip("-_")
    return token or "SANOM-ORG"


def normalize_deployment_mode(value: str) -> str:
    token = str(value or "private").strip().lower()
    return token if token in {"private", "multi"} else "private"


@dataclass(slots=True)
class OwnerRegistration:
    registration_code: str
    deployment_mode: str
    organization_name: str
    organization_id: str
    owner_name: str
    owner_display_name: str
    executive_owner_id: str
    trusted_registry_signed_by: str
    registered_at: str

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "OwnerRegistration":
        return build_owner_registration(data)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_owner_registration(
    data: dict[str, object] | None = None,
    *,
    existing: OwnerRegistration | None = None,
    registered_at: str | None = None,
) -> OwnerRegistration:
    payload = dict(data or {})
    candidate_code = (
        str(payload.get("registration_code", "")).strip()
        or (existing.registration_code if existing is not None else "")
    )
    if not candidate_code.strip():
        raise ValueError("registration_code is required in owner registration.")
    registration_code = normalize_registration_code(candidate_code)
    deployment_mode = normalize_deployment_mode(
        str(payload.get("deployment_mode", "")).strip()
        or (existing.deployment_mode if existing is not None else "private")
    )
    code_changed = existing is None or registration_code != existing.registration_code

    def _pick_string(key: str, fallback: str) -> str:
        value = str(payload.get(key, "")).strip()
        if value:
            return value
        if existing is not None and not code_changed:
            existing_value = str(getattr(existing, key, "")).strip()
            if existing_value:
                return existing_value
        return fallback

    owner_name = _pick_string("owner_name", "Executive Owner")
    owner_display_name = _pick_string("owner_display_name", owner_name)
    organization_name = _pick_string("organization_name", registration_code)
    organization_id = normalize_organization_id(_pick_string("organization_id", registration_code))
    executive_owner_id = normalize_owner_id(_pick_string("executive_owner_id", registration_code))
    trusted_registry_signed_by = _pick_string("trusted_registry_signed_by", executive_owner_id)
    payload_registered_at = str(payload.get("registered_at", "")).strip()

    if registered_at:
        effective_registered_at = registered_at
    elif payload_registered_at:
        effective_registered_at = payload_registered_at
    elif existing is not None and not code_changed:
        effective_registered_at = existing.registered_at
    else:
        effective_registered_at = utc_now()

    registration = OwnerRegistration(
        registration_code=registration_code,
        deployment_mode=deployment_mode,
        organization_name=organization_name,
        organization_id=organization_id,
        owner_name=owner_name,
        owner_display_name=owner_display_name,
        executive_owner_id=executive_owner_id,
        trusted_registry_signed_by=trusted_registry_signed_by,
        registered_at=effective_registered_at,
    )
    validate_owner_registration(registration)
    return registration


def load_owner_registration(path: Path | None) -> OwnerRegistration | None:
    if path is None or not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("owner_registration.json must contain a JSON object.")
    return build_owner_registration(payload)


def validate_owner_registration(registration: OwnerRegistration) -> None:
    if not registration.registration_code.strip():
        raise ValueError("registration_code is required in owner registration.")
    if registration.deployment_mode not in {"private", "multi"}:
        raise ValueError("deployment_mode must be private or multi in owner registration.")
    if not registration.organization_name.strip():
        raise ValueError("organization_name is required in owner registration.")
    if not registration.organization_id.strip():
        raise ValueError("organization_id is required in owner registration.")
    if not registration.owner_name.strip():
        raise ValueError("owner_name is required in owner registration.")
    if not registration.owner_display_name.strip():
        raise ValueError("owner_display_name is required in owner registration.")
    if not registration.executive_owner_id.strip():
        raise ValueError("executive_owner_id is required in owner registration.")
    if not registration.trusted_registry_signed_by.strip():
        raise ValueError("trusted_registry_signed_by is required in owner registration.")
    if not registration.registered_at.strip():
        raise ValueError("registered_at is required in owner registration.")


def write_owner_registration(path: Path, registration: OwnerRegistration, *, force: bool = False) -> OwnerRegistration:
    validate_owner_registration(registration)
    if path.exists() and not force:
        raise FileExistsError(f"Owner registration already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registration.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return registration

