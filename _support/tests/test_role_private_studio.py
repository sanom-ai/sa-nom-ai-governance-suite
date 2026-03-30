import shutil
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from config import AppConfig
from owner_registration import OwnerRegistration, utc_now, write_owner_registration
from registry import RoleRegistry
from role_private_studio_service import RolePrivateStudioService


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
    source_base = Path(__file__).resolve().parent
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
    (temp_path / "role_private_studio_templates.json").write_text(
        (source_base / "role_private_studio_templates.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (temp_path / "role_private_studio_examples.json").write_text(
        (source_base / "role_private_studio_examples.json").read_text(encoding="utf-8"),
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
        assert (temp_path / "CONTRACT_REVIEW_ANALYST.ptn").exists()


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
