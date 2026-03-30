import json
from pathlib import Path
from tempfile import TemporaryDirectory

from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.integrations.model_provider_registry import ModelProviderRegistry


class _FakeResponse:
    def __init__(self, payload: dict[str, object], status: int = 200) -> None:
        self._payload = payload
        self.status = status

    def read(self) -> bytes:
        return json.dumps(self._payload).encode('utf-8')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeUrlopen:
    def __init__(self, response_map: dict[str, dict[str, object]]) -> None:
        self.response_map = response_map
        self.calls: list[dict[str, object]] = []

    def __call__(self, request, timeout: int = 0):
        self.calls.append(
            {
                'url': request.full_url,
                'headers': dict(request.header_items()),
                'payload': json.loads(request.data.decode('utf-8')),
                'timeout': timeout,
            }
        )
        for suffix, payload in self.response_map.items():
            if request.full_url.endswith(suffix):
                return _FakeResponse(payload)
        raise AssertionError(f'Unexpected request URL: {request.full_url}')


def _base_config(temp_dir: str) -> AppConfig:
    return AppConfig(base_dir=Path(temp_dir), persist_runtime=False, model_provider_timeout_seconds=7)


def test_model_provider_health_marks_default_provider_ready() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        config.default_model_provider = 'openai'
        config.openai_api_key = 'sk-test'
        config.openai_model = 'gpt-5.4-mini'
        registry = ModelProviderRegistry(config)

        health = registry.health()

        assert health['status'] == 'configured'
        assert health['default_provider'] == 'openai'
        assert health['default_provider_ready'] is True
        assert health['configured_providers'] == 1


def test_model_provider_setup_report_defaults_to_ollama_for_private_demo_lane() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        registry = ModelProviderRegistry(config)

        report = registry.setup_report()

        assert report['status'] == 'disabled'
        assert report['recommended_provider'] == 'ollama'
        assert any('SANOM_MODEL_PROVIDER_DEFAULT=ollama' in item for item in report['next_actions'])


def test_model_provider_probe_supports_openai_responses_api() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        config.openai_api_key = 'sk-test'
        config.openai_model = 'gpt-5.4-mini'
        fake = _FakeUrlopen({'/responses': {'output_text': 'PONG'}})
        registry = ModelProviderRegistry(config, urlopen=fake)

        result = registry.probe(provider_id='openai')

        assert result['status'] == 'ok'
        assert result['results'][0]['output_text'] == 'PONG'
        assert fake.calls[0]['payload']['model'] == 'gpt-5.4-mini'
        assert fake.calls[0]['payload']['input']


def test_model_provider_probe_supports_anthropic_messages_api() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        config.anthropic_api_key = 'anthropic-test'
        config.anthropic_model = 'claude-sonnet-4-20250514'
        fake = _FakeUrlopen({'/v1/messages': {'content': [{'type': 'text', 'text': 'PONG'}]}})
        registry = ModelProviderRegistry(config, urlopen=fake)

        result = registry.probe(provider_id='anthropic')

        assert result['status'] == 'ok'
        assert result['results'][0]['output_text'] == 'PONG'
        headers = {key.lower(): value for key, value in fake.calls[0]['headers'].items()}
        assert headers['x-api-key'] == 'anthropic-test'
        assert fake.calls[0]['payload']['messages'][0]['role'] == 'user'


def test_model_provider_probe_supports_ollama_generate_api() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        config.ollama_model = 'gemma3'
        fake = _FakeUrlopen({'/api/generate': {'response': 'PONG'}})
        registry = ModelProviderRegistry(config, urlopen=fake)

        result = registry.probe(provider_id='ollama')

        assert result['status'] == 'ok'
        assert result['results'][0]['output_text'] == 'PONG'
        assert fake.calls[0]['payload']['stream'] is False


def test_model_provider_probe_fails_cleanly_when_provider_is_partial() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        config.default_model_provider = 'openai'
        config.openai_model = 'gpt-5.4-mini'
        registry = ModelProviderRegistry(config)

        result = registry.probe(provider_id='openai')

        assert result['status'] == 'error'
        assert result['results'][0]['reason'] == 'OpenAI model is set but API key is missing.'
