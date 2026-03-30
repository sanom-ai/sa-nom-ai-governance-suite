from __future__ import annotations

from sa_nom_governance.human_ask.human_ask_models import AskDecisionSummary, AskParticipantDecision, CallableDirectoryEntry


def assignment_signature(entry: CallableDirectoryEntry) -> str:
    if entry.operating_mode == "indirect":
        human_owner = entry.assigned_user_id or "assigned human operator"
        seat_note = f" on seat {entry.seat_id}" if entry.seat_id else ""
        return f"Indirect mode attached to {human_owner}{seat_note}"
    seat_note = f" for seat {entry.seat_id}" if entry.seat_id else ""
    executive_owner = entry.executive_owner_id or "executive owner"
    return f"Direct mode under executive owner {executive_owner}{seat_note}"


def build_transcript_summary(
    entry: CallableDirectoryEntry,
    entries: list[CallableDirectoryEntry],
    decision_summary: AskDecisionSummary,
    participant_decisions: list[AskParticipantDecision],
    mode: str,
) -> str:
    participant_note = ""
    if mode == "meeting":
        participant_note = f" across {len(entries)} hats"
    summary = (
        f"{entry.display_name} was routed through Human Ask as a {mode_label(mode).lower()} record"
        f"{participant_note} with {decision_summary.automation_state} automation posture."
        f" {assignment_signature(entry)}."
    )
    if mode == "meeting":
        overview = meeting_decision_overview(participant_decisions)
        summary += (
            f" Decision lanes: {overview['ready_total']} ready, {overview['guarded_total']} guarded,"
            f" {overview['blocked_total']} blocked."
        )
    if decision_summary.escalated and decision_summary.escalated_to:
        return f"{summary} The record is waiting for {decision_summary.escalated_to}."
    return f"{summary} Confidence {decision_summary.confidence_score:.2f}, risk {decision_summary.risk_score:.2f}."


def build_response_message(
    entry: CallableDirectoryEntry,
    decision_summary: AskDecisionSummary,
    prompt: str,
    mode: str,
) -> str:
    hat_label = f"AI Director is operating under hat {entry.role_id} ({entry.display_name})."
    base = (
        f"{hat_label} This hat is available for governed reporting in business domain "
        f"{entry.business_domain or 'general_operations'}. {assignment_signature(entry)}."
    )
    if entry.source == "studio_draft":
        base = (
            f"{hat_label} This hat is being routed from Role Private Studio for governed reporting."
            f" Publication status is {entry.publication_status}."
        )
    if decision_summary.escalated and decision_summary.escalated_to:
        return (
            f"{base} The request '{prompt}' has been paused for review and routed to "
            f"{decision_summary.escalated_to}. {decision_summary.escalation_reason or ''}".strip()
        )
    if decision_summary.outcome == "blocked":
        return f"{base} The record request is blocked because structural or callable posture does not allow safe automation."
    if mode == "report":
        return (
            f"{base} The report request '{prompt}' has been accepted as a governed reporting request."
            f" A structured record can now be preserved under confidence"
            f" {decision_summary.confidence_score:.2f} and risk {decision_summary.risk_score:.2f}."
        )
    return (
        f"{base} The current meeting record may continue on '{prompt}' "
        f"under confidence {decision_summary.confidence_score:.2f} and risk {decision_summary.risk_score:.2f}."
    )


def build_meeting_synthesis(
    entries: list[CallableDirectoryEntry],
    prompt: str,
    decision_summary: AskDecisionSummary,
    meeting_overview: dict[str, object],
) -> str:
    role_list = ", ".join(item.role_id for item in entries)
    blocked_roles = ", ".join(str(item) for item in meeting_overview.get("blocked_roles", []))
    guarded_roles = ", ".join(str(item) for item in meeting_overview.get("guarded_roles", []))
    lane_outcome = "The Director can preserve this meeting record and continue autonomous reporting."
    if int(meeting_overview.get("blocked_total", 0)) > 0:
        lane_outcome = (
            f"The Director should hold the meeting record until blocked hats"
            f" are cleared: {blocked_roles or 'blocked lanes require review'}."
        )
    elif int(meeting_overview.get("guarded_total", 0)) > 0:
        lane_outcome = (
            f"The Director may keep recording the meeting while hats"
            f" {guarded_roles or 'with human gates'} stay under review."
        )
    return (
        f"AI Director synthesized the governed meeting record for '{prompt}' across hats {role_list}."
        f" Decision lanes are {meeting_overview.get('ready_total', 0)} ready,"
        f" {meeting_overview.get('guarded_total', 0)} guarded, and"
        f" {meeting_overview.get('blocked_total', 0)} blocked."
        f" The current record posture is {decision_summary.outcome} with"
        f" confidence {decision_summary.confidence_score:.2f} and risk {decision_summary.risk_score:.2f}."
        f" {lane_outcome}"
    )


