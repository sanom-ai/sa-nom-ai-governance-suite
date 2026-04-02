from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from sa_nom_governance.audit.audit_logger import AuditLogger
from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.core.core_engine import CoreEngine
from sa_nom_governance.core.hierarchy_registry import HierarchyEntry
from sa_nom_governance.human_ask.human_ask_presenter import (
    build_meeting_synthesis,
    build_participant_contribution_summary,
    build_participant_next_safe_action,
    build_response_message,
    build_session_record,
    build_transcript_summary,
    mode_label as present_mode_label,
)
from sa_nom_governance.human_ask.human_ask_models import (
    AskActionItem,
    AskContextChain,
    AskDecisionSummary,
    AskExchange,
    AskParticipantDecision,
    AskParticipant,
    AskParticipantSummary,
    CallableDirectoryEntry,
    HumanAskSession,
    HumanDecisionInboxContract,
    utc_now,
)
from sa_nom_governance.human_ask.human_ask_scope import assess_prompt_scope
from sa_nom_governance.human_ask.human_ask_store import HumanAskStore
from sa_nom_governance.utils.owner_identity import normalize_executive_owner_id
from sa_nom_governance.ptag.pt_oss_engine import PTOSSEngine
from sa_nom_governance.utils.registry import RoleRegistry
from sa_nom_governance.studio.role_private_studio_models import (
    NormalizedRoleSpec,
    PTOSSAssessment,
    SimulationReport,
    StructuredJD,
    ValidationReport,
)
from sa_nom_governance.studio.role_private_studio_service import RolePrivateStudioService


