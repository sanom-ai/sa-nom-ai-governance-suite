import json
from pathlib import Path


EXAMPLES_DIR = Path(__file__).resolve().parents[2] / 'examples'
JSON_EXAMPLES = [
    'owner_registration.example.json',
    'access_profiles.example.json',
    'generated_access_tokens.example.json',
    'trusted_registry_manifest.example.json',
    'guided_smoke_test.example.json',
    'runtime_startup_smoke.example.json',
    'provider_demo_flow.ollama.example.json',
    'legal_review_role_pack.example.json',
    'legal_review_scenario.example.json',
    'hr_policy_role_pack.example.json',
    'hr_policy_scenario.example.json',
    'purchasing_supplier_risk_role_pack.example.json',
    'purchasing_supplier_risk_scenario.example.json',
    'finance_budget_variance_role_pack.example.json',
    'finance_budget_variance_scenario.example.json',
    'accounting_close_exception_role_pack.example.json',
    'banking_treasury_control_role_pack.example.json',
    'new_model_launch_readiness_role_pack.example.json',
    'new_model_launch_readiness_scenario.example.json',
    'warehouse_material_shortage_role_pack.example.json',
]


def _load(name: str):
    return json.loads((EXAMPLES_DIR / name).read_text(encoding='utf-8'))


def test_json_examples_are_valid() -> None:
    for name in JSON_EXAMPLES:
        _load(name)


def test_guided_smoke_example_is_public_safe_and_ollama_first() -> None:
    payload = _load('guided_smoke_test.example.json')

    assert payload['provider']['recommended_provider'] == 'ollama'
    assert payload['provider']['selected_provider'] == 'ollama'
    assert payload['passed'] is True
    encoded = json.dumps(payload)
    assert 'TAWAN' not in encoded
    assert 'D:\\' not in encoded


def test_access_profile_example_matches_current_enterprise_profile_ids() -> None:
    payload = _load('access_profiles.example.json')

    profile_ids = [item['profile_id'] for item in payload]
    assert profile_ids == [
        'enterprise-operator',
        'enterprise-reviewer',
        'enterprise-auditor',
        'enterprise-viewer',
    ]


def test_legal_review_scenario_example_matches_role_pack_story() -> None:
    payload = _load('legal_review_scenario.example.json')

    assert payload['selected_provider'] == 'ollama'
    assert payload['default_private_demo_lane'] == 'ollama'
    assert payload['role_pack']['template_id'] == 'legal_review_escalation_pack'
    assert payload['review_result']['escalation_required'] is True
    assert 'approve_contract_exception' in payload['review_result']['wait_human_actions']
    assert 'sign_contract' in payload['review_result']['forbidden_actions_enforced']
    encoded = json.dumps(payload)
    assert 'TAWAN' not in encoded
    assert 'D:\\' not in encoded


def test_hr_policy_role_pack_example_preserves_human_hr_boundary() -> None:
    payload = _load('hr_policy_role_pack.example.json')

    assert payload['template_id'] == 'hr_policy_escalation_pack'
    assert payload['reporting_line'] == 'HR'
    assert 'approve_hr_policy_exception' in payload['wait_human_actions']
    assert 'approve_compensation_exception' in payload['wait_human_actions']
    assert 'terminate_employee' in payload['forbidden_actions']
    encoded = json.dumps(payload)
    assert 'TAWAN' not in encoded
    assert 'D:\\' not in encoded


def test_hr_policy_scenario_example_matches_role_pack_story() -> None:
    payload = _load('hr_policy_scenario.example.json')

    assert payload['selected_provider'] == 'ollama'
    assert payload['default_private_demo_lane'] == 'ollama'
    assert payload['role_pack']['template_id'] == 'hr_policy_escalation_pack'
    assert payload['review_result']['escalation_required'] is True
    assert 'approve_hr_policy_exception' in payload['review_result']['wait_human_actions']
    assert 'terminate_employee' in payload['review_result']['forbidden_actions_enforced']
    encoded = json.dumps(payload)
    assert 'TAWAN' not in encoded
    assert 'D:\\' not in encoded


def test_purchasing_supplier_risk_role_pack_example_preserves_human_procurement_boundary() -> None:
    payload = _load('purchasing_supplier_risk_role_pack.example.json')

    assert payload['template_id'] == 'purchasing_supplier_risk_pack'
    assert payload['reporting_line'] == 'PROCUREMENT'
    assert 'approve_procurement_exception' in payload['wait_human_actions']
    assert 'approve_supplier_override' in payload['wait_human_actions']
    assert 'appoint_supplier' in payload['forbidden_actions']
    encoded = json.dumps(payload)
    assert 'TAWAN' not in encoded
    assert 'D:\\' not in encoded


