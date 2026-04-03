import io
import json
import urllib.error
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from sa_nom_governance.integrations.model_provider_registry import ModelProviderRegistry, ProviderProbeResult
from sa_nom_governance.utils.config import AppConfig


class _FakeResponse:
    def __init__(self, payload, status: int = 200) -> None:
        self._payload = payload
        self.status = status

    def read(self) -> bytes:
        if isinstance(self._payload, bytes):
            return self._payload
        return json.dumps(self._payload).encode('utf-8')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False



def _base_config(temp_dir: str) -> AppConfig:
    return AppConfig(base_dir=Path(temp_dir), persist_runtime=False, model_provider_timeout_seconds=7)



def test_setup_report_handles_targeted_provider_and_unknown_provider() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        config.openai_api_key = 'sk-test'
        config.openai_model = 'gpt-5.4-mini'
        registry = ModelProviderRegistry(config)

        report = registry.setup_report(provider_id='openai')

        assert report['status'] == 'ready'
        assert report['providers_total'] == 1
        assert report['providers'][0]['provider_id'] == 'openai'
        assert any('provider_smoke_test.py --provider openai' in item for item in report['next_actions'])

        with pytest.raises(ValueError, match='Unknown provider: missing'):
            registry.setup_report(provider_id='missing')



def test_health_and_setup_report_show_partial_default_not_ready() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        config.default_model_provider = 'openai'
        config.openai_model = 'gpt-5.4-mini'
        registry = ModelProviderRegistry(config)

        health = registry.health()
        report = registry.setup_report()

        assert health['status'] == 'disabled'
        assert health['default_provider_ready'] is False
        assert report['status'] == 'partial'
        assert report['partial_providers'] == 1
        assert any('SANOM_OPENAI_API_KEY' in item['missing_env_vars'] for item in report['providers'] if item['provider_id'] == 'openai')



def test_probe_handles_unknown_provider_and_disabled_registry() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        registry = ModelProviderRegistry(config)

        unknown = registry.probe(provider_id='missing')
        disabled = registry.probe()

        assert unknown['status'] == 'error'
        assert unknown['results'][0]['provider_type'] == 'unknown'
        assert disabled['status'] == 'disabled'
        assert disabled['results'] == []



def test_generate_and_resolve_provider_paths(monkeypatch) -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        config.openai_api_key = 'sk-test'
        config.openai_model = 'gpt-5.4-mini'
        config.default_model_provider = 'openai'
        registry = ModelProviderRegistry(config)

        monkeypatch.setattr(
            registry,
            '_probe_provider',
            lambda provider, **kwargs: ProviderProbeResult(
                provider_id=provider.provider_id,
                provider_type=provider.provider_type,
                status='ok',
                reason='ready',
                endpoint_url=provider.endpoint_url,
                model=provider.model,
                duration_ms=1,
                output_text='PONG',
            ),
        )
        generated = registry.generate('Reply with PONG.')
        assert generated['output_text'] == 'PONG'

        monkeypatch.setattr(
            registry,
            '_probe_provider',
            lambda provider, **kwargs: ProviderProbeResult(
                provider_id=provider.provider_id,
                provider_type=provider.provider_type,
                status='error',
                reason='provider failed',
                endpoint_url=provider.endpoint_url,
                model=provider.model,
                duration_ms=1,
            ),
        )
        with pytest.raises(ValueError, match='provider failed'):
            registry.generate('Reply with PONG.')

        assert registry._resolve_provider(None).provider_id == 'openai'
        with pytest.raises(ValueError, match='Unknown provider: missing'):
            registry._resolve_provider('missing')

    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        config.openai_model = 'gpt-5.4-mini'
        partial_registry = ModelProviderRegistry(config)
        with pytest.raises(ValueError, match='OpenAI model is set but API key is missing.'):
            partial_registry._resolve_provider('openai')

    with TemporaryDirectory() as temp_dir:
        empty_registry = ModelProviderRegistry(_base_config(temp_dir))
        with pytest.raises(ValueError, match='No model provider is configured.'):
            empty_registry._resolve_provider(None)



def test_post_json_handles_non_dict_payload_empty_body_and_http_errors() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        registry = ModelProviderRegistry(config, urlopen=lambda request, timeout=0: _FakeResponse(['pong']))
        status, payload = registry._post_json('https://example.test', {'Content-Type': 'application/json'}, {'ping': True}, timeout=5)
        assert status == 200
        assert payload == {'payload': ['pong']}

        registry = ModelProviderRegistry(config, urlopen=lambda request, timeout=0: _FakeResponse(b'   '))
        status, payload = registry._post_json('https://example.test', {'Content-Type': 'application/json'}, {'ping': True}, timeout=5)
        assert payload == {}

        def _raise_http_error(request, timeout=0):
            raise urllib.error.HTTPError(request.full_url, 500, 'boom', hdrs=None, fp=io.BytesIO(b'{"error": "downstream"}'))

        registry = ModelProviderRegistry(config, urlopen=_raise_http_error)
        with pytest.raises(ValueError, match='HTTP 500'):
            registry._post_json('https://example.test', {'Content-Type': 'application/json'}, {'ping': True}, timeout=5)



def test_extract_output_fallbacks_and_excerpt() -> None:
    with TemporaryDirectory() as temp_dir:
        registry = ModelProviderRegistry(_base_config(temp_dir))

        openai_text = registry._extract_openai_output(
            {
                'output': [
                    {'content': [{'type': 'output_text', 'text': 'PONG'}]},
                    {'content': [{'type': 'output_text', 'text': 'READY'}]},
                ]
            }
        )
        anthropic_text = registry._extract_anthropic_output({'content': [{'type': 'text', 'text': 'PONG'}]})
        excerpt = registry._excerpt('x' * 400, limit=40)

        assert openai_text == 'PONG\nREADY'
        assert anthropic_text == 'PONG'
        assert excerpt.endswith('...')
        assert registry._excerpt(None) is None

        with pytest.raises(ValueError, match='OpenAI response did not contain output text'):
            registry._extract_openai_output({'output': []})
        with pytest.raises(ValueError, match='Anthropic response did not contain text content'):
            registry._extract_anthropic_output({'content': []})
