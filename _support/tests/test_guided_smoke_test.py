from pathlib import Path
from tempfile import TemporaryDirectory

from sa_nom_governance.deployment.guided_smoke_test import build_guided_smoke_test
from sa_nom_governance.utils.config import AppConfig


def _base_config(temp_dir: str) -> AppConfig:
    return AppConfig(base_dir=Path(temp_dir), persist_runtime=True, environment='development')


def test_guided_smoke_test_bootstraps_first_run_and_defaults_to_ollama() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        report = build_guided_smoke_test(config=config, registration_code='demo-org')

        assert report['passed'] is True
        assert report['steps']['public_resources']['action'] == 'seeded'
        assert report['steps']['owner_registration']['action'] == 'created'
        assert report['steps']['access_profiles']['action'] == 'created'
        assert report['steps']['trusted_registry']['action'] == 'refreshed'
        assert report['startup']['ready'] is True
        assert report['provider']['recommended_provider'] == 'ollama'
        assert report['provider']['selected_provider'] == 'ollama'
        assert report['runtime_smoke']['passed'] is True
        assert report['performance_baseline']['status'] in {'ready', 'monitoring', 'critical', 'failed'}
        assert Path(report['artifacts']['runtime_performance_baseline']).exists()
        assert config.owner_registration_path is not None and config.owner_registration_path.exists()
        assert config.access_profiles_path is not None and config.access_profiles_path.exists()
        assert config.trusted_registry_manifest_path is not None and config.trusted_registry_manifest_path.exists()
        assert config.trusted_registry_cache_path is not None and config.trusted_registry_cache_path.exists()


def test_guided_smoke_test_reuses_existing_bootstrap_artifacts_on_rerun() -> None:
    with TemporaryDirectory() as temp_dir:
        config = _base_config(temp_dir)
        build_guided_smoke_test(config=config, registration_code='demo-org')
        report = build_guided_smoke_test(config=config, registration_code='demo-org', skip_runtime_smoke=True)

        assert report['passed'] is True
        assert report['steps']['public_resources']['action'] == 'existing'
        assert report['steps']['owner_registration']['action'] == 'existing'
        assert report['steps']['access_profiles']['action'] == 'existing'
        assert report['steps']['trusted_registry']['action'] == 'existing'
        assert report['runtime_smoke']['status'] == 'skipped'
        assert report['performance_baseline']['status'] in {'ready', 'monitoring', 'critical', 'failed'}
        assert Path(report['artifacts']['runtime_performance_baseline']).exists()
