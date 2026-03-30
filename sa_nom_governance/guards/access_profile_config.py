import json
from collections.abc import Mapping
from json import JSONDecodeError
from pathlib import Path


class AccessProfileConfigurationError(ValueError):
    """Raised when access profile configuration cannot be parsed safely."""


def load_access_profile_items(path: Path) -> list[dict[str, object]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except JSONDecodeError as error:
        raise AccessProfileConfigurationError(
            f"access_profiles.json contains invalid JSON at line {error.lineno}, column {error.colno}: {error.msg}."
        ) from error
    if not isinstance(data, list):
        raise AccessProfileConfigurationError("access_profiles.json must contain a JSON array of profile objects.")

    items: list[dict[str, object]] = []
    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise AccessProfileConfigurationError(
                f"access_profiles.json entry {index} must be a JSON object."
            )
        items.append(item)
    return items


def require_profile_id(item: Mapping[str, object], *, index: int) -> str:
    profile_id = str(item.get("profile_id", "")).strip()
    if not profile_id:
        raise AccessProfileConfigurationError(
            f"access_profiles.json entry {index} is missing required field 'profile_id'."
        )
    return profile_id


def profile_role_name(item: Mapping[str, object]) -> str:
    role_name = str(item.get("role_name", "viewer")).strip()
    return role_name or "viewer"


def profile_permissions(
    item: Mapping[str, object],
    default_permissions: Mapping[str, set[str]],
    *,
    index: int,
) -> set[str]:
    configured = item.get("permissions")
    if configured in (None, [], (), set()):
        return set(default_permissions.get(profile_role_name(item), set()))
    if not isinstance(configured, (list, tuple, set)):
        raise AccessProfileConfigurationError(
            f"access_profiles.json entry {index} field 'permissions' must be an array of strings."
        )
    return {str(permission) for permission in configured}


def string_list_field(item: Mapping[str, object], field_name: str, *, index: int) -> list[str]:
    raw = item.get(field_name, [])
    if raw is None:
        return []
    if not isinstance(raw, (list, tuple, set)):
        raise AccessProfileConfigurationError(
            f"access_profiles.json entry {index} field '{field_name}' must be an array of strings."
        )
    return [str(value) for value in raw]
