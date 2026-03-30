from dataclasses import asdict, is_dataclass
from pathlib import Path

from sa_nom_governance.api.api_schemas import DecisionResult, OverrideReviewResult
from sa_nom_governance.audit.audit_logger import AuditLogger
from sa_nom_governance.guards.authority_guard import AuthorityGuard
from sa_nom_governance.core.decision_engine import DecisionEngine
from sa_nom_governance.core.decision_models import DecisionComputation, DecisionTrace
from sa_nom_governance.core.dispatcher import RequestDispatcher
from sa_nom_governance.guards.ethics_guard import EthicsGuard
from sa_nom_governance.core.hierarchy_registry import HierarchyEscalationDecision, HierarchyRegistry
from sa_nom_governance.guards.human_override import HumanOverrideGateway, HumanOverrideState
from sa_nom_governance.core.lock_manager import ResourceConflictError, ResourceLockManager
from sa_nom_governance.core.request_consistency import IdempotencyReplay, RequestConsistencyError, RequestConsistencyManager
from sa_nom_governance.core.result_builder import build_result
from sa_nom_governance.core.risk_scorer import RiskScorer
from sa_nom_governance.core.role_activation_router import RoleActivationError, RoleActivationRouter
from sa_nom_governance.ptag.role_loader import RoleLoader
from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.utils.owner_identity import DEFAULT_EXECUTIVE_OWNER_ID


