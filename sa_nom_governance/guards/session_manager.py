import hashlib
import secrets
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol

from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.utils.persistence import build_state_store


@dataclass(slots=True)
class SessionState:
    session_id: str
    profile_id: str
    display_name: str
    role_name: str
    permissions: list[str]
    token_hash: str
    status: str
    created_at: str
    last_seen_at: str
    expires_at: str
    idle_expires_at: str
    auth_method: str
    revoked_at: str | None = None
    revoke_reason: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "SessionState":
        permissions_value = data.get("permissions", [])
        permissions_items = permissions_value if isinstance(permissions_value, list) else []
        return cls(
            session_id=str(data["session_id"]),
            profile_id=str(data["profile_id"]),
            display_name=str(data["display_name"]),
            role_name=str(data["role_name"]),
            permissions=[str(item) for item in permissions_items],
            token_hash=str(data["token_hash"]),
            status=str(data["status"]),
            created_at=str(data["created_at"]),
            last_seen_at=str(data["last_seen_at"]),
            expires_at=str(data["expires_at"]),
            idle_expires_at=str(data["idle_expires_at"]),
            auth_method=str(data.get("auth_method", "access_token")),
            revoked_at=str(data["revoked_at"]) if data.get("revoked_at") else None,
            revoke_reason=str(data["revoke_reason"]) if data.get("revoke_reason") else None,
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def to_public_dict(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "profile_id": self.profile_id,
            "display_name": self.display_name,
            "role_name": self.role_name,
            "permissions": list(self.permissions),
            "status": self.status,
            "created_at": self.created_at,
            "last_seen_at": self.last_seen_at,
            "expires_at": self.expires_at,
            "idle_expires_at": self.idle_expires_at,
            "auth_method": self.auth_method,
            "revoked_at": self.revoked_at,
            "revoke_reason": self.revoke_reason,
        }


@dataclass(slots=True)
class SessionAuthResult:
    authenticated: bool
    session: SessionState | None
    reason: str
    token_present: bool
    profile_id: str | None = None
    session_id: str | None = None


class SessionProfile(Protocol):
    profile_id: str
    display_name: str
    role_name: str
    permissions: set[str]


class SessionManager:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.store = build_state_store(config, config.session_store_path, logical_name="sessions")
        self.store_path = self.store.path
        self.session_ttl_minutes = config.session_ttl_minutes
        self.session_idle_timeout_minutes = config.session_idle_timeout_minutes
        self._sessions: dict[str, SessionState] = {}
        self._load_existing()

    def issue(self, profile: SessionProfile, auth_method: str = "access_token") -> tuple[SessionState, str]:
        token = f"sns_{secrets.token_urlsafe(24)}"
        now = self._now()
        state = SessionState(
            session_id=f"session-{secrets.token_hex(8)}",
            profile_id=str(profile.profile_id),
            display_name=str(profile.display_name),
            role_name=str(profile.role_name),
            permissions=sorted(profile.permissions),
            token_hash=self._hash_token(token),
            status="active",
            created_at=now.isoformat(),
            last_seen_at=now.isoformat(),
            expires_at=(now + timedelta(minutes=self.session_ttl_minutes)).isoformat(),
            idle_expires_at=(now + timedelta(minutes=self.session_idle_timeout_minutes)).isoformat(),
            auth_method=auth_method,
        )
        self._sessions[state.session_id] = state
        self._persist()
        return state, token

    def authenticate_token(self, token: str | None) -> SessionAuthResult:
        if not token:
            return SessionAuthResult(authenticated=False, session=None, reason="missing_session", token_present=False)

        for state in self._sessions.values():
            if not secrets.compare_digest(state.token_hash, self._hash_token(token)):
                continue
            self._materialize_status(state)
            if state.status != "active":
                self._persist()
                return SessionAuthResult(
                    authenticated=False,
                    session=None,
                    reason=f"{state.status}_session",
                    token_present=True,
                    profile_id=state.profile_id,
                    session_id=state.session_id,
                )
            self._touch(state)
            self._persist()
            return SessionAuthResult(
                authenticated=True,
                session=state,
                reason="authenticated_session",
                token_present=True,
                profile_id=state.profile_id,
                session_id=state.session_id,
            )

        return SessionAuthResult(authenticated=False, session=None, reason="unknown_session", token_present=True)

    def list_sessions(self, status: str | None = None) -> list[SessionState]:
        sessions = []
        for state in self._sessions.values():
            self._materialize_status(state)
            if status is None or state.status == status:
                sessions.append(state)
        self._persist()
        return sorted(sessions, key=lambda item: item.created_at, reverse=True)

    def get_session(self, session_id: str) -> SessionState:
        state = self._sessions.get(session_id)
        if state is None:
            raise KeyError(f"Session not found: {session_id}")
        self._materialize_status(state)
        self._persist()
        return state

    def revoke_token(self, token: str | None, reason: str = "logout") -> dict[str, object]:
        if not token:
            return {"success": False, "reason": "missing_session"}

        for state in self._sessions.values():
            if not secrets.compare_digest(state.token_hash, self._hash_token(token)):
                continue
            return self._revoke_state(state, reason=reason)

        return {"success": False, "reason": "unknown_session"}

    def revoke_session_id(self, session_id: str, reason: str = "admin_revoke") -> dict[str, object]:
        state = self._sessions.get(session_id)
        if state is None:
            return {"success": False, "reason": "unknown_session", "session_id": session_id}
        return self._revoke_state(state, reason=reason)

    def health(self) -> dict[str, object]:
        active = 0
        expired = 0
        idle_expired = 0
        revoked = 0
        for state in self._sessions.values():
            self._materialize_status(state)
            if state.status == "active":
                active += 1
            elif state.status == "expired":
                expired += 1
            elif state.status == "idle_expired":
                idle_expired += 1
            elif state.status == "revoked":
                revoked += 1
        self._persist()
        return {
            "sessions_total": len(self._sessions),
            "sessions_active": active,
            "sessions_expired": expired,
            "sessions_idle_expired": idle_expired,
            "sessions_revoked": revoked,
            "session_ttl_minutes": self.session_ttl_minutes,
            "session_idle_timeout_minutes": self.session_idle_timeout_minutes,
        }

    def _revoke_state(self, state: SessionState, reason: str) -> dict[str, object]:
        self._materialize_status(state)
        if state.status == "revoked":
            return {"success": False, "reason": "already_revoked", "session": state.to_public_dict()}
        state.status = "revoked"
        state.revoked_at = self._utc_now()
        state.revoke_reason = reason
        self._persist()
        return {"success": True, "reason": "revoked", "session": state.to_public_dict()}

    def _touch(self, state: SessionState) -> None:
        now = self._now()
        state.last_seen_at = now.isoformat()
        state.idle_expires_at = (now + timedelta(minutes=self.session_idle_timeout_minutes)).isoformat()

    def _materialize_status(self, state: SessionState) -> None:
        if state.status == "revoked":
            return
        now = self._now()
        if self._parse_time(state.expires_at) <= now:
            state.status = "expired"
            return
        if self._parse_time(state.idle_expires_at) <= now:
            state.status = "idle_expired"
            return
        state.status = "active"

    def _persist(self) -> None:
        payload = [state.to_dict() for state in self._sessions.values()]
        self.store.write(payload)

    def _load_existing(self) -> None:
        data = self.store.read(default=[])
        for item in data:
            state = SessionState.from_dict(item)
            self._materialize_status(state)
            self._sessions[state.session_id] = state

    def _hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def _parse_time(self, value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _utc_now(self) -> str:
        return self._now().isoformat()


