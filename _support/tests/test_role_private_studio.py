import shutil
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.utils.owner_registration import OwnerRegistration, utc_now, write_owner_registration
from sa_nom_governance.utils.registry import RoleRegistry
from sa_nom_governance.studio.role_private_studio_service import RolePrivateStudioService


BASE_PAYLOAD = {
    "role_name": "Contract Review Analyst",
    "purpose": "Review contract packets and route risky documents for human attention.",
    "reporting_line": "LEGAL",
    "business_domain": "legal_operations",
    "operating_mode": "indirect",
    "assigned_user_id": "LEGAL_MANAGER_01",
    "executive_owner_id": "AREE",
    "seat_id": "OPS-LEGAL",
    "responsibilities": ["review incoming contracts", "flag risk"],
    "allowed_actions": ["review_contract", "flag_risk", "advise_compliance"],
    "forbidden_actions": ["sign_contract"],
    "wait_human_actions": [],
    "handled_resources": ["contract"],
    "financial_sensitivity": "medium",
    "legal_sensitivity": "high",
    "compliance_sensitivity": "high",
}


@contextmanager
def workspace_temp_dir():
    source_base = Path(__file__).resolve().parents[2]
    runtime_tmp = source_base / "_runtime" / "tmp_test"
    runtime_tmp.mkdir(parents=True, exist_ok=True)
    temp_path = runtime_tmp / f"studio_{uuid4().hex[:8]}"
    temp_path.mkdir(parents=True, exist_ok=True)
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


