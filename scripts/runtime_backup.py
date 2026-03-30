from _bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from sa_nom_governance.deployment.runtime_backup import *
from sa_nom_governance.deployment.runtime_backup import main

if __name__ == '__main__':
    main()
