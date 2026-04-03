from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from sa_nom_governance.guards.access_control import AccessControl
from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.utils.persistence import build_state_store

SLUG_RE = re.compile(r"[^a-z0-9]+")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify(value: str, prefix: str) -> str:
    normalized = SLUG_RE.sub("-", str(value or "").strip().lower()).strip("-")
    return normalized or prefix


def titleize(value: str) -> str:
    raw = str(value or "").replace("_", " ").replace("-", " ").strip()
    return " ".join(part.capitalize() for part in raw.split()) if raw else "Unknown"


def age_hours(payload: dict[str, object], *keys: str) -> float:
    for key in keys:
        raw = str(payload.get(key, "") or "").strip()
        if not raw:
            continue
        try:
            timestamp = datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc)
        except ValueError:
            continue
        return max(0.0, round((datetime.now(timezone.utc) - timestamp).total_seconds() / 3600, 2))
    return 0.0


class MasterDataStore:
    def __init__(self, config: AppConfig, store_path) -> None:
        self.store = build_state_store(config, store_path, logical_name="master_data")

    def snapshot(self) -> dict[str, object]:
        payload = self.store.read(default={})
        return {
            "generated_at": str(payload.get("generated_at", "") or ""),
            "organization": payload.get("organization", {}) if isinstance(payload.get("organization", {}), dict) else {},
            "people": payload.get("people", []) if isinstance(payload.get("people", []), list) else [],
            "seats": payload.get("seats", []) if isinstance(payload.get("seats", []), list) else [],
            "teams": payload.get("teams", []) if isinstance(payload.get("teams", []), list) else [],
        }

    def replace(self, *, organization: dict[str, object], people: list[dict[str, object]], seats: list[dict[str, object]], teams: list[dict[str, object]]) -> dict[str, object]:
        next_payload = {
            "generated_at": utc_now(),
            "organization": organization,
            "people": people,
            "seats": seats,
            "teams": teams,
        }
        current_payload = self.snapshot()
        stable_current = json.dumps({key: current_payload.get(key) for key in ("organization", "people", "seats", "teams")}, ensure_ascii=False, sort_keys=True)
        stable_next = json.dumps({key: next_payload.get(key) for key in ("organization", "people", "seats", "teams")}, ensure_ascii=False, sort_keys=True)
        if stable_current != stable_next:
            self.store.write(next_payload)
            return next_payload
        return current_payload


