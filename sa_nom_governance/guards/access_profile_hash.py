from argparse import ArgumentParser
from collections.abc import Sequence

from sa_nom_governance.guards.access_control import hash_token


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(description='Generate a SHA-256 token hash for SA-NOM access profiles.')
    parser.add_argument('token')
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    print(hash_token(args.token))


if __name__ == '__main__':
    main()
