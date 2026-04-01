from pathlib import Path

import pytest

from sa_nom_governance.alignment.constitution_registry import RegionalConstitutionRegistry


def test_registry_loads_public_constitution_templates() -> None:
    registry = RegionalConstitutionRegistry(Path('resources/alignment'))

    snapshot = registry.build_snapshot()

    assert snapshot['summary']['regions_total'] == 3
    assert snapshot['summary']['principles_total'] >= 6
    assert {item['region_id'] for item in snapshot['regions']} == {'thailand', 'eu', 'usa'}


def test_registry_load_returns_structured_constitution() -> None:
    registry = RegionalConstitutionRegistry(Path('resources/alignment'))

    constitution = registry.load('thailand')

    assert constitution.display_name == 'Thailand Harmony Constitution'
    assert constitution.default_locale == 'th-TH'
    assert constitution.principles[0].principle_id == 'TH_RESPECTFUL_FORMALITY'
    assert 'respect' in constitution.values


def test_registry_raises_for_unknown_region() -> None:
    registry = RegionalConstitutionRegistry(Path('resources/alignment'))

    with pytest.raises(KeyError):
        registry.load('japan')


def test_registry_rejects_constitution_without_principles(tmp_path: Path) -> None:
    (tmp_path / 'broken.json').write_text(
        '{"region_id":"broken","display_name":"Broken","geography_scope":"Nowhere","default_locale":"en","constitutional_version":"1","principles":[]}',
        encoding='utf-8',
    )

    with pytest.raises(ValueError):
        RegionalConstitutionRegistry(tmp_path)
