import shutil
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.core.hierarchy_registry import HierarchyEntry
from sa_nom_governance.human_ask.human_ask_service import HumanAskService
from sa_nom_governance.studio.role_private_studio_models import PTOSSAssessment, PTOSSIssue


class FakeAuditLogger:
    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []

    def record_event(self, **payload) -> None:
        self.events.append(payload)


class FakeHumanOverride:
    def list_requests(self, status=None):
        return []


class FakeLockManager:
    def list_locks(self):
        return []


class FakeHierarchyRegistry:
    def __init__(self, entries):
        self._entries = list(entries)

    def list_entries(self):
        return list(self._entries)


class FakeStudioStore:
    def list_requests(self):
        return []


class FakeRolePrivateStudio:
    def __init__(self) -> None:
        self.store = FakeStudioStore()


class FakeEngine:
    def __init__(self, entries, audit_logger: FakeAuditLogger) -> None:
        self.audit_logger = audit_logger
        self.human_override = FakeHumanOverride()
        self.lock_manager = FakeLockManager()
        self.hierarchy_registry = FakeHierarchyRegistry(entries)


@contextmanager
def workspace_temp_dir():
    source_base = Path(__file__).resolve().parents[2]
    runtime_tmp = source_base / "_runtime" / "tmp_test"
    runtime_tmp.mkdir(parents=True, exist_ok=True)
    temp_path = runtime_tmp / f"human_ask_{uuid4().hex[:8]}"
    temp_path.mkdir(parents=True, exist_ok=True)
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


