from pathlib import Path
from tempfile import TemporaryDirectory

from sa_nom_governance.api.api_engine import build_engine_app
from sa_nom_governance.utils.config import AppConfig


def build_test_app(base_dir: Path):
    return build_engine_app(AppConfig(base_dir=base_dir, persist_runtime=True))


def test_evidence_export_creates_manifest_with_integrity_contract() -> None:
    with TemporaryDirectory() as temp_dir:
        app = build_test_app(Path(temp_dir))
        result = app.create_evidence_pack(requested_by='Executive Owner Test')

        contract = result['integrity_contract']
        assert result['bundle_type'] == 'evidence_pack'
        assert result['pack_id'].startswith('evidence-')
        assert result['artifact_total'] >= 1
        assert result['go_live_status'] in {'ready', 'blocked'}
        assert contract['contract_version'] == 'v0.7.1'
        assert contract['artifact_sha256_total'] == result['artifact_total']
        assert contract['tracked_file_present_total'] >= 1
        assert contract['audit_chain_status'] in {'verified', 'legacy_verified'}
        assert contract['trusted_registry_signature_status'] == 'verified'
        assert contract['tamper_evident'] is True
        assert result['posture'] == 'ready'


def test_evidence_export_detects_trusted_role_mismatch() -> None:
    with TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        app = build_test_app(base_dir)
        role_path = app.registry.resolve('GOV')
        role_path.write_text(role_path.read_text(encoding='utf-8') + '\n# tampered\n', encoding='utf-8')

        result = app.create_evidence_pack(requested_by='Executive Owner Test')
        contract = result['integrity_contract']

        assert contract['trusted_role_mismatch_total'] >= 1
        assert 'GOV' in contract['role_pack_mismatches']
        assert result['posture'] == 'attention_required'
