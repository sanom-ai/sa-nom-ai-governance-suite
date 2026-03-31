from importlib import import_module

from _bootstrap import ensure_repo_root_on_path


MODULE_PATH = "sa_nom_governance.guards.bootstrap_access_profiles"


def main() -> int:
    ensure_repo_root_on_path()
    module = import_module(MODULE_PATH)
    result = module.main()
    return result if isinstance(result, int) else 0


if __name__ == "__main__":
    raise SystemExit(main())
