from api_engine import build_engine_app
from config import AppConfig


config = AppConfig()
app = build_engine_app(config)
