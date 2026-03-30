import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from access_profile_config import (
    AccessProfileConfigurationError,
    load_access_profile_items,
    profile_permissions,
    profile_role_name,
    require_profile_id,
    string_list_field,
)
from config import AppConfig
from session_manager import SessionManager


@dataclass(slots=True)
class AccessProfile:
    profile_id: str
    display_name: str
    role_name: str
    permissions: set[str] = field(default_factory=set)
    description: str = ''
    token: str | None = None
    token_hash: str | None = None
    previous_token_hashes: list[str] = field(default_factory=list)
    not_before: str | None = None
    expires_at: str | None = None
    rotate_after: str | None = None
    disabled: bool = False
    source: str = 'file'

    def can(self, permission: str) -> bool:
        return '*' in self.permissions or permission in self.permissions

    def is_active(self) -> bool:
        return self.status() == 'active'

    def status(self) -> str:
        now = datetime.now(timezone.utc)
        if self.disabled:
            return 'disabled'
        if self.not_before is not None and self._parse_time(self.not_before) > now:
            return 'not_yet_active'
        if self.expires_at is not None and self._parse_time(self.expires_at) <= now:
            return 'expired'
        return 'active'

    def rotation_required(self) -> bool:
        if self.rotate_after is None:
            return False
        return self._parse_time(self.rotate_after) <= datetime.now(timezone.utc)

    def token_match_mode(self, token: str) -> str | None:
        if self.token is not None and secrets.compare_digest(self.token, token):
            return 'plain'
        if self.token_hash is not None:
            candidate_hash = hash_token(token)
            if secrets.compare_digest(self.token_hash, candidate_hash):
                return 'sha256'
            for previous_hash in self.previous_token_hashes:
                if secrets.compare_digest(previous_hash, candidate_hash):
                    return 'previous_sha256'
        return None

    def token_mode(self) -> str:
        if self.token_hash:
            return 'sha256'
        if self.token:
            return 'plain'
        return 'none'

    def to_public_dict(self) -> dict[str, object]:
        return {
            'profile_id': self.profile_id,
            'display_name': self.display_name,
            'role_name': self.role_name,
            'permissions': sorted(self.permissions),
            'description': self.description,
            'status': self.status(),
            'not_before': self.not_before,
            'expires_at': self.expires_at,
            'rotate_after': self.rotate_after,
            'rotation_required': self.rotation_required(),
            'token_mode': self.token_mode(),
            'previous_token_hashes': len(self.previous_token_hashes),
            'source': self.source,
        }

    def _parse_time(self, value: str) -> datetime:
        return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(timezone.utc)


@dataclass(slots=True)
class AuthResult:
    authenticated: bool
    profile: AccessProfile | None
    reason: str
    token_present: bool
    profile_id: str | None = None
    auth_method: str | None = None
    session_id: str | None = None


