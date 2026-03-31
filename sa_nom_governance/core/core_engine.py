from dataclasses import asdict
from pathlib import Path

from sa_nom_governance.api.api_schemas import DecisionResult, OverrideReviewResult
from sa_nom_governance.audit.audit_logger import AuditLogger
from sa_nom_governance.core.authority_policy_engine import AuthorityPolicyEngine
from sa_nom_governance.core.decision_engine import DecisionEngine
from sa_nom_governance.core.decision_models import DecisionComputation, DecisionTrace
from sa_nom_governance.core.dispatcher import RequestDispatcher
from sa_nom_governance.core.hierarchy_registry import HierarchyEscalationDecision, HierarchyRegistry
from sa_nom_governance.core.lock_manager import ResourceConflictError, ResourceLockManager
from sa_nom_governance.core.policy_runtime_contracts import RuntimeContractGuard
from sa_nom_governance.core.request_consistency import (
    IdempotencyReplay,
    RequestConsistencyError,
    RequestConsistencyManager,
)
from sa_nom_governance.core.result_builder import build_result
from sa_nom_governance.core.risk_scorer import RiskScorer
from sa_nom_governance.core.role_activation_router import RoleActivationError, RoleActivationRouter
from sa_nom_governance.core.runtime_recovery_store import RuntimeRecoveryStore
from sa_nom_governance.core.state_flow_engine import RuntimeStateFlowEngine
from sa_nom_governance.core.workflow_state_store import WorkflowStateStore
from sa_nom_governance.guards.authority_guard import AuthorityGuard
from sa_nom_governance.guards.ethics_guard import EthicsGuard
from sa_nom_governance.guards.human_override import HumanOverrideGateway, HumanOverrideState
from sa_nom_governance.ptag.role_loader import RoleLoader
from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.utils.owner_identity import DEFAULT_EXECUTIVE_OWNER_ID


