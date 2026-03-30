import argparse
import json

from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.integrations.model_provider_registry import DEFAULT_PROBE_PROMPT, ModelProviderRegistry


def main() -> None:
    parser = argparse.ArgumentParser(description='Probe configured SA-NOM model providers.')
    parser.add_argument('--provider', default=None, help='Specific provider to probe: openai, anthropic, or ollama.')
    parser.add_argument('--prompt', default=None, help='Custom probe prompt.')
    parser.add_argument('--require-configured', action='store_true', help='Exit non-zero if no provider is configured.')
    args = parser.parse_args()

    registry = ModelProviderRegistry(AppConfig())
    result = registry.probe(provider_id=args.provider, prompt=args.prompt or DEFAULT_PROBE_PROMPT)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result['status'] == 'ok':
        return
    if result['status'] == 'disabled' and not args.require_configured:
        return
    raise SystemExit(1)


if __name__ == '__main__':
    main()
