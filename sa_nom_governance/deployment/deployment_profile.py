from dataclasses import asdict, dataclass, field
from typing import Any

from sa_nom_governance.guards.access_control import AccessControl
from sa_nom_governance.guards.access_profile_config import (
    AccessProfileConfigurationError,
    load_access_profile_items,
    profile_permissions,
    profile_role_name,
    require_profile_id,
)
from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.utils.owner_registration import validate_owner_registration


@dataclass(slots=True)
class DeploymentCheck:
    code: str
    status: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(slots=True)
class DeploymentReadinessReport:
    environment: str
    strict: bool
    ready: bool
    checks: list[DeploymentCheck] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            'environment': self.environment,
            'strict': self.strict,
            'ready': self.ready,
            'checks': [check.to_dict() for check in self.checks],
            'errors': sum(1 for check in self.checks if check.status == 'error'),
            'warnings': sum(1 for check in self.checks if check.status == 'warning'),
        }


class DeploymentValidationError(RuntimeError):
    pass


DEV_API_TOKEN = 'sanom-dev-token'
DEV_REGISTRY_KEY = 'sanom-dev-registry-key'


def build_deployment_report(config: AppConfig) -> DeploymentReadinessReport:
    checks: list[DeploymentCheck] = []
    environment = config.environment.lower()
    is_production = environment == 'production'

    checks.append(_check('ENVIRONMENT', 'ok', f'Runtime environment is {config.environment}.'))
    checks.extend(_inspect_owner_registration(config))
    if not config.api_token:
        checks.append(_check('API_TOKEN_MISSING', 'error', 'SANOM_API_TOKEN is not configured.'))
    elif is_production and config.api_token == DEV_API_TOKEN:
        checks.append(_check('API_TOKEN_DEV_DEFAULT', 'error', 'Production cannot use the development owner token.'))
    else:
        checks.append(_check('API_TOKEN_READY', 'ok', 'Owner API token is configured.'))

    if not config.trusted_registry_signing_key:
        checks.append(_check('REGISTRY_KEY_MISSING', 'error', 'Trusted registry signing key is not configured.'))
    elif is_production and config.trusted_registry_signing_key == DEV_REGISTRY_KEY:
        checks.append(_check('REGISTRY_KEY_DEV_DEFAULT', 'error', 'Production cannot use the development trusted-registry key.'))
    else:
        checks.append(_check('REGISTRY_KEY_READY', 'ok', 'Trusted registry signing key is configured.'))

    checks.append(
        _check('REGISTRY_SIGNATURE_ENABLED', 'ok', 'Trusted registry signature verification is enabled.')
        if config.trusted_registry_signature_required
        else _check('REGISTRY_SIGNATURE_DISABLED', 'error' if is_production else 'warning', 'Trusted registry signature verification is disabled.')
    )
    checks.append(
        _check('REGISTRY_MANIFEST_READY', 'ok', f'Trusted registry manifest found at {config.trusted_registry_manifest_path}.')
        if config.trusted_registry_manifest_path and config.trusted_registry_manifest_path.exists()
        else _check('REGISTRY_MANIFEST_MISSING', 'error' if is_production else 'warning', 'Trusted registry manifest file is missing.')
    )
    checks.append(
        _check('SESSION_TTL_READY', 'ok', f'Session TTL is {config.session_ttl_minutes} minutes.')
        if config.session_ttl_minutes > 0
        else _check('SESSION_TTL_INVALID', 'error', 'SANOM_SESSION_TTL_MINUTES must be greater than zero.')
    )
    if config.session_idle_timeout_minutes <= 0:
        checks.append(_check('SESSION_IDLE_INVALID', 'error', 'SANOM_SESSION_IDLE_TIMEOUT_MINUTES must be greater than zero.'))
    elif config.session_idle_timeout_minutes > config.session_ttl_minutes:
        checks.append(_check('SESSION_IDLE_GT_TTL', 'error', 'Session idle timeout cannot exceed session TTL.'))
    else:
        checks.append(_check('SESSION_IDLE_READY', 'ok', f'Session idle timeout is {config.session_idle_timeout_minutes} minutes.'))

    checks.append(
        _check('SESSION_STORE_READY', 'ok', f'Session store path is {config.session_store_path}.')
        if config.persist_runtime and config.session_store_path is not None
        else _check('SESSION_STORE_DISABLED', 'warning' if not is_production else 'error', 'Session persistence is not enabled.')
    )
    checks.append(
        _check('ROLE_PRIVATE_STUDIO_STORE_READY', 'ok', f'Role Private Studio store path is {config.role_private_studio_store_path}.')
        if config.persist_runtime and config.role_private_studio_store_path is not None
        else _check('ROLE_PRIVATE_STUDIO_STORE_DISABLED', 'warning' if not is_production else 'error', 'Role Private Studio persistence is not enabled.')
    )

    if is_production and not config.server_public_base_url:
        checks.append(_check('PUBLIC_BASE_URL_MISSING', 'warning', 'SANOM_SERVER_PUBLIC_BASE_URL is not configured.'))
    elif config.server_public_base_url:
        if is_production and not str(config.server_public_base_url).startswith('https://'):
            checks.append(_check('PUBLIC_BASE_URL_READY', 'warning', 'Production public base URL should use HTTPS.'))
        else:
            checks.append(_check('PUBLIC_BASE_URL_READY', 'ok', f'Public base URL is {config.server_public_base_url}.'))

    checks.extend(_inspect_access_profiles(config))
    ready = not any(check.status == 'error' for check in checks)
    return DeploymentReadinessReport(environment=config.environment, strict=config.strict_startup_validation, ready=ready, checks=checks)


