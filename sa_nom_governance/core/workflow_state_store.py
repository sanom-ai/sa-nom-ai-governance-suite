from dataclasses import dataclass
from typing import Any

from sa_nom_governance.core.execution_context import ExecutionContext
from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.utils.persistence import build_state_store


@dataclass(slots=True)
class WorkflowStateSnapshot:
    workflow_id: str
    request_id: str
    requester: str
    action: str
    active_role: str
    current_state: str
    role_state: str
    updated_at: str
    revision: int
    plan_id: str | None = None
    step_id: str | None = None
    step_index: int | None = None
    total_steps: int | None = None
    outcome: str | None = None
    policy_basis: str | None = None
    reason: str | None = None
    decision_queue_id: str | None = None
    decision_queue_lane: str | None = None
    source: str = "runtime_result"
    role_transition: dict[str, Any] | None = None
    runtime_reliability: dict[str, Any] | None = None
    governed_autonomy: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "workflow_id": self.workflow_id,
            "request_id": self.request_id,
            "requester": self.requester,
            "action": self.action,
            "active_role": self.active_role,
            "current_state": self.current_state,
            "role_state": self.role_state,
            "updated_at": self.updated_at,
            "revision": self.revision,
            "plan_id": self.plan_id,
            "step_id": self.step_id,
            "step_index": self.step_index,
            "total_steps": self.total_steps,
            "outcome": self.outcome,
            "policy_basis": self.policy_basis,
            "reason": self.reason,
            "decision_queue_id": self.decision_queue_id,
            "decision_queue_lane": self.decision_queue_lane,
            "source": self.source,
            "role_transition": dict(self.role_transition or {}),
            "runtime_reliability": dict(self.runtime_reliability or {}),
            "governed_autonomy": dict(self.governed_autonomy or {}),
        }
        return payload


