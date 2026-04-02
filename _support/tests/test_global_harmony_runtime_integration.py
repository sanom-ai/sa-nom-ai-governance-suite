from pathlib import Path

import pytest

from sa_nom_governance.api.api_engine import build_engine_app
from sa_nom_governance.utils.config import AppConfig

DEFAULT_ALIGNMENT_CATALOG_DIR = Path(__file__).resolve().parents[2] / 'resources' / 'alignment'


def build_test_app():
    return build_engine_app(AppConfig(persist_runtime=False))


def test_runtime_attaches_global_harmony_signal_for_low_risk_request() -> None:
    app = build_test_app()

    result = app.request(
        requester='operator.tawan',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'GH-RT-1', 'amount': 1000000},
        metadata={
            'global_harmony': {
                'region_id': 'thailand',
                'selected_by': 'operator.tawan',
                'rationale': 'Internal ASEAN pilot alignment for low-risk review.',
                'context': {
                    'audience': 'internal',
                    'channel': 'internal',
                    'sensitivity': 'normal',
                    'tone': 'neutral',
                    'requires_approval': False,
                },
                'draft_text': 'Internal coordination update.',
            }
        },
    )

    assert result.outcome == 'approved'
    harmony = result.metadata['metadata']['global_harmony_runtime']
    assert harmony['mode'] == 'requested_region_preview'
    assert harmony['selection_intent']['action'] == 'direct_switch'
    assert harmony['evaluation']['status'] == 'aligned'
    assert harmony['evaluation']['resonance_band'] == 'high'


def test_runtime_waits_for_human_when_global_harmony_requires_approval() -> None:
    app = build_test_app()

    result = app.request(
        requester='operator.tawan',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'GH-RT-2', 'amount': 1000000},
        metadata={
            'global_harmony': {
                'region_id': 'thailand',
                'selected_by': 'operator.tawan',
                'rationale': 'Customer-facing ASEAN pilot alignment requiring review.',
                'context': {
                    'audience': 'customer',
                    'channel': 'public',
                    'sensitivity': 'high',
                    'tone': 'aggressive',
                    'requires_approval': False,
                },
                'draft_text': 'Aggressive escalation message to a customer.',
            }
        },
    )

    assert result.outcome == 'waiting_human'
    assert result.policy_basis == 'runtime.global_harmony.selection'
    assert result.decision_trace['source_type'] == 'global_harmony'
    assert result.human_override is not None
    harmony = result.metadata['metadata']['global_harmony_runtime']
    assert harmony['selection_intent']['action'] == 'require_approval'
    assert harmony['evaluation']['status'] == 'escalated'
    assert harmony['evaluation']['resonance_band'] == 'low'


def test_runtime_keeps_active_region_alignment_signal_in_metadata() -> None:
    app = build_test_app()

    result = app.request(
        requester='operator.tawan',
        role_id='LEGAL',
        action='review_contract',
        payload={'resource': 'contract', 'resource_id': 'GH-RT-3', 'amount': 1000000},
        metadata={
            'global_harmony': {
                'context': {
                    'audience': 'customer',
                    'channel': 'public',
                    'sensitivity': 'regulated',
                    'tone': 'neutral',
                    'explanation_visible': False,
                    'requires_approval': True,
                },
                'draft_text': 'Provide a policy explanation to a customer.',
            }
        },
    )

    assert result.outcome == 'approved'
    harmony = result.metadata['metadata']['global_harmony_runtime']
    assert harmony['mode'] == 'active_runtime'
    assert harmony['region_id'] == 'eu'
    assert harmony['evaluation']['status'] == 'guarded'
    assert harmony['evaluation']['resonance_band'] == 'moderate'
    concern_codes = {item['code'] for item in harmony['evaluation']['concerns']}
    assert 'EXPLANATION_GAP' in concern_codes


def test_runtime_bootstraps_global_harmony_outside_repo_root(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)

    app = build_test_app()

    snapshot = app.engine.global_harmony_alignment.build_runtime_snapshot()

    assert snapshot['available_regions']
    assert snapshot['active_selection']['region_id'] == 'eu'


def test_app_config_defaults_alignment_resources_to_bundled_catalog(tmp_path: Path) -> None:
    config = AppConfig(base_dir=tmp_path, persist_runtime=False)

    assert config.alignment_resources_dir == tmp_path / 'resources' / 'alignment'
    assert config.alignment_resources_dir.exists()
    assert (config.alignment_resources_dir / 'eu_transparency_constitution.json').exists()
    assert config.alignment_default_region == 'eu'


def test_app_config_resolves_relative_alignment_resource_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('SANOM_ALIGNMENT_RESOURCES_DIR', 'resources/alignment')

    config = AppConfig(persist_runtime=False)

    assert config.alignment_resources_dir == config.base_dir / 'resources' / 'alignment'

def test_app_config_resolves_alignment_default_region_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('SANOM_ALIGNMENT_DEFAULT_REGION', 'thailand')

    config = AppConfig(persist_runtime=False)

    assert config.alignment_default_region == 'thailand'


def test_runtime_uses_configured_alignment_default_region(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('SANOM_ALIGNMENT_DEFAULT_REGION', 'thailand')

    app = build_engine_app(AppConfig(persist_runtime=False))
    snapshot = app.engine.global_harmony_alignment.build_runtime_snapshot()

    assert snapshot['active_selection']['region_id'] == 'thailand'
    assert snapshot['active_selection']['source'] == 'configured-default'
