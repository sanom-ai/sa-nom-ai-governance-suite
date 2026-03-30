import argparse
import json
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sa_nom_governance.guards.access_control import AccessControl, hash_token


DEFAULT_PROFILES = [
    ('enterprise-operator', 'Enterprise Operator', 'operator', 'Operator profile for governed runtime execution and Role Private Studio authoring.'),
    ('enterprise-reviewer', 'Enterprise Reviewer', 'reviewer', 'Reviewer profile for override decisions and Role Private Studio approval.'),
    ('enterprise-auditor', 'Enterprise Auditor', 'auditor', 'Auditor profile for evidence, audit, and runtime inspection.'),
    ('enterprise-viewer', 'Enterprise Viewer', 'viewer', 'Viewer profile for read-only dashboard access.'),
]

PRIVILEGED_OPERATOR_PERMISSIONS = {
    'session.manage',
    'retention.manage',
    'audit.manage',
    'ops.manage',
    'studio.publish',
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def validate_profile_lifetimes(days_valid: int, rotate_days: int) -> None:
    if days_valid <= 0:
        raise ValueError('days_valid must be greater than zero.')
    if rotate_days <= 0:
        raise ValueError('rotate_days must be greater than zero.')
    if rotate_days >= days_valid:
        raise ValueError('rotate_days must be less than days_valid so tokens rotate before they expire.')


def build_profiles(days_valid: int, rotate_days: int) -> tuple[list[dict[str, object]], dict[str, object]]:
    validate_profile_lifetimes(days_valid, rotate_days)
    now = utc_now()
    expires_at = (now + timedelta(days=days_valid)).isoformat()
    rotate_after = (now + timedelta(days=rotate_days)).isoformat()
    profiles: list[dict[str, object]] = []
    tokens: list[dict[str, str]] = []

    for profile_id, display_name, role_name, description in DEFAULT_PROFILES:
        token = secrets.token_urlsafe(32)
        permissions = set(AccessControl.DEFAULT_PERMISSIONS[role_name])
        if role_name == 'operator':
            permissions.update(PRIVILEGED_OPERATOR_PERMISSIONS)
        profiles.append(
            {
                'profile_id': profile_id,
                'display_name': display_name,
                'role_name': role_name,
                'token_hash': hash_token(token),
                'previous_token_hashes': [],
                'permissions': sorted(permissions),
                'not_before': now.isoformat(),
                'expires_at': expires_at,
                'rotate_after': rotate_after,
                'description': description,
            }
        )
        tokens.append({'profile_id': profile_id, 'display_name': display_name, 'role_name': role_name, 'token': token})

    token_bundle = {
        'generated_at': now.isoformat(),
        'expires_at': expires_at,
        'rotate_after': rotate_after,
        'profiles': tokens,
        'notes': [
            'Store these raw tokens in a secure secret manager.',
            'Only the token hashes belong in access_profiles.json.',
            'Rotate tokens before rotate_after and distribute new values securely.',
        ],
    }
    return profiles, token_bundle


def main() -> None:
    parser = argparse.ArgumentParser(description='Generate production-ready access_profiles.json with hashed tokens for SA-NOM private server deployment. Register the executive owner first with register_owner.py.')
    parser.add_argument('--output', default='_runtime/access_profiles.json')
    parser.add_argument('--tokens-output', default='_runtime/generated_access_tokens.json')
    parser.add_argument('--days-valid', type=int, default=365)
    parser.add_argument('--rotate-days', type=int, default=180)
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()

    output_path = Path(args.output).resolve()
    tokens_path = Path(args.tokens_output).resolve()
    if output_path.exists() and not args.force:
        raise SystemExit(f'Output already exists: {output_path}. Use --force to overwrite it.')
    if tokens_path.exists() and not args.force:
        raise SystemExit(f'Token export already exists: {tokens_path}. Use --force to overwrite it.')

    try:
        profiles, token_bundle = build_profiles(days_valid=args.days_valid, rotate_days=args.rotate_days)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    output_path.write_text(json.dumps(profiles, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tokens_path.write_text(json.dumps(token_bundle, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    print(json.dumps({
        'access_profiles_path': str(output_path),
        'tokens_output_path': str(tokens_path),
        'profiles_generated': len(profiles),
        'days_valid': args.days_valid,
        'rotate_days': args.rotate_days,
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

