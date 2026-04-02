from pathlib import Path

from sa_nom_governance.alignment.constitution_registry import RegionalConstitutionRegistry
from sa_nom_governance.alignment.cultural_alignment_evaluator import CulturalAlignmentEvaluator

ALIGNMENT_CATALOG_DIR = Path(__file__).resolve().parents[2] / 'resources' / 'alignment'


def _registry() -> RegionalConstitutionRegistry:
    return RegionalConstitutionRegistry(ALIGNMENT_CATALOG_DIR)


def test_thailand_sensitive_forceful_context_escalates_without_human_review() -> None:
    registry = _registry()
    evaluator = CulturalAlignmentEvaluator()

    result = evaluator.evaluate(
        registry.load('thailand'),
        context={
            'audience': 'internal',
            'channel': 'internal',
            'hierarchy': 'formal',
            'sensitivity': 'high',
            'tone': 'aggressive',
            'requires_approval': False,
        },
        draft_text='Escalate this issue immediately and force resolution.',
    )

    assert result.status == 'escalated'
    assert result.human_review_required is True
    assert {item.code for item in result.concerns} >= {'HUMAN_REVIEW_REQUIRED', 'TONE_MISMATCH'}
    assert result.resonance_band == 'low'
    assert result.resonance_score < 65
    assert any(item.principle_id == 'TH_ESCALATION_CLARITY' for item in result.matched_principles)


def test_eu_external_context_is_guarded_when_explanation_is_missing() -> None:
    registry = _registry()
    evaluator = CulturalAlignmentEvaluator()

    result = evaluator.evaluate(
        registry.load('eu'),
        context={
            'audience': 'external',
            'channel': 'public',
            'sensitivity': 'regulated',
            'tone': 'neutral',
            'requires_approval': True,
            'explanation_visible': False,
        },
        draft_text='This output is ready for external communication.',
    )

    assert result.status == 'guarded'
    assert result.human_review_required is True
    assert any(item.code == 'EXPLANATION_GAP' for item in result.concerns)
    assert result.resonance_band == 'moderate'
    assert 65 <= result.resonance_score < 85
    assert any(item.principle_id == 'EU_EXPLAIN_LIMITS' for item in result.matched_principles)


def test_usa_sensitive_context_can_align_when_owner_and_review_are_visible() -> None:
    registry = _registry()
    evaluator = CulturalAlignmentEvaluator()

    result = evaluator.evaluate(
        registry.load('usa'),
        context={
            'audience': 'customer',
            'channel': 'customer',
            'sensitivity': 'high',
            'tone': 'neutral',
            'requires_approval': True,
            'owner_visible': True,
            'explanation_visible': True,
        },
        draft_text='The accountable owner will review and approve the next step before release.',
    )

    assert result.status == 'aligned'
    assert result.human_review_required is True
    assert result.resonance_band == 'high'
    assert result.resonance_score >= 85
    assert not result.concerns
    assert any(item.principle_id == 'US_NAME_OWNER' for item in result.matched_principles)


def test_result_contract_is_audit_ready_dict() -> None:
    registry = _registry()
    evaluator = CulturalAlignmentEvaluator()

    result = evaluator.evaluate(
        registry.load('thailand'),
        context={
            'audience': 'internal',
            'channel': 'internal',
            'hierarchy': 'formal',
            'sensitivity': 'normal',
            'tone': 'polite',
            'requires_approval': False,
        },
        draft_text='Please review this escalation path with the designated approver.',
    )

    payload = result.to_dict()

    assert payload['status'] in {'aligned', 'guarded', 'escalated'}
    assert 'normalized_context' in payload
    assert isinstance(payload['resonance_score'], int)
    assert payload['resonance_band'] in {'high', 'moderate', 'low'}
    assert isinstance(payload['matched_principles'], list)
    assert isinstance(payload['concerns'], list)
    assert isinstance(payload['rationale'], list)
