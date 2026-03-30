from _bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from sa_nom_governance.audit.audit_reseal import *
from sa_nom_governance.audit.audit_reseal import main

if __name__ == '__main__':
    main()
