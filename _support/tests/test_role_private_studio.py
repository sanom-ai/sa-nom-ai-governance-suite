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