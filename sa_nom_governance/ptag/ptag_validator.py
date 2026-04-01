from sa_nom_governance.ptag.ptag_ast import PTAGDocument
from sa_nom_governance.ptag.ptag_semantic import SemanticDocument, ValidationIssue


class PTAGValidator:
    REQUIRED_HEADERS = {"language", "module", "version", "owner"}
    ALLOWED_BLOCK_TYPES = {"role", "authority", "constraint", "policy", "dictionary", "decision", "flow"}

    def validate(self, document: PTAGDocument) -> None:
        missing_headers = self.REQUIRED_HEADERS.difference(document.headers)
        if missing_headers:
            missing = ", ".join(sorted(missing_headers))
            raise ValueError(f"PTAG document missing required headers: {missing}")

        if not document.blocks:
            raise ValueError("PTAG document contains no blocks.")

        unknown_blocks: list[str] = []
        for block in document.blocks:
            block_type = block.name.split(" ", 1)[0]
            if block_type not in self.ALLOWED_BLOCK_TYPES:
                unknown_blocks.append(block.name)

        if unknown_blocks:
            joined = ", ".join(unknown_blocks)
            raise ValueError(f"PTAG document contains unsupported block types: {joined}")

    def validate_semantic(self, semantic: SemanticDocument) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        if not semantic.roles:
            raise ValueError("PTAG semantic document contains no role definitions.")

        for role_id in semantic.roles:
            if role_id not in semantic.authorities:
                raise ValueError(f"Role {role_id} is missing an authority block.")

        for role_id in semantic.authorities:
            if role_id not in semantic.roles:
                raise ValueError(f"Authority block defined for unknown role: {role_id}")

        covered_actions: set[str] = set()
        for policy in semantic.policies.values():
            covered_actions.update(policy.action_refs)
            if not policy.conditions:
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        code="TRIGGER_MISSING_WHEN",
                        message=f"Policy {policy.policy_id} is missing a WHEN condition in its trigger grammar.",
                    )
                )
            if not policy.then_actions:
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        code="TRIGGER_MISSING_THEN",
                        message=f"Policy {policy.policy_id} is missing a THEN action in its trigger grammar.",
                    )
                )
        for constraint in semantic.constraints.values():
            covered_actions.update(constraint.action_refs)

        for role_id, authority in semantic.authorities.items():
            governed_actions = set(authority.allow)
            governed_actions.update(authority.require.keys())
            for action in sorted(governed_actions):
                if action not in covered_actions:
                    issues.append(
                        ValidationIssue(
                            severity="warning",
                            code="POLICY_COVERAGE_GAP",
                            message=f"Role {role_id} grants or requires action {action} without policy or constraint coverage.",
                            role_id=role_id,
                            action=action,
                        )
                    )

        return issues
