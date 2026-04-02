import shutil
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from sa_nom_governance.documents.document_service import GovernedDocumentService
from sa_nom_governance.utils.config import AppConfig


@contextmanager
def workspace_temp_dir():
    source_base = Path(__file__).resolve().parents[2]
    runtime_tmp = source_base / "_runtime" / "tmp_test"
    runtime_tmp.mkdir(parents=True, exist_ok=True)
    temp_path = runtime_tmp / f"documents_{uuid4().hex[:8]}"
    temp_path.mkdir(parents=True, exist_ok=True)
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


def build_service(temp_path: Path) -> GovernedDocumentService:
    config = AppConfig(
        base_dir=temp_path,
        environment="development",
        api_token="owner-token",
        trusted_registry_signing_key="registry-key",
    )
    return GovernedDocumentService(config=config)


def test_document_create_assigns_numbering_metadata_and_store_path():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        created = service.create_document(
            {
                "title": "Vendor Risk Policy",
                "document_class": "policy",
                "content": "Policy body",
                "case_id": "CASE-REQ-1001",
                "owner_id": "EXEC_OWNER",
                "approver_id": "LEGAL_OWNER",
                "retention_code": "RET-POL-7Y",
                "business_domain": "vendor_risk",
                "tags": ["vendor", "policy"],
                "metadata": {"region": "th"},
            },
            created_by="EXEC_OWNER",
        )

        assert created["document_number"].startswith("POL-")
        assert created["case_id"] == "CASE-REQ-1001"
        assert created["status"] == "draft"
        assert created["current_revision_number"] == 1
        assert created["active_revision_number"] == 1
        assert created["summary"]["working_revision_status"] == "draft"
        assert created["current_revision"]["metadata"]["region"] == "th"
        assert (temp_path / "_runtime" / "runtime_document_store.json").exists()


def test_document_review_publish_and_supersede_flow_preserves_active_version_logic():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        created = service.create_document(
            {
                "title": "Quality Standard",
                "document_class": "standard",
                "content": "Standard v1",
                "case_id": "CASE-WF-2001",
                "owner_id": "QA_OWNER",
                "approver_id": "EXEC_OWNER",
            },
            created_by="QA_OWNER",
        )
        reviewed = service.submit_review(created["document_id"], submitted_by="QA_OWNER", note="Ready for QA review")
        approved = service.approve_document(created["document_id"], approved_by="EXEC_OWNER", note="Approved")
        published = service.publish_document(created["document_id"], published_by="EXEC_OWNER", note="Publish revision 1")

        assert reviewed["status"] == "in_review"
        assert approved["status"] == "approved"
        assert published["status"] == "published"
        assert published["published_revision_number"] == 1
        assert published["active_revision_number"] == 1

        revised = service.create_revision(
            created["document_id"],
            {
                "title": "Quality Standard",
                "content": "Standard v2",
                "change_note": "Add supplier qualification controls",
            },
            created_by="QA_OWNER",
        )
        assert revised["status"] == "draft"
        assert revised["current_revision_number"] == 2
        assert revised["active_revision_number"] == 1
        assert revised["summary"]["active_revision_status"] == "published"

        service.submit_review(created["document_id"], submitted_by="QA_OWNER", note="Review revision 2")
        service.approve_document(created["document_id"], approved_by="EXEC_OWNER", note="Approve revision 2")
        republished = service.publish_document(created["document_id"], published_by="EXEC_OWNER", note="Publish revision 2")

        assert republished["published_revision_number"] == 2
        assert republished["active_revision_number"] == 2
        assert republished["revisions"][0]["status"] == "superseded"
        assert republished["revisions"][1]["status"] == "published"


def test_document_search_snapshot_and_case_linking_work_together():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        first = service.create_document(
            {
                "title": "Vendor Escalation Procedure",
                "document_class": "procedure",
                "content": "Escalate supplier issues within 24 hours.",
                "case_id": "CASE-REQ-9001",
                "business_domain": "vendor_risk",
                "tags": ["vendor", "escalation"],
            },
            created_by="OPS_OWNER",
        )
        second = service.create_document(
            {
                "title": "Finance Approval Form",
                "document_class": "form",
                "content": "Finance approval routing sheet.",
                "case_id": "CASE-REQ-9002",
                "business_domain": "finance",
                "tags": ["finance"],
            },
            created_by="FIN_OWNER",
        )

        results = service.search_documents("vendor", case_id="CASE-REQ-9001")
        snapshot = service.document_center_snapshot()

        assert len(results) == 1
        assert results[0]["document_id"] == first["document_id"]
        assert snapshot["summary"]["documents_total"] == 2
        assert snapshot["summary"]["case_linked_total"] == 2
        assert snapshot["summary"]["document_class_counts"]["procedure"] == 1
        assert second["document_class"] == "form"


def test_document_human_ask_report_and_archive_flow():
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        created = service.create_document(
            {
                "title": "Controlled Record Template",
                "document_class": "template",
                "content": "Template body",
                "case_id": "CASE-STUDIO-77",
                "owner_id": "DOC_OWNER",
                "approver_id": "EXEC_OWNER",
            },
            created_by="DOC_OWNER",
        )
        service.submit_review(created["document_id"], submitted_by="DOC_OWNER")
        service.approve_document(created["document_id"], approved_by="EXEC_OWNER")
        service.publish_document(created["document_id"], published_by="EXEC_OWNER")
        archived = service.archive_document(created["document_id"], archived_by="EXEC_OWNER", note="Template retired")
        report = service.document_human_ask_report(case_id="CASE-STUDIO-77")
        active_documents = service.list_documents(active_only=True)

        assert archived["status"] == "archived"
        assert report["summary"]["documents_total"] == 1
        assert report["summary"]["archived_total"] == 1
        assert created["document_number"] in report["narrative"]
        assert active_documents == []
