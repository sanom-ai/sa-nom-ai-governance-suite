import json
from pathlib import Path


EXAMPLES_DIR = Path(__file__).resolve().parents[2] / 'examples'
JSON_EXAMPLES = [
    'owner_registration.example.json',
    'access_profiles.example.json',
    'generated_access_tokens.example.json',
    'trusted_registry_manifest.example.json',
    'guided_smoke_test.example.json',
    'runtime_startup_smoke.example.json',
    'provider_demo_flow.ollama.example.json',
]


def _load(name: str):
    return json.loads((EXAMPLES_DIR / name).read_text(encoding='utf-8'))


def test_json_examples_are_valid() -> None:
    for name in JSON_EXAMPLES:
        _load(name)


def test_guided_smoke_example_is_public_safe_and_ollama_first() -> None:
    payload = _load('guided_smoke_test.example.json')

    assert payload['provider']['recommended_provider'] == 'ollama'
    assert payload['provider']['selected_provider'] == 'ollama'
    assert payload['passed'] is True
    encoded = json.dumps(payload)
    assert 'TAWAN' not in encoded
    assert 'D:\\' not in encoded


def test_access_profile_example_matches_current_enterprise_profile_ids() -> None:
    payload = _load('access_profiles.example.json')

    profile_ids = [item['profile_id'] for item in payload]
    assert profile_ids == [
        'enterprise-operator',
        'enterprise-reviewer',
        'enterprise-auditor',
        'enterprise-viewer',
    ]
