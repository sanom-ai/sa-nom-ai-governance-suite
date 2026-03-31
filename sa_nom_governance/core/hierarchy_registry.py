from dataclasses import dataclass, field

from sa_nom_governance.core.execution_context import ExecutionContext
from sa_nom_governance.ptag.role_loader import RoleLoader
from sa_nom_governance.utils.owner_identity import (
    DEFAULT_EXECUTIVE_OWNER_ID,
    is_default_owner_alias,
    normalize_executive_owner_id,
)


def _normalize_token(value: object | None) -> str | None:
    if value is None:
        return None
    token = str(value).strip()
    return token or None


def _normalize_upper_token(value: object | None) -> str | None:
    token = _normalize_token(value)
    return token.upper() if token is not None else None


def _resource_tokens(payload: dict[str, object]) -> set[str]:
    tokens: set[str] = set()
    for key in ("resource", "resource_type", "domain_resource"):
        value = _normalize_token(payload.get(key))
        if value is not None:
            tokens.add(value.lower())
    return tokens


@dataclass(slots=True)
class HierarchyEntry:
    role_id: str
    title: str
    stratum: int
    reports_to: str | None
    escalation_to: str | None
    safety_owner: str | None
    business_domain: str | None
    handled_resources: set[str] = field(default_factory=set)
    allowed_actions: set[str] = field(default_factory=set)
    required_human_actions: set[str] = field(default_factory=set)
    denied_actions: set[str] = field(default_factory=set)
    operating_mode: str = "direct"
    assigned_user_id: str | None = None
    executive_owner_id: str | None = None
    seat_id: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "role_id": self.role_id,
            "title": self.title,
            "stratum": self.stratum,
            "reports_to": self.reports_to,
            "escalation_to": self.escalation_to,
            "safety_owner": self.safety_owner,
            "business_domain": self.business_domain,
            "handled_resources": sorted(self.handled_resources),
            "allowed_actions": sorted(self.allowed_actions),
            "required_human_actions": sorted(self.required_human_actions),
            "denied_actions": sorted(self.denied_actions),
            "operating_mode": self.operating_mode,
            "assigned_user_id": self.assigned_user_id,
            "executive_owner_id": self.executive_owner_id,
            "seat_id": self.seat_id,
        }


@dataclass(slots=True)
class HierarchyEscalationDecision:
    rule_id: str
    escalated_to: str
    reason: str
    notes: list[str] = field(default_factory=list)


