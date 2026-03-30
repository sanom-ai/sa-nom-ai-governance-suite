from _bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from sa_nom_governance.compliance.trusted_registry_refresh import *
from sa_nom_governance.compliance.trusted_registry_refresh import main

if __name__ == '__main__':
    main()
