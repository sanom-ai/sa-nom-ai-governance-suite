import shutil
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from access_control import AccessControl
from config import AppConfig
from owner_registration import (
    OwnerRegistration,
    build_owner_registration,
    load_owner_registration,
    utc_now,
    write_owner_registration,
)


@contextmanager
def workspace_temp_dir():
    source_base = Path(__file__).resolve().parents[2]
    runtime_tmp = source_base / "_runtime" / "tmp_test"
    runtime_tmp.mkdir(parents=True, exist_ok=True)
    temp_path = runtime_tmp / f"owner_registration_{uuid4().hex[:8]}"
    temp_path.mkdir(parents=True, exist_ok=True)
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


def test_access_control_owner_profile_uses_registered_owner_name() -> None:
    with workspace_temp_dir() as temp_path:
        config = AppConfig(
            base_dir=temp_path,
            environment="development",
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

        access_control = AccessControl(config)
        owner_profile = next(profile for profile in access_control.list_public_profiles() if profile["profile_id"] == "owner")

        assert owner_profile["display_name"] == "Aree Executive Owner"
        assert config.deployment_mode() == "private"
        assert config.organization_id() == "EXAMPLE_ORG"
        assert config.executive_owner_id() == "AREE"
        assert config.trusted_registry_signed_by == "Aree"


def test_owner_registration_can_be_derived_from_registration_code_only() -> None:
    registration = build_owner_registration({"registration_code": "tower-hq-01"})

    assert registration.registration_code == "TOWER-HQ-01"
    assert registration.organization_name == "TOWER-HQ-01"
    assert registration.organization_id == "TOWER_HQ_01"
    assert registration.owner_name == "Executive Owner"
    assert registration.owner_display_name == "Executive Owner"
    assert registration.executive_owner_id == "TOWER_HQ_01"
    assert registration.trusted_registry_signed_by == "TOWER_HQ_01"
    assert registration.deployment_mode == "private"


def test_owner_registration_requires_registration_code_for_first_registration() -> None:
    try:
        build_owner_registration({})
    except ValueError as exc:
        assert "registration_code is required" in str(exc)
    else:
        raise AssertionError("Expected build_owner_registration({}) to require a registration code.")


def test_owner_registration_supports_multi_mode_identity() -> None:
    with workspace_temp_dir() as temp_path:
        registration_path = temp_path / "_runtime" / "owner_registration.json"
        write_owner_registration(
            registration_path,
            OwnerRegistration(
                registration_code="ALLIANCE-GOVERNANCE-GROUP",
                deployment_mode="multi",
                organization_name="Alliance Governance Group",
                organization_id="ALLIANCE_GOVERNANCE_GROUP",
                owner_name="Nalin",
                owner_display_name="Nalin Group Executive",
                executive_owner_id="NALIN",
                trusted_registry_signed_by="Nalin",
                registered_at=utc_now(),
            ),
            force=True,
        )

        registration = load_owner_registration(registration_path)

        assert registration is not None
        assert registration.deployment_mode == "multi"
        assert registration.organization_id == "ALLIANCE_GOVERNANCE_GROUP"
        assert registration.executive_owner_id == "NALIN"


def test_owner_registration_roundtrip_preserves_registered_at() -> None:
    with workspace_temp_dir() as temp_path:
        registration_path = temp_path / "_runtime" / "owner_registration.json"
        expected_registered_at = "2026-03-30T00:00:00+00:00"
        write_owner_registration(
            registration_path,
            OwnerRegistration(
                registration_code="ROUNDTRIP-ORG",
                deployment_mode="private",
                organization_name="Roundtrip Org",
                organization_id="ROUNDTRIP_ORG",
                owner_name="Rin",
                owner_display_name="Rin Executive Owner",
                executive_owner_id="RIN",
                trusted_registry_signed_by="Rin",
                registered_at=expected_registered_at,
            ),
            force=True,
        )

        registration = load_owner_registration(registration_path)

        assert registration is not None
        assert registration.registered_at == expected_registered_at
