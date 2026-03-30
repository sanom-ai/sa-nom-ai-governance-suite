from sa_nom_governance.api.api_engine import build_engine_app
from sa_nom_governance.utils.config import AppConfig


def build_test_app():
    return build_engine_app(AppConfig(persist_runtime=False))


def test_compliance_snapshot_returns_frameworks() -> None:
    app = build_test_app()
    snapshot = app.compliance_snapshot()
    framework_ids = {item['framework_id'] for item in snapshot['frameworks']}
    assert snapshot['summary']['frameworks_total'] >= 6
    assert {'THAI_BANKING_BASELINE', 'THAI_GOVERNMENT_BASELINE'} <= framework_ids


def test_evidence_pack_summary_is_available() -> None:
    app = build_test_app()
    summary = app.evidence_pack_summary()
    assert 'exports_total' in summary
