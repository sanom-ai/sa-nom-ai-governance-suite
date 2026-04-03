from __future__ import annotations

from copy import deepcopy
from uuid import uuid4

from sa_nom_governance.documents.document_models import (
    DOCUMENT_CLASS_CATALOG,
    DocumentRevision,
    GovernedDocumentRecord,
    build_document_number,
    normalize_document_class,
    utc_now,
)
from sa_nom_governance.documents.document_store import GovernedDocumentStore
from sa_nom_governance.utils.config import AppConfig


class GovernedDocumentService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.store = GovernedDocumentStore(config, config.document_store_path)

    def document_classes(self) -> list[dict[str, str]]:
        return [
            {"document_class": key, "prefix": value["prefix"], "label": value["label"]}
            for key, value in DOCUMENT_CLASS_CATALOG.items()
        ]

    def create_document(self, payload: dict[str, object], *, created_by: str) -> dict[str, object]:
        normalized = self._normalize_payload(payload)
        created_at = utc_now()
        sequence = self.store.next_sequence(normalized["document_class"])
        document_number = build_document_number(normalized["document_class"], sequence, created_at)
        revision = DocumentRevision(
            revision_number=1,
            title=normalized["title"],
            content=normalized["content"],
            metadata=normalized["metadata"],
            status="draft",
            created_at=created_at,
            updated_at=created_at,
            created_by=created_by,
            updated_by=created_by,
            change_note=normalized["change_note"],
        )
        document = GovernedDocumentRecord(
            document_id=f"doc_{uuid4().hex[:12]}",
            document_number=document_number,
            document_class=normalized["document_class"],
            title=normalized["title"],
            case_id=normalized["case_id"],
            owner_id=normalized["owner_id"],
            approver_id=normalized["approver_id"],
            retention_code=normalized["retention_code"],
            business_domain=normalized["business_domain"],
            tags=normalized["tags"],
            created_at=created_at,
            updated_at=created_at,
            current_revision_number=1,
            active_revision_number=1,
            published_revision_number=None,
            status="draft",
            revisions=[revision],
        )
        self.store.save_document(document)
        return self._document_payload(document)

    def update_draft(self, document_id: str, updates: dict[str, object], *, updated_by: str) -> dict[str, object]:
        document = self.store.get_document(document_id)
        revision = document.current_revision()
        if revision.status in {"published", "superseded", "archived"}:
            raise ValueError("Use create_revision() after publish or archive instead of editing the active revision directly.")
        normalized = self._normalize_update_payload(updates, document)
        now = utc_now()
        revision.title = normalized["title"]
        revision.content = normalized["content"]
        revision.metadata = normalized["metadata"]
        revision.updated_at = now
        revision.updated_by = updated_by
        revision.status = "draft"
        revision.change_note = normalized["change_note"]
        revision.review_submitted_at = None
        revision.review_submitted_by = None
        revision.review_note = ""
        revision.approved_at = None
        revision.approved_by = None
        revision.approval_note = ""
        document.title = normalized["title"]
        document.case_id = normalized["case_id"]
        document.owner_id = normalized["owner_id"]
        document.approver_id = normalized["approver_id"]
        document.retention_code = normalized["retention_code"]
        document.business_domain = normalized["business_domain"]
        document.tags = normalized["tags"]
        document.updated_at = now
        document.status = "draft"
        self.store.save_document(document)
        return self._document_payload(document)

    def create_revision(self, document_id: str, updates: dict[str, object], *, created_by: str) -> dict[str, object]:
        document = self.store.get_document(document_id)
        current = document.current_revision()
        if current.status not in {"published", "superseded", "archived"}:
            raise ValueError("Create a new revision only after the current working revision has already been published or closed.")
        normalized = self._normalize_update_payload(updates, document)
        now = utc_now()
        next_revision_number = int(document.current_revision_number or 0) + 1
        revision = DocumentRevision(
            revision_number=next_revision_number,
            title=normalized["title"],
            content=normalized["content"],
            metadata=normalized["metadata"],
            status="draft",
            created_at=now,
            updated_at=now,
            created_by=created_by,
            updated_by=created_by,
            change_note=normalized["change_note"],
        )
        document.revisions.append(revision)
        document.current_revision_number = next_revision_number
        document.title = normalized["title"]
        document.case_id = normalized["case_id"]
        document.owner_id = normalized["owner_id"]
        document.approver_id = normalized["approver_id"]
        document.retention_code = normalized["retention_code"]
        document.business_domain = normalized["business_domain"]
        document.tags = normalized["tags"]
        document.updated_at = now
        document.status = "draft"
        self.store.save_document(document)
        return self._document_payload(document)

    def submit_review(self, document_id: str, *, submitted_by: str, note: str = "") -> dict[str, object]:
        document = self.store.get_document(document_id)
        revision = document.current_revision()
        if revision.status != "draft":
            raise ValueError("Only draft revisions can be submitted for review.")
        now = utc_now()
        revision.status = "in_review"
        revision.updated_at = now
        revision.updated_by = submitted_by
        revision.review_submitted_at = now
        revision.review_submitted_by = submitted_by
        revision.review_note = str(note or "")
        document.updated_at = now
        document.status = "in_review"
        self.store.save_document(document)
        return self._document_payload(document)

    def approve_document(self, document_id: str, *, approved_by: str, note: str = "") -> dict[str, object]:
        document = self.store.get_document(document_id)
        revision = document.current_revision()
        if revision.status != "in_review":
            raise ValueError("Only in-review revisions can be approved.")
        now = utc_now()
        revision.status = "approved"
        revision.updated_at = now
        revision.updated_by = approved_by
        revision.approved_at = now
        revision.approved_by = approved_by
        revision.approval_note = str(note or "")
        document.updated_at = now
        document.status = "approved"
        self.store.save_document(document)
        return self._document_payload(document)

    def publish_document(self, document_id: str, *, published_by: str, note: str = "") -> dict[str, object]:
        document = self.store.get_document(document_id)
        revision = document.current_revision()
        if revision.status != "approved":
            raise ValueError("Only approved revisions can be published.")
        now = utc_now()
        previous_published = document.published_revision_number
        if previous_published is not None and previous_published != revision.revision_number:
            previous_revision = document.get_revision(previous_published)
            previous_revision.status = "superseded"
            previous_revision.updated_at = now
            previous_revision.updated_by = published_by
            previous_revision.superseded_at = now
            previous_revision.superseded_by = published_by
            previous_revision.superseded_by_revision = revision.revision_number
        revision.status = "published"
        revision.updated_at = now
        revision.updated_by = published_by
        revision.published_at = now
        revision.published_by = published_by
        revision.publish_note = str(note or "")
        document.updated_at = now
        document.status = "published"
        document.published_revision_number = revision.revision_number
        document.active_revision_number = revision.revision_number
        self.store.save_document(document)
        return self._document_payload(document)

    def archive_document(self, document_id: str, *, archived_by: str, note: str = "") -> dict[str, object]:
        document = self.store.get_document(document_id)
        if document.current_revision_number != document.active_revision_number:
            raise ValueError("Archive the working revision first or publish/supersede it before archiving the active document.")
        revision = document.current_revision()
        if revision.status not in {"published", "approved", "draft", "in_review"}:
            raise ValueError("This document revision cannot be archived from its current state.")
        now = utc_now()
        revision.status = "archived"
        revision.updated_at = now
        revision.updated_by = archived_by
        revision.archived_at = now
        revision.archived_by = archived_by
        revision.archive_note = str(note or "")
        document.updated_at = now
        document.status = "archived"
        if document.published_revision_number == revision.revision_number:
            document.published_revision_number = None
        document.active_revision_number = revision.revision_number
        self.store.save_document(document)
        return self._document_payload(document)

    def refresh(self) -> None:
        self.store.refresh()

    def list_documents(
        self,
        *,
        status: str | None = None,
        document_class: str | None = None,
        case_id: str | None = None,
        active_only: bool = False,
        limit: int | None = None,
    ) -> list[dict[str, object]]:
        items = self.store.list_documents()
        filtered = [
            item for item in items
            if self._matches_filters(item, status=status, document_class=document_class, case_id=case_id, active_only=active_only)
        ]
        if limit is not None:
            filtered = filtered[:limit]
        return [self._document_payload(item, compact=True) for item in filtered]

    def search_documents(self, query: str = "", **filters: object) -> list[dict[str, object]]:
        records = self._filtered_records(query=query, **filters)
        return [self._document_payload(item, compact=True) for item in records]

    def document_center_snapshot(self, *, limit: int = 50) -> dict[str, object]:
        items = self.store.list_documents()
        return {
            "summary": self._summary(items),
            "items": [self._document_payload(item, compact=True) for item in items[:limit]],
            "document_classes": self.document_classes(),
        }

    def filtered_document_snapshot(
        self,
        query: str = "",
        *,
        status: str | None = None,
        document_class: str | None = None,
        case_id: str | None = None,
        active_only: bool = False,
        limit: int = 50,
    ) -> dict[str, object]:
        items = self._filtered_records(
            query=query,
            status=status,
            document_class=document_class,
            case_id=case_id,
            active_only=active_only,
            limit=limit,
        )
        return {
            "summary": self._summary(items),
            "items": [self._document_payload(item, compact=True) for item in items],
            "document_classes": self.document_classes(),
            "filters": {
                "query": str(query or "").strip(),
                "status": str(status or "").strip(),
                "document_class": str(document_class or "").strip(),
                "case_id": str(case_id or "").strip(),
                "active_only": bool(active_only),
            },
        }

    def document_human_ask_report(
        self,
        query: str = "",
        *,
        case_id: str | None = None,
        document_class: str | None = None,
        status: str | None = None,
        limit: int = 5,
    ) -> dict[str, object]:
        items = self.search_documents(query, case_id=case_id, document_class=document_class, status=status, limit=limit)
        filtered_records = [self.store.get_document(hit["document_id"]) for hit in items]
        summary = self._summary(filtered_records)
        if items:
            first = items[0]
            narrative = (
                f"{summary['documents_total']} governed documents are in scope. "
                f"{summary['published_total']} are published, {summary['in_review_total']} are in review, and "
                f"{summary['archived_total']} are archived. "
                f"The lead document is {first['document_number']} ({first['status']}) titled {first['title']}."
            )
        else:
            narrative = "No governed documents matched the requested scope."
        return {
            "summary": summary,
            "items": items,
            "narrative": narrative,
        }

    def _summary(self, items: list[GovernedDocumentRecord]) -> dict[str, object]:
        documents_total = len(items)
        published_total = sum(1 for item in items if item.published_revision_number is not None and item.active_revision().status == "published")
        in_review_total = sum(1 for item in items if item.current_revision().status == "in_review")
        approved_total = sum(1 for item in items if item.current_revision().status == "approved")
        draft_total = sum(1 for item in items if item.current_revision().status == "draft")
        archived_total = sum(1 for item in items if item.status == "archived")
        case_linked_total = sum(1 for item in items if item.case_id)
        active_total = sum(1 for item in items if item.status != "archived")
        class_counts: dict[str, int] = {}
        for item in items:
            class_counts[item.document_class] = class_counts.get(item.document_class, 0) + 1
        return {
            "documents_total": documents_total,
            "active_total": active_total,
            "published_total": published_total,
            "in_review_total": in_review_total,
            "approved_total": approved_total,
            "draft_total": draft_total,
            "archived_total": archived_total,
            "case_linked_total": case_linked_total,
            "document_class_counts": class_counts,
        }

    def _filtered_records(self, query: str = "", **filters: object) -> list[GovernedDocumentRecord]:
        needle = str(query or "").strip().lower()
        limit = filters.get("limit")
        items = self.store.list_documents()
        matches = []
        for item in items:
            if not self._matches_filters(item, **filters):
                continue
            if needle and needle not in self._search_blob(item):
                continue
            matches.append(item)
        if limit is not None:
            matches = matches[: int(limit)]
        return matches

    def _document_payload(self, document: GovernedDocumentRecord, *, compact: bool = False) -> dict[str, object]:
        current_revision = document.current_revision()
        active_revision = document.active_revision()
        payload = {
            "document_id": document.document_id,
            "document_number": document.document_number,
            "document_class": document.document_class,
            "document_class_label": DOCUMENT_CLASS_CATALOG[document.document_class]["label"],
            "title": document.title,
            "case_id": document.case_id,
            "owner_id": document.owner_id,
            "approver_id": document.approver_id,
            "retention_code": document.retention_code,
            "business_domain": document.business_domain,
            "tags": list(document.tags),
            "created_at": document.created_at,
            "updated_at": document.updated_at,
            "status": document.status,
            "current_revision_number": document.current_revision_number,
            "active_revision_number": document.active_revision_number,
            "published_revision_number": document.published_revision_number,
            "summary": {
                "working_revision_status": current_revision.status,
                "active_revision_status": active_revision.status,
                "has_published_version": document.published_revision_number is not None,
                "active_version_logic": "published revision stays active until a newer approved revision is published" if document.published_revision_number is not None else "current revision is active until the first publish",
            },
            "current_revision": current_revision.to_dict(),
            "active_revision": active_revision.to_dict(),
        }
        if not compact:
            payload["revisions"] = [revision.to_dict() for revision in document.revisions]
        return payload

    def _matches_filters(
        self,
        item: GovernedDocumentRecord,
        *,
        status: str | None = None,
        document_class: str | None = None,
        case_id: str | None = None,
        active_only: bool = False,
        limit: int | None = None,
        **_: object,
    ) -> bool:
        if status is not None and str(item.status) != str(status):
            return False
        if document_class is not None and item.document_class != normalize_document_class(str(document_class)):
            return False
        if case_id is not None and str(item.case_id) != str(case_id):
            return False
        if active_only and item.status == "archived":
            return False
        return True

    def _search_blob(self, item: GovernedDocumentRecord) -> str:
        revision = item.current_revision()
        values = [
            item.document_id,
            item.document_number,
            item.document_class,
            DOCUMENT_CLASS_CATALOG[item.document_class]["label"],
            item.title,
            item.case_id,
            item.owner_id,
            item.approver_id,
            item.retention_code,
            item.business_domain,
            revision.content,
            revision.status,
            " ".join(item.tags),
            " ".join(f"{key}:{value}" for key, value in sorted(revision.metadata.items())),
        ]
        return " ".join(str(value or "") for value in values).lower()

    def _normalize_payload(self, payload: dict[str, object]) -> dict[str, object]:
        title = str(payload.get("title", "") or "").strip()
        if not title:
            raise ValueError("Document title is required.")
        document_class = normalize_document_class(str(payload.get("document_class", "") or ""))
        return {
            "title": title,
            "document_class": document_class,
            "content": str(payload.get("content", "") or ""),
            "case_id": str(payload.get("case_id", "") or "").strip(),
            "owner_id": str(payload.get("owner_id", "") or "").strip(),
            "approver_id": str(payload.get("approver_id", "") or "").strip(),
            "retention_code": str(payload.get("retention_code", "") or "").strip(),
            "business_domain": str(payload.get("business_domain", "") or "").strip(),
            "tags": [str(item).strip() for item in payload.get("tags", []) if str(item).strip()],
            "metadata": deepcopy(payload.get("metadata", {}) if isinstance(payload.get("metadata", {}), dict) else {}),
            "change_note": str(payload.get("change_note", "") or "").strip(),
        }

    def _normalize_update_payload(self, updates: dict[str, object], document: GovernedDocumentRecord) -> dict[str, object]:
        current = document.current_revision()
        merged = {
            "title": updates.get("title", document.title),
            "content": updates.get("content", current.content),
            "case_id": updates.get("case_id", document.case_id),
            "owner_id": updates.get("owner_id", document.owner_id),
            "approver_id": updates.get("approver_id", document.approver_id),
            "retention_code": updates.get("retention_code", document.retention_code),
            "business_domain": updates.get("business_domain", document.business_domain),
            "tags": updates.get("tags", list(document.tags)),
            "metadata": updates.get("metadata", deepcopy(current.metadata)),
            "change_note": updates.get("change_note", ""),
            "document_class": document.document_class,
        }
        return self._normalize_payload(merged)
