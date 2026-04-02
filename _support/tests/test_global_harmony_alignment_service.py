from pathlib import Path

import pytest

from sa_nom_governance.alignment.alignment_service import GlobalHarmonyAlignmentService

ALIGNMENT_CATALOG_DIR = Path(__file__).resolve().parents[2] / 'resources' / 'alignment'


def test_alignment_service_initializes_with_active_selection() -> None:
    service = GlobalHarmonyAlignmentService(ALIGNMENT_CATALOG_DIR)

    snapshot = service.build_runtime_snapshot()

    assert snapshot['active_selection']['region_id'] == 'eu'
    assert snapshot['active_selection']['source'] == 'catalog-default'
    assert snapshot['safe_claim']
    assert snapshot['available_regions']
    assert snapshot['switch_policy']['requires_named_actor'] is True
    assert snapshot['switch_policy']['preview_required_without_context'] is True
    assert snapshot['audit_handoff']['event_type'] == 'alignment.selection'
    assert snapshot['audit_handoff']['selection_intent']['action'] == 'active'
    assert 'evaluation' not in snapshot


def test_alignment_service_can_switch_active_region_for_low_risk_context() -> None:
    service = GlobalHarmonyAlignmentService(ALIGNMENT_CATALOG_DIR)

    selection = service.select_region(
        'thailand',
        selected_by='operator.tawan',
        rationale='Internal ASEAN pilot alignment for low-risk coordination.',
        context={
            'audience': 'internal',
            'channel': 'internal',
            'sensitivity': 'normal',
            'tone': 'neutral',
            'requires_approval': False,
        },
        draft_text='Internal coordination update.',
    )
    snapshot = service.build_runtime_snapshot()

    assert selection.region_id == 'thailand'
    assert snapshot['active_selection']['region_id'] == 'thailand'
    assert snapshot['active_selection']['selected_by'] == 'operator.tawan'
    assert snapshot['active_selection']['rationale'] == 'Internal ASEAN pilot alignment for low-risk coordination.'


def test_alignment_service_rejects_switch_without_meaningful_rationale() -> None:
    service = GlobalHarmonyAlignmentService(ALIGNMENT_CATALOG_DIR)

    with pytest.raises(ValueError):
        service.select_region('thailand', selected_by='operator.tawan', rationale='too short')


def test_alignment_service_marks_missing_context_as_preview_only() -> None:
    service = GlobalHarmonyAlignmentService(ALIGNMENT_CATALOG_DIR)

    preview = service.preview_switch(
        'thailand',
        selected_by='operator.tawan',
        rationale='ASEAN pilot alignment for future rollout.',
    )

    assert preview['selection_intent']['action'] == 'preview_only'
    assert 'evaluation' not in preview


def test_alignment_service_requires_approval_for_sensitive_context() -> None:
    service = GlobalHarmonyAlignmentService(ALIGNMENT_CATALOG_DIR)

    preview = service.preview_switch(
        'thailand',
        selected_by='operator.tawan',
        rationale='Customer-facing ASEAN pilot alignment.',
        context={
            'audience': 'customer',
            'channel': 'public',
            'sensitivity': 'high',
            'tone': 'aggressive',
            'requires_approval': False,
        },
        draft_text='Aggressive escalation message to a customer.',
    )

    assert preview['decision']['allowed'] is True
    assert preview['selection_intent']['action'] == 'require_approval'
    assert preview['selection_intent']['approval_required'] is True
    assert preview['evaluation']['status'] == 'escalated'
    assert preview['evaluation']['resonance_band'] == 'low'
    concern_codes = {item['code'] for item in preview['evaluation']['concerns']}
    assert 'HUMAN_REVIEW_REQUIRED' in concern_codes

    with pytest.raises(ValueError):
        service.select_region(
            'thailand',
            selected_by='operator.tawan',
            rationale='Customer-facing ASEAN pilot alignment.',
            context={
                'audience': 'customer',
                'channel': 'public',
                'sensitivity': 'high',
                'tone': 'aggressive',
                'requires_approval': False,
            },
            draft_text='Aggressive escalation message to a customer.',
        )


def test_alignment_service_accepts_sensitive_switch_when_approved() -> None:
    service = GlobalHarmonyAlignmentService(ALIGNMENT_CATALOG_DIR)

    selection = service.select_region(
        'usa',
        selected_by='operator.tawan',
        rationale='Accountability-first evaluation path for public customer messaging.',
        context={
            'audience': 'customer',
            'channel': 'public',
            'sensitivity': 'regulated',
            'tone': 'neutral',
            'owner_visible': True,
            'explanation_visible': True,
            'requires_approval': True,
        },
        draft_text='Provide a transparent policy explanation to the customer.',
        approved_by='reviewer.sanom',
    )

    assert selection.region_id == 'usa'
    assert 'approved_by=reviewer.sanom' in selection.rationale


def test_alignment_service_builds_runtime_evaluation_snapshot() -> None:
    service = GlobalHarmonyAlignmentService(ALIGNMENT_CATALOG_DIR)
    service.select_region(
        'usa',
        selected_by='operator.tawan',
        rationale='Accountability-first evaluation path.',
        context={
            'audience': 'internal',
            'channel': 'internal',
            'sensitivity': 'normal',
            'tone': 'neutral',
            'requires_approval': False,
        },
        draft_text='Internal accountability update.',
    )

    snapshot = service.build_runtime_snapshot(
        context={
            'audience': 'customer',
            'channel': 'public',
            'sensitivity': 'regulated',
            'tone': 'neutral',
            'owner_visible': False,
            'explanation_visible': True,
            'requires_approval': True,
        },
        draft_text='Provide a transparent policy explanation to the customer.',
    )

    assert snapshot['evaluation']['status'] == 'guarded'
    assert snapshot['evaluation']['human_review_required'] is True
    assert snapshot['evaluation']['resonance_band'] == 'moderate'
    concern_codes = {item['code'] for item in snapshot['evaluation']['concerns']}
    assert 'OWNER_NOT_VISIBLE' in concern_codes
    assert snapshot['safe_claim']
    assert snapshot['notes']

def test_alignment_service_accepts_explicit_default_region() -> None:
    service = GlobalHarmonyAlignmentService(ALIGNMENT_CATALOG_DIR, default_region_id='thailand')

    snapshot = service.build_runtime_snapshot()

    assert snapshot['active_selection']['region_id'] == 'thailand'
    assert snapshot['active_selection']['source'] == 'configured-default'
    assert snapshot['active_selection']['rationale'] == 'Initialized from explicit default region thailand.'


def test_alignment_service_rejects_unknown_explicit_default_region() -> None:
    with pytest.raises(ValueError, match='Unknown default regional constitution'):
        GlobalHarmonyAlignmentService(ALIGNMENT_CATALOG_DIR, default_region_id='japan')
