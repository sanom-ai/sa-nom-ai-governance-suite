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
        self._effect_appliers = {
            'approval_gate': self._apply_approval_gate_effect,
            'policy_pack': self._apply_policy_pack_effect,
            'tone_rewrite': self._apply_tone_rewrite_effect,
            'evidence_log': self._apply_evidence_log_effect,
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
            'runtime_effects': [],
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
        effect_kinds = self._runtime_effect_kinds(action_plan)
        if effect_kinds:
            notes.append(f"Runtime executors prepared: {', '.join(effect_kinds)}.")
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

        approval_role = str(trigger_runtime.get('approval_role', '')).strip()
        runtime_effects = self._resolve_runtime_effects(trigger_runtime)
        policy_runtime: dict[str, Any] = {
            'source_policy_id': str(trigger_runtime.get('policy_id', '')),
            'branch': str(trigger_runtime.get('branch', '')),
            'requires_approval': bool(trigger_runtime.get('requires_approval')),
            'approval_role': approval_role,
            'active_policy_packs': [],
            'evidence_tags': [],
            'unknown_actions': [str(item) for item in trigger_runtime.get('unknown_actions', [])],
            'runtime_effects': [dict(effect) for effect in runtime_effects],
            'applied_effect_kinds': [],
            'terminal_outcome': computation.outcome,
        }
        context.metadata['policy_runtime'] = policy_runtime

        harmony_runtime = context.metadata.get('global_harmony_runtime')
        harmony_mapping = harmony_runtime if isinstance(harmony_runtime, dict) else None
        for effect in runtime_effects:
            effect_kind = str(effect.get('kind', '')).strip().lower()
            applier = self._effect_appliers.get(effect_kind)
            if applier is None:
                continue
            applier(
                context=context,
                trigger_runtime=trigger_runtime,
                policy_runtime=policy_runtime,
                harmony_runtime=harmony_mapping,
                effect=effect,
            )

        if harmony_mapping is not None:
            harmony_mapping['trigger_runtime'] = {
                'policy_id': str(trigger_runtime.get('policy_id', '')),
                'branch': str(trigger_runtime.get('branch', '')),
                'requires_approval': bool(trigger_runtime.get('requires_approval')),
                'approval_role': approval_role,
                'policy_packs': list(policy_runtime['active_policy_packs']),
                'evidence_tags': list(policy_runtime['evidence_tags']),
                'tone_profile': self._resolve_tone_profile(context),
                'runtime_effects': [dict(effect) for effect in runtime_effects],
                'applied_effect_kinds': list(policy_runtime['applied_effect_kinds']),
                'terminal_outcome': computation.outcome,
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
        self._append_runtime_effect(
            plan,
            {
                'kind': 'approval_gate',
                'role': str(plan['approval_role']).strip(),
            },
        )

    def _collect_apply_policy_pack(self, plan: dict[str, Any], action: ParsedTriggerAction) -> None:
        if action.args:
            self._append_unique(plan['policy_packs'], action.args[0])
            self._append_runtime_effect(
                plan,
                {
                    'kind': 'policy_pack',
                    'pack_id': action.args[0],
                },
            )

    def _collect_rewrite_tone(self, plan: dict[str, Any], action: ParsedTriggerAction) -> None:
        if action.args:
            plan['tone_profile'] = action.args[0]
            self._append_runtime_effect(
                plan,
                {
                    'kind': 'tone_rewrite',
                    'tone_profile': action.args[0],
                },
            )

    def _collect_log_evidence(self, plan: dict[str, Any], action: ParsedTriggerAction) -> None:
        if action.args:
            self._append_unique(plan['evidence_tags'], action.args[0])
            self._append_runtime_effect(
                plan,
                {
                    'kind': 'evidence_log',
                    'tag': action.args[0],
                },
            )

    def _append_unique(self, target: list[str], value: str) -> None:
        if value not in target:
            target.append(value)

    def _append_runtime_effect(self, plan: dict[str, Any], effect: dict[str, Any]) -> None:
        effect_list = plan.setdefault('runtime_effects', [])
        if effect not in effect_list:
            effect_list.append(dict(effect))

    def _runtime_effect_kinds(self, action_plan: dict[str, Any]) -> list[str]:
        kinds: list[str] = []
        for effect in self._resolve_runtime_effects(action_plan):
            kind = str(effect.get('kind', '')).strip()
            if kind and kind not in kinds:
                kinds.append(kind)
        return kinds

    def _resolve_runtime_effects(self, trigger_runtime: dict[str, Any]) -> list[dict[str, Any]]:
        raw_effects = trigger_runtime.get('runtime_effects')
        normalized_effects: list[dict[str, Any]] = []
        if isinstance(raw_effects, list):
            for effect in raw_effects:
                normalized = self._normalize_effect(effect)
                if normalized is not None:
                    normalized_effects.append(normalized)
        if normalized_effects:
            return normalized_effects

        fallback_effects: list[dict[str, Any]] = []
        approval_role = str(trigger_runtime.get('approval_role', '')).strip()
        if trigger_runtime.get('requires_approval'):
            fallback_effects.append({'kind': 'approval_gate', 'role': approval_role})

        for pack_id in [str(item) for item in trigger_runtime.get('policy_packs', []) if str(item).strip()]:
            fallback_effects.append({'kind': 'policy_pack', 'pack_id': pack_id})

        tone_profile = str(trigger_runtime.get('tone_profile', '')).strip()
        if tone_profile:
            fallback_effects.append({'kind': 'tone_rewrite', 'tone_profile': tone_profile})

        for tag in [str(item) for item in trigger_runtime.get('evidence_tags', []) if str(item).strip()]:
            fallback_effects.append({'kind': 'evidence_log', 'tag': tag})

        return fallback_effects

    def _normalize_effect(self, effect: Any) -> dict[str, Any] | None:
        if not isinstance(effect, dict):
            return None
        kind = str(effect.get('kind', '')).strip().lower()
        if not kind:
            return None
        normalized: dict[str, Any] = {'kind': kind}
        for key, value in effect.items():
            if key == 'kind':
                continue
            normalized[str(key)] = value.strip() if isinstance(value, str) else value
        return normalized

    def _apply_approval_gate_effect(
        self,
        *,
        context: ExecutionContext,
        trigger_runtime: dict[str, Any],
        policy_runtime: dict[str, Any],
        harmony_runtime: dict[str, Any] | None,
        effect: dict[str, Any],
    ) -> None:
        approval_role = str(effect.get('role', '')).strip() or str(trigger_runtime.get('approval_role', '')).strip()
        policy_runtime['approval_gate'] = {
            'required': True,
            'role': approval_role,
            'source_policy_id': str(trigger_runtime.get('policy_id', '')),
        }
        self._record_applied_effect(policy_runtime, 'approval_gate')
        if harmony_runtime is not None:
            harmony_runtime['approval_gate'] = {
                'required': True,
                'role': approval_role,
                'source_policy_id': str(trigger_runtime.get('policy_id', '')),
            }

    def _apply_policy_pack_effect(
        self,
        *,
        context: ExecutionContext,
        trigger_runtime: dict[str, Any],
        policy_runtime: dict[str, Any],
        harmony_runtime: dict[str, Any] | None,
        effect: dict[str, Any],
    ) -> None:
        pack_id = str(effect.get('pack_id', '')).strip()
        if not pack_id:
            return
        self._append_unique(policy_runtime['active_policy_packs'], pack_id)
        self._record_applied_effect(policy_runtime, 'policy_pack')
        if harmony_runtime is not None:
            active_packs = harmony_runtime.get('active_policy_packs')
            if not isinstance(active_packs, list):
                active_packs = []
                harmony_runtime['active_policy_packs'] = active_packs
            self._append_unique(active_packs, pack_id)

            effect_rows = harmony_runtime.get('policy_pack_effects')
            if not isinstance(effect_rows, list):
                effect_rows = []
                harmony_runtime['policy_pack_effects'] = effect_rows
            effect_payload = {
                'pack_id': pack_id,
                'source_policy_id': str(trigger_runtime.get('policy_id', '')),
                'branch': str(trigger_runtime.get('branch', '')),
            }
            if effect_payload not in effect_rows:
                effect_rows.append(effect_payload)

    def _apply_tone_rewrite_effect(
        self,
        *,
        context: ExecutionContext,
        trigger_runtime: dict[str, Any],
        policy_runtime: dict[str, Any],
        harmony_runtime: dict[str, Any] | None,
        effect: dict[str, Any],
    ) -> None:
        tone_profile = str(effect.get('tone_profile', '')).strip()
        if not tone_profile:
            return
        context.metadata['output_guidance'] = {
            'source_policy_id': str(trigger_runtime.get('policy_id', '')),
            'tone_profile': tone_profile,
            'rewrite_required': True,
            'guidance_type': 'tone_rewrite',
            'applied_branch': str(trigger_runtime.get('branch', '')),
        }
        self._record_applied_effect(policy_runtime, 'tone_rewrite')
        if harmony_runtime is not None:
            harmony_runtime['tone_guidance'] = {
                'tone_profile': tone_profile,
                'source_policy_id': str(trigger_runtime.get('policy_id', '')),
                'guidance_type': 'tone_rewrite',
            }

    def _apply_evidence_log_effect(
        self,
        *,
        context: ExecutionContext,
        trigger_runtime: dict[str, Any],
        policy_runtime: dict[str, Any],
        harmony_runtime: dict[str, Any] | None,
        effect: dict[str, Any],
    ) -> None:
        evidence_tag = str(effect.get('tag', '')).strip()
        if not evidence_tag:
            return
        self._append_unique(policy_runtime['evidence_tags'], evidence_tag)
        runtime_evidence_tags = context.metadata.get('runtime_evidence_tags')
        if not isinstance(runtime_evidence_tags, list):
            runtime_evidence_tags = []
            context.metadata['runtime_evidence_tags'] = runtime_evidence_tags
        self._append_unique(runtime_evidence_tags, evidence_tag)
        self._record_applied_effect(policy_runtime, 'evidence_log')
        if harmony_runtime is not None:
            harmony_evidence_tags = harmony_runtime.get('evidence_tags')
            if not isinstance(harmony_evidence_tags, list):
                harmony_evidence_tags = []
                harmony_runtime['evidence_tags'] = harmony_evidence_tags
            self._append_unique(harmony_evidence_tags, evidence_tag)

    def _record_applied_effect(self, policy_runtime: dict[str, Any], effect_kind: str) -> None:
        effect_kinds = policy_runtime.get('applied_effect_kinds')
        if not isinstance(effect_kinds, list):
            effect_kinds = []
            policy_runtime['applied_effect_kinds'] = effect_kinds
        self._append_unique(effect_kinds, effect_kind)

    def _resolve_tone_profile(self, context: ExecutionContext) -> str:
        output_guidance = context.metadata.get('output_guidance')
        if isinstance(output_guidance, dict):
            return str(output_guidance.get('tone_profile', '')).strip()
        return ''

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
