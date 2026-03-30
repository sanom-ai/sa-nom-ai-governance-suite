import argparse
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit, urlunsplit

from sa_nom_governance.integrations.model_provider_registry import ModelProviderRegistry
from sa_nom_governance.utils.config import AppConfig


DEFAULT_COMPOSE_PROFILE = 'local-llm'
DEFAULT_RECOMMENDED_MODEL = 'gemma3'
DEFAULT_OUTPUT_PATH = '_review/ollama_demo_environment.json'


def build_ollama_demo_environment(
    config: AppConfig | None = None,
    *,
    registry: ModelProviderRegistry | None = None,
    urlopen: Callable[..., Any] | None = None,
    probe: bool = False,
) -> dict[str, object]:
    runtime_config = config or AppConfig()
    urlopen_fn = urlopen or urllib.request.urlopen
    provider_registry = registry or ModelProviderRegistry(runtime_config, urlopen=urlopen_fn)

    provider_setup = provider_registry.setup_report(provider_id='ollama')
    provider_entry = provider_setup['providers'][0]
    default_provider = (runtime_config.default_model_provider or '').strip().lower() or None
    requested_model = runtime_config.ollama_model.strip()
    daemon = _probe_ollama_daemon(
        runtime_config.ollama_base_url,
        model=requested_model,
        urlopen=urlopen_fn,
        timeout=runtime_config.model_provider_timeout_seconds,
    )
    compose = _build_compose_plan(runtime_config.base_dir, model=requested_model)

    status = _environment_status(
        provider_entry=provider_entry,
        daemon=daemon,
        default_provider=default_provider,
    )

    result: dict[str, object] = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'status': status,
        'default_provider': default_provider,
        'default_private_demo_lane': 'ollama',
        'environment': {
            'example_file': provider_entry['example_file'],
            'default_provider_is_ollama': default_provider == 'ollama',
            'ollama_base_url': runtime_config.ollama_base_url,
            'ollama_model': requested_model,
            'missing_env_vars': list(provider_entry['missing_env_vars']),
        },
        'compose': compose,
        'daemon': daemon,
        'provider_setup': provider_setup,
        'probe': None,
        'artifacts': {
            'default_output_path': str(runtime_config.base_dir / DEFAULT_OUTPUT_PATH),
        },
        'next_actions': [],
    }

    if probe:
        probe_result = provider_registry.probe(provider_id='ollama')
        result['probe'] = probe_result
        if probe_result.get('status') != 'ok' and result['status'] == 'ready':
            result['status'] = 'partial'

    result['next_actions'] = _build_next_actions(
        provider_entry=provider_entry,
        default_provider=default_provider,
        daemon=daemon,
        compose=compose,
        probe_result=result['probe'],
    )
    return result


def _environment_status(
    *,
    provider_entry: dict[str, object],
    daemon: dict[str, object],
    default_provider: str | None,
) -> str:
    if not provider_entry['configured']:
        return 'disabled'
    if daemon['status'] not in {'ready', 'online'}:
        return 'partial'
    if daemon['model_present'] is False:
        return 'partial'
    if default_provider != 'ollama':
        return 'partial'
    return 'ready'


def _build_compose_plan(base_dir: Path, *, model: str) -> dict[str, object]:
    compose_path = base_dir / 'docker-compose.yml'
    effective_model = model or DEFAULT_RECOMMENDED_MODEL
    return {
        'path': str(compose_path),
        'available': compose_path.exists(),
        'profile': DEFAULT_COMPOSE_PROFILE,
        'service': 'ollama',
        'startup_command': 'docker compose --profile local-llm up -d ollama',
        'full_stack_command': 'docker compose --profile local-llm up -d',
        'model_pull_command': f'docker compose exec ollama ollama pull {effective_model}',
        'model_list_command': 'docker compose exec ollama ollama list',
        'logs_command': 'docker compose logs ollama --tail=50',
        'stop_command': 'docker compose stop ollama',
        'recommended_model': effective_model,
    }


