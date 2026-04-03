import json
from argparse import ArgumentParser
from collections.abc import Sequence

from sa_nom_governance.api.api_engine import build_engine_app
from sa_nom_governance.utils.config import AppConfig


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(description='Reseal legacy audit entries into a fully chained SA-NOM audit log.')
    parser.add_argument('--requested-by', default='SYSTEM_MAINTENANCE')
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(list(argv) if argv is not None else None)

    app = build_engine_app(AppConfig())
    result = app.reseal_audit_log(requested_by=args.requested_by)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
