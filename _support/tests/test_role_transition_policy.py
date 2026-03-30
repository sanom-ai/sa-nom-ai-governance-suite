from sa_nom_governance.core.role_transition_policy import RoleTransitionPolicyMatrix
from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.utils.registry import RoleRegistry
from sa_nom_governance.ptag.role_loader import RoleLoader
from sa_nom_governance.core.hierarchy_registry import HierarchyRegistry


def build_policy():
    config = AppConfig(persist_runtime=False)
    registry = RoleRegistry(config.roles_dir, manifest_path=config.trusted_registry_manifest_path, cache_path=config.trusted_registry_cache_path, signing_key=config.trusted_registry_signing_key, signature_required=config.trusted_registry_signature_required)
    loader = RoleLoader(registry)
    hierarchy = HierarchyRegistry(loader)
    return RoleTransitionPolicyMatrix(hierarchy)


def test_transition_policy_allows_gov_to_legal_delegation() -> None:
    policy = build_policy()
    decision = policy.evaluate(previous_role='GOV', new_role='LEGAL', activation_source='context_router', action='review_contract', business_domain='legal_operations', resource='contract')
    assert decision.decision == 'allow'
    assert decision.rule_id == 'GOV_TO_LEGAL_DELEGATION'


def test_transition_policy_reviews_legal_to_gov() -> None:
    policy = build_policy()
    decision = policy.evaluate(previous_role='LEGAL', new_role='GOV', activation_source='context_router', action='review_audit', business_domain='governance', resource='audit')
    assert decision.decision == 'review'
    assert decision.escalated_to == 'GOV'
