# Dispatch v1 Contract

`dispatch.v1` is the provider-neutral request contract for outbound model dispatch under SA-NOM governance runtime.

## Goal

Keep one stable API contract while allowing provider-specific adapters to evolve independently.

## Contract Version

- `contract_version`: `dispatch.v1`

## Request Shape

```json
{
  "request_id": "req-001",
  "provider_lane": "openai",
  "prompt": "Summarize current governance status.",
  "max_output_tokens": 256,
  "metadata": {
    "tenant_id": "tenant-a",
    "workflow_id": "wf-001"
  }
}
```

## Request Rules

- `provider_lane` is required.
- Allowed lanes: `openai`, `claude`, `gemini`, `ollama`.
- `prompt` is required and must not be empty.
- `max_output_tokens` is optional, integer range `1-4096`, default `128`.
- `metadata` is optional and must be an object.

## Provider Lane Mapping

- `openai` -> runtime provider id `openai`
- `claude` -> runtime provider id `anthropic`
- `gemini` -> runtime provider id `gemini` (contract lane reserved; runtime availability depends on provider adapter)
- `ollama` -> runtime provider id `ollama`

## Success Response

```json
{
  "contract_version": "dispatch.v1",
  "status": "ok",
  "request_id": "req-001",
  "provider_lane": "openai",
  "provider_id": "openai",
  "model": "gpt-5.4-mini",
  "duration_ms": 124,
  "output_text": "...",
  "metadata": {
    "tenant_id": "tenant-a"
  }
}
```

## Error Response

```json
{
  "contract_version": "dispatch.v1",
  "status": "error",
  "request_id": "req-001",
  "provider_lane": "openai",
  "error": {
    "code": "provider_unavailable",
    "message": "Selected provider lane is unavailable or not configured.",
    "http_status": 503,
    "details": {
      "runtime_provider_id": "openai"
    }
  }
}
```

## Error Model

- `invalid_request` (`400`): contract validation failed.
- `policy_denied` (`403`): governance policy blocked dispatch.
- `approval_required` (`409`): human approval required.
- `provider_unavailable` (`503`): provider lane unavailable/not configured.
- `dispatch_failed` (`502`): provider call attempted but failed.

## Current Runtime Behavior

- OpenAI lane: available when OpenAI credentials and model are configured.
- Claude lane: available via Anthropic adapter when Anthropic credentials and model are configured.
- Gemini lane: contract-recognized; returns `provider_unavailable` until Gemini runtime adapter is configured.
- Ollama lane: available when local model is configured.

## Related Artifacts

- [PROVIDER_SETUP.md](PROVIDER_SETUP.md)`r`n- [resources/config/dispatch_v1_request.schema.json](../resources/config/dispatch_v1_request.schema.json)
- [SELF_SERVE_GOVERNANCE_API_WORK_ORDER.md](SELF_SERVE_GOVERNANCE_API_WORK_ORDER.md)
- [examples/dispatch_v1_openai.example.json](../examples/dispatch_v1_openai.example.json)
- [examples/dispatch_v1_claude.example.json](../examples/dispatch_v1_claude.example.json)
- [examples/dispatch_v1_gemini.example.json](../examples/dispatch_v1_gemini.example.json)

