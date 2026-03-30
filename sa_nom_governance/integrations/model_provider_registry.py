import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Callable

from sa_nom_governance.utils.config import AppConfig


DEFAULT_OPENAI_BASE_URL = 'https://api.openai.com/v1'
DEFAULT_ANTHROPIC_BASE_URL = 'https://api.anthropic.com'
DEFAULT_ANTHROPIC_VERSION = '2023-06-01'
DEFAULT_OLLAMA_BASE_URL = 'http://localhost:11434'
DEFAULT_PROBE_PROMPT = 'Reply with PONG and no extra words.'


@dataclass(slots=True)
class ProviderConfig:
    provider_id: str
    provider_type: str
    endpoint_url: str
    model: str
    timeout_seconds: int
    auth_mode: str
    configured: bool
    reason: str
    api_key: str | None = None
    anthropic_version: str | None = None

    def to_public_dict(self, *, default_provider: str | None = None) -> dict[str, object]:
        return {
            'provider_id': self.provider_id,
            'provider_type': self.provider_type,
            'endpoint_url': self.endpoint_url,
            'model': self.model,
            'timeout_seconds': self.timeout_seconds,
            'auth_mode': self.auth_mode,
            'configured': self.configured,
            'status': 'configured' if self.configured else 'partial',
            'reason': self.reason,
            'default': self.provider_id == (default_provider or ''),
        }


@dataclass(slots=True)
class ProviderProbeResult:
    provider_id: str
    provider_type: str
    status: str
    reason: str
    endpoint_url: str
    model: str
    duration_ms: int
    http_status: int | None = None
    response_excerpt: str | None = None
    output_text: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            'provider_id': self.provider_id,
            'provider_type': self.provider_type,
            'status': self.status,
            'reason': self.reason,
            'endpoint_url': self.endpoint_url,
            'model': self.model,
            'duration_ms': self.duration_ms,
            'http_status': self.http_status,
            'response_excerpt': self.response_excerpt,
            'output_text': self.output_text,
        }