def build_session_record(
    *,
    prompt: str,
    mode: str,
    participant_entry: CallableDirectoryEntry,
    participant_entries: list[CallableDirectoryEntry],
    decision_summary: AskDecisionSummary,
    meeting_overview: dict[str, object],
) -> dict[str, object]:
    if mode == "meeting":
        return {
            "record_type": "meeting_record",
            "title": f"Meeting record: {participant_entry.display_name}",
            "prompt": prompt,
            "participants": [item.role_id for item in participant_entries],
            "summary": build_meeting_synthesis(
                participant_entries,
                prompt,
                decision_summary,
                meeting_overview,
            ),
            "ready_total": meeting_overview.get("ready_total", 0),
            "guarded_total": meeting_overview.get("guarded_total", 0),
            "blocked_total": meeting_overview.get("blocked_total", 0),
            "status": decision_summary.outcome,
        }
    return {
        "record_type": "report_record",
        "title": f"Report record: {participant_entry.display_name}",
        "prompt": prompt,
        "participant": participant_entry.role_id,
        "summary": build_response_message(participant_entry, decision_summary, prompt, "report"),
        "scope_status": decision_summary.metadata.get("scope_status", "in_scope"),
        "status": decision_summary.outcome,
    }


def build_participant_next_safe_action(
    *,
    entry: CallableDirectoryEntry,
    action_focus: list[str],
    required_human_actions: list[str],
    mode: str,
    primary: bool,
    decision_status: str,
) -> str:
    action_focus_label = ", ".join(action_focus[:2]) or "governed role actions"
    human_actions = ", ".join(required_human_actions[:2])
    role_position = "primary hat" if primary else "consulted hat"
    if decision_status == "blocked":
        return f"Hold the record for {entry.role_id} until callable posture is restored and governance conditions are rechecked."
    if decision_status == "guarded" and human_actions:
        return f"Use {entry.role_id} as a {role_position} for reporting only, then route human-only actions such as {human_actions} to the escalation owner."
    if mode == "meeting":
        return f"Carry {entry.role_id} forward as a {role_position} reporting lane focused on {action_focus_label} before the final meeting record is preserved."
    if mode == "report":
        return f"Refine the report through {action_focus_label} and preserve the output as the governed record."
    return f"Continue reporting with {entry.role_id} under {action_focus_label} and keep within callable boundaries."


def build_participant_contribution_summary(
    *,
    entry: CallableDirectoryEntry,
    decision_summary: AskDecisionSummary,
    prompt: str,
    mode: str,
    primary: bool,
    action_focus: list[str],
    handled_resources: list[str],
) -> str:
    action_focus_label = ", ".join(action_focus[:3]) or "governed role actions"
    resource_focus = ", ".join(handled_resources[:3]) or "governed resources"
    role_position = "primary active hat" if primary else "consulted hat"
    if mode == "meeting":
        return (
            f"As the {role_position}, this hat contributes domain posture"
            f" {entry.business_domain or 'general_operations'}, keeps focus on {action_focus_label},"
            f" and covers {resource_focus} under shared meeting confidence"
            f" {decision_summary.confidence_score:.2f}."
        )
    if mode == "report":
        return (
            f"As the {role_position}, this hat frames a structured report through {action_focus_label}"
            f" and summarizes {resource_focus} with PT-OSS posture {entry.pt_oss_posture}."
        )
    return (
        f"As the {role_position}, this hat addresses '{prompt}' through {action_focus_label}"
        f" while governing {resource_focus} for the final record."
    )


def meeting_decision_overview(participant_decisions: list[AskParticipantDecision]) -> dict[str, object]:
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


def mode_label(mode: str) -> str:
    labels = {
        "report": "Report",
        "meeting": "Meeting",
    }
    return labels.get(mode, "Report")
