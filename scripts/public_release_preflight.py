from _bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from sa_nom_governance.deployment.public_release_preflight import *
from sa_nom_governance.deployment.public_release_preflight import main

if __name__ == '__main__':
    raise SystemExit(main())