class MasterDataService:
    def __init__(self, config: AppConfig, access_control: AccessControl) -> None:
        self.config = config
        self.access_control = access_control
        self.store = MasterDataStore(config, config.master_data_store_path)

    def master_data_snapshot(self, *, roles: list[dict[str, object]], requests: list[dict[str, object]], overrides: list[dict[str, object]], human_ask: dict[str, object], role_private_studio: dict[str, object], documents: dict[str, object], actions: dict[str, object], cases: dict[str, object], owner_registration: dict[str, object]) -> dict[str, object]:
        organization, people, seats, teams = self._derive_registry(
            roles=roles,
            requests=requests,
            overrides=overrides,
            human_ask=human_ask,
            role_private_studio=role_private_studio,
            documents=documents,
            actions=actions,
            cases=cases,
            owner_registration=owner_registration,
        )
        payload = self.store.replace(organization=organization, people=people, seats=seats, teams=teams)
        return {
            "summary": {
                "organization_name": str(payload.get("organization", {}).get("organization_name", "") if isinstance(payload.get("organization", {}), dict) else ""),
                "people_total": len(payload.get("people", [])),
                "seats_total": len(payload.get("seats", [])),
                "teams_total": len(payload.get("teams", [])),
                "active_people_total": sum(1 for item in payload.get("people", []) if str(item.get("status", "active")) == "active"),
                "role_seat_total": sum(1 for item in payload.get("seats", []) if str(item.get("role_name", "") or "")),
                "search_ready": True,
                "primary_view": "directory",
            },
            "organization": payload.get("organization", {}),
            "people": payload.get("people", []),
            "seats": payload.get("seats", []),
            "teams": payload.get("teams", []),
            "store": self.store.store.descriptor().to_dict(),
        }

    def assignment_queue_snapshot(self, *, master_data: dict[str, object], overrides: list[dict[str, object]], human_ask: dict[str, object], role_private_studio: dict[str, object], documents: dict[str, object], actions: dict[str, object], unified_work_inbox: dict[str, object]) -> dict[str, object]:
        people = {str(item.get("person_id", "") or ""): item for item in master_data.get("people", []) if isinstance(item, dict)}
        teams = {str(item.get("team_id", "") or ""): item for item in master_data.get("teams", []) if isinstance(item, dict)}
        items: list[dict[str, object]] = []

        def resolve_owner(owner_id: str) -> tuple[str, str]:
            normalized = str(owner_id or "").strip()
            if normalized and normalized in people:
                return normalized, str(people[normalized].get("display_name", normalized) or normalized)
            return normalized, titleize(normalized) if normalized else "Unassigned"

        def resolve_team(team_id: str) -> tuple[str, str]:
            normalized = str(team_id or "").strip()
            if normalized and normalized in teams:
                return normalized, str(teams[normalized].get("label", normalized) or normalized)
            return normalized, self._team_label(normalized) if normalized else "Unassigned"

        def classify_sla(hours: float, priority: str) -> str:
            if priority == "critical":
                return "critical" if hours >= 8 else "warning" if hours >= 2 else "in_target"
            if priority == "high":
                return "critical" if hours >= 24 else "warning" if hours >= 8 else "in_target"
            return "critical" if hours >= 72 else "warning" if hours >= 24 else "in_target"

        def enqueue(*, assignment_id: str, kind: str, title: str, detail: str, view: str, focus_type: str, focus_id: str, status: str, priority: str, owner_id: str, team_hint: str, payload: dict[str, object], case_id: str = "", reference_id: str = "", action_label: str = "", next_action: str = "") -> None:
            owner_key, owner_label = resolve_owner(owner_id)
            team_key, team_label = resolve_team(team_hint or self._team_id_from_hint(owner_key or owner_label))
            item_age_hours = age_hours(payload, "updated_at", "resolved_at", "created_at", "timestamp", "opened_at")
            items.append({
                "assignment_id": assignment_id,
                "kind": kind,
                "title": title,
                "detail": detail,
                "view": view,
                "focus_type": focus_type,
                "focus_id": focus_id,
                "status": status,
                "priority": priority,
                "sla_status": classify_sla(item_age_hours, priority),
                "age_hours": item_age_hours,
                "owner_id": owner_key,
                "owner_label": owner_label,
                "team_id": team_key,
                "team_label": team_label,
                "case_id": case_id,
                "reference_id": reference_id,
                "action_label": action_label or f"Open {titleize(view)}",
                "next_action": next_action or "Continue the governed work from the linked lane.",
            })

        for item in overrides:
            if str(item.get("status", "") or "") == "pending":
                enqueue(assignment_id=f"override:{item.get('request_id', '')}", kind="override", title=f"Review override {item.get('request_id', '-')}", detail="A request crossed a human boundary and needs approval or veto with rationale.", view="overrides", focus_type="override", focus_id=str(item.get("request_id", "") or ""), status="human_required", priority="critical", owner_id=str(item.get("approver_role", "reviewer") or "reviewer"), team_hint=self._team_id_from_hint(str(item.get("approver_role", "reviewer") or "reviewer")), payload=item, case_id=str(item.get("case_id", "") or ""), reference_id=str(item.get("origin_request_id", item.get("request_id", "")) or ""), action_label="Open Overrides", next_action="Record the human decision so governed flow can continue safely.")

        for item in human_ask.get("sessions", []) if isinstance(human_ask.get("sessions", []), list) else []:
            status = str(item.get("status", "") or "")
            if status in {"waiting_human", "escalated", "blocked"}:
                priority = "critical" if status in {"blocked", "waiting_human"} else "high"
                summary = item.get("summary", {}) if isinstance(item.get("summary", {}), dict) else {}
                enqueue(assignment_id=f"human_ask:{item.get('session_id', '')}", kind="human_ask", title=f"Review record {item.get('session_id', '-')}", detail=str(summary.get("prompt", "Governed Human Ask record needs follow-through.") or "Governed Human Ask record needs follow-through."), view="human_ask", focus_type="human_ask_session", focus_id=str(item.get("session_id", "") or ""), status="human_required" if status != "escalated" else "attention_required", priority=priority, owner_id=str(item.get("requested_by", "operator") or "operator"), team_hint=self._team_id_from_hint("human_ask"), payload=item, case_id=str(item.get("case_id", "") or ""), reference_id=str(item.get("session_id", "") or ""), action_label="Open Human Ask", next_action="Review the record, decide whether to continue, and capture the next safe step.")

        for item in role_private_studio.get("requests", []) if isinstance(role_private_studio.get("requests", []), list) else []:
            status = str(item.get("status", "") or "")
            if status not in {"published", "archived", "closed"}:
                priority = "high" if bool(item.get("publisher_ready")) or "review" in status else "normal"
                enqueue(assignment_id=f"studio:{item.get('request_id', '')}", kind="studio", title=f"Advance studio request {item.get('request_id', '-')}", detail=str(item.get("title", "Role Private Studio request still needs review or publication.") or "Role Private Studio request still needs review or publication."), view="studio", focus_type="studio_request", focus_id=str(item.get("request_id", "") or ""), status="attention_required" if priority == "high" else "monitoring", priority=priority, owner_id=str(item.get("requested_by", "operator") or "operator"), team_hint=self._team_id_from_hint("studio"), payload=item, case_id=str(item.get("case_id", "") or ""), reference_id=str(item.get("request_id", "") or ""), action_label="Open Role Private Studio", next_action="Move the draft through review, simulation, or trusted publication.")

        for item in documents.get("items", []) if isinstance(documents.get("items", []), list) else []:
            status = str(item.get("status", "") or "")
            if status in {"draft", "in_review", "approved"}:
                priority = "high" if status in {"in_review", "approved"} else "normal"
                enqueue(assignment_id=f"document:{item.get('document_id', '')}", kind="document", title=f"Advance document {item.get('document_number', item.get('document_id', '-'))}", detail=str(item.get("title", "Governed document still needs lifecycle follow-through.") or "Governed document still needs lifecycle follow-through."), view="documents", focus_type="document", focus_id=str(item.get("document_id", "") or ""), status="attention_required" if priority == "high" else "monitoring", priority=priority, owner_id=str(item.get("approver_id", item.get("owner_id", "operator")) or "operator"), team_hint=self._team_id_from_hint("documents"), payload=item, case_id=str(item.get("case_id", "") or ""), reference_id=str(item.get("document_number", item.get("document_id", "")) or ""), action_label="Open Documents", next_action="Continue the review, approval, or publication lane for this document.")

        for item in actions.get("items", []) if isinstance(actions.get("items", []), list) else []:
            status = str(item.get("status", "") or "")
            if status in {"planned", "running", "waiting_human", "failed_closed"}:
                priority = "critical" if status in {"waiting_human", "failed_closed"} else "high" if status == "running" else "normal"
                queue_status = "human_required" if status == "waiting_human" else "blocked" if status == "failed_closed" else "in_progress"
                enqueue(assignment_id=f"action:{item.get('action_id', '')}", kind="action", title=str(item.get("label", item.get("action_type", "AI action")) or "AI action"), detail=str(item.get("output_summary", item.get("next_action", "Governed AI action still needs follow-through.")) or "Governed AI action still needs follow-through."), view="actions", focus_type="action", focus_id=str(item.get("action_id", "") or ""), status=queue_status, priority=priority, owner_id=str(item.get("requested_by", "operator") or "operator"), team_hint=self._team_id_from_hint("actions"), payload=item, case_id=str(item.get("case_id", "") or ""), reference_id=str(item.get("action_id", "") or ""), action_label="Open AI Actions", next_action=str(item.get("next_action", "Review the action outcome and continue from the linked lane.") or "Review the action outcome and continue from the linked lane."))

        if not items:
            for item in unified_work_inbox.get("items", []) if isinstance(unified_work_inbox.get("items", []), list) else []:
                enqueue(assignment_id=f"lane:{item.get('lane_id', '')}", kind="lane", title=str(item.get("title", "Governed work item") or "Governed work item"), detail=str(item.get("operator_action", "Review the governed work lane.") or "Review the governed work lane."), view=str(item.get("view", "overview") or "overview"), focus_type="", focus_id="", status="attention_required" if str(item.get("status", "")) in {"warning", "critical", "stale"} else "monitoring", priority="high" if str(item.get("status", "")) in {"critical", "stale"} else "normal", owner_id="operator", team_hint=self._team_id_from_hint(str(item.get("view", "overview") or "overview")), payload=item, action_label=str(item.get("action_label", "Open view") or "Open view"), next_action=str(item.get("operator_action", "Review the governed work lane.") or "Review the governed work lane."))

        priority_rank = {"critical": 0, "high": 1, "normal": 2}
        status_rank = {"human_required": 0, "blocked": 1, "attention_required": 2, "in_progress": 3, "monitoring": 4}
        items.sort(key=lambda item: (priority_rank.get(str(item.get("priority", "normal")), 9), status_rank.get(str(item.get("status", "monitoring")), 9), -float(item.get("age_hours", 0.0) or 0.0), str(item.get("title", "")).lower()))
        return {"summary": {"items_total": len(items), "critical_total": sum(1 for item in items if str(item.get("priority", "")) == "critical"), "high_total": sum(1 for item in items if str(item.get("priority", "")) == "high"), "human_required_total": sum(1 for item in items if str(item.get("status", "")) == "human_required"), "blocked_total": sum(1 for item in items if str(item.get("status", "")) == "blocked"), "warning_total": sum(1 for item in items if str(item.get("sla_status", "")) == "warning"), "sla_critical_total": sum(1 for item in items if str(item.get("sla_status", "")) == "critical"), "primary_view": str(items[0].get("view", "directory")) if items else "directory"}, "items": items[:50]}

    def global_search_snapshot(self, *, master_data: dict[str, object], assignment_queue: dict[str, object], cases: dict[str, object], requests: list[dict[str, object]], documents: dict[str, object], actions: dict[str, object], human_ask: dict[str, object], roles: list[dict[str, object]], evidence_exports: dict[str, object], sessions: list[dict[str, object]], role_private_studio: dict[str, object]) -> dict[str, object]:
        items: list[dict[str, object]] = []

        def append(*, kind: str, item_id: str, label: str, detail: str, view: str, focus_type: str = "", focus_id: str = "", case_id: str = "", status: str = "", owner_id: str = "", owner_label: str = "", team_id: str = "", team_label: str = "", extra_search: list[str] | None = None) -> None:
            parts = [kind, label, detail, status, case_id, owner_id, owner_label, team_id, team_label] + list(extra_search or [])
            items.append({"search_id": f"{kind}:{item_id or slugify(label, kind)}", "kind": kind, "kind_label": titleize(kind), "id": item_id, "label": label, "detail": detail, "view": view, "focus_type": focus_type, "focus_id": focus_id, "case_id": case_id, "status": status, "owner_id": owner_id, "owner_label": owner_label, "team_id": team_id, "team_label": team_label, "search_text": " ".join(str(part or "") for part in parts).strip()})

        for item in master_data.get("people", []):
            if isinstance(item, dict):
                append(kind="person", item_id=str(item.get("person_id", "") or ""), label=str(item.get("display_name", item.get("person_id", "Person")) or "Person"), detail=str(item.get("primary_role", "Runtime actor") or "Runtime actor"), view="directory", status=str(item.get("status", "active") or "active"), team_id=(item.get("team_ids") or [""])[0] if isinstance(item.get("team_ids"), list) else "", extra_search=[" ".join(str(alias) for alias in item.get("aliases", []) if str(alias))])
        for item in master_data.get("seats", []):
            if isinstance(item, dict):
                append(kind="seat", item_id=str(item.get("seat_id", "") or ""), label=str(item.get("label", item.get("seat_id", "Seat")) or "Seat"), detail=str(item.get("role_name", "Role seat") or "Role seat"), view="directory", status=str(item.get("status", "active") or "active"), owner_id=str(item.get("occupant_id", "") or ""), team_id=str(item.get("team_id", "") or ""), extra_search=[str(item.get("permission_scope", "") or "")])
        for item in master_data.get("teams", []):
            if isinstance(item, dict):
                append(kind="team", item_id=str(item.get("team_id", "") or ""), label=str(item.get("label", item.get("team_id", "Team")) or "Team"), detail=f"{len(item.get('member_ids', [])) if isinstance(item.get('member_ids', []), list) else 0} members", view="directory", team_id=str(item.get("team_id", "") or ""), team_label=str(item.get("label", item.get("team_id", "Team")) or "Team"), extra_search=[" ".join(str(domain) for domain in item.get("domains", []) if str(domain))])
        for item in assignment_queue.get("items", []):
            if isinstance(item, dict):
                append(kind="assignment", item_id=str(item.get("assignment_id", "") or ""), label=str(item.get("title", "Assignment") or "Assignment"), detail=str(item.get("detail", "") or ""), view=str(item.get("view", "directory") or "directory"), focus_type=str(item.get("focus_type", "") or ""), focus_id=str(item.get("focus_id", "") or ""), case_id=str(item.get("case_id", "") or ""), status=str(item.get("status", "") or ""), owner_id=str(item.get("owner_id", "") or ""), owner_label=str(item.get("owner_label", "") or ""), team_id=str(item.get("team_id", "") or ""), team_label=str(item.get("team_label", "") or ""), extra_search=[str(item.get("priority", "") or ""), str(item.get("sla_status", "") or "")])
        for item in cases.get("items", []):
            if isinstance(item, dict):
                append(kind="case", item_id=str(item.get("case_id", "") or ""), label=str(item.get("title", item.get("case_id", "Case")) or "Case"), detail=str(item.get("summary", item.get("case_reference", "Canonical governed case")) or "Canonical governed case"), view="cases", focus_type="case", focus_id=str(item.get("case_id", "") or ""), case_id=str(item.get("case_id", "") or ""), status=str(item.get("status", "") or ""), extra_search=[str(item.get("case_reference", "") or "")])
        for item in requests:
            append(kind="request", item_id=str(item.get("request_id", "") or ""), label=str(item.get("action", item.get("request_id", "Request")) or "Request"), detail=str(item.get("reason", item.get("outcome", "Governed request")) or "Governed request"), view="requests", focus_type="request", focus_id=str(item.get("request_id", "") or ""), case_id=str(item.get("case_id", "") or ""), status=str(item.get("outcome", "") or ""), owner_id=str(item.get("requester", "") or ""), extra_search=[str(item.get("active_role", "") or ""), str(item.get("resource", "") or "")])
        for item in documents.get("items", []) if isinstance(documents.get("items", []), list) else []:
            if isinstance(item, dict):
                append(kind="document", item_id=str(item.get("document_id", "") or ""), label=str(item.get("title", item.get("document_number", "Document")) or "Document"), detail=str(item.get("document_number", item.get("document_class", "Governed document")) or "Governed document"), view="documents", focus_type="document", focus_id=str(item.get("document_id", "") or ""), case_id=str(item.get("case_id", "") or ""), status=str(item.get("status", "") or ""), owner_id=str(item.get("owner_id", "") or ""), extra_search=[str(item.get("document_class", "") or ""), str(item.get("business_domain", "") or "")])
        for item in actions.get("items", []) if isinstance(actions.get("items", []), list) else []:
            if isinstance(item, dict):
                append(kind="action", item_id=str(item.get("action_id", "") or ""), label=str(item.get("label", item.get("action_type", "AI action")) or "AI action"), detail=str(item.get("output_summary", item.get("next_action", "Governed AI action")) or "Governed AI action"), view="actions", focus_type="action", focus_id=str(item.get("action_id", "") or ""), case_id=str(item.get("case_id", "") or ""), status=str(item.get("status", "") or ""), owner_id=str(item.get("requested_by", "") or ""), extra_search=[str(item.get("action_type", "") or ""), str(item.get("authority_boundary", "") or "")])

        for item in human_ask.get("sessions", []) if isinstance(human_ask.get("sessions", []), list) else []:
            if isinstance(item, dict):
                summary = item.get("summary", {}) if isinstance(item.get("summary", {}), dict) else {}
                append(kind="human_ask", item_id=str(item.get("session_id", "") or ""), label=str(summary.get("participant", item.get("session_id", "Human Ask")) or "Human Ask"), detail=str(summary.get("prompt", item.get("status", "Governed record")) or "Governed record"), view="human_ask", focus_type="human_ask_session", focus_id=str(item.get("session_id", "") or ""), case_id=str(item.get("case_id", "") or ""), status=str(item.get("status", "") or ""), owner_id=str(item.get("requested_by", "") or ""))
        for item in role_private_studio.get("requests", []) if isinstance(role_private_studio.get("requests", []), list) else []:
            if isinstance(item, dict):
                append(kind="studio", item_id=str(item.get("request_id", "") or ""), label=str(item.get("title", item.get("request_id", "Studio request")) or "Studio request"), detail=str(item.get("status", "Role Private Studio request") or "Role Private Studio request"), view="studio", focus_type="studio_request", focus_id=str(item.get("request_id", "") or ""), case_id=str(item.get("case_id", "") or ""), status=str(item.get("status", "") or ""), owner_id=str(item.get("requested_by", "") or ""))
        for item in roles:
            append(kind="role", item_id=str(item.get("role_id", "") or ""), label=str(item.get("title", item.get("role_id", "Role")) or "Role"), detail=str(item.get("business_domain", item.get("purpose", "Governed role pack")) or "Governed role pack"), view="policies", status=str(item.get("status", "") or ""), extra_search=[str(item.get("role_id", "") or ""), str(item.get("stratum", "") or "")])
        for item in evidence_exports.get("exports", []) if isinstance(evidence_exports.get("exports", []), list) else []:
            if isinstance(item, dict):
                append(kind="evidence", item_id=str(item.get("pack_id", "") or ""), label=str(item.get("pack_id", "Evidence pack") or "Evidence pack"), detail=str(item.get("posture", item.get("status", "Evidence export")) or "Evidence export"), view="audit", status=str(item.get("status", "") or ""), owner_id=str(item.get("requested_by", "") or ""))
        for item in sessions:
            append(kind="session", item_id=str(item.get("session_id", "") or ""), label=str(item.get("display_name", item.get("session_id", "Session")) or "Session"), detail=str(item.get("role_name", item.get("status", "Runtime session")) or "Runtime session"), view="sessions", status=str(item.get("status", "") or ""), owner_id=str(item.get("profile_id", "") or ""))

        kind_counts: dict[str, int] = {}
        for item in items:
            kind_counts[item["kind"]] = int(kind_counts.get(item["kind"], 0)) + 1
        priority_order = {"assignment": 0, "case": 1, "request": 2, "document": 3, "action": 4, "human_ask": 5, "studio": 6, "person": 7, "team": 8, "seat": 9, "role": 10, "evidence": 11, "session": 12}
        items.sort(key=lambda item: (priority_order.get(item["kind"], 99), str(item.get("label", "")).lower()))
        return {"summary": {"indexed_total": len(items), "kind_counts": kind_counts, "primary_view": "directory"}, "items": items[:250]}

    def _derive_registry(self, *, roles: list[dict[str, object]], requests: list[dict[str, object]], overrides: list[dict[str, object]], human_ask: dict[str, object], role_private_studio: dict[str, object], documents: dict[str, object], actions: dict[str, object], cases: dict[str, object], owner_registration: dict[str, object]) -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
        registration = owner_registration if isinstance(owner_registration, dict) else {}
        organization = {"organization_id": str(registration.get("organization_id", self.config.organization_id()) or self.config.organization_id()), "organization_name": str(registration.get("organization_name", self.config.organization_name() or "SA-NOM Organization") or self.config.organization_name() or "SA-NOM Organization"), "executive_owner_id": str(registration.get("owner_id", self.config.executive_owner_id()) or self.config.executive_owner_id()), "deployment_mode": str(self.config.deployment_mode() or "private"), "source": "owner_registration"}
        people: dict[str, dict[str, object]] = {}
        seats: dict[str, dict[str, object]] = {}
        teams: dict[str, dict[str, object]] = {}

        def ensure_team(team_id: str, *, label: str = "", source: str = "derived", domains: list[str] | None = None) -> dict[str, object]:
            normalized = str(team_id or "team-operations").strip() or "team-operations"
            team = teams.get(normalized)
            if team is None:
                team = {"team_id": normalized, "label": label or self._team_label(normalized), "kind": "functional", "source": source, "member_ids": [], "seat_ids": [], "domains": list(domains or []), "metadata": {}}
                teams[normalized] = team
            else:
                for domain in domains or []:
                    if domain and domain not in team["domains"]:
                        team["domains"].append(domain)
            return team

        def ensure_person(person_id: str, *, display_name: str = "", primary_role: str = "", source: str = "runtime_observed", descriptor: str = "", alias: str = "", team_id: str = "", seat_id: str = "", last_seen_at: str = "", metadata: dict[str, object] | None = None) -> dict[str, object]:
            normalized = str(person_id or "").strip() or f"person-{slugify(display_name or primary_role or 'runtime', 'person')}"
            person = people.get(normalized)
            if person is None:
                person = {"person_id": normalized, "display_name": display_name or titleize(normalized), "primary_role": primary_role, "status": "active", "source": source, "seat_ids": [], "team_ids": [], "aliases": [], "descriptors": [], "last_seen_at": "", "metadata": dict(metadata or {})}
                people[normalized] = person
            else:
                person["metadata"].update(metadata or {})
                if display_name and (not person["display_name"] or person["display_name"] == titleize(person["person_id"])):
                    person["display_name"] = display_name
                if primary_role and not person["primary_role"]:
                    person["primary_role"] = primary_role
            if descriptor and descriptor not in person["descriptors"]:
                person["descriptors"].append(descriptor)
            if alias and alias not in person["aliases"]:
                person["aliases"].append(alias)
            if team_id and team_id not in person["team_ids"]:
                person["team_ids"].append(team_id)
            if seat_id and seat_id not in person["seat_ids"]:
                person["seat_ids"].append(seat_id)
            if last_seen_at and (not person["last_seen_at"] or last_seen_at > str(person["last_seen_at"])):
                person["last_seen_at"] = last_seen_at
            return person

        for profile in self.access_control.list_public_profiles():
            profile_id = str(profile.get("profile_id", "") or "")
            role_name = str(profile.get("role_name", profile_id) or profile_id)
            display_name = str(profile.get("display_name", titleize(profile_id)) or titleize(profile_id))
            permissions = profile.get("permissions", []) if isinstance(profile.get("permissions", []), list) else []
            team_id = self._team_id_from_hint(role_name)
            team = ensure_team(team_id, source="access_profile")
            seat_id = f"seat-{slugify(profile_id, 'seat')}"
            seats[seat_id] = {"seat_id": seat_id, "label": f"{display_name} seat", "role_name": role_name, "occupant_id": profile_id, "status": str(profile.get("status", "active") or "active"), "source": str(profile.get("source", "access_profile") or "access_profile"), "permissions_total": len(permissions), "permission_scope": "all" if "*" in permissions else f"{len(permissions)} permissions", "team_id": team_id, "metadata": {"description": str(profile.get("description", "") or "")}}
            if seat_id not in team["seat_ids"]:
                team["seat_ids"].append(seat_id)
            person = ensure_person(profile_id, display_name=display_name, primary_role=role_name, source=str(profile.get("source", "access_profile") or "access_profile"), descriptor=str(profile.get("description", "") or ""), alias=role_name, team_id=team_id, seat_id=seat_id, metadata={"permissions_total": len(permissions)})
            if person["person_id"] not in team["member_ids"]:
                team["member_ids"].append(person["person_id"])

        executive_id = str(registration.get("owner_id", organization["executive_owner_id"]) or organization["executive_owner_id"])
        executive_name = str(registration.get("display_name", self.config.owner_display_name()) or self.config.owner_display_name())
        executive_team = ensure_team("team-executive", label="Executive stewardship", source="owner_registration")
        executive_person = ensure_person(executive_id, display_name=executive_name, primary_role="owner", source="owner_registration", descriptor="Executive owner", alias="owner", team_id=executive_team["team_id"], metadata={"organization_id": organization["organization_id"]})
        if executive_person["person_id"] not in executive_team["member_ids"]:
            executive_team["member_ids"].append(executive_person["person_id"])

        for role in roles:
            business_domain = str(role.get("business_domain", "") or "").strip()
            if business_domain:
                team_id = self._team_id_from_hint(business_domain)
                team = ensure_team(team_id, source="role_catalog", domains=[business_domain])
                role_id = str(role.get("role_id", "") or "")
                if role_id:
                    person = ensure_person(role_id, display_name=str(role.get("title", titleize(role_id)) or titleize(role_id)), primary_role=role_id, source="role_catalog", descriptor=business_domain, alias=role_id, team_id=team["team_id"])
                    if person["person_id"] not in team["member_ids"]:
                        team["member_ids"].append(person["person_id"])

        def observe_actor(person_ref: str, *, role_hint: str = "", source: str = "runtime", descriptor: str = "", last_seen_at: str = "") -> None:
            normalized = str(person_ref or "").strip()
            if not normalized:
                return
            team_id = self._team_id_from_hint(role_hint or normalized)
            team = ensure_team(team_id, source=source)
            person = ensure_person(normalized, display_name=titleize(normalized), primary_role=role_hint, source=source, descriptor=descriptor, alias=role_hint, team_id=team_id, last_seen_at=last_seen_at)
            if person["person_id"] not in team["member_ids"]:
                team["member_ids"].append(person["person_id"])

        for item in requests:
            observe_actor(str(item.get("requester", "") or ""), role_hint=str(item.get("active_role", "") or ""), source="requests", descriptor=str(item.get("action", "") or ""), last_seen_at=str(item.get("timestamp", "") or ""))
        for item in overrides:
            observe_actor(str(item.get("requester", "") or ""), role_hint=str(item.get("active_role", "") or ""), source="overrides", descriptor="requester", last_seen_at=str(item.get("created_at", "") or ""))
            observe_actor(str(item.get("approver_role", "") or ""), role_hint=str(item.get("approver_role", "") or ""), source="overrides", descriptor="approver", last_seen_at=str(item.get("created_at", "") or ""))
            observe_actor(str(item.get("resolved_by", "") or ""), role_hint=str(item.get("approver_role", "") or ""), source="overrides", descriptor="resolver", last_seen_at=str(item.get("resolved_at", "") or ""))
        for item in human_ask.get("sessions", []) if isinstance(human_ask.get("sessions", []), list) else []:
            observe_actor(str(item.get("requested_by", "") or ""), role_hint="human_ask", source="human_ask", descriptor="record requester", last_seen_at=str(item.get("updated_at", item.get("created_at", "")) or ""))
        for item in role_private_studio.get("requests", []) if isinstance(role_private_studio.get("requests", []), list) else []:
            observe_actor(str(item.get("requested_by", "") or ""), role_hint="studio", source="studio", descriptor="studio request", last_seen_at=str(item.get("updated_at", item.get("created_at", "")) or ""))
        for item in documents.get("items", []) if isinstance(documents.get("items", []), list) else []:
            observe_actor(str(item.get("owner_id", "") or ""), role_hint="documents", source="documents", descriptor=str(item.get("document_class", "document") or "document"), last_seen_at=str(item.get("updated_at", "") or ""))
            observe_actor(str(item.get("approver_id", "") or ""), role_hint="reviewer", source="documents", descriptor="document approver", last_seen_at=str(item.get("updated_at", "") or ""))
        for item in actions.get("items", []) if isinstance(actions.get("items", []), list) else []:
            observe_actor(str(item.get("requested_by", "") or ""), role_hint=str(item.get("requested_role", "actions") or "actions"), source="actions", descriptor=str(item.get("action_type", "action") or "action"), last_seen_at=str(item.get("updated_at", "") or ""))
        for item in cases.get("items", []) if isinstance(cases.get("items", []), list) else []:
            primary_view = str(item.get("primary_view", "") or "")
            if primary_view:
                ensure_team(self._team_id_from_hint(primary_view), source="cases")

        people_list = sorted(people.values(), key=lambda value: (str(value.get("display_name", "")).lower(), str(value.get("person_id", "")).lower()))
        seats_list = sorted(seats.values(), key=lambda value: (str(value.get("label", "")).lower(), str(value.get("seat_id", "")).lower()))
        teams_list = sorted(teams.values(), key=lambda value: (str(value.get("label", "")).lower(), str(value.get("team_id", "")).lower()))
        return organization, people_list, seats_list, teams_list

    def _team_id_from_hint(self, hint: str) -> str:
        normalized = str(hint or "").strip().lower()
        if not normalized:
            return "team-operations"
        if any(token in normalized for token in ("owner", "executive", "exec")):
            return "team-executive"
        if any(token in normalized for token in ("review", "audit", "legal", "compliance", "gov")):
            return "team-governance"
        if any(token in normalized for token in ("document", "record")):
            return "team-documents"
        if any(token in normalized for token in ("studio", "role", "hat")):
            return "team-studio"
        if any(token in normalized for token in ("human ask", "human_ask", "meeting", "report")):
            return "team-reporting"
        if any(token in normalized for token in ("session", "access", "identity")):
            return "team-access"
        if any(token in normalized for token in ("action", "runtime", "operator", "ops")):
            return "team-operations"
        return f"team-{slugify(normalized, 'team')}"

    def _team_label(self, team_id: str) -> str:
        mapping = {"team-executive": "Executive stewardship", "team-governance": "Governance and review", "team-documents": "Document operations", "team-studio": "Role Private Studio", "team-reporting": "Human Ask reporting", "team-access": "Access and session control", "team-operations": "Runtime operations"}
        return mapping.get(team_id, titleize(str(team_id).replace("team-", "")))