class AccessControl:
    DEFAULT_PERMISSIONS = {
        'viewer': {'dashboard.read', 'requests.read', 'roles.read', 'health.read', 'studio.read', 'human_ask.read'},
        'reviewer': {'dashboard.read', 'requests.read', 'overrides.read', 'override.review', 'locks.read', 'roles.read', 'health.read', 'studio.read', 'studio.review', 'compliance.read', 'integration.read', 'human_ask.read'},
        'auditor': {'dashboard.read', 'requests.read', 'overrides.read', 'locks.read', 'audit.read', 'roles.read', 'health.read', 'sessions.read', 'studio.read', 'compliance.read', 'evidence.read', 'evidence.export', 'integration.read', 'human_ask.read'},
        'operator': {'dashboard.read', 'requests.read', 'request.create', 'overrides.read', 'override.review', 'locks.read', 'audit.read', 'roles.read', 'health.read', 'studio.read', 'studio.create', 'compliance.read', 'integration.read', 'human_ask.read', 'human_ask.create'},
        'owner': {'*'},
    }

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.session_manager = SessionManager(config)
        self._profile_configuration_error: str | None = None
        self._profiles: list[AccessProfile] = self._load_profiles()

    def authenticate(self, headers) -> AccessProfile | None:
        result = self.authenticate_result(headers)
        return result.profile if result.authenticated else None

    def authenticate_result(self, headers) -> AuthResult:
        session_token = self._extract_session_token(headers)
        if session_token:
            session_result = self.session_manager.authenticate_token(session_token)
            if session_result.authenticated and session_result.session is not None:
                profile = self._profile_from_session(session_result.session)
                return AuthResult(authenticated=True, profile=profile, reason=session_result.reason, token_present=True, profile_id=session_result.profile_id, auth_method='session', session_id=session_result.session_id)
            return AuthResult(authenticated=False, profile=None, reason=session_result.reason, token_present=True, profile_id=session_result.profile_id, auth_method='session', session_id=session_result.session_id)
        return self.authenticate_access_token_result(headers)

    def authenticate_access_token_result(self, headers) -> AuthResult:
        token = self._extract_access_token(headers)
        if not token:
            return AuthResult(authenticated=False, profile=None, reason='missing_token', token_present=False)
        return self._authenticate_access_token(token)

    def issue_session_from_headers(self, headers) -> tuple[AuthResult, dict[str, object] | None]:
        auth = self.authenticate_access_token_result(headers)
        if not auth.authenticated or auth.profile is None:
            return auth, None
        state, session_token = self.session_manager.issue(auth.profile, auth_method=auth.auth_method or 'access_token')
        return AuthResult(authenticated=True, profile=self._profile_from_session(state), reason='session_issued', token_present=True, profile_id=state.profile_id, auth_method='session', session_id=state.session_id), {'session_token': session_token, 'session': state.to_public_dict()}

    def revoke_session_from_headers(self, headers) -> dict[str, object]:
        return self.session_manager.revoke_token(self._extract_session_token(headers), reason='logout')

    def list_sessions(self, status: str | None = None) -> list[dict[str, object]]:
        return [session.to_public_dict() for session in self.session_manager.list_sessions(status=status)]

    def revoke_session(self, session_id: str, reason: str = 'admin_revoke') -> dict[str, object]:
        return self.session_manager.revoke_session_id(session_id, reason=reason)

    def require(self, profile: AccessProfile | None, permission: str) -> bool:
        return profile is not None and profile.is_active() and profile.can(permission)

    def list_public_profiles(self) -> list[dict[str, object]]:
        return [profile.to_public_dict() for profile in self._profiles]

    def health(self) -> dict[str, object]:
        active = sum(1 for profile in self._profiles if profile.status() == 'active')
        expired = sum(1 for profile in self._profiles if profile.status() == 'expired')
        disabled = sum(1 for profile in self._profiles if profile.status() == 'disabled')
        not_yet_active = sum(1 for profile in self._profiles if profile.status() == 'not_yet_active')
        hashed = sum(1 for profile in self._profiles if profile.token_mode() == 'sha256')
        plain = sum(1 for profile in self._profiles if profile.token_mode() == 'plain')
        plain_file_tokens = sum(1 for profile in self._profiles if profile.source == 'file' and profile.token_mode() == 'plain')
        plain_owner_tokens = sum(1 for profile in self._profiles if profile.source == 'owner' and profile.token_mode() == 'plain')
        file_profiles = sum(1 for profile in self._profiles if profile.source == 'file')
        development_profiles = sum(1 for profile in self._profiles if profile.source == 'development')
        rotation_required = sum(1 for profile in self._profiles if profile.rotation_required())
        return {
            'profiles_total': len(self._profiles),
            'profiles_active': active,
            'profiles_expired': expired,
            'profiles_disabled': disabled,
            'profiles_not_yet_active': not_yet_active,
            'profiles_rotation_required': rotation_required,
            'hashed_tokens': hashed,
            'plain_tokens': plain,
            'plain_file_tokens': plain_file_tokens,
            'plain_owner_tokens': plain_owner_tokens,
            'file_profiles': file_profiles,
            'development_profiles': development_profiles,
            'access_profile_configuration_valid': self._profile_configuration_error is None,
            'access_profile_configuration_error': self._profile_configuration_error,
            **self.session_manager.health(),
        }

    def _authenticate_access_token(self, token: str) -> AuthResult:
        for profile in self._profiles:
            match_mode = profile.token_match_mode(token)
            if match_mode is None:
                continue
            status = profile.status()
            if status == 'disabled':
                return AuthResult(authenticated=False, profile=None, reason='disabled_profile', token_present=True, profile_id=profile.profile_id, auth_method=match_mode)
            if status == 'expired':
                return AuthResult(authenticated=False, profile=None, reason='expired_profile', token_present=True, profile_id=profile.profile_id, auth_method=match_mode)
            if status == 'not_yet_active':
                return AuthResult(authenticated=False, profile=None, reason='not_yet_active_profile', token_present=True, profile_id=profile.profile_id, auth_method=match_mode)
            return AuthResult(authenticated=True, profile=profile, reason='authenticated_previous_token' if match_mode == 'previous_sha256' else 'authenticated', token_present=True, profile_id=profile.profile_id, auth_method=match_mode)
        return AuthResult(authenticated=False, profile=None, reason='unknown_token', token_present=True)

    def _profile_from_session(self, state) -> AccessProfile:
        return AccessProfile(profile_id=state.profile_id, display_name=state.display_name, role_name=state.role_name, permissions=set(state.permissions), description='Session-authenticated runtime profile.', source='session')

    def _load_profiles(self) -> list[AccessProfile]:
        profiles: list[AccessProfile] = []
        if self.config.api_token:
            organization_name = self.config.organization_name()
            description = 'Full control profile for the private server runtime.'
            if organization_name:
                description = f'Full control profile for {organization_name}.'
            profiles.append(
                AccessProfile(
                    profile_id='owner',
                    display_name=self.config.owner_display_name(),
                    role_name='owner',
                    token=self.config.api_token,
                    permissions=set(self.DEFAULT_PERMISSIONS['owner']),
                    description=description,
                    source='owner',
                )
            )
        path = self.config.effective_access_profiles_path()
        if path is not None and path.exists():
            try:
                profiles.extend(self._load_profile_file(path))
            except AccessProfileConfigurationError as error:
                self._profile_configuration_error = str(error)
        elif self.config.environment == 'development':
            profiles.extend(self._default_dev_profiles())
        return profiles

    def _load_profile_file(self, path: Path) -> list[AccessProfile]:
        data = load_access_profile_items(path)
        profiles: list[AccessProfile] = []
        for index, item in enumerate(data, start=1):
            profile_id = require_profile_id(item, index=index)
            role_name = profile_role_name(item)
            permissions = profile_permissions(item, self.DEFAULT_PERMISSIONS, index=index)
            previous_token_hashes = string_list_field(item, 'previous_token_hashes', index=index)
            profiles.append(
                AccessProfile(
                    profile_id=profile_id,
                    display_name=str(item.get('display_name', profile_id)),
                    role_name=role_name,
                    token=str(item['token']) if item.get('token') else None,
                    token_hash=str(item['token_hash']) if item.get('token_hash') else None,
                    previous_token_hashes=previous_token_hashes,
                    permissions=permissions,
                    description=str(item.get('description', '')),
                    not_before=str(item['not_before']) if item.get('not_before') else None,
                    expires_at=str(item['expires_at']) if item.get('expires_at') else None,
                    rotate_after=str(item['rotate_after']) if item.get('rotate_after') else None,
                    disabled=bool(item.get('disabled', False)),
                    source='file',
                )
            )
        return profiles

    def _default_dev_profiles(self) -> list[AccessProfile]:
        return [
            AccessProfile(profile_id='operator-dev', display_name='Operator Dev', role_name='operator', token='sanom-operator-token', permissions=set(self.DEFAULT_PERMISSIONS['operator']), description='Development operator profile with request and override control.', source='development'),
            AccessProfile(profile_id='reviewer-dev', display_name='Reviewer Dev', role_name='reviewer', token='sanom-reviewer-token', permissions=set(self.DEFAULT_PERMISSIONS['reviewer']), description='Development reviewer profile for human override and studio review.', source='development'),
            AccessProfile(profile_id='auditor-dev', display_name='Auditor Dev', role_name='auditor', token='sanom-auditor-token', permissions=set(self.DEFAULT_PERMISSIONS['auditor']), description='Development auditor profile for evidence and audit inspection.', source='development'),
            AccessProfile(profile_id='viewer-dev', display_name='Viewer Dev', role_name='viewer', token='sanom-viewer-token', permissions=set(self.DEFAULT_PERMISSIONS['viewer']), description='Development viewer profile for read-only dashboard access.', source='development'),
        ]

    def _extract_access_token(self, headers) -> str | None:
        provided = headers.get('X-SA-NOM-Token')
        authorization = headers.get('Authorization', '')
        if not provided and authorization.startswith('Bearer '):
            provided = authorization.removeprefix('Bearer ').strip()
        return provided.strip() if provided else None

    def _extract_session_token(self, headers) -> str | None:
        provided = headers.get('X-SA-NOM-Session')
        return str(provided).strip() or None if provided else None


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()
