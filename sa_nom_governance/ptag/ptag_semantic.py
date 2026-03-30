from dataclasses import dataclass, field

from sa_nom_governance.ptag.ptag_ast import PTAGDocument


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    return value


def _split_csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(',') if part.strip()]


def _extract_action_reference(condition: str) -> str | None:
    if not condition.startswith('action =='):
        return None
    return condition.split('==', 1)[1].strip().strip('"')


def _extract_constraint_action(line: str) -> str | None:
    line = line.strip()
    if line.startswith('forbid ') and ' to ' in line:
        return line.rsplit(' to ', 1)[1].strip()
    if line.startswith('require ') and ' for ' in line:
        return line.rsplit(' for ', 1)[1].strip()
    return None


@dataclass(slots=True)
class ValidationIssue:
    severity: str
    code: str
    message: str
    role_id: str | None = None
    action: str | None = None


@dataclass(slots=True)
class RoleDefinition:
    role_id: str
    fields: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class AuthorityDefinition:
    role_id: str
    allow: set[str] = field(default_factory=set)
    deny: set[str] = field(default_factory=set)
    require: dict[str, list[str]] = field(default_factory=dict)


@dataclass(slots=True)
class ConstraintDefinition:
    constraint_id: str
    body: list[str] = field(default_factory=list)
    action_refs: set[str] = field(default_factory=set)


@dataclass(slots=True)
class PolicyDefinition:
    policy_id: str
    body: list[str] = field(default_factory=list)
    conditions: list[str] = field(default_factory=list)
    action_refs: set[str] = field(default_factory=set)


@dataclass(slots=True)
class SemanticDocument:
    headers: dict[str, str]
    roles: dict[str, RoleDefinition] = field(default_factory=dict)
    authorities: dict[str, AuthorityDefinition] = field(default_factory=dict)
    constraints: dict[str, ConstraintDefinition] = field(default_factory=dict)
    policies: dict[str, PolicyDefinition] = field(default_factory=dict)
    validation_issues: list[ValidationIssue] = field(default_factory=list)


class SemanticAnalyzer:
    def analyze(self, document: PTAGDocument) -> SemanticDocument:
        semantic = SemanticDocument(headers=document.headers.copy())
        for block in document.blocks:
            if block.name.startswith('role '):
                role_id = block.name.split(' ', 1)[1]
                semantic.roles[role_id] = self._parse_role(role_id, block.body)
            elif block.name.startswith('authority '):
                role_id = block.name.split(' ', 1)[1]
                semantic.authorities[role_id] = self._parse_authority(role_id, block.body)
            elif block.name.startswith('constraint '):
                constraint_id = block.name.split(' ', 1)[1]
                semantic.constraints[constraint_id] = self._parse_constraint(constraint_id, block.body)
            elif block.name.startswith('policy '):
                policy_id = block.name.split(' ', 1)[1]
                semantic.policies[policy_id] = self._parse_policy(policy_id, block.body)
        return semantic

    def _parse_role(self, role_id: str, body: str) -> RoleDefinition:
        fields: dict[str, object] = {}
        for raw_line in body.splitlines():
            line = raw_line.strip()
            if not line or ':' not in line:
                continue
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            if value.startswith('[') and value.endswith(']'):
                items = value[1:-1].strip()
                fields[key] = _split_csv(items) if items else []
            elif value.isdigit():
                fields[key] = int(value)
            else:
                fields[key] = _strip_quotes(value)
        return RoleDefinition(role_id=role_id, fields=fields)

    def _parse_authority(self, role_id: str, body: str) -> AuthorityDefinition:
        authority = AuthorityDefinition(role_id=role_id)
        for raw_line in body.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith('allow:'):
                authority.allow.update(_split_csv(line.split(':', 1)[1].strip()))
                continue
            if line.startswith('deny:'):
                authority.deny.update(_split_csv(line.split(':', 1)[1].strip()))
                continue
            if line.startswith('require '):
                remainder = line.removeprefix('require ').strip()
                if ' for ' not in remainder:
                    continue
                requirement, action = remainder.split(' for ', 1)
                authority.require.setdefault(action.strip(), []).append(requirement.strip())
        return authority

    def _parse_constraint(self, constraint_id: str, body: str) -> ConstraintDefinition:
        lines = [line.strip() for line in body.splitlines() if line.strip()]
        action_refs = {action for line in lines if (action := _extract_constraint_action(line)) is not None}
        return ConstraintDefinition(constraint_id=constraint_id, body=lines, action_refs=action_refs)

    def _parse_policy(self, policy_id: str, body: str) -> PolicyDefinition:
        lines = [line.strip() for line in body.splitlines() if line.strip()]
        conditions = [line.removeprefix('when ').strip() for line in lines if line.startswith('when ')]
        conditions.extend(line.removeprefix('and ').strip() for line in lines if line.startswith('and '))
        action_refs = {action for condition in conditions if (action := _extract_action_reference(condition)) is not None}
        return PolicyDefinition(policy_id=policy_id, body=lines, conditions=conditions, action_refs=action_refs)