def build_service(temp_path: Path) -> RolePrivateStudioService:
    source_base = Path(__file__).resolve().parents[2]
    config = AppConfig(
        base_dir=temp_path,
        environment="development",
        api_token="owner-token",
        trusted_registry_signing_key="registry-key",
    )
    assert config.owner_registration_path is not None
    write_owner_registration(
        config.owner_registration_path,
        OwnerRegistration(
            registration_code="EXAMPLE-ORG",
            deployment_mode="private",
            organization_name="Example Org",
            organization_id="EXAMPLE_ORG",
            owner_name="Aree",
            owner_display_name="Aree Executive Owner",
            executive_owner_id="AREE",
            trusted_registry_signed_by="Aree",
            registered_at=utc_now(),
        ),
        force=True,
    )
    manifest_path = config.trusted_registry_manifest_path
    cache_path = config.trusted_registry_cache_path
    manifest_path.write_text(
        '{"roles": {}, "signature": {"algorithm": "hmac_sha256", "key_id": "TEST", "signed_at": "2026-01-01T00:00:00+00:00", "value": "placeholder"}}',
        encoding="utf-8",
    )
    cache_path.write_text('{"entries": {}}', encoding="utf-8")
    registry = RoleRegistry(
        config.roles_dir,
        manifest_path=manifest_path,
        cache_path=cache_path,
        signing_key=config.trusted_registry_signing_key,
        signature_required=False,
    )
    studio_dir = temp_path / "resources" / "studio"
    studio_dir.mkdir(parents=True, exist_ok=True)
    (studio_dir / "role_private_studio_templates.json").write_text(
        (source_base / "resources" / "studio" / "role_private_studio_templates.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (studio_dir / "role_private_studio_examples.json").write_text(
        (source_base / "resources" / "studio" / "role_private_studio_examples.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return RolePrivateStudioService(config=config, registry=registry)


def test_role_private_studio_create_review_publish_flow():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        created = service.create_request(BASE_PAYLOAD, requested_by="EXEC_OWNER")
        assert created["status"] in {"in_review", "approved", "simulation_failed"}
        assert created["summary"]["current_revision"] == 1
        reviewed = service.review_request(created["request_id"], reviewer="EXEC_OWNER", decision="approve", note="Approved for publish.")
        assert reviewed["status"] == "approved"
        assert reviewed["publish_readiness"]["gates"]["review"] is True
        published = service.publish_request(created["request_id"], published_by="EXEC_OWNER")
        assert published["status"] == "published"
        assert (temp_path / "resources" / "roles" / "CONTRACT_REVIEW_ANALYST.ptn").exists()


def test_role_private_studio_update_creates_new_revision_and_resets_publish_readiness():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        created = service.create_request(BASE_PAYLOAD, requested_by="EXEC_OWNER")
        reviewed = service.review_request(created["request_id"], reviewer="EXEC_OWNER", decision="approve", note="Approved on revision one.")
        assert reviewed["publish_readiness"]["status"] == "ready"

        updated = service.update_request(
            created["request_id"],
            {
                "purpose": "Review contract packets, summarize control exposure, and route risky documents for human attention.",
                "responsibilities": ["review incoming contracts", "flag risk", "summarize control exposure"],
            },
            updated_by="EXEC_OWNER",
        )
        assert updated["status"] == "in_review"
        assert updated["summary"]["current_revision"] == 2
        assert updated["summary"]["approved_for_current_revision"] is False
        assert updated["publish_readiness"]["status"] == "blocked"
        assert "The current revision has not been approved yet." in updated["publish_readiness"]["blockers"]
        latest_revision = updated["revisions"][-1]
        assert latest_revision["diff_summary"]["ptag"]["changed"] is True
        assert any("Purpose" in item or "Responsibilities" in item for item in latest_revision["change_summary"])

        rereviewed = service.review_request(created["request_id"], reviewer="EXEC_OWNER", decision="approve", note="Approved on revision two.")
        assert rereviewed["publish_readiness"]["status"] == "ready"
        assert rereviewed["review_history"][-1]["revision_number"] == 2


def test_role_private_studio_ptag_live_editor_switches_to_manual_mode():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        created = service.create_request(BASE_PAYLOAD, requested_by="EXEC_OWNER")
        original_ptag = created["generated_ptag"]
        manual_ptag = original_ptag.replace(
            'context "SA-NOM Role Private Studio"',
            'context "SA-NOM Role Private Studio Manual"',
        )

        updated = service.update_request_ptag(created["request_id"], manual_ptag, updated_by="EXEC_OWNER")
        assert updated["ptag_source_mode"] == "manual"
        assert updated["summary"]["ptag_override_present"] is True
        assert updated["generated_ptag"] == manual_ptag
        assert updated["revisions"][-1]["ptag_source_mode"] == "manual"

        reset = service.reset_request_ptag(created["request_id"], updated_by="EXEC_OWNER")
        assert reset["ptag_source_mode"] == "generated"
        assert reset["summary"]["ptag_override_present"] is False
        assert reset["generated_ptag"] != manual_ptag


def test_role_private_studio_publication_workflow_summary_tracks_review_and_publish():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        created = service.create_request(BASE_PAYLOAD, requested_by="EXEC_OWNER")
        workflow = created["publication_workflow"]
        assert workflow["stages"][0]["id"] == "authoring"
        assert workflow["stages"][3]["id"] == "structural"
        assert workflow["stages"][4]["id"] == "review"

        approved = service.review_request(created["request_id"], reviewer="EXEC_OWNER", decision="approve", note="Approved for registry promotion.")
        assert approved["publication_workflow"]["status"] == "publisher_ready"
        assert approved["publication_workflow"]["latest_review_decision"] == "approve"

        published = service.publish_request(created["request_id"], published_by="EXEC_OWNER")
        assert published["publication_workflow"]["status"] == "published"
        assert published["publication_workflow"]["published_by"] == "EXEC_OWNER"


def test_role_private_studio_generates_assignment_fields_for_indirect_hat():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        created = service.create_request(BASE_PAYLOAD, requested_by="EXEC_OWNER")

        assert created["structured_jd"]["operating_mode"] == "indirect"
        assert created["normalized_spec"]["operating_mode"] == "indirect"
        assert created["normalized_spec"]["assigned_user_id"] == "LEGAL_MANAGER_01"
        assert created["normalized_spec"]["executive_owner_id"] == "AREE"
        assert created["normalized_spec"]["seat_id"] == "OPS-LEGAL"
        assert 'owner "Aree"' in created["generated_ptag"]
        assert "operating_mode: indirect" in created["generated_ptag"]
        assert "assigned_user_id: LEGAL_MANAGER_01" in created["generated_ptag"]
        assert "safety_owner: LEGAL" in created["generated_ptag"]
        assert 'seat_id: "OPS-LEGAL"' in created["generated_ptag"]


def test_role_private_studio_blocks_indirect_hat_without_assigned_user():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        payload = dict(BASE_PAYLOAD)
        payload["assigned_user_id"] = ""

        created = service.create_request(payload, requested_by="EXEC_OWNER")

        findings = created["validation_report"]["findings"]
        assert any(item["code"] == "INDIRECT_REQUIRES_ASSIGNED_USER" for item in findings)
        assert created["publish_readiness"]["status"] == "blocked"


def test_role_private_studio_template_library_includes_legal_review_escalation_pack():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        template = service.load_template()
        library = template["library"]
        legal_pack = next(item for item in library if item["template_id"] == "legal_review_escalation_pack")

        assert legal_pack["category"] == "legal"
        assert legal_pack["payload"]["role_name"] == "Legal Review Escalation Counsel"
        assert "approve_contract_exception" in legal_pack["payload"]["allowed_actions"]
        assert "approve_contract_exception" in legal_pack["payload"]["wait_human_actions"]
        assert "sign_contract" in legal_pack["payload"]["forbidden_actions"]
        assert "waive_regulatory_obligation" in legal_pack["payload"]["forbidden_actions"]


def test_role_private_studio_examples_include_vendor_contract_risk_counsel():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        examples = service.load_examples()
        legal_example = next(item for item in examples if item["name"] == "Vendor Contract Risk Counsel")

        assert legal_example["operating_mode"] == "indirect"
        assert legal_example["reporting_line"] == "LEGAL"
        assert "approve_contract_exception" in legal_example["wait_human_actions"]
        assert "vendor_packet" in legal_example["handled_resources"]
        assert "policy exception routing" in legal_example["sample_scenarios"]


def test_role_private_studio_legal_review_pack_preserves_human_approval_boundary():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        template = service.load_template()
        payload = next(item["payload"] for item in template["library"] if item["template_id"] == "legal_review_escalation_pack")
        created = service.create_request(payload, requested_by="EXEC_OWNER")

        assert created["normalized_spec"]["role_id"] == "LEGAL_REVIEW_ESCALATION_COUNSEL"
        assert "approve_contract_exception" in created["normalized_spec"]["wait_human_actions"]
        assert "sign_contract" in created["generated_ptag"]
        assert "require human_override for approve_contract_exception" in created["generated_ptag"]
        assert created["publish_readiness"]["gates"]["validation"] is True



def test_role_private_studio_template_library_includes_hr_policy_escalation_pack():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        template = service.load_template()
        library = template["library"]
        hr_pack = next(item for item in library if item["template_id"] == "hr_policy_escalation_pack")

        assert hr_pack["category"] == "hr"
        assert hr_pack["payload"]["role_name"] == "HR Policy Escalation Lead"
        assert "approve_hr_policy_exception" in hr_pack["payload"]["allowed_actions"]
        assert "approve_compensation_exception" in hr_pack["payload"]["wait_human_actions"]
        assert "terminate_employee" in hr_pack["payload"]["forbidden_actions"]
        assert "finalize_compensation_change" in hr_pack["payload"]["forbidden_actions"]


def test_role_private_studio_examples_include_hr_policy_escalation_lead():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        examples = service.load_examples()
        hr_example = next(item for item in examples if item["name"] == "HR Policy Escalation Lead")

        assert hr_example["operating_mode"] == "indirect"
        assert hr_example["reporting_line"] == "HR"
        assert "approve_hr_policy_exception" in hr_example["wait_human_actions"]
        assert "employee_case" in hr_example["handled_resources"]
        assert "policy accommodation routing" in hr_example["sample_scenarios"]


def test_role_private_studio_hr_policy_pack_preserves_human_hr_boundary():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        template = service.load_template()
        payload = next(item["payload"] for item in template["library"] if item["template_id"] == "hr_policy_escalation_pack")
        created = service.create_request(payload, requested_by="EXEC_OWNER")

        assert created["normalized_spec"]["role_id"] == "HR_POLICY_ESCALATION_LEAD"
        assert "approve_hr_policy_exception" in created["normalized_spec"]["wait_human_actions"]
        assert "approve_compensation_exception" in created["normalized_spec"]["wait_human_actions"]
        assert "terminate_employee" in created["generated_ptag"]
        assert "require human_override for approve_hr_policy_exception" in created["generated_ptag"]
        assert created["publish_readiness"]["gates"]["validation"] is True



def test_role_private_studio_template_library_includes_purchasing_supplier_risk_pack():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        template = service.load_template()
        library = template["library"]
        purchasing_pack = next(item for item in library if item["template_id"] == "purchasing_supplier_risk_pack")

        assert purchasing_pack["category"] == "procurement"
        assert purchasing_pack["payload"]["role_name"] == "Purchasing Supplier Risk Lead"
        assert "approve_procurement_exception" in purchasing_pack["payload"]["allowed_actions"]
        assert "approve_supplier_override" in purchasing_pack["payload"]["wait_human_actions"]
        assert "appoint_supplier" in purchasing_pack["payload"]["forbidden_actions"]
        assert "release_funds" in purchasing_pack["payload"]["forbidden_actions"]


def test_role_private_studio_examples_include_purchasing_supplier_risk_lead():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        examples = service.load_examples()
        purchasing_example = next(item for item in examples if item["name"] == "Purchasing Supplier Risk Lead")

        assert purchasing_example["operating_mode"] == "indirect"
        assert purchasing_example["reporting_line"] == "PROCUREMENT"
        assert "approve_procurement_exception" in purchasing_example["wait_human_actions"]
        assert "supplier_packet" in purchasing_example["handled_resources"]
        assert "lead-time disruption routing" in purchasing_example["sample_scenarios"]


def test_role_private_studio_purchasing_pack_preserves_human_procurement_boundary():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        template = service.load_template()
        payload = next(item["payload"] for item in template["library"] if item["template_id"] == "purchasing_supplier_risk_pack")
        created = service.create_request(payload, requested_by="EXEC_OWNER")

        assert created["normalized_spec"]["role_id"] == "PURCHASING_SUPPLIER_RISK_LEAD"
        assert "approve_procurement_exception" in created["normalized_spec"]["wait_human_actions"]
        assert "approve_supplier_override" in created["normalized_spec"]["wait_human_actions"]
        assert "appoint_supplier" in created["generated_ptag"]
        assert "require human_override for approve_procurement_exception" in created["generated_ptag"]
        assert created["publish_readiness"]["gates"]["validation"] is True



def test_role_private_studio_template_library_includes_finance_budget_variance_pack():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        template = service.load_template()
        library = template["library"]
        finance_pack = next(item for item in library if item["template_id"] == "finance_budget_variance_pack")

        assert finance_pack["category"] == "finance"
        assert finance_pack["payload"]["role_name"] == "Finance Budget Variance Lead"
        assert "approve_budget_exception" in finance_pack["payload"]["allowed_actions"]
        assert "approve_capex_commitment" in finance_pack["payload"]["wait_human_actions"]
        assert "release_funds" in finance_pack["payload"]["forbidden_actions"]
        assert "change_customer_pricing" in finance_pack["payload"]["forbidden_actions"]


def test_role_private_studio_examples_include_finance_budget_variance_lead():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        examples = service.load_examples()
        finance_example = next(item for item in examples if item["name"] == "Finance Budget Variance Lead")

        assert finance_example["operating_mode"] == "indirect"
        assert finance_example["reporting_line"] == "FINANCE"
        assert "approve_budget_exception" in finance_example["wait_human_actions"]
        assert "variance_packet" in finance_example["handled_resources"]
        assert "margin pressure escalation" in finance_example["sample_scenarios"]


def test_role_private_studio_finance_pack_preserves_human_finance_boundary():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        template = service.load_template()
        payload = next(item["payload"] for item in template["library"] if item["template_id"] == "finance_budget_variance_pack")
        created = service.create_request(payload, requested_by="EXEC_OWNER")

        assert created["normalized_spec"]["role_id"] == "FINANCE_BUDGET_VARIANCE_LEAD"
        assert "approve_budget_exception" in created["normalized_spec"]["wait_human_actions"]
        assert "approve_capex_commitment" in created["normalized_spec"]["wait_human_actions"]
        assert "release_funds" in created["generated_ptag"]
        assert "require human_override for approve_budget_exception" in created["generated_ptag"]
        assert created["publish_readiness"]["gates"]["validation"] is True


def test_role_private_studio_template_library_includes_accounting_close_exception_pack():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        template = service.load_template()
        library = template["library"]
        accounting_pack = next(item for item in library if item["template_id"] == "accounting_close_exception_pack")

        assert accounting_pack["category"] == "accounting"
        assert accounting_pack["payload"]["role_name"] == "Accounting Close Exception Lead"
        assert "approve_close_exception" in accounting_pack["payload"]["allowed_actions"]
        assert "approve_manual_adjustment" in accounting_pack["payload"]["wait_human_actions"]
        assert "post_manual_journal" in accounting_pack["payload"]["forbidden_actions"]
        assert "release_payment" in accounting_pack["payload"]["forbidden_actions"]


def test_role_private_studio_examples_include_accounting_close_exception_lead():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        examples = service.load_examples()
        accounting_example = next(item for item in examples if item["name"] == "Accounting Close Exception Lead")

        assert accounting_example["operating_mode"] == "indirect"
        assert accounting_example["reporting_line"] == "ACCOUNTING"
        assert "approve_close_exception" in accounting_example["wait_human_actions"]
        assert "close_packet" in accounting_example["handled_resources"]
        assert "GR/IR exception routing" in accounting_example["sample_scenarios"]


def test_role_private_studio_accounting_pack_preserves_human_accounting_boundary():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        template = service.load_template()
        payload = next(item["payload"] for item in template["library"] if item["template_id"] == "accounting_close_exception_pack")
        created = service.create_request(payload, requested_by="EXEC_OWNER")

        assert created["normalized_spec"]["role_id"] == "ACCOUNTING_CLOSE_EXCEPTION_LEAD"
        assert "approve_close_exception" in created["normalized_spec"]["wait_human_actions"]
        assert "approve_manual_adjustment" in created["normalized_spec"]["wait_human_actions"]
        assert "post_manual_journal" in created["generated_ptag"]
        assert "require human_override for approve_close_exception" in created["generated_ptag"]
        assert created["publish_readiness"]["gates"]["validation"] is True


def test_role_private_studio_template_library_includes_banking_treasury_control_pack():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        template = service.load_template()
        library = template["library"]
        treasury_pack = next(item for item in library if item["template_id"] == "banking_treasury_control_pack")

        assert treasury_pack["category"] == "treasury"
        assert treasury_pack["payload"]["role_name"] == "Treasury Payment Control Lead"
        assert "approve_payment_exception" in treasury_pack["payload"]["allowed_actions"]
        assert "approve_bank_file_release" in treasury_pack["payload"]["wait_human_actions"]
        assert "release_payment" in treasury_pack["payload"]["forbidden_actions"]
        assert "sign_bank_instruction" in treasury_pack["payload"]["forbidden_actions"]


def test_role_private_studio_examples_include_treasury_payment_control_lead():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        examples = service.load_examples()
        treasury_example = next(item for item in examples if item["name"] == "Treasury Payment Control Lead")

        assert treasury_example["operating_mode"] == "indirect"
        assert treasury_example["reporting_line"] == "TREASURY"
        assert "approve_payment_exception" in treasury_example["wait_human_actions"]
        assert "bank_file" in treasury_example["handled_resources"]
        assert "bank-file release routing" in treasury_example["sample_scenarios"]


def test_role_private_studio_banking_pack_preserves_human_treasury_boundary():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        template = service.load_template()
        payload = next(item["payload"] for item in template["library"] if item["template_id"] == "banking_treasury_control_pack")
        created = service.create_request(payload, requested_by="EXEC_OWNER")

        assert created["normalized_spec"]["role_id"] == "TREASURY_PAYMENT_CONTROL_LEAD"
        assert "approve_payment_exception" in created["normalized_spec"]["wait_human_actions"]
        assert "approve_bank_file_release" in created["normalized_spec"]["wait_human_actions"]
        assert "release_payment" in created["generated_ptag"]
        assert "require human_override for approve_payment_exception" in created["generated_ptag"]
        assert created["publish_readiness"]["gates"]["validation"] is True

def test_role_private_studio_template_library_includes_new_model_launch_readiness_pack():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        template = service.load_template()
        library = template["library"]
        npi_pack = next(item for item in library if item["template_id"] == "new_model_launch_readiness_pack")

        assert npi_pack["category"] == "manufacturing_npi"
        assert npi_pack["payload"]["role_name"] == "New Model Launch Readiness Lead"
        assert "approve_launch_exception" in npi_pack["payload"]["allowed_actions"]
        assert "approve_process_change" in npi_pack["payload"]["wait_human_actions"]
        assert "release_new_model_launch" in npi_pack["payload"]["forbidden_actions"]
        assert "waive_customer_requirement" in npi_pack["payload"]["forbidden_actions"]


def test_role_private_studio_examples_include_new_model_launch_readiness_lead():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        examples = service.load_examples()
        npi_example = next(item for item in examples if item["name"] == "New Model Launch Readiness Lead")

        assert npi_example["operating_mode"] == "indirect"
        assert npi_example["reporting_line"] == "NPI"
        assert "approve_launch_exception" in npi_example["wait_human_actions"]
        assert "control_plan" in npi_example["handled_resources"]
        assert "PPAP readiness escalation" in npi_example["sample_scenarios"]


def test_role_private_studio_new_model_launch_pack_preserves_human_npi_boundary():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        template = service.load_template()
        payload = next(item["payload"] for item in template["library"] if item["template_id"] == "new_model_launch_readiness_pack")
        created = service.create_request(payload, requested_by="EXEC_OWNER")

        assert created["normalized_spec"]["role_id"] == "NEW_MODEL_LAUNCH_READINESS_LEAD"
        assert "approve_launch_exception" in created["normalized_spec"]["wait_human_actions"]
        assert "approve_process_change" in created["normalized_spec"]["wait_human_actions"]
        assert "release_new_model_launch" in created["generated_ptag"]
        assert "require human_override for approve_launch_exception" in created["generated_ptag"]
        assert created["publish_readiness"]["gates"]["validation"] is True

def test_role_private_studio_template_library_includes_warehouse_material_shortage_pack():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        template = service.load_template()
        library = template["library"]
        warehouse_pack = next(item for item in library if item["template_id"] == "warehouse_material_shortage_pack")

        assert warehouse_pack["category"] == "warehouse"
        assert warehouse_pack["payload"]["role_name"] == "Warehouse Material Shortage Lead"
        assert "approve_allocation_exception" in warehouse_pack["payload"]["allowed_actions"]
        assert "approve_inventory_override" in warehouse_pack["payload"]["wait_human_actions"]
        assert "issue_material_to_line" in warehouse_pack["payload"]["forbidden_actions"]
        assert "adjust_inventory_balance" in warehouse_pack["payload"]["forbidden_actions"]


def test_role_private_studio_examples_include_warehouse_material_shortage_lead():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        examples = service.load_examples()
        warehouse_example = next(item for item in examples if item["name"] == "Warehouse Material Shortage Lead")

        assert warehouse_example["operating_mode"] == "indirect"
        assert warehouse_example["reporting_line"] == "WAREHOUSE"
        assert "approve_allocation_exception" in warehouse_example["wait_human_actions"]
        assert "inventory_snapshot" in warehouse_example["handled_resources"]
        assert "line-starvation escalation" in warehouse_example["sample_scenarios"]


def test_role_private_studio_warehouse_pack_preserves_human_warehouse_boundary():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        template = service.load_template()
        payload = next(item["payload"] for item in template["library"] if item["template_id"] == "warehouse_material_shortage_pack")
        created = service.create_request(payload, requested_by="EXEC_OWNER")

        assert created["normalized_spec"]["role_id"] == "WAREHOUSE_MATERIAL_SHORTAGE_LEAD"
        assert "approve_allocation_exception" in created["normalized_spec"]["wait_human_actions"]
        assert "approve_inventory_override" in created["normalized_spec"]["wait_human_actions"]
        assert "issue_material_to_line" in created["generated_ptag"]
        assert "require human_override for approve_allocation_exception" in created["generated_ptag"]
        assert created["publish_readiness"]["gates"]["validation"] is True

def test_role_private_studio_template_library_includes_production_line_exception_pack():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        template = service.load_template()
        library = template["library"]
        production_pack = next(item for item in library if item["template_id"] == "production_line_exception_pack")

        assert production_pack["category"] == "production"
        assert production_pack["payload"]["role_name"] == "Production Line Exception Lead"


def test_role_private_studio_examples_include_production_line_exception_lead():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        examples = service.load_examples()
        production_example = next(item for item in examples if item["name"] == "Production Line Exception Lead")

        assert production_example["operating_mode"] == "indirect"
        assert production_example["reporting_line"] == "PRODUCTION"


def test_role_private_studio_production_pack_preserves_human_production_boundary():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        template = service.load_template()
        payload = next(item["payload"] for item in template["library"] if item["template_id"] == "production_line_exception_pack")
        created = service.create_request(payload, requested_by="EXEC_OWNER")

        assert created["normalized_spec"]["role_id"] == "PRODUCTION_LINE_EXCEPTION_LEAD"
        assert "approve_recovery_exception" in created["normalized_spec"]["wait_human_actions"]
        assert "approve_schedule_override" in created["normalized_spec"]["wait_human_actions"]
        assert "release_production_schedule_change" in created["normalized_spec"]["forbidden_actions"]
        assert "override_quality_hold" in created["normalized_spec"]["forbidden_actions"]
        assert "require human_override for approve_recovery_exception" in created["generated_ptag"]


def test_role_private_studio_template_library_includes_quality_audit_readiness_pack():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        template = service.load_template()
        library = template["library"]
        quality_pack = next(item for item in library if item["template_id"] == "quality_audit_readiness_pack")

        assert quality_pack["category"] == "quality_audit"
        assert quality_pack["payload"]["role_name"] == "Quality Audit Readiness Lead"


def test_role_private_studio_examples_include_quality_audit_readiness_lead():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        examples = service.load_examples()
        quality_example = next(item for item in examples if item["name"] == "Quality Audit Readiness Lead")

        assert quality_example["operating_mode"] == "indirect"
        assert quality_example["reporting_line"] == "QUALITY"


def test_role_private_studio_quality_pack_preserves_human_quality_boundary():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        template = service.load_template()
        payload = next(item["payload"] for item in template["library"] if item["template_id"] == "quality_audit_readiness_pack")
        created = service.create_request(payload, requested_by="EXEC_OWNER")

        assert created["normalized_spec"]["role_id"] == "QUALITY_AUDIT_READINESS_LEAD"
        assert "approve_release_exception" in created["normalized_spec"]["wait_human_actions"]
        assert "approve_deviation_waiver" in created["normalized_spec"]["wait_human_actions"]
        assert "release_quality_hold" in created["normalized_spec"]["forbidden_actions"]
        assert "waive_specification_requirement" in created["normalized_spec"]["forbidden_actions"]
        assert "require human_override for approve_release_exception" in created["generated_ptag"]


def test_role_private_studio_template_library_includes_delivery_readiness_pack():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        template = service.load_template()
        library = template["library"]
        delivery_pack = next(item for item in library if item["template_id"] == "delivery_readiness_pack")

        assert delivery_pack["category"] == "delivery"
        assert delivery_pack["payload"]["role_name"] == "Delivery Readiness Lead"


def test_role_private_studio_examples_include_delivery_readiness_lead():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        examples = service.load_examples()
        delivery_example = next(item for item in examples if item["name"] == "Delivery Readiness Lead")

        assert delivery_example["operating_mode"] == "indirect"
        assert delivery_example["reporting_line"] == "DELIVERY"


def test_role_private_studio_delivery_pack_preserves_human_delivery_boundary():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        template = service.load_template()
        payload = next(item["payload"] for item in template["library"] if item["template_id"] == "delivery_readiness_pack")
        created = service.create_request(payload, requested_by="EXEC_OWNER")

        assert created["normalized_spec"]["role_id"] == "DELIVERY_READINESS_LEAD"
        assert "approve_dispatch_exception" in created["normalized_spec"]["wait_human_actions"]
        assert "approve_customer_commitment_change" in created["normalized_spec"]["wait_human_actions"]
        assert "release_shipment" in created["normalized_spec"]["forbidden_actions"]
        assert "change_customer_delivery_commitment" in created["normalized_spec"]["forbidden_actions"]
        assert "require human_override for approve_dispatch_exception" in created["generated_ptag"]


def test_role_private_studio_template_library_includes_external_audit_response_pack():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        template = service.load_template()
        library = template["library"]
        audit_pack = next(item for item in library if item["template_id"] == "external_audit_response_pack")

        assert audit_pack["category"] == "audit_external"
        assert audit_pack["payload"]["role_name"] == "External Audit Response Lead"


def test_role_private_studio_examples_include_external_audit_response_lead():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        examples = service.load_examples()
        audit_example = next(item for item in examples if item["name"] == "External Audit Response Lead")

        assert audit_example["operating_mode"] == "indirect"
        assert audit_example["reporting_line"] == "AUDIT"


def test_role_private_studio_external_audit_pack_preserves_human_audit_boundary():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        template = service.load_template()
        payload = next(item["payload"] for item in template["library"] if item["template_id"] == "external_audit_response_pack")
        created = service.create_request(payload, requested_by="EXEC_OWNER")

        assert created["normalized_spec"]["role_id"] == "EXTERNAL_AUDIT_RESPONSE_LEAD"
        assert "approve_audit_response_exception" in created["normalized_spec"]["wait_human_actions"]
        assert "approve_regulatory_response" in created["normalized_spec"]["wait_human_actions"]
        assert "close_audit_finding" in created["normalized_spec"]["forbidden_actions"]
        assert "alter_audit_evidence" in created["normalized_spec"]["forbidden_actions"]
        assert "require human_override for approve_audit_response_exception" in created["generated_ptag"]


def test_role_private_studio_template_library_includes_regulator_response_pack():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        template = service.load_template()
        library = template["library"]
        regulator_pack = next(item for item in library if item["template_id"] == "regulator_response_pack")

        assert regulator_pack["category"] == "regulator_response"
        assert regulator_pack["payload"]["role_name"] == "Regulator Response Coordination Lead"


def test_role_private_studio_examples_include_regulator_response_coordination_lead():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        examples = service.load_examples()
        regulator_example = next(item for item in examples if item["name"] == "Regulator Response Coordination Lead")

        assert regulator_example["operating_mode"] == "indirect"
        assert regulator_example["reporting_line"] == "COMPLIANCE"


def test_role_private_studio_regulator_pack_preserves_human_regulator_boundary():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        template = service.load_template()
        payload = next(item["payload"] for item in template["library"] if item["template_id"] == "regulator_response_pack")
        created = service.create_request(payload, requested_by="EXEC_OWNER")

        assert created["normalized_spec"]["role_id"] == "REGULATOR_RESPONSE_COORDINATION_LEAD"
        assert "approve_regulator_response_exception" in created["normalized_spec"]["wait_human_actions"]
        assert "approve_regulatory_filing" in created["normalized_spec"]["wait_human_actions"]
        assert "release_official_regulator_response" in created["normalized_spec"]["forbidden_actions"]
        assert "waive_regulatory_requirement" in created["normalized_spec"]["forbidden_actions"]
        assert "require human_override for approve_regulator_response_exception" in created["generated_ptag"]
