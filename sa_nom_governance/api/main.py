from sa_nom_governance.api.api_engine import build_engine_app
from sa_nom_governance.utils.config import AppConfig


config = AppConfig()
app = build_engine_app(config)
