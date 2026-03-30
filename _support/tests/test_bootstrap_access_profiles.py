from sa_nom_governance.guards.bootstrap_access_profiles import build_profiles


def test_bootstrap_access_profiles_delegate_privileged_operator_permissions() -> None:
    profiles, token_bundle = build_profiles(days_valid=365, rotate_days=180)

    operator_profile = next(item for item in profiles if item["role_name"] == "operator")
    permissions = set(operator_profile["permissions"])

    assert {
        "session.manage",
        "retention.manage",
        "audit.manage",
        "ops.manage",
        "studio.publish",
    }.issubset(permissions)
    assert len(token_bundle["profiles"]) == 4


def test_bootstrap_access_profiles_reject_invalid_lifetimes() -> None:
    invalid_cases = [
        (0, 180, "days_valid"),
        (365, 0, "rotate_days"),
        (30, 30, "rotate_days"),
        (30, 45, "rotate_days"),
    ]

    for days_valid, rotate_days, expected_label in invalid_cases:
        try:
            build_profiles(days_valid=days_valid, rotate_days=rotate_days)
        except ValueError as exc:
            assert expected_label in str(exc)
        else:
            raise AssertionError(
                f"Expected build_profiles(days_valid={days_valid}, rotate_days={rotate_days}) to fail."
            )
