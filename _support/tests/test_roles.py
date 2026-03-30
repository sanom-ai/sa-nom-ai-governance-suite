from pathlib import Path
from tempfile import TemporaryDirectory

import json
import pytest

from registry import RoleRegistry
from role_loader import RoleLoader
from trusted_registry import TrustedRegistryError, write_trusted_registry_files


BASE_DIR = Path(__file__).resolve().parent
DEV_SIGNING_KEY = "sanom-dev-registry-key"
TEST_SIGNING_KEY = "test-registry-signing-key"
TEST_KEY_ID = "TEST_REGISTRY"


def test_role_loader_loads_gov_role() -> None:
    registry = RoleRegistry(
        BASE_DIR,
        manifest_path=BASE_DIR / "trusted_registry_manifest.json",
        cache_path=BASE_DIR / "trusted_registry_cache.json",
        signing_key=DEV_SIGNING_KEY,
    )
    loader = RoleLoader(registry)
    document = loader.load("GOV")
    assert "GOV" in document.roles
    assert "review_audit" in document.authorities["GOV"].allow
    assert document.headers["trusted_source_origin"] == "trusted_registry"
    assert document.headers["trusted_manifest_signature_status"] == "verified"


def test_role_loader_uses_last_known_good_when_live_role_file_changes() -> None:
    with TemporaryDirectory(dir=BASE_DIR) as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        source_path = BASE_DIR / "GOV.ptn"
        temp_role_path = temp_dir / "GOV.ptn"
        temp_role_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")

        manifest_path = temp_dir / "trusted_registry_manifest.json"
        cache_path = temp_dir / "trusted_registry_cache.json"
        write_trusted_registry_files(
            roles_dir=temp_dir,
            manifest_path=manifest_path,
            cache_path=cache_path,
            role_ids=["GOV"],
            signing_key=TEST_SIGNING_KEY,
            key_id=TEST_KEY_ID,
        )

        temp_role_path.write_text(temp_role_path.read_text(encoding="utf-8") + "\n# tampered\n", encoding="utf-8")

        registry = RoleRegistry(
            temp_dir,
            manifest_path=manifest_path,
            cache_path=cache_path,
            signing_key=TEST_SIGNING_KEY,
        )
        loader = RoleLoader(registry)
        document = loader.load("GOV")

        assert document.headers["trusted_source_origin"] == "last_known_good"
        assert any(issue.code == "REGISTRY_FALLBACK_USED" for issue in document.validation_issues)


def test_role_loader_rejects_role_without_trusted_manifest_entry() -> None:
    with TemporaryDirectory(dir=BASE_DIR) as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        temp_role_path = temp_dir / "GOV.ptn"
        temp_role_path.write_text((BASE_DIR / "GOV.ptn").read_text(encoding="utf-8"), encoding="utf-8")
        manifest_path = temp_dir / "trusted_registry_manifest.json"
        cache_path = temp_dir / "trusted_registry_cache.json"
        manifest_path.write_text('{"registry_name": "test", "roles": {}, "signature": {"algorithm": "hmac_sha256", "key_id": "test", "signed_at": "now", "value": "deadbeef"}}', encoding="utf-8")
        cache_path.write_text('{"entries": {}}', encoding="utf-8")

        registry = RoleRegistry(
            temp_dir,
            manifest_path=manifest_path,
            cache_path=cache_path,
            signing_key=TEST_SIGNING_KEY,
        )
        loader = RoleLoader(registry)

        with pytest.raises(TrustedRegistryError):
            loader.load("GOV")


def test_role_loader_rejects_invalid_manifest_signature() -> None:
    with TemporaryDirectory(dir=BASE_DIR) as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        source_path = BASE_DIR / "GOV.ptn"
        temp_role_path = temp_dir / "GOV.ptn"
        temp_role_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")

        manifest_path = temp_dir / "trusted_registry_manifest.json"
        cache_path = temp_dir / "trusted_registry_cache.json"
        write_trusted_registry_files(
            roles_dir=temp_dir,
            manifest_path=manifest_path,
            cache_path=cache_path,
            role_ids=["GOV"],
            signing_key=TEST_SIGNING_KEY,
            key_id=TEST_KEY_ID,
        )

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["signature"]["value"] = "invalid-signature"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        registry = RoleRegistry(
            temp_dir,
            manifest_path=manifest_path,
            cache_path=cache_path,
            signing_key=TEST_SIGNING_KEY,
        )
        loader = RoleLoader(registry)

        with pytest.raises(TrustedRegistryError):
            loader.load("GOV")
