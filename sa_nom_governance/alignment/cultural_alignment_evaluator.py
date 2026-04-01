from sa_nom_governance.alignment.constitution_models import AlignmentPrinciple, RegionalConstitution
from sa_nom_governance.alignment.evaluation_models import AlignmentConcern, AlignmentEvaluationResult, AlignmentMatch


class CulturalAlignmentEvaluator:
    def normalize_context(self, context: dict[str, object]) -> dict[str, object]:
        sensitivity = str(context.get('sensitivity', 'normal')).strip().lower() or 'normal'
        audience = str(context.get('audience', 'internal')).strip().lower() or 'internal'
        channel = str(context.get('channel', 'internal')).strip().lower() or 'internal'
        tone = str(context.get('tone', 'neutral')).strip().lower() or 'neutral'
        hierarchy = str(context.get('hierarchy', 'standard')).strip().lower() or 'standard'
        requires_approval = bool(context.get('requires_approval', False))
        owner_visible = bool(context.get('owner_visible', False))
        explanation_visible = bool(context.get('explanation_visible', False))

        categories: set[str] = set()
        if audience in {'customer', 'external', 'public'} or channel in {'press', 'public', 'customer'}:
            categories.update({'communication', 'cultural_posture'})
        if hierarchy in {'executive', 'formal', 'high'}:
            categories.update({'cultural_posture', 'governance'})
        if sensitivity in {'high', 'legal_sensitive', 'regulated'}:
            categories.update({'governance', 'transparency', 'accountability'})
        if owner_visible:
            categories.add('accountability')
        if explanation_visible:
            categories.add('transparency')

        return {
            'sensitivity': sensitivity,
            'audience': audience,
            'channel': channel,
            'tone': tone,
            'hierarchy': hierarchy,
            'requires_approval': requires_approval,
            'owner_visible': owner_visible,
            'explanation_visible': explanation_visible,
            'categories': sorted(categories),
        }

    def evaluate(
        self,
        constitution: RegionalConstitution,
        *,
        context: dict[str, object],
        draft_text: str = '',
    ) -> AlignmentEvaluationResult:
        normalized = self.normalize_context(context)
        concerns: list[AlignmentConcern] = []
        matches: list[AlignmentMatch] = []
        rationale: list[str] = []
        categories = set(str(item) for item in normalized['categories'])
        lower_text = draft_text.lower()

        for principle in constitution.principles:
            reason = self._match_reason(principle, normalized, categories, lower_text)
            if reason:
                matches.append(
                    AlignmentMatch(
                        principle_id=principle.principle_id,
                        title=principle.title,
                        category=principle.category,
                        reason=reason,
                    )
                )

        sensitivity = str(normalized['sensitivity'])
        tone = str(normalized['tone'])
        requires_approval = bool(normalized['requires_approval'])
        owner_visible = bool(normalized['owner_visible'])
        explanation_visible = bool(normalized['explanation_visible'])
        audience = str(normalized['audience'])

        if sensitivity in {'high', 'legal_sensitive', 'regulated'} and not requires_approval:
            concerns.append(
                AlignmentConcern(
                    code='HUMAN_REVIEW_REQUIRED',
                    severity='critical',
                    message='Sensitive regional alignment context should keep an explicit human approval or escalation path.',
                )
            )
            rationale.append('High-sensitivity context escalated because no human review path was declared.')

        if 'polite' in constitution.communication_posture.get('tone', '').lower() and tone in {'aggressive', 'confrontational'}:
            concerns.append(
                AlignmentConcern(
                    code='TONE_MISMATCH',
                    severity='warning',
                    message='Declared tone conflicts with the selected regional expectation for respectful or non-inflammatory communication.',
                )
            )
            rationale.append('Tone posture is more forceful than the selected constitution recommends.')

        if constitution.region_id == 'eu' and audience in {'public', 'external', 'customer'} and not explanation_visible:
            concerns.append(
                AlignmentConcern(
                    code='EXPLANATION_GAP',
                    severity='warning',
                    message='Transparency-oriented contexts should keep visible explanation or limits when communicating externally.',
                )
            )
            rationale.append('External EU-facing communication should surface explanation or limits more explicitly.')

        if constitution.region_id == 'usa' and sensitivity in {'high', 'legal_sensitive', 'regulated'} and not owner_visible:
            concerns.append(
                AlignmentConcern(
                    code='OWNER_NOT_VISIBLE',
                    severity='warning',
                    message='Accountability-oriented contexts should name an owner, approver, or escalation path for sensitive work.',
                )
            )
            rationale.append('Sensitive accountability-heavy context should keep ownership visible.')

        primary_matches = {item.principle_id for item in matches if any(principle.principle_id == item.principle_id and principle.weight == 'primary' for principle in constitution.principles)}
        if categories and not primary_matches:
            concerns.append(
                AlignmentConcern(
                    code='PRIMARY_ALIGNMENT_GAP',
                    severity='warning',
                    message='The selected regional context did not match any primary alignment principle strongly enough to claim a fully aligned posture.',
                )
            )
            rationale.append('Context normalized correctly but did not align strongly with a primary constitutional principle.')

        if any(item.severity == 'critical' for item in concerns):
            status = 'escalated'
        elif concerns:
            status = 'guarded'
        else:
            status = 'aligned'
            rationale.append('No cultural or governance conflicts were detected in the evaluated context.')

        resonance_score = self._calculate_resonance_score(status, matches, concerns)
        if resonance_score >= 85:
            resonance_band = 'high'
        elif resonance_score >= 65:
            resonance_band = 'moderate'
        else:
            resonance_band = 'low'
        rationale.append(f'Resonance score: {resonance_score}/100 ({resonance_band}).')

        return AlignmentEvaluationResult(
            status=status,
            human_review_required=status == 'escalated' or requires_approval,
            resonance_score=resonance_score,
            resonance_band=resonance_band,
            normalized_context=normalized,
            matched_principles=matches,
            concerns=concerns,
            rationale=rationale,
        )

    def _calculate_resonance_score(
        self,
        status: str,
        matches: list[AlignmentMatch],
        concerns: list[AlignmentConcern],
    ) -> int:
        if status == 'escalated':
            score = 45
        elif status == 'guarded':
            score = 72
        else:
            score = 88

        warning_count = sum(1 for concern in concerns if concern.severity == 'warning')
        critical_count = sum(1 for concern in concerns if concern.severity == 'critical')
        score -= warning_count * 4
        score -= critical_count * 10

        # Reward contextual matches while keeping guarded/escalated paths clearly below high confidence.
        score += min(len(matches) * 2, 10)
        return max(0, min(100, score))

    def _match_reason(
        self,
        principle: AlignmentPrinciple,
        normalized: dict[str, object],
        categories: set[str],
        lower_text: str,
    ) -> str:
        if principle.category in categories:
            return f"Context category matched {principle.category}."
        for keyword in principle.keywords:
            if keyword.lower() in lower_text:
                return f"Draft text matched keyword '{keyword}'."
        posture_text = ' '.join(str(value).lower() for value in normalized.values() if isinstance(value, str))
        for keyword in principle.keywords:
            if keyword.lower() in posture_text:
                return f"Normalized context matched keyword '{keyword}'."
        return ''
