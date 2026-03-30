from sa_nom_governance.core.execution_context import ExecutionContext
from sa_nom_governance.utils.owner_identity import DEFAULT_EXECUTIVE_OWNER_ID, replace_default_owner_alias


class RequestDispatcher:
    def dispatch(
        self,
        requester: str,
        action: str,
        role_id: str,
        payload: dict,
        request_id: str | None = None,
        metadata: dict | None = None,
    ) -> ExecutionContext:
        metadata_copy = dict(metadata or {})
        role_transition = metadata_copy.get("role_transition", {})
        normalized_requester = replace_default_owner_alias(
            requester,
            fallback=DEFAULT_EXECUTIVE_OWNER_ID,
        )
        return ExecutionContext(
            request_id=request_id or self._build_request_id(),
            requester=normalized_requester,
            action=action,
            role_id=role_id,
            payload=payload,
            metadata=metadata_copy,
            role_transition=dict(role_transition) if isinstance(role_transition, dict) else {},
        )

    def _build_request_id(self) -> str:
        from uuid import uuid4

        return f"request-{uuid4()}"
