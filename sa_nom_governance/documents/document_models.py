from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

DOCUMENT_CLASS_CATALOG: dict[str, dict[str, str]] = {
    "policy": {"prefix": "POL", "label": "Policy"},
    "standard": {"prefix": "STD", "label": "Standard"},
    "procedure": {"prefix": "PROC", "label": "Procedure"},
    "work_instruction": {"prefix": "WI", "label": "Work Instruction"},
    "form": {"prefix": "FORM", "label": "Form"},
    "template": {"prefix": "TPL", "label": "Template"},
    "record": {"prefix": "REC", "label": "Record"},
}

WORKING_DOCUMENT_STATUSES = {"draft", "in_review", "approved", "published", "archived"}
REVISION_STATUSES = WORKING_DOCUMENT_STATUSES | {"superseded"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_document_class(value: str) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if normalized not in DOCUMENT_CLASS_CATALOG:
        raise ValueError(f"Unsupported document class: {value}")
    return normalized


def build_document_number(document_class: str, sequence: int, created_at: str | None = None) -> str:
    normalized = normalize_document_class(document_class)
    prefix = DOCUMENT_CLASS_CATALOG[normalized]["prefix"]
    year = str(created_at or utc_now())[:4]
    return f"{prefix}-{year}-{int(sequence):04d}"


@dataclass(slots=True)
class DocumentRevision:
    revision_number: int
    title: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    status: str = "draft"
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    created_by: str = "system"
    updated_by: str = "system"
    change_note: str = ""
    review_submitted_at: str | None = None
    review_submitted_by: str | None = None
    review_note: str = ""
    approved_at: str | None = None
    approved_by: str | None = None
    approval_note: str = ""
    published_at: str | None = None
    published_by: str | None = None
    publish_note: str = ""
    superseded_at: str | None = None
    superseded_by: str | None = None
    superseded_by_revision: int | None = None
    archive_note: str = ""
    archived_at: str | None = None
    archived_by: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "revision_number": self.revision_number,
            "title": self.title,
            "content": self.content,
            "metadata": deepcopy(self.metadata),
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "change_note": self.change_note,
            "review_submitted_at": self.review_submitted_at,
            "review_submitted_by": self.review_submitted_by,
            "review_note": self.review_note,
            "approved_at": self.approved_at,
            "approved_by": self.approved_by,
            "approval_note": self.approval_note,
            "published_at": self.published_at,
            "published_by": self.published_by,
            "publish_note": self.publish_note,
            "superseded_at": self.superseded_at,
            "superseded_by": self.superseded_by,
            "superseded_by_revision": self.superseded_by_revision,
            "archive_note": self.archive_note,
            "archived_at": self.archived_at,
            "archived_by": self.archived_by,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DocumentRevision":
        return cls(
            revision_number=int(payload.get("revision_number", 1) or 1),
            title=str(payload.get("title", "") or ""),
            content=str(payload.get("content", "") or ""),
            metadata=deepcopy(payload.get("metadata", {}) if isinstance(payload.get("metadata", {}), dict) else {}),
            status=str(payload.get("status", "draft") or "draft"),
            created_at=str(payload.get("created_at", utc_now()) or utc_now()),
            updated_at=str(payload.get("updated_at", payload.get("created_at", utc_now())) or utc_now()),
            created_by=str(payload.get("created_by", "system") or "system"),
            updated_by=str(payload.get("updated_by", payload.get("created_by", "system")) or "system"),
            change_note=str(payload.get("change_note", "") or ""),
            review_submitted_at=payload.get("review_submitted_at"),
            review_submitted_by=payload.get("review_submitted_by"),
            review_note=str(payload.get("review_note", "") or ""),
            approved_at=payload.get("approved_at"),
            approved_by=payload.get("approved_by"),
            approval_note=str(payload.get("approval_note", "") or ""),
            published_at=payload.get("published_at"),
            published_by=payload.get("published_by"),
            publish_note=str(payload.get("publish_note", "") or ""),
            superseded_at=payload.get("superseded_at"),
            superseded_by=payload.get("superseded_by"),
            superseded_by_revision=int(payload["superseded_by_revision"]) if payload.get("superseded_by_revision") is not None else None,
            archive_note=str(payload.get("archive_note", "") or ""),
            archived_at=payload.get("archived_at"),
            archived_by=payload.get("archived_by"),
        )


@dataclass(slots=True)
class GovernedDocumentRecord:
    document_id: str
    document_number: str
    document_class: str
    title: str
    case_id: str = ""
    owner_id: str = ""
    approver_id: str = ""
    retention_code: str = ""
    business_domain: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    current_revision_number: int = 1
    active_revision_number: int = 1
    published_revision_number: int | None = None
    status: str = "draft"
    revisions: list[DocumentRevision] = field(default_factory=list)

    def get_revision(self, revision_number: int) -> DocumentRevision:
        for revision in self.revisions:
            if revision.revision_number == revision_number:
                return revision
        raise KeyError(f"Document revision not found: {revision_number}")

    def current_revision(self) -> DocumentRevision:
        return self.get_revision(self.current_revision_number)

    def active_revision(self) -> DocumentRevision:
        return self.get_revision(self.active_revision_number)

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "document_number": self.document_number,
            "document_class": self.document_class,
            "title": self.title,
            "case_id": self.case_id,
            "owner_id": self.owner_id,
            "approver_id": self.approver_id,
            "retention_code": self.retention_code,
            "business_domain": self.business_domain,
            "tags": list(self.tags),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "current_revision_number": self.current_revision_number,
            "active_revision_number": self.active_revision_number,
            "published_revision_number": self.published_revision_number,
            "status": self.status,
            "revisions": [revision.to_dict() for revision in self.revisions],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "GovernedDocumentRecord":
        revisions = [
            DocumentRevision.from_dict(item)
            for item in payload.get("revisions", [])
            if isinstance(item, dict)
        ]
        revisions.sort(key=lambda item: item.revision_number)
        return cls(
            document_id=str(payload.get("document_id", "") or ""),
            document_number=str(payload.get("document_number", "") or ""),
            document_class=normalize_document_class(str(payload.get("document_class", "policy") or "policy")),
            title=str(payload.get("title", "") or ""),
            case_id=str(payload.get("case_id", "") or ""),
            owner_id=str(payload.get("owner_id", "") or ""),
            approver_id=str(payload.get("approver_id", "") or ""),
            retention_code=str(payload.get("retention_code", "") or ""),
            business_domain=str(payload.get("business_domain", "") or ""),
            tags=[str(item) for item in payload.get("tags", []) if str(item).strip()],
            created_at=str(payload.get("created_at", utc_now()) or utc_now()),
            updated_at=str(payload.get("updated_at", payload.get("created_at", utc_now())) or utc_now()),
            current_revision_number=int(payload.get("current_revision_number", 1) or 1),
            active_revision_number=int(payload.get("active_revision_number", payload.get("published_revision_number") or payload.get("current_revision_number", 1)) or 1),
            published_revision_number=int(payload["published_revision_number"]) if payload.get("published_revision_number") is not None else None,
            status=str(payload.get("status", "draft") or "draft"),
            revisions=revisions,
        )