def validate_startup_or_raise(config: AppConfig) -> DeploymentReadinessReport:
    report = build_deployment_report(config)
    if config.strict_startup_validation and not report.ready:
        errors = [f'- {check.code}: {check.message}' for check in report.checks if check.status == 'error']
        raise DeploymentValidationError('Startup validation failed:\n' + '\n'.join(errors))
    return report


def _inspect_access_profiles(config: AppConfig) -> list[DeploymentCheck]:
    checks: list[DeploymentCheck] = []
    path = config.effective_access_profiles_path()
    is_production = config.environment.lower() == 'production'
    if path is None or not path.exists():
        checks.append(_check('ACCESS_PROFILES_MISSING', 'error' if is_production else 'warning', 'access_profiles.json is missing.'))
        return checks

    checks.append(_check('ACCESS_PROFILES_READY', 'ok', f'Access profiles found at {path}.'))
    try:
        data = load_access_profile_items(path)
    except AccessProfileConfigurationError as error:
        checks.append(_check('ACCESS_PROFILES_INVALID', 'error', f'access_profiles.json is invalid: {error}'))
        return checks

    if not data:
        checks.append(_check('ACCESS_PROFILES_EMPTY', 'error', 'access_profiles.json does not contain any profiles.'))
        return checks

    profile_ids: list[str] = []
    plain_profiles: list[str] = []
    hashed_profiles: list[str] = []
    rotating_profiles: list[str] = []
    disabled_profiles: list[str] = []
    role_names: set[str] = set()
    delegated_permissions: set[str] = set()

    try:
        for index, item in enumerate(data, start=1):
            profile_id = require_profile_id(item, index=index)
            profile_ids.append(profile_id)
            if item.get('token'):
                plain_profiles.append(profile_id)
            if item.get('token_hash'):
                hashed_profiles.append(profile_id)
            if item.get('rotate_after'):
                rotating_profiles.append(profile_id)
            if item.get('disabled'):
                disabled_profiles.append(profile_id)
            role_names.add(profile_role_name(item))
            delegated_permissions.update(profile_permissions(item, AccessControl.DEFAULT_PERMISSIONS, index=index))
    except AccessProfileConfigurationError as error:
        checks.append(_check('ACCESS_PROFILES_INVALID', 'error', f'access_profiles.json is invalid: {error}'))
        return checks

    duplicate_ids = sorted({profile_id for profile_id in profile_ids if profile_ids.count(profile_id) > 1})

    if duplicate_ids:
        checks.append(_check('ACCESS_PROFILES_DUPLICATE_ID', 'error', f'Duplicate access profile ids found: {", ".join(duplicate_ids)}.'))
    else:
        checks.append(_check('ACCESS_PROFILES_UNIQUE_ID', 'ok', 'Access profile ids are unique.'))

    if config.access_profiles_require_hashes and plain_profiles:
        checks.append(_check('ACCESS_PROFILES_PLAIN_TOKEN', 'error' if is_production else 'warning', f'Profiles use plain tokens in file storage: {", ".join(plain_profiles)}.'))
    else:
        checks.append(_check('ACCESS_PROFILES_HASHED_OK', 'ok', f'Hashed token profiles: {len(hashed_profiles)}.'))

    if is_production and not rotating_profiles:
        checks.append(_check('ACCESS_PROFILES_ROTATION_MISSING', 'warning', 'No access profiles define a rotate_after policy.'))
    else:
        checks.append(_check('ACCESS_PROFILES_ROTATION', 'ok', f'Profiles with rotate_after policy: {len(rotating_profiles)}.'))

    checks.append(_check('ACCESS_PROFILES_DISABLED', 'ok', f'Profiles marked disabled: {len(disabled_profiles)}.'))

    required_roles = {'operator', 'reviewer'}
    recommended_roles = {'auditor', 'viewer'}
    missing_required_roles = sorted(required_roles - role_names)
    missing_recommended_roles = sorted(recommended_roles - role_names)

    if missing_required_roles:
        checks.append(_check('ACCESS_PROFILES_REQUIRED_ROLE_MISSING', 'error' if is_production else 'warning', f'Missing required access profile roles: {", ".join(missing_required_roles)}.'))
    else:
        checks.append(_check('ACCESS_PROFILES_REQUIRED_ROLE_COVERAGE', 'ok', 'Required access profile roles are present.'))

    if missing_recommended_roles:
        checks.append(_check('ACCESS_PROFILES_RECOMMENDED_ROLE_MISSING', 'warning', f'Missing recommended access profile roles: {", ".join(missing_recommended_roles)}.'))
    else:
        checks.append(_check('ACCESS_PROFILES_RECOMMENDED_ROLE_COVERAGE', 'ok', 'Recommended access profile roles are present.'))

    privileged_permissions = {
        'session.manage': 'session control',
        'retention.manage': 'retention enforcement',
        'audit.manage': 'audit reseal',
        'ops.manage': 'runtime backup operations',
        'studio.publish': 'Role Private Studio publication',
    }
    missing_privileged_permissions = sorted(
        permission for permission in privileged_permissions if permission not in delegated_permissions
    )
    if missing_privileged_permissions:
        labels = ", ".join(
            f"{permission} ({privileged_permissions[permission]})" for permission in missing_privileged_permissions
        )
        checks.append(
            _check(
                'ACCESS_PROFILES_PRIVILEGED_PERMISSION_GAP',
                'error' if is_production else 'warning',
                'Delegated access profiles do not cover privileged runtime permissions: '
                f'{labels}. These actions would remain owner-only in the live dashboard.',
            )
        )
    else:
        checks.append(
            _check(
                'ACCESS_PROFILES_PRIVILEGED_PERMISSION_COVERAGE',
                'ok',
                'Delegated access profiles cover privileged runtime operations beyond the owner token.',
            )
        )

    return checks


