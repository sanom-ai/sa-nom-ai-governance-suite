from argparse import ArgumentParser

from sa_nom_governance.guards.access_control import hash_token


def main() -> None:
    parser = ArgumentParser(description="Generate a SHA-256 token hash for SA-NOM access profiles.")
    parser.add_argument("token")
    args = parser.parse_args()
    print(hash_token(args.token))


if __name__ == "__main__":
    main()
