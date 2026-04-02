import shutil
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from sa_nom_governance.dashboard.dashboard_server import DashboardService
from sa_nom_governance.documents.document_service import GovernedDocumentService
from sa_nom_governance.guards.access_control import AccessControl, AccessProfile
from sa_nom_governance.guards.bootstrap_access_profiles import PRIVILEGED_OPERATOR_PERMISSIONS
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

def build_dashboard_service(temp_path: Path) -> DashboardService:
    config = AppConfig(
        base_dir=temp_path,
        environment="development",
        api_token="owner-token",
        trusted_registry_signing_key="registry-key",
    )
    return DashboardService(config=config)


def build_profile(role_name: str, *, extra_permissions: set[str] | None = None) -> AccessProfile:
    permissions = set(AccessControl.DEFAULT_PERMISSIONS[role_name])
    if extra_permissions:
        permissions.update(extra_permissions)
    return AccessProfile(
        profile_id=f'{role_name}-test',
        display_name=role_name.title(),
        role_name=role_name,
        permissions=permissions,
    )


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


def test_document_permissions_are_present_in_default_and_privileged_profiles():
    assert 'documents.read' in AccessControl.DEFAULT_PERMISSIONS['viewer']
    assert 'documents.read' in AccessControl.DEFAULT_PERMISSIONS['reviewer']
    assert 'documents.review' in AccessControl.DEFAULT_PERMISSIONS['reviewer']
    assert 'documents.read' in AccessControl.DEFAULT_PERMISSIONS['operator']
    assert 'documents.create' in AccessControl.DEFAULT_PERMISSIONS['operator']
    assert {'documents.publish', 'documents.archive'} <= PRIVILEGED_OPERATOR_PERMISSIONS


def test_dashboard_document_runtime_flow_records_auditable_lifecycle_events():
    with workspace_temp_dir() as temp_path:
        service = build_dashboard_service(temp_path)
        operator = build_profile('operator')
        reviewer = build_profile('reviewer')
        publisher = build_profile('operator', extra_permissions={'documents.publish', 'documents.archive'})

        created = service.create_document(
            {
                'title': 'Incident Response Playbook',
                'document_class': 'procedure',
                'content': 'Initial incident response workflow.',
                'case_id': 'request:req_9001',
                'owner_id': 'OPS_OWNER',
                'approver_id': 'SEC_OWNER',
                'retention_code': 'RET-SEC-5Y',
                'business_domain': 'security_operations',
                'tags': ['incident', 'playbook'],
                'metadata': {'severity': 'high'},
            },
            operator,
        )
        updated = service.update_document(
            created['document_id'],
            {
                'content': 'Updated incident workflow with containment step.',
                'change_note': 'Add containment guidance',
                'metadata': {'severity': 'high', 'phase': 'containment'},
            },
            operator,
        )
        in_review = service.submit_document_review(created['document_id'], {'note': 'Ready for review'}, operator)
        approved = service.approve_document(created['document_id'], {'note': 'Approved for release'}, reviewer)
        published = service.publish_document(created['document_id'], {'note': 'Publish into runtime'}, publisher)
        archived = service.archive_document(created['document_id'], {'note': 'Superseded by next major version'}, publisher)
        documents_snapshot = service.documents(limit=10)
        audit_items = service.list_audit(limit=20)
        audit_actions = {str(item.get('action') or '') for item in audit_items}

        assert updated['current_revision']['change_note'] == 'Add containment guidance'
        assert in_review['status'] == 'in_review'
        assert approved['status'] == 'approved'
        assert published['status'] == 'published'
        assert archived['status'] == 'archived'
        assert documents_snapshot['summary']['documents_total'] == 1
        assert documents_snapshot['summary']['archived_total'] == 1
        assert created['document_number'] == documents_snapshot['items'][0]['document_number']
        assert 'governed_document_created' in audit_actions
        assert 'governed_document_updated' in audit_actions
        assert 'governed_document_review_submitted' in audit_actions
        assert 'governed_document_approved' in audit_actions
        assert 'governed_document_published' in audit_actions
        assert 'governed_document_archived' in audit_actions
