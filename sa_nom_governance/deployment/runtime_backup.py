import json
from argparse import ArgumentParser

from sa_nom_governance.api.api_engine import build_engine_app
from sa_nom_governance.utils.config import AppConfig


def main() -> None:
    parser = ArgumentParser(description='Create a runtime operations backup bundle for SA-NOM AI Governance Suite.')
    parser.add_argument('--requested-by', default='SYSTEM_OPERATIONS')
    args = parser.parse_args()

    app = build_engine_app(AppConfig())
    result = app.create_runtime_backup(requested_by=args.requested_by)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
