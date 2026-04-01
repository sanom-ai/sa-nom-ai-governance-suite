from dataclasses import dataclass, field

from sa_nom_governance.ptag.ptag_ast import PTAGDocument


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    return value


def _split_csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(',') if part.strip()]


def _split_top_level_csv(value: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    quote_char: str | None = None
    depth = 0

    for char in value:
        if quote_char is not None:
            current.append(char)
            if char == quote_char:
                quote_char = None
            continue

        if char in {'"', "'"}:
            quote_char = char
            current.append(char)
            continue

        if char in '([{':
            depth += 1
            current.append(char)
            continue

        if char in ')]}':
            depth = max(0, depth - 1)
            current.append(char)
            continue

        if char == ',' and depth == 0:
            part = ''.join(current).strip()
            if part:
                parts.append(part)
            current = []
            continue

        current.append(char)

    part = ''.join(current).strip()
    if part:
        parts.append(part)
    return parts


def _split_top_level_keyword(value: str, keyword: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    quote_char: str | None = None
    depth = 0
    upper_value = value.upper()
    keyword = keyword.upper()
    keyword_len = len(keyword)
    index = 0

    while index < len(value):
        char = value[index]
        if quote_char is not None:
            current.append(char)
            if char == quote_char:
                quote_char = None
            index += 1
            continue

        if char in {'"', "'"}:
            quote_char = char
            current.append(char)
            index += 1
            continue

        if char in '([{':
            depth += 1
            current.append(char)
            index += 1
            continue

        if char in ')]}':
            depth = max(0, depth - 1)
            current.append(char)
            index += 1
            continue

        candidate = upper_value[index:index + keyword_len]
        prev_ok = index == 0 or value[index - 1].isspace()
        next_index = index + keyword_len
        next_ok = next_index >= len(value) or value[next_index].isspace()
        if depth == 0 and candidate == keyword and prev_ok and next_ok:
            part = ''.join(current).strip()
            if part:
                parts.append(part)
            current = []
            index += keyword_len
            while index < len(value) and value[index].isspace():
                index += 1
            continue

        current.append(char)
        index += 1

    part = ''.join(current).strip()
    if part:
        parts.append(part)
    return parts


def _keyword_payload(line: str, keyword: str) -> str | None:
    stripped = line.strip()
    prefix = f'{keyword} '
    if stripped.lower().startswith(prefix):
        return stripped[len(prefix):].strip()
    if stripped.lower() == keyword:
        return ''
    return None


def _split_condition_clauses(value: str) -> list[str]:
    return [part.strip() for part in _split_top_level_keyword(value, 'AND') if part.strip()]


def _split_action_clauses(value: str) -> list[str]:
    return _split_top_level_csv(value)


def _extract_action_references(condition: str) -> set[str]:
    lower_condition = condition.lower()
    if lower_condition.startswith('action =='):
        return {condition.split('==', 1)[1].strip().strip('"')}
    if not lower_condition.startswith('action in'):
        return set()
    payload = condition[len('action in'):].strip()
    if not (payload.startswith('[') and payload.endswith(']')):
        return set()
    return {item.strip().strip('"') for item in _split_top_level_csv(payload[1:-1].strip()) if item.strip()}


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
    then_actions: list[str] = field(default_factory=list)
    else_actions: list[str] = field(default_factory=list)
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
        conditions: list[str] = []
        then_actions: list[str] = []
        else_actions: list[str] = []

        for line in lines:
            if (payload := _keyword_payload(line, 'when')) is not None:
                conditions.extend(_split_condition_clauses(payload))
                continue
            if (payload := _keyword_payload(line, 'and')) is not None:
                conditions.extend(_split_condition_clauses(payload))
                continue
            if (payload := _keyword_payload(line, 'then')) is not None:
                then_actions.extend(_split_action_clauses(payload))
                continue
            if (payload := _keyword_payload(line, 'else')) is not None:
                else_actions.extend(_split_action_clauses(payload))

        action_refs: set[str] = set()
        for condition in conditions:
            action_refs.update(_extract_action_references(condition))

        return PolicyDefinition(
            policy_id=policy_id,
            body=lines,
            conditions=conditions,
            then_actions=then_actions,
            else_actions=else_actions,
            action_refs=action_refs,
        )
