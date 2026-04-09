from __future__ import annotations

from dataclasses import dataclass

DISPATCH_CONTRACT_VERSION = 'dispatch.v1'
SUPPORTED_PROVIDER_LANES: tuple[str, ...] = ('openai', 'claude', 'gemini', 'ollama')

_PROVIDER_LANE_ALIASES = {
    'openai': 'openai',
    'claude': 'anthropic',
    'anthropic': 'anthropic',
    'gemini': 'gemini',
    'ollama': 'ollama',
}

DISPATCH_ERROR_MODEL: dict[str, dict[str, object]] = {
    'invalid_request': {
        'http_status': 400,
        'description': 'Request shape failed contract validation.',
    },
    'policy_denied': {
        'http_status': 403,
        'description': 'Governance policy denied outbound dispatch.',
    },
    'approval_required': {
        'http_status': 409,
        'description': 'Human approval is required before dispatch.',
    },
    'provider_unavailable': {
        'http_status': 503,
        'description': 'Selected provider lane is unavailable or not configured.',
    },
    'dispatch_failed': {
        'http_status': 502,
        'description': 'Provider call failed after outbound dispatch attempt.',
    },
}


@dataclass(slots=True)
class DispatchContractError(ValueError):
    code: str
    message: str
    details: dict[str, object]

    @property
    def http_status(self) -> int:
        metadata = DISPATCH_ERROR_MODEL.get(self.code, {})
        value = metadata.get('http_status')
        return int(value) if isinstance(value, int) else 500

    def to_dict(self) -> dict[str, object]:
        return {
            'code': self.code,
            'message': self.message,
            'http_status': self.http_status,
            'details': self.details,
        }


@dataclass(slots=True)
class DispatchRequestV1:
    provider_lane: str
    prompt: str
    max_output_tokens: int
    request_id: str | None = None
    metadata: dict[str, object] | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, object]) -> 'DispatchRequestV1':
        provider_lane_raw = str(payload.get('provider_lane') or '').strip().lower()
        prompt = str(payload.get('prompt') or '').strip()
        max_output_tokens_raw = payload.get('max_output_tokens', 128)
        request_id = payload.get('request_id')
        metadata = payload.get('metadata')

        if not provider_lane_raw:
            raise DispatchContractError(
                code='invalid_request',
                message='provider_lane is required for dispatch.v1.',
                details={'field': 'provider_lane'},
            )
        if provider_lane_raw not in SUPPORTED_PROVIDER_LANES:
            raise DispatchContractError(
                code='invalid_request',
                message=f"Unsupported provider_lane '{provider_lane_raw}'.",
                details={'field': 'provider_lane', 'supported': list(SUPPORTED_PROVIDER_LANES)},
            )
        if not prompt:
            raise DispatchContractError(
                code='invalid_request',
                message='prompt is required for dispatch.v1.',
                details={'field': 'prompt'},
            )
        if len(prompt) > 12000:
            raise DispatchContractError(
                code='invalid_request',
                message='prompt exceeds dispatch.v1 limit.',
                details={'field': 'prompt', 'max_length': 12000},
            )
        if not isinstance(max_output_tokens_raw, int):
            raise DispatchContractError(
                code='invalid_request',
                message='max_output_tokens must be an integer.',
                details={'field': 'max_output_tokens'},
            )
        if max_output_tokens_raw < 1 or max_output_tokens_raw > 4096:
            raise DispatchContractError(
                code='invalid_request',
                message='max_output_tokens must be between 1 and 4096.',
                details={'field': 'max_output_tokens', 'min': 1, 'max': 4096},
            )
        if request_id is not None and not isinstance(request_id, str):
            raise DispatchContractError(
                code='invalid_request',
                message='request_id must be a string when provided.',
                details={'field': 'request_id'},
            )
        if metadata is not None and not isinstance(metadata, dict):
            raise DispatchContractError(
                code='invalid_request',
                message='metadata must be an object when provided.',
                details={'field': 'metadata'},
            )
        return cls(
            provider_lane=provider_lane_raw,
            prompt=prompt,
            max_output_tokens=max_output_tokens_raw,
            request_id=request_id.strip() if isinstance(request_id, str) else None,
            metadata=metadata if isinstance(metadata, dict) else None,
        )


def contract_profile() -> dict[str, object]:
    return {
        'contract_version': DISPATCH_CONTRACT_VERSION,
        'supported_provider_lanes': list(SUPPORTED_PROVIDER_LANES),
        'error_model': DISPATCH_ERROR_MODEL,
    }


def provider_lane_to_runtime_id(provider_lane: str) -> str:
    normalized = provider_lane.strip().lower()
    if normalized not in _PROVIDER_LANE_ALIASES:
        raise DispatchContractError(
            code='invalid_request',
            message=f"Unsupported provider_lane '{provider_lane}'.",
            details={'field': 'provider_lane', 'supported': list(SUPPORTED_PROVIDER_LANES)},
        )
    return _PROVIDER_LANE_ALIASES[normalized]


def build_dispatch_error(
    *,
    code: str,
    message: str,
    request_id: str | None = None,
    provider_lane: str | None = None,
    details: dict[str, object] | None = None,
) -> dict[str, object]:
    metadata = DISPATCH_ERROR_MODEL.get(code, {})
    return {
        'contract_version': DISPATCH_CONTRACT_VERSION,
        'status': 'error',
        'request_id': request_id,
        'provider_lane': provider_lane,
        'error': {
            'code': code,
            'message': message,
            'http_status': int(metadata.get('http_status', 500)),
            'details': details or {},
        },
    }


def build_dispatch_success(
    *,
    request_id: str | None,
    provider_lane: str,
    provider_id: str,
    model: str,
    output_text: str,
    duration_ms: int,
    metadata: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        'contract_version': DISPATCH_CONTRACT_VERSION,
        'status': 'ok',
        'request_id': request_id,
        'provider_lane': provider_lane,
        'provider_id': provider_id,
        'model': model,
        'duration_ms': duration_ms,
        'output_text': output_text,
        'metadata': metadata or {},
    }
