import json
import urllib.error
from pathlib import Path
from tempfile import TemporaryDirectory

from sa_nom_governance.deployment.ollama_demo_environment import build_ollama_demo_environment
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
    def __init__(self, response_map: dict[str, dict[str, object]] | None = None, *, offline_suffixes: set[str] | None = None) -> None:
        self.response_map = response_map or {}
        self.offline_suffixes = offline_suffixes or set()

    def __call__(self, request, timeout: int = 0):
        full_url = request.full_url
        for suffix in self.offline_suffixes:
            if full_url.endswith(suffix):
                raise urllib.error.URLError('connection refused')
        for suffix, payload in self.response_map.items():
            if full_url.endswith(suffix):
                return _FakeResponse(payload)
        raise AssertionError(f'Unexpected request URL: {full_url}')


def _base_config(temp_dir: str) -> AppConfig:
    compose_path = Path(temp_dir) / 'docker-compose.yml'
    compose_path.write_text('services:\n  ollama:\n    image: ollama/ollama:latest\n', encoding='utf-8')
    return AppConfig(base_dir=Path(temp_dir), persist_runtime=False, model_provider_timeout_seconds=7)


def test_ollama_demo_environment_starts_with_missing_model_guidance() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        report = build_ollama_demo_environment(config=config, urlopen=_FakeUrlopen(offline_suffixes={'/api/tags'}))

        assert report['status'] == 'disabled'
        assert report['environment']['missing_env_vars'] == ['SANOM_OLLAMA_MODEL']
        assert report['compose']['available'] is True
        assert any('SANOM_OLLAMA_MODEL=gemma3' in item for item in report['next_actions'])
        assert any('docker compose --profile local-llm up -d ollama' in item for item in report['next_actions'])


def test_ollama_demo_environment_reports_missing_pulled_model() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        config.default_model_provider = 'ollama'
        config.ollama_model = 'gemma3'
        report = build_ollama_demo_environment(
            config=config,
            urlopen=_FakeUrlopen({'/api/tags': {'models': [{'name': 'llama3.2:latest'}]}}),
        )

        assert report['status'] == 'partial'
        assert report['daemon']['status'] == 'missing-model'
        assert report['daemon']['model_present'] is False
        assert any('docker compose exec ollama ollama pull gemma3' in item for item in report['next_actions'])


def test_ollama_demo_environment_can_probe_ready_lane() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        config.default_model_provider = 'ollama'
        config.ollama_model = 'gemma3'
        report = build_ollama_demo_environment(
            config=config,
            urlopen=_FakeUrlopen(
                {
                    '/api/tags': {'models': [{'name': 'gemma3:latest'}]},
                    '/api/generate': {'response': 'PONG'},
                }
            ),
            probe=True,
        )

        assert report['status'] == 'ready'
        assert report['daemon']['status'] == 'ready'
        assert report['daemon']['model_present'] is True
        assert report['probe']['status'] == 'ok'
        assert report['probe']['results'][0]['output_text'] == 'PONG'
        assert any('python scripts/private_server_smoke_test.py' in item for item in report['next_actions'])