def test_purchasing_supplier_risk_scenario_example_matches_role_pack_story() -> None:
    payload = _load('purchasing_supplier_risk_scenario.example.json')

    assert payload['selected_provider'] == 'ollama'
    assert payload['default_private_demo_lane'] == 'ollama'
    assert payload['role_pack']['template_id'] == 'purchasing_supplier_risk_pack'
    assert payload['review_result']['escalation_required'] is True
    assert 'approve_procurement_exception' in payload['review_result']['wait_human_actions']
    assert 'appoint_supplier' in payload['review_result']['forbidden_actions_enforced']
    encoded = json.dumps(payload)
    assert 'TAWAN' not in encoded
    assert 'D:\\' not in encoded


def test_finance_budget_variance_role_pack_example_preserves_human_finance_boundary() -> None:
    payload = _load('finance_budget_variance_role_pack.example.json')

    assert payload['template_id'] == 'finance_budget_variance_pack'
    assert payload['reporting_line'] == 'FINANCE'
    assert 'approve_budget_exception' in payload['wait_human_actions']
    assert 'approve_capex_commitment' in payload['wait_human_actions']
    assert 'release_funds' in payload['forbidden_actions']
    encoded = json.dumps(payload)
    assert 'TAWAN' not in encoded
    assert 'D:\\' not in encoded


def test_finance_budget_variance_scenario_example_matches_role_pack_story() -> None:
    payload = _load('finance_budget_variance_scenario.example.json')

    assert payload['selected_provider'] == 'ollama'
    assert payload['default_private_demo_lane'] == 'ollama'
    assert payload['role_pack']['template_id'] == 'finance_budget_variance_pack'
    assert payload['review_result']['escalation_required'] is True
    assert 'approve_budget_exception' in payload['review_result']['wait_human_actions']
    assert 'release_funds' in payload['review_result']['forbidden_actions_enforced']
    encoded = json.dumps(payload)
    assert 'TAWAN' not in encoded
    assert 'D:\\' not in encoded


def test_accounting_close_exception_role_pack_example_preserves_human_accounting_boundary() -> None:
    payload = _load('accounting_close_exception_role_pack.example.json')

    assert payload['template_id'] == 'accounting_close_exception_pack'
    assert payload['reporting_line'] == 'ACCOUNTING'
    assert 'approve_close_exception' in payload['wait_human_actions']
    assert 'approve_manual_adjustment' in payload['wait_human_actions']
    assert 'post_manual_journal' in payload['forbidden_actions']
    encoded = json.dumps(payload)
    assert 'TAWAN' not in encoded
    assert 'D:\\' not in encoded


def test_banking_treasury_control_role_pack_example_preserves_human_treasury_boundary() -> None:
    payload = _load('banking_treasury_control_role_pack.example.json')

    assert payload['template_id'] == 'banking_treasury_control_pack'
    assert payload['reporting_line'] == 'TREASURY'
    assert 'approve_payment_exception' in payload['wait_human_actions']
    assert 'approve_bank_file_release' in payload['wait_human_actions']
    assert 'release_payment' in payload['forbidden_actions']
    encoded = json.dumps(payload)
    assert 'TAWAN' not in encoded
    assert 'D:\\' not in encoded

def test_new_model_launch_readiness_role_pack_example_preserves_human_npi_boundary() -> None:
    payload = _load('new_model_launch_readiness_role_pack.example.json')

    assert payload['template_id'] == 'new_model_launch_readiness_pack'
    assert payload['reporting_line'] == 'NPI'
    assert 'approve_launch_exception' in payload['wait_human_actions']
    assert 'approve_process_change' in payload['wait_human_actions']
    assert 'release_new_model_launch' in payload['forbidden_actions']
    encoded = json.dumps(payload)
    assert 'TAWAN' not in encoded
    assert 'D:\\' not in encoded

def test_new_model_launch_readiness_scenario_example_matches_role_pack_story() -> None:
    payload = _load('new_model_launch_readiness_scenario.example.json')

    assert payload['selected_provider'] == 'ollama'
    assert payload['default_private_demo_lane'] == 'ollama'
    assert payload['role_pack']['template_id'] == 'new_model_launch_readiness_pack'
    assert payload['review_result']['escalation_required'] is True
    assert 'approve_launch_exception' in payload['review_result']['wait_human_actions']
    assert 'release_new_model_launch' in payload['review_result']['forbidden_actions_enforced']
    encoded = json.dumps(payload)
    assert 'TAWAN' not in encoded
    assert 'D:\\' not in encoded

def test_warehouse_material_shortage_role_pack_example_preserves_human_warehouse_boundary() -> None:
    payload = _load('warehouse_material_shortage_role_pack.example.json')

    assert payload['template_id'] == 'warehouse_material_shortage_pack'
    assert payload['reporting_line'] == 'WAREHOUSE'
    assert 'approve_allocation_exception' in payload['wait_human_actions']
    assert 'approve_inventory_override' in payload['wait_human_actions']
    assert 'issue_material_to_line' in payload['forbidden_actions']
    encoded = json.dumps(payload)
    assert 'TAWAN' not in encoded
    assert 'D:\\' not in encoded