class HumanRequiredError(Exception):
    """Runtime signal for trust-sensitive decisions that must pause for human input."""


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
        workflow_state_store_path: Path | None = None,
        runtime_recovery_store_path: Path | None = None,
        runtime_dead_letter_path: Path | None = None,
    ) -> None:
        self.dispatcher = RequestDispatcher()
        self.role_loader = role_loader
        self.ethics_guard = EthicsGuard()
        self.authority_guard = AuthorityGuard()
        self.risk_scorer = RiskScorer()
        self.runtime_contract_guard = RuntimeContractGuard()
        self.authority_policy_engine = AuthorityPolicyEngine()
        self.decision_engine = DecisionEngine()
        self.state_flow_engine = RuntimeStateFlowEngine()
        self.human_override = HumanOverrideGateway(store_path=override_store_path, config=config)
        self.lock_manager = ResourceLockManager(store_path=lock_store_path, config=config)
        self.request_consistency = RequestConsistencyManager(store_path=consistency_store_path, config=config)
        self.workflow_state_store = WorkflowStateStore(config=config, store_path=workflow_state_store_path)
        self.runtime_recovery_store = RuntimeRecoveryStore(
            config=config,
            store_path=runtime_recovery_store_path,
            dead_letter_path=runtime_dead_letter_path,
        )
        self.audit_logger = AuditLogger(log_path=audit_log_path, config=config)
        default_executive_owner_id = (
            config.executive_owner_id() if config is not None else DEFAULT_EXECUTIVE_OWNER_ID
        )
        self.hierarchy_registry = HierarchyRegistry(role_loader, default_executive_owner_id=default_executive_owner_id)
        self.role_activation_router = RoleActivationRouter(self.hierarchy_registry)
        self.role_transition_policy = self.role_activation_router.transition_policy

    def process(self, requester: str, action: str, role_id: str | None, payload: dict, metadata: dict | None = None):
        max_attempts = self._runtime_retry_max_attempts(metadata)
        attempt = 1
        while True:
            try:
                return self._process_once(
                    requester=requester,
                    action=action,
                    role_id=role_id,
                    payload=payload,
                    metadata=metadata,
                    attempt=attempt,
                    max_attempts=max_attempts,
                )
            except Exception as error:
                outcome = self._classify_runtime_error(error)
                if outcome == 'retryable' and attempt < max_attempts:
                    attempt += 1
                    continue
                result = self._build_runtime_failure_result(
                    requester=requester,
                    action=action,
                    role_id=role_id,
                    payload=payload,
                    metadata=metadata,
                    attempt=attempt,
                    max_attempts=max_attempts,
                    error=error,
                    outcome=outcome,
                )
                failure_context = self.dispatcher.dispatch(
                    requester=requester,
                    action=action,
                    role_id=role_id or 'UNRESOLVED',
                    payload=payload if isinstance(payload, dict) else {'raw_payload_type': type(payload).__name__},
                    request_id=str(result.metadata.get('request_id', '')) or None,
                    metadata=metadata if isinstance(metadata, dict) else {},
                )
                self._set_runtime_reliability_metadata(
                    failure_context.metadata,
                    attempt=attempt,
                    max_attempts=max_attempts,
                    outcome_state=outcome,
                    error=error,
                )
                self._record_runtime_recovery(
                    failure_context,
                    result,
                    attempt=attempt,
                    max_attempts=max_attempts,
                    error=error,
                    outcome=outcome,
                )
                self.audit_logger.record(result)
                return result

    def _process_once(
        self,
        *,
        requester: str,
        action: str,
        role_id: str | None,
        payload: dict,
        metadata: dict | None,
        attempt: int,
        max_attempts: int,
    ):
        request_violation = self.runtime_contract_guard.request_violation(
            requester=requester,
            action=action,
            role_id=role_id,
            payload=payload,
            metadata=metadata,
        )
        if request_violation is not None:
            context = self.dispatcher.dispatch(
                requester=requester,
                action=action,
                role_id=role_id or 'UNRESOLVED',
                payload=payload if isinstance(payload, dict) else {'raw_payload_type': type(payload).__name__},
                metadata=metadata if isinstance(metadata, dict) else {},
            )
            self._set_runtime_reliability_metadata(
                context.metadata,
                attempt=attempt,
                max_attempts=max_attempts,
                outcome_state='request_violation',
            )
            result = build_result(
                context,
                self.runtime_contract_guard.to_computation(request_violation, phase='request'),
            )
            self._sync_runtime_reliability_result_metadata(result, context)
            self._sync_state_flow_result_metadata(result, context)
            self.audit_logger.record(result)
            return result

        context, activation_error = self._build_activation_context(
            requester=requester,
            action=action,
            role_id=role_id,
            payload=payload,
            metadata=metadata,
        )
        self._set_runtime_reliability_metadata(
            context.metadata,
            attempt=attempt,
            max_attempts=max_attempts,
            outcome_state='in_progress',
        )
        self.state_flow_engine.bootstrap(context)
        self._sync_workflow_state_store(context, source='runtime_bootstrap')

        try:
            self.request_consistency.prepare(context)
        except IdempotencyReplay as replay:
            self.audit_logger.record_event(
                active_role=context.role_id,
                action='runtime_idempotent_replay',
                outcome='replayed',
                reason='Request replayed from idempotency store.',
                metadata=replay.audit_metadata,
            )
            return replay.result
        except RequestConsistencyError as error:
            result = self._build_consistency_result(context, error)
            self._sync_state_flow_result_metadata(result, context)
            self.audit_logger.record(result)
            return result

        self._record_role_transition(context, activation_error=activation_error)
        if activation_error is not None:
            result = self._build_activation_failure_result(context, activation_error)
            self._set_runtime_reliability_metadata(
                context.metadata,
                attempt=attempt,
                max_attempts=max_attempts,
                outcome_state=result.outcome,
            )
            self._sync_runtime_reliability_result_metadata(result, context)
            self._sync_state_flow_result_metadata(result, context)
            self.request_consistency.complete(context, result)
            self.audit_logger.record(result)
            return result

        try:
            lock_state = self.lock_manager.acquire(context)
        except ResourceConflictError as conflict:
            context.metadata['resource_conflict'] = conflict.existing_lock.to_dict()
            result = build_result(
                context,
                DecisionComputation(
                    outcome='conflicted',
                    reason=f'Request blocked by active resource lock on {conflict.requested_key}.',
                    policy_basis='runtime.resource_lock',
                    trace=DecisionTrace(
                        source_type='runtime_conflict',
                        source_id=conflict.requested_key,
                        notes=[
                            'Resource conflict detected before decision execution.',
                            f'Lock owned by request {conflict.existing_lock.owner_request_id}.',
                        ],
                    ),
                ),
                conflict_lock=conflict.existing_lock.to_dict(),
            )
            self._set_runtime_reliability_metadata(
                context.metadata,
                attempt=attempt,
                max_attempts=max_attempts,
                outcome_state=result.outcome,
            )
            self._sync_runtime_reliability_result_metadata(result, context)
            self._sync_state_flow_result_metadata(result, context)
            self.request_consistency.complete(context, result)
            self.audit_logger.record(result)
            return result

        if lock_state is not None:
            context.metadata['resource_lock'] = lock_state.to_dict()

        try:
            result = self._evaluate_context(context)
            result = self._sync_lock_state(result, request_id=context.request_id)
        except Exception:
            self.request_consistency.abort(context)
            if lock_state is not None:
                self.lock_manager.release_by_request(context.request_id)
            raise

        if result.outcome == 'waiting_human' and context.metadata.get('role_hierarchy_escalation'):
            self._record_role_escalation(context, result.reason)

        self._set_runtime_reliability_metadata(
            context.metadata,
            attempt=attempt,
            max_attempts=max_attempts,
            outcome_state=result.outcome,
        )
        self._sync_runtime_reliability_result_metadata(result, context)
        self._sync_state_flow_result_metadata(result, context)
        self.request_consistency.complete(context, result)
        self.audit_logger.record(result)
        return result

    def _runtime_retry_max_attempts(self, metadata: dict | None) -> int:
        if not isinstance(metadata, dict):
            return 2
        raw_value = metadata.get('runtime_retry_max_attempts', 2)
        try:
            return min(3, max(1, int(raw_value)))
        except (TypeError, ValueError):
            return 2

    def _classify_runtime_error(self, error: Exception) -> str:
        if isinstance(error, HumanRequiredError):
            return 'human_required'
        if isinstance(error, PermissionError):
            return 'rejected'
        if isinstance(error, (TimeoutError, ConnectionError, OSError)):
            return 'retryable'
        return 'blocked'

    def _build_runtime_failure_result(
        self,
        *,
        requester: str,
        action: str,
        role_id: str | None,
        payload: dict,
        metadata: dict | None,
        attempt: int,
        max_attempts: int,
        error: Exception,
        outcome: str,
    ) -> DecisionResult:
        context = self.dispatcher.dispatch(
            requester=requester,
            action=action,
            role_id=role_id or 'UNRESOLVED',
            payload=payload if isinstance(payload, dict) else {'raw_payload_type': type(payload).__name__},
            metadata=metadata if isinstance(metadata, dict) else {},
        )
        self._set_runtime_reliability_metadata(
            context.metadata,
            attempt=attempt,
            max_attempts=max_attempts,
            outcome_state=outcome,
            error=error,
        )
        result = build_result(
            context,
            DecisionComputation(
                outcome=outcome,
                reason=f'Runtime orchestration intercepted {type(error).__name__}: {error}',
                policy_basis='runtime.orchestration.reliability',
                trace=DecisionTrace(
                    source_type='runtime_reliability',
                    source_id=type(error).__name__,
                    notes=[
                        'Exception captured by reliability orchestration layer.',
                        f'attempt={attempt}/{max_attempts}',
                    ],
                ),
            ),
        )
        self._sync_runtime_reliability_result_metadata(result, context)
        self._sync_state_flow_result_metadata(result, context)
        return result

    def _set_runtime_reliability_metadata(
        self,
        metadata: dict[str, object],
        *,
        attempt: int,
        max_attempts: int,
        outcome_state: str,
        error: Exception | None = None,
    ) -> None:
        runtime_metadata: dict[str, object] = {
            'attempts_used': attempt,
            'max_attempts': max_attempts,
            'outcome_state': outcome_state,
            'retry_exhausted': attempt >= max_attempts,
        }
        if error is not None:
            runtime_metadata['error_type'] = type(error).__name__
            runtime_metadata['error_message'] = str(error)
        metadata['runtime_reliability'] = runtime_metadata

    def _sync_runtime_reliability_result_metadata(self, result: DecisionResult, context) -> None:
        runtime_metadata = context.metadata.get('runtime_reliability')
        if not isinstance(runtime_metadata, dict):
            return
        envelope = result.metadata.setdefault('metadata', {})
        envelope['runtime_reliability'] = dict(runtime_metadata)

    def _set_reasoning_control_metadata(self, context) -> None:
        context.metadata['reasoning_control'] = self.runtime_contract_guard.reasoning_profile(context)

    def _normalize_resume_contract_metadata(self, context) -> None:
        execution_plan = self.runtime_contract_guard.normalized_execution_plan_contract(context.metadata.get('execution_plan'))
        if execution_plan is not None:
            context.metadata['execution_plan'] = execution_plan
        task_packet = self.runtime_contract_guard.normalized_task_packet_contract(context.metadata.get('task_packet'))
        if task_packet is not None:
            context.metadata['task_packet'] = task_packet

    def _set_execution_plan_metadata(self, context) -> None:
        execution_plan = self.runtime_contract_guard.execution_plan_profile(context)
        if execution_plan is not None:
            context.metadata['execution_plan'] = execution_plan

    def _set_task_packet_metadata(self, context) -> None:
        task_packet = self.runtime_contract_guard.task_packet_profile(context)
        if task_packet is not None:
            context.metadata['task_packet'] = task_packet

    def _sync_state_flow_result_metadata(self, result: DecisionResult, context, *, source: str = 'runtime_result') -> None:
        self.state_flow_engine.bootstrap(context)
        self.state_flow_engine.apply_outcome(context, result)
        envelope = result.metadata.setdefault('metadata', {})
        runtime_flow = context.metadata.get('runtime_state_flow')
        if isinstance(runtime_flow, dict):
            envelope['runtime_state_flow'] = dict(runtime_flow)
        role_lifecycle = context.metadata.get('role_execution_lifecycle')
        if isinstance(role_lifecycle, dict):
            envelope['role_execution_lifecycle'] = dict(role_lifecycle)
        reasoning_control = context.metadata.get('reasoning_control')
        if isinstance(reasoning_control, dict):
            envelope['reasoning_control'] = dict(reasoning_control)
        execution_plan = context.metadata.get('execution_plan')
        if isinstance(execution_plan, dict):
            envelope['execution_plan'] = dict(execution_plan)
        task_packet = context.metadata.get('task_packet')
        if isinstance(task_packet, dict):
            envelope['task_packet'] = dict(task_packet)
        workflow_state = self._sync_workflow_state_store(context, result=result, source=source)
        if isinstance(workflow_state, dict):
            envelope['workflow_state'] = dict(workflow_state)

    def _sync_workflow_state_store(self, context, *, result: DecisionResult | None = None, source: str = 'runtime_result') -> dict[str, object]:
        return self.workflow_state_store.save_runtime_state(context, result=result, source=source)

    def _record_runtime_recovery(
        self,
        context,
        result: DecisionResult,
        *,
        attempt: int,
        max_attempts: int,
        error: Exception,
        outcome: str,
    ) -> None:
        failure_classification = 'retry_exhausted' if outcome == 'retryable' and attempt >= max_attempts else 'runtime_failure'
        self.runtime_recovery_store.save_failure(
            context,
            outcome=result.outcome,
            policy_basis=result.policy_basis or 'runtime.orchestration.reliability',
            reason=result.reason,
            attempts_used=attempt,
            max_attempts=max_attempts,
            failure_classification=failure_classification,
        )

        self.audit_logger.record_event(
            active_role=context.role_id,
            action='runtime_dead_letter',
            outcome='dead_letter',
            reason='Runtime failure captured into governed dead-letter recovery store.',
            metadata={
                'request_id': context.request_id,
                'error_type': type(error).__name__,
                'failure_classification': failure_classification,
                'attempts_used': attempt,
                'max_attempts': max_attempts,
                'result_outcome': result.outcome,
            },
        )

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
        context_violation = self.runtime_contract_guard.context_violation(context)
        if context_violation is not None:
            return build_result(
                context,
                self.runtime_contract_guard.to_computation(context_violation, phase='context'),
            )

        self._set_reasoning_control_metadata(context)
        self._set_execution_plan_metadata(context)
        self._set_task_packet_metadata(context)
        preflight_violation = self.runtime_contract_guard.preflight_violation(
            context,
            expected_override_approver_role=self.hierarchy_registry.default_escalation_target(context.role_id),
        )
        if preflight_violation is not None:
            return build_result(
                context,
                self.runtime_contract_guard.to_computation(preflight_violation, phase='preflight'),
            )

        reasoning_profile = context.metadata['reasoning_control']
        if reasoning_profile['requires_human_confirmation']:
            computation = DecisionComputation(
                outcome='human_required',
                reason='Deep-think reasoning mode requires explicit human confirmation by runtime contract.',
                policy_basis='runtime.reasoning_control',
                trace=DecisionTrace(
                    source_type='reasoning_control',
                    source_id='deep_think_human_gate',
                    notes=[
                        f"reasoning_mode={reasoning_profile['reasoning_mode']}",
                        f"max_reasoning_steps={reasoning_profile['max_reasoning_steps']}",
                    ],
                ),
            )
        else:
            computation = None

        role_document = self.role_loader.load(context.role_id)
        self.authority_guard.ensure_action_allowed(role_document, context.action)
        context.risk_score = self.risk_scorer.score(context)
        self.ethics_guard.ensure_allowed(context)

        authority_violation = self.authority_policy_engine.contract_violation(context)
        if computation is not None:
            self._set_authority_gate_metadata(
                context,
                outcome=computation.outcome,
                source_id=computation.trace.source_id,
                reason=computation.reason,
                requires_human_confirmation=True,
            )
        elif authority_violation is not None:
            self._set_authority_gate_metadata(
                context,
                outcome='blocked',
                source_id=authority_violation.code,
                reason=authority_violation.reason,
                requires_human_confirmation=False,
            )
            return build_result(
                context,
                self.authority_policy_engine.to_computation(authority_violation),
            )

        hierarchy_escalation = None
        authority_decision = self.authority_policy_engine.evaluate(context) if computation is None else None
        if computation is not None:
            pass
        elif authority_decision is not None:
            if self._authority_override_matches(context, authority_decision, approved_override):
                computation = DecisionComputation(
                    outcome='approved',
                    reason='Action resumed after authority contract approval.',
                    policy_basis='runtime.authority_contract',
                    trace=DecisionTrace(
                        source_type='human_override_resume',
                        source_id=approved_override.request_id if approved_override is not None else 'runtime.authority_contract',
                        notes=['Authority contract approval resumed execution.'],
                    ),
                    human_override=approved_override,
                )
                self._set_authority_gate_metadata(
                    context,
                    outcome='approved',
                    source_id='human_override_resume',
                    reason=computation.reason,
                    requires_human_confirmation=False,
                    resumed_override=approved_override,
                )
            else:
                computation = authority_decision
                self._set_authority_gate_metadata(
                    context,
                    outcome=computation.outcome,
                    source_id=computation.trace.source_id,
                    reason=computation.reason,
                    requires_human_confirmation=computation.outcome in {'waiting_human', 'human_required'},
                )
        else:
            self._set_authority_gate_passthrough(context)
            hierarchy_escalation = self._transition_policy_escalation(context) or self.hierarchy_registry.evaluate_escalation(context)
            if hierarchy_escalation is not None:
                context.role_transition['escalated_to'] = hierarchy_escalation.escalated_to
                context.metadata['role_transition'] = dict(context.role_transition)
                context.metadata['role_hierarchy_escalation'] = {
                    'rule_id': hierarchy_escalation.rule_id,
                    'escalated_to': hierarchy_escalation.escalated_to,
                    'reason': hierarchy_escalation.reason,
                    'notes': list(hierarchy_escalation.notes),
                }
                computation = self._resolve_hierarchy_escalation(
                    context=context,
                    hierarchy_escalation=hierarchy_escalation,
                    approved_override=approved_override,
                )
            else:
                computation = self.decision_engine.decide(context, role_document, approved_override=approved_override)

        approver_role = self._override_approver_role(context, hierarchy_escalation)
        if computation.outcome in {'waiting_human', 'human_required'} and computation.human_override is None and approved_override is None:
            computation.human_override = self.human_override.create_state(
                context=context,
                required_by=computation.policy_basis,
                reason=computation.reason,
                approver_role=approver_role,
            )
        elif approved_override is not None and computation.human_override is None:
            computation.human_override = approved_override

        decision_violation = self.runtime_contract_guard.decision_violation(computation, context=context)
        if decision_violation is not None:
            computation = self.runtime_contract_guard.to_computation(decision_violation, phase='decision')

        lock_state = self.lock_manager.get_by_request(context.request_id)
        if lock_state is not None:
            context.metadata['resource_lock'] = lock_state.to_dict()

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

    def _authority_override_matches(
        self,
        context,
        authority_decision: DecisionComputation,
        approved_override: HumanOverrideState | None,
    ) -> bool:
        if authority_decision.outcome != 'human_required' or approved_override is None:
            return False
        return (
            approved_override.status == 'approved'
            and approved_override.active_role == context.role_id
            and approved_override.action == context.action
            and approved_override.required_by == 'runtime.authority_contract'
        )

    def _set_authority_gate_metadata(
        self,
        context,
        *,
        outcome: str,
        source_id: str,
        reason: str,
        requires_human_confirmation: bool,
        resumed_override: HumanOverrideState | None = None,
    ) -> None:
        metadata: dict[str, object] = {
            'gate_triggered': True,
            'outcome': outcome,
            'source_id': source_id,
            'reason': reason,
            'requires_human_confirmation': requires_human_confirmation,
            'decision_mode': 'ai_prepared_human_confirmed' if requires_human_confirmation else 'ai_autonomous',
        }
        if resumed_override is not None:
            metadata['resumed_from_override_request_id'] = resumed_override.request_id
        context.metadata['authority_gate'] = metadata

    def _set_authority_gate_passthrough(self, context) -> None:
        context.metadata['authority_gate'] = {
            'gate_triggered': False,
            'decision_mode': 'policy_fallback',
            'reason': 'Authority contract gate not triggered for this request.',
        }

    def _sync_lock_state(self, result, request_id: str):
        lock_state = self.lock_manager.get_by_request(request_id)
        if lock_state is None:
            return result

        if result.outcome in {"waiting_human", "human_required"}:
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

    def list_workflow_states(
        self,
        *,
        current_state: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, object]]:
        return self.workflow_state_store.list_workflows(current_state=current_state, limit=limit)

    def get_workflow_state(self, workflow_id: str) -> dict[str, object]:
        return self.workflow_state_store.get_workflow(workflow_id)

    def list_runtime_recovery_records(
        self,
        *,
        status: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, object]]:
        return self.runtime_recovery_store.list_records(status=status, limit=limit)

    def list_runtime_dead_letters(self, *, limit: int | None = None) -> list[dict[str, object]]:
        return self.runtime_recovery_store.list_dead_letters(limit=limit)

    def resume_runtime_recovery(self, request_id: str, resumed_by: str):
        record = self.runtime_recovery_store.get_record(request_id)
        if record.status != 'dead_letter':
            raise ValueError('Recovery resume is fail-closed: record is not in dead_letter status.')
        if record.outcome not in {'retryable', 'blocked'}:
            raise ValueError('Recovery resume is fail-closed: only retryable or blocked runtime outcomes are resumable.')

        metadata = dict(record.metadata)
        metadata['recovery_resume_of'] = record.request_id
        metadata['recovery_resumed_by'] = resumed_by
        metadata['recovery_attempt'] = int(metadata.get('recovery_attempt', 0)) + 1

        result = self.process(
            requester=record.requester,
            role_id=record.role_id,
            action=record.action,
            payload=dict(record.payload),
            metadata=metadata,
        )
        resumed_request_id = str(result.metadata.get('request_id', ''))
        self.runtime_recovery_store.mark_resumed(
            record.request_id,
            resumed_by=resumed_by,
            resumed_request_id=resumed_request_id,
            resumed_outcome=result.outcome,
        )
        self.audit_logger.record_event(
            active_role=record.role_id,
            action='runtime_recovery_resume',
            outcome=result.outcome,
            reason='Runtime dead-letter request resumed through governed recovery path.',
            metadata={
                'origin_request_id': record.request_id,
                'resumed_request_id': resumed_request_id,
                'resumed_by': resumed_by,
                'previous_outcome': record.outcome,
            },
        )
        return result

    def list_runtime_evidence(
        self,
        *,
        limit: int | None = None,
        outcome: str | None = None,
        source_type: str | None = None,
    ) -> list[dict[str, object]]:
        return self.audit_logger.list_runtime_evidence(
            limit=limit,
            outcome=outcome,
            source_type=source_type,
        )

    def review_override(self, request_id: str, resolved_by: str, decision: str, note: str | None = None) -> OverrideReviewResult:
        execution_result = None
        released_lock = None
        if decision == "approve":
            state = self.human_override.approve(request_id=request_id, resolved_by=resolved_by, note=note)
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
        if execution_result is not None:
            metadata['execution_result'] = asdict(execution_result)
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
        transition_violation = self._authority_transition_violation(context, state)
        if transition_violation is not None:
            self._set_reasoning_control_metadata(context)
            self._set_execution_plan_metadata(context)
            self._sync_state_flow_result_metadata(transition_violation, context)
            self.request_consistency.complete(context, transition_violation)
            self.audit_logger.record(transition_violation)
            return transition_violation

        self.lock_manager.mark_active(state.origin_request_id)
        self.state_flow_engine.resume_after_human_confirmation(context)
        self._normalize_resume_contract_metadata(context)
        self._set_reasoning_control_metadata(context)
        self._sync_workflow_state_store(context, source='override_resume')
        result = self._evaluate_context(context, approved_override=state)
        result = self._sync_lock_state(result, request_id=context.request_id)
        self._sync_state_flow_result_metadata(result, context, source='override_review')
        self.request_consistency.complete(context, result)
        self.audit_logger.record(result)
        return result

    def _authority_transition_violation(self, context, state: HumanOverrideState) -> DecisionResult | None:
        runtime_flow = context.metadata.get('runtime_state_flow')
        lifecycle = context.metadata.get('role_execution_lifecycle')
        authority_gate = context.metadata.get('authority_gate')
        reasoning_control = context.metadata.get('reasoning_control')

        current_runtime_state = runtime_flow.get('current_state') if isinstance(runtime_flow, dict) else None
        current_role_state = lifecycle.get('current_state') if isinstance(lifecycle, dict) else None

        if current_runtime_state not in {'awaiting_human_confirmation', 'escalated'}:
            return build_result(
                context,
                DecisionComputation(
                    outcome='out_of_order',
                    reason='Override approval is out of order because runtime is not awaiting human confirmation.',
                    policy_basis='runtime.authority_transition',
                    trace=DecisionTrace(
                        source_type='authority_transition',
                        source_id='runtime_state_invalid_for_resume',
                        notes=[f'current_runtime_state={current_runtime_state or "unknown"}'],
                    ),
                ),
            )

        if current_role_state != 'paused_for_human':
            return build_result(
                context,
                DecisionComputation(
                    outcome='out_of_order',
                    reason='Override approval is out of order because role lifecycle is not paused for human review.',
                    policy_basis='runtime.authority_transition',
                    trace=DecisionTrace(
                        source_type='authority_transition',
                        source_id='role_state_invalid_for_resume',
                        notes=[f'current_role_state={current_role_state or "unknown"}'],
                    ),
                ),
            )

        if state.required_by == 'runtime.authority_contract':
            if not (isinstance(authority_gate, dict) and authority_gate.get('requires_human_confirmation') is True):
                return build_result(
                    context,
                    DecisionComputation(
                        outcome='blocked',
                        reason='Override approval is blocked because authority-gate metadata does not support human-confirmed resume.',
                        policy_basis='runtime.authority_transition',
                        trace=DecisionTrace(
                            source_type='authority_transition',
                            source_id='authority_gate_resume_not_allowed',
                            notes=['Authority gate metadata is missing or not human-confirmed.'],
                        ),
                    ),
                )

        if state.required_by == 'runtime.reasoning_control':
            if not (isinstance(reasoning_control, dict) and reasoning_control.get('requires_human_confirmation') is True):
                return build_result(
                    context,
                    DecisionComputation(
                        outcome='blocked',
                        reason='Override approval is blocked because reasoning-control metadata does not support human-confirmed deep-think resume.',
                        policy_basis='runtime.authority_transition',
                        trace=DecisionTrace(
                            source_type='authority_transition',
                            source_id='reasoning_control_resume_not_allowed',
                            notes=['Reasoning control metadata is missing or not human-confirmed.'],
                        ),
                    ),
                )

        return None

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

















