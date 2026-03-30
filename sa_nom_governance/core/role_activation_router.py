from dataclasses import dataclass, field

from sa_nom_governance.core.hierarchy_registry import HierarchyRegistry
from sa_nom_governance.core.role_transition_policy import RoleTransitionPolicyMatrix


AUTO_ROLE_TOKENS = {"", "AUTO", "auto", "AUTO_ROLE", "context"}


@dataclass(slots=True)
class RoleTransitionModel:
    requested_role: str | None
    previous_role: str | None
    new_role: str | None
    switch_reason: str
    activation_source: str
    candidate_roles: list[str] = field(default_factory=list)
    business_domain: str | None = None
    resource: str | None = None
    escalated_to: str | None = None
    transition_rule_id: str | None = None
    transition_disposition: str = "allow"
    transition_policy_reason: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "requested_role": self.requested_role,
            "previous_role": self.previous_role,
            "new_role": self.new_role,
            "switch_reason": self.switch_reason,
            "activation_source": self.activation_source,
            "candidate_roles": list(self.candidate_roles),
            "business_domain": self.business_domain,
            "resource": self.resource,
            "escalated_to": self.escalated_to,
            "transition_rule_id": self.transition_rule_id,
            "transition_disposition": self.transition_disposition,
            "transition_policy_reason": self.transition_policy_reason,
        }


@dataclass(slots=True)
class RoleActivationResolution:
    active_role: str
    transition: RoleTransitionModel


class RoleActivationError(ValueError):
    def __init__(self, code: str, reason: str, transition: RoleTransitionModel) -> None:
        super().__init__(reason)
        self.code = code
        self.reason = reason
        self.transition = transition


