from sa_nom_governance.api.api_engine import build_engine_app
from sa_nom_governance.utils.config import AppConfig


def create_app(config: AppConfig | None = None):
    resolved_config = config or AppConfig()
    return build_engine_app(resolved_config)


config = AppConfig()
app = create_app(config)