class CoreEngine:
    def __init__(
        self,
        role_loader: RoleLoader,
        *,
        config: AppConfig | None = None,
        audit_log_path: Path | None = None,
        override_store_path: Path | None = None,
        lock_store_path: Path | None = None,
        consistency_store_path: Path | None = None,
    ) -> None:
        self.dispatcher = RequestDispatcher()
        self.role_loader = role_loader
        self.ethics_guard = EthicsGuard()
        self.authority_guard = AuthorityGuard()
        self.risk_scorer = RiskScorer()
        self.decision_engine = DecisionEngine()
        self.human_override = HumanOverrideGateway(store_path=override_store_path, config=config)
        self.lock_manager = ResourceLockManager(store_path=lock_store_path, config=config)
        self.request_consistency = RequestConsistencyManager(store_path=consistency_store_path, config=config)
        self.audit_logger = AuditLogger(log_path=audit_log_path, config=config)
        default_executive_owner_id = (
            config.executive_owner_id() if config is not None else DEFAULT_EXECUTIVE_OWNER_ID
        )
        self.hierarchy_registry = HierarchyRegistry(role_loader, default_executive_owner_id=default_executive_owner_id)
        self.role_activation_router = RoleActivationRouter(self.hierarchy_registry)
        self.role_transition_policy = self.role_activation_router.transition_policy

    def process(self, requester: str, action: str, role_id: str | None, payload: dict, metadata: dict | None = None):
        context, activation_error = self._build_activation_context(
            requester=requester,
            action=action,
            role_id=role_id,
            payload=payload,
            metadata=metadata,
        )

        try:
            self.request_consistency.prepare(context)
        except IdempotencyReplay as replay:
            self.audit_logger.record_event(
                active_role=context.role_id,
                action="runtime_idempotent_replay",
                outcome="replayed",
                reason="Request replayed from idempotency store.",
                metadata=replay.audit_metadata,
            )
            return replay.result
        except RequestConsistencyError as error:
            result = self._build_consistency_result(context, error)
            self.audit_logger.record(result)
            return result

        self._record_role_transition(context, activation_error=activation_error)
        if activation_error is not None:
            result = self._build_activation_failure_result(context, activation_error)
            self.request_consistency.complete(context, result)
            self.audit_logger.record(result)
            return result

        try:
            lock_state = self.lock_manager.acquire(context)
        except ResourceConflictError as conflict:
            context.metadata["resource_conflict"] = conflict.existing_lock.to_dict()
            result = build_result(
                context,
                DecisionComputation(
                    outcome="conflicted",
                    reason=f"Request blocked by active resource lock on {conflict.requested_key}.",
                    policy_basis="runtime.resource_lock",
                    trace=DecisionTrace(
                        source_type="runtime_conflict",
                        source_id=conflict.requested_key,
                        notes=[
                            "Resource conflict detected before decision execution.",
                            f"Lock owned by request {conflict.existing_lock.owner_request_id}.",
                        ],
                    ),
                ),
                conflict_lock=conflict.existing_lock.to_dict(),
            )
            self.request_consistency.complete(context, result)
            self.audit_logger.record(result)
            return result

        if lock_state is not None:
            context.metadata["resource_lock"] = lock_state.to_dict()

        try:
            result = self._evaluate_context(context)
            result = self._sync_lock_state(result, request_id=context.request_id)
        except Exception:
            self.request_consistency.abort(context)
            if lock_state is not None:
                self.lock_manager.release_by_request(context.request_id)
            raise

        if result.outcome == "waiting_human" and context.metadata.get("role_hierarchy_escalation"):
            self._record_role_escalation(context, result.reason)

        self.request_consistency.complete(context, result)
        self.audit_logger.record(result)
        return result

    def _build_activation_context(self, requester: str, action: str, role_id: str | None, payload: dict, metadata: dict | None = None):
        try:
            activation = self.role_activation_router.resolve(
                requester=requester,
                requested_role=role_id,
                action=action,
                payload=payload,
                metadata=metadata,
            )
            merged_metadata = self._merge_transition_metadata(metadata, activation.transition.to_dict())
            context = self.dispatcher.dispatch(
                requester=requester,
                action=action,
                role_id=activation.active_role,
                payload=payload,
                metadata=merged_metadata,
            )
            return context, None
        except RoleActivationError as error:
            merged_metadata = self._merge_transition_metadata(metadata, error.transition.to_dict())
            context = self.dispatcher.dispatch(
                requester=requester,
                action=action,
                role_id=error.transition.new_role or "UNRESOLVED",
                payload=payload,
                metadata=merged_metadata,
            )
            return context, error

    def _evaluate_context(self, context, approved_override: HumanOverrideState | None = None):
        role_document = self.role_loader.load(context.role_id)
        self.authority_guard.ensure_action_allowed(role_document, context.action)
        context.risk_score = self.risk_scorer.score(context)
        self.ethics_guard.ensure_allowed(context)

        hierarchy_escalation = self._transition_policy_escalation(context) or self.hierarchy_registry.evaluate_escalation(context)
        if hierarchy_escalation is not None:
            context.role_transition["escalated_to"] = hierarchy_escalation.escalated_to
            context.metadata["role_transition"] = dict(context.role_transition)
            context.metadata["role_hierarchy_escalation"] = {
                "rule_id": hierarchy_escalation.rule_id,
                "escalated_to": hierarchy_escalation.escalated_to,
                "reason": hierarchy_escalation.reason,
                "notes": list(hierarchy_escalation.notes),
            }
            computation = self._resolve_hierarchy_escalation(
                context=context,
                hierarchy_escalation=hierarchy_escalation,
                approved_override=approved_override,
            )
        else:
            computation = self.decision_engine.decide(context, role_document, approved_override=approved_override)

        approver_role = self._override_approver_role(context, hierarchy_escalation)
        if computation.outcome == "waiting_human" and computation.human_override is None and approved_override is None:
            computation.human_override = self.human_override.create_state(
                context=context,
                required_by=computation.policy_basis,
                reason=computation.reason,
                approver_role=approver_role,
            )
        elif approved_override is not None and computation.human_override is None:
            computation.human_override = approved_override

        lock_state = self.lock_manager.get_by_request(context.request_id)
        if lock_state is not None:
            context.metadata["resource_lock"] = lock_state.to_dict()

        return build_result(
            context,
            computation,
            resource_lock=lock_state.to_dict() if lock_state is not None else None,
        )

    def _transition_policy_escalation(self, context) -> HierarchyEscalationDecision | None:
        transition = dict(context.role_transition)
        if transition.get("transition_disposition") != "review":
            return None
        escalated_to = transition.get("escalated_to") or self.hierarchy_registry.default_escalation_target(context.role_id)
        rule_id = str(transition.get("transition_rule_id") or f"{context.role_id}.transition_review")
        reason = str(transition.get("transition_policy_reason") or transition.get("switch_reason") or "Role transition requires human review.")
        return HierarchyEscalationDecision(
            rule_id=rule_id,
            escalated_to=str(escalated_to),
            reason=reason,
            notes=[
                f"previous_role={transition.get('previous_role') or '-'}",
                f"new_role={transition.get('new_role') or context.role_id}",
                f"activation_source={transition.get('activation_source') or '-'}",
            ],
        )

    def _resolve_hierarchy_escalation(
        self,
        *,
        context,
        hierarchy_escalation: HierarchyEscalationDecision,
        approved_override: HumanOverrideState | None,
    ) -> DecisionComputation:
        override_matches = (
            approved_override is not None
            and approved_override.status == "approved"
            and approved_override.active_role == context.role_id
            and approved_override.action == context.action
            and approved_override.required_by == hierarchy_escalation.rule_id
        )
        if override_matches:
            return DecisionComputation(
                outcome="approved",
                reason=f"Action resumed after hierarchy escalation approval for {hierarchy_escalation.rule_id}.",
                policy_basis=hierarchy_escalation.rule_id,
                trace=DecisionTrace(
                    source_type="human_override_resume",
                    source_id=approved_override.request_id,
                    notes=[
                        "Hierarchy escalation approval resumed execution.",
                        f"Escalated to: {hierarchy_escalation.escalated_to}.",
                    ],
                ),
                human_override=approved_override,
            )
        return DecisionComputation(
            outcome="waiting_human",
            reason=hierarchy_escalation.reason,
            policy_basis=hierarchy_escalation.rule_id,
            trace=DecisionTrace(
                source_type="hierarchy_escalation",
                source_id=hierarchy_escalation.rule_id,
                notes=list(hierarchy_escalation.notes),
            ),
        )

    def _override_approver_role(self, context, hierarchy_escalation: HierarchyEscalationDecision | None) -> str:
        if hierarchy_escalation is not None:
            return hierarchy_escalation.escalated_to
        return self.hierarchy_registry.default_escalation_target(context.role_id)

    def _sync_lock_state(self, result, request_id: str):
        lock_state = self.lock_manager.get_by_request(request_id)
        if lock_state is None:
            return result

        if result.outcome == "waiting_human":
            lock_state = self.lock_manager.mark_waiting(request_id) or lock_state
            result.resource_lock = lock_state.to_dict()
        else:
            self.lock_manager.release_by_request(request_id)
            result.resource_lock = None

        result.metadata["resource_lock"] = result.resource_lock
        return result

    def list_override_requests(self, status: str | None = None) -> list[dict[str, object]]:
        return [request.to_dict() for request in self.human_override.list_requests(status=status)]

    def get_override_request(self, request_id: str) -> dict[str, object]:
        return self.human_override.get_request(request_id).to_dict()

    def list_lock_states(self, status: str | None = None) -> list[dict[str, object]]:
        return [lock.to_dict() for lock in self.lock_manager.list_locks(status=status)]

    def list_audit_entries(self, limit: int | None = None) -> list[dict[str, object]]:
        return [entry.to_dict() for entry in self.audit_logger.list_entries(limit=limit)]

    def review_override(self, request_id: str, resolved_by: str, decision: str, note: str | None = None) -> OverrideReviewResult:
        execution_result = None
        released_lock = None
        if decision == "approve":
            state = self.human_override.approve(request_id=request_id, resolved_by=resolved_by, note=note)
            self.lock_manager.mark_active(state.origin_request_id)
            execution_result = self._resume_override(state)
            self.human_override.record_execution(
                request_id=request_id,
                outcome=execution_result.outcome,
                policy_basis=execution_result.policy_basis or "unknown",
                reason=execution_result.reason,
            )
            state = self.human_override.get_request(request_id)
        elif decision == "veto":
            state = self.human_override.veto(request_id=request_id, resolved_by=resolved_by, note=note)
            released_lock = self.lock_manager.release_by_request(state.origin_request_id)
        else:
            raise ValueError(f"Unsupported override decision: {decision}")

        metadata = state.to_dict()
        if released_lock is not None:
            metadata["released_lock"] = released_lock.to_dict()

        self.audit_logger.record_override_event(
            active_role=state.active_role,
            action=f"override_{decision}",
            outcome=state.status,
            reason=f"Human override request {request_id} resolved by {resolved_by}.",
            metadata=metadata,
        )

        return OverrideReviewResult(
            request_id=state.request_id,
            status=state.status,
            resolved_by=state.resolved_by,
            resolution_note=state.resolution_note,
            active_role=state.active_role,
            action=state.action,
            required_by=state.required_by,
            execution_result=asdict(execution_result) if execution_result is not None else None,
        )

    def _resume_override(self, state: HumanOverrideState):
        context = self.dispatcher.dispatch(
            requester=state.requester,
            action=state.action,
            role_id=state.active_role,
            payload=state.payload_snapshot,
            request_id=state.origin_request_id,
            metadata=state.context_metadata_snapshot,
        )
        result = self._evaluate_context(context, approved_override=state)
        result = self._sync_lock_state(result, request_id=context.request_id)
        self.request_consistency.complete(context, result)
        self.audit_logger.record(result)
        return result

    def _build_consistency_result(self, context, error: RequestConsistencyError) -> DecisionResult:
        context.metadata.setdefault("request_consistency", {})["consistency_status"] = error.consistency_status
        return build_result(
            context,
            DecisionComputation(
                outcome=error.outcome,
                reason=error.reason,
                policy_basis=error.policy_basis,
                trace=DecisionTrace(
                    source_type=error.source_type,
                    source_id=error.source_id,
                    notes=error.notes,
                ),
            ),
        )

    def _build_activation_failure_result(self, context, error: RoleActivationError) -> DecisionResult:
        return build_result(
            context,
            DecisionComputation(
                outcome="escalated",
                reason=error.reason,
                policy_basis="runtime.role_activation",
                trace=DecisionTrace(
                    source_type="role_activation",
                    source_id=error.code,
                    notes=[
                        "Role activation router failed closed.",
                        error.reason,
                    ],
                ),
            ),
        )

    def _merge_transition_metadata(self, metadata: dict | None, transition: dict[str, object]) -> dict[str, object]:
        merged = dict(metadata or {})
        merged["role_transition"] = transition
        business_domain = transition.get("business_domain")
        if business_domain and not merged.get("business_domain"):
            merged["business_domain"] = business_domain
        return merged

    def _record_role_transition(self, context, activation_error: RoleActivationError | None = None) -> None:
        transition = dict(context.role_transition)
        if not transition:
            return
        previous_role = transition.get("previous_role")
        new_role = transition.get("new_role") or context.role_id
        event_action = "role_switch" if previous_role and previous_role != new_role else "role_activation"
        event_outcome = "escalated" if activation_error is not None else "activated"
        self.audit_logger.record_event(
            active_role=str(new_role),
            action=event_action,
            outcome=event_outcome,
            reason=str(transition.get("switch_reason") or f"Role {new_role} activated for action {context.action}."),
            metadata={
                "request_id": context.request_id,
                "requester": context.requester,
                "action": context.action,
                "transition": transition,
            },
        )

    def _record_role_escalation(self, context, reason: str) -> None:
        escalation = context.metadata.get("role_hierarchy_escalation", {})
        self.audit_logger.record_event(
            active_role=context.role_id,
            action="role_escalation",
            outcome="waiting_human",
            reason=reason,
            metadata={
                "request_id": context.request_id,
                "requester": context.requester,
                "action": context.action,
                "transition": dict(context.role_transition),
                "hierarchy_escalation": escalation,
            },
        )
