import pytest

from ethics_guard import EthicsGuard
from execution_context import ExecutionContext


def test_ethics_guard_blocks_banned_action() -> None:
    context = ExecutionContext(requester="tester", action="coerce_user", role_id="GOV")
    with pytest.raises(PermissionError):
        EthicsGuard().ensure_allowed(context)
