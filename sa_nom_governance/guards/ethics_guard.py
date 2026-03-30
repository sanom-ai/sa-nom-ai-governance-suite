from sa_nom_governance.core.execution_context import ExecutionContext


class EthicsGuard:
    def ensure_allowed(self, context: ExecutionContext) -> None:
        banned_actions = {"coerce_user", "bypass_ethics"}
        if context.action in banned_actions:
            raise PermissionError(f"Action blocked by ethics policy: {context.action}")
