from dataclasses import dataclass
from numbers import Real

from sa_nom_governance.core.decision_models import DecisionComputation, DecisionTrace
from sa_nom_governance.core.execution_context import ExecutionContext


@dataclass(slots=True)
class RuntimeContractViolation:
    code: str
    reason: str
    notes: list[str]


class RuntimeContractGuard:
    """Fail-closed contract checks for runtime context and decision output."""

    _ALLOWED_OUTCOMES = {
        'approved',
        'rejected',
        'waiting_human',
        'human_required',
        'retryable',
        'blocked',
        'suspended',
        'escalated',
        'conflicted',
        'out_of_order',
    }
    _EXCEPTION_OUTCOMES = {'rejected', 'retryable', 'blocked', 'escalated', 'conflicted', 'out_of_order'}
    _POLICY_CONTRACT_KEYS = {
        'required_role',
        'allowed_roles',
        'allowed_actions',
        'required_payload_fields',
        'allowed_outcomes',
        'required_policy_basis_prefix',
        'required_trace_sources',
        'reasoning_mode',
        'max_reasoning_steps',
        'max_runtime_ms',
        'requires_human_for_deep_think',
        'human_required',
        'exception',
        'override_path',
    }
    _ALLOWED_REASONING_MODES = {'standard', 'think', 'deep_think'}
    _HUMAN_REQUIRED_KEYS = {'required', 'required_policy_basis_prefix'}
    _EXCEPTION_KEYS = {'allowed_outcomes', 'required_trace_sources'}
    _OVERRIDE_PATH_KEYS = {'required', 'required_policy_basis_prefix', 'required_approver_role'}
    _TASK_PACKET_KEYS = {
        'packet_id',
        'packet_type',
        'source_role',
        'target_role',
        'workflow_id',
        'step_id',
        'queue_lane',
        'authority_ref',
        'policy_basis_ref',
        'correlation',
        'evidence_refs',
        'packet_status',
    }
    _TASK_PACKET_CORRELATION_KEYS = {'request_id', 'origin_request_id', 'parent_packet_id'}
    _TASK_PACKET_STATUSES = {'prepared', 'dispatched', 'received', 'failed', 'dead_letter', 'resumed'}
    _EXECUTION_PLAN_KEYS = {
        'plan_id',
        'step_id',
        'intent',
        'expected_output',
        'stop_condition',
        'step_index',
        'total_steps',
        'previous_step_id',
        'allowed_previous_steps',
        'allowed_next_steps',
        'checkpoint_required',
        'checkpoint_policy_basis_prefix',
        'handoff_required',
        'handoff_from_role',
        'handoff_target_role',
    }

    def request_violation(
        self,
        *,
        requester: object,
        action: object,
        role_id: object,
        payload: object,
        metadata: object,
    ) -> RuntimeContractViolation | None:
        if not isinstance(requester, str) or not requester.strip():
            return RuntimeContractViolation(
                code='requester_invalid',
                reason='Runtime contract violation: requester must be a non-empty string.',
                notes=['Incoming requester is missing or invalid.'],
            )
        if not isinstance(action, str) or not action.strip():
            return RuntimeContractViolation(
                code='action_invalid',
                reason='Runtime contract violation: action must be a non-empty string.',
                notes=['Incoming action is missing or invalid.'],
            )
        if role_id is not None and (not isinstance(role_id, str) or (role_id != '' and not role_id.strip())):
            return RuntimeContractViolation(
                code='role_invalid',
                reason='Runtime contract violation: role_id must be a non-empty string when provided.',
                notes=['Incoming role_id is present but invalid.'],
            )
        if not isinstance(payload, dict):
            return RuntimeContractViolation(
                code='payload_invalid',
                reason='Runtime contract violation: payload must be an object map.',
                notes=['Incoming payload is not a dictionary.'],
            )
        if metadata is not None and not isinstance(metadata, dict):
            return RuntimeContractViolation(
                code='metadata_invalid',
                reason='Runtime contract violation: metadata must be an object map when provided.',
                notes=['Incoming metadata is present but not a dictionary.'],
            )
        if isinstance(metadata, dict):
            policy_contract_violation = self._policy_contract_shape_violation(metadata.get('policy_contract'))
            if policy_contract_violation is not None:
                return policy_contract_violation
            execution_plan_violation = self._execution_plan_shape_violation(metadata.get('execution_plan'))
            if execution_plan_violation is not None:
                return execution_plan_violation
            task_packet_violation = self._task_packet_shape_violation(metadata.get('task_packet'))
            if task_packet_violation is not None:
                return task_packet_violation
        return None

    def context_violation(self, context: ExecutionContext) -> RuntimeContractViolation | None:
        if not isinstance(context.requester, str) or not context.requester.strip():
            return RuntimeContractViolation(
                code='requester_invalid',
                reason='Runtime contract violation: requester must be a non-empty string.',
                notes=['Context requester is missing or invalid.'],
            )
        if not isinstance(context.action, str) or not context.action.strip():
            return RuntimeContractViolation(
                code='action_invalid',
                reason='Runtime contract violation: action must be a non-empty string.',
                notes=['Context action is missing or invalid.'],
            )
        if not isinstance(context.role_id, str) or not context.role_id.strip():
            return RuntimeContractViolation(
                code='role_invalid',
                reason='Runtime contract violation: role_id must be a non-empty string.',
                notes=['Context role_id is missing or invalid.'],
            )
        if not isinstance(context.payload, dict):
            return RuntimeContractViolation(
                code='payload_invalid',
                reason='Runtime contract violation: payload must be an object map.',
                notes=['Context payload is not a dictionary.'],
            )
        if not isinstance(context.metadata, dict):
            return RuntimeContractViolation(
                code='metadata_invalid',
                reason='Runtime contract violation: metadata must be an object map.',
                notes=['Context metadata is not a dictionary.'],
            )

        policy_contract = context.metadata.get('policy_contract')
        shape_violation = self._policy_contract_shape_violation(policy_contract)
        if shape_violation is not None:
            return shape_violation

        execution_plan = context.metadata.get('execution_plan')
        execution_plan_violation = self._execution_plan_shape_violation(execution_plan)
        if execution_plan_violation is not None:
            return execution_plan_violation
        task_packet = context.metadata.get('task_packet')
        task_packet_violation = self._task_packet_shape_violation(task_packet)
        if task_packet_violation is not None:
            return task_packet_violation

        amount = context.payload.get('amount')
        if amount is not None:
            if not isinstance(amount, Real):
                return RuntimeContractViolation(
                    code='amount_type_invalid',
                    reason='Runtime contract violation: payload.amount must be numeric when present.',
                    notes=['payload.amount exists but is not numeric.'],
                )
            if float(amount) < 0:
                return RuntimeContractViolation(
                    code='amount_negative',
                    reason='Runtime contract violation: payload.amount cannot be negative.',
                    notes=['payload.amount is below zero.'],
                )

        boundary_violation = self._policy_contract_context_boundary_violation(context, policy_contract)
        if boundary_violation is not None:
            return boundary_violation

        return None

    def preflight_violation(
        self,
        context: ExecutionContext,
        *,
        expected_override_approver_role: str | None = None,
    ) -> RuntimeContractViolation | None:
        policy_contract = context.metadata.get('policy_contract')
        execution_plan = context.metadata.get('execution_plan')
        if not isinstance(policy_contract, dict) and not isinstance(execution_plan, dict):
            return None

        supported_human_required_bases = self._supported_human_required_bases(context, policy_contract if isinstance(policy_contract, dict) else None)

        execution_plan_violation = self._execution_plan_preflight_violation(
            execution_plan,
            context=context,
            supported_human_required_bases=supported_human_required_bases,
        )
        if execution_plan_violation is not None:
            return execution_plan_violation

        if not isinstance(policy_contract, dict):
            return None

        human_required_contract = policy_contract.get('human_required')
        if isinstance(human_required_contract, dict):
            required = human_required_contract.get('required') is True
            required_prefix = human_required_contract.get('required_policy_basis_prefix')
            if required and not supported_human_required_bases:
                return RuntimeContractViolation(
                    code='policy_contract_human_required_unavailable',
                    reason='Runtime contract violation: policy contract requires a human-required path, but runtime metadata does not expose one.',
                    notes=['No compatible human-required path is configured for this request.'],
                )
            if isinstance(required_prefix, str) and supported_human_required_bases and not any(
                basis.startswith(required_prefix) for basis in supported_human_required_bases
            ):
                return RuntimeContractViolation(
                    code='policy_contract_human_required_policy_basis_mismatch',
                    reason='Runtime contract violation: configured human-required path does not match policy contract required policy basis prefix.',
                    notes=[f"required prefix: {required_prefix}", f"available paths: {', '.join(supported_human_required_bases)}"],
                )

        override_path_contract = policy_contract.get('override_path')
        if isinstance(override_path_contract, dict) and override_path_contract.get('required') is True:
            if not supported_human_required_bases:
                return RuntimeContractViolation(
                    code='policy_contract_override_path_unavailable',
                    reason='Runtime contract violation: policy contract requires an override path, but runtime metadata does not expose a resumable human-confirmed path.',
                    notes=['Override path requires a compatible human-required runtime boundary.'],
                )
            required_prefix = override_path_contract.get('required_policy_basis_prefix')
            if isinstance(required_prefix, str) and not any(
                basis.startswith(required_prefix) for basis in supported_human_required_bases
            ):
                return RuntimeContractViolation(
                    code='policy_contract_override_policy_basis_mismatch',
                    reason='Runtime contract violation: configured override path does not match policy contract required policy basis prefix.',
                    notes=[f"required prefix: {required_prefix}", f"available paths: {', '.join(supported_human_required_bases)}"],
                )
            required_approver_role = override_path_contract.get('required_approver_role')
            if (
                isinstance(required_approver_role, str)
                and expected_override_approver_role is not None
                and required_approver_role != expected_override_approver_role
            ):
                return RuntimeContractViolation(
                    code='policy_contract_override_approver_role_mismatch',
                    reason='Runtime contract violation: override path approver role does not match policy contract requirement.',
                    notes=[
                        f'required approver role: {required_approver_role}',
                        f'actual approver role: {expected_override_approver_role}',
                    ],
                )

        return None

    def decision_violation(
        self,
        computation: DecisionComputation,
        *,
        context: ExecutionContext | None = None,
    ) -> RuntimeContractViolation | None:
        if computation.outcome not in self._ALLOWED_OUTCOMES:
            return RuntimeContractViolation(
                code='outcome_invalid',
                reason=f"Runtime contract violation: unsupported decision outcome '{computation.outcome}'.",
                notes=['Decision outcome is outside the allowed runtime set.'],
            )

        if not isinstance(computation.policy_basis, str) or not computation.policy_basis.strip():
            return RuntimeContractViolation(
                code='policy_basis_missing',
                reason='Runtime contract violation: policy_basis must be a non-empty string.',
                notes=['Decision policy basis is empty or invalid.'],
            )

        if not computation.trace.source_type or not computation.trace.source_id:
            return RuntimeContractViolation(
                code='trace_invalid',
                reason='Runtime contract violation: decision trace requires source_type and source_id.',
                notes=['Decision trace metadata is incomplete.'],
            )

        policy_contract = context.metadata.get('policy_contract') if context is not None else None
        boundary_violation = self._policy_contract_decision_boundary_violation(computation, policy_contract)
        if boundary_violation is not None:
            return boundary_violation

        return None

    def to_computation(
        self,
        violation: RuntimeContractViolation,
        *,
        phase: str,
    ) -> DecisionComputation:
        return DecisionComputation(
            outcome='escalated',
            reason=violation.reason,
            policy_basis=f'runtime.contract.{phase}',
            trace=DecisionTrace(
                source_type='runtime_contract',
                source_id=violation.code,
                notes=list(violation.notes),
            ),
        )

    def reasoning_profile(self, context: ExecutionContext) -> dict[str, object]:
        policy_contract = context.metadata.get('policy_contract')
        if not isinstance(policy_contract, dict):
            return {
                'reasoning_mode': 'standard',
                'max_reasoning_steps': 1,
                'max_runtime_ms': None,
                'requires_human_confirmation': False,
            }

        reasoning_mode = str(policy_contract.get('reasoning_mode') or 'standard')
        max_reasoning_steps = int(policy_contract.get('max_reasoning_steps', 1 if reasoning_mode == 'standard' else 8))
        max_runtime_ms = policy_contract.get('max_runtime_ms')
        requires_human_confirmation = (
            reasoning_mode == 'deep_think' and bool(policy_contract.get('requires_human_for_deep_think', False))
        )

        return {
            'reasoning_mode': reasoning_mode,
            'max_reasoning_steps': max_reasoning_steps,
            'max_runtime_ms': int(max_runtime_ms) if isinstance(max_runtime_ms, int) else None,
            'requires_human_confirmation': requires_human_confirmation,
        }

    def normalized_execution_plan_contract(self, execution_plan: object) -> dict[str, object] | None:
        if not isinstance(execution_plan, dict):
            return None
        return {key: execution_plan[key] for key in self._EXECUTION_PLAN_KEYS if key in execution_plan}

    def normalized_task_packet_contract(self, task_packet: object) -> dict[str, object] | None:
        if not isinstance(task_packet, dict):
            return None
        return {key: task_packet[key] for key in self._TASK_PACKET_KEYS if key in task_packet}

    def task_packet_profile(self, context: ExecutionContext) -> dict[str, object] | None:
        execution_plan = context.metadata.get('execution_plan')
        task_packet = context.metadata.get('task_packet')
        if not isinstance(execution_plan, dict) and not isinstance(task_packet, dict):
            return None

        packet: dict[str, object] = dict(task_packet) if isinstance(task_packet, dict) else {}
        plan: dict[str, object] = dict(execution_plan) if isinstance(execution_plan, dict) else {}
        decision_queue_value = context.metadata.get('decision_queue')
        decision_queue: dict[str, object] = dict(decision_queue_value) if isinstance(decision_queue_value, dict) else {}
        authority_gate_value = context.metadata.get('authority_gate')
        authority_gate: dict[str, object] = dict(authority_gate_value) if isinstance(authority_gate_value, dict) else {}
        correlation_value = packet.get('correlation')
        correlation: dict[str, object] = dict(correlation_value) if isinstance(correlation_value, dict) else {}

        source_role = str(packet.get('source_role') or context.role_id)
        target_role = str(packet.get('target_role') or plan.get('handoff_target_role') or context.role_id)
        workflow_id = str(packet.get('workflow_id') or plan.get('plan_id') or context.request_id)
        step_id = str(packet.get('step_id') or plan.get('step_id') or context.action)
        packet_status = packet.get('packet_status')
        if not isinstance(packet_status, str):
            packet_status = 'dispatched' if target_role != source_role else 'prepared'

        queue_lane = packet.get('queue_lane')
        if not isinstance(queue_lane, str):
            queue_lane = decision_queue.get('queue_lane') if isinstance(decision_queue.get('queue_lane'), str) else None

        authority_ref = packet.get('authority_ref')
        if not isinstance(authority_ref, str):
            authority_ref = authority_gate.get('source_id') if isinstance(authority_gate.get('source_id'), str) else None

        policy_basis_ref = packet.get('policy_basis_ref')
        if not isinstance(policy_basis_ref, str):
            policy_basis_ref = authority_gate.get('reason') if isinstance(authority_gate.get('reason'), str) else None

        evidence_refs_value = packet.get('evidence_refs')
        evidence_refs: list[object] = evidence_refs_value if isinstance(evidence_refs_value, list) else []
        valid_evidence_refs = [item for item in evidence_refs if isinstance(item, str) and item.strip()]
        if context.request_id not in valid_evidence_refs:
            valid_evidence_refs.append(context.request_id)

        packet_id = packet.get('packet_id')
        if not isinstance(packet_id, str) or not packet_id.strip():
            packet_id = f'packet-{context.request_id}'

        packet_type = packet.get('packet_type')
        if not isinstance(packet_type, str) or not packet_type.strip():
            packet_type = 'runtime_step'

        return {
            'packet_id': packet_id,
            'packet_type': packet_type,
            'source_role': source_role,
            'target_role': target_role,
            'workflow_id': workflow_id,
            'step_id': step_id,
            'queue_lane': queue_lane,
            'authority_ref': authority_ref,
            'policy_basis_ref': policy_basis_ref,
            'correlation': {
                'request_id': str(correlation.get('request_id') or context.request_id),
                'origin_request_id': self._optional_str(correlation.get('origin_request_id') or context.metadata.get('recovery_resume_of')),
                'parent_packet_id': self._optional_str(correlation.get('parent_packet_id')),
            },
            'evidence_refs': valid_evidence_refs,
            'packet_status': packet_status,
        }

    def execution_plan_profile(self, context: ExecutionContext) -> dict[str, object] | None:
        execution_plan = context.metadata.get('execution_plan')
        if not isinstance(execution_plan, dict):
            return None

        step_index = execution_plan.get('step_index')
        total_steps = execution_plan.get('total_steps')
        previous_step_id = execution_plan.get('previous_step_id')
        allowed_previous_steps = execution_plan.get('allowed_previous_steps')
        handoff_required = execution_plan.get('handoff_required') is True
        handoff_from_role = execution_plan.get('handoff_from_role') if isinstance(execution_plan.get('handoff_from_role'), str) else None
        handoff_target_role = execution_plan.get('handoff_target_role') if isinstance(execution_plan.get('handoff_target_role'), str) else None
        return {
            'plan_id': str(execution_plan['plan_id']),
            'step_id': str(execution_plan['step_id']),
            'intent': str(execution_plan['intent']),
            'expected_output': str(execution_plan['expected_output']),
            'stop_condition': str(execution_plan['stop_condition']),
            'step_index': int(step_index) if isinstance(step_index, int) else 1,
            'total_steps': int(total_steps) if isinstance(total_steps, int) else None,
            'previous_step_id': previous_step_id if isinstance(previous_step_id, str) else None,
            'allowed_previous_steps': list(allowed_previous_steps) if isinstance(allowed_previous_steps, list) else [],
            'allowed_next_steps': list(execution_plan.get('allowed_next_steps', [])) if isinstance(execution_plan.get('allowed_next_steps'), list) else [],
            'checkpoint_required': execution_plan.get('checkpoint_required') is True,
            'checkpoint_policy_basis_prefix': execution_plan.get('checkpoint_policy_basis_prefix') if isinstance(execution_plan.get('checkpoint_policy_basis_prefix'), str) else None,
            'handoff_required': handoff_required,
            'handoff_from_role': handoff_from_role,
            'handoff_target_role': handoff_target_role,
            'active_role': context.role_id,
            'routing_status': self._execution_plan_routing_status(context, execution_plan),
            'plan_status': 'handoff_active' if handoff_required else 'active_step',
        }

    def _policy_contract_shape_violation(self, policy_contract: object) -> RuntimeContractViolation | None:
        if policy_contract is None:
            return None
        if not isinstance(policy_contract, dict):
            return RuntimeContractViolation(
                code='policy_contract_invalid_type',
                reason='Runtime contract violation: metadata.policy_contract must be an object map when provided.',
                notes=['metadata.policy_contract is present but not a dictionary.'],
            )
        unknown_keys = sorted(key for key in policy_contract if key not in self._POLICY_CONTRACT_KEYS)
        if unknown_keys:
            return RuntimeContractViolation(
                code='policy_contract_unknown_keys',
                reason='Runtime contract violation: metadata.policy_contract contains unsupported keys.',
                notes=[f"unsupported keys: {', '.join(unknown_keys)}"],
            )
        if 'required_role' in policy_contract:
            required_role = policy_contract['required_role']
            if not isinstance(required_role, str) or not required_role.strip():
                return RuntimeContractViolation(
                    code='policy_contract_required_role_invalid',
                    reason='Runtime contract violation: policy_contract.required_role must be a non-empty string.',
                    notes=['metadata.policy_contract.required_role is invalid.'],
                )
        if 'required_policy_basis_prefix' in policy_contract:
            prefix = policy_contract['required_policy_basis_prefix']
            if not isinstance(prefix, str) or not prefix.strip():
                return RuntimeContractViolation(
                    code='policy_contract_policy_prefix_invalid',
                    reason='Runtime contract violation: policy_contract.required_policy_basis_prefix must be a non-empty string.',
                    notes=['metadata.policy_contract.required_policy_basis_prefix is invalid.'],
                )
        for key in (
            'allowed_roles',
            'allowed_actions',
            'required_payload_fields',
            'allowed_outcomes',
            'required_trace_sources',
        ):
            if key in policy_contract and not self._string_list(policy_contract[key]):
                return RuntimeContractViolation(
                    code=f'policy_contract_{key}_invalid',
                    reason=f'Runtime contract violation: policy_contract.{key} must be a list of non-empty strings.',
                    notes=[f'metadata.policy_contract.{key} has invalid shape.'],
                )
        reasoning_mode = policy_contract.get('reasoning_mode')
        if reasoning_mode is not None and reasoning_mode not in self._ALLOWED_REASONING_MODES:
            return RuntimeContractViolation(
                code='policy_contract_reasoning_mode_invalid',
                reason='Runtime contract violation: policy_contract.reasoning_mode must be standard, think, or deep_think.',
                notes=['metadata.policy_contract.reasoning_mode is invalid.'],
            )
        for key in ('max_reasoning_steps', 'max_runtime_ms'):
            if key in policy_contract:
                value = policy_contract[key]
                if not isinstance(value, int) or value <= 0:
                    return RuntimeContractViolation(
                        code=f'policy_contract_{key}_invalid',
                        reason=f'Runtime contract violation: policy_contract.{key} must be a positive integer.',
                        notes=[f'metadata.policy_contract.{key} is invalid.'],
                    )
        requires_human_for_deep_think = policy_contract.get('requires_human_for_deep_think')
        if requires_human_for_deep_think is not None and not isinstance(requires_human_for_deep_think, bool):
            return RuntimeContractViolation(
                code='policy_contract_requires_human_for_deep_think_invalid',
                reason='Runtime contract violation: policy_contract.requires_human_for_deep_think must be boolean when provided.',
                notes=['metadata.policy_contract.requires_human_for_deep_think is invalid.'],
            )

        nested_violation = self._nested_policy_contract_shape_violation(
            'human_required',
            policy_contract.get('human_required'),
            self._HUMAN_REQUIRED_KEYS,
        )
        if nested_violation is not None:
            return nested_violation
        nested_violation = self._nested_policy_contract_shape_violation(
            'exception',
            policy_contract.get('exception'),
            self._EXCEPTION_KEYS,
        )
        if nested_violation is not None:
            return nested_violation
        nested_violation = self._nested_policy_contract_shape_violation(
            'override_path',
            policy_contract.get('override_path'),
            self._OVERRIDE_PATH_KEYS,
        )
        if nested_violation is not None:
            return nested_violation

        human_required_contract = policy_contract.get('human_required')
        if isinstance(human_required_contract, dict):
            required = human_required_contract.get('required')
            if required is not None and not isinstance(required, bool):
                return RuntimeContractViolation(
                    code='policy_contract_human_required_required_invalid',
                    reason='Runtime contract violation: policy_contract.human_required.required must be boolean when provided.',
                    notes=['metadata.policy_contract.human_required.required is invalid.'],
                )
            required_prefix = human_required_contract.get('required_policy_basis_prefix')
            if required_prefix is not None and (not isinstance(required_prefix, str) or not required_prefix.strip()):
                return RuntimeContractViolation(
                    code='policy_contract_human_required_policy_prefix_invalid',
                    reason='Runtime contract violation: policy_contract.human_required.required_policy_basis_prefix must be a non-empty string.',
                    notes=['metadata.policy_contract.human_required.required_policy_basis_prefix is invalid.'],
                )

        exception_contract = policy_contract.get('exception')
        if isinstance(exception_contract, dict):
            allowed_outcomes = exception_contract.get('allowed_outcomes')
            if allowed_outcomes is not None:
                if not self._string_list(allowed_outcomes):
                    return RuntimeContractViolation(
                        code='policy_contract_exception_allowed_outcomes_invalid',
                        reason='Runtime contract violation: policy_contract.exception.allowed_outcomes must be a list of non-empty strings.',
                        notes=['metadata.policy_contract.exception.allowed_outcomes has invalid shape.'],
                    )
                invalid_outcomes = sorted(outcome for outcome in allowed_outcomes if outcome not in self._EXCEPTION_OUTCOMES)
                if invalid_outcomes:
                    return RuntimeContractViolation(
                        code='policy_contract_exception_allowed_outcomes_unsupported',
                        reason='Runtime contract violation: policy_contract.exception.allowed_outcomes may only contain exception outcomes.',
                        notes=[f"unsupported outcomes: {', '.join(invalid_outcomes)}"],
                    )
            required_trace_sources = exception_contract.get('required_trace_sources')
            if required_trace_sources is not None and not self._string_list(required_trace_sources):
                return RuntimeContractViolation(
                    code='policy_contract_exception_required_trace_sources_invalid',
                    reason='Runtime contract violation: policy_contract.exception.required_trace_sources must be a list of non-empty strings.',
                    notes=['metadata.policy_contract.exception.required_trace_sources has invalid shape.'],
                )

        override_path_contract = policy_contract.get('override_path')
        if isinstance(override_path_contract, dict):
            required = override_path_contract.get('required')
            if required is not None and not isinstance(required, bool):
                return RuntimeContractViolation(
                    code='policy_contract_override_required_invalid',
                    reason='Runtime contract violation: policy_contract.override_path.required must be boolean when provided.',
                    notes=['metadata.policy_contract.override_path.required is invalid.'],
                )
            required_prefix = override_path_contract.get('required_policy_basis_prefix')
            if required_prefix is not None and (not isinstance(required_prefix, str) or not required_prefix.strip()):
                return RuntimeContractViolation(
                    code='policy_contract_override_policy_prefix_invalid',
                    reason='Runtime contract violation: policy_contract.override_path.required_policy_basis_prefix must be a non-empty string.',
                    notes=['metadata.policy_contract.override_path.required_policy_basis_prefix is invalid.'],
                )
            required_approver_role = override_path_contract.get('required_approver_role')
            if required_approver_role is not None and (
                not isinstance(required_approver_role, str) or not required_approver_role.strip()
            ):
                return RuntimeContractViolation(
                    code='policy_contract_override_approver_role_invalid',
                    reason='Runtime contract violation: policy_contract.override_path.required_approver_role must be a non-empty string.',
                    notes=['metadata.policy_contract.override_path.required_approver_role is invalid.'],
                )
        return None

    def _execution_plan_shape_violation(self, execution_plan: object) -> RuntimeContractViolation | None:
        if execution_plan is None:
            return None
        if not isinstance(execution_plan, dict):
            return RuntimeContractViolation(
                code='execution_plan_invalid_type',
                reason='Runtime contract violation: metadata.execution_plan must be an object map when provided.',
                notes=['metadata.execution_plan is present but not a dictionary.'],
            )

        unknown_keys = sorted(key for key in execution_plan if key not in self._EXECUTION_PLAN_KEYS)
        if unknown_keys:
            return RuntimeContractViolation(
                code='execution_plan_unknown_keys',
                reason='Runtime contract violation: metadata.execution_plan contains unsupported keys.',
                notes=[f"unsupported keys: {', '.join(unknown_keys)}"],
            )

        for key in ('plan_id', 'step_id', 'intent', 'expected_output', 'stop_condition'):
            value = execution_plan.get(key)
            if not isinstance(value, str) or not value.strip():
                return RuntimeContractViolation(
                    code=f'execution_plan_{key}_invalid',
                    reason=f'Runtime contract violation: execution_plan.{key} must be a non-empty string.',
                    notes=[f'metadata.execution_plan.{key} is invalid.'],
                )

        for key in ('step_index', 'total_steps'):
            value = execution_plan.get(key)
            if value is not None and (not isinstance(value, int) or value <= 0):
                return RuntimeContractViolation(
                    code=f'execution_plan_{key}_invalid',
                    reason=f'Runtime contract violation: execution_plan.{key} must be a positive integer when provided.',
                    notes=[f'metadata.execution_plan.{key} is invalid.'],
                )

        step_index = execution_plan.get('step_index')
        total_steps = execution_plan.get('total_steps')
        if isinstance(step_index, int) and isinstance(total_steps, int) and step_index > total_steps:
            return RuntimeContractViolation(
                code='execution_plan_step_index_out_of_range',
                reason='Runtime contract violation: execution_plan.step_index cannot exceed execution_plan.total_steps.',
                notes=[f'step_index={step_index}', f'total_steps={total_steps}'],
            )

        previous_step_id = execution_plan.get('previous_step_id')
        if previous_step_id is not None and (not isinstance(previous_step_id, str) or not previous_step_id.strip()):
            return RuntimeContractViolation(
                code='execution_plan_previous_step_id_invalid',
                reason='Runtime contract violation: execution_plan.previous_step_id must be a non-empty string when provided.',
                notes=['metadata.execution_plan.previous_step_id is invalid.'],
            )

        for key in ('allowed_previous_steps', 'allowed_next_steps'):
            value = execution_plan.get(key)
            if value is not None and not self._string_list(value):
                return RuntimeContractViolation(
                    code=f'execution_plan_{key}_invalid',
                    reason=f'Runtime contract violation: execution_plan.{key} must be a list of non-empty strings when provided.',
                    notes=[f'metadata.execution_plan.{key} has invalid shape.'],
                )

        checkpoint_required = execution_plan.get('checkpoint_required')
        if checkpoint_required is not None and not isinstance(checkpoint_required, bool):
            return RuntimeContractViolation(
                code='execution_plan_checkpoint_required_invalid',
                reason='Runtime contract violation: execution_plan.checkpoint_required must be boolean when provided.',
                notes=['metadata.execution_plan.checkpoint_required is invalid.'],
            )

        checkpoint_prefix = execution_plan.get('checkpoint_policy_basis_prefix')
        if checkpoint_prefix is not None and (not isinstance(checkpoint_prefix, str) or not checkpoint_prefix.strip()):
            return RuntimeContractViolation(
                code='execution_plan_checkpoint_policy_basis_prefix_invalid',
                reason='Runtime contract violation: execution_plan.checkpoint_policy_basis_prefix must be a non-empty string when provided.',
                notes=['metadata.execution_plan.checkpoint_policy_basis_prefix is invalid.'],
            )

        handoff_required = execution_plan.get('handoff_required')
        if handoff_required is not None and not isinstance(handoff_required, bool):
            return RuntimeContractViolation(
                code='execution_plan_handoff_required_invalid',
                reason='Runtime contract violation: execution_plan.handoff_required must be boolean when provided.',
                notes=['metadata.execution_plan.handoff_required is invalid.'],
            )

        handoff_from_role = execution_plan.get('handoff_from_role')
        if handoff_from_role is not None and (not isinstance(handoff_from_role, str) or not handoff_from_role.strip()):
            return RuntimeContractViolation(
                code='execution_plan_handoff_from_role_invalid',
                reason='Runtime contract violation: execution_plan.handoff_from_role must be a non-empty string when provided.',
                notes=['metadata.execution_plan.handoff_from_role is invalid.'],
            )

        handoff_target_role = execution_plan.get('handoff_target_role')
        if handoff_target_role is not None and (not isinstance(handoff_target_role, str) or not handoff_target_role.strip()):
            return RuntimeContractViolation(
                code='execution_plan_handoff_target_role_invalid',
                reason='Runtime contract violation: execution_plan.handoff_target_role must be a non-empty string when provided.',
                notes=['metadata.execution_plan.handoff_target_role is invalid.'],
            )
        if handoff_required is True and not isinstance(handoff_target_role, str):
            return RuntimeContractViolation(
                code='execution_plan_handoff_target_role_required',
                reason='Runtime contract violation: execution_plan.handoff_target_role is required when handoff_required is true.',
                notes=['metadata.execution_plan.handoff_required requires a target role.'],
            )

        return None

    def _task_packet_shape_violation(self, task_packet: object) -> RuntimeContractViolation | None:
        if task_packet is None:
            return None
        if not isinstance(task_packet, dict):
            return RuntimeContractViolation(
                code='task_packet_invalid_type',
                reason='Runtime contract violation: metadata.task_packet must be an object map when provided.',
                notes=['metadata.task_packet is present but not a dictionary.'],
            )

        unknown_keys = sorted(key for key in task_packet if key not in self._TASK_PACKET_KEYS)
        if unknown_keys:
            return RuntimeContractViolation(
                code='task_packet_unknown_keys',
                reason='Runtime contract violation: metadata.task_packet contains unsupported keys.',
                notes=[f"unsupported keys: {', '.join(unknown_keys)}"],
            )

        for key in ('packet_id', 'packet_type', 'source_role', 'target_role', 'workflow_id', 'step_id'):
            value = task_packet.get(key)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                return RuntimeContractViolation(
                    code=f'task_packet_{key}_invalid',
                    reason=f'Runtime contract violation: task_packet.{key} must be a non-empty string when provided.',
                    notes=[f'metadata.task_packet.{key} is invalid.'],
                )

        queue_lane = task_packet.get('queue_lane')
        if queue_lane is not None and (not isinstance(queue_lane, str) or not queue_lane.strip()):
            return RuntimeContractViolation(
                code='task_packet_queue_lane_invalid',
                reason='Runtime contract violation: task_packet.queue_lane must be a non-empty string when provided.',
                notes=['metadata.task_packet.queue_lane is invalid.'],
            )

        for key in ('authority_ref', 'policy_basis_ref'):
            value = task_packet.get(key)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                return RuntimeContractViolation(
                    code=f'task_packet_{key}_invalid',
                    reason=f'Runtime contract violation: task_packet.{key} must be a non-empty string when provided.',
                    notes=[f'metadata.task_packet.{key} is invalid.'],
                )

        correlation = task_packet.get('correlation')
        if correlation is not None:
            if not isinstance(correlation, dict):
                return RuntimeContractViolation(
                    code='task_packet_correlation_invalid',
                    reason='Runtime contract violation: task_packet.correlation must be an object map when provided.',
                    notes=['metadata.task_packet.correlation is invalid.'],
                )
            unknown_correlation_keys = sorted(key for key in correlation if key not in self._TASK_PACKET_CORRELATION_KEYS)
            if unknown_correlation_keys:
                return RuntimeContractViolation(
                    code='task_packet_correlation_unknown_keys',
                    reason='Runtime contract violation: task_packet.correlation contains unsupported keys.',
                    notes=[f"unsupported keys: {', '.join(unknown_correlation_keys)}"],
                )
            for key, value in correlation.items():
                if value is not None and (not isinstance(value, str) or not value.strip()):
                    return RuntimeContractViolation(
                        code=f'task_packet_correlation_{key}_invalid',
                        reason=f'Runtime contract violation: task_packet.correlation.{key} must be a non-empty string when provided.',
                        notes=[f'metadata.task_packet.correlation.{key} is invalid.'],
                    )

        evidence_refs = task_packet.get('evidence_refs')
        if evidence_refs is not None and not self._string_list(evidence_refs):
            return RuntimeContractViolation(
                code='task_packet_evidence_refs_invalid',
                reason='Runtime contract violation: task_packet.evidence_refs must be a list of non-empty strings when provided.',
                notes=['metadata.task_packet.evidence_refs has invalid shape.'],
            )

        packet_status = task_packet.get('packet_status')
        if packet_status is not None and packet_status not in self._TASK_PACKET_STATUSES:
            return RuntimeContractViolation(
                code='task_packet_status_invalid',
                reason='Runtime contract violation: task_packet.packet_status contains unsupported state.',
                notes=[f'unsupported packet_status: {packet_status}'],
            )
        return None

    def _execution_plan_preflight_violation(
        self,
        execution_plan: object,
        *,
        context: ExecutionContext,
        supported_human_required_bases: list[str],
    ) -> RuntimeContractViolation | None:
        if not isinstance(execution_plan, dict):
            return None

        if execution_plan.get('checkpoint_required') is True:
            if not supported_human_required_bases:
                return RuntimeContractViolation(
                    code='execution_plan_checkpoint_unavailable',
                    reason='Runtime contract violation: execution_plan requires a governed human checkpoint, but no compatible human-required runtime path is available.',
                    notes=['execution_plan.checkpoint_required is true without a compatible human boundary.'],
                )

            required_prefix = execution_plan.get('checkpoint_policy_basis_prefix')
            if isinstance(required_prefix, str) and not any(
                basis.startswith(required_prefix) for basis in supported_human_required_bases
            ):
                return RuntimeContractViolation(
                    code='execution_plan_checkpoint_policy_basis_mismatch',
                    reason='Runtime contract violation: execution_plan checkpoint policy basis does not match the available human-required runtime path.',
                    notes=[f"required prefix: {required_prefix}", f"available paths: {', '.join(supported_human_required_bases)}"],
                )

        previous_step_id = execution_plan.get('previous_step_id')
        allowed_previous_steps = execution_plan.get('allowed_previous_steps')
        if isinstance(previous_step_id, str) and isinstance(allowed_previous_steps, list) and previous_step_id not in allowed_previous_steps:
            return RuntimeContractViolation(
                code='execution_plan_previous_step_outside_allowlist',
                reason='Runtime contract violation: execution_plan.previous_step_id is outside execution_plan.allowed_previous_steps.',
                notes=[f'previous_step_id={previous_step_id}', f"allowed_previous_steps={', '.join(allowed_previous_steps)}"],
            )

        if execution_plan.get('handoff_required') is not True:
            return None

        handoff_target_role = execution_plan.get('handoff_target_role')
        if isinstance(handoff_target_role, str) and context.role_id != handoff_target_role:
            return RuntimeContractViolation(
                code='execution_plan_handoff_target_role_mismatch',
                reason='Runtime contract violation: execution_plan handoff target role does not match the active runtime role.',
                notes=[f'required target role: {handoff_target_role}', f'active role: {context.role_id}'],
            )

        transition = context.role_transition if isinstance(context.role_transition, dict) else {}
        previous_role = transition.get('previous_role') if isinstance(transition.get('previous_role'), str) else None
        if previous_role is None:
            previous_role = context.metadata.get('current_role') if isinstance(context.metadata.get('current_role'), str) else None
        if previous_role is None:
            previous_role = context.metadata.get('previous_role') if isinstance(context.metadata.get('previous_role'), str) else None

        if previous_role is None:
            return RuntimeContractViolation(
                code='execution_plan_handoff_context_missing',
                reason='Runtime contract violation: execution_plan requires a routed handoff, but previous role context is missing.',
                notes=['handoff_required is true without previous_role/current_role context.'],
            )

        handoff_from_role = execution_plan.get('handoff_from_role')
        if isinstance(handoff_from_role, str) and previous_role != handoff_from_role:
            return RuntimeContractViolation(
                code='execution_plan_handoff_source_role_mismatch',
                reason='Runtime contract violation: execution_plan handoff source role does not match the routed previous role.',
                notes=[f'required source role: {handoff_from_role}', f'previous role: {previous_role}'],
            )

        if previous_role == context.role_id:
            return RuntimeContractViolation(
                code='execution_plan_handoff_not_transitioned',
                reason='Runtime contract violation: execution_plan requires a role handoff, but runtime is still executing under the same role.',
                notes=[f'previous role: {previous_role}', f'active role: {context.role_id}'],
            )

        return None

    def _policy_contract_context_boundary_violation(
        self,
        context: ExecutionContext,
        policy_contract: object,
    ) -> RuntimeContractViolation | None:
        if not isinstance(policy_contract, dict):
            return None

        required_role = policy_contract.get('required_role')
        if isinstance(required_role, str) and context.role_id != required_role:
            return RuntimeContractViolation(
                code='policy_contract_required_role_mismatch',
                reason=f"Runtime contract violation: role_id '{context.role_id}' does not match required role '{required_role}'.",
                notes=['Request role is outside policy contract required_role boundary.'],
            )

        allowed_roles = policy_contract.get('allowed_roles')
        if isinstance(allowed_roles, list) and context.role_id not in allowed_roles:
            return RuntimeContractViolation(
                code='policy_contract_role_outside_allowlist',
                reason=f"Runtime contract violation: role_id '{context.role_id}' is outside policy contract allowed_roles.",
                notes=['Request role is outside allowed_roles boundary.'],
            )

        allowed_actions = policy_contract.get('allowed_actions')
        if isinstance(allowed_actions, list) and context.action not in allowed_actions:
            return RuntimeContractViolation(
                code='policy_contract_action_outside_allowlist',
                reason=f"Runtime contract violation: action '{context.action}' is outside policy contract allowed_actions.",
                notes=['Request action is outside allowed_actions boundary.'],
            )

        required_payload_fields = policy_contract.get('required_payload_fields')
        if isinstance(required_payload_fields, list):
            missing_fields = [field for field in required_payload_fields if field not in context.payload]
            if missing_fields:
                return RuntimeContractViolation(
                    code='policy_contract_missing_payload_fields',
                    reason='Runtime contract violation: required payload fields are missing for policy contract.',
                    notes=[f"missing fields: {', '.join(missing_fields)}"],
                )

        return None

    def _policy_contract_decision_boundary_violation(
        self,
        computation: DecisionComputation,
        policy_contract: object,
    ) -> RuntimeContractViolation | None:
        if not isinstance(policy_contract, dict):
            return None

        allowed_outcomes = policy_contract.get('allowed_outcomes')
        if isinstance(allowed_outcomes, list) and computation.outcome not in allowed_outcomes:
            return RuntimeContractViolation(
                code='policy_contract_outcome_outside_allowlist',
                reason=f"Runtime contract violation: outcome '{computation.outcome}' is outside policy contract allowed_outcomes.",
                notes=['Decision outcome is outside allowed_outcomes boundary.'],
            )

        required_prefix = policy_contract.get('required_policy_basis_prefix')
        if isinstance(required_prefix, str) and not computation.policy_basis.startswith(required_prefix):
            return RuntimeContractViolation(
                code='policy_contract_policy_basis_prefix_mismatch',
                reason='Runtime contract violation: decision policy_basis does not match required policy basis prefix.',
                notes=[f"required prefix: {required_prefix}", f"actual policy_basis: {computation.policy_basis}"],
            )

        required_trace_sources = policy_contract.get('required_trace_sources')
        if isinstance(required_trace_sources, list) and computation.trace.source_type not in required_trace_sources:
            return RuntimeContractViolation(
                code='policy_contract_trace_source_outside_allowlist',
                reason=f"Runtime contract violation: trace source_type '{computation.trace.source_type}' is outside policy contract required_trace_sources.",
                notes=['Decision trace source_type is outside required_trace_sources boundary.'],
            )

        human_required_contract = policy_contract.get('human_required')
        if isinstance(human_required_contract, dict) and human_required_contract.get('required') is True:
            override_completed = computation.outcome == 'approved' and self._human_override_status(computation) == 'approved'
            if computation.outcome not in {'waiting_human', 'human_required'} and not override_completed:
                return RuntimeContractViolation(
                    code='policy_contract_human_required_not_triggered',
                    reason='Runtime contract violation: policy contract required a human-required outcome, but runtime completed without entering that boundary.',
                    notes=[f"actual outcome: {computation.outcome}"],
                )
            required_human_prefix = human_required_contract.get('required_policy_basis_prefix')
            if isinstance(required_human_prefix, str) and not computation.policy_basis.startswith(required_human_prefix):
                return RuntimeContractViolation(
                    code='policy_contract_human_required_policy_basis_mismatch',
                    reason='Runtime contract violation: human-required outcome does not match the required policy basis prefix.',
                    notes=[f"required prefix: {required_human_prefix}", f"actual policy_basis: {computation.policy_basis}"],
                )

        exception_contract = policy_contract.get('exception')
        if isinstance(exception_contract, dict) and computation.outcome in self._EXCEPTION_OUTCOMES:
            exception_allowed_outcomes = exception_contract.get('allowed_outcomes')
            if isinstance(exception_allowed_outcomes, list) and computation.outcome not in exception_allowed_outcomes:
                return RuntimeContractViolation(
                    code='policy_contract_exception_outcome_outside_allowlist',
                    reason=f"Runtime contract violation: exception outcome '{computation.outcome}' is outside policy contract exception.allowed_outcomes.",
                    notes=['Exception outcome is outside exception.allowed_outcomes boundary.'],
                )
            exception_trace_sources = exception_contract.get('required_trace_sources')
            if isinstance(exception_trace_sources, list) and computation.trace.source_type not in exception_trace_sources:
                return RuntimeContractViolation(
                    code='policy_contract_exception_trace_source_outside_allowlist',
                    reason=f"Runtime contract violation: exception trace source_type '{computation.trace.source_type}' is outside policy contract exception.required_trace_sources.",
                    notes=['Exception trace source_type is outside exception.required_trace_sources boundary.'],
                )

        override_path_contract = policy_contract.get('override_path')
        if isinstance(override_path_contract, dict) and override_path_contract.get('required') is True:
            override_completed = computation.outcome == 'approved' and self._human_override_status(computation) == 'approved'
            if computation.outcome not in {'waiting_human', 'human_required'} and not override_completed:
                return RuntimeContractViolation(
                    code='policy_contract_override_path_not_triggered',
                    reason='Runtime contract violation: policy contract required an override path, but runtime did not enter a resumable human-confirmed state.',
                    notes=[f"actual outcome: {computation.outcome}"],
                )
            required_override_prefix = override_path_contract.get('required_policy_basis_prefix')
            if isinstance(required_override_prefix, str) and not computation.policy_basis.startswith(required_override_prefix):
                return RuntimeContractViolation(
                    code='policy_contract_override_policy_basis_mismatch',
                    reason='Runtime contract violation: override path does not match the required policy basis prefix.',
                    notes=[f"required prefix: {required_override_prefix}", f"actual policy_basis: {computation.policy_basis}"],
                )
            required_approver_role = override_path_contract.get('required_approver_role')
            actual_approver_role = self._human_override_approver_role(computation)
            if isinstance(required_approver_role, str) and actual_approver_role != required_approver_role:
                return RuntimeContractViolation(
                    code='policy_contract_override_approver_role_mismatch',
                    reason='Runtime contract violation: created override path approver role does not match policy contract requirement.',
                    notes=[
                        f'required approver role: {required_approver_role}',
                        f'actual approver role: {actual_approver_role or "missing"}',
                    ],
                )

        return None

    def _execution_plan_routing_status(self, context: ExecutionContext, execution_plan: dict[str, object]) -> str:
        if execution_plan.get('handoff_required') is not True:
            return 'active_step'

        transition = context.role_transition if isinstance(context.role_transition, dict) else {}
        previous_role = transition.get('previous_role') if isinstance(transition.get('previous_role'), str) else None
        if previous_role is None:
            previous_role = context.metadata.get('current_role') if isinstance(context.metadata.get('current_role'), str) else None
        if previous_role is None:
            previous_role = context.metadata.get('previous_role') if isinstance(context.metadata.get('previous_role'), str) else None

        handoff_target_role = execution_plan.get('handoff_target_role')
        if isinstance(previous_role, str) and isinstance(handoff_target_role, str) and previous_role != context.role_id and handoff_target_role == context.role_id:
            return 'handoff_active'
        return 'handoff_pending'

    def _supported_human_required_bases(
        self,
        context: ExecutionContext,
        policy_contract: dict[str, object] | None,
    ) -> list[str]:
        supported: list[str] = []
        authority_contract = context.metadata.get('authority_contract')
        if isinstance(authority_contract, dict) and authority_contract.get('approval_gate') == 'human_required':
            supported.append('runtime.authority_contract')

        reasoning_mode = policy_contract.get('reasoning_mode') if isinstance(policy_contract, dict) else None
        requires_human_for_deep_think = policy_contract.get('requires_human_for_deep_think') is True if isinstance(policy_contract, dict) else False
        if reasoning_mode == 'deep_think' and requires_human_for_deep_think:
            supported.append('runtime.reasoning_control')

        return supported

    def _nested_policy_contract_shape_violation(
        self,
        name: str,
        value: object,
        allowed_keys: set[str],
    ) -> RuntimeContractViolation | None:
        if value is None:
            return None
        if not isinstance(value, dict):
            return RuntimeContractViolation(
                code=f'policy_contract_{name}_invalid_type',
                reason=f'Runtime contract violation: policy_contract.{name} must be an object map when provided.',
                notes=[f'metadata.policy_contract.{name} is present but not a dictionary.'],
            )
        unknown_keys = sorted(key for key in value if key not in allowed_keys)
        if unknown_keys:
            return RuntimeContractViolation(
                code=f'policy_contract_{name}_unknown_keys',
                reason=f'Runtime contract violation: policy_contract.{name} contains unsupported keys.',
                notes=[f"unsupported keys: {', '.join(unknown_keys)}"],
            )
        return None

    def _human_override_approver_role(self, computation: DecisionComputation) -> str | None:
        override = computation.human_override
        if override is None:
            return None
        approver_role = getattr(override, 'approver_role', None)
        if isinstance(approver_role, str) and approver_role.strip():
            return approver_role
        return None

    def _human_override_status(self, computation: DecisionComputation) -> str | None:
        override = computation.human_override
        if override is None:
            return None
        status = getattr(override, 'status', None)
        if isinstance(status, str) and status.strip():
            return status
        return None

    def _optional_str(self, value: object) -> str | None:
        if not isinstance(value, str):
            return None
        text = value.strip()
        return text or None

    def _string_list(self, value: object) -> bool:
        if not isinstance(value, list):
            return False
        return all(isinstance(item, str) and item.strip() for item in value)
