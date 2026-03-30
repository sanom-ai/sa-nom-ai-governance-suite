import argparse
import json

from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.dashboard.dashboard_server import run_server
from sa_nom_governance.deployment.deployment_profile import validate_startup_or_raise
from sa_nom_governance.deployment.private_server_smoke_test import run_smoke


def main() -> None:
    parser = argparse.ArgumentParser(description='Run the SA-NOM private server with optional startup smoke validation.')
    parser.add_argument('--host', default=None)
    parser.add_argument('--port', type=int, default=None)
    parser.add_argument('--token', default=None)
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--smoke-only', action='store_true')
    parser.add_argument('--smoke-before-serve', action='store_true')
    args = parser.parse_args()

    config = AppConfig()
    if args.token is not None:
        config.api_token = args.token

    report = validate_startup_or_raise(config)
    if args.check_only:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return

    if args.smoke_only:
        result = run_smoke(config=config, token=config.api_token)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.smoke_before_serve:
        result = run_smoke(config=config, token=config.api_token)
        print(json.dumps({'startup_smoke': result}, ensure_ascii=False, indent=2))
        if not result['passed']:
            raise SystemExit(1)

    run_server(config=config, host=args.host, port=args.port)


if __name__ == '__main__':
    main()