def _probe_ollama_daemon(
    base_url: str,
    *,
    model: str,
    urlopen: Callable[..., Any],
    timeout: int,
) -> dict[str, object]:
    tags_url = _ollama_tags_url(base_url)
    request = urllib.request.Request(tags_url, method='GET')
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode('utf-8', errors='replace')
            payload = json.loads(raw) if raw.strip() else {}
            if not isinstance(payload, dict):
                raise ValueError('Ollama tags response was not a JSON object.')
    except urllib.error.URLError as error:
        return {
            'status': 'offline',
            'base_url': base_url,
            'tags_url': tags_url,
            'reachable': False,
            'model_requested': model or None,
            'model_present': False if model else None,
            'models_total': 0,
            'models': [],
            'reason': str(error),
        }
    except ValueError as error:
        return {
            'status': 'error',
            'base_url': base_url,
            'tags_url': tags_url,
            'reachable': False,
            'model_requested': model or None,
            'model_present': False if model else None,
            'models_total': 0,
            'models': [],
            'reason': str(error),
        }

    models = [str(item.get('name')).strip() for item in payload.get('models', []) if isinstance(item, dict) and item.get('name')]
    if model:
        model_present = any(_ollama_model_matches(name, model) for name in models)
        status = 'ready' if model_present else 'missing-model'
        reason = 'Requested model is available in the Ollama daemon.' if model_present else 'Ollama is reachable but the requested model is not installed yet.'
    else:
        model_present = None
        status = 'online'
        reason = 'Ollama daemon is reachable but SANOM_OLLAMA_MODEL is not configured yet.'

    return {
        'status': status,
        'base_url': base_url,
        'tags_url': tags_url,
        'reachable': True,
        'model_requested': model or None,
        'model_present': model_present,
        'models_total': len(models),
        'models': models,
        'reason': reason,
    }


def _ollama_tags_url(base_url: str) -> str:
    parts = urlsplit(base_url)
    path = parts.path.rstrip('/')
    if path.endswith('/api/tags'):
        resolved_path = path
    elif path.endswith('/api'):
        resolved_path = f'{path}/tags'
    else:
        resolved_path = f'{path}/api/tags' if path else '/api/tags'
    return urlunsplit((parts.scheme or 'http', parts.netloc, resolved_path, '', ''))


def _ollama_model_matches(available_model: str, requested_model: str) -> bool:
    available = available_model.strip().lower()
    requested = requested_model.strip().lower()
    return available == requested or available.startswith(f'{requested}:')


def _build_next_actions(
    *,
    provider_entry: dict[str, object],
    default_provider: str | None,
    daemon: dict[str, object],
    compose: dict[str, object],
    probe_result: dict[str, object] | None,
) -> list[str]:
    actions: list[str] = []
    requested_model = str(daemon.get('model_requested') or '')
    effective_model = requested_model or str(compose['recommended_model'])

    if not provider_entry['configured']:
        actions.append(f"Start from {provider_entry['example_file']} and set SANOM_OLLAMA_MODEL={effective_model}.")
    if default_provider != 'ollama':
        actions.append('Set SANOM_MODEL_PROVIDER_DEFAULT=ollama for the default private demo lane.')

    if not daemon['reachable']:
        if compose['available']:
            actions.append(f"Start the local Ollama service with `{compose['startup_command']}`.")
            actions.append(f"Follow with `{compose['model_pull_command']}` once the service is up.")
        actions.append('If you are not using Docker, start a local daemon with `ollama serve`.')
        actions.append('Re-run `python scripts/ollama_demo_environment.py` after the daemon is reachable.')
        return actions

    if daemon['model_present'] is False:
        if compose['available']:
            actions.append(f"Install the requested model with `{compose['model_pull_command']}`.")
        actions.append(f'Or run `ollama pull {effective_model}` if you are using a host-level Ollama install.')
        actions.append('Re-run `python scripts/ollama_demo_environment.py --probe` after the model is available.')
        return actions

    if probe_result is not None and probe_result.get('status') != 'ok':
        actions.append('The Ollama lane is present but the probe did not complete successfully yet.')
        actions.append('Review the probe output and then rerun `python scripts/ollama_demo_environment.py --probe`.')
        return actions

    actions.append('Run `python scripts/ollama_demo_environment.py --probe --output _review/ollama_demo_environment.json` for a customer-facing readiness artifact.')
    actions.append('Run `python scripts/provider_demo_flow.py --provider ollama --probe` to capture the provider-specific report.')
    actions.append('Run `python scripts/private_server_smoke_test.py` to validate the full runtime path.')
    actions.append('Archive the Ollama environment and provider reports with the demo or release notes.')
    return actions


def main() -> None:
    parser = argparse.ArgumentParser(description='Build a real-world Ollama demo-environment report for SA-NOM.')
    parser.add_argument('--probe', action='store_true', help='Run the Ollama provider probe when the environment appears ready enough.')
    parser.add_argument('--output', default=DEFAULT_OUTPUT_PATH, help='Optional path to write the JSON report.')
    parser.add_argument('--require-ready', action='store_true', help='Exit non-zero unless the environment report status is ready.')
    args = parser.parse_args()

    report = build_ollama_demo_environment(probe=args.probe)
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
