from importlib import import_module
from typing import Any

from _bootstrap import ensure_repo_root_on_path


MODULE_PATH = "sa_nom_governance.api.api_engine"

ensure_repo_root_on_path()
_module = import_module(MODULE_PATH)


__all__ = [name for name in dir(_module) if not name.startswith("_")]


def __getattr__(name: str) -> Any:
    return getattr(_module, name)