class ModelProviderRegistry:
    def __init__(self, config: AppConfig, *, urlopen: Callable[..., Any] | None = None) -> None:
        self.config = config
        self._urlopen = urlopen or urllib.request.urlopen
        self.providers = self._build_provider_catalog()

    def _build_provider_catalog(self) -> dict[str, ProviderConfig]:
        timeout = self.config.model_provider_timeout_seconds
        providers = {
            'openai': ProviderConfig(
                provider_id='openai',
                provider_type='openai',
                endpoint_url=f"{self.config.openai_base_url.rstrip('/')}/responses",
                model=self.config.openai_model,
                timeout_seconds=timeout,
                auth_mode='bearer',
                configured=bool(self.config.openai_api_key and self.config.openai_model),
                reason=self._provider_reason('OpenAI', self.config.openai_api_key, self.config.openai_model),
                api_key=self.config.openai_api_key,
            ),
            'anthropic': ProviderConfig(
                provider_id='anthropic',
                provider_type='anthropic',
                endpoint_url=f"{self.config.anthropic_base_url.rstrip('/')}/v1/messages",
                model=self.config.anthropic_model,
                timeout_seconds=timeout,
                auth_mode='x-api-key',
                configured=bool(self.config.anthropic_api_key and self.config.anthropic_model),
                reason=self._provider_reason('Anthropic', self.config.anthropic_api_key, self.config.anthropic_model),
                api_key=self.config.anthropic_api_key,
                anthropic_version=self.config.anthropic_version,
            ),
            'ollama': ProviderConfig(
                provider_id='ollama',
                provider_type='ollama',
                endpoint_url=f"{self.config.ollama_base_url.rstrip('/')}/api/generate",
                model=self.config.ollama_model,
                timeout_seconds=timeout,
                auth_mode='none',
                configured=bool(self.config.ollama_model),
                reason='Ollama model configured.' if self.config.ollama_model else 'Configure SANOM_OLLAMA_MODEL to enable Ollama probes.',
            ),
        }
        return providers

    def _provider_reason(self, vendor: str, api_key: str | None, model: str | None) -> str:
        if api_key and model:
            return f'{vendor} credentials and model are configured.'
        if api_key and not model:
            return f'{vendor} API key is set but model is missing.'
        if model and not api_key:
            return f'{vendor} model is set but API key is missing.'
        return f'{vendor} provider is disabled until credentials and model are configured.'

    def health(self) -> dict[str, object]:
        default_provider = (self.config.default_model_provider or '').strip().lower() or None
        providers = [provider.to_public_dict(default_provider=default_provider) for provider in self.providers.values()]
        configured_total = sum(1 for provider in self.providers.values() if provider.configured)
        partial_total = sum(1 for provider in self.providers.values() if not provider.configured and provider.model)
        default_ready = bool(default_provider and default_provider in self.providers and self.providers[default_provider].configured)
        if configured_total == 0:
            status = 'disabled'
        elif default_provider and not default_ready:
            status = 'partial'
        elif partial_total:
            status = 'partial'
        else:
            status = 'configured'
        return {
            'status': status,
            'default_provider': default_provider,
            'default_provider_ready': default_ready if default_provider else None,
            'configured_providers': configured_total,
            'partial_providers': partial_total,
            'providers': providers,
        }

    def configured_providers(self) -> list[ProviderConfig]:
        return [provider for provider in self.providers.values() if provider.configured]

    def generate(
        self,
        prompt: str,
        *,
        provider_id: str | None = None,
        max_output_tokens: int = 128,
    ) -> dict[str, object]:
        provider = self._resolve_provider(provider_id)
        result = self._probe_provider(provider, prompt=prompt, max_output_tokens=max_output_tokens)
        if result.status != 'ok':
            raise ValueError(result.reason)
        return result.to_dict()

    def probe(
        self,
        *,
        provider_id: str | None = None,
        prompt: str = DEFAULT_PROBE_PROMPT,
        max_output_tokens: int = 64,
    ) -> dict[str, object]:
        generated_at = datetime.now(timezone.utc).isoformat()
        if provider_id:
            provider = self.providers.get(provider_id)
            if provider is None:
                return {
                    'generated_at': generated_at,
                    'status': 'error',
                    'default_provider': self.health().get('default_provider'),
                    'providers_total': 0,
                    'successful_providers': 0,
                    'failed_providers': 1,
                    'results': [
                        {
                            'provider_id': provider_id,
                            'provider_type': 'unknown',
                            'status': 'error',
                            'reason': f'Unknown provider: {provider_id}',
                            'endpoint_url': '',
                            'model': '',
                            'duration_ms': 0,
                        }
                    ],
                }
            if not provider.configured:
                return {
                    'generated_at': generated_at,
                    'status': 'error',
                    'default_provider': self.health().get('default_provider'),
                    'providers_total': 1,
                    'successful_providers': 0,
                    'failed_providers': 1,
                    'results': [
                        {
                            'provider_id': provider.provider_id,
                            'provider_type': provider.provider_type,
                            'status': 'error',
                            'reason': provider.reason,
                            'endpoint_url': provider.endpoint_url,
                            'model': provider.model,
                            'duration_ms': 0,
                        }
                    ],
                }
            targets = [provider]
        else:
            targets = self.configured_providers()

        if not targets:
            return {
                'generated_at': generated_at,
                'status': 'disabled',
                'default_provider': self.health().get('default_provider'),
                'providers_total': 0,
                'successful_providers': 0,
                'failed_providers': 0,
                'results': [],
            }

        results = [
            self._probe_provider(provider, prompt=prompt, max_output_tokens=max_output_tokens).to_dict()
            for provider in targets
        ]
        failed_total = sum(1 for item in results if item['status'] != 'ok')
        return {
            'generated_at': generated_at,
            'status': 'ok' if failed_total == 0 else 'partial',
            'default_provider': self.health().get('default_provider'),
            'providers_total': len(targets),
            'successful_providers': len(targets) - failed_total,
            'failed_providers': failed_total,
            'results': results,
        }

    def _resolve_provider(self, provider_id: str | None) -> ProviderConfig:
        candidate = (provider_id or self.config.default_model_provider or '').strip().lower()
        if candidate:
            provider = self.providers.get(candidate)
            if provider is None:
                raise ValueError(f'Unknown provider: {candidate}')
            if not provider.configured:
                raise ValueError(provider.reason)
            return provider
        configured = self.configured_providers()
        if not configured:
            raise ValueError('No model provider is configured.')
        return configured[0]

    def _probe_provider(self, provider: ProviderConfig, *, prompt: str, max_output_tokens: int) -> ProviderProbeResult:
        started = perf_counter()
        try:
            if provider.provider_id == 'openai':
                status_code, payload = self._post_json(
                    provider.endpoint_url,
                    {
                        'Authorization': f'Bearer {provider.api_key}',
                        'Content-Type': 'application/json',
                    },
                    {
                        'model': provider.model,
                        'input': prompt,
                        'max_output_tokens': max_output_tokens,
                    },
                    timeout=provider.timeout_seconds,
                )
                output_text = self._extract_openai_output(payload)
                reason = 'OpenAI Responses API probe succeeded.'
            elif provider.provider_id == 'anthropic':
                status_code, payload = self._post_json(
                    provider.endpoint_url,
                    {
                        'x-api-key': str(provider.api_key),
                        'anthropic-version': str(provider.anthropic_version or DEFAULT_ANTHROPIC_VERSION),
                        'content-type': 'application/json',
                    },
                    {
                        'model': provider.model,
                        'max_tokens': max_output_tokens,
                        'messages': [{'role': 'user', 'content': prompt}],
                    },
                    timeout=provider.timeout_seconds,
                )
                output_text = self._extract_anthropic_output(payload)
                reason = 'Anthropic Messages API probe succeeded.'
            else:
                status_code, payload = self._post_json(
                    provider.endpoint_url,
                    {'Content-Type': 'application/json'},
                    {
                        'model': provider.model,
                        'prompt': prompt,
                        'stream': False,
                    },
                    timeout=provider.timeout_seconds,
                )
                output_text = str(payload.get('response') or '').strip()
                reason = 'Ollama API probe succeeded.'

            return ProviderProbeResult(
                provider_id=provider.provider_id,
                provider_type=provider.provider_type,
                status='ok',
                reason=reason,
                endpoint_url=provider.endpoint_url,
                model=provider.model,
                duration_ms=int((perf_counter() - started) * 1000),
                http_status=status_code,
                response_excerpt=self._excerpt(output_text or json.dumps(payload, ensure_ascii=False)),
                output_text=output_text,
            )
        except (urllib.error.URLError, ValueError) as error:
            return ProviderProbeResult(
                provider_id=provider.provider_id,
                provider_type=provider.provider_type,
                status='error',
                reason=str(error),
                endpoint_url=provider.endpoint_url,
                model=provider.model,
                duration_ms=int((perf_counter() - started) * 1000),
            )

    def _post_json(
        self,
        url: str,
        headers: dict[str, str],
        payload: dict[str, object],
        *,
        timeout: int,
    ) -> tuple[int, dict[str, object]]:
        request = urllib.request.Request(
            url=url,
            data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
            headers=headers,
            method='POST',
        )
        try:
            with self._urlopen(request, timeout=timeout) as response:
                raw = response.read().decode('utf-8', errors='replace')
                parsed = json.loads(raw) if raw.strip() else {}
                return int(getattr(response, 'status', 200)), parsed if isinstance(parsed, dict) else {'payload': parsed}
        except urllib.error.HTTPError as error:
            raw = error.read().decode('utf-8', errors='replace')
            excerpt = self._excerpt(raw)
            raise ValueError(f'HTTP {getattr(error, "code", "error")}: {excerpt}') from error

    def _extract_openai_output(self, payload: dict[str, object]) -> str:
        output_text = str(payload.get('output_text') or '').strip()
        if output_text:
            return output_text
        fragments: list[str] = []
        for item in payload.get('output', []) or []:
            if not isinstance(item, dict):
                continue
            for content in item.get('content', []) or []:
                if isinstance(content, dict) and content.get('type') == 'output_text' and content.get('text'):
                    fragments.append(str(content['text']).strip())
        joined = '\n'.join(fragment for fragment in fragments if fragment)
        if joined:
            return joined
        raise ValueError('OpenAI response did not contain output text.')

    def _extract_anthropic_output(self, payload: dict[str, object]) -> str:
        fragments = [
            str(item.get('text')).strip()
            for item in payload.get('content', []) or []
            if isinstance(item, dict) and item.get('type') == 'text' and item.get('text')
        ]
        joined = '\n'.join(fragment for fragment in fragments if fragment)
        if joined:
            return joined
        raise ValueError('Anthropic response did not contain text content.')

    def _excerpt(self, value: str | None, *, limit: int = 240) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        if len(text) <= limit:
            return text
        return f"{text[:limit - 3]}..."