class RoleActivationRouter:
    def __init__(self, hierarchy_registry: HierarchyRegistry) -> None:
        self.hierarchy_registry = hierarchy_registry
        self.transition_policy = RoleTransitionPolicyMatrix(hierarchy_registry)

    def resolve(
        self,
        *,
        requester: str,
        requested_role: str | None,
        action: str,
        payload: dict[str, object],
        metadata: dict[str, object] | None = None,
    ) -> RoleActivationResolution:
        metadata = dict(metadata or {})
        previous_role = self._normalize_role(metadata.get("current_role") or metadata.get("active_role") or metadata.get("previous_role"))
        requested_role = self._normalize_role(requested_role)
        business_domain = self._normalize_token(payload.get("business_domain") or metadata.get("business_domain") or metadata.get("domain"))
        resource = self._normalize_token(payload.get("resource") or payload.get("resource_type"))

        if requested_role is not None and requested_role not in AUTO_ROLE_TOKENS:
            entry = self.hierarchy_registry.get(requested_role.upper())
            if entry is None:
                transition = RoleTransitionModel(
                    requested_role=requested_role.upper(),
                    previous_role=previous_role,
                    new_role="UNRESOLVED",
                    switch_reason=f"Requested role {requested_role.upper()} is not registered in the trusted hierarchy.",
                    activation_source="manual_unresolved",
                    business_domain=business_domain,
                    resource=resource,
                )
                raise RoleActivationError("unknown_role", transition.switch_reason, transition)
            transition = RoleTransitionModel(
                requested_role=requested_role.upper(),
                previous_role=previous_role,
                new_role=entry.role_id,
                switch_reason=f"Explicit role request selected {entry.role_id} for action {action}.",
                activation_source="manual",
                business_domain=business_domain,
                resource=resource,
            )
            self._apply_transition_policy(transition, action=action)
            return RoleActivationResolution(active_role=entry.role_id, transition=transition)

        candidates = self._candidate_entries(action=action)
        candidate_ids = [entry.role_id for entry in candidates]
        if not candidates:
            transition = RoleTransitionModel(
                requested_role=None,
                previous_role=previous_role,
                new_role="UNRESOLVED",
                switch_reason=f"No eligible role found for action {action}.",
                activation_source="context_router_unresolved",
                candidate_roles=[],
                business_domain=business_domain,
                resource=resource,
            )
            raise RoleActivationError("no_candidate_role", transition.switch_reason, transition)

        scored = sorted(
            ((self._score_entry(entry, payload=payload, business_domain=business_domain, previous_role=previous_role), entry) for entry in candidates),
            key=lambda item: (item[0], item[1].stratum, item[1].role_id),
            reverse=True,
        )
        top_score = scored[0][0]
        top_entries = [entry for score, entry in scored if score == top_score]

        if len(top_entries) > 1:
            top_entries = self._disambiguate(top_entries, previous_role=previous_role)

        if len(top_entries) != 1:
            transition = RoleTransitionModel(
                requested_role=None,
                previous_role=previous_role,
                new_role="UNRESOLVED",
                switch_reason=f"Context router found ambiguous role candidates for action {action}: {', '.join(entry.role_id for entry in top_entries)}.",
                activation_source="context_router_ambiguous",
                candidate_roles=candidate_ids,
                business_domain=business_domain,
                resource=resource,
            )
            raise RoleActivationError("ambiguous_role_candidates", transition.switch_reason, transition)

        selected = top_entries[0]
        transition = RoleTransitionModel(
            requested_role=None,
            previous_role=previous_role,
            new_role=selected.role_id,
            switch_reason=f"Context router selected {selected.role_id} for action {action} using action, resource, and business-domain signals.",
            activation_source="context_router",
            candidate_roles=candidate_ids,
            business_domain=business_domain,
            resource=resource,
        )
        self._apply_transition_policy(transition, action=action)
        return RoleActivationResolution(active_role=selected.role_id, transition=transition)

    def _candidate_entries(self, *, action: str):
        candidates = []
        for entry in self.hierarchy_registry.list_entries():
            if action in entry.denied_actions:
                continue
            if action not in entry.allowed_actions and action not in entry.required_human_actions:
                continue
            candidates.append(entry)
        return candidates

    def _score_entry(
        self,
        entry,
        *,
        payload: dict[str, object],
        business_domain: str | None,
        previous_role: str | None,
    ) -> int:
        score = 100
        resource = self._normalize_token(payload.get("resource") or payload.get("resource_type"))
        if resource is not None and resource.lower() in entry.handled_resources:
            score += 25
        if business_domain is not None and entry.business_domain is not None and entry.business_domain.lower() == business_domain.lower():
            score += 20
        if previous_role is not None and entry.role_id == previous_role:
            score += 5
        if entry.required_human_actions:
            score += 1
        return score

    def _disambiguate(self, entries, previous_role: str | None):
        if previous_role is not None:
            matching_previous = [entry for entry in entries if entry.role_id == previous_role]
            if len(matching_previous) == 1:
                return matching_previous
        highest_stratum = max(entry.stratum for entry in entries)
        return [entry for entry in entries if entry.stratum == highest_stratum]

    def _apply_transition_policy(self, transition: RoleTransitionModel, *, action: str) -> None:
        decision = self.transition_policy.evaluate(
            previous_role=transition.previous_role,
            new_role=transition.new_role,
            activation_source=transition.activation_source,
            action=action,
            business_domain=transition.business_domain,
            resource=transition.resource,
        )
        transition.transition_rule_id = decision.rule_id
        transition.transition_disposition = decision.decision
        transition.transition_policy_reason = decision.reason
        if decision.escalated_to and not transition.escalated_to:
            transition.escalated_to = decision.escalated_to
        if decision.decision == "block":
            transition.switch_reason = decision.reason
            raise RoleActivationError("transition_blocked", decision.reason, transition)
        if decision.decision == "review":
            transition.switch_reason = decision.reason

    def _normalize_role(self, value: object | None) -> str | None:
        token = self._normalize_token(value)
        return token.upper() if token is not None else None

    def _normalize_token(self, value: object | None) -> str | None:
        if value is None:
            return None
        token = str(value).strip()
        return token or None
