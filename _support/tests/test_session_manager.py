import json
from pathlib import Path
from tempfile import TemporaryDirectory

from access_control import AccessControl, hash_token
from config import AppConfig


class FakeHeaders(dict):
    def get(self, key, default=None):
        return super().get(key, default)


def test_session_issue_authenticate_and_revoke() -> None:
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
        config = AppConfig(base_dir=temp_dir, persist_runtime=True)
        control = AccessControl(config)

        auth_result, payload = control.issue_session_from_headers(FakeHeaders({"X-SA-NOM-Token": "secret-token"}))
        assert auth_result.authenticated is True
        assert payload is not None
        assert payload["session_token"]

        session_result = control.authenticate_result(FakeHeaders({"X-SA-NOM-Session": payload["session_token"]}))
        assert session_result.authenticated is True
        assert session_result.auth_method == "session"

        revoke_result = control.revoke_session_from_headers(FakeHeaders({"X-SA-NOM-Session": payload["session_token"]}))
        assert revoke_result["success"] is True

        denied = control.authenticate_result(FakeHeaders({"X-SA-NOM-Session": payload["session_token"]}))
        assert denied.authenticated is False
        assert denied.reason == "revoked_session"


def test_access_control_rejects_not_yet_active_profile() -> None:
    with TemporaryDirectory() as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        profile_path = temp_dir / "access_profiles.json"
        profile_path.write_text(
            json.dumps(
                [
                    {
                        "profile_id": "future-reviewer",
                        "display_name": "Future Reviewer",
                        "role_name": "reviewer",
                        "token_hash": hash_token("future-token"),
                        "not_before": "2099-01-01T00:00:00+00:00",
                    }
                ],
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        config = AppConfig(base_dir=temp_dir, persist_runtime=False)
        control = AccessControl(config)
        result = control.authenticate_result(FakeHeaders({"X-SA-NOM-Token": "future-token"}))
        assert result.authenticated is False
        assert result.reason == "not_yet_active_profile"
