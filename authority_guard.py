from ptag_semantic import SemanticDocument


class AuthorityGuard:
    def ensure_action_allowed(self, role_document: SemanticDocument, action: str) -> None:
        if not role_document.roles:
            raise PermissionError("No role definition loaded for document.")

        role_id = next(iter(role_document.roles))
        authority = role_document.authorities.get(role_id)
        if authority is None:
            raise PermissionError(f"No authority block defined for role: {role_id}")

        if action in authority.deny:
            raise PermissionError(f"Action explicitly denied: {action}")

        if authority.allow and action not in authority.allow and action not in authority.require:
            raise PermissionError(f"Action not granted for role {role_id}: {action}")