class WorkflowStateStore:
    def __init__(self, config: AppConfig | None, store_path) -> None:
        self.store = build_state_store(config, store_path, logical_name="workflow_state")
        self.store_path = self.store.path
        self.workflows: dict[str, dict[str, Any]] = {}
        self.request_index: dict[str, str] = {}
        self._load()

    def save_runtime_state(
        self,
        context: ExecutionContext,
        *,
        result=None,
        source: str = "runtime_result",
    ) -> dict[str, Any]:
        snapshot = self._snapshot_from_context(context, result=result, source=source)
        record = self._normalized_workflow_item(snapshot.to_dict())
        self.workflows[snapshot.workflow_id] = record
        self.request_index[snapshot.request_id] = snapshot.workflow_id
        self._save()
        return dict(record)

    def get_workflow(self, workflow_id: str) -> dict[str, Any]:
        if workflow_id not in self.workflows:
            raise KeyError(f"Workflow state not found: {workflow_id}")
        return dict(self._normalized_workflow_item(self.workflows[workflow_id]))

    def get_by_request(self, request_id: str) -> dict[str, Any]:
        workflow_id = self.request_index.get(request_id)
        if workflow_id is None:
            raise KeyError(f"Workflow request not found: {request_id}")
        return self.get_workflow(workflow_id)

    def list_workflows(self, current_state: str | None = None, *, limit: int | None = None) -> list[dict[str, Any]]:
        items = sorted(
            (self._normalized_workflow_item(item) for item in self.workflows.values()),
            key=lambda item: str(item.get("updated_at", "")),
            reverse=True,
        )
        if current_state is not None:
            items = [item for item in items if item.get("current_state") == current_state]
        if limit is not None:
            items = items[: max(0, limit)]
        return [dict(item) for item in items]

    def summary(self) -> dict[str, Any]:
        normalized_items = [self._normalized_workflow_item(item) for item in self.workflows.values()]
        states: dict[str, int] = {}
        for item in normalized_items:
            state = str(item.get("current_state") or "unknown")
            states[state] = states.get(state, 0) + 1
        return {
            "total": len(normalized_items),
            "states": dict(sorted(states.items())),
            "governed_autonomy": self._governed_autonomy_summary(normalized_items),
            "store": self.store.descriptor().to_dict(),
        }

    def _load(self) -> None:
        data = self.store.read(default={})
        self.workflows = {
            workflow_id: self._normalized_workflow_item(dict(item))
            for workflow_id, item in data.get("workflows", {}).items()
            if isinstance(item, dict)
        }
        self.request_index = {
            str(request_id): str(workflow_id)
            for request_id, workflow_id in data.get("request_index", {}).items()
        }

    def _save(self) -> None:
        self.store.write(
            {
                "workflows": {
                    workflow_id: dict(self._normalized_workflow_item(item))
                    for workflow_id, item in sorted(self.workflows.items())
                },
                "request_index": dict(sorted(self.request_index.items())),
            }
        )

    def _snapshot_from_context(self, context: ExecutionContext, *, result=None, source: str) -> WorkflowStateSnapshot:
        runtime_flow = context.metadata.get("runtime_state_flow")
        role_lifecycle = context.metadata.get("role_execution_lifecycle")
        execution_plan = context.metadata.get("execution_plan")
        decision_queue = context.metadata.get("decision_queue")
        runtime_reliability = context.metadata.get("runtime_reliability")

        workflow_id = self._workflow_id_for(context)
        previous = self.workflows.get(workflow_id, {})
        current_state = "received"
        updated_at = ""
        if isinstance(runtime_flow, dict):
            current_state = str(runtime_flow.get("current_state") or current_state)
            updated_at = str(runtime_flow.get("entered_at") or updated_at)
        role_state = "assigned"
        if isinstance(role_lifecycle, dict):
            role_state = str(role_lifecycle.get("current_state") or role_state)
            updated_at = str(role_lifecycle.get("entered_at") or updated_at or "")

        plan_id = workflow_id if isinstance(execution_plan, dict) and execution_plan.get("plan_id") else None
        step_id = None
        step_index = None
        total_steps = None
        if isinstance(execution_plan, dict):
            plan_id = str(execution_plan.get("plan_id") or workflow_id)
            step_id = self._string_or_none(execution_plan.get("step_id"))
            step_index = self._int_or_none(execution_plan.get("step_index"))
            total_steps = self._int_or_none(execution_plan.get("total_steps"))

        decision_queue_id = None
        decision_queue_lane = None
        if isinstance(decision_queue, dict):
            decision_queue_id = self._string_or_none(decision_queue.get("queue_id"))
            decision_queue_lane = self._string_or_none(decision_queue.get("queue_lane"))

        policy_basis = getattr(result, "policy_basis", None) if result is not None else None
        reason = getattr(result, "reason", None) if result is not None else None

        governed_autonomy = self._governed_autonomy_for(
            current_state=current_state,
            role_state=role_state,
            decision_queue_lane=decision_queue_lane,
            runtime_reliability=dict(runtime_reliability) if isinstance(runtime_reliability, dict) else {},
            source=source,
            reason=self._string_or_none(reason),
        )

        return WorkflowStateSnapshot(
            workflow_id=workflow_id,
            request_id=context.request_id,
            requester=context.requester,
            action=context.action,
            active_role=context.role_id,
            current_state=current_state,
            role_state=role_state,
            updated_at=updated_at,
            revision=int(previous.get("revision", 0)) + 1,
            plan_id=plan_id,
            step_id=step_id,
            step_index=step_index,
            total_steps=total_steps,
            policy_basis=self._string_or_none(policy_basis),
            reason=self._string_or_none(reason),
            decision_queue_id=decision_queue_id,
            decision_queue_lane=decision_queue_lane,
            source=source,
            role_transition=dict(context.role_transition),
            runtime_reliability=dict(runtime_reliability) if isinstance(runtime_reliability, dict) else {},
            governed_autonomy=governed_autonomy,
        )

    def _normalized_workflow_item(self, item: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(item)
        current_state = self._string_or_none(normalized.get("current_state")) or "received"
        role_state = self._string_or_none(normalized.get("role_state")) or "assigned"
        decision_queue_lane = self._string_or_none(normalized.get("decision_queue_lane"))
        source = self._string_or_none(normalized.get("source")) or "runtime_result"
        reason = self._string_or_none(normalized.get("reason"))
        runtime_reliability_value = normalized.get("runtime_reliability")
        runtime_reliability = dict(runtime_reliability_value) if isinstance(runtime_reliability_value, dict) else {}
        governed_autonomy = normalized.get("governed_autonomy")
        if not isinstance(governed_autonomy, dict) or not governed_autonomy:
            governed_autonomy = self._governed_autonomy_for(
                current_state=current_state,
                role_state=role_state,
                decision_queue_lane=decision_queue_lane,
                runtime_reliability=runtime_reliability,
                source=source,
                reason=reason,
            )
        normalized["governed_autonomy"] = dict(governed_autonomy)
        normalized["runtime_reliability"] = runtime_reliability
        return normalized

    def _governed_autonomy_for(
        self,
        *,
        current_state: str,
        role_state: str,
        decision_queue_lane: str | None,
        runtime_reliability: dict[str, Any],
        source: str,
        reason: str | None,
    ) -> dict[str, Any]:
        state_token = current_state.strip().lower() if current_state else "unknown"
        role_token = role_state.strip().lower() if role_state else "unknown"
        lane_token = decision_queue_lane.strip().lower() if decision_queue_lane else None
        reliability_error = self._string_or_none(runtime_reliability.get("error_type")) if isinstance(runtime_reliability, dict) else None
        reliability_outcome = self._string_or_none(runtime_reliability.get("outcome_state")) if isinstance(runtime_reliability, dict) else None

        if state_token in {"received", "classified", "routed", "in_progress_ai", "approved"}:
            if source == "override_resume":
                posture_reason = "Workflow resumed after human approval and AI can continue inside the governed path."
            else:
                posture_reason = reason or "Workflow is progressing autonomously inside the approved governed path."
            return {
                "posture": "autonomous_inflight",
                "next_action": "continue_autonomously",
                "ai_can_continue": True,
                "human_gate_open": False,
                "operator_attention_required": False,
                "queue_lane": lane_token,
                "reason": posture_reason,
            }

        if state_token in {"awaiting_human_confirmation", "escalated"} or role_token == "paused_for_human":
            if lane_token == "clearance":
                next_action = "await_clearance_review"
                posture_reason = "Workflow is paused until clearance review is completed."
            elif lane_token == "human_review":
                next_action = "await_human_review"
                posture_reason = "Workflow is paused until human review is completed."
            elif lane_token == "guarded_follow_up":
                next_action = "await_guarded_follow_up"
                posture_reason = "Workflow is paused until guarded follow-up is acknowledged."
            else:
                next_action = "await_human_decision"
                posture_reason = reason or "Workflow is paused for a human governance decision before AI can continue."
            return {
                "posture": "human_gate_open",
                "next_action": next_action,
                "ai_can_continue": False,
                "human_gate_open": True,
                "operator_attention_required": True,
                "queue_lane": lane_token,
                "reason": posture_reason,
            }

        if state_token == "closed_with_exception" or reliability_outcome == "retryable":
            detail = reason or "Workflow encountered a runtime exception and needs governed recovery."
            if reliability_error:
                detail = f"Workflow encountered {reliability_error} and needs governed recovery before AI can resume."
            return {
                "posture": "recovery_required",
                "next_action": "recover_then_retry",
                "ai_can_continue": False,
                "human_gate_open": False,
                "operator_attention_required": True,
                "queue_lane": lane_token,
                "reason": detail,
            }

        if state_token == "blocked":
            return {
                "posture": "fail_closed",
                "next_action": "review_blocked_workflow",
                "ai_can_continue": False,
                "human_gate_open": False,
                "operator_attention_required": True,
                "queue_lane": lane_token,
                "reason": reason or "Workflow is fail-closed and requires operator review before any continuation.",
            }

        if state_token == "completed":
            return {
                "posture": "completed",
                "next_action": "none",
                "ai_can_continue": False,
                "human_gate_open": False,
                "operator_attention_required": False,
                "queue_lane": lane_token,
                "reason": reason or "Workflow completed inside the governed runtime.",
            }

        return {
            "posture": "unknown",
            "next_action": "review_runtime_state",
            "ai_can_continue": False,
            "human_gate_open": False,
            "operator_attention_required": True,
            "queue_lane": lane_token,
            "reason": reason or f"Workflow is in unclassified state {state_token}.",
        }

    def _governed_autonomy_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        posture_counts: dict[str, int] = {}
        for item in items:
            autonomy = item.get("governed_autonomy") if isinstance(item.get("governed_autonomy"), dict) else {}
            posture = str(autonomy.get("posture") or "unknown")
            posture_counts[posture] = posture_counts.get(posture, 0) + 1

        autonomous_inflight_total = posture_counts.get("autonomous_inflight", 0)
        human_gate_open_total = posture_counts.get("human_gate_open", 0)
        fail_closed_total = posture_counts.get("fail_closed", 0)
        recovery_required_total = posture_counts.get("recovery_required", 0)
        completed_total = posture_counts.get("completed", 0)
        unknown_total = posture_counts.get("unknown", 0)

        status = "idle"
        recommended_runtime_action = "none"
        if recovery_required_total > 0:
            status = "blocked"
            recommended_runtime_action = "recover_then_retry"
        elif fail_closed_total > 0:
            status = "blocked"
            recommended_runtime_action = "review_blocked_workflow"
        elif human_gate_open_total > 0:
            status = "human_gated"
            recommended_runtime_action = "await_human_gate"
        elif autonomous_inflight_total > 0:
            status = "autonomous_inflight"
            recommended_runtime_action = "continue_autonomously"
        elif items:
            status = "settled"

        return {
            "status": status,
            "recommended_runtime_action": recommended_runtime_action,
            "autonomous_inflight_total": autonomous_inflight_total,
            "human_gate_open_total": human_gate_open_total,
            "fail_closed_total": fail_closed_total,
            "recovery_required_total": recovery_required_total,
            "completed_total": completed_total,
            "unknown_total": unknown_total,
            "postures": dict(sorted(posture_counts.items())),
        }

    def _workflow_id_for(self, context: ExecutionContext) -> str:
        execution_plan = context.metadata.get("execution_plan")
        if isinstance(execution_plan, dict) and execution_plan.get("plan_id"):
            return str(execution_plan["plan_id"])
        raw_plan = context.metadata.get("execution_plan")
        if isinstance(raw_plan, dict) and raw_plan.get("plan_id"):
            return str(raw_plan["plan_id"])
        return context.request_id

    def _string_or_none(self, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _int_or_none(self, value: Any) -> int | None:
        try:
            return None if value is None else int(value)
        except (TypeError, ValueError):
            return None