class HumanAskService:
    SAFETY_DOMAINS = {"product_safety", "safety", "safety_operations"}
    HIGH_RISK_TERMS = {
        "approve": 0.12,
        "publish": 0.12,
        "release": 0.18,
        "sign": 0.20,
        "fund": 0.18,
        "delete": 0.22,
        "terminate": 0.24,
        "emergency": 0.22,
        "incident": 0.18,
        "override": 0.14,
        "suspend": 0.18,
        "safety": 0.18,
        "contract": 0.10,
        "policy": 0.08,
        "compliance": 0.08,
    }

    def __init__(
        self,
        config: AppConfig,
        engine: CoreEngine,
        registry: RoleRegistry,
        role_private_studio: RolePrivateStudioService,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        self.config = config
        self.engine = engine
        self.registry = registry
        self.role_private_studio = role_private_studio
        self.audit_logger = audit_logger or engine.audit_logger
        self.store = HumanAskStore(config, config.human_ask_store_path)
        bundled_dir = Path(__file__).resolve().parents[2]
        foundation_path = config.pt_oss_foundation_path or (config.base_dir / "resources" / "pt_oss" / "pt_oss_foundation.json")
        legacy_foundation_path = config.base_dir / "pt_oss_foundation.json"
        effective_foundation_path = foundation_path if foundation_path.exists() else legacy_foundation_path
        self.pt_oss_engine = PTOSSEngine(effective_foundation_path if effective_foundation_path.exists() else bundled_dir / "resources" / "pt_oss" / "pt_oss_foundation.json")
        self.confidence_threshold = config.human_ask_confidence_threshold
        self.freshness_warning_hours = max(1, int(config.human_ask_freshness_warning_hours))
        self.freshness_stale_hours = max(self.freshness_warning_hours, int(config.human_ask_freshness_stale_hours))

    def human_ask_snapshot(self, limit: int = 50) -> dict[str, object]:
        sessions = [self._session_payload(item, compact=True) for item in self.store.list_sessions()[:limit]]
        directory = self.callable_directory(limit=limit)
        statuses = [item["status"] for item in sessions]
        modes = [item.get("mode", "report") for item in sessions]
        summaries = [item.get("summary", {}) for item in sessions]
        dispositions = [item.get("director_disposition", "ready_to_proceed") for item in summaries]
        queue_states = [item.get("queue_state", "not_queued") for item in summaries]
        queue_lanes = [item.get("queue_lane", "autonomy") for item in summaries]
        queue_priorities = [item.get("queue_priority", "normal") for item in summaries]
        inbox_states = [item.get("inbox_state", "autonomy_ready") for item in summaries]
        confidence_bands = [item.get("confidence_band", "ready") for item in summaries]
        freshness_states = [item.get("freshness_status", "fresh") for item in summaries]
        reporting_postures = [item.get("governed_reporting_posture", "autonomy_ready") for item in summaries]
        return {
            "summary": {
                "sessions_total": len(sessions),
                "completed_total": statuses.count("completed"),
                "waiting_human_total": statuses.count("waiting_human"),
                "escalated_total": statuses.count("escalated"),
                "blocked_total": statuses.count("blocked"),
                "report_total": modes.count("report"),
                "meeting_total": modes.count("meeting"),
                "recorded_total": len(sessions),
                "follow_up_total": sum(1 for item in summaries if item.get("follow_up")),
                "multi_participant_total": sum(1 for item in summaries if int(item.get("participant_total", 1)) > 1),
                "ready_to_proceed_total": dispositions.count("ready_to_proceed"),
                "guarded_follow_up_total": dispositions.count("guarded_follow_up"),
                "hold_for_clearance_total": dispositions.count("hold_for_clearance"),
                "decision_queue_total": sum(1 for item in queue_states if item != "not_queued"),
                "human_queue_total": sum(1 for item in summaries if item.get("queue_human_required")),
                "autonomy_queue_total": queue_lanes.count("autonomy"),
                "human_review_queue_total": queue_lanes.count("human_review"),
                "clearance_queue_total": queue_lanes.count("clearance"),
                "guarded_queue_total": queue_lanes.count("guarded_follow_up"),
                "high_priority_queue_total": sum(1 for item in queue_priorities if item in {"high", "critical"}),
                "execution_plan_linked_total": sum(1 for item in summaries if item.get("queue_execution_plan_id")),
                "inbox_total": sum(1 for item in inbox_states if item != "autonomy_ready"),
                "inbox_human_action_total": inbox_states.count("human_action_required"),
                "inbox_clearance_total": inbox_states.count("clearance_required"),
                "inbox_guarded_total": inbox_states.count("guarded_follow_up"),
                "confidence_threshold": self.confidence_threshold,
                "freshness_warning_hours": self.freshness_warning_hours,
                "freshness_stale_hours": self.freshness_stale_hours,
                "low_confidence_total": confidence_bands.count("below_threshold"),
                "guarded_confidence_total": confidence_bands.count("guarded"),
                "ready_confidence_total": confidence_bands.count("ready"),
                "fresh_total": freshness_states.count("fresh"),
                "aging_total": freshness_states.count("aging"),
                "stale_total": freshness_states.count("stale"),
                "oldest_session_age_hours": max((int(item.get("freshness_age_hours", 0) or 0) for item in summaries), default=0),
                "autonomy_ready_posture_total": reporting_postures.count("autonomy_ready"),
                "guarded_follow_up_posture_total": reporting_postures.count("guarded_follow_up"),
                "human_gated_posture_total": reporting_postures.count("human_gated"),
                "blocked_posture_total": reporting_postures.count("blocked"),
                "callable_total": directory["summary"]["callable_total"],
                "studio_callable_total": directory["summary"]["studio_callable_total"],
                "published_callable_total": directory["summary"]["published_callable_total"],
            },
            "sessions": sessions,
            "callable_directory": directory,
        }

    def list_sessions(self, status: str | None = None, limit: int = 100) -> list[dict[str, object]]:
        return [self._session_payload(item, compact=True) for item in self.store.list_sessions(status=status)[:limit]]

    def list_human_decision_inbox(
        self,
        *,
        inbox_state: str | None = None,
        queue_lane: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, object]]:
        sessions = self.store.list_sessions()
        items: list[dict[str, object]] = []
        for session in sessions:
            session_payload = self._session_payload(session, compact=True)
            session_metadata = session_payload.get("metadata", {}) if isinstance(session_payload.get("metadata", {}), dict) else {}
            inbox = session_metadata.get("human_decision_inbox", {}) if isinstance(session_metadata.get("human_decision_inbox", {}), dict) else {}
            if not inbox:
                continue
            if inbox_state is not None and inbox.get("inbox_state") != inbox_state:
                continue
            if queue_lane is not None and inbox.get("queue_lane") != queue_lane:
                continue
            item = {
                "session_id": session_payload["session_id"],
                "status": session_payload["status"],
                "requested_by": session_payload["requested_by"],
                "participant": session_payload["participant"]["display_name"],
                "role_id": session_payload["participant"]["role_id"],
                "mode": session_payload["mode"],
                "director_disposition": str(session_payload.get("summary", {}).get("director_disposition", "ready_to_proceed")),
                "human_decision_inbox": inbox,
                "session_summary": session_payload.get("summary", {}),
            }
            items.append(item)
        return items[:limit]

    def get_session(self, session_id: str) -> dict[str, object]:
        return self._session_payload(self.store.get_session(session_id), compact=False)

    def _session_payload(self, session: HumanAskSession, *, compact: bool = False) -> dict[str, object]:
        payload = session.to_dict(compact=compact)
        decision_summary = payload.get("decision_summary", {}) if isinstance(payload.get("decision_summary", {}), dict) else {}
        decision_metadata = decision_summary.get("metadata", {}) if isinstance(decision_summary.get("metadata", {}), dict) else {}
        session_metadata = payload.get("metadata", {}) if isinstance(payload.get("metadata", {}), dict) else {}
        inbox_contract = session_metadata.get("human_decision_inbox", {}) if isinstance(session_metadata.get("human_decision_inbox", {}), dict) else {}
        summary = payload.get("summary", {}) if isinstance(payload.get("summary", {}), dict) else {}
        confidence_score = float(summary.get("confidence_score", 0.0) or 0.0)
        confidence_gap = round(confidence_score - self.confidence_threshold, 4)
        confidence_band = self._confidence_band(confidence_score)
        freshness_age_hours = self._age_hours(str(payload.get("updated_at") or payload.get("created_at") or ""))
        freshness_status = self._freshness_status(freshness_age_hours)
        governed_reporting_posture = self._reporting_posture(
            status=str(payload.get("status", "completed")),
            director_disposition=str(summary.get("director_disposition", "ready_to_proceed")),
            inbox_state=str(summary.get("inbox_state", "autonomy_ready")),
            confidence_band=confidence_band,
        )
        evidence_refs = [str(item) for item in inbox_contract.get("evidence_refs", []) if str(item)] if isinstance(inbox_contract.get("evidence_refs", []), list) else []
        scope_status = str(decision_metadata.get("scope_status", "unknown"))

        summary.update(
            {
                "confidence_threshold": self.confidence_threshold,
                "confidence_gap": confidence_gap,
                "confidence_band": confidence_band,
                "freshness_age_hours": freshness_age_hours,
                "freshness_status": freshness_status,
                "freshness_warning_hours": self.freshness_warning_hours,
                "freshness_stale_hours": self.freshness_stale_hours,
                "governed_reporting_posture": governed_reporting_posture,
                "scope_status": scope_status,
                "scope_assessment_recorded": bool(decision_metadata),
                "evidence_refs_total": len(evidence_refs),
                "human_review_required": str(summary.get("inbox_state", "autonomy_ready")) in {"human_action_required", "clearance_required"},
            }
        )
        payload["summary"] = summary

        if decision_summary:
            decision_summary["metadata"] = {
                **decision_metadata,
                "confidence_gap": confidence_gap,
                "confidence_band": confidence_band,
            }
            payload["decision_summary"] = decision_summary

        session_metadata["governed_reporting_posture"] = governed_reporting_posture
        session_metadata["human_ask_policy"] = {
            "confidence_threshold": self.confidence_threshold,
            "freshness_warning_hours": self.freshness_warning_hours,
            "freshness_stale_hours": self.freshness_stale_hours,
        }
        payload["metadata"] = session_metadata
        return payload

    def _confidence_band(self, confidence_score: float) -> str:
        if confidence_score < self.confidence_threshold:
            return "below_threshold"
        if confidence_score < min(self.confidence_threshold + 0.08, 0.99):
            return "guarded"
        return "ready"

    def _freshness_status(self, age_hours: int) -> str:
        if age_hours >= self.freshness_stale_hours:
            return "stale"
        if age_hours >= self.freshness_warning_hours:
            return "aging"
        return "fresh"

    def _reporting_posture(
        self,
        *,
        status: str,
        director_disposition: str,
        inbox_state: str,
        confidence_band: str,
    ) -> str:
        if status == "blocked" or director_disposition == "hold_for_clearance" or inbox_state == "clearance_required":
            return "blocked"
        if status in {"waiting_human", "escalated"} or inbox_state == "human_action_required":
            return "human_gated"
        if inbox_state == "guarded_follow_up" or director_disposition == "guarded_follow_up" or confidence_band == "guarded":
            return "guarded_follow_up"
        return "autonomy_ready"

    def _age_hours(self, timestamp: str) -> int:
        parsed = self._parse_timestamp(timestamp)
        if parsed is None:
            return 0
        return max(0, int((datetime.now(timezone.utc) - parsed).total_seconds() // 3600))

    def _parse_timestamp(self, value: str | None) -> datetime | None:
        if value in {None, ""}:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None

    def callable_directory(self, limit: int = 200) -> dict[str, object]:
        entries = self._build_callable_directory()
        statuses = [item.callable_status for item in entries]
        return {
            "summary": {
                "entries_total": len(entries),
                "callable_total": sum(1 for item in entries if item.callable),
                "published_callable_total": sum(1 for item in entries if item.source == "published_role" and item.callable),
                "studio_callable_total": sum(1 for item in entries if item.source == "studio_draft" and item.callable),
                "available_total": statuses.count("available"),
                "busy_total": statuses.count("busy"),
                "under_override_total": statuses.count("under_override"),
                "review_required_total": statuses.count("review_required"),
                "restricted_total": statuses.count("restricted"),
            },
            "entries": [item.to_dict() for item in entries[:limit]],
        }

    def create_session(self, payload: dict[str, object], requested_by: str) -> dict[str, object]:
        prompt = str(payload.get("prompt", "")).strip()
        if not prompt:
            raise ValueError("Human Ask prompt is required.")

        mode = self._normalize_mode(str(payload.get("mode", "report") or "report"))
        participant_entries = self._resolve_session_entries(payload, mode=mode)
        participant_entry = participant_entries[0]
        parent_session_id = str(payload.get("parent_session_id") or "").strip() or None
        inheritance_mode = str(payload.get("inheritance_mode") or ("inherit" if parent_session_id else "reset")).strip().lower()
        context_chain = self._build_context_chain(parent_session_id=parent_session_id, inheritance_mode=inheritance_mode)
        metadata = payload.get("metadata", {}) if isinstance(payload.get("metadata", {}), dict) else {}
        request_metadata = {**metadata, "mode": mode}
        decision_summary = self._build_decision_summary(prompt=prompt, entry=participant_entry, metadata=request_metadata)
        decision_queue = self._build_decision_queue(
            entry=participant_entry,
            decision_summary=decision_summary,
            metadata=request_metadata,
        )
        participant_summaries = self._build_participant_summaries(
            entries=participant_entries,
            decision_summary=decision_summary,
            prompt=prompt,
        )
        participant_decisions = self._build_participant_decisions(
            entries=participant_entries,
            decision_summary=decision_summary,
            prompt=prompt,
        )
        meeting_overview = self._meeting_decision_overview(participant_decisions)
        director_disposition = self._director_disposition(
            mode=mode,
            decision_summary=decision_summary,
            meeting_overview=meeting_overview,
        )
        transcript = self._build_transcript(
            prompt=prompt,
            entry=participant_entry,
            entries=participant_entries,
            decision_summary=decision_summary,
            context_chain=context_chain,
            participant_decisions=participant_decisions,
            meeting_overview=meeting_overview,
        )
        action_items = self._build_action_items(
            entry=participant_entry,
            entries=participant_entries,
            decision_summary=decision_summary,
            participant_decisions=participant_decisions,
        )
        participant = self._participant_from_entry(participant_entry)
        session_id = f"ask_{uuid4().hex[:12]}"
        human_decision_inbox = self._build_human_decision_inbox(
            session_id=session_id,
            prompt=prompt,
            entry=participant_entry,
            decision_summary=decision_summary,
            decision_queue=decision_queue,
            metadata=request_metadata,
            director_disposition=director_disposition,
        )
        session = HumanAskSession(
            session_id=session_id,
            requested_by=requested_by,
            created_at=utc_now(),
            updated_at=utc_now(),
            status=decision_summary.outcome,
            mode=mode,
            prompt=prompt,
            participant=participant,
            context_chain=context_chain,
            transcript=transcript,
            decision_summary=decision_summary,
            action_items=action_items,
            transcript_summary=self._build_transcript_summary(
                entry=participant_entry,
                entries=participant_entries,
                decision_summary=decision_summary,
                participant_decisions=participant_decisions,
            ),
            metadata={
                "director_identity": "AI Director",
                "active_hat": participant_entry.role_id,
                "session_kind": mode,
                "directory_entry_id": participant_entry.entry_id,
                "source": participant_entry.source,
                "studio_request_id": participant_entry.metadata.get("studio_request_id"),
                "requested_role_id": str(payload.get("role_id") or participant_entry.role_id),
                "recorded_from_studio": participant_entry.source == "studio_draft",
                "human_ask_phase": "A",
                "participant_total": len(participant_entries),
                "decision_queue": decision_queue,
                "human_decision_inbox": human_decision_inbox.to_dict(),
                "participants": [self._participant_payload(item) for item in participant_entries],
                "participant_summaries": [item.to_dict() for item in participant_summaries],
                "participant_decisions": [item.to_dict() for item in participant_decisions],
                "meeting_overview": meeting_overview,
                "director_disposition": director_disposition,
                "session_record": self._build_session_record(
                    prompt=prompt,
                    mode=mode,
                    participant_entry=participant_entry,
                    participant_entries=participant_entries,
                    decision_summary=decision_summary,
                    meeting_overview=meeting_overview,
                    participant_decisions=participant_decisions,
                ),
            },
        )
        self.store.save_session(session)
        self._audit(
            action="human_ask_session_created",
            outcome=session.status,
            reason=f"Human Ask record created for {participant_entry.display_name}.",
            metadata={
                "session_id": session.session_id,
                "requested_by": requested_by,
                "participant": participant_entry.to_dict(),
                "participants": [item.to_dict() for item in participant_entries],
                "participant_summaries": [item.to_dict() for item in participant_summaries],
                "participant_decisions": [item.to_dict() for item in participant_decisions],
                "meeting_overview": meeting_overview,
                "director_disposition": director_disposition,
                "decision_summary": decision_summary.to_dict(),
                "decision_queue": decision_queue,
                "human_decision_inbox": human_decision_inbox.to_dict(),
                "parent_session_id": parent_session_id,
            },
        )
        return self._session_payload(session, compact=False)

    def create_studio_record_request(self, studio_request_id: str, payload: dict[str, object], requested_by: str) -> dict[str, object]:
        forwarded = dict(payload)
        forwarded["studio_request_id"] = studio_request_id
        forwarded.setdefault("mode", "report")
        forwarded.setdefault("prompt", "Prepare a governed report for the current Role Private Studio draft.")
        result = self.create_session(forwarded, requested_by=requested_by)
        self._audit(
            action="human_ask_studio_record",
            outcome=result.get("status", "completed"),
            reason="Role Private Studio draft was routed into Human Ask for governed record capture.",
            metadata={
                "session_id": result.get("session_id"),
                "studio_request_id": studio_request_id,
                "requested_by": requested_by,
            },
        )
        return result

    def _resolve_session_entries(self, payload: dict[str, object], *, mode: str) -> list[CallableDirectoryEntry]:
        if mode != "meeting":
            return [self._resolve_target_entry(payload)]
        directory = self._build_callable_directory()
        entry_by_id = {item.entry_id: item for item in directory}
        requested_entry_ids = [str(item).strip() for item in payload.get("participant_entry_ids", []) if str(item).strip()]
        requested_role_ids = [str(item).strip().upper() for item in payload.get("participant_role_ids", []) if str(item).strip()]
        entries: list[CallableDirectoryEntry] = []
        seen: set[str] = set()

        for entry_id in requested_entry_ids:
            entry = entry_by_id.get(entry_id)
            if entry is None:
                raise ValueError(f"Human Ask meeting participant not found: {entry_id}")
            if entry.entry_id not in seen:
                entries.append(entry)
                seen.add(entry.entry_id)

        for role_id in requested_role_ids:
            candidate = next((item for item in directory if item.role_id == role_id and item.source == "published_role"), None)
            if candidate is None:
                raise ValueError(f"Human Ask meeting role target not found: {role_id}")
            if candidate.entry_id not in seen:
                entries.append(candidate)
                seen.add(candidate.entry_id)

        if not entries:
            entries.append(self._resolve_target_entry(payload))
        return entries

    def _build_callable_directory(self) -> list[CallableDirectoryEntry]:
        entries: list[CallableDirectoryEntry] = []
        override_roles = {item.active_role for item in self.engine.human_override.list_requests(status="pending")}
        lock_states = self.engine.lock_manager.list_locks()
        locked_roles = {item.active_role: item.status for item in lock_states}

        for hierarchy_entry in sorted(self.engine.hierarchy_registry.list_entries(), key=lambda item: (item.stratum, item.role_id)):
            pt_oss_assessment = self._assess_runtime_role(hierarchy_entry)
            callable_status = "available"
            notes: list[str] = []
            if hierarchy_entry.role_id in override_roles:
                callable_status = "under_override"
                notes.append("A pending human override currently involves this role.")
            elif hierarchy_entry.role_id in locked_roles:
                callable_status = "under_override" if locked_roles[hierarchy_entry.role_id] == "waiting_human" else "busy"
                notes.append("A live runtime lock currently holds this role on an active resource.")
            elif not hierarchy_entry.allowed_actions and not hierarchy_entry.required_human_actions:
                callable_status = "restricted"
                notes.append("The role has no callable actions available through runtime policy.")
            entries.append(
                CallableDirectoryEntry(
                    entry_id=f"role:{hierarchy_entry.role_id}",
                    source="published_role",
                    role_id=hierarchy_entry.role_id,
                    display_name=hierarchy_entry.title or hierarchy_entry.role_id,
                    business_domain=hierarchy_entry.business_domain,
                    callable=callable_status != "restricted",
                    callable_status=callable_status,
                    active_hat=hierarchy_entry.role_id,
                    escalation_owner=hierarchy_entry.escalation_to,
                    safety_owner=hierarchy_entry.safety_owner,
                    publication_status="published",
                    pt_oss_posture=pt_oss_assessment.posture,
                    pt_oss_readiness_score=pt_oss_assessment.readiness_score,
                    operating_mode=hierarchy_entry.operating_mode,
                    assigned_user_id=hierarchy_entry.assigned_user_id,
                    executive_owner_id=hierarchy_entry.executive_owner_id,
                    seat_id=hierarchy_entry.seat_id,
                    notes=notes or pt_oss_assessment.recommendations[:2],
                    summary=self._runtime_entry_summary(hierarchy_entry, pt_oss_assessment, callable_status),
                    metadata={
                        "stratum": hierarchy_entry.stratum,
                        "reports_to": hierarchy_entry.reports_to,
                        "allowed_actions": sorted(hierarchy_entry.allowed_actions),
                        "required_human_actions": sorted(hierarchy_entry.required_human_actions),
                        "handled_resources": sorted(hierarchy_entry.handled_resources),
                        "operating_mode": hierarchy_entry.operating_mode,
                        "assigned_user_id": hierarchy_entry.assigned_user_id,
                        "executive_owner_id": hierarchy_entry.executive_owner_id,
                        "seat_id": hierarchy_entry.seat_id,
                    },
                )
            )

        for request in self.role_private_studio.store.list_requests():
            if request.publish_artifact is not None:
                continue
            role_id = request.normalized_spec.role_id if request.normalized_spec else request.structured_jd.role_name.upper().replace(" ", "_")
            posture = request.pt_oss_assessment.posture if request.pt_oss_assessment else "unknown"
            readiness_score = request.pt_oss_assessment.readiness_score if request.pt_oss_assessment else 0
            validation_ok = bool(request.validation_report and not request.validation_report.blocked_publish)
            simulation_ok = bool(request.simulation_report and request.simulation_report.status == "passed")
            callable_status = "available" if validation_ok and simulation_ok else "review_required"
            if not request.generated_ptag or request.normalized_spec is None:
                callable_status = "restricted"
            notes = []
            if request.pt_oss_assessment:
                notes = [item.message for item in request.pt_oss_assessment.blockers[:2]]
            entries.append(
                CallableDirectoryEntry(
                    entry_id=f"studio:{request.request_id}",
                    source="studio_draft",
                    role_id=role_id,
                    display_name=request.structured_jd.role_name or role_id,
                    business_domain=request.structured_jd.business_domain or (request.normalized_spec.domain if request.normalized_spec else None),
                    callable=callable_status != "restricted",
                    callable_status=callable_status,
                    active_hat=role_id,
                    escalation_owner=request.normalized_spec.reports_to if request.normalized_spec else request.structured_jd.reporting_line,
                    safety_owner=self._extract_safety_owner(request),
                    publication_status=request.status,
                    pt_oss_posture=posture,
                    pt_oss_readiness_score=readiness_score,
                    operating_mode="direct",
                    executive_owner_id=self._effective_request_executive_owner_id(request),
                    notes=notes,
                    summary=self._studio_entry_summary(request, callable_status),
                    metadata={
                        "studio_request_id": request.request_id,
                        "validation_blocked": request.validation_report.blocked_publish if request.validation_report else True,
                        "simulation_status": request.simulation_report.status if request.simulation_report else "not_run",
                        "ptag_source_mode": request.ptag_source_mode,
                        "operating_mode": "direct",
                        "executive_owner_id": self._effective_request_executive_owner_id(request),
                    },
                )
            )

        return entries

    def _resolve_target_entry(self, payload: dict[str, object]) -> CallableDirectoryEntry:
        directory = self._build_callable_directory()
        entry_by_id = {item.entry_id: item for item in directory}
        target_entry_id = str(payload.get("directory_entry_id") or "").strip()
        studio_request_id = str(payload.get("studio_request_id") or "").strip()
        role_id = str(payload.get("role_id") or "").strip().upper()

        if target_entry_id:
            entry = entry_by_id.get(target_entry_id)
            if entry is None:
                raise ValueError(f"Human Ask target not found: {target_entry_id}")
            return entry

        if studio_request_id:
            entry = entry_by_id.get(f"studio:{studio_request_id}")
            if entry is None:
                raise ValueError(f"Human Ask Studio draft not found: {studio_request_id}")
            return entry

        if role_id:
            candidates = [item for item in directory if item.role_id == role_id and item.source == "published_role"]
            if not candidates:
                raise ValueError(f"Human Ask role target not found: {role_id}")
            return candidates[0]

        raise ValueError("Human Ask target is required.")

    def _build_context_chain(self, *, parent_session_id: str | None, inheritance_mode: str) -> AskContextChain:
        if not parent_session_id:
            return AskContextChain(parent_session_id=None, inheritance_mode="reset")
        parent = self.store.get_session(parent_session_id)
        if inheritance_mode not in {"inherit", "trim", "reset"}:
            inheritance_mode = "inherit"
        inherited_summary = ""
        inherited_ids: list[str] = []
        if inheritance_mode != "reset":
            inherited_summary = parent.transcript_summary
            inherited_ids = [parent.session_id, *parent.context_chain.inherited_session_ids]
        return AskContextChain(
            parent_session_id=parent.session_id,
            inheritance_mode=inheritance_mode,
            inherited_session_ids=inherited_ids,
            inherited_summary=inherited_summary,
        )

    def _build_decision_summary(self, *, prompt: str, entry: CallableDirectoryEntry, metadata: dict[str, object]) -> AskDecisionSummary:
        scope_assessment = self._scope_assessment(prompt, entry)
        risk_score = self._risk_score(prompt, entry)
        confidence_score = self._confidence_score(prompt, entry, risk_score)
        confidence_gap = round(confidence_score - self.confidence_threshold, 4)
        confidence_band = self._confidence_band(confidence_score)
        structural_gate = self._pt_oss_structural_gate(entry)
        automation_state = self._automation_state(
            entry=entry,
            confidence_score=confidence_score,
            risk_score=risk_score,
            scope_assessment=scope_assessment,
            structural_gate=structural_gate,
        )
        structural_posture = entry.pt_oss_posture or "unknown"
        recommendations = self._recommendations(
            entry=entry,
            automation_state=automation_state,
            risk_score=risk_score,
            scope_assessment=scope_assessment,
            structural_gate=structural_gate,
        )
        policy_basis = "human_ask.phase_a.report"
        escalated = False
        escalated_to = None
        escalation_reason = None
        outcome = "completed"
        notes: list[str] = []

        if automation_state == "blocked":
            outcome = "blocked"
            policy_basis = "human_ask.phase_a.structural_gate" if structural_gate["gate"] == "blocked" else "human_ask.phase_a.callable_boundary"
            notes.append(structural_gate["reason"] if structural_gate["gate"] == "blocked" else "The target is not callable in its current state.")
        elif automation_state == "review":
            escalated = True
            escalated_to = entry.safety_owner or entry.escalation_owner or entry.executive_owner_id or self.config.executive_owner_id()
            escalation_reason = self._escalation_reason(entry, risk_score, confidence_score, scope_assessment, structural_gate)
            outcome = "waiting_human"
            if scope_assessment["status"] in {"out_of_scope", "human_only_boundary"}:
                policy_basis = "human_ask.phase_a.scope_boundary"
            elif confidence_score < self.confidence_threshold:
                policy_basis = "human_ask.phase_a.confidence_guard"
            else:
                policy_basis = "human_ask.phase_a.structural_review"
            notes.append(escalation_reason)
        elif structural_gate["gate"] == "guarded":
            notes.append(structural_gate["reason"])
        elif risk_score >= 0.85 and confidence_score < max(self.confidence_threshold - 0.20, 0.40):
            notes.append(
                f"Automation continued within scope despite elevated risk {risk_score:.2f}; monitor follow-up lanes."
            )

        if metadata.get("force_human_review") is True and not escalated:
            escalated = True
            outcome = "waiting_human"
            escalated_to = entry.safety_owner or entry.escalation_owner or entry.executive_owner_id or self.config.executive_owner_id()
            escalation_reason = "Human Ask request was manually forced into human review."
            policy_basis = "human_ask.phase_a.manual_review"
            notes.append(escalation_reason)

        return AskDecisionSummary(
            outcome=outcome,
            confidence_score=confidence_score,
            confidence_threshold=self.confidence_threshold,
            automation_state=automation_state,
            risk_score=risk_score,
            structural_posture=structural_posture,
            policy_basis=policy_basis,
            escalated=escalated,
            escalated_to=escalated_to,
            escalation_reason=escalation_reason,
            recommendations=recommendations,
            notes=notes,
            metadata={
                "entry_id": entry.entry_id,
                "entry_source": entry.source,
                "publication_status": entry.publication_status,
                "mode": self._normalize_mode(str(metadata.get("mode", "report") or "report")) if metadata else "report",
                "scope_status": scope_assessment["status"],
                "scope_reason": scope_assessment["reason"],
                "matched_allowed_actions": scope_assessment["matched_allowed_actions"],
                "matched_required_human_actions": scope_assessment["matched_required_human_actions"],
                "matched_resources": scope_assessment["matched_resources"],
                "matched_sensitive_terms": scope_assessment["matched_sensitive_terms"],
                "automation_ready": scope_assessment["automation_ready"],
                "confidence_gap": confidence_gap,
                "confidence_band": confidence_band,
                "confidence_guard_triggered": confidence_score < self.confidence_threshold,
                "pt_oss_gate": structural_gate["gate"],
                "pt_oss_gate_reason": structural_gate["reason"],
                "pt_oss_readiness_score": entry.pt_oss_readiness_score,
            },
        )

    def _build_decision_queue(
        self,
        *,
        entry: CallableDirectoryEntry,
        decision_summary: AskDecisionSummary,
        metadata: dict[str, object],
    ) -> dict[str, object]:
        execution_plan = metadata.get("execution_plan") if isinstance(metadata.get("execution_plan"), dict) else {}
        queue_lane = self._decision_queue_lane(decision_summary)
        queue_state = self._decision_queue_state(decision_summary, queue_lane)
        priority = self._decision_queue_priority(decision_summary, metadata)
        human_required = queue_lane in {"human_review", "clearance"}
        queue_owner = decision_summary.escalated_to if decision_summary.escalated else None
        return {
            "queue_id": f"dq_{uuid4().hex[:10]}",
            "queue_lane": queue_lane,
            "queue_state": queue_state,
            "priority": priority,
            "human_required": human_required,
            "queue_owner": queue_owner,
            "automation_state": decision_summary.automation_state,
            "policy_basis": decision_summary.policy_basis,
            "queue_reason": decision_summary.escalation_reason or (decision_summary.notes[0] if decision_summary.notes else "Autonomy can continue inside governed boundaries."),
            "execution_plan": {
                "plan_id": str(execution_plan.get("plan_id", "")),
                "step_id": str(execution_plan.get("step_id", "")),
                "previous_step_id": str(execution_plan.get("previous_step_id", "")),
                "handoff_target_role": str(execution_plan.get("handoff_target_role", "")),
            },
            "correlation": {
                "origin_request_id": str(metadata.get("origin_request_id", metadata.get("request_id", ""))),
                "parent_session_id": str(metadata.get("parent_session_id", "")),
            },
        }

    def _decision_queue_lane(self, decision_summary: AskDecisionSummary) -> str:
        if decision_summary.outcome == "blocked":
            return "clearance"
        if decision_summary.outcome in {"waiting_human", "escalated"} or decision_summary.escalated:
            return "human_review"
        if str(decision_summary.metadata.get("pt_oss_gate", "clear")) in {"guarded", "watch"}:
            return "guarded_follow_up"
        return "autonomy"

    def _decision_queue_state(self, decision_summary: AskDecisionSummary, queue_lane: str) -> str:
        if queue_lane == "clearance":
            return "blocked"
        if queue_lane == "human_review":
            return "queued_human_review"
        if queue_lane == "guarded_follow_up":
            return "queued_guarded_follow_up"
        return "ready_for_autonomy"

    def _decision_queue_priority(self, decision_summary: AskDecisionSummary, metadata: dict[str, object]) -> str:
        if metadata.get("force_human_review") is True or decision_summary.outcome == "blocked":
            return "critical"
        if decision_summary.risk_score >= 0.85 or decision_summary.outcome in {"waiting_human", "escalated"}:
            return "high"
        if str(decision_summary.metadata.get("pt_oss_gate", "clear")) in {"guarded", "watch"}:
            return "medium"
        return "normal"

    def _build_human_decision_inbox(
        self,
        *,
        session_id: str,
        prompt: str,
        entry: CallableDirectoryEntry,
        decision_summary: AskDecisionSummary,
        decision_queue: dict[str, object],
        metadata: dict[str, object],
        director_disposition: str,
    ) -> HumanDecisionInboxContract:
        queue_lane = str(decision_queue.get("queue_lane", "autonomy"))
        if queue_lane == "clearance":
            inbox_state = "clearance_required"
        elif queue_lane == "human_review":
            inbox_state = "human_action_required"
        elif queue_lane == "guarded_follow_up":
            inbox_state = "guarded_follow_up"
        else:
            inbox_state = "autonomy_ready"

        required_action = self._inbox_required_action(queue_lane, decision_summary, metadata)
        operator_actions = self._inbox_operator_actions(queue_lane)
        task_packet = metadata.get("task_packet") if isinstance(metadata.get("task_packet"), dict) else {}
        origin_request_id = str(metadata.get("origin_request_id", metadata.get("request_id", "")))
        evidence_refs = [session_id]
        if origin_request_id:
            evidence_refs.append(origin_request_id)
        task_packet_id = str(task_packet.get("packet_id", ""))
        if task_packet_id:
            evidence_refs.append(task_packet_id)

        return HumanDecisionInboxContract(
            inbox_id=f"inbox_{session_id}",
            inbox_state=inbox_state,
            queue_lane=queue_lane,
            queue_state=str(decision_queue.get("queue_state", "ready_for_autonomy")),
            priority=str(decision_queue.get("priority", "normal")),
            human_required=bool(decision_queue.get("human_required", False)),
            required_action=required_action,
            queue_owner=str(decision_queue.get("queue_owner")) if decision_queue.get("queue_owner") else None,
            decision_context={
                "participant": entry.display_name,
                "role_id": entry.role_id,
                "prompt": prompt,
                "automation_state": decision_summary.automation_state,
                "policy_basis": decision_summary.policy_basis,
                "queue_reason": str(decision_queue.get("queue_reason", "")),
                "director_disposition": director_disposition,
                "confidence_score": decision_summary.confidence_score,
                "confidence_threshold": decision_summary.confidence_threshold,
                "confidence_gap": float(decision_summary.metadata.get("confidence_gap", 0.0) or 0.0),
                "confidence_band": str(decision_summary.metadata.get("confidence_band", "ready")),
                "risk_score": decision_summary.risk_score,
                "scope_status": str(decision_summary.metadata.get("scope_status", "unknown")),
                "scope_reason": str(decision_summary.metadata.get("scope_reason", "")),
            },
            authority={
                "escalated": decision_summary.escalated,
                "escalated_to": decision_summary.escalated_to,
                "escalation_reason": decision_summary.escalation_reason,
                "human_required": bool(decision_queue.get("human_required", False)),
            },
            execution_plan=dict(decision_queue.get("execution_plan", {})) if isinstance(decision_queue.get("execution_plan", {}), dict) else {},
            task_packet=dict(task_packet),
            correlation={
                "session_id": session_id,
                "origin_request_id": origin_request_id,
                "parent_session_id": str(metadata.get("parent_session_id", "")),
            },
            evidence_refs=evidence_refs,
            operator_actions=operator_actions,
        )

    def _inbox_required_action(
        self,
        queue_lane: str,
        decision_summary: AskDecisionSummary,
        metadata: dict[str, object],
    ) -> str:
        if queue_lane == "clearance":
            return "clearance_review"
        if queue_lane == "human_review":
            if metadata.get("force_human_review") is True:
                return "manual_review"
            if decision_summary.metadata.get("scope_status") == "human_only_boundary":
                return "human_decision"
            if decision_summary.metadata.get("confidence_band") == "below_threshold":
                return "confidence_review"
            return "approve_or_escalate"
        if queue_lane == "guarded_follow_up":
            return "guarded_follow_up"
        return "observe"

    def _inbox_operator_actions(self, queue_lane: str) -> list[str]:
        if queue_lane == "clearance":
            return ["clear", "request_follow_up", "escalate"]
        if queue_lane == "human_review":
            return ["approve", "request_follow_up", "escalate"]
        if queue_lane == "guarded_follow_up":
            return ["acknowledge", "request_follow_up"]
        return ["observe"]

    def _build_transcript(
        self,
        *,
        prompt: str,
        entry: CallableDirectoryEntry,
        entries: list[CallableDirectoryEntry],
        decision_summary: AskDecisionSummary,
        context_chain: AskContextChain,
        participant_decisions: list[AskParticipantDecision],
        meeting_overview: dict[str, object],
    ) -> list[AskExchange]:
        mode = str(decision_summary.metadata.get("mode", "report"))
        transcript = [
            AskExchange(
                exchange_id=f"hex_{uuid4().hex[:10]}",
                timestamp=utc_now(),
                speaker_type="human",
                speaker_id="human_requester",
                speaker_label="Human",
                message_type="prompt",
                content=prompt,
                metadata={"entry_id": entry.entry_id},
            ),
            AskExchange(
                exchange_id=f"hex_{uuid4().hex[:10]}",
                timestamp=utc_now(),
                speaker_type="system",
                speaker_id="human_ask_router",
                speaker_label="Human Ask Router",
                message_type="resolution",
                content=self._resolution_message(entry, decision_summary, context_chain),
                metadata={
                    "automation_state": decision_summary.automation_state,
                    "confidence_score": decision_summary.confidence_score,
                    "risk_score": decision_summary.risk_score,
                    "mode": decision_summary.metadata.get("mode", "report"),
                },
            ),
        ]
        if mode == "meeting":
            transcript.append(
                AskExchange(
                    exchange_id=f"hex_{uuid4().hex[:10]}",
                    timestamp=utc_now(),
                    speaker_type="system",
                    speaker_id="director_meeting_brief",
                    speaker_label="Director Meeting Brief",
                    message_type="meeting_brief",
                    content=self._meeting_brief_message(entries, context_chain),
                    metadata={
                        "mode": mode,
                        "participant_total": len(entries),
                        "participant_roles": [item.role_id for item in entries],
                    },
                )
            )
        transcript.extend(
            [
                AskExchange(
                exchange_id=f"hex_{uuid4().hex[:10]}",
                timestamp=utc_now(),
                speaker_type="system",
                speaker_id="director_hat_brief",
                speaker_label="Director Hat Brief",
                message_type="hat_brief",
                content=self._hat_brief_message(entry, context_chain),
                metadata={
                    "active_hat": entry.role_id,
                    "source": entry.source,
                    "publication_status": entry.publication_status,
                },
            ),
            AskExchange(
                exchange_id=f"hex_{uuid4().hex[:10]}",
                timestamp=utc_now(),
                speaker_type="ai",
                speaker_id=entry.role_id,
                speaker_label=entry.display_name,
                message_type="response",
                content=self._response_message(entry, decision_summary, prompt, str(decision_summary.metadata.get("mode", "report"))),
                metadata={
                    "business_domain": entry.business_domain,
                    "escalated_to": decision_summary.escalated_to,
                    "policy_basis": decision_summary.policy_basis,
                    "mode": decision_summary.metadata.get("mode", "report"),
                },
            ),
            ]
        )
        if mode == "meeting":
            for participant_entry in entries[1:]:
                transcript.append(
                    AskExchange(
                        exchange_id=f"hex_{uuid4().hex[:10]}",
                        timestamp=utc_now(),
                        speaker_type="ai",
                        speaker_id=participant_entry.role_id,
                        speaker_label=participant_entry.display_name,
                        message_type="response",
                        content=self._meeting_participant_response(participant_entry, prompt, decision_summary),
                        metadata={
                            "business_domain": participant_entry.business_domain,
                            "mode": mode,
                        },
                    )
                )
            for participant_decision in participant_decisions:
                transcript.append(
                    AskExchange(
                        exchange_id=f"hex_{uuid4().hex[:10]}",
                        timestamp=utc_now(),
                        speaker_type="system",
                        speaker_id=f"director_decision_{participant_decision.role_id.lower()}",
                        speaker_label="Director Decision Lane",
                        message_type="decision_block",
                        content=self._participant_decision_message(participant_decision),
                        metadata={
                            "mode": mode,
                            "role_id": participant_decision.role_id,
                            "decision_status": participant_decision.decision_status,
                            "primary": participant_decision.primary,
                        },
                    )
                )
            transcript.append(
                AskExchange(
                    exchange_id=f"hex_{uuid4().hex[:10]}",
                    timestamp=utc_now(),
                    speaker_type="system",
                    speaker_id="director_meeting_synthesis",
                    speaker_label="Director Meeting Synthesis",
                    message_type="synthesis",
                    content=self._meeting_synthesis(entries, prompt, decision_summary, participant_decisions, meeting_overview),
                    metadata={
                        "mode": mode,
                        "participant_total": len(entries),
                        "meeting_overview": meeting_overview,
                    },
                )
            )
        return transcript

    def _build_action_items(
        self,
        *,
        entry: CallableDirectoryEntry,
        entries: list[CallableDirectoryEntry],
        decision_summary: AskDecisionSummary,
        participant_decisions: list[AskParticipantDecision],
    ) -> list[AskActionItem]:
        items: list[AskActionItem] = []
        mode = str(decision_summary.metadata.get("mode", "report"))
        if decision_summary.escalated and decision_summary.escalated_to:
            items.append(
                AskActionItem(
                    action_item_id=f"hai_{uuid4().hex[:10]}",
                    title=f"Review Human Ask {self._mode_label(mode).lower()} boundary for {entry.display_name}",
                    owner_role=decision_summary.escalated_to,
                    note=decision_summary.escalation_reason or "Human Ask paused because this request crossed a human boundary.",
                )
            )
        if entry.source == "studio_draft":
            items.append(
                AskActionItem(
                    action_item_id=f"hai_{uuid4().hex[:10]}",
                    title=f"Attach Human Ask record back to Role Private Studio draft {entry.metadata.get('studio_request_id', '-')}",
                    owner_role=entry.escalation_owner,
                    note="Use the Human Ask record to refine the draft or confirm it is ready for review.",
                )
            )
        if mode == "report" and decision_summary.outcome == "completed":
            items.append(
                AskActionItem(
                    action_item_id=f"hai_{uuid4().hex[:10]}",
                    title=f"Capture governed report record from {entry.display_name}",
                    owner_role=entry.role_id,
                    note="Preserve the governed report for follow-up review, evidence, or meeting preparation.",
                )
            )
        if mode == "meeting" and decision_summary.outcome == "completed":
            items.append(
                AskActionItem(
                    action_item_id=f"hai_{uuid4().hex[:10]}",
                    title=f"Capture meeting record across {len(entries)} hats",
                    owner_role=entry.escalation_owner or entry.role_id,
                    note="Preserve the meeting synthesis and participant lanes as the formal meeting record.",
                )
            )
            for participant_decision in participant_decisions:
                if participant_decision.decision_status == "ready":
                    continue
                items.append(
                    AskActionItem(
                        action_item_id=f"hai_{uuid4().hex[:10]}",
                        title=f"Resolve {participant_decision.role_id} decision lane before acting on meeting output",
                        owner_role=participant_decision.escalation_owner or participant_decision.role_id,
                        note=participant_decision.next_safe_action or "This consulted hat still needs governed review.",
                    )
                )
        if not items and decision_summary.outcome == "completed":
            items.append(
                AskActionItem(
                    action_item_id=f"hai_{uuid4().hex[:10]}",
                    title=f"Preserve governed {self._mode_label(mode).lower()} record for {entry.display_name}",
                    owner_role=entry.role_id,
                    note="This record is ready for follow-up reporting with inherited context.",
                )
            )
        return items

    def _build_participant_summaries(
        self,
        *,
        entries: list[CallableDirectoryEntry],
        decision_summary: AskDecisionSummary,
        prompt: str,
    ) -> list[AskParticipantSummary]:
        mode = str(decision_summary.metadata.get("mode", "report"))
        return [
            AskParticipantSummary(
                participant_id=f"ps_{uuid4().hex[:10]}",
                role_id=entry.role_id,
                display_name=entry.display_name,
                source=entry.source,
                business_domain=entry.business_domain,
                callable_status=entry.callable_status,
                pt_oss_posture=entry.pt_oss_posture,
                pt_oss_readiness_score=entry.pt_oss_readiness_score,
                action_focus=self._action_focus(entry),
                required_human_actions=self._required_human_actions(entry),
                handled_resources=self._handled_resources(entry),
                contribution_summary=self._participant_contribution_summary(
                    entry=entry,
                    decision_summary=decision_summary,
                    prompt=prompt,
                    mode=mode,
                    primary=index == 0,
                ),
                escalation_owner=entry.escalation_owner,
                safety_owner=entry.safety_owner,
                publication_status=entry.publication_status,
                primary=index == 0,
                metadata={
                    "mode": mode,
                    "callable": entry.callable,
                    "notes": list(entry.notes),
                },
            )
            for index, entry in enumerate(entries)
        ]

    def _build_participant_decisions(
        self,
        *,
        entries: list[CallableDirectoryEntry],
        decision_summary: AskDecisionSummary,
        prompt: str,
    ) -> list[AskParticipantDecision]:
        mode = str(decision_summary.metadata.get("mode", "report"))
        return [
            self._participant_decision_block(
                entry=entry,
                decision_summary=decision_summary,
                prompt=prompt,
                mode=mode,
                primary=index == 0,
            )
            for index, entry in enumerate(entries)
        ]

    def _build_transcript_summary(
        self,
        entry: CallableDirectoryEntry,
        entries: list[CallableDirectoryEntry],
        decision_summary: AskDecisionSummary,
        participant_decisions: list[AskParticipantDecision],
    ) -> str:
        return build_transcript_summary(
            entry=entry,
            entries=entries,
            decision_summary=decision_summary,
            participant_decisions=participant_decisions,
            mode=str(decision_summary.metadata.get("mode", "report")),
        )

    def _participant_from_entry(self, entry: CallableDirectoryEntry) -> AskParticipant:
        return AskParticipant(
            participant_id=f"participant_{uuid4().hex[:10]}",
            entry_id=entry.entry_id,
            source=entry.source,
            role_id=entry.role_id,
            display_name=entry.display_name,
            business_domain=entry.business_domain,
            callable_status=entry.callable_status,
            callable=entry.callable,
            escalation_owner=entry.escalation_owner,
            safety_owner=entry.safety_owner,
            pt_oss_posture=entry.pt_oss_posture,
            pt_oss_readiness_score=entry.pt_oss_readiness_score,
            publication_status=entry.publication_status,
            operating_mode=entry.operating_mode,
            assigned_user_id=entry.assigned_user_id,
            executive_owner_id=entry.executive_owner_id,
            seat_id=entry.seat_id,
            notes=list(entry.notes),
            metadata=dict(entry.metadata),
        )

    def _assess_runtime_role(self, entry: HierarchyEntry) -> PTOSSAssessment:
        domain = entry.business_domain or ""
        sensitivity = "high" if domain in self.SAFETY_DOMAINS or "legal" in domain or "compliance" in domain else "medium"
        structured_jd = StructuredJD(
            role_name=entry.title or entry.role_id,
            purpose=f"Published runtime role {entry.role_id} callable through Human Ask.",
            reporting_line=entry.reports_to or entry.executive_owner_id or self.config.executive_owner_id(),
            business_domain=domain,
            responsibilities=sorted(entry.allowed_actions)[:6],
            allowed_actions=sorted(entry.allowed_actions),
            forbidden_actions=sorted(entry.denied_actions),
            wait_human_actions=sorted(entry.required_human_actions),
            handled_resources=sorted(entry.handled_resources),
            financial_sensitivity=sensitivity,
            legal_sensitivity=sensitivity,
            compliance_sensitivity="high" if domain in self.SAFETY_DOMAINS else sensitivity,
            sample_scenarios=["human ask report request"],
            operator_notes="Runtime PT-OSS posture synthesized for Human Ask.",
        )
        normalized_spec = NormalizedRoleSpec(
            role_id=entry.role_id,
            title=entry.title,
            purpose=structured_jd.purpose,
            reports_to=entry.reports_to or entry.executive_owner_id or self.config.executive_owner_id(),
            domain=domain,
            operating_mode=entry.operating_mode,
            assigned_user_id=entry.assigned_user_id or "",
            executive_owner_id=entry.executive_owner_id or self.config.executive_owner_id(),
            seat_id=entry.seat_id or "",
            responsibilities=structured_jd.responsibilities,
            allowed_actions=structured_jd.allowed_actions,
            forbidden_actions=structured_jd.forbidden_actions,
            wait_human_actions=structured_jd.wait_human_actions,
            auto_wait_human_actions=[],
            handled_resources=structured_jd.handled_resources,
            sensitivity_profile={
                "financial": structured_jd.financial_sensitivity,
                "legal": structured_jd.legal_sensitivity,
                "compliance": structured_jd.compliance_sensitivity,
            },
            risk_threshold=0.6,
            ambiguity_notes=[],
            risk_flags=[],
        )
        validation_report = ValidationReport(
            report_id=f"human_ask_{entry.role_id.lower()}",
            syntax_passed=True,
            semantic_passed=True,
            blocked_publish=False,
            generated_at=utc_now(),
            findings=[],
            coverage_gaps=[],
        )
        simulation_report = SimulationReport(
            report_id=f"human_ask_{entry.role_id.lower()}",
            generated_at=utc_now(),
            scenario_results=[],
            status="passed",
        )
        ptag_snapshot = "\n".join(
            [
                f"reports_to: {entry.reports_to or entry.executive_owner_id or self.config.executive_owner_id()}",
                f"escalation_to: {entry.escalation_to or entry.executive_owner_id or self.config.executive_owner_id()}",
                f"safety_owner: {entry.safety_owner or entry.escalation_to or entry.executive_owner_id or self.config.executive_owner_id()}",
            ]
        )
        return self.pt_oss_engine.assess_role_draft(
            structured_jd=structured_jd,
            normalized_spec=normalized_spec,
            validation_report=validation_report,
            simulation_report=simulation_report,
            current_ptag=ptag_snapshot,
            generated_ptag=ptag_snapshot,
        )

    def _scope_assessment(self, prompt: str, entry: CallableDirectoryEntry) -> dict[str, object]:
        return assess_prompt_scope(prompt, entry, self.HIGH_RISK_TERMS)

    def _risk_score(self, prompt: str, entry: CallableDirectoryEntry) -> float:
        score = 0.18
        prompt_tokens = prompt.lower()
        for token, weight in self.HIGH_RISK_TERMS.items():
            if token in prompt_tokens:
                score += weight
        if entry.source == "studio_draft":
            score += 0.08
        if entry.callable_status in {"busy", "under_override"}:
            score += 0.12
        if entry.callable_status == "restricted":
            score += 0.18
        if (entry.business_domain or "").lower() in self.SAFETY_DOMAINS:
            score += 0.16
        if entry.pt_oss_posture in {"critical", "fragile"}:
            score += 0.14
        elif entry.pt_oss_posture == "watch":
            score += 0.08
        if entry.pt_oss_readiness_score < 50:
            score += 0.12
        elif entry.pt_oss_readiness_score < 70:
            score += 0.06
        return max(0.05, min(score, 0.99))

    def _confidence_score(self, prompt: str, entry: CallableDirectoryEntry, risk_score: float) -> float:
        confidence = 0.92
        if entry.source == "studio_draft":
            confidence -= 0.16
        if entry.callable_status == "busy":
            confidence -= 0.08
        if entry.callable_status == "under_override":
            confidence -= 0.18
        if entry.callable_status == "restricted":
            confidence -= 0.30
        if entry.pt_oss_posture in {"critical", "fragile"}:
            confidence -= 0.18
        elif entry.pt_oss_posture == "watch":
            confidence -= 0.08
        if entry.pt_oss_readiness_score < 50:
            confidence -= 0.12
        elif entry.pt_oss_readiness_score < 70:
            confidence -= 0.06
        if risk_score >= 0.70:
            confidence -= 0.10
        if len(prompt.strip()) < 14:
            confidence -= 0.05
        return max(0.05, min(confidence, 0.99))

    def _pt_oss_structural_gate(self, entry: CallableDirectoryEntry) -> dict[str, str]:
        posture = (entry.pt_oss_posture or "unknown").lower()
        readiness = int(entry.pt_oss_readiness_score or 0)
        if posture == "critical" or readiness < 42:
            return {
                "gate": "blocked",
                "reason": "PT-OSS structural gate is blocking automation because this hat is too structurally fragile for safe runtime continuation.",
            }
        if posture in {"elevated", "fragile"} or readiness < 60:
            return {
                "gate": "guarded",
                "reason": "PT-OSS structural gate is forcing guarded execution. Keep this record bounded and avoid expanding authority.",
            }
        if posture == "watch" or readiness < 72:
            return {
                "gate": "watch",
                "reason": "PT-OSS structural posture is watchful. Automation may continue, but the Director should preserve a guarded record trail.",
            }
        return {
            "gate": "clear",
            "reason": "PT-OSS structural posture allows bounded automation for this record.",
        }

    def _automation_state(
        self,
        *,
        entry: CallableDirectoryEntry,
        confidence_score: float,
        risk_score: float,
        scope_assessment: dict[str, object],
        structural_gate: dict[str, str],
    ) -> str:
        if not entry.callable or entry.callable_status == "restricted":
            return "blocked"
        if structural_gate["gate"] == "blocked":
            return "blocked"
        if scope_assessment["status"] in {"out_of_scope", "human_only_boundary"}:
            return "review"
        if confidence_score < self.confidence_threshold:
            return "review"
        if structural_gate["gate"] == "guarded" and risk_score >= 0.78 and confidence_score < self.confidence_threshold:
            return "review"
        return "clear"

    def _recommendations(
        self,
        *,
        entry: CallableDirectoryEntry,
        automation_state: str,
        risk_score: float,
        scope_assessment: dict[str, object],
        structural_gate: dict[str, str],
    ) -> list[str]:
        recommendations: list[str] = []
        if entry.source == "studio_draft":
            recommendations.append("Use this Human Ask record to refine the draft before publication.")
        if scope_assessment["status"] == "human_only_boundary":
            recommendations.append("Route the human-only action to the configured owner and let the Director handle the rest.")
        elif scope_assessment["status"] == "out_of_scope":
            recommendations.append("Pause automation and ask a human to decide because the request sits outside the loaded JD scope.")
        else:
            recommendations.append("Keep automation inside allowed actions and handled resources for this hat.")
        if structural_gate["gate"] in {"guarded", "watch"}:
            recommendations.append(structural_gate["reason"])
        if entry.pt_oss_posture in {"critical", "elevated", "fragile"}:
            recommendations.append("Reduce structural concentration before using this hat in broader automation chains.")
        if risk_score >= 0.70:
            recommendations.append("Use guarded automation for this lane and avoid stepping outside the current hat boundaries.")
        if automation_state == "blocked":
            recommendations.append("Do not continue automation until callable and structural posture return to a safe state.")
        return recommendations

    def _escalation_reason(
        self,
        entry: CallableDirectoryEntry,
        risk_score: float,
        confidence_score: float,
        scope_assessment: dict[str, object],
        structural_gate: dict[str, str],
    ) -> str:
        if scope_assessment["status"] == "human_only_boundary":
            actions = ", ".join(str(item) for item in scope_assessment["matched_required_human_actions"]) or "human-only actions"
            return f"The request reached {actions} for {entry.display_name}, which stays reserved for human decision."
        if scope_assessment["status"] == "out_of_scope":
            return f"The request is outside the loaded JD scope for {entry.display_name}: {scope_assessment['reason']}"
        if structural_gate["gate"] == "guarded":
            return structural_gate["reason"]
        if confidence_score < self.confidence_threshold:
            return f"Confidence {confidence_score:.2f} fell below threshold {self.confidence_threshold:.2f} outside clear scope alignment."
        return f"Risk score {risk_score:.2f} crossed the automation boundary outside the loaded JD scope."

    def _resolution_message(self, entry: CallableDirectoryEntry, decision_summary: AskDecisionSummary, context_chain: AskContextChain) -> str:
        mode = str(decision_summary.metadata.get("mode", "report"))
        scope_status = str(decision_summary.metadata.get("scope_status", "in_scope"))
        inherited = ""
        if context_chain.parent_session_id and context_chain.inheritance_mode != "reset":
            inherited = f" Inherited context from {context_chain.parent_session_id} using mode {context_chain.inheritance_mode}."
        return (
            f"Resolved Human Ask {self._mode_label(mode).lower()} target to {entry.display_name} ({entry.role_id}) from {entry.source}."
            f" Callable status is {entry.callable_status}; PT-OSS posture is {entry.pt_oss_posture}; "
            f"automation state is {decision_summary.automation_state}; confidence is {decision_summary.confidence_score:.2f};"
            f" scope status is {scope_status}."
            f"{inherited}"
        )

    def _response_message(self, entry: CallableDirectoryEntry, decision_summary: AskDecisionSummary, prompt: str, mode: str) -> str:
        return build_response_message(entry, decision_summary, prompt, mode)

    def _hat_brief_message(self, entry: CallableDirectoryEntry, context_chain: AskContextChain) -> str:
        allowed_actions = entry.metadata.get("allowed_actions", [])
        required_human_actions = entry.metadata.get("required_human_actions", [])
        handled_resources = entry.metadata.get("handled_resources", [])
        action_preview = ", ".join(str(item) for item in allowed_actions[:3]) or "governed role actions"
        resource_preview = ", ".join(str(item) for item in handled_resources[:3]) or "governed resources"
        review_note = ""
        if required_human_actions:
            review_note = (
                " Human review is required for actions such as "
                f"{', '.join(str(item) for item in required_human_actions[:3])}."
            )
        studio_note = ""
        if entry.source == "studio_draft":
            studio_note = (
                f" This hat comes from a studio draft in status {entry.publication_status}"
                " and should be treated as a governed test posture."
            )
        inherited_note = ""
        if context_chain.parent_session_id and context_chain.inheritance_mode != "reset":
            inherited_note = (
                f" Inherited context from {context_chain.parent_session_id}"
                f" using {context_chain.inheritance_mode} mode."
            )
            if context_chain.inherited_summary:
                inherited_note += f" Prior summary: {context_chain.inherited_summary}"
        return (
            f"AI Director has selected hat {entry.role_id} ({entry.display_name})."
            f" Primary action focus includes {action_preview}."
            f" Managed resources include {resource_preview}."
            f" Callable status is {entry.callable_status}; PT-OSS posture is {entry.pt_oss_posture}."
            f"{review_note}{studio_note}{inherited_note}"
        )

    def _meeting_brief_message(self, entries: list[CallableDirectoryEntry], context_chain: AskContextChain) -> str:
        participant_summary = ", ".join(f"{item.role_id} ({item.display_name})" for item in entries)
        inherited_note = ""
        if context_chain.parent_session_id and context_chain.inheritance_mode != "reset":
            inherited_note = (
                f" Inherited context from {context_chain.parent_session_id}"
                f" using {context_chain.inheritance_mode} mode."
            )
        return (
            f"AI Director has opened a governed meeting across {len(entries)} hats:"
            f" {participant_summary}.{inherited_note}"
        )

    def _meeting_participant_response(
        self,
        entry: CallableDirectoryEntry,
        prompt: str,
        decision_summary: AskDecisionSummary,
    ) -> str:
        contribution_summary = self._participant_contribution_summary(
            entry=entry,
            decision_summary=decision_summary,
            prompt=prompt,
            mode="meeting",
            primary=False,
        )
        return (
            f"AI Director is also consulting hat {entry.role_id} ({entry.display_name})"
            f" on '{prompt}'. {contribution_summary}"
        )

    def _meeting_synthesis(
        self,
        entries: list[CallableDirectoryEntry],
        prompt: str,
        decision_summary: AskDecisionSummary,
        participant_decisions: list[AskParticipantDecision],
        meeting_overview: dict[str, object],
    ) -> str:
        _ = participant_decisions
        return build_meeting_synthesis(entries, prompt, decision_summary, meeting_overview)

    def _participant_payload(self, entry: CallableDirectoryEntry) -> dict[str, object]:
        return {
            "entry_id": entry.entry_id,
            "role_id": entry.role_id,
            "display_name": entry.display_name,
            "source": entry.source,
            "callable_status": entry.callable_status,
            "business_domain": entry.business_domain,
            "operating_mode": entry.operating_mode,
            "assigned_user_id": entry.assigned_user_id,
            "executive_owner_id": entry.executive_owner_id,
            "seat_id": entry.seat_id,
        }

    def _build_session_record(
        self,
        *,
        prompt: str,
        mode: str,
        participant_entry: CallableDirectoryEntry,
        participant_entries: list[CallableDirectoryEntry],
        decision_summary: AskDecisionSummary,
        meeting_overview: dict[str, object],
        participant_decisions: list[AskParticipantDecision],
    ) -> dict[str, object]:
        _ = participant_decisions
        return build_session_record(
            prompt=prompt,
            mode=mode,
            participant_entry=participant_entry,
            participant_entries=participant_entries,
            decision_summary=decision_summary,
            meeting_overview=meeting_overview,
        )

    def _participant_decision_block(
        self,
        *,
        entry: CallableDirectoryEntry,
        decision_summary: AskDecisionSummary,
        prompt: str,
        mode: str,
        primary: bool,
    ) -> AskParticipantDecision:
        participant_risk = self._risk_score(prompt, entry)
        participant_confidence = self._confidence_score(prompt, entry, participant_risk)
        scope_assessment = self._scope_assessment(prompt, entry)
        blockers = list(entry.notes)
        human_gate = scope_assessment["status"] == "human_only_boundary"
        decision_status = "ready"
        pt_oss_gate = str(decision_summary.metadata.get("pt_oss_gate", "clear"))
        if not entry.callable or entry.callable_status == "restricted" or decision_summary.automation_state == "blocked" or pt_oss_gate == "blocked":
            decision_status = "blocked"
            blockers.append("This hat is not callable in its current posture.")
        elif scope_assessment["status"] == "out_of_scope":
            decision_status = "blocked"
            blockers.append(scope_assessment["reason"])
        elif entry.callable_status in {"review_required", "under_override", "busy"} or human_gate or pt_oss_gate in {"guarded", "watch"}:
            decision_status = "guarded"
        elif participant_risk >= 0.85 and participant_confidence < max(self.confidence_threshold - 0.20, 0.40):
            decision_status = "guarded"
        next_safe_action = self._participant_next_safe_action(
            entry=entry,
            mode=mode,
            primary=primary,
            decision_status=decision_status,
        )
        return AskParticipantDecision(
            decision_id=f"pd_{uuid4().hex[:10]}",
            role_id=entry.role_id,
            display_name=entry.display_name,
            decision_status=decision_status,
            next_safe_action=next_safe_action,
            confidence_score=participant_confidence,
            risk_score=participant_risk,
            human_gate=human_gate,
            blockers=blockers,
            escalation_owner=entry.safety_owner or entry.escalation_owner,
            primary=primary,
            metadata={
                "mode": mode,
                "callable_status": entry.callable_status,
                "business_domain": entry.business_domain,
                "required_human_actions": self._required_human_actions(entry),
                "operating_mode": entry.operating_mode,
                "assigned_user_id": entry.assigned_user_id,
                "executive_owner_id": entry.executive_owner_id,
                "seat_id": entry.seat_id,
                "scope_status": scope_assessment["status"],
                "scope_reason": scope_assessment["reason"],
                "matched_allowed_actions": scope_assessment["matched_allowed_actions"],
                "matched_required_human_actions": scope_assessment["matched_required_human_actions"],
                "pt_oss_gate": pt_oss_gate,
            },
        )

    def _participant_next_safe_action(
        self,
        *,
        entry: CallableDirectoryEntry,
        mode: str,
        primary: bool,
        decision_status: str,
    ) -> str:
        return build_participant_next_safe_action(
            entry=entry,
            action_focus=self._action_focus(entry),
            required_human_actions=self._required_human_actions(entry),
            mode=mode,
            primary=primary,
            decision_status=decision_status,
        )

    def _participant_decision_message(self, participant_decision: AskParticipantDecision) -> str:
        blocker_text = ""
        if participant_decision.blockers:
            blocker_text = f" Blockers: {'; '.join(participant_decision.blockers[:2])}."
        return (
            f"Hat {participant_decision.role_id} is currently in {participant_decision.decision_status} decision status"
            f" with confidence {participant_decision.confidence_score:.2f} and risk {participant_decision.risk_score:.2f}."
            f" Next safe action: {participant_decision.next_safe_action}.{blocker_text}"
        )

    def _meeting_decision_overview(self, participant_decisions: list[AskParticipantDecision]) -> dict[str, object]:
        ready_roles = [item.role_id for item in participant_decisions if item.decision_status == "ready"]
        guarded_roles = [item.role_id for item in participant_decisions if item.decision_status == "guarded"]
        blocked_roles = [item.role_id for item in participant_decisions if item.decision_status == "blocked"]
        return {
            "ready_total": len(ready_roles),
            "guarded_total": len(guarded_roles),
            "blocked_total": len(blocked_roles),
            "human_gate_total": sum(1 for item in participant_decisions if item.human_gate),
            "ready_roles": ready_roles,
            "guarded_roles": guarded_roles,
            "blocked_roles": blocked_roles,
        }

    def _director_disposition(
        self,
        *,
        mode: str,
        decision_summary: AskDecisionSummary,
        meeting_overview: dict[str, object],
    ) -> str:
        if decision_summary.outcome == "blocked" or int(meeting_overview.get("blocked_total", 0)) > 0:
            return "hold_for_clearance"
        if (
            decision_summary.escalated
            or decision_summary.outcome in {"waiting_human", "escalated"}
            or str(decision_summary.metadata.get("pt_oss_gate", "clear")) in {"guarded", "watch"}
            or int(meeting_overview.get("guarded_total", 0)) > 0
        ):
            return "guarded_follow_up"
        return "ready_to_proceed"

    def _action_focus(self, entry: CallableDirectoryEntry) -> list[str]:
        return [str(item) for item in entry.metadata.get("allowed_actions", [])[:4]]

    def _required_human_actions(self, entry: CallableDirectoryEntry) -> list[str]:
        return [str(item) for item in entry.metadata.get("required_human_actions", [])[:4]]

    def _handled_resources(self, entry: CallableDirectoryEntry) -> list[str]:
        return [str(item) for item in entry.metadata.get("handled_resources", [])[:4]]

    def _participant_contribution_summary(
        self,
        *,
        entry: CallableDirectoryEntry,
        decision_summary: AskDecisionSummary,
        prompt: str,
        mode: str,
        primary: bool,
    ) -> str:
        return build_participant_contribution_summary(
            entry=entry,
            decision_summary=decision_summary,
            prompt=prompt,
            mode=mode,
            primary=primary,
            action_focus=self._action_focus(entry),
            handled_resources=self._handled_resources(entry),
        )

    def _normalize_mode(self, mode: str) -> str:
        normalized = mode.strip().lower()
        aliases = {
            "ask": "report",
            "single": "report",
            "single_target": "report",
            "direct_ask": "report",
            "command": "report",
            "report": "report",
            "meeting": "meeting",
            "studio_record": "report",
            "studio_report": "report",
        }
        return aliases.get(normalized, "report")

    def _mode_label(self, mode: str) -> str:
        return present_mode_label(mode)

    def _runtime_entry_summary(self, entry: HierarchyEntry, assessment: PTOSSAssessment, callable_status: str) -> str:
        assignment_note = (
            f"Indirect mode attached to {entry.assigned_user_id or 'an assigned human'}"
            if entry.operating_mode == "indirect"
            else f"Direct mode under executive owner {entry.executive_owner_id or self.config.executive_owner_id()}"
        )
        return (
            f"Published role {entry.role_id} is {callable_status} with PT-OSS posture {assessment.posture} "
            f"and escalation owner {entry.escalation_to or entry.executive_owner_id or self.config.executive_owner_id()}. {assignment_note}."
        )

    def _studio_entry_summary(self, request, callable_status: str) -> str:
        posture = request.pt_oss_assessment.posture if request.pt_oss_assessment else "unknown"
        return (
            f"Studio draft {request.request_id} is {callable_status} for governed record testing."
            f" Current publication status is {request.status} with PT-OSS posture {posture}."
            " Draft hats default to Direct mode until organizational assignment is defined."
        )

    def _extract_safety_owner(self, request) -> str | None:
        default_owner = self.config.executive_owner_id()
        if request.normalized_spec is None:
            return request.structured_jd.reporting_line or self._effective_request_executive_owner_id(request) or default_owner
        if request.ptag_override_source and "safety_owner:" in request.ptag_override_source:
            for line in request.ptag_override_source.splitlines():
                if line.strip().startswith("safety_owner:"):
                    value = line.split(":", 1)[1].strip()
                    if value:
                        return value
        if request.normalized_spec.operating_mode == "direct":
            return self._effective_request_executive_owner_id(request) or default_owner
        return request.normalized_spec.reports_to or request.structured_jd.reporting_line or self._effective_request_executive_owner_id(request) or default_owner

    def _effective_request_executive_owner_id(self, request) -> str:
        candidate = ''
        if request.normalized_spec is not None:
            candidate = str(request.normalized_spec.executive_owner_id or '').strip().upper()
        if not candidate:
            candidate = str(request.structured_jd.executive_owner_id or '').strip().upper()
        return normalize_executive_owner_id(
            candidate,
            fallback=self.config.executive_owner_id(),
        )

    def _audit(self, action: str, outcome: str, reason: str, metadata: dict[str, object]) -> None:
        self.audit_logger.record_event(
            active_role="HUMAN_ASK",
            action=action,
            outcome=outcome,
            reason=reason,
            metadata=metadata,
        )