def build_service(temp_path: Path) -> HumanAskService:
    source_base = Path(__file__).resolve().parents[2]
    (temp_path / "pt_oss_foundation.json").write_text(
        (source_base / "pt_oss_foundation.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    audit_logger = FakeAuditLogger()
    entries = [
        HierarchyEntry(
            role_id="GOV",
            title="Governance Director",
            stratum=0,
            reports_to=None,
            escalation_to="EXEC_OWNER",
            safety_owner="EXEC_OWNER",
            business_domain="governance",
            handled_resources={"policy", "governance_case"},
            allowed_actions={"review_policy", "route_escalation", "summarize_governance"},
            required_human_actions={"approve_policy"},
            denied_actions={"publish_policy_directly"},
            operating_mode="direct",
            executive_owner_id="EXEC_OWNER",
            seat_id="EXEC-GOV",
        ),
        HierarchyEntry(
            role_id="LEGAL",
            title="Legal Director",
            stratum=1,
            reports_to="GOV",
            escalation_to="EXEC_OWNER",
            safety_owner="EXEC_OWNER",
            business_domain="legal_operations",
            handled_resources={"contract", "legal_case"},
            allowed_actions={"review_contract", "flag_risk", "summarize_legal"},
            required_human_actions={"sign_contract"},
            denied_actions={"execute_payment"},
            operating_mode="indirect",
            assigned_user_id="LEGAL_MANAGER_01",
            executive_owner_id="EXEC_OWNER",
            seat_id="OPS-LEGAL",
        ),
    ]
    config = AppConfig(base_dir=temp_path, persist_runtime=False, environment="development", api_token="owner-token")
    engine = FakeEngine(entries, audit_logger=audit_logger)
    return HumanAskService(
        config=config,
        engine=engine,
        registry=object(),
        role_private_studio=FakeRolePrivateStudio(),
        audit_logger=audit_logger,
    )


def test_human_ask_session_tracks_director_hat_identity() -> None:
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        session = service.create_session(
            {
                "role_id": "GOV",
                "prompt": "Review this governance policy for escalation needs.",
            },
            requested_by="EXEC_OWNER",
        )

        assert session["metadata"]["director_identity"] == "AI Director"
        assert session["metadata"]["active_hat"] == "GOV"
        assert session["metadata"]["director_disposition"] == "ready_to_proceed"
        assert session["mode"] == "report"
        assert session["decision_summary"]["metadata"]["scope_status"] == "in_scope"
        assert session["metadata"]["session_record"]["record_type"] == "report_record"
        assert len(session["transcript"]) == 4
        hat_brief = session["transcript"][2]
        assert hat_brief["message_type"] == "hat_brief"
        assert "AI Director has selected hat GOV" in hat_brief["content"]
        ai_response = session["transcript"][3]
        assert "AI Director is operating under hat GOV" in ai_response["content"]


def test_human_ask_follow_up_hat_brief_mentions_inherited_context() -> None:
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        first = service.create_session(
            {
                "role_id": "GOV",
                "prompt": "Summarize the current governance posture.",
            },
            requested_by="EXEC_OWNER",
        )
        follow_up = service.create_session(
            {
                "role_id": "GOV",
                "prompt": "Continue with the next governance action.",
                "parent_session_id": first["session_id"],
                "inheritance_mode": "inherit",
            },
            requested_by="EXEC_OWNER",
        )

        hat_brief = follow_up["transcript"][2]
        assert "Inherited context from" in hat_brief["content"]
        assert first["session_id"] in hat_brief["content"]
        assert "Prior summary:" in hat_brief["content"]


def test_human_ask_command_alias_normalizes_to_report() -> None:
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        session = service.create_session(
            {
                "role_id": "GOV",
                "mode": "command",
                "prompt": "Route this governance exception to the escalation owner.",
            },
            requested_by="EXEC_OWNER",
        )

        assert session["mode"] == "report"
        assert session["metadata"]["session_kind"] == "report"
        assert session["metadata"]["director_disposition"] == "ready_to_proceed"
        assert "report target" in session["transcript"][1]["content"].lower()
        assert "governed reporting request" in session["transcript"][3]["content"]
        assert session["metadata"]["session_record"]["record_type"] == "report_record"


def test_human_ask_report_mode_uses_report_language() -> None:
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        session = service.create_session(
            {
                "role_id": "GOV",
                "mode": "report",
                "prompt": "Prepare a governance summary for the executive review.",
            },
            requested_by="EXEC_OWNER",
        )

        assert session["mode"] == "report"
        assert session["metadata"]["session_kind"] == "report"
        assert session["metadata"]["director_disposition"] == "ready_to_proceed"
        assert session["metadata"]["session_record"]["record_type"] == "report_record"
        assert "report target" in session["transcript"][1]["content"].lower()
        assert "governed reporting request" in session["transcript"][3]["content"]
        assert any("report record" in item["title"].lower() for item in session["action_items"])


def test_human_ask_meeting_mode_tracks_multiple_hats() -> None:
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        session = service.create_session(
            {
                "mode": "meeting",
                "participant_role_ids": ["GOV", "LEGAL"],
                "prompt": "Review the governance and legal posture for this contract exception.",
            },
            requested_by="EXEC_OWNER",
        )

        assert session["mode"] == "meeting"
        assert session["metadata"]["session_kind"] == "meeting"
        assert session["metadata"]["participant_total"] == 2
        assert len(session["metadata"]["participants"]) == 2
        assert len(session["metadata"]["participant_summaries"]) == 2
        assert len(session["metadata"]["participant_decisions"]) == 2
        assert session["metadata"]["meeting_overview"]["ready_total"] == 2
        assert session["metadata"]["meeting_overview"]["guarded_total"] == 0
        assert session["metadata"]["meeting_overview"]["blocked_total"] == 0
        assert session["metadata"]["director_disposition"] == "ready_to_proceed"
        assert session["metadata"]["session_record"]["record_type"] == "meeting_record"
        assert session["summary"]["participant_summary_total"] == 2
        assert session["summary"]["participant_decision_total"] == 2
        assert session["summary"]["director_disposition"] == "ready_to_proceed"
        primary_summary = session["metadata"]["participant_summaries"][0]
        secondary_summary = session["metadata"]["participant_summaries"][1]
        primary_decision = session["metadata"]["participant_decisions"][0]
        secondary_decision = session["metadata"]["participant_decisions"][1]
        assert primary_summary["primary"] is True
        assert secondary_summary["primary"] is False
        assert primary_decision["primary"] is True
        assert secondary_decision["primary"] is False
        assert primary_decision["decision_status"] == "ready"
        assert secondary_decision["decision_status"] == "ready"
        assert secondary_decision["next_safe_action"]
        assert "shared meeting confidence" in secondary_summary["contribution_summary"]
        assert primary_summary["action_focus"]
        meeting_brief = next(item for item in session["transcript"] if item["message_type"] == "meeting_brief")
        decision_block = next(item for item in session["transcript"] if item["message_type"] == "decision_block")
        synthesis = next(item for item in session["transcript"] if item["message_type"] == "synthesis")
        assert "opened a governed meeting across 2 hats" in meeting_brief["content"]
        assert "decision status" in decision_block["content"]
        assert "Decision lanes are 2 ready, 0 guarded, and 0 blocked." in synthesis["content"]
        assert "meeting record" in synthesis["content"]
        assert "continue autonomous reporting" in synthesis["content"]
        assert "Decision lanes: 2 ready, 0 guarded, 0 blocked." in session["transcript_summary"]
        assert "synthesized the governed meeting record" in synthesis["content"]
        assert any("meeting record" in item["title"].lower() for item in session["action_items"])


def test_human_ask_human_only_boundary_waits_for_human() -> None:
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        session = service.create_session(
            {
                "role_id": "GOV",
                "prompt": "Approve this governance policy for release.",
            },
            requested_by="EXEC_OWNER",
        )

        assert session["status"] == "waiting_human"
        assert session["metadata"]["director_disposition"] == "guarded_follow_up"
        assert session["decision_summary"]["metadata"]["scope_status"] == "human_only_boundary"
        assert session["decision_summary"]["metadata"]["matched_required_human_actions"] == ["approve_policy"]
        assert session["metadata"]["session_record"]["record_type"] == "report_record"


def test_human_ask_out_of_scope_request_waits_for_human_decision() -> None:
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        session = service.create_session(
            {
                "role_id": "GOV",
                "prompt": "Hire the regional manager and approve payroll.",
            },
            requested_by="EXEC_OWNER",
        )

        assert session["status"] == "waiting_human"
        assert session["metadata"]["director_disposition"] == "hold_for_clearance"
        assert session["decision_summary"]["metadata"]["scope_status"] == "out_of_scope"
        assert session["metadata"]["session_record"]["record_type"] == "report_record"
        assert "outside the loaded JD scope" in (session["decision_summary"]["escalation_reason"] or "")


def test_human_ask_studio_record_request_preserves_requested_mode() -> None:
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        original_create_session = service.create_session

        def fake_create_session(payload, requested_by):
            return {
                "session_id": "ask_stub",
                "status": "completed",
                "mode": payload.get("mode"),
                "requested_by": requested_by,
            }

        service.create_session = fake_create_session
        try:
            result = service.create_studio_record_request(
                "studio-123",
                {"mode": "report", "prompt": "Summarize readiness for governed publication."},
                requested_by="EXEC_OWNER",
            )
        finally:
            service.create_session = original_create_session

        assert result["mode"] == "report"
        assert result["requested_by"] == "EXEC_OWNER"


def test_callable_directory_exposes_direct_and_indirect_modes() -> None:
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        directory = service.callable_directory()
        entries = {item["role_id"]: item for item in directory["entries"]}

        assert entries["GOV"]["operating_mode"] == "direct"
        assert entries["GOV"]["executive_owner_id"] == "EXEC_OWNER"
        assert entries["GOV"]["assigned_user_id"] is None
        assert entries["GOV"]["seat_id"] == "EXEC-GOV"
        assert entries["LEGAL"]["operating_mode"] == "indirect"
        assert entries["LEGAL"]["assigned_user_id"] == "LEGAL_MANAGER_01"
        assert entries["LEGAL"]["executive_owner_id"] == "EXEC_OWNER"
        assert entries["LEGAL"]["seat_id"] == "OPS-LEGAL"


def test_session_participant_keeps_operating_assignment_metadata() -> None:
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        session = service.create_session(
            {
                "role_id": "LEGAL",
                "prompt": "Prepare a legal summary for the current contract exception.",
            },
            requested_by="EXEC_OWNER",
        )

        participant = session["participant"]
        assert participant["operating_mode"] == "indirect"
        assert participant["assigned_user_id"] == "LEGAL_MANAGER_01"
        assert participant["executive_owner_id"] == "EXEC_OWNER"
        assert participant["seat_id"] == "OPS-LEGAL"


def test_human_ask_snapshot_reports_mode_totals() -> None:
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)

        service.create_session(
            {
                "role_id": "GOV",
                "prompt": "Summarize the current governance posture.",
            },
            requested_by="EXEC_OWNER",
        )
        service.create_session(
            {
                "role_id": "GOV",
                "mode": "command",
                "prompt": "Route this governance exception to the escalation owner.",
            },
            requested_by="EXEC_OWNER",
        )
        service.create_session(
            {
                "role_id": "GOV",
                "mode": "report",
                "prompt": "Prepare a governance summary for the executive review.",
            },
            requested_by="EXEC_OWNER",
        )
        service.create_session(
            {
                "mode": "meeting",
                "participant_role_ids": ["GOV", "LEGAL"],
                "prompt": "Review the governance and legal posture for this contract exception.",
            },
            requested_by="EXEC_OWNER",
        )

        snapshot = service.human_ask_snapshot(limit=10)
        summary = snapshot["summary"]

        assert summary["report_total"] == 3
        assert summary["meeting_total"] == 1
        assert summary["recorded_total"] == 4
        assert summary["multi_participant_total"] == 1
        assert summary["ready_to_proceed_total"] == 4
        assert summary["guarded_follow_up_total"] == 0
        assert summary["hold_for_clearance_total"] == 0


def test_human_ask_pt_oss_watch_keeps_record_completed_but_guarded() -> None:
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)
        original_assess_runtime_role = service._assess_runtime_role
        service._assess_runtime_role = lambda entry: PTOSSAssessment(
            assessment_id="ptoss-watch",
            generated_at="2026-01-01T00:00:00+00:00",
            mode="PT_OSS_FULL",
            posture="watch",
            readiness_score=70,
            metrics=[],
            blockers=[],
            recommendations=["Strengthen structural resilience before scaling this hat."],
            context={},
        )
        try:
            session = service.create_session(
                {
                    "role_id": "GOV",
                    "prompt": "Please report the current governance posture and next safe action.",
                },
                requested_by="EXEC_OWNER",
            )
        finally:
            service._assess_runtime_role = original_assess_runtime_role

        assert session["status"] == "completed"
        assert session["metadata"]["director_disposition"] == "guarded_follow_up"
        assert session["decision_summary"]["automation_state"] == "clear"
        assert session["decision_summary"]["metadata"]["pt_oss_gate"] == "watch"


def test_human_ask_pt_oss_block_stops_record_request() -> None:
    with workspace_temp_dir() as temp_path:
        service = build_service(temp_path)
        original_assess_runtime_role = service._assess_runtime_role
        service._assess_runtime_role = lambda entry: PTOSSAssessment(
            assessment_id="ptoss-blocked",
            generated_at="2026-01-01T00:00:00+00:00",
            mode="PT_OSS_FULL",
            posture="critical",
            readiness_score=28,
            metrics=[],
            blockers=[PTOSSIssue(category="fragility", severity="critical", message="Structural fragility is above the safe threshold.", blocks_publish=True)],
            recommendations=["Pause runtime use of this hat until fragility is reduced."],
            context={},
        )
        try:
            session = service.create_session(
                {
                    "role_id": "GOV",
                    "prompt": "Please report the current governance posture and next safe action.",
                },
                requested_by="EXEC_OWNER",
            )
        finally:
            service._assess_runtime_role = original_assess_runtime_role

        assert session["status"] == "blocked"
        assert session["metadata"]["director_disposition"] == "hold_for_clearance"
        assert session["decision_summary"]["automation_state"] == "blocked"
        assert session["decision_summary"]["metadata"]["pt_oss_gate"] == "blocked"