class HierarchyRegistry:
    SAFETY_DOMAINS = {"product_safety", "safety", "safety_operations"}
    SAFETY_RESOURCES = {"product_safety", "safety", "safety_incident", "safety_event", "safety_case"}

    def __init__(self, role_loader: RoleLoader, default_executive_owner_id: str = DEFAULT_EXECUTIVE_OWNER_ID) -> None:
        self.role_loader = role_loader
        self.default_executive_owner_id = normalize_executive_owner_id(
            default_executive_owner_id,
            fallback=DEFAULT_EXECUTIVE_OWNER_ID,
        )
        self._entries: dict[str, HierarchyEntry] | None = None

    def reload(self) -> None:
        self._entries = None

    def entries(self) -> dict[str, HierarchyEntry]:
        if self._entries is None:
            self._entries = self._load_entries()
        return self._entries

    def get(self, role_id: str) -> HierarchyEntry | None:
        return self.entries().get(role_id)

    def list_entries(self) -> list[HierarchyEntry]:
        return list(self.entries().values())

    def default_escalation_target(self, role_id: str) -> str:
        entry = self.get(role_id)
        if entry is None:
            return self.default_executive_owner_id
        return entry.escalation_to or entry.reports_to or entry.executive_owner_id or self.default_executive_owner_id

    def evaluate_escalation(self, context: ExecutionContext) -> HierarchyEscalationDecision | None:
        entry = self.get(context.role_id)
        if entry is None:
            return None

        business_domain = self._context_business_domain(context, entry)
        resources = _resource_tokens(context.payload)
        action_token = context.action.lower()

        if business_domain in self.SAFETY_DOMAINS or resources.intersection(self.SAFETY_RESOURCES):
            escalated_to = entry.safety_owner or entry.escalation_to or entry.executive_owner_id or self.default_executive_owner_id
            return HierarchyEscalationDecision(
                rule_id=f"{context.role_id}.product_safety_override",
                escalated_to=escalated_to,
                reason=f"Safety-sensitive context requires immediate human review for role {context.role_id}.",
                notes=[
                    f"business_domain={business_domain or '-'}",
                    f"resources={sorted(resources) or ['-']}",
                    "Hierarchy escalation matrix routed this request to human override.",
                ],
            )

        if entry.stratum <= 0 and action_token in {"emergency_stop", "suspend_role"} and context.risk_score >= 0.50:
            escalated_to = entry.escalation_to or entry.executive_owner_id or self.default_executive_owner_id
            return HierarchyEscalationDecision(
                rule_id=f"{context.role_id}.director_high_risk_override",
                escalated_to=escalated_to,
                reason=f"High-authority action {context.action} requires human escalation for role {context.role_id}.",
                notes=[
                    f"stratum={entry.stratum}",
                    f"risk_score={context.risk_score:.2f}",
                    "Director-level authority crossed the high-risk threshold.",
                ],
            )

        return None

    def _load_entries(self) -> dict[str, HierarchyEntry]:
        entries: dict[str, HierarchyEntry] = {}
        for path in sorted(self.role_loader.registry.roles_dir.glob("*.ptn")):
            role_id = path.stem
            if role_id.lower() == "core_terms":
                continue
            try:
                document = self.role_loader.load(role_id)
            except Exception:
                continue
            role = document.roles.get(role_id)
            authority = document.authorities.get(role_id)
            if role is None or authority is None:
                continue

            fields = role.fields
            reports_to = self._resolve_role_owner_token(fields.get("reports_to"))
            if reports_to == "NONE":
                reports_to = None
            executive_owner_id = self._resolve_owner_identifier(fields.get("executive_owner_id"))
            escalation_to = self._resolve_role_owner_token(fields.get("escalation_to")) or reports_to or executive_owner_id
            safety_owner = self._resolve_role_owner_token(fields.get("safety_owner")) or escalation_to or executive_owner_id
            business_domain = _normalize_token(fields.get("business_domain"))
            assigned_user_id = _normalize_token(fields.get("assigned_user_id"))
            operating_mode = (_normalize_token(fields.get("operating_mode")) or ("indirect" if assigned_user_id else "direct")).lower()
            if operating_mode not in {"indirect", "direct"}:
                operating_mode = "indirect" if assigned_user_id else "direct"
            if operating_mode == "direct":
                assigned_user_id = None
            seat_id = _normalize_token(fields.get("seat_id"))
            handled_resources = self._extract_handled_resources(fields, document)

            entries[role_id] = HierarchyEntry(
                role_id=role_id,
                title=str(fields.get("title", role_id)),
                stratum=int(fields.get("stratum", 99)),
                reports_to=reports_to,
                escalation_to=escalation_to,
                safety_owner=safety_owner,
                business_domain=business_domain,
                handled_resources=handled_resources,
                allowed_actions=set(authority.allow),
                required_human_actions=set(authority.require.keys()),
                denied_actions=set(authority.deny),
                operating_mode=operating_mode,
                assigned_user_id=assigned_user_id,
                executive_owner_id=executive_owner_id,
                seat_id=seat_id,
            )
        return entries

    def _extract_handled_resources(self, fields: dict[str, object], document) -> set[str]:
        handled_resources = fields.get("handled_resources", [])
        if isinstance(handled_resources, list):
            return {str(value).strip().lower() for value in handled_resources if str(value).strip()}

        discovered: set[str] = set()
        for policy in document.policies.values():
            for condition in policy.conditions:
                if not condition.startswith("resource =="):
                    continue
                token = condition.split("==", 1)[1].strip().strip('"').lower()
                if token:
                    discovered.add(token)
        return discovered

    def _context_business_domain(self, context: ExecutionContext, entry: HierarchyEntry) -> str | None:
        metadata = context.metadata
        value = (
            context.payload.get("business_domain")
            or metadata.get("business_domain")
            or metadata.get("domain")
            or entry.business_domain
        )
        token = _normalize_token(value)
        return token.lower() if token is not None else None

    def _resolve_owner_identifier(self, value: object | None) -> str:
        return normalize_executive_owner_id(value, fallback=self.default_executive_owner_id)

    def _resolve_role_owner_token(self, value: object | None) -> str | None:
        token = _normalize_upper_token(value)
        if token is None:
            return None
        if is_default_owner_alias(token, include_empty=False):
            return self.default_executive_owner_id
        return token
