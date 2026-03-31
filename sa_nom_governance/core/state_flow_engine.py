from dataclasses import dataclass
from datetime import datetime, timezone

from sa_nom_governance.api.api_schemas import DecisionResult
from sa_nom_governance.core.execution_context import ExecutionContext


@dataclass(slots=True)
class RuntimeTransitionRecord:
    from_state: str | None
    to_state: str
    event: str
    reason: str
    at: str

    def to_dict(self) -> dict[str, str | None]:
        return {
            "from_state": self.from_state,
            "to_state": self.to_state,
            "event": self.event,
            "reason": self.reason,
            "at": self.at,
        }


class RuntimeStateFlowEngine:
    """Tracks governed runtime state and role lifecycle transitions."""

    _OUTCOME_TO_RUNTIME_STATE = {
        "approved": "completed",
        "waiting_human": "awaiting_human_confirmation",
        "human_required": "awaiting_human_confirmation",
        "escalated": "escalated",
        "blocked": "blocked",
        "rejected": "blocked",
        "conflicted": "blocked",
        "out_of_order": "blocked",
        "suspended": "blocked",
        "retryable": "closed_with_exception",
    }

    def bootstrap(self, context: ExecutionContext, *, object_type: str = "request") -> None:
        flow = context.metadata.get("runtime_state_flow")
        if isinstance(flow, dict) and isinstance(flow.get("history"), list):
            self._ensure_role_lifecycle(context)
            return

        now = self._utc_now()
        context.metadata["runtime_state_flow"] = {
            "object_type": object_type,
            "current_state": "received",
            "entered_at": now,
            "history": [
                RuntimeTransitionRecord(
                    from_state=None,
                    to_state="received",
                    event="intake_registered",
                    reason="Request entered governed runtime orchestration.",
                    at=now,
                ).to_dict()
            ],
        }
        context.metadata["role_execution_lifecycle"] = {
            "current_state": "assigned",
            "entered_at": now,
            "history": [
                RuntimeTransitionRecord(
                    from_state=None,
                    to_state="assigned",
                    event="role_assigned",
                    reason=f"Role {context.role_id} assigned to runtime path.",
                    at=now,
                ).to_dict()
            ],
        }
        self._transition_runtime(
            context,
            to_state="classified",
            event="boundary_checked",
            reason="Runtime classification and boundary check completed.",
        )
        self._transition_runtime(
            context,
            to_state="routed",
            event="route_selected",
            reason=f"Workflow routed to role {context.role_id}.",
        )
        self._transition_runtime(
            context,
            to_state="in_progress_ai",
            event="ai_execution_started",
            reason="AI execution started inside approved runtime boundary.",
        )
        self._transition_role(
            context,
            to_state="active",
            event="role_active",
            reason=f"Role {context.role_id} is active for AI execution.",
        )

    def resume_after_human_confirmation(self, context: ExecutionContext) -> None:
        self.bootstrap(context)
        self._transition_role(
            context,
            to_state="resumed",
            event="human_confirmation_resumed",
            reason="Human decision recorded. Runtime resumed for AI execution.",
        )
        self._transition_runtime(
            context,
            to_state="in_progress_ai",
            event="ai_execution_resumed",
            reason="Workflow resumed after human confirmation.",
        )
        self._transition_role(
            context,
            to_state="active",
            event="role_reactivated",
            reason="Role returned to active execution state.",
        )

    def apply_outcome(self, context: ExecutionContext, result: DecisionResult) -> None:
        self.bootstrap(context)
        target_state = self._OUTCOME_TO_RUNTIME_STATE.get(result.outcome, "closed_with_exception")

        if target_state == "awaiting_human_confirmation":
            self._transition_runtime(
                context,
                to_state="awaiting_human_confirmation",
                event=f"decision_{result.outcome}",
                reason=result.reason,
            )
            self._transition_role(
                context,
                to_state="paused_for_human",
                event="human_confirmation_required",
                reason="Runtime paused for trust-sensitive human decision.",
            )
            return

        if target_state == "escalated":
            self._transition_runtime(
                context,
                to_state="escalated",
                event="decision_escalated",
                reason=result.reason,
            )
            self._transition_role(
                context,
                to_state="paused_for_human",
                event="escalation_pending",
                reason="Escalation requires human authority before continuation.",
            )
            return

        if result.outcome == "approved":
            self._transition_runtime(
                context,
                to_state="approved",
                event="decision_approved",
                reason=result.reason,
            )
            self._transition_runtime(
                context,
                to_state="completed",
                event="workflow_completed",
                reason="Workflow reached governed completion.",
            )
            self._transition_role(
                context,
                to_state="completed",
                event="role_completed",
                reason=f"Role {context.role_id} completed governed execution.",
            )
            return

        self._transition_runtime(
            context,
            to_state=target_state,
            event=f"decision_{result.outcome}",
            reason=result.reason,
        )
        self._transition_role(
            context,
            to_state="stopped",
            event="runtime_stopped",
            reason=f"Workflow stopped in state {target_state}.",
        )

    def _ensure_role_lifecycle(self, context: ExecutionContext) -> None:
        lifecycle = context.metadata.get("role_execution_lifecycle")
        if isinstance(lifecycle, dict) and isinstance(lifecycle.get("history"), list):
            return
        now = self._utc_now()
        context.metadata["role_execution_lifecycle"] = {
            "current_state": "assigned",
            "entered_at": now,
            "history": [
                RuntimeTransitionRecord(
                    from_state=None,
                    to_state="assigned",
                    event="role_assigned",
                    reason=f"Role {context.role_id} assigned to runtime path.",
                    at=now,
                ).to_dict()
            ],
        }

    def _transition_runtime(
        self,
        context: ExecutionContext,
        *,
        to_state: str,
        event: str,
        reason: str,
    ) -> None:
        flow = context.metadata["runtime_state_flow"]
        from_state = flow.get("current_state")
        if from_state == to_state:
            return
        transition = RuntimeTransitionRecord(
            from_state=str(from_state) if from_state is not None else None,
            to_state=to_state,
            event=event,
            reason=reason,
            at=self._utc_now(),
        )
        history = flow.get("history", [])
        history.append(transition.to_dict())
        flow["history"] = history
        flow["current_state"] = to_state
        flow["entered_at"] = transition.at

    def _transition_role(
        self,
        context: ExecutionContext,
        *,
        to_state: str,
        event: str,
        reason: str,
    ) -> None:
        lifecycle = context.metadata["role_execution_lifecycle"]
        from_state = lifecycle.get("current_state")
        if from_state == to_state:
            return
        transition = RuntimeTransitionRecord(
            from_state=str(from_state) if from_state is not None else None,
            to_state=to_state,
            event=event,
            reason=reason,
            at=self._utc_now(),
        )
        history = lifecycle.get("history", [])
        history.append(transition.to_dict())
        lifecycle["history"] = history
        lifecycle["current_state"] = to_state
        lifecycle["entered_at"] = transition.at

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()
