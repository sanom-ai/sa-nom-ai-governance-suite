import json
import shutil
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.deployment.deployment_profile import build_deployment_report
from sa_nom_governance.utils.owner_registration import OwnerRegistration, utc_now, write_owner_registration


@contextmanager
def workspace_temp_dir():
    source_base = Path(__file__).resolve().parents[2]
    runtime_tmp = source_base / "_runtime" / "tmp_test"
    runtime_tmp.mkdir(parents=True, exist_ok=True)
    temp_path = runtime_tmp / f"deployment_profile_{uuid4().hex[:8]}"
    temp_path.mkdir(parents=True, exist_ok=True)
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


def _build_config(temp_path: Path, *, environment: str = "development") -> AppConfig:
    config = AppConfig(
        base_dir=temp_path,
        environment=environment,
        api_token="owner-token",
        trusted_registry_signing_key="registry-key",
    )
    assert config.owner_registration_path is not None
    write_owner_registration(
        config.owner_registration_path,
        OwnerRegistration(
            registration_code="EXAMPLE-ORG",
            deployment_mode="private",
            organization_name="Example Org",
            organization_id="EXAMPLE_ORG",
            owner_name="Aree",
            owner_display_name="Aree Executive Owner",
            executive_owner_id="AREE",
            trusted_registry_signed_by="Aree",
            registered_at=utc_now(),
        ),
        force=True,
    )
    if config.trusted_registry_manifest_path is not None:
        config.trusted_registry_manifest_path.write_text(
            json.dumps(
                {
                    "roles": {},
                    "signature": {
                        "algorithm": "hmac_sha256",
                        "key_id": "TEST",
                        "signed_at": "2026-01-01T00:00:00+00:00",
                        "value": "placeholder",
                    },
                }
            ),
            encoding="utf-8",
        )
    return config


def test_deployment_profile_requires_owner_registration_in_production() -> None:
    with workspace_temp_dir() as temp_path:
        config = AppConfig(
            base_dir=temp_path,
            environment="production",
            api_token="owner-token",
            trusted_registry_signing_key="registry-key",
        )
        if config.trusted_registry_manifest_path is not None:
            config.trusted_registry_manifest_path.write_text(
                json.dumps(
                    {
                        "roles": {},
                        "signature": {
                            "algorithm": "hmac_sha256",
                            "key_id": "TEST",
                            "signed_at": "2026-01-01T00:00:00+00:00",
                            "value": "placeholder",
                        },
                    }
                ),
                encoding="utf-8",
            )

        report = build_deployment_report(config).to_dict()
        owner_check = next(item for item in report["checks"] if item["code"] == "OWNER_REGISTRATION_MISSING")

        assert owner_check["status"] == "error"


def test_deployment_profile_warns_when_privileged_permissions_are_owner_only() -> None:
    with workspace_temp_dir() as temp_path:
        config = _build_config(temp_path)
        assert config.access_profiles_path is not None
        config.access_profiles_path.write_text(
            json.dumps(
                [
                    {
                        "profile_id": "operator-one",
                        "display_name": "Operator One",
                        "role_name": "operator",
                        "token_hash": "hash-1",
                    },
                    {
                        "profile_id": "reviewer-one",
                        "display_name": "Reviewer One",
                        "role_name": "reviewer",
                        "token_hash": "hash-2",
                    },
                ]
            ),
            encoding="utf-8",
        )

        report = build_deployment_report(config).to_dict()
        gap_check = next(item for item in report["checks"] if item["code"] == "ACCESS_PROFILES_PRIVILEGED_PERMISSION_GAP")

        assert gap_check["status"] == "warning"
        assert "session.manage" in gap_check["message"]
        assert "studio.publish" in gap_check["message"]


def test_deployment_profile_accepts_delegated_privileged_permissions() -> None:
    with workspace_temp_dir() as temp_path:
        config = _build_config(temp_path, environment="production")
        assert config.access_profiles_path is not None
        config.access_profiles_path.write_text(
            json.dumps(
                [
                    {
                        "profile_id": "operator-one",
                        "display_name": "Operator One",
                        "role_name": "operator",
                        "token_hash": "hash-1",
                        "permissions": [
                            "dashboard.read",
                            "requests.read",
                            "request.create",
                            "studio.read",
                            "studio.create",
                            "human_ask.read",
                            "human_ask.create",
                            "session.manage",
                            "retention.manage",
                            "audit.manage",
                            "ops.manage",
                            "studio.publish",
                        ],
                    },
                    {
                        "profile_id": "reviewer-one",
                        "display_name": "Reviewer One",
                        "role_name": "reviewer",
                        "token_hash": "hash-2",
                    },
                    {
                        "profile_id": "auditor-one",
                        "display_name": "Auditor One",
                        "role_name": "auditor",
                        "token_hash": "hash-3",
                    },
                    {
                        "profile_id": "viewer-one",
                        "display_name": "Viewer One",
                        "role_name": "viewer",
                        "token_hash": "hash-4",
                    },
                ]
            ),
            encoding="utf-8",
        )

        report = build_deployment_report(config).to_dict()
        coverage_check = next(item for item in report["checks"] if item["code"] == "ACCESS_PROFILES_PRIVILEGED_PERMISSION_COVERAGE")

        assert coverage_check["status"] == "ok"


def test_deployment_profile_marks_invalid_access_profiles_without_crashing() -> None:
    with workspace_temp_dir() as temp_path:
        config = _build_config(temp_path, environment="production")
        assert config.access_profiles_path is not None
        config.access_profiles_path.write_text("{bad json", encoding="utf-8")

        report = build_deployment_report(config).to_dict()
        invalid_check = next(item for item in report["checks"] if item["code"] == "ACCESS_PROFILES_INVALID")

        assert report["ready"] is False
        assert invalid_check["status"] == "error"
        assert "invalid JSON" in invalid_check["message"]
