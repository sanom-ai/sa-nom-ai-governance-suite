import argparse
import json
from collections.abc import Sequence

from sa_nom_governance.integrations.model_provider_registry import DEFAULT_PROBE_PROMPT, ModelProviderRegistry
from sa_nom_governance.utils.config import AppConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Probe configured SA-NOM model providers.')
    parser.add_argument('--provider', default=None, help='Specific provider to probe: openai, anthropic, or ollama.')
    parser.add_argument('--prompt', default=None, help='Custom probe prompt.')
    parser.add_argument('--require-configured', action='store_true', help='Exit non-zero if no provider is configured.')
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(list(argv) if argv is not None else None)

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
