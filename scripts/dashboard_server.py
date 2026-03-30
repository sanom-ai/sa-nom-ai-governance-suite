from _bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from sa_nom_governance.dashboard.dashboard_server import *
from sa_nom_governance.dashboard.dashboard_server import main

if __name__ == '__main__':
    main()
