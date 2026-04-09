import json
from pathlib import Path
from tempfile import TemporaryDirectory

from sa_nom_governance.integrations.model_provider_registry import ModelProviderRegistry
from sa_nom_governance.integrations.provider_dispatch_contract import (
    DISPATCH_CONTRACT_VERSION,
    DispatchContractError,
    DispatchRequestV1,
    contract_profile,
    provider_lane_to_runtime_id,
)
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


def test_dispatch_contract_profile_and_lane_mapping() -> None:
    profile = contract_profile()

    assert profile['contract_version'] == DISPATCH_CONTRACT_VERSION
    assert 'openai' in profile['supported_provider_lanes']
    assert 'claude' in profile['supported_provider_lanes']
    assert 'gemini' in profile['supported_provider_lanes']
    assert provider_lane_to_runtime_id('claude') == 'anthropic'



def test_dispatch_request_validation_rejects_invalid_payloads() -> None:
    try:
        DispatchRequestV1.from_payload({'provider_lane': 'openai', 'prompt': ''})
        assert False, 'Expected DispatchContractError for empty prompt'
    except DispatchContractError as error:
        assert error.code == 'invalid_request'

    try:
        DispatchRequestV1.from_payload({'provider_lane': 'unknown', 'prompt': 'hello'})
        assert False, 'Expected DispatchContractError for unknown provider lane'
    except DispatchContractError as error:
        assert error.code == 'invalid_request'



def test_dispatch_v1_openai_success_path_returns_contract_shape() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        config.openai_api_key = 'sk-test'
        config.openai_model = 'gpt-5.4-mini'
        fake = _FakeUrlopen({'/responses': {'output_text': 'PONG'}})
        registry = ModelProviderRegistry(config, urlopen=fake)

        result = registry.dispatch_v1(
            {
                'request_id': 'req-openai-001',
                'provider_lane': 'openai',
                'prompt': 'Reply with PONG.',
                'max_output_tokens': 64,
                'metadata': {'tenant_id': 'tenant-a'},
            }
        )

        assert result['contract_version'] == DISPATCH_CONTRACT_VERSION
        assert result['status'] == 'ok'
        assert result['provider_lane'] == 'openai'
        assert result['provider_id'] == 'openai'
        assert result['output_text'] == 'PONG'
        assert fake.calls[0]['payload']['model'] == 'gpt-5.4-mini'



def test_dispatch_v1_claude_lane_maps_to_anthropic_provider() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        config.anthropic_api_key = 'anthropic-test'
        config.anthropic_model = 'claude-sonnet-4-20250514'
        fake = _FakeUrlopen({'/v1/messages': {'content': [{'type': 'text', 'text': 'PONG'}]}})
        registry = ModelProviderRegistry(config, urlopen=fake)

        result = registry.dispatch_v1(
            {
                'request_id': 'req-claude-001',
                'provider_lane': 'claude',
                'prompt': 'Reply with PONG.',
                'max_output_tokens': 64,
            }
        )

        assert result['status'] == 'ok'
        assert result['provider_lane'] == 'claude'
        assert result['provider_id'] == 'anthropic'
        headers = {key.lower(): value for key, value in fake.calls[0]['headers'].items()}
        assert headers['x-api-key'] == 'anthropic-test'



def test_dispatch_v1_gemini_lane_returns_provider_unavailable() -> None:
    with TemporaryDirectory() as temp_dir:
        registry = ModelProviderRegistry(_base_config(temp_dir))

        result = registry.dispatch_v1(
            {
                'request_id': 'req-gemini-001',
                'provider_lane': 'gemini',
                'prompt': 'Reply with PONG.',
            }
        )

        assert result['status'] == 'error'
        assert result['error']['code'] == 'provider_unavailable'
        assert result['provider_lane'] == 'gemini'



def test_dispatch_v1_invalid_shape_returns_error_model() -> None:
    with TemporaryDirectory() as temp_dir:
        registry = ModelProviderRegistry(_base_config(temp_dir))

        result = registry.dispatch_v1(
            {
                'request_id': 'req-invalid-001',
                'provider_lane': 'openai',
                'prompt': 'Reply with PONG.',
                'max_output_tokens': 'sixty',
            }
        )

        assert result['status'] == 'error'
        assert result['error']['code'] == 'invalid_request'
        assert result['error']['http_status'] == 400


def test_dispatch_v1_schema_matches_contract_profile() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    schema_path = repo_root / 'resources' / 'config' / 'dispatch_v1_request.schema.json'
    schema = json.loads(schema_path.read_text(encoding='utf-8'))
    profile = contract_profile()

    assert schema['properties']['provider_lane']['enum'] == profile['supported_provider_lanes']
