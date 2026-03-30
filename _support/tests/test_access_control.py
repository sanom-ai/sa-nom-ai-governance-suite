import json
from pathlib import Path
from tempfile import TemporaryDirectory

from sa_nom_governance.guards.access_control import AccessControl, hash_token
from sa_nom_governance.utils.config import AppConfig


class FakeHeaders(dict):
    def get(self, key, default=None):
        return super().get(key, default)


def test_access_control_accepts_hashed_token_profiles() -> None:
    with TemporaryDirectory() as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        profile_path = temp_dir / "access_profiles.json"
        profile_path.write_text(
            json.dumps(
                [
                    {
                        "profile_id": "hashed-operator",
                        "display_name": "Hashed Operator",
                        "role_name": "operator",
                        "token_hash": hash_token("secret-token"),
                    }
                ],
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        config = AppConfig(base_dir=temp_dir, persist_runtime=False)
        control = AccessControl(config)
        result = control.authenticate_result(FakeHeaders({"X-SA-NOM-Token": "secret-token"}))
        assert result.authenticated is True
        assert result.profile is not None
        assert result.profile.profile_id == "hashed-operator"


def test_access_control_rejects_expired_profile() -> None:
    with TemporaryDirectory() as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        profile_path = temp_dir / "access_profiles.json"
        profile_path.write_text(
            json.dumps(
                [
                    {
                        "profile_id": "expired-reviewer",
                        "display_name": "Expired Reviewer",
                        "role_name": "reviewer",
                        "token_hash": hash_token("expired-token"),
                        "expires_at": "2020-01-01T00:00:00+00:00",
                    }
                ],
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        config = AppConfig(base_dir=temp_dir, persist_runtime=False)
        control = AccessControl(config)
        result = control.authenticate_result(FakeHeaders({"X-SA-NOM-Token": "expired-token"}))
        assert result.authenticated is False
        assert result.reason == "expired_profile"


def test_access_control_surfaces_invalid_profile_file_without_crashing() -> None:
    with TemporaryDirectory() as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        profile_path = temp_dir / "access_profiles.json"
        profile_path.write_text("{bad json", encoding="utf-8")

        config = AppConfig(
            base_dir=temp_dir,
            environment="production",
            api_token="owner-token",
            trusted_registry_signing_key="registry-key",
            persist_runtime=False,
        )
        control = AccessControl(config)

        health = control.health()
        result = control.authenticate_result(FakeHeaders({"X-SA-NOM-Token": "owner-token"}))

        assert health["access_profile_configuration_valid"] is False
        assert "invalid JSON" in str(health["access_profile_configuration_error"])
        assert [profile["profile_id"] for profile in control.list_public_profiles()] == ["owner"]
        assert result.authenticated is True
        assert result.profile is not None
        assert result.profile.profile_id == "owner"
