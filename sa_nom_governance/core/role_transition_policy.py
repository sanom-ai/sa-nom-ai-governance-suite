import json
from dataclasses import dataclass, field
from pathlib import Path

from sa_nom_governance.core.hierarchy_registry import HierarchyRegistry


def _normalize_role(value: object | None) -> str | None:
    if value is None:
        return None
    token = str(value).strip()
    return token.upper() if token else None


def _normalize_token(value: object | None) -> str | None:
    if value is None:
        return None
    token = str(value).strip()
    return token.lower() if token else None


@dataclass(slots=True)
class TransitionPolicyRule:
    rule_id: str
    from_roles: set[str] = field(default_factory=set)
    to_roles: set[str] = field(default_factory=set)
    activation_sources: set[str] = field(default_factory=set)
    actions: set[str] = field(default_factory=set)
    business_domains: set[str] = field(default_factory=set)
    resources: set[str] = field(default_factory=set)
    decision: str = "allow"
    reason: str = ""
    escalated_to: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "TransitionPolicyRule":
        return cls(
            rule_id=str(data.get("rule_id", "unnamed_rule")),
            from_roles={str(value).upper() for value in data.get("from", []) if str(value).strip()},
            to_roles={str(value).upper() for value in data.get("to", []) if str(value).strip()},
            activation_sources={str(value).strip().lower() for value in data.get("activation_sources", []) if str(value).strip()},
            actions={str(value).strip().lower() for value in data.get("actions", []) if str(value).strip()},
            business_domains={str(value).strip().lower() for value in data.get("business_domains", []) if str(value).strip()},
            resources={str(value).strip().lower() for value in data.get("resources", []) if str(value).strip()},
            decision=str(data.get("decision", "allow")).strip().lower(),
            reason=str(data.get("reason", "Transition rule matched.")).strip(),
            escalated_to=str(data.get("escalated_to")).strip() if data.get("escalated_to") else None,
        )

    def matches(
        self,
        *,
        previous_role: str | None,
        new_role: str | None,
        activation_source: str,
        action: str,
        business_domain: str | None,
        resource: str | None,
    ) -> bool:
        return (
            self._matches(self.from_roles, previous_role, upper=True)
            and self._matches(self.to_roles, new_role, upper=True)
            and self._matches(self.activation_sources, activation_source)
            and self._matches(self.actions, action)
            and self._matches(self.business_domains, business_domain)
            and self._matches(self.resources, resource)
        )

    def _matches(self, allowed: set[str], value: str | None, *, upper: bool = False) -> bool:
        if not allowed or "*" in allowed:
            return True
        if value is None:
            return False
        probe = value.upper() if upper else value.lower()
        return probe in allowed


@dataclass(slots=True)
class TransitionPolicyDecision:
    decision: str
    rule_id: str
    reason: str
    escalated_to: str | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "decision": self.decision,
            "rule_id": self.rule_id,
            "reason": self.reason,
            "escalated_to": self.escalated_to,
            "notes": list(self.notes),
        }


