from pathlib import Path

from sa_nom_governance.utils.config import AppConfig, bundled_resources_dir


def test_bundled_resources_match_public_resources_catalog() -> None:
    public_root = Path(__file__).resolve().parents[2] / "resources"
    bundled_root = bundled_resources_dir()

    public_files = sorted(path.relative_to(public_root).as_posix() for path in public_root.rglob("*") if path.is_file())
    bundled_files = sorted(path.relative_to(bundled_root).as_posix() for path in bundled_root.rglob("*") if path.is_file())

    assert bundled_files == public_files
    for relative_path in public_files:
        assert (bundled_root / relative_path).read_bytes() == (public_root / relative_path).read_bytes()


def test_app_config_seeds_bundled_resources_into_new_base_dir(tmp_path: Path) -> None:
    config = AppConfig(base_dir=tmp_path, persist_runtime=False)

    assert config.alignment_resources_dir == tmp_path / "resources" / "alignment"
    assert (config.alignment_resources_dir / "eu_transparency_constitution.json").exists()
    assert config.pt_oss_foundation_path is not None and config.pt_oss_foundation_path.exists()
    assert config.role_private_studio_template_path is not None and config.role_private_studio_template_path.exists()
    assert config.role_private_studio_examples_path is not None and config.role_private_studio_examples_path.exists()
    assert config.trusted_registry_manifest_path is not None and config.trusted_registry_manifest_path.exists()
