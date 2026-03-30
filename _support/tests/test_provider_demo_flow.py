import json
from pathlib import Path
from tempfile import TemporaryDirectory

from sa_nom_governance.deployment.provider_demo_flow import build_provider_demo_flow
from sa_nom_governance.integrations.model_provider_registry import ModelProviderRegistry
from sa_nom_governance.utils.config import AppConfig


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

    def __call__(self, request, timeout: int = 0):
        for suffix, payload in self.response_map.items():
            if request.full_url.endswith(suffix):
                return _FakeResponse(payload)
        raise AssertionError(f'Unexpected request URL: {request.full_url}')


def _base_config(temp_dir: str) -> AppConfig:
    return AppConfig(base_dir=Path(temp_dir), persist_runtime=False, model_provider_timeout_seconds=7)


def test_provider_demo_flow_reports_missing_openai_settings() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        report = build_provider_demo_flow(config)

        openai = next(item for item in report['setup']['providers'] if item['provider_id'] == 'openai')
        assert report['status'] == 'disabled'
        assert openai['example_file'] == 'examples/.env.openai.example'
        assert openai['missing_env_vars'] == ['SANOM_OPENAI_API_KEY', 'SANOM_OPENAI_MODEL']


def test_provider_demo_flow_is_partial_when_provider_is_configured_without_default() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        config.openai_api_key = 'sk-test'
        config.openai_model = 'gpt-5.4-mini'

        report = build_provider_demo_flow(config)

        assert report['status'] == 'partial'
        assert report['recommended_provider'] == 'openai'
        assert any('SANOM_MODEL_PROVIDER_DEFAULT=openai' in item for item in report['setup']['next_actions'])


def test_provider_demo_flow_can_probe_selected_provider() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        config.default_model_provider = 'openai'
        config.openai_api_key = 'sk-test'
        config.openai_model = 'gpt-5.4-mini'
        registry = ModelProviderRegistry(config, urlopen=_FakeUrlopen({'/responses': {'output_text': 'PONG'}}))

        report = build_provider_demo_flow(config, registry=registry, provider_id='openai', probe=True)

        assert report['status'] == 'ready'
        assert report['selected_provider'] == 'openai'
        assert report['probe']['status'] == 'ok'
        assert report['probe']['results'][0]['output_text'] == 'PONG'