class RoleTransitionPolicyMatrix:
    def __init__(self, hierarchy_registry: HierarchyRegistry, matrix_path: Path | None = None) -> None:
        self.hierarchy_registry = hierarchy_registry
        self.matrix_path = matrix_path or (self.hierarchy_registry.role_loader.registry.roles_dir / "role_transition_matrix.json")
        self.defaults: dict[str, str] = {}
        self.rules: list[TransitionPolicyRule] = []
        self.reload()

    def reload(self) -> None:
        payload = self._load_payload()
        self.defaults = {str(key): str(value) for key, value in payload.get("defaults", {}).items()}
        self.rules = [TransitionPolicyRule.from_dict(item) for item in payload.get("rules", []) if isinstance(item, dict)]

    def health(self) -> dict[str, object]:
        return {
            "status": "configured" if self.rules else "default_only",
            "matrix_path": str(self.matrix_path),
            "configured_rules": len(self.rules),
            "default_same_role": self.defaults.get("same_role", "allow"),
            "default_initial_activation": self.defaults.get("initial_activation", "allow"),
            "default_cross_domain": self.defaults.get("fallback_cross_domain", "block"),
            "fail_closed": True,
        }

    def evaluate(
        self,
        *,
        previous_role: str | None,
        new_role: str | None,
        activation_source: str,
        action: str,
        business_domain: str | None,
        resource: str | None,
    ) -> TransitionPolicyDecision:
        previous_role = _normalize_role(previous_role)
        new_role = _normalize_role(new_role)
        activation_source = str(activation_source).strip().lower()
        action = str(action).strip().lower()
        business_domain = _normalize_token(business_domain)
        resource = _normalize_token(resource)

        for rule in self.rules:
            if not rule.matches(
                previous_role=previous_role,
                new_role=new_role,
                activation_source=activation_source,
                action=action,
                business_domain=business_domain,
                resource=resource,
            ):
                continue
            return TransitionPolicyDecision(
                decision=rule.decision,
                rule_id=rule.rule_id,
                reason=rule.reason,
                escalated_to=self._resolve_escalation_target(rule.escalated_to, previous_role, new_role),
                notes=[
                    f"activation_source={activation_source}",
                    f"action={action}",
                    f"business_domain={business_domain or '-'}",
                    f"resource={resource or '-'}",
                ],
            )

        return self._fallback_decision(
            previous_role=previous_role,
            new_role=new_role,
            activation_source=activation_source,
            action=action,
            business_domain=business_domain,
        )

    def _fallback_decision(
        self,
        *,
        previous_role: str | None,
        new_role: str | None,
        activation_source: str,
        action: str,
        business_domain: str | None,
    ) -> TransitionPolicyDecision:
        if new_role is None:
            return TransitionPolicyDecision(
                decision="block",
                rule_id="DEFAULT_UNRESOLVED_TARGET",
                reason="Role transition failed closed because the target role was unresolved.",
            )

        if previous_role is None:
            return TransitionPolicyDecision(
                decision=self.defaults.get("initial_activation", "allow"),
                rule_id="DEFAULT_INITIAL_ACTIVATION",
                reason=f"Initial activation allowed for role {new_role}.",
            )

        if previous_role == new_role:
            return TransitionPolicyDecision(
                decision=self.defaults.get("same_role", "allow"),
                rule_id="DEFAULT_SAME_ROLE",
                reason=f"Role remained on {new_role}.",
            )

        previous_entry = self.hierarchy_registry.get(previous_role)
        new_entry = self.hierarchy_registry.get(new_role)
        if previous_entry is None or new_entry is None:
            return TransitionPolicyDecision(
                decision=self.defaults.get("unregistered_transition", "block"),
                rule_id="DEFAULT_UNREGISTERED_TRANSITION",
                reason="Role transition failed closed because one side of the transition is not in the trusted hierarchy.",
            )

        if new_role in self._children_of(previous_role):
            return TransitionPolicyDecision(
                decision="allow",
                rule_id="DEFAULT_DOWNWARD_DELEGATION",
                reason=f"Hierarchy allows {previous_role} to delegate work to child role {new_role}.",
            )

        if new_role in {previous_entry.reports_to, previous_entry.escalation_to}:
            return TransitionPolicyDecision(
                decision="review",
                rule_id="DEFAULT_UPWARD_ESCALATION_REVIEW",
                reason=f"Transition from {previous_role} to higher-governance role {new_role} requires human review.",
                escalated_to=new_role,
                notes=[f"activation_source={activation_source}", f"action={action}"],
            )

        if previous_entry.business_domain and new_entry.business_domain and previous_entry.business_domain.lower() == new_entry.business_domain.lower():
            return TransitionPolicyDecision(
                decision="allow",
                rule_id="DEFAULT_SAME_DOMAIN_PEER",
                reason=f"Transition remained inside business domain {previous_entry.business_domain}.",
            )

        if abs(previous_entry.stratum - new_entry.stratum) <= 1:
            return TransitionPolicyDecision(
                decision="review",
                rule_id="DEFAULT_ADJACENT_STRATUM_REVIEW",
                reason=f"Adjacent-stratum transition from {previous_role} to {new_role} requires oversight before execution.",
                escalated_to=(
                    new_entry.escalation_to
                    or previous_entry.escalation_to
                    or previous_entry.reports_to
                    or new_entry.executive_owner_id
                    or previous_entry.executive_owner_id
                    or self.hierarchy_registry.default_executive_owner_id
                ),
                notes=[f"business_domain={business_domain or '-'}"],
            )

        return TransitionPolicyDecision(
            decision=self.defaults.get("fallback_cross_domain", "block"),
            rule_id="DEFAULT_CROSS_DOMAIN_BLOCK",
            reason=f"Cross-domain transition from {previous_role} to {new_role} is blocked until an explicit matrix rule exists.",
        )

    def _children_of(self, role_id: str) -> set[str]:
        children: set[str] = set()
        for entry in self.hierarchy_registry.list_entries():
            if entry.reports_to == role_id:
                children.add(entry.role_id)
        return children

    def _resolve_escalation_target(self, token: str | None, previous_role: str | None, new_role: str | None) -> str | None:
        if token is None:
            return None
        normalized = token.strip().upper()
        if normalized == "SAFETY_OWNER" and new_role is not None:
            target = self.hierarchy_registry.get(new_role)
            return (
                target.safety_owner
                if target is not None and target.safety_owner is not None
                else self.hierarchy_registry.default_executive_owner_id
            )
        if normalized == "TARGET_ROLE":
            return new_role
        if normalized == "PREVIOUS_ROLE":
            return previous_role
        if normalized == "DEFAULT" and new_role is not None:
            return self.hierarchy_registry.default_escalation_target(new_role)
        return normalized

    def _load_payload(self) -> dict[str, object]:
        if not self.matrix_path.exists():
            return {"defaults": {}, "rules": []}
        return json.loads(self.matrix_path.read_text(encoding="utf-8-sig"))
