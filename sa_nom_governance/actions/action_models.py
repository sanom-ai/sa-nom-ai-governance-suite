from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


ACTION_CATALOG: dict[str, dict[str, str]] = {
    "summarize_case": {
        "label": "Summarize case",
        "description": "Produce a governed summary of one canonical case without side effects.",
        "primary_view": "cases",
        "authority_boundary": "read_case_scope",
        "side_effect_policy": "read_only",
        "default_next_action": "Review the case summary and continue in the lead lane.",
    },
    "draft_document": {
        "label": "Draft governed document",
        "description": "Create a governed document draft linked to one case.",
        "primary_view": "documents",
        "authority_boundary": "document_runtime_scope",
        "side_effect_policy": "create_document_draft",
        "default_next_action": "Open the draft and decide whether it should be reviewed or refined.",
    },
    "request_human": {
        "label": "Request human review",
        "description": "Open a governed Human Ask record tied to one case.",
        "primary_view": "human_ask",
        "authority_boundary": "human_boundary_scope",
        "side_effect_policy": "open_human_gate",
        "default_next_action": "Review the governed record and capture the human decision in the correct lane.",
    },
}

ACTION_STATUSES = {"planned", "running", "waiting_human", "completed", "failed_closed"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_action_type(value: str) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if normalized not in ACTION_CATALOG:
        raise ValueError(f"Unsupported AI action type: {value}")
    return normalized


def normalize_action_status(value: str) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if normalized not in ACTION_STATUSES:
        raise ValueError(f"Unsupported AI action status: {value}")
    return normalized


@dataclass(slots=True)
class ActionArtifactRef:
    kind: str
    ref_id: str
    label: str
    view: str
    case_id: str = ""
    detail: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "kind": self.kind,
            "ref_id": self.ref_id,
            "label": self.label,
            "view": self.view,
            "case_id": self.case_id,
            "detail": self.detail,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ActionArtifactRef":
        return cls(
            kind=str(payload.get("kind", "") or ""),
            ref_id=str(payload.get("ref_id", "") or ""),
            label=str(payload.get("label", "") or ""),
            view=str(payload.get("view", "overview") or "overview"),
            case_id=str(payload.get("case_id", "") or ""),
            detail=str(payload.get("detail", "") or ""),
        )


@dataclass(slots=True)
class ActionExecutionEvent:
    timestamp: str
    status: str
    title: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {
            "timestamp": self.timestamp,
            "status": self.status,
            "title": self.title,
            "detail": self.detail,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ActionExecutionEvent":
        return cls(
            timestamp=str(payload.get("timestamp", utc_now()) or utc_now()),
            status=str(payload.get("status", "planned") or "planned"),
            title=str(payload.get("title", "") or ""),
            detail=str(payload.get("detail", "") or ""),
        )


@dataclass(slots=True)
class GovernedActionRecord:
    action_id: str
    action_type: str
    label: str
    case_id: str = ""
    requested_by: str = ""
    requested_role: str = ""
    status: str = "planned"
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    started_at: str | None = None
    completed_at: str | None = None
    failed_at: str | None = None
    authority_boundary: str = ""
    side_effect_policy: str = ""
    input_payload: dict[str, Any] = field(default_factory=dict)
    output_summary: str = ""
    output_payload: dict[str, Any] = field(default_factory=dict)
    next_action: str = ""
    next_view: str = "overview"
    latest_error: str = ""
    waiting_reason: str = ""
    artifacts: list[ActionArtifactRef] = field(default_factory=list)
    execution_log: list[ActionExecutionEvent] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type,
            "label": self.label,
            "case_id": self.case_id,
            "requested_by": self.requested_by,
            "requested_role": self.requested_role,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "failed_at": self.failed_at,
            "authority_boundary": self.authority_boundary,
            "side_effect_policy": self.side_effect_policy,
            "input_payload": deepcopy(self.input_payload),
            "output_summary": self.output_summary,
            "output_payload": deepcopy(self.output_payload),
            "next_action": self.next_action,
            "next_view": self.next_view,
            "latest_error": self.latest_error,
            "waiting_reason": self.waiting_reason,
            "artifacts": [item.to_dict() for item in self.artifacts],
            "execution_log": [item.to_dict() for item in self.execution_log],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "GovernedActionRecord":
        return cls(
            action_id=str(payload.get("action_id", "") or ""),
            action_type=normalize_action_type(str(payload.get("action_type", "summarize_case") or "summarize_case")),
            label=str(payload.get("label", "") or ""),
            case_id=str(payload.get("case_id", "") or ""),
            requested_by=str(payload.get("requested_by", "") or ""),
            requested_role=str(payload.get("requested_role", "") or ""),
            status=normalize_action_status(str(payload.get("status", "planned") or "planned")),
            created_at=str(payload.get("created_at", utc_now()) or utc_now()),
            updated_at=str(payload.get("updated_at", payload.get("created_at", utc_now())) or utc_now()),
            started_at=payload.get("started_at"),
            completed_at=payload.get("completed_at"),
            failed_at=payload.get("failed_at"),
            authority_boundary=str(payload.get("authority_boundary", "") or ""),
            side_effect_policy=str(payload.get("side_effect_policy", "") or ""),
            input_payload=deepcopy(payload.get("input_payload", {}) if isinstance(payload.get("input_payload", {}), dict) else {}),
            output_summary=str(payload.get("output_summary", "") or ""),
            output_payload=deepcopy(payload.get("output_payload", {}) if isinstance(payload.get("output_payload", {}), dict) else {}),
            next_action=str(payload.get("next_action", "") or ""),
            next_view=str(payload.get("next_view", "overview") or "overview"),
            latest_error=str(payload.get("latest_error", "") or ""),
            waiting_reason=str(payload.get("waiting_reason", "") or ""),
            artifacts=[
                ActionArtifactRef.from_dict(item)
                for item in payload.get("artifacts", [])
                if isinstance(item, dict)
            ],
            execution_log=[
                ActionExecutionEvent.from_dict(item)
                for item in payload.get("execution_log", [])
                if isinstance(item, dict)
            ],
        )