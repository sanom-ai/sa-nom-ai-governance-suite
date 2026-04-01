from dataclasses import dataclass, field
from typing import Any

from sa_nom_governance.core.decision_models import DecisionComputation
from sa_nom_governance.core.execution_context import ExecutionContext


@dataclass(slots=True)
class ParsedTriggerAction:
    raw: str
    name: str
    args: list[str] = field(default_factory=list)


class TriggerActionRegistry:
    TERMINAL_OUTCOMES = {
        'approve': 'approved',
        'reject': 'rejected',
        'wait_human': 'waiting_human',
        'suspend': 'suspended',
        'escalate': 'escalated',
    }

    def __init__(self) -> None:
        self._collectors = {
            'require_approval': self._collect_require_approval,
            'apply_policy_pack': self._collect_apply_policy_pack,
            'rewrite_tone': self._collect_rewrite_tone,
            'log_evidence': self._collect_log_evidence,
        }

    def build_action_plan(
        self,
        policy_id: str,
        *,
        branch: str,
        action_tokens: list[str],
        override_active: bool,
    ) -> dict[str, Any]:
        actions = [self.parse_action_token(token) for token in action_tokens]
        plan: dict[str, Any] = {
            'policy_id': policy_id,
            'branch': branch,
            'actions': [self._serialize_action(action) for action in actions],
            'requires_approval': False,
            'approval_role': '',
            'policy_packs': [],
            'evidence_tags': [],
            'tone_profile': '',
            'unknown_actions': [],
            'terminal_action': None,
            'terminal_outcome': None,
            'override_active': override_active,
        }

        for action in actions:
            normalized_name = action.name.lower()
            if normalized_name in self.TERMINAL_OUTCOMES:
                if plan['terminal_action'] is None:
                    plan['terminal_action'] = normalized_name
                continue
            collector = self._collectors.get(normalized_name)
            if collector is None:
                plan['unknown_actions'].append(action.raw)
                continue
            collector(plan, action)

        if plan['requires_approval'] and not override_active:
            plan['terminal_outcome'] = 'waiting_human'
        elif isinstance(plan['terminal_action'], str):
            plan['terminal_outcome'] = self.TERMINAL_OUTCOMES.get(plan['terminal_action'], plan['terminal_action'])
        elif plan['requires_approval'] and override_active:
            plan['terminal_outcome'] = 'approved'

        return plan

    def build_policy_notes(self, action_plan: dict[str, Any] | None) -> list[str]:
        notes = ['Policy evaluation completed.']
        if not isinstance(action_plan, dict):
            return notes

        branch = action_plan.get('branch')
        if branch:
            notes.append(f"Trigger branch resolved through {str(branch).upper()}.")
        if action_plan.get('policy_packs'):
            notes.append(
                f"Policy packs prepared: {', '.join(str(item) for item in action_plan['policy_packs'])}."
            )
        if action_plan.get('evidence_tags'):
            notes.append(
                f"Evidence tags prepared: {', '.join(str(item) for item in action_plan['evidence_tags'])}."
            )
        tone_profile = action_plan.get('tone_profile')
        if tone_profile:
            notes.append(f"Tone rewrite suggested: {tone_profile}.")
        if action_plan.get('requires_approval'):
            approval_role = str(action_plan.get('approval_role', '')).strip() or 'governed reviewer'
            notes.append(f"Human approval requested through {approval_role}.")
        return notes

    def resolve_approval_role(self, context: ExecutionContext) -> str | None:
        trigger_runtime = context.metadata.get('ptag_trigger_runtime')
        if not isinstance(trigger_runtime, dict):
            return None
        approval_role = str(trigger_runtime.get('approval_role', '')).strip()
        return approval_role or None

    def apply_runtime_effects(self, context: ExecutionContext, computation: DecisionComputation) -> None:
        trigger_runtime = context.metadata.get('ptag_trigger_runtime')
        if not isinstance(trigger_runtime, dict):
            return

        policy_packs = [str(item) for item in trigger_runtime.get('policy_packs', []) if str(item).strip()]
        evidence_tags = [str(item) for item in trigger_runtime.get('evidence_tags', []) if str(item).strip()]
        tone_profile = str(trigger_runtime.get('tone_profile', '')).strip()
        approval_role = str(trigger_runtime.get('approval_role', '')).strip()

        context.metadata['policy_runtime'] = {
            'source_policy_id': str(trigger_runtime.get('policy_id', '')),
            'branch': str(trigger_runtime.get('branch', '')),
            'requires_approval': bool(trigger_runtime.get('requires_approval')),
            'approval_role': approval_role,
            'active_policy_packs': policy_packs,
            'evidence_tags': evidence_tags,
            'unknown_actions': [str(item) for item in trigger_runtime.get('unknown_actions', [])],
            'terminal_outcome': computation.outcome,
        }

        if tone_profile:
            context.metadata['output_guidance'] = {
                'source_policy_id': str(trigger_runtime.get('policy_id', '')),
                'tone_profile': tone_profile,
                'rewrite_required': True,
                'applied_branch': str(trigger_runtime.get('branch', '')),
            }

        if evidence_tags:
            context.metadata['runtime_evidence_tags'] = list(evidence_tags)

        harmony_runtime = context.metadata.get('global_harmony_runtime')
        if isinstance(harmony_runtime, dict):
            harmony_runtime['trigger_runtime'] = {
                'policy_id': str(trigger_runtime.get('policy_id', '')),
                'branch': str(trigger_runtime.get('branch', '')),
                'requires_approval': bool(trigger_runtime.get('requires_approval')),
                'approval_role': approval_role,
                'policy_packs': list(policy_packs),
                'evidence_tags': list(evidence_tags),
                'tone_profile': tone_profile,
                'terminal_outcome': computation.outcome,
            }
            if policy_packs:
                harmony_runtime['active_policy_packs'] = list(policy_packs)
            if tone_profile:
                harmony_runtime['tone_guidance'] = {
                    'tone_profile': tone_profile,
                    'source_policy_id': str(trigger_runtime.get('policy_id', '')),
                }

    def parse_action_token(self, token: str) -> ParsedTriggerAction:
        stripped = token.strip()
        if '(' not in stripped or not stripped.endswith(')'):
            return ParsedTriggerAction(raw=stripped, name=stripped)
        name, remainder = stripped.split('(', 1)
        args_payload = remainder[:-1].strip()
        if not args_payload:
            return ParsedTriggerAction(raw=stripped, name=name.strip())
        args = [self._stringify_argument(item) for item in self._split_top_level_csv(args_payload)]
        return ParsedTriggerAction(raw=stripped, name=name.strip(), args=args)

    def _collect_require_approval(self, plan: dict[str, Any], action: ParsedTriggerAction) -> None:
        plan['requires_approval'] = True
        if action.args and not plan['approval_role']:
            plan['approval_role'] = action.args[0]

    def _collect_apply_policy_pack(self, plan: dict[str, Any], action: ParsedTriggerAction) -> None:
        if action.args:
            self._append_unique(plan['policy_packs'], action.args[0])

    def _collect_rewrite_tone(self, plan: dict[str, Any], action: ParsedTriggerAction) -> None:
        if action.args:
            plan['tone_profile'] = action.args[0]

    def _collect_log_evidence(self, plan: dict[str, Any], action: ParsedTriggerAction) -> None:
        if action.args:
            self._append_unique(plan['evidence_tags'], action.args[0])

    def _append_unique(self, target: list[str], value: str) -> None:
        if value not in target:
            target.append(value)

    def _stringify_argument(self, value: str) -> str:
        stripped = value.strip()
        if stripped.startswith('"') and stripped.endswith('"'):
            return stripped[1:-1]
        if stripped.startswith("'") and stripped.endswith("'"):
            return stripped[1:-1]
        return stripped

    def _split_top_level_csv(self, value: str) -> list[str]:
        parts: list[str] = []
        current: list[str] = []
        quote_char: str | None = None
        depth = 0

        for char in value:
            if quote_char is not None:
                current.append(char)
                if char == quote_char:
                    quote_char = None
                continue

            if char in {'"', "'"}:
                quote_char = char
                current.append(char)
                continue

            if char in '([{':
                depth += 1
                current.append(char)
                continue

            if char in ')]}':
                depth = max(0, depth - 1)
                current.append(char)
                continue

            if char == ',' and depth == 0:
                part = ''.join(current).strip()
                if part:
                    parts.append(part)
                current = []
                continue

            current.append(char)

        part = ''.join(current).strip()
        if part:
            parts.append(part)
        return parts

    def _serialize_action(self, action: ParsedTriggerAction) -> dict[str, Any]:
        return {
            'raw': action.raw,
            'name': action.name,
            'args': list(action.args),
        }
