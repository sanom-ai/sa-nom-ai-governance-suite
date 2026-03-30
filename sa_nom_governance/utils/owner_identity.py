from __future__ import annotations

DEFAULT_EXECUTIVE_OWNER_ID = "EXEC_OWNER"
DEFAULT_OWNER_NAME = "Executive Owner"
DEFAULT_OWNER_DISPLAY_NAME = "Executive Owner"
# Preserve the pre-open-source executive owner token so older local data can still load cleanly.
LEGACY_OWNER_ALIASES = frozenset({"TAWAN"})
DEFAULT_OWNER_ALIASES = frozenset({DEFAULT_EXECUTIVE_OWNER_ID, *LEGACY_OWNER_ALIASES})


def _normalized_text(value: object | None) -> str:
    return str(value or "").strip()


def _upper_token(value: object | None) -> str:
    token = _normalized_text(value)
    return token.upper() if token else ""


def is_default_owner_alias(value: object | None, *, include_empty: bool = True) -> bool:
    token = _upper_token(value)
    return (include_empty and not token) or token in DEFAULT_OWNER_ALIASES


def normalize_executive_owner_id(value: object | None, *, fallback: str = DEFAULT_EXECUTIVE_OWNER_ID) -> str:
    token = _upper_token(value)
    normalized_fallback = _upper_token(fallback) or DEFAULT_EXECUTIVE_OWNER_ID
    if not token or token in DEFAULT_OWNER_ALIASES:
        return normalized_fallback
    return token


def replace_default_owner_alias(value: object | None, *, fallback: str = DEFAULT_EXECUTIVE_OWNER_ID) -> str:
    raw = _normalized_text(value)
    if is_default_owner_alias(raw):
        return normalize_executive_owner_id(fallback, fallback=DEFAULT_EXECUTIVE_OWNER_ID)
    return raw
