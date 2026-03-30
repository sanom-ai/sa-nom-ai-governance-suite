from api_engine import build_engine_app
from config import AppConfig


def build_test_app():
    return build_engine_app(AppConfig(persist_runtime=False))


def test_compliance_snapshot_returns_frameworks() -> None:
    app = build_test_app()
    snapshot = app.compliance_snapshot()
    assert snapshot['summary']['frameworks_total'] >= 4
    assert 'frameworks' in snapshot


def test_evidence_pack_summary_is_available() -> None:
    app = build_test_app()
    summary = app.evidence_pack_summary()
    assert 'exports_total' in summary
