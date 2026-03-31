from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


_LEGACY_AUTOMATION_STATE_KEYS = ("summon" "_safety",)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class AskContextChain:
    parent_session_id: str | None = None
    inheritance_mode: str = "reset"
    inherited_session_ids: list[str] = field(default_factory=list)
    inherited_summary: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "AskContextChain":
        if not data:
            return cls()
        return cls(
            parent_session_id=str(data.get("parent_session_id")) if data.get("parent_session_id") else None,
            inheritance_mode=str(data.get("inheritance_mode", "reset") or "reset"),
            inherited_session_ids=[str(item) for item in data.get("inherited_session_ids", [])],
            inherited_summary=str(data.get("inherited_summary", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AskParticipant:
    participant_id: str
    entry_id: str
    source: str
    role_id: str
    display_name: str
    business_domain: str | None = None
    callable_status: str = "available"
    callable: bool = True
    escalation_owner: str | None = None
    safety_owner: str | None = None
    pt_oss_posture: str = "unknown"
    pt_oss_readiness_score: int = 0
    publication_status: str = "published"
    operating_mode: str = "direct"
    assigned_user_id: str | None = None
    executive_owner_id: str | None = None
    seat_id: str | None = None
    notes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AskParticipant":
        return cls(
            participant_id=str(data.get("participant_id", "")),
            entry_id=str(data.get("entry_id", "")),
            source=str(data.get("source", "published_role")),
            role_id=str(data.get("role_id", "")),
            display_name=str(data.get("display_name", "")),
            business_domain=str(data.get("business_domain")) if data.get("business_domain") else None,
            callable_status=str(data.get("callable_status", "available")),
            callable=bool(data.get("callable", True)),
            escalation_owner=str(data.get("escalation_owner")) if data.get("escalation_owner") else None,
            safety_owner=str(data.get("safety_owner")) if data.get("safety_owner") else None,
            pt_oss_posture=str(data.get("pt_oss_posture", "unknown")),
            pt_oss_readiness_score=int(data.get("pt_oss_readiness_score", 0)),
            publication_status=str(data.get("publication_status", "published")),
            operating_mode=str(data.get("operating_mode", "direct")),
            assigned_user_id=str(data.get("assigned_user_id")) if data.get("assigned_user_id") else None,
            executive_owner_id=str(data.get("executive_owner_id")) if data.get("executive_owner_id") else None,
            seat_id=str(data.get("seat_id")) if data.get("seat_id") else None,
            notes=[str(item) for item in data.get("notes", [])],
            metadata=data.get("metadata", {}) if isinstance(data.get("metadata", {}), dict) else {},
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CallableDirectoryEntry:
    entry_id: str
    source: str
    role_id: str
    display_name: str
    business_domain: str | None = None
    callable_status: str = "available"
    callable: bool = True
    active_hat: str | None = None
    escalation_owner: str | None = None
    safety_owner: str | None = None
    publication_status: str = "published"
    pt_oss_posture: str = "unknown"
    pt_oss_readiness_score: int = 0
    operating_mode: str = "direct"
    assigned_user_id: str | None = None
    executive_owner_id: str | None = None
    seat_id: str | None = None
    notes: list[str] = field(default_factory=list)
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CallableDirectoryEntry":
        return cls(
            entry_id=str(data.get("entry_id", "")),
            source=str(data.get("source", "published_role")),
            role_id=str(data.get("role_id", "")),
            display_name=str(data.get("display_name", "")),
            business_domain=str(data.get("business_domain")) if data.get("business_domain") else None,
            callable_status=str(data.get("callable_status", "available")),
            callable=bool(data.get("callable", True)),
            active_hat=str(data.get("active_hat")) if data.get("active_hat") else None,
            escalation_owner=str(data.get("escalation_owner")) if data.get("escalation_owner") else None,
            safety_owner=str(data.get("safety_owner")) if data.get("safety_owner") else None,
            publication_status=str(data.get("publication_status", "published")),
            pt_oss_posture=str(data.get("pt_oss_posture", "unknown")),
            pt_oss_readiness_score=int(data.get("pt_oss_readiness_score", 0)),
            operating_mode=str(data.get("operating_mode", "direct")),
            assigned_user_id=str(data.get("assigned_user_id")) if data.get("assigned_user_id") else None,
            executive_owner_id=str(data.get("executive_owner_id")) if data.get("executive_owner_id") else None,
            seat_id=str(data.get("seat_id")) if data.get("seat_id") else None,
            notes=[str(item) for item in data.get("notes", [])],
            summary=str(data.get("summary", "")),
            metadata=data.get("metadata", {}) if isinstance(data.get("metadata", {}), dict) else {},
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AskExchange:
    exchange_id: str
    timestamp: str
    speaker_type: str
    speaker_id: str
    speaker_label: str
    message_type: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AskExchange":
        return cls(
            exchange_id=str(data.get("exchange_id", "")),
            timestamp=str(data.get("timestamp", utc_now())),
            speaker_type=str(data.get("speaker_type", "system")),
            speaker_id=str(data.get("speaker_id", "")),
            speaker_label=str(data.get("speaker_label", "")),
            message_type=str(data.get("message_type", "note")),
            content=str(data.get("content", "")),
            metadata=data.get("metadata", {}) if isinstance(data.get("metadata", {}), dict) else {},
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AskActionItem:
    action_item_id: str
    title: str
    owner_role: str | None = None
    status: str = "open"
    note: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AskActionItem":
        return cls(
            action_item_id=str(data.get("action_item_id", "")),
            title=str(data.get("title", "")),
            owner_role=str(data.get("owner_role")) if data.get("owner_role") else None,
            status=str(data.get("status", "open")),
            note=str(data.get("note", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AskParticipantSummary:
    participant_id: str
    role_id: str
    display_name: str
    source: str = "published_role"
    business_domain: str | None = None
    callable_status: str = "available"
    pt_oss_posture: str = "unknown"
    pt_oss_readiness_score: int = 0
    action_focus: list[str] = field(default_factory=list)
    required_human_actions: list[str] = field(default_factory=list)
    handled_resources: list[str] = field(default_factory=list)
    contribution_summary: str = ""
    escalation_owner: str | None = None
    safety_owner: str | None = None
    publication_status: str = "published"
    primary: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AskParticipantSummary":
        return cls(
            participant_id=str(data.get("participant_id", "")),
            role_id=str(data.get("role_id", "")),
            display_name=str(data.get("display_name", "")),
            source=str(data.get("source", "published_role")),
            business_domain=str(data.get("business_domain")) if data.get("business_domain") else None,
            callable_status=str(data.get("callable_status", "available")),
            pt_oss_posture=str(data.get("pt_oss_posture", "unknown")),
            pt_oss_readiness_score=int(data.get("pt_oss_readiness_score", 0)),
            action_focus=[str(item) for item in data.get("action_focus", [])],
            required_human_actions=[str(item) for item in data.get("required_human_actions", [])],
            handled_resources=[str(item) for item in data.get("handled_resources", [])],
            contribution_summary=str(data.get("contribution_summary", "")),
            escalation_owner=str(data.get("escalation_owner")) if data.get("escalation_owner") else None,
            safety_owner=str(data.get("safety_owner")) if data.get("safety_owner") else None,
            publication_status=str(data.get("publication_status", "published")),
            primary=bool(data.get("primary", False)),
            metadata=data.get("metadata", {}) if isinstance(data.get("metadata", {}), dict) else {},
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AskParticipantDecision:
    decision_id: str
    role_id: str
    display_name: str
    decision_status: str = "ready"
    next_safe_action: str = ""
    confidence_score: float = 0.0
    risk_score: float = 0.0
    human_gate: bool = False
    blockers: list[str] = field(default_factory=list)
    escalation_owner: str | None = None
    primary: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AskParticipantDecision":
        return cls(
            decision_id=str(data.get("decision_id", "")),
            role_id=str(data.get("role_id", "")),
            display_name=str(data.get("display_name", "")),
            decision_status=str(data.get("decision_status", "ready")),
            next_safe_action=str(data.get("next_safe_action", "")),
            confidence_score=float(data.get("confidence_score", 0.0)),
            risk_score=float(data.get("risk_score", 0.0)),
            human_gate=bool(data.get("human_gate", False)),
            blockers=[str(item) for item in data.get("blockers", [])],
            escalation_owner=str(data.get("escalation_owner")) if data.get("escalation_owner") else None,
            primary=bool(data.get("primary", False)),
            metadata=data.get("metadata", {}) if isinstance(data.get("metadata", {}), dict) else {},
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["confidence_percent"] = round(self.confidence_score * 100, 1)
        payload["risk_percent"] = round(self.risk_score * 100, 1)
        return payload


@dataclass(slots=True)
class AskDecisionSummary:
    outcome: str
    confidence_score: float
    confidence_threshold: float
    automation_state: str
    risk_score: float
    structural_posture: str
    policy_basis: str | None = None
    escalated: bool = False
    escalated_to: str | None = None
    escalation_reason: str | None = None
    recommendations: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "AskDecisionSummary | None":
        if not data:
            return None
        automation_state = data.get("automation_state", "clear")
        if "automation_state" not in data:
            for key in _LEGACY_AUTOMATION_STATE_KEYS:
                if key in data:
                    automation_state = data.get(key, "clear")
                    break
        return cls(
            outcome=str(data.get("outcome", "completed")),
            confidence_score=float(data.get("confidence_score", 0.0)),
            confidence_threshold=float(data.get("confidence_threshold", 0.0)),
            automation_state=str(automation_state),
            risk_score=float(data.get("risk_score", 0.0)),
            structural_posture=str(data.get("structural_posture", "unknown")),
            policy_basis=str(data.get("policy_basis")) if data.get("policy_basis") else None,
            escalated=bool(data.get("escalated", False)),
            escalated_to=str(data.get("escalated_to")) if data.get("escalated_to") else None,
            escalation_reason=str(data.get("escalation_reason")) if data.get("escalation_reason") else None,
            recommendations=[str(item) for item in data.get("recommendations", [])],
            notes=[str(item) for item in data.get("notes", [])],
            metadata=data.get("metadata", {}) if isinstance(data.get("metadata", {}), dict) else {},
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["confidence_percent"] = round(self.confidence_score * 100, 1)
        payload["risk_percent"] = round(self.risk_score * 100, 1)
        return payload


@dataclass(slots=True)
class HumanDecisionInboxContract:
    inbox_id: str
    inbox_state: str
    queue_lane: str
    queue_state: str
    priority: str
    human_required: bool
    required_action: str
    queue_owner: str | None = None
    decision_context: dict[str, Any] = field(default_factory=dict)
    authority: dict[str, Any] = field(default_factory=dict)
    execution_plan: dict[str, Any] = field(default_factory=dict)
    task_packet: dict[str, Any] = field(default_factory=dict)
    correlation: dict[str, Any] = field(default_factory=dict)
    evidence_refs: list[str] = field(default_factory=list)
    operator_actions: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "HumanDecisionInboxContract | None":
        if not data:
            return None
        return cls(
            inbox_id=str(data.get("inbox_id", "")),
            inbox_state=str(data.get("inbox_state", "autonomy_ready")),
            queue_lane=str(data.get("queue_lane", "autonomy")),
            queue_state=str(data.get("queue_state", "ready_for_autonomy")),
            priority=str(data.get("priority", "normal")),
            human_required=bool(data.get("human_required", False)),
            required_action=str(data.get("required_action", "observe")),
            queue_owner=str(data.get("queue_owner")) if data.get("queue_owner") else None,
            decision_context=data.get("decision_context", {}) if isinstance(data.get("decision_context", {}), dict) else {},
            authority=data.get("authority", {}) if isinstance(data.get("authority", {}), dict) else {},
            execution_plan=data.get("execution_plan", {}) if isinstance(data.get("execution_plan", {}), dict) else {},
            task_packet=data.get("task_packet", {}) if isinstance(data.get("task_packet", {}), dict) else {},
            correlation=data.get("correlation", {}) if isinstance(data.get("correlation", {}), dict) else {},
            evidence_refs=[str(item) for item in data.get("evidence_refs", [])],
            operator_actions=[str(item) for item in data.get("operator_actions", [])],
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class HumanAskSession:
    session_id: str
    requested_by: str
    created_at: str
    updated_at: str
    status: str
    mode: str
    prompt: str
    participant: AskParticipant
    context_chain: AskContextChain = field(default_factory=AskContextChain)
    transcript: list[AskExchange] = field(default_factory=list)
    decision_summary: AskDecisionSummary | None = None
    action_items: list[AskActionItem] = field(default_factory=list)
    transcript_summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HumanAskSession":
        return cls(
            session_id=str(data.get("session_id", "")),
            requested_by=str(data.get("requested_by", "")),
            created_at=str(data.get("created_at", utc_now())),
            updated_at=str(data.get("updated_at", utc_now())),
            status=str(data.get("status", "completed")),
            mode=str(data.get("mode", "report")),
            prompt=str(data.get("prompt", "")),
            participant=AskParticipant.from_dict(data.get("participant", {})),
            context_chain=AskContextChain.from_dict(data.get("context_chain")),
            transcript=[AskExchange.from_dict(item) for item in data.get("transcript", [])],
            decision_summary=AskDecisionSummary.from_dict(data.get("decision_summary")),
            action_items=[AskActionItem.from_dict(item) for item in data.get("action_items", [])],
            transcript_summary=str(data.get("transcript_summary", "")),
            metadata=data.get("metadata", {}) if isinstance(data.get("metadata", {}), dict) else {},
        )

    def to_dict(self, compact: bool = False) -> dict[str, Any]:
        payload = {
            "session_id": self.session_id,
            "requested_by": self.requested_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status,
            "mode": self.mode,
            "prompt": self.prompt,
            "participant": self.participant.to_dict(),
            "context_chain": self.context_chain.to_dict(),
            "transcript": [item.to_dict() for item in self.transcript],
            "decision_summary": self.decision_summary.to_dict() if self.decision_summary else None,
            "action_items": [item.to_dict() for item in self.action_items],
            "transcript_summary": self.transcript_summary,
            "metadata": self.metadata,
        }
        decision_queue = self.metadata.get("decision_queue", {}) if isinstance(self.metadata.get("decision_queue", {}), dict) else {}
        inbox_contract = self.metadata.get("human_decision_inbox", {}) if isinstance(self.metadata.get("human_decision_inbox", {}), dict) else {}
        execution_plan = decision_queue.get("execution_plan", {}) if isinstance(decision_queue.get("execution_plan", {}), dict) else {}
        payload["summary"] = {
            "participant": self.participant.display_name,
            "role_id": self.participant.role_id,
            "status": self.status,
            "mode": self.mode,
            "director_disposition": str(self.metadata.get("director_disposition", "ready_to_proceed")),
            "participant_total": len(self.metadata.get("participants", [])) or 1,
            "participant_summary_total": len(self.metadata.get("participant_summaries", [])) or 1,
            "participant_decision_total": len(self.metadata.get("participant_decisions", [])) or 1,
            "confidence_score": self.decision_summary.confidence_score if self.decision_summary else 0.0,
            "risk_score": self.decision_summary.risk_score if self.decision_summary else 0.0,
            "automation_state": self.decision_summary.automation_state if self.decision_summary else "unknown",
            "structural_posture": self.decision_summary.structural_posture if self.decision_summary else "unknown",
            "escalated": self.decision_summary.escalated if self.decision_summary else False,
            "action_item_total": len(self.action_items),
            "transcript_entries": len(self.transcript),
            "follow_up": bool(self.context_chain.parent_session_id),
            "queue_state": str(decision_queue.get("queue_state", "not_queued")),
            "queue_lane": str(decision_queue.get("queue_lane", "autonomy")),
            "queue_priority": str(decision_queue.get("priority", "normal")),
            "queue_human_required": bool(decision_queue.get("human_required", False)),
            "queue_execution_plan_id": str(execution_plan.get("plan_id", "")),
            "queue_step_id": str(execution_plan.get("step_id", "")),
            "inbox_state": str(inbox_contract.get("inbox_state", "autonomy_ready")),
            "inbox_required_action": str(inbox_contract.get("required_action", "observe")),
            "inbox_owner": str(inbox_contract.get("queue_owner", "")),
        }
        if compact:
            payload["transcript"] = []
            payload["action_items"] = [item.to_dict() for item in self.action_items[:3]]
        return payload
