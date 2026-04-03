import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.utils.owner_registration import (
    build_owner_registration,
    normalize_deployment_mode,
    normalize_registration_code,
    write_owner_registration,
)


def build_parser(default_output: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Register the executive owner before using SA-NOM AI Governance Suite in a new organization.'
    )
    parser.add_argument('--output', default=default_output)
    parser.add_argument('--registration-code', required=True)
    parser.add_argument('--deployment-mode', default='private', choices=['private', 'multi'])
    parser.add_argument('--organization-name')
    parser.add_argument('--organization-id')
    parser.add_argument('--owner-name')
    parser.add_argument('--owner-display-name')
    parser.add_argument('--executive-owner-id')
    parser.add_argument('--trusted-registry-signed-by')
    parser.add_argument('--force', action='store_true')
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    config = AppConfig()
    default_output = config.runtime_dir / 'owner_registration.json'
    args = build_parser(str(default_output)).parse_args(list(argv) if argv is not None else None)

    registration_code = normalize_registration_code(str(args.registration_code))
    registration = build_owner_registration(
        {
            'registration_code': registration_code,
            'deployment_mode': normalize_deployment_mode(str(args.deployment_mode)),
            'organization_name': args.organization_name or '',
            'organization_id': args.organization_id or '',
            'owner_name': args.owner_name or '',
            'owner_display_name': args.owner_display_name or '',
            'executive_owner_id': args.executive_owner_id or '',
            'trusted_registry_signed_by': args.trusted_registry_signed_by or '',
        }
    )

    output_path = Path(args.output).resolve()
    write_owner_registration(output_path, registration, force=args.force)
    print(
        json.dumps(
            {
                'owner_registration_path': str(output_path),
                'registration_code': registration.registration_code,
                'deployment_mode': registration.deployment_mode,
                'organization_name': registration.organization_name,
                'organization_id': registration.organization_id,
                'owner_name': registration.owner_name,
                'owner_display_name': registration.owner_display_name,
                'executive_owner_id': registration.executive_owner_id,
                'trusted_registry_signed_by': registration.trusted_registry_signed_by,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == '__main__':
    main()