def _inspect_owner_registration(config: AppConfig) -> list[DeploymentCheck]:
    checks: list[DeploymentCheck] = []
    is_production = config.environment.lower() == 'production'
    path = config.effective_owner_registration_path()
    if path is None or not path.exists():
        checks.append(
            _check(
                'OWNER_REGISTRATION_MISSING',
                'error' if is_production else 'warning',
                'Owner registration is missing. Run register_owner.py before enterprise use so the organization and executive owner are defined.',
            )
        )
        return checks

    try:
        registration = config.owner_registration()
        if registration is None:
            raise ValueError('Owner registration could not be loaded.')
        validate_owner_registration(registration)
    except Exception as error:
        checks.append(_check('OWNER_REGISTRATION_INVALID', 'error', f'Owner registration is invalid: {error}'))
        return checks

    checks.append(
        _check(
            'OWNER_REGISTRATION_READY',
            'ok',
            f'Owner registration loaded for {registration.organization_name} with executive owner {registration.executive_owner_id}.',
        )
    )
    if config.trusted_registry_signed_by != registration.trusted_registry_signed_by:
        checks.append(
            _check(
                'OWNER_SIGNER_MISMATCH',
                'warning',
                'Trusted registry signing identity differs from owner registration. '
                f'Runtime signer={config.trusted_registry_signed_by}, registered signer={registration.trusted_registry_signed_by}.',
            )
        )
    else:
        checks.append(
            _check(
                'OWNER_SIGNER_READY',
                'ok',
                f'Trusted registry signer aligns with registered owner identity {registration.trusted_registry_signed_by}.',
            )
        )
    return checks


def _check(code: str, status: str, message: str) -> DeploymentCheck:
    return DeploymentCheck(code=code, status=status, message=message)

