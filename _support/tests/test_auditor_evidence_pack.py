from sa_nom_governance.api.api_engine import build_engine_app
from sa_nom_governance.utils.config import AppConfig


def build_test_app():
    return build_engine_app(AppConfig(persist_runtime=False))


def test_evidence_export_creates_manifest() -> None:
    app = build_test_app()
    result = app.create_evidence_pack(requested_by='Executive Owner Test')
    assert result['pack_id'].startswith('evidence-')
    assert result['artifact_total'] >= 1
    assert result['go_live_status'] in {'ready', 'blocked'}
