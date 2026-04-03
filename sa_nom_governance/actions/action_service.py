from __future__ import annotations

from copy import deepcopy
from uuid import uuid4

from sa_nom_governance.actions.action_models import (
    ACTION_CATALOG,
    ActionArtifactRef,
    ActionExecutionEvent,
    GovernedActionRecord,
    normalize_action_type,
    utc_now,
)
from sa_nom_governance.actions.action_store import GovernedActionStore
from sa_nom_governance.audit.audit_logger import AuditLogger
from sa_nom_governance.documents.document_service import GovernedDocumentService
from sa_nom_governance.human_ask.human_ask_service import HumanAskService
from sa_nom_governance.utils.config import AppConfig


class GovernedActionService:
    def __init__(
        self,
        config: AppConfig,
        human_ask: HumanAskService,
        audit_logger: AuditLogger,
    ) -> None:
        self.config = config
        self.human_ask = human_ask
        self.audit_logger = audit_logger
        self.document_center = GovernedDocumentService(config)
        self.store = GovernedActionStore(config, config.action_runtime_store_path)

    def registry(self) -> list[dict[str, str]]:
        return [
            {
                "action_type": action_type,
                "label": spec["label"],
                "description": spec["description"],
                "primary_view": spec["primary_view"],
                "authority_boundary": spec["authority_boundary"],
                "side_effect_policy": spec["side_effect_policy"],
            }
            for action_type, spec in ACTION_CATALOG.items()
        ]

    def list_actions(
        self,
        *,
        status: str | None = None,
        action_type: str | None = None,
        case_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, object]]:
        return [
            self._payload(item, compact=True)
            for item in self.store.list_actions(
                status=status,
                action_type=action_type,
                case_id=case_id,
                limit=limit,
            )
        ]

    def get_action(self, action_id: str) -> dict[str, object]:
        return self._payload(self.store.get_action(action_id), compact=False)

    def action_runtime_snapshot(
        self,
        *,
        status: str | None = None,
        action_type: str | None = None,
        case_id: str | None = None,
        limit: int = 50,
    ) -> dict[str, object]:
        items = self.store.list_actions(
            status=status,
            action_type=action_type,
            case_id=case_id,
            limit=limit,
        )
        payloads = [self._payload(item, compact=True) for item in items]
        statuses = [item.status for item in items]
        types = [item.action_type for item in items]
        primary_view = "actions" if payloads else "overview"
        return {
            "summary": {
                "actions_total": len(items),
                "planned_total": statuses.count("planned"),
                "running_total": statuses.count("running"),
                "waiting_human_total": statuses.count("waiting_human"),
                "completed_total": statuses.count("completed"),
                "failed_closed_total": statuses.count("failed_closed"),
                "case_linked_total": sum(1 for item in items if item.case_id),
                "document_artifact_total": sum(
                    1 for item in items for artifact in item.artifacts if artifact.kind == "document"
                ),
                "human_ask_artifact_total": sum(
                    1 for item in items for artifact in item.artifacts if artifact.kind == "human_ask_session"
                ),
                "summarize_case_total": types.count("summarize_case"),
                "draft_document_total": types.count("draft_document"),
                "request_human_total": types.count("request_human"),
                "primary_view": primary_view,
            },
            "registry": self.registry(),
            "items": payloads,
            "store": self.store.store.descriptor().to_dict(),
        }

    def create_and_execute_action(
        self,
        payload: dict[str, object],
        *,
        requested_by: str,
        case_snapshot: dict[str, object] | None = None,
    ) -> dict[str, object]:
        record = self.queue_action(payload, requested_by=requested_by)
        return self.execute_action(
            record.action_id,
            requested_by=requested_by,
            case_snapshot=case_snapshot,
        )

    def queue_action(
        self,
        payload: dict[str, object],
        *,
        requested_by: str,
    ) -> GovernedActionRecord:
        action_type = normalize_action_type(str(payload.get("action_type", "") or ""))
        spec = ACTION_CATALOG[action_type]
        case_id = str(payload.get("case_id", "") or "").strip()
        case_reference = str(payload.get("case_reference", "") or "").strip()
        if not case_id:
            raise ValueError("AI action requires case_id.")
        if not case_reference and ':' in case_id:
            case_reference = case_id
        now = utc_now()
        record = GovernedActionRecord(
            action_id=f"act_{uuid4().hex[:12]}",
            action_type=action_type,
            label=str(payload.get("label", spec["label"]) or spec["label"]),
            case_id=case_id,
            requested_by=requested_by,
            requested_role=str(payload.get("requested_role", payload.get("role_id", "")) or ""),
            status="planned",
            created_at=now,
            updated_at=now,
            authority_boundary=spec["authority_boundary"],
            side_effect_policy=spec["side_effect_policy"],
            input_payload=self._sanitized_input(payload),
            next_action=spec["default_next_action"],
            next_view=spec["primary_view"],
            execution_log=[
                ActionExecutionEvent(
                    timestamp=now,
                    status="planned",
                    title="Action planned",
                    detail=f"{spec['label']} was queued in the governed AI runtime.",
                )
            ],
        )
        self.store.save_action(record)
        self._audit(
            action="governed_ai_action_queued",
            outcome="planned",
            reason=f"{spec['label']} was queued in the AI action runtime.",
            metadata={
                "action_id": record.action_id,
                "action_type": record.action_type,
                "case_id": record.case_id,
                "requested_by": requested_by,
                "case_reference": case_reference,
            },
        )
        return record

    def execute_action(
        self,
        action_id: str,
        *,
        requested_by: str,
        case_snapshot: dict[str, object] | None = None,
    ) -> dict[str, object]:
        record = self.store.get_action(action_id)
        running_at = utc_now()
        record.status = "running"
        record.started_at = record.started_at or running_at
        record.updated_at = running_at
        record.execution_log.append(
            ActionExecutionEvent(
                timestamp=running_at,
                status="running",
                title="Action running",
                detail=f"{record.label} is executing inside the governed AI runtime.",
            )
        )
        self.store.save_action(record)
        self._audit(
            action="governed_ai_action_started",
            outcome="running",
            reason=f"{record.label} started in the AI action runtime.",
            metadata={
                "action_id": record.action_id,
                "action_type": record.action_type,
                "case_id": record.case_id,
                "requested_by": requested_by,
                "case_reference": str(record.input_payload.get("case_reference", "") or ""),
            },
        )
        try:
            if record.action_type == "summarize_case":
                self._run_summarize_case(record, case_snapshot=case_snapshot)
            elif record.action_type == "draft_document":
                self._run_draft_document(record, requested_by=requested_by, case_snapshot=case_snapshot)
            elif record.action_type == "request_human":
                self._run_request_human(record, requested_by=requested_by, case_snapshot=case_snapshot)
            else:
                raise ValueError(f"Unsupported AI action runtime handler: {record.action_type}")
        except Exception as error:
            failed_at = utc_now()
            record.status = "failed_closed"
            record.failed_at = failed_at
            record.updated_at = failed_at
            record.latest_error = str(error)
            record.next_action = "Inspect the failed action, review the case context, and re-run only if the boundary is understood."
            record.next_view = "actions"
            record.execution_log.append(
                ActionExecutionEvent(
                    timestamp=failed_at,
                    status="failed_closed",
                    title="Action failed closed",
                    detail=str(error),
                )
            )
            self.store.save_action(record)
            self._audit(
                action="governed_ai_action_failed",
                outcome="failed_closed",
                reason=f"{record.label} failed closed in the AI action runtime.",
                metadata={
                    "action_id": record.action_id,
                    "action_type": record.action_type,
                    "case_id": record.case_id,
                    "error": str(error),
                    "case_reference": str(record.input_payload.get("case_reference", "") or ""),
                },
            )
            raise
        self.store.save_action(record)
        return self._payload(record, compact=False)

    def _run_summarize_case(
        self,
        record: GovernedActionRecord,
        *,
        case_snapshot: dict[str, object] | None = None,
    ) -> None:
        case_item = self._require_case_snapshot(record, case_snapshot)
        completed_at = utc_now()
        summary_text = self._case_summary_text(case_item)
        record.status = "completed"
        record.completed_at = completed_at
        record.updated_at = completed_at
        record.output_summary = summary_text
        record.output_payload = {
            "case_id": str(case_item.get("case_id", "") or record.case_id),
            "status": str(case_item.get("status", "monitoring") or "monitoring"),
            "primary_view": str(case_item.get("primary_view", "cases") or "cases"),
            "timeline_total": int(case_item.get("timeline_total", 0) or 0),
            "summary": deepcopy(case_item.get("summary", {}) if isinstance(case_item.get("summary", {}), dict) else {}),
            "case_reference": str(case_item.get("case_reference", "") or record.input_payload.get("case_reference", "") or ""),
        }
        record.artifacts = [
            ActionArtifactRef(
                kind="case_summary",
                ref_id=record.case_id,
                label=str(case_item.get("case_id", record.case_id) or record.case_id),
                view="cases",
                case_id=record.case_id,
                detail="Governed case summary prepared by the AI action runtime.",
            )
        ]
        record.next_action = "Review the summary and continue in the lead case lane."
        record.next_view = "cases"
        record.execution_log.append(
            ActionExecutionEvent(
                timestamp=completed_at,
                status="completed",
                title="Case summary completed",
                detail="The AI action runtime produced a governed summary of the case without side effects.",
            )
        )
        self._audit(
            action="governed_ai_case_summarized",
            outcome="completed",
            reason="AI action runtime summarized a governed case.",
            metadata={
                "action_id": record.action_id,
                "case_id": record.case_id,
                "timeline_total": int(case_item.get("timeline_total", 0) or 0),
                "case_reference": str(case_item.get("case_reference", "") or record.input_payload.get("case_reference", "") or ""),
            },
        )

    def _run_draft_document(
        self,
        record: GovernedActionRecord,
        *,
        requested_by: str,
        case_snapshot: dict[str, object] | None = None,
    ) -> None:
        case_item = self._require_case_snapshot(record, case_snapshot)
        input_payload = dict(record.input_payload)
        case_reference = str(input_payload.get("case_reference", "") or case_item.get("case_reference", "") or record.case_id).strip()
        document_class = str(input_payload.get("document_class", "record") or "record")
        title = str(input_payload.get("title", "") or self._default_document_title(case_item))
        content = str(input_payload.get("content", "") or self._default_document_content(case_item))
        created = self.document_center.create_document(
            {
                "title": title,
                "document_class": document_class,
                "content": content,
                "case_id": case_reference or record.case_id,
                "owner_id": str(input_payload.get("owner_id", requested_by) or requested_by),
                "approver_id": str(input_payload.get("approver_id", "") or ""),
                "retention_code": str(input_payload.get("retention_code", "") or ""),
                "business_domain": str(input_payload.get("business_domain", "") or self._case_business_domain(case_item)),
                "tags": [str(item) for item in input_payload.get("tags", []) if str(item).strip()] if isinstance(input_payload.get("tags", []), list) else [],
                "metadata": {
                    **(input_payload.get("metadata", {}) if isinstance(input_payload.get("metadata", {}), dict) else {}),
                    "generated_by_action_id": record.action_id,
                    "generated_by_action_type": record.action_type,
                    "generated_from_case_reference": case_reference,
                },
            },
            created_by=requested_by,
        )
        completed_at = utc_now()
        record.status = "completed"
        record.completed_at = completed_at
        record.updated_at = completed_at
        record.output_summary = f"Drafted governed document {created['document_number']} for case {record.case_id}."
        record.output_payload = deepcopy(created)
        record.artifacts = [
            ActionArtifactRef(
                kind="document",
                ref_id=str(created.get("document_id", "") or ""),
                label=str(created.get("document_number", "") or title),
                view="documents",
                case_id=record.case_id,
                detail=str(created.get("title", title) or title),
            )
        ]
        record.next_action = "Open the draft, refine it if needed, then submit it for review."
        record.next_view = "documents"
        record.execution_log.append(
            ActionExecutionEvent(
                timestamp=completed_at,
                status="completed",
                title="Document draft created",
                detail=f"{created['document_number']} was created inside the governed document runtime.",
            )
        )
        self._audit(
            action="governed_ai_document_drafted",
            outcome="completed",
            reason="AI action runtime created a governed document draft.",
            metadata={
                "action_id": record.action_id,
                "case_id": record.case_id,
                "document_id": created.get("document_id"),
                "document_number": created.get("document_number"),
                "document_class": created.get("document_class"),
                "case_reference": case_reference,
            },
        )

    def _run_request_human(
        self,
        record: GovernedActionRecord,
        *,
        requested_by: str,
        case_snapshot: dict[str, object] | None = None,
    ) -> None:
        case_item = self._require_case_snapshot(record, case_snapshot)
        input_payload = dict(record.input_payload)
        case_reference = str(input_payload.get("case_reference", "") or case_item.get("case_reference", "") or record.case_id).strip()
        role_id = str(input_payload.get("role_id", "") or self._default_human_role_id())
        session = self.human_ask.create_session(
            {
                "mode": str(input_payload.get("mode", "report") or "report"),
                "role_id": role_id,
                "prompt": str(input_payload.get("prompt", "") or self._default_human_prompt(case_item)),
                "metadata": {
                    **(input_payload.get("metadata", {}) if isinstance(input_payload.get("metadata", {}), dict) else {}),
                    "case_id": record.case_id,
                    "case_reference": case_reference,
                    "origin_action_id": record.action_id,
                    "source": "ai_action_runtime",
                },
            },
            requested_by=requested_by,
        )
        summary = session.get("summary", {}) if isinstance(session.get("summary", {}), dict) else {}
        session_status = str(session.get("status", "completed") or "completed")
        completed_at = utc_now()
        waiting_human = session_status in {"waiting_human", "escalated"} or bool(summary.get("human_review_required"))
        record.status = "waiting_human" if waiting_human else "completed"
        record.completed_at = completed_at if not waiting_human else None
        record.updated_at = completed_at
        record.waiting_reason = "Human review is required before the governed path can continue." if waiting_human else ""
        record.output_summary = f"Opened governed Human Ask record {session.get('session_id')} for case {record.case_id}."
        record.output_payload = deepcopy(session)
        record.artifacts = [
            ActionArtifactRef(
                kind="human_ask_session",
                ref_id=str(session.get("session_id", "") or ""),
                label=str(session.get("session_id", "") or "Human Ask record"),
                view="human_ask",
                case_id=record.case_id,
                detail=str(summary.get("governed_reporting_posture", "Governed record opened.") or "Governed record opened."),
            )
        ]
        record.next_action = (
            "Open the governed record and capture the human decision before the runtime continues."
            if waiting_human
            else "Open the governed record to review the AI-prepared report."
        )
        record.next_view = "human_ask"
        record.execution_log.append(
            ActionExecutionEvent(
                timestamp=completed_at,
                status=record.status,
                title="Human Ask record opened",
                detail="The AI action runtime routed this case into Human Ask for governed human review.",
            )
        )
        self._audit(
            action="governed_ai_human_request_opened",
            outcome=record.status,
            reason="AI action runtime opened a governed Human Ask record.",
            metadata={
                "action_id": record.action_id,
                "case_id": record.case_id,
                "session_id": session.get("session_id"),
                "role_id": role_id,
                "case_reference": case_reference,
            },
        )

    def _payload(self, record: GovernedActionRecord, *, compact: bool) -> dict[str, object]:
        payload = record.to_dict()
        payload["catalog"] = deepcopy(ACTION_CATALOG[record.action_type])
        payload["artifacts_total"] = len(record.artifacts)
        payload["case_reference"] = str(
            record.output_payload.get("case_reference", "")
            or record.input_payload.get("case_reference", "")
            or ""
        )
        if compact:
            payload["execution_log"] = payload["execution_log"][:3]
        return payload

    def _require_case_snapshot(
        self,
        record: GovernedActionRecord,
        case_snapshot: dict[str, object] | None,
    ) -> dict[str, object]:
        if isinstance(case_snapshot, dict) and str(case_snapshot.get("case_id", "") or "").strip():
            return case_snapshot
        raise ValueError(f"AI action {record.action_id} requires a live case snapshot for case {record.case_id}.")

    def _sanitized_input(self, payload: dict[str, object]) -> dict[str, object]:
        return {
            str(key): deepcopy(value)
            for key, value in payload.items()
            if str(key) not in {"action_type", "__case_snapshot__"}
        }

    def _case_summary_text(self, case_item: dict[str, object]) -> str:
        continuity = case_item.get("continuity", {}) if isinstance(case_item.get("continuity", {}), dict) else {}
        summary = case_item.get("summary", {}) if isinstance(case_item.get("summary", {}), dict) else {}
        work_items = case_item.get("work_items", []) if isinstance(case_item.get("work_items", []), list) else []
        linked = ", ".join(
            f"{item.get('label')} {int(item.get('total', 0) or 0)}"
            for item in work_items
            if int(item.get("total", 0) or 0) > 0
        ) or "no linked work items yet"
        return (
            f"Case {case_item.get('case_id', self._safe_case_id(case_item))} is currently {case_item.get('status', 'monitoring')}. "
            f"It has {int(case_item.get('timeline_total', 0) or 0)} timeline events and linked work across {linked}. "
            f"Human-required count is {int(summary.get('waiting_human_total', 0) or 0)}, "
            f"blocked count is {int(summary.get('blocked_total', 0) or 0)}, and "
            f"attention count is {int(summary.get('attention_total', 0) or 0)}. "
            f"Next governed move: {continuity.get('next_detail', continuity.get('next_label', 'Continue in the primary lane.'))}"
        )

    def _default_document_title(self, case_item: dict[str, object]) -> str:
        title = str(case_item.get("title", "") or self._safe_case_id(case_item)).strip()
        return f"{title} governed record"

    def _default_document_content(self, case_item: dict[str, object]) -> str:
        continuity = case_item.get("continuity", {}) if isinstance(case_item.get("continuity", {}), dict) else {}
        return (
            f"Governed document draft for {self._safe_case_id(case_item)}.\n\n"
            f"Status: {case_item.get('status', 'monitoring')}\n"
            f"Primary view: {case_item.get('primary_view', 'cases')}\n"
            f"Next governed move: {continuity.get('next_detail', continuity.get('next_label', 'Continue governed follow-up.'))}\n"
        )

    def _default_human_prompt(self, case_item: dict[str, object]) -> str:
        return (
            f"Please review case {self._safe_case_id(case_item)}, summarize the governed posture, "
            "identify the next safe action, and note whether a human approval or escalation is still required."
        )

    def _default_human_role_id(self) -> str:
        directory = self.human_ask.callable_directory(limit=20)
        entries = directory.get("entries", []) if isinstance(directory.get("entries", []), list) else []
        for entry in entries:
            if bool(entry.get("callable")):
                role_id = str(entry.get("role_id", "") or "").strip()
                if role_id:
                    return role_id
        raise ValueError("No callable Human Ask role is available for request_human.")

    def _case_business_domain(self, case_item: dict[str, object]) -> str:
        for timeline_item in case_item.get("timeline", []) if isinstance(case_item.get("timeline", []), list) else []:
            detail = str(timeline_item.get("detail", "") or "").strip()
            if detail:
                return detail.split()[0].lower().replace("/", "_").replace("-", "_")
        return ""

    def _safe_case_id(self, case_item: dict[str, object]) -> str:
        return str(case_item.get("case_id", "") or "case")

    def _audit(self, *, action: str, outcome: str, reason: str, metadata: dict[str, object]) -> None:
        self.audit_logger.record_event(
            active_role="AI_ACTION_RUNTIME",
            action=action,
            outcome=outcome,
            reason=reason,
            metadata=metadata,
        )