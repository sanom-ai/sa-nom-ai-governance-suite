import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.integrations.model_provider_registry import DEFAULT_PROBE_PROMPT, ModelProviderRegistry


def build_provider_demo_flow(
    config: AppConfig | None = None,
    *,
    registry: ModelProviderRegistry | None = None,
    provider_id: str | None = None,
    probe: bool = False,
    prompt: str = DEFAULT_PROBE_PROMPT,
    max_output_tokens: int = 64,
) -> dict[str, object]:
    runtime_config = config or AppConfig()
    provider_registry = registry or ModelProviderRegistry(runtime_config)
    setup = provider_registry.setup_report(provider_id=provider_id)
    selected_provider = provider_id or setup.get('recommended_provider')
    selected_entry = next(
        (item for item in setup.get('providers', []) if item.get('provider_id') == selected_provider),
        None,
    )

    result: dict[str, object] = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'status': setup['status'],
        'default_provider': setup.get('default_provider'),
        'selected_provider': selected_provider,
        'recommended_provider': setup.get('recommended_provider'),
        'setup': setup,
        'demo_path': _build_demo_path(selected_entry),
        'probe': None,
    }

    if probe and selected_provider:
        probe_result = provider_registry.probe(
            provider_id=selected_provider,
            prompt=prompt,
            max_output_tokens=max_output_tokens,
        )
        result['probe'] = probe_result
        if probe_result.get('status') != 'ok':
            result['status'] = 'partial' if result['status'] != 'disabled' else 'disabled'

    return result


def _build_demo_path(selected_entry: dict[str, object] | None) -> list[dict[str, object]]:
    if selected_entry is None:
        return [
            {
                'step': 1,
                'title': 'Choose a provider lane',
                'action': 'Use Ollama as the default private demo lane, or choose OpenAI or Claude only when you need a hosted evaluation lane.',
            },
            {
                'step': 2,
                'title': 'Apply an example environment file',
                'action': 'Start with examples/.env.ollama.example for the default private demo lane unless you intentionally want a hosted evaluation lane.',
            },
            {
                'step': 3,
                'title': 'Set the runtime default provider',
                'action': 'Set SANOM_MODEL_PROVIDER_DEFAULT=ollama for the default private demo lane, or point it to a hosted provider only for evaluation needs.',
            },
            {
                'step': 4,
                'title': 'Run the provider probe',
                'action': 'Run `python scripts/provider_demo_flow.py --provider <provider-id> --probe`.',
            },
            {
                'step': 5,
                'title': 'Validate the runtime end-to-end',
                'action': 'Run `python scripts/private_server_smoke_test.py` after the provider probe passes.',
            },
        ]

    return [
        {
            'step': 1,
            'title': 'Load the provider template',
            'action': f"Use {selected_entry['example_file']} as the starting point for environment setup.",
        },
        {
            'step': 2,
            'title': 'Set the runtime default',
            'action': f"Set SANOM_MODEL_PROVIDER_DEFAULT={selected_entry['provider_id']}.",
        },
        {
            'step': 3,
            'title': 'Run the provider probe',
            'action': str(selected_entry['demo_flow_command']),
        },
        {
            'step': 4,
            'title': 'Run the provider smoke test',
            'action': str(selected_entry['smoke_test_command']),
        },
        {
            'step': 5,
            'title': 'Validate the full runtime path',
            'action': 'python scripts/private_server_smoke_test.py',
        },
        {
            'step': 6,
            'title': 'Capture the readiness artifact',
            'action': 'Archive the provider probe output with the release, pilot, or discovery-call notes.',
        },
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description='Build a demo-ready provider onboarding report for SA-NOM.')
    parser.add_argument('--provider', default=None, help='Specific provider to target: openai, anthropic, or ollama.')
    parser.add_argument('--probe', action='store_true', help='Probe the selected or recommended provider.')
    parser.add_argument('--prompt', default=DEFAULT_PROBE_PROMPT, help='Custom probe prompt to use when probing a provider.')
    parser.add_argument('--max-output-tokens', type=int, default=64, help='Maximum output tokens to request during a probe.')
    parser.add_argument('--output', default=None, help='Optional path to write the JSON report.')
    parser.add_argument('--require-ready', action='store_true', help='Exit non-zero unless the report status is ready.')
    args = parser.parse_args()

    report = build_provider_demo_flow(
        provider_id=args.provider,
        probe=args.probe,
        prompt=args.prompt,
        max_output_tokens=args.max_output_tokens,
    )
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    print(encoded)

    if args.output:
        Path(args.output).write_text(encoded + '\n', encoding='utf-8')

    if args.probe and report.get('probe') is not None and report['probe'].get('status') != 'ok':
        raise SystemExit(1)
    if args.require_ready and report.get('status') != 'ready':